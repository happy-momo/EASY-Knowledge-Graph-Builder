"""
单元测试

测试核心模块的功能正确性。
"""

import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# 测试状态管理器
class TestStateManager(unittest.TestCase):
    """测试StateManager"""

    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """测试后清理"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)

    def test_save_and_load(self):
        """测试保存和加载"""
        from utils.state_manager import StateManager

        manager = StateManager()
        manager.save('test', {'key': 'value'})

        result = manager.load('test')
        self.assertEqual(result['key'], 'value')

    def test_load_nonexistent(self):
        """测试加载不存在的键"""
        from utils.state_manager import StateManager

        manager = StateManager()
        result = manager.load('nonexistent', 'default')
        self.assertEqual(result, 'default')

    def test_clear(self):
        """测试清除"""
        from utils.state_manager import StateManager

        manager = StateManager()
        manager.save('test', {'key': 'value'})
        manager.clear('test')

        result = manager.load('test', 'default')
        self.assertEqual(result, 'default')


# 测试LLM配置
class TestLLMConfig(unittest.TestCase):
    """测试LLMConfig"""

    def test_valid_config(self):
        """测试有效配置"""
        from utils.llm_config import LLMConfig

        config = LLMConfig(
            api_endpoint="https://api.example.com/v1/",
            api_key="test-key",
            model_name="test-model"
        )

        self.assertEqual(config.api_endpoint, "https://api.example.com/v1/")
        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.model_name, "test-model")

    def test_missing_endpoint(self):
        """测试缺少端点"""
        from utils.llm_config import LLMConfig

        with self.assertRaises(ValueError):
            LLMConfig(
                api_endpoint="",
                api_key="test-key",
                model_name="test-model"
            )

    def test_missing_api_key(self):
        """测试缺少API Key"""
        from utils.llm_config import LLMConfig

        with self.assertRaises(ValueError):
            LLMConfig(
                api_endpoint="https://api.example.com/v1/",
                api_key="",
                model_name="test-model"
            )

    def test_to_dict(self):
        """测试转换为字典"""
        from utils.llm_config import LLMConfig

        config = LLMConfig(
            api_endpoint="https://api.example.com/v1/",
            api_key="test-key",
            model_name="test-model"
        )

        config_dict = config.to_dict()
        self.assertEqual(config_dict['api_endpoint'], "https://api.example.com/v1/")
        self.assertEqual(config_dict['api_key'], "test-key")


# 测试Cypher生成器
class TestCypherGenerator(unittest.TestCase):
    """测试Cypher生成器"""

    def test_sanitize_identifier(self):
        """测试标识符清理"""
        from utils.cypher_generator import sanitize_identifier

        self.assertEqual(sanitize_identifier("Person"), "Person")
        self.assertEqual(sanitize_identifier("Person 123"), "Person123")
        self.assertEqual(sanitize_identifier("123Person"), "_123Person")
        self.assertEqual(sanitize_identifier("Person' OR '1'='1"), "PersonOR11")

    def test_sanitize_string(self):
        """测试字符串清理：参数化值仅移除控制字符，不再转义引号（避免数据损坏）"""
        from utils.cypher_generator import sanitize_string

        self.assertEqual(sanitize_string("Hello"), "Hello")
        # 单引号原样保留（值通过 $param 参数化传递，无需转义）
        self.assertEqual(sanitize_string("Hello'World"), "Hello'World")
        self.assertEqual(sanitize_string(""), "")

    def test_generate_cypher_safe(self):
        """测试生成安全Cypher"""
        from utils.cypher_generator import generate_cypher_safe
        from utils.extractor import KnowledgeGraphTriple

        triple = KnowledgeGraphTriple(
            head="张三",
            head_type="Person",
            head_properties={"age": "30"},
            relation="worksAt",
            tail="阿里巴巴",
            tail_type="Company",
            tail_properties={"industry": "科技"}
        )

        queries = generate_cypher_safe([triple])
        self.assertEqual(len(queries), 1)

        # 检查是否使用了参数化查询
        query = queries[0]
        self.assertIn("$head_name", query.query)
        self.assertIn("$tail_name", query.query)
        self.assertEqual(query.parameters['head_name'], "张三")
        self.assertEqual(query.parameters['tail_name'], "阿里巴巴")


# 测试文件管理器
class TestFileManager(unittest.TestCase):
    """测试FileManager"""

    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """测试后清理"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)

    def test_add_and_remove_file(self):
        """测试添加和移除文件"""
        from utils.file_manager import FileManager

        manager = FileManager()

        # 创建模拟上传文件
        class MockFile:
            def __init__(self):
                self.name = "test.pdf"
                self.size = 1024

            def getbuffer(self):
                return b"test content"

        mock_file = MockFile()
        file_info = manager.add_uploaded_file(mock_file)

        self.assertEqual(file_info.name, "test.pdf")
        self.assertEqual(len(manager.get_files()), 1)

        # 移除文件
        manager.remove_file(file_info.id)
        self.assertEqual(len(manager.get_files()), 0)


# 测试进度追踪器
class TestProgressTracker(unittest.TestCase):
    """测试ProgressTracker"""

    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """测试后清理"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)

    def test_progress_tracking(self):
        """测试进度追踪"""
        from utils.progress_tracker import ProgressTracker

        tracker = ProgressTracker()
        tracker.start(total_files=2, total_chunks=10)

        self.assertEqual(tracker._progress.total_files, 2)
        self.assertEqual(tracker._progress.total_chunks, 10)

        # 更新分块
        tracker.update_chunk_start(0, "file1", "file1_id")
        tracker.update_chunk_complete(0, [{"test": "data"}], 1)

        self.assertEqual(tracker._progress.processed_chunks, 1)
        self.assertEqual(tracker._progress.total_triples, 1)

    def test_can_resume(self):
        """测试断点续传"""
        from utils.progress_tracker import ProgressTracker

        tracker = ProgressTracker()
        tracker.start(total_files=1, total_chunks=5)

        # 处理2个分块
        for i in range(2):
            tracker.update_chunk_start(i, "file1", "file1_id")
            tracker.update_chunk_complete(i, [], 0)

        self.assertTrue(tracker.can_resume())

        # 完成所有分块
        for i in range(2, 5):
            tracker.update_chunk_start(i, "file1", "file1_id")
            tracker.update_chunk_complete(i, [], 0)

        tracker.complete()
        self.assertFalse(tracker.can_resume())


# 测试Schema验证
class TestSchemaValidation(unittest.TestCase):
    """测试Schema验证"""

    def test_valid_schema(self):
        """测试有效Schema"""
        from components.schema_templates import validate_schema

        schema = {
            "entities": [
                {"name": "Person", "properties": ["name", "age"]}
            ],
            "relationships": [
                {"head": "Person", "relation": "knows", "tail": "Person"}
            ]
        }

        is_valid, error = validate_schema(schema)
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_missing_entities(self):
        """测试缺少entities"""
        from components.schema_templates import validate_schema

        schema = {
            "relationships": []
        }

        is_valid, error = validate_schema(schema)
        self.assertFalse(is_valid)
        self.assertIn("entities", error)

    def test_invalid_relation(self):
        """测试无效的关系"""
        from components.schema_templates import validate_schema

        schema = {
            "entities": [
                {"name": "Person", "properties": ["name"]}
            ],
            "relationships": [
                {"head": "Person", "relation": "knows", "tail": "Company"}
            ]
        }

        is_valid, error = validate_schema(schema)
        self.assertFalse(is_valid)
        self.assertIn("Company", error)


if __name__ == '__main__':
    unittest.main()