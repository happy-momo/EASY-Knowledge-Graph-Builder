"""
核心 LLM 抽取模块（重构版）

使用标准化 LLM 配置，支持任意厂商模型。

关键设计：
- ExtractionContext：批量抽取时只解析一次本体、只创建一个 LLM 客户端（复用
  httpx 连接池），避免每个分块重复创建/泄漏连接。
- _invoke_with_retry：对超时/限流/5xx 等可恢复异常做指数退避重试，单块瞬时
  失败不再直接终止整批抽取。
- _parse_llm_response：字符串感知的健壮 JSON 解析，避免早期正则破坏含冒号的
  合法 JSON（如时间、URL），解析失败时记录原始响应而非静默返回空。
"""

import json
import re
import time
import logging
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from utils.llm_config import LLMConfig, create_chat_model

logger = logging.getLogger(__name__)


class KnowledgeGraphTriple(BaseModel):
    """知识图谱三元组"""
    head: str = Field(description="头实体名称")
    head_type: str = Field(description="头实体类型 (必须来自本体定义)")
    head_properties: Dict = Field(description="头实体属性")
    relation: str = Field(description="关系名称 (必须来自本体定义)")
    tail: str = Field(description="尾实体名称")
    tail_type: str = Field(description="尾实体类型 (必须来自本体定义)")
    tail_properties: Dict = Field(description="尾实体属性")


class ExtractionResult(BaseModel):
    """抽取结果"""
    triples: List[KnowledgeGraphTriple]


class ExtractionContext:
    """
    抽取上下文：预解析的本体 + 复用的 LLM 客户端。

    批量抽取（处理多个分块）时应通过 prepare_extraction 创建一次并复用，
    结束后调用 close() 释放底层 httpx 连接池。
    """

    def __init__(self, llm, allowed_entity_types, allowed_relation_types,
                 relation_constraints, entity_properties):
        self.llm = llm
        self.allowed_entity_types = allowed_entity_types
        self.allowed_relation_types = allowed_relation_types
        self.relation_constraints = relation_constraints
        self.entity_properties = entity_properties
        # 由 prepare_extraction 设置，用于 close()
        self._http_client = None

    def close(self):
        """释放底层 httpx 连接（如有）"""
        if self._http_client is not None:
            try:
                self._http_client.close()
            except Exception as e:
                logger.warning(f"关闭 httpx 客户端失败: {e}")
            self._http_client = None


def prepare_extraction(ontology: str, config: LLMConfig) -> ExtractionContext:
    """
    预解析本体并创建 LLM 客户端（批量抽取只调用一次）。

    Args:
        ontology: YAML 格式的本体定义
        config: LLM 配置

    Returns:
        ExtractionContext，结束后需调用 close()
    """
    import yaml

    ontology_dict = yaml.safe_load(ontology) or {}

    allowed_entity_types = [entity['name'] for entity in ontology_dict.get('entities', [])]
    allowed_relation_types = [rel['relation'] for rel in ontology_dict.get('relationships', [])]

    relation_constraints = {}
    for rel in ontology_dict.get('relationships', []):
        relation_constraints[rel['relation']] = {
            'head': rel['head'],
            'tail': rel['tail']
        }

    entity_properties = {}
    for entity in ontology_dict.get('entities', []):
        entity_properties[entity['name']] = entity.get('properties', [])

    # 复用一个 httpx 连接池（仅路径 A 需要），避免每块新建连接泄漏文件描述符
    http_client = None
    if config.vendor_type == "openai_compatible":
        try:
            import httpx
            http_client = httpx.Client(
                transport=httpx.HTTPTransport(),
                timeout=httpx.Timeout(config.timeout, connect=10.0),
            )
        except ImportError:
            http_client = None

    llm = create_chat_model(config, http_client=http_client)

    ctx = ExtractionContext(
        llm=llm,
        allowed_entity_types=allowed_entity_types,
        allowed_relation_types=allowed_relation_types,
        relation_constraints=relation_constraints,
        entity_properties=entity_properties,
    )
    ctx._http_client = http_client
    return ctx


