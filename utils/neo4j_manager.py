"""
安全的Neo4j连接管理器

修复连接安全问题，支持连接池和重试机制。
"""

from neo4j import GraphDatabase
from typing import Optional, List, Dict
import logging
import time

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
        if not self.connect():
            raise RuntimeError(f"Neo4j 连接失败: {self.uri}（请检查 URI/用户名/密码及服务是否启动）")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def _run_single(self, session, query_obj) -> bool:
        """执行单条查询（带重试），失败返回 False"""
        for attempt in range(self.max_retries + 1):
            try:
                if hasattr(query_obj, 'query') and hasattr(query_obj, 'parameters'):
                    session.run(query_obj.query, **query_obj.parameters)
                else:
                    session.run(query_obj)
                return True
            except Exception as e:
                logger.error(f"Cypher执行错误 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}")
                if attempt < self.max_retries:
                    time.sleep(0.1 * (attempt + 1))  # 轻微退避
        return False

    def execute_cypher(self, queries: List, retry_count: int = 0) -> bool:
        """
        执行Cypher查询（逐条执行，单条失败不中断剩余查询）

        Args:
            queries: CypherQuery列表或Cypher语句列表
            retry_count: 未使用（保留以向后兼容），重试在 _run_single 内完成

        Returns:
            是否全部成功（若有任意一条失败则返回 False，但已尽可能执行其余查询）
        """
        if not self._driver:
            if not self.connect():
                return False

        failed = 0
        try:
            with self._driver.session() as session:
                for query_obj in queries:
                    if not self._run_single(session, query_obj):
                        failed += 1

            if failed:
                logger.error(f"Neo4j: {failed}/{len(queries)} 条查询执行失败")
                return False
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
        if not self._driver:
            if not self.connect():
                return {}
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