"""
安全的Neo4j连接管理器

修复连接安全问题，支持连接池和重试机制。
"""

from neo4j import GraphDatabase
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class Neo4jManager:
    """安全的Neo4j连接管理器"""

    def __init__(self, uri: str, user: str, password: str, max_retries: int = 3):
        """
        初始化Neo4j管理器

        Args:
            uri: Neo4j URI
            user: 用户名
            password: 密码
            max_retries: 最大重试次数
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.max_retries = max_retries
        self._driver = None

    def connect(self) -> bool:
        """建立连接"""
        try:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_pool_size=10,
                connection_acquisition_timeout=10
            )
            # 验证连接
            self._driver.verify_connectivity()
            logger.info("Neo4j连接成功")
            return True
        except Exception as e:
            logger.error(f"Neo4j连接失败: {e}")
            return False

    def close(self):
        """关闭连接"""
        if self._driver:
            self._driver.close()
            self._driver = None

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def execute_cypher(self, queries: List, retry_count: int = 0) -> bool:
        """
        执行Cypher查询（支持重试）

        Args:
            queries: CypherQuery列表或Cypher语句列表
            retry_count: 当前重试次数

        Returns:
            是否成功
        """
        if not self._driver:
            if not self.connect():
                return False

        try:
            with self._driver.session() as session:
                for query_obj in queries:
                    try:
                        if hasattr(query_obj, 'query') and hasattr(query_obj, 'parameters'):
                            # 参数化查询
                            session.run(query_obj.query, **query_obj.parameters)
                        else:
                            # 普通查询
                            session.run(query_obj)
                    except Exception as e:
                        logger.error(f"Cypher执行错误: {e}")
                        if retry_count < self.max_retries:
                            logger.info(f"重试执行 (第{retry_count + 1}次)")
                            return self.execute_cypher([query_obj], retry_count + 1)
                        raise

            return True

        except Exception as e:
            logger.error(f"Neo4j执行失败: {e}")
            return False

    def test_connection(self) -> tuple:
        """
        测试连接

        Returns:
            (是否成功, 消息)
        """
        try:
            if not self._driver:
                if not self.connect():
                    return False, "连接失败"

            with self._driver.session() as session:
                result = session.run("RETURN 1 AS test")
                record = result.single()
                if record and record["test"] == 1:
                    return True, "连接成功"
                return False, "连接测试失败"

        except Exception as e:
            return False, str(e)

    def get_statistics(self) -> Dict:
        """获取数据库统计信息"""
        try:
            with self._driver.session() as session:
                # 节点统计
                node_result = session.run("""
                    MATCH (n)
                    RETURN labels(n)[0] AS label, count(*) AS count
                    ORDER BY count DESC
                """)
                nodes = {record["label"]: record["count"] for record in node_result}

                # 关系统计
                rel_result = session.run("""
                    MATCH ()-[r]->()
                    RETURN type(r) AS type, count(*) AS count
                    ORDER BY count DESC
                """)
                relationships = {record["type"]: record["count"] for record in rel_result}

                return {
                    "nodes": nodes,
                    "relationships": relationships,
                    "total_nodes": sum(nodes.values()),
                    "total_relationships": sum(relationships.values())
                }

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}