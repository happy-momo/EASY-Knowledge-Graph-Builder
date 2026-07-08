"""
安全的Cypher查询生成器

修复Cypher注入漏洞，使用参数化查询。
"""

import re
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class CypherQuery:
    """Cypher查询对象"""
    query: str
    parameters: Dict


def sanitize_identifier(identifier: str) -> str:
    """
    清理标识符（节点标签、关系类型等）
    只允许字母、数字、下划线
    """
    if not identifier:
        return ""
    # 移除非法字符
    sanitized = re.sub(r'[^\w]', '', str(identifier))
    # 确保不以数字开头
    if sanitized and sanitized[0].isdigit():
        sanitized = '_' + sanitized
    return sanitized


def sanitize_string(value: str) -> str:
    """
    清理字符串值
    移除控制字符和潜在危险的字符
    """
    if not value:
        return ""
    # 移除控制字符
    sanitized = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', str(value))
    # 转义单引号
    sanitized = sanitized.replace("'", "\\'")
    return sanitized


def generate_cypher_safe(triples: List) -> List[CypherQuery]:
    """
    生成安全的Cypher查询
    使用参数化查询防止Cypher注入

    Args:
        triples: 三元组列表

    Returns:
        CypherQuery列表
    """
    queries = []

    for triple in triples:
        # 清理标识符
        head_type = sanitize_identifier(triple.head_type)
        tail_type = sanitize_identifier(triple.tail_type)
        relation = sanitize_identifier(triple.relation)

        # 清理属性值
        head_name = sanitize_string(triple.head)
        tail_name = sanitize_string(triple.tail)

        # 构建参数化查询
        params = {
            'head_name': head_name,
            'tail_name': tail_name
        }

        # 构建Cypher查询
        query = f"""
        // 创建头节点
        MERGE (h:{head_type} {{name: $head_name}})
        """

        # 头节点属性
        if triple.head_properties and isinstance(triple.head_properties, dict):
            head_props = []
            for k, v in triple.head_properties.items():
                if k != "name" and v is not None:
                    param_key = f"head_{k}"
                    params[param_key] = str(v)
                    head_props.append(f"h.{k} = ${param_key}")

            if head_props:
                query += f"\n        SET {', '.join(head_props)}"

        # 尾节点
        query += f"""

        // 创建尾节点
        MERGE (t:{tail_type} {{name: $tail_name}})
        """

        # 尾节点属性
        if triple.tail_properties and isinstance(triple.tail_properties, dict):
            tail_props = []
            for k, v in triple.tail_properties.items():
                if k != "name" and v is not None:
                    param_key = f"tail_{k}"
                    params[param_key] = str(v)
                    tail_props.append(f"t.{k} = ${param_key}")

            if tail_props:
                query += f"\n        SET {', '.join(tail_props)}"

        # 关系
        query += f"""

        // 创建关系
        MERGE (h)-[:{relation}]->(t)
        """

        queries.append(CypherQuery(query=query, parameters=params))

    return queries


def generate_cypher_batch(triples: List, batch_size: int = 100) -> List[List[CypherQuery]]:
    """
    批量生成Cypher查询

    Args:
        triples: 三元组列表
        batch_size: 每批大小

    Returns:
        分批的CypherQuery列表
    """
    all_queries = generate_cypher_safe(triples)
    batches = []

    for i in range(0, len(all_queries), batch_size):
        batch = all_queries[i:i + batch_size]
        batches.append(batch)

    return batches