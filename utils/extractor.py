"""
核心 LLM 抽取模块（重构版）

使用标准化 LLM 配置，支持任意厂商模型。
"""

import json
import re
import os
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field

from utils.llm_config import LLMConfig, create_chat_model


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


def extract_triples(text: str, ontology: str, config: LLMConfig) -> List[KnowledgeGraphTriple]:
    """
    从文本中抽取三元组

    Args:
        text: 待处理的文本
        ontology: YAML 格式的本体定义
        config: LLM 配置

    Returns:
        三元组列表
    """
    try:
        from langchain.prompts import PromptTemplate
        from langchain.output_parsers import PydanticOutputParser

        # 解析本体
        import yaml
        ontology_dict = yaml.safe_load(ontology)

        allowed_entity_types = [entity['name'] for entity in ontology_dict.get('entities', [])]
        allowed_relation_types = [rel['relation'] for rel in ontology_dict.get('relationships', [])]

        # 构建关系约束
        relation_constraints = {}
        for rel in ontology_dict.get('relationships', []):
            relation_constraints[rel['relation']] = {
                'head': rel['head'],
                'tail': rel['tail']
            }

        # 构建实体属性映射
        entity_properties = {}
        for entity in ontology_dict.get('entities', []):
            entity_properties[entity['name']] = entity.get('properties', [])

        # 动态创建 LLM
        llm = create_chat_model(config)

        # 构建提示词
        prompt = _build_extraction_prompt(
            allowed_entity_types,
            allowed_relation_types,
            relation_constraints,
            entity_properties,
            text
        )

        # 调用 LLM
        response = llm.invoke(prompt)

        # 解析响应
        triples = _parse_llm_response(response.content)

        # 后处理过滤
        filtered_triples = _filter_triples(triples, allowed_entity_types, allowed_relation_types, relation_constraints)

        return filtered_triples

    except Exception as e:
        raise ExtractionError(f"抽取失败：{e}")


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


def _parse_llm_response(response_text: str) -> List[KnowledgeGraphTriple]:
    """解析 LLM 响应"""
    try:
        # 提取 JSON
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            return []

        json_str = json_match.group(0)

        # 清理 JSON
        json_str = _clean_json_string(json_str)

        # 解析
        data = json.loads(json_str)

        triples = []
        for triple_data in data.get('triples', []):
            triple = KnowledgeGraphTriple(
                head=triple_data.get('head', ''),
                head_type=triple_data.get('head_type', ''),
                head_properties=triple_data.get('head_properties', {}),
                relation=triple_data.get('relation', ''),
                tail=triple_data.get('tail', ''),
                tail_type=triple_data.get('tail_type', ''),
                tail_properties=triple_data.get('tail_properties', {})
            )
            triples.append(triple)

        return triples

    except json.JSONDecodeError:
        return []
    except Exception:
        return []


def _clean_json_string(json_str: str) -> str:
    """清理 JSON 字符串"""
    # 移除注释
    json_str = re.sub(r'//[^\n]*', '', json_str)
    json_str = re.sub(r'/\*[^*]*\*+(?:[^/*][^*]*\*+)*/', '', json_str)

    # 移除尾随逗号
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)

    # 修复属性名引号
    json_str = re.sub(r'(\w+):', r'"\1":', json_str)

    # 修复字符串值引号
    json_str = re.sub(r"'([^']*)'", r'"\1"', json_str)

    return json_str


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