def extract_triples(text: str, ontology_or_ctx, config: Optional[LLMConfig] = None) -> List[KnowledgeGraphTriple]:
    """
    从文本中抽取三元组。

    两种调用方式：
    - 批量（推荐）：先 ctx = prepare_extraction(ontology, config)，再循环调用
      extract_triples(chunk, ctx)，复用 LLM 客户端；结束后 ctx.close()。
    - 单次（向后兼容）：extract_triples(text, ontology, config)，内部自建并关闭
      客户端。

    Args:
        text: 待处理的文本
        ontology_or_ctx: ExtractionContext（批量）或 YAML 本体字符串（单次）
        config: LLM 配置（仅单次模式需要）

    Returns:
        三元组列表
    """
    own_ctx = False
    if isinstance(ontology_or_ctx, ExtractionContext):
        ctx = ontology_or_ctx
    else:
        if config is None:
            raise ValueError("单次抽取模式需要提供 config 参数")
        ctx = prepare_extraction(ontology_or_ctx, config)
        own_ctx = True

    try:
        prompt = _build_extraction_prompt(
            ctx.allowed_entity_types,
            ctx.allowed_relation_types,
            ctx.relation_constraints,
            ctx.entity_properties,
            text
        )

        # 带重试的 LLM 调用
        response = _invoke_with_retry(ctx.llm, prompt)

        # 解析响应
        triples = _parse_llm_response(response.content if hasattr(response, 'content') else str(response))

        # 后处理过滤
        filtered_triples = _filter_triples(
            triples,
            ctx.allowed_entity_types,
            ctx.allowed_relation_types,
            ctx.relation_constraints
        )

        return filtered_triples

    except Exception as e:
        raise ExtractionError(f"抽取失败：{e}")
    finally:
        if own_ctx:
            ctx.close()


def _build_extraction_prompt(entity_types: List[str], relation_types: List[str],
                             constraints: Dict, entity_props: Dict, text: str) -> str:
    """构建抽取提示词"""

    entity_types_str = "\n".join([f"- {et}" for et in entity_types])
    relation_types_str = "\n".join([f"- {rt}" for rt in relation_types])
    constraints_str = "\n".join([f"- {rel}: {info['head']} -> {info['tail']}" for rel, info in constraints.items()])
    props_str = "\n".join([f"- {entity}: {props}" for entity, props in entity_props.items()])

    return f"""你是一个知识图谱构建专家。请根据以下本体定义，从给定的文本中提取实体和关系。

【本体定义】:

**允许的实体类型**:
{entity_types_str}

**允许的关系类型**:
{relation_types_str}

**关系约束**:
{constraints_str}

**实体属性**:
{props_str}

【待分析文本】:
{text}

【抽取规则】:
1. 实体类型必须严格匹配允许的列表
2. 关系类型必须严格匹配允许的列表
3. 关系约束必须严格遵守
4. 属性必须来自定义列表
5. 禁止推测和创造信息
6. 如果信息不符合约束，返回空列表

请以 JSON 格式返回结果：
{{
  "triples": [
    {{
      "head": "实体名称",
      "head_type": "实体类型",
      "head_properties": {{"属性名": "属性值"}},
      "relation": "关系类型",
      "tail": "实体名称",
      "tail_type": "实体类型",
      "tail_properties": {{"属性名": "属性值"}}
    }}
  ]
}}"""


# ==================== 可恢复异常判定与重试 ====================

# 通过类名子串判定可恢复异常，避免硬依赖具体异常类型（包可能未安装）
_TRANSIENT_MARKERS = (
    "timeout", "timedout", "connect", "connection", "ratelimit", "rate_limit",
    "retry", "temporarily", "unavailable", "internalservererror", "serverdisconnected",
    "remoteprotocol", "readtimeout", "pooltimeout", "429", "503", "502", "500", "504",
)
_TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}


def _is_transient(exc: Exception) -> bool:
    """判断异常是否为可恢复的瞬时异常（值得重试）"""
    # 状态码判定
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    try:
        if status is not None and int(status) in _TRANSIENT_STATUS_CODES:
            return True
    except (TypeError, ValueError):
        pass

    # 异常类名 + 消息子串判定
    text = f"{type(exc).__name__} {exc}".lower()
    return any(marker in text for marker in _TRANSIENT_MARKERS)


def _invoke_with_retry(llm, prompt, max_retries: int = 3):
    """
    调用 LLM，对可恢复异常做指数退避重试。

    非瞬时异常立即抛出（不浪费重试次数）。
    """
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            return llm.invoke(prompt)
        except Exception as e:
            last_exc = e
            if _is_transient(e) and attempt < max_retries:
                wait = min(2 ** attempt, 8)  # 1s, 2s, 4s ... 上限 8s
                logger.warning(
                    f"LLM 调用瞬时失败（第 {attempt + 1}/{max_retries + 1} 次），"
                    f"{wait}s 后重试: {type(e).__name__}: {e}"
                )
                time.sleep(wait)
                continue
            # 非瞬时异常或重试耗尽：抛出
            raise
    raise last_exc  # 理论不可达


# ==================== 健壮 JSON 解析 ====================

def _extract_json_object(text: str) -> Optional[str]:
    """
    从文本中提取首个平衡的 JSON 对象（字符串感知，尊重转义）。

    从第一个 '{' 开始，按括号深度配对到匹配的 '}'，忽略字符串字面量内的括号，
    避免贪婪正则抓取过大或过小的问题。
    """
    start = text.find('{')
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
    return None  # 括号不平衡


def _repair_json(text: str) -> str:
    """
    字符串感知的 JSON 修复：移除注释、移除尾随逗号、为裸键加引号。

    仅在严格 json.loads 失败时调用。逐字符遍历并跟踪字符串字面量状态，
    确保不会破坏值中含 :, //, } 等字符的合法字符串（早期正则会破坏它们）。
    """
    out = []
    i = 0
    n = len(text)
    in_string = False
    escape = False
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        # 字符串开始
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue

        # 行注释 //...
        if ch == '/' and i + 1 < n and text[i + 1] == '/':
            while i < n and text[i] != '\n':
                i += 1
            continue

        # 块注释 /*...*/
        if ch == '/' and i + 1 < n and text[i + 1] == '*':
            i += 2
            while i + 1 < n and not (text[i] == '*' and text[i + 1] == '/'):
                i += 1
            i += 2
            continue

        # 尾随逗号：逗号后（跳过空白）紧跟 } 或 ] -> 丢弃逗号
        if ch == ',':
            j = i + 1
            while j < n and text[j].isspace():
                j += 1
            if j < n and text[j] in '}]':
                i += 1
                continue
            out.append(ch)
            i += 1
            continue

        # 裸键：标识符（含 CJK）后跟可选空白再跟 ':' -> 加引号
        if ch.isalpha() or ch == '_' or ch == '$':
            j = i
            while j < n and (text[j].isalnum() or text[j] == '_' or text[j] == '$'):
                j += 1
            k = j
            while k < n and text[k].isspace():
                k += 1
            if k < n and text[k] == ':':
                out.append('"')
                out.append(text[i:j])
                out.append('"')
                i = j
                continue
            out.append(text[i:j])
            i = j
            continue

        out.append(ch)
        i += 1

    return ''.join(out)


def _parse_llm_response(response_text: str) -> List[KnowledgeGraphTriple]:
    """
    解析 LLM 响应为三元组列表。

    解析失败时记录原始响应（截断）并返回空列表，而非静默丢弃。
    """
    if not response_text:
        return []

    json_str = _extract_json_object(response_text)
    if not json_str:
        logger.warning(f"LLM 响应中未找到 JSON 对象，原始（截断）: {response_text[:800]!r}")
        return []

    # 1) 严格解析
    data = None
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # 2) 严格失败 -> 字符串感知修复后重试
    if data is None:
        try:
            repaired = _repair_json(json_str)
            data = json.loads(repaired)
        except json.JSONDecodeError as e:
            logger.warning(
                f"LLM 响应 JSON 解析失败: {e}；原始（截断）: {json_str[:800]!r}"
            )
            return []

    triples = []
    for triple_data in data.get('triples', []):
        try:
            triple = KnowledgeGraphTriple(
                head=triple_data.get('head', ''),
                head_type=triple_data.get('head_type', ''),
                head_properties=triple_data.get('head_properties', {}) or {},
                relation=triple_data.get('relation', ''),
                tail=triple_data.get('tail', ''),
                tail_type=triple_data.get('tail_type', ''),
                tail_properties=triple_data.get('tail_properties', {}) or {}
            )
            triples.append(triple)
        except Exception as e:
            logger.warning(f"跳过格式异常的三元组: {e}；数据: {triple_data!r}")

    return triples


def _filter_triples(triples: List[KnowledgeGraphTriple], allowed_entities: List[str],
                    allowed_relations: List[str], constraints: Dict) -> List[KnowledgeGraphTriple]:
    """过滤不符合约束的三元组"""
    filtered = []

    for triple in triples:
        # 检查实体类型
        if triple.head_type not in allowed_entities:
            continue
        if triple.tail_type not in allowed_entities:
            continue

        # 检查关系类型
        if triple.relation not in allowed_relations:
            continue

        # 检查关系约束
        if triple.relation in constraints:
            constraint = constraints[triple.relation]
            if triple.head_type != constraint['head'] or triple.tail_type != constraint['tail']:
                continue

        filtered.append(triple)

    return filtered


class ExtractionError(Exception):
    """抽取错误"""
    pass
