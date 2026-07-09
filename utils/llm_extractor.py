import json
import os
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List


# 定义输出结构，强制 LLM 返回 JSON
class KnowledgeGraphTriple(BaseModel):
    head: str = Field(description="头实体名称")
    head_type: str = Field(description="头实体类型 (必须来自本体定义)")
    head_properties: dict = Field(description="头实体属性，包含所有在本体中定义的属性")
    relation: str = Field(description="关系名称 (必须来自本体定义)")
    tail: str = Field(description="尾实体名称")
    tail_type: str = Field(description="尾实体类型 (必须来自本体定义)")
    tail_properties: dict = Field(description="尾实体属性，包含所有在本体中定义的属性")


class ExtractionResult(BaseModel):
    triples: List[KnowledgeGraphTriple]


def process_text_with_llm(text_chunk, ontology, api_key, model_name="glm-4-flash"):
    """
    调用指定的LLM模型进行抽取
    """
    # 根据模型名称选择合适的API基础URL和参数
    llm_config = {
        "temperature": 0.1,
        "openai_api_key": api_key
    }
    
    # 配置不同模型的API基础URL和参数
    if model_name in ["glm-4-flash", "glm-4"]:
        # 智谱AI GLM系列
        llm_config["model"] = model_name
        llm_config["openai_api_base"] = "https://open.bigmodel.cn/api/paas/v4/"
    elif model_name in ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"]:
        # OpenAI GPT系列
        llm_config["model"] = model_name
        llm_config["openai_api_base"] = "https://api.openai.com/v1/"
    elif model_name in ["qwen-turbo", "qwen-plus", "qwen-max"]:
        # 阿里云通义千问
        llm_config["model"] = model_name
        llm_config["openai_api_base"] = "https://dashscope.aliyuncs.com/compatible-mode/v1/"
    elif model_name.startswith("claude-3-"):
        # Anthropic Claude 3系列
        # 注意：Claude API与OpenAI API不完全兼容
        # 可以通过Anthropic的OpenAI兼容接口调用
        llm_config["model"] = model_name
        llm_config["openai_api_base"] = "https://api.anthropic.com/v1/"
    elif model_name.startswith("gemini-"):
        # Google Gemini系列
        # 使用Gemini的OpenAI兼容接口
        llm_config["model"] = model_name
        llm_config["openai_api_base"] = "https://generativelanguage.googleapis.com/v1beta/"
    elif model_name.startswith("llama3-"):
        # Meta Llama 3系列
        # 使用Meta的OpenAI兼容接口或第三方服务
        llm_config["model"] = model_name
        llm_config["openai_api_base"] = "https://api.meta.ai/v1/"
    else:
        # 默认使用GLM-4-Flash
        llm_config["model"] = "glm-4-flash"
        llm_config["openai_api_base"] = "https://open.bigmodel.cn/api/paas/v4/"
    
    # 配置LLM并添加错误处理
    try:
        llm = ChatOpenAI(**llm_config)
    except Exception as e:
        raise ValueError(f"配置LLM失败: {str(e)}")

    parser = PydanticOutputParser(pydantic_object=ExtractionResult)

    # 解析YAML本体定义
    import yaml
    ontology_dict = yaml.safe_load(ontology)
    
    # 获取允许的实体类型和关系类型
    allowed_entity_types = [entity['name'] for entity in ontology_dict.get('entities', [])]
    allowed_relation_types = [rel['relation'] for rel in ontology_dict.get('relationships', [])]
    
    # 构建关系约束映射
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
    
    prompt = PromptTemplate(
        template="""你是一个知识图谱构建专家。请根据以下本体（Ontology）定义，从给定的文本中提取实体和关系。

        【本体定义 - 严格约束】:
        
        **允许的实体类型（仅限以下类型）**:
        {entity_types}
        
        **允许的关系类型（仅限以下类型）**:
        {relation_types}
        
        **关系约束（必须严格遵守）**:
        {relation_constraints}
        
        **实体属性约束**:
        {entity_properties}

        【待分析文本】:
        {text}

        【严格抽取规则 - 违反以下任何规则将导致抽取失败】:
        1. **实体类型必须严格匹配**: 只能使用上述允许的实体类型，其他类型一律禁止
        2. **关系类型必须严格匹配**: 只能使用上述允许的关系类型，其他类型一律禁止
        3. **关系约束必须严格遵守**: 关系的头实体和尾实体类型必须符合关系约束定义
        4. **属性必须来自定义列表**: 每个实体的属性必须来自该实体类型定义的属性列表
        5. **禁止推测和创造**: 仅提取文本中明确提到的信息，禁止推测、创造或添加额外信息
        6. **禁止创建不符合约束的关系**: 如果关系不符合本体定义中的约束，绝对禁止创建

        【违规示例 - 以下情况绝对不允许】:
        - 错误: 使用"属性"作为实体类型（不在允许列表中）
        - 错误: 使用"年龄"作为关系类型（不在允许列表中）
        - 错误: 使用"是"作为关系类型（不在允许列表中）
        - 错误: 创建"人物"->"属性"的关系（不符合关系约束）

        【正确示例】:
        {{
          "triples": [
            {{
              "head": "张三",
              "head_type": "人物",
              "head_properties": {{
                "name": "张三",
                "job": "工程师"
              }},
              "relation": "任职于",
              "tail": "科技公司A",
              "tail_type": "公司",
              "tail_properties": {{
                "name": "科技公司A",
                "industry": "科技"
              }}
            }}
          ]
        }}

        **重要提醒**: 如果文本中的信息不符合本体定义约束，请返回空列表 []，不要尝试创建不符合约束的三元组！

        """,
        input_variables=["entity_types", "relation_types", "relation_constraints", "entity_properties", "text"]
    )

    chain = prompt | llm | parser

    try:
        # 首先尝试直接调用LLM获取原始响应
        raw_response = llm.invoke(prompt.format(
            entity_types="\n".join([f"- {entity_type}" for entity_type in allowed_entity_types]),
            relation_types="\n".join([f"- {relation_type}" for relation_type in allowed_relation_types]),
            relation_constraints="\n".join([f"- {rel}: {constraints['head']} -> {constraints['tail']}" for rel, constraints in relation_constraints.items()]),
            entity_properties="\n".join([f"- {entity}: {props}" for entity, props in entity_properties.items()]),
            text=text_chunk
        ))
        
        print(f"LLM原始响应: {raw_response.content}")
        
        # 尝试解析JSON
        import re
        
        # 提取JSON部分
        json_match = re.search(r'\{[\s\S]*\}', raw_response.content)
        if json_match:
            json_str = json_match.group(0)
            print(f"提取的JSON字符串: {json_str}")
            
            # 清理JSON字符串：移除注释和尾随逗号
            def clean_json_string(json_str):
                # 1. 移除单行注释 (// ...)
                cleaned = re.sub(r'//[^\n]*', '', json_str)
                # 2. 移除多行注释 (/* ... */)
                cleaned = re.sub(r'/\*[^*]*\*+(?:[^/*][^*]*\*+)*/', '', cleaned)
                # 3. 移除尾随逗号（在对象和数组末尾）
                cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
                # 4. 清理多余的空格和换行
                cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
                cleaned = re.sub(r'^\s+|\s+$', '', cleaned, flags=re.MULTILINE)
                # 5. 修复可能的问题：确保属性名用双引号包围
                cleaned = re.sub(r'(\w+):', r'"\1":', cleaned)
                # 6. 确保字符串值用双引号包围（如果当前是单引号）
                cleaned = re.sub(r"'([^']*)'", r'"\1"', cleaned)
                return cleaned
            
            cleaned_json = clean_json_string(json_str)
            print(f"清理后的JSON字符串: {cleaned_json}")
            
            # 尝试解析JSON
            try:
                json_data = json.loads(cleaned_json)
                print(f"成功解析JSON: {json_data}")
                
                # 手动构建ExtractionResult对象
                triples_list = []
                if 'triples' in json_data and isinstance(json_data['triples'], list):
                    for triple_data in json_data['triples']:
                        # 创建KnowledgeGraphTriple对象
                        triple = KnowledgeGraphTriple(
                            head=triple_data.get('head', ''),
                            head_type=triple_data.get('head_type', ''),
                            head_properties=triple_data.get('head_properties', {}),
                            relation=triple_data.get('relation', ''),
                            tail=triple_data.get('tail', ''),
                            tail_type=triple_data.get('tail_type', ''),
                            tail_properties=triple_data.get('tail_properties', {})
                        )
                        triples_list.append(triple)
                
                # 创建ExtractionResult对象
                result = ExtractionResult(triples=triples_list)
                print(f"手动构建的结果: {result}")
                
            except json.JSONDecodeError as json_error:
                print(f"标准JSON解析错误: {json_error}")
                print(f"清理后的JSON字符串: {cleaned_json}")
                
                # 尝试更宽松的解析方式
                try:
                    # 使用demjson3库进行更宽松的解析
                    import demjson3
                    json_data = demjson3.decode(cleaned_json)
                    print(f"使用demjson3成功解析JSON: {json_data}")
                    
                    # 手动构建ExtractionResult对象
                    triples_list = []
                    if 'triples' in json_data and isinstance(json_data['triples'], list):
                        for triple_data in json_data['triples']:
                            triple = KnowledgeGraphTriple(
                                head=triple_data.get('head', ''),
                                head_type=triple_data.get('head_type', ''),
                                head_properties=triple_data.get('head_properties', {}),
                                relation=triple_data.get('relation', ''),
                                tail=triple_data.get('tail', ''),
                                tail_type=triple_data.get('tail_type', ''),
                                tail_properties=triple_data.get('tail_properties', {})
                            )
                            triples_list.append(triple)
                    
                    result = ExtractionResult(triples=triples_list)
                    print(f"手动构建的结果: {result}")
                except Exception as demjson_error:
                    print(f"demjson3解析也失败: {demjson_error}")
                    
                    # 最后尝试：手动修复常见的JSON格式问题
                    try:
                        # 手动修复注释问题
                        manual_fixed_json = json_str
                        # 移除所有注释行
                        lines = manual_fixed_json.split('\n')
                        cleaned_lines = []
                        for line in lines:
                            if '//' in line:
                                # 保留注释前的部分
                                line = line.split('//')[0]
                            cleaned_lines.append(line.strip())
                        manual_fixed_json = '\n'.join(cleaned_lines)
                        
                        # 移除尾随逗号
                        manual_fixed_json = re.sub(r',\s*\n\s*([}\]])', r'\n\1', manual_fixed_json)
                        
                        print(f"手动修复后的JSON: {manual_fixed_json}")
                        
                        json_data = json.loads(manual_fixed_json)
                        print(f"手动修复后成功解析JSON: {json_data}")
                        
                        # 手动构建ExtractionResult对象
                        triples_list = []
                        if 'triples' in json_data and isinstance(json_data['triples'], list):
                            for triple_data in json_data['triples']:
                                triple = KnowledgeGraphTriple(
                                    head=triple_data.get('head', ''),
                                    head_type=triple_data.get('head_type', ''),
                                    head_properties=triple_data.get('head_properties', {}),
                                    relation=triple_data.get('relation', ''),
                                    tail=triple_data.get('tail', ''),
                                    tail_type=triple_data.get('tail_type', ''),
                                    tail_properties=triple_data.get('tail_properties', {})
                                )
                                triples_list.append(triple)
                        
                        result = ExtractionResult(triples=triples_list)
                        print(f"手动构建的结果: {result}")
                    except Exception as final_error:
                        print(f"所有解析方法都失败: {final_error}")
                        return []
        else:
            print("未找到JSON格式的响应")
            return []
        
        # 后处理过滤：确保所有三元组都符合本体定义
        filtered_triples = []
        for triple in result.triples:
            # 检查实体类型是否在允许列表中
            if triple.head_type not in allowed_entity_types:
                print(f"警告: 跳过不符合本体定义的实体类型: {triple.head_type}")
                continue
            if triple.tail_type not in allowed_entity_types:
                print(f"警告: 跳过不符合本体定义的实体类型: {triple.tail_type}")
                continue
            
            # 检查关系类型是否在允许列表中
            if triple.relation not in allowed_relation_types:
                print(f"警告: 跳过不符合本体定义的关系类型: {triple.relation}")
                continue
            
            # 检查关系约束
            if triple.relation in relation_constraints:
                constraint = relation_constraints[triple.relation]
                if triple.head_type != constraint['head'] or triple.tail_type != constraint['tail']:
                    print(f"警告: 跳过不符合关系约束的三元组: {triple.head_type}-[{triple.relation}]->{triple.tail_type}")
                    continue
            
            filtered_triples.append(triple)
        
        print(f"过滤后三元组数量: {len(filtered_triples)}")
        return filtered_triples
        
    except Exception as e:
        print(f"LLM Extraction Error: {e}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        return []


def generate_cypher(triples):
    """
    将三元组转换为 Cypher 语句
    逻辑：
    1. 对每个三元组，构建一个完整的Cypher查询
    2. 使用MERGE创建或匹配节点
    3. 使用SET更新节点属性
    4. 使用MERGE创建关系
    """
    queries = []
    for t in triples:
        # 清理特殊字符，防止 Cypher 注入 (简单处理)
        h_name = t.head.replace("'", "").replace('"', "")
        t_name = t.tail.replace("'", "").replace('"', "")
        relation = t.relation.replace("'", "").replace('"', "")

        # 构建完整的Cypher查询
        cypher_query = f"""
        // 处理头节点
        MERGE (h:{t.head_type} {{name: '{h_name}'}})
        """

        # 设置头实体的属性
        if t.head_properties and isinstance(t.head_properties, dict):
            # 只保留非空属性
            valid_head_props = {k: v for k, v in t.head_properties.items() if v is not None}
            if valid_head_props:
                # 构建SET语句
                head_props = []
                for k, v in valid_head_props.items():
                    if k != "name":
                        # 先处理单引号转义
                        prop_value = str(v).replace("'", "''")
                        # 再构建属性字符串
                        head_props.append(f"h.{k} = '{prop_value}'")
                head_props_str = ", ".join(head_props)
                if head_props_str:
                    cypher_query += f"\n        SET {head_props_str}"

        # 处理尾节点
        cypher_query += f"""
        
        // 处理尾节点
        MERGE (t:{t.tail_type} {{name: '{t_name}'}})
        """

        # 设置尾实体的属性
        if t.tail_properties and isinstance(t.tail_properties, dict):
            # 只保留非空属性
            valid_tail_props = {k: v for k, v in t.tail_properties.items() if v is not None}
            if valid_tail_props:
                # 构建SET语句
                tail_props = []
                for k, v in valid_tail_props.items():
                    if k != "name":
                        # 先处理单引号转义
                        prop_value = str(v).replace("'", "''")
                        # 再构建属性字符串
                        tail_props.append(f"t.{k} = '{prop_value}'")
                tail_props_str = ", ".join(tail_props)
                if tail_props_str:
                    cypher_query += f"\n        SET {tail_props_str}"

        # 处理关系
        cypher_query += f"""
        
        // 处理关系
        MERGE (h)-[:{relation}]->(t)
        """

        queries.append(cypher_query)

    return queries