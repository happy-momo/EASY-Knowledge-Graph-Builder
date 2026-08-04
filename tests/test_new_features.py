"""
新功能与回归测试

覆盖本轮优化新增/修改的功能：
- Schema 结构图可视化
- FileInfo.from_dict 容错
- Cypher 批量生成
- ProgressTracker upsert + 重启恢复
- Extractor 解析与过滤
- StateManager 原子写
- 共享 SUPPORTED_EXTENSIONS
- doc_loader 统一读取
"""

import unittest
import json
import threading
import time
from pathlib import Path
from html import escape as html_escape


class TestSchemaVisualizer(unittest.TestCase):
    """Schema 结构图可视化"""

    def test_render_basic_graph(self):
        """基础结构图渲染"""
        from utils.schema_visualizer import render_schema_graph

        schema = {
            "entities": [
                {"name": "Person", "properties": ["name", "age"]},
                {"name": "Company", "properties": ["name", "industry"]},
            ],
            "relationships": [
                {"head": "Person", "relation": "worksAt", "tail": "Company"},
            ],
        }
        html = render_schema_graph(schema)

        # 包含 SVG 容器
        self.assertIn('<svg', html)
        self.assertIn('</svg>', html)
        # 包含 2 个实体节点
        self.assertEqual(html.count('<circle'), 2)
        # 包含 1 条关系（无自环）
        self.assertIn('schema-arrow', html)
        # 包含 tooltip
        self.assertIn('<title>', html)
        # 包含实体名
        self.assertIn('Person', html)
        self.assertIn('Company', html)

    def test_render_empty_schema(self):
        """空 Schema 不崩溃"""
        from utils.schema_visualizer import render_schema_graph

        html = render_schema_graph({"entities": [], "relationships": []})
        self.assertIn("暂无实体", html)

    def test_render_self_loop(self):
        """自环关系正确渲染"""
        from utils.schema_visualizer import render_schema_graph

        schema = {
            "entities": [{"name": "Person", "properties": []}],
            "relationships": [
                {"head": "Person", "relation": "knows", "tail": "Person"},
            ],
        }
        html = render_schema_graph(schema)
        self.assertEqual(html.count('<circle'), 1)
        # 自环应渲染（不崩溃）
        self.assertIn('schema-arrow', html)

    def test_render_skips_invalid_relations(self):
        """引用不存在实体的关系被跳过"""
        from utils.schema_visualizer import render_schema_graph

        schema = {
            "entities": [{"name": "Person", "properties": []}],
            "relationships": [
                {"head": "Person", "relation": "owns", "tail": "Ghost"},  # Ghost 不存在
            ],
        }
        # 不崩溃
        html = render_schema_graph(schema)
        self.assertIn('<svg', html)

    def test_render_details(self):
        """明细摘要"""
        from utils.schema_visualizer import render_schema_details

        schema = {
            "entities": [{"name": "Person", "properties": ["name", "age"]}],
            "relationships": [
                {"head": "Person", "relation": "knows", "tail": "Person"},
            ],
        }
        html = render_schema_details(schema)
        self.assertIn("实体类型", html)
        self.assertIn("关系约束", html)
        self.assertIn("Person", html)
        self.assertIn("knows", html)


class TestFileInfoFromDictTolerance(unittest.TestCase):
    """FileInfo.from_dict 应容错未知键/缺失键"""

    def test_ignores_unknown_keys(self):
        """未知键被忽略"""
        from utils.file_manager import FileInfo

        data = {
            "id": "f1",
            "name": "test.pdf",
            "path": "/tmp/test.pdf",
            "unknown_field": "should be ignored",
            "another_unknown": 42,
        }
        info = FileInfo.from_dict(data)
        self.assertEqual(info.id, "f1")
        self.assertEqual(info.name, "test.pdf")
        # 确认未知属性不存在
        self.assertFalse(hasattr(info, "unknown_field"))

    def test_uses_defaults_for_missing_keys(self):
        """缺失键使用默认值"""
        from utils.file_manager import FileInfo

        data = {"id": "f1", "name": "test.pdf", "path": "/tmp/test.pdf"}
        info = FileInfo.from_dict(data)
        self.assertEqual(info.id, "f1")
        self.assertEqual(info.name, "test.pdf")
        self.assertEqual(info.path, "/tmp/test.pdf")
        self.assertEqual(info.original_path, "")
        self.assertEqual(info.size, 0)
        self.assertEqual(info.chunks, [])
        self.assertEqual(info.status, "pending")

    def test_roundtrip(self):
        """to_dict -> from_dict 保持一致"""
        from utils.file_manager import FileInfo

        original = FileInfo(id="x", name="x.txt", path="/tmp/x.txt", size=100)
        restored = FileInfo.from_dict(original.to_dict())
        self.assertEqual(original.id, restored.id)
        self.assertEqual(original.name, restored.name)
        self.assertEqual(original.size, restored.size)


class TestCypherBatch(unittest.TestCase):
    """Cypher 批量生成"""

    def test_batch_size(self):
        """批量生成按指定大小分批"""
        from utils.cypher_generator import generate_cypher_batch
        from utils.extractor import KnowledgeGraphTriple

        triples = [
            KnowledgeGraphTriple(
                head=f"h{i}", head_type="T", head_properties={},
                relation="rel", tail=f"t{i}", tail_type="T", tail_properties={}
            )
            for i in range(10)
        ]
        batches = generate_cypher_batch(triples, batch_size=3)
        self.assertEqual(len(batches), 4)  # 3, 3, 3, 1
        self.assertEqual(len(batches[0]), 3)
        self.assertEqual(len(batches[-1]), 1)

    def test_parameterization_prevents_injection(self):
        """参数化查询防止注入"""
        from utils.cypher_generator import generate_cypher_safe
        from utils.extractor import KnowledgeGraphTriple

        triple = KnowledgeGraphTriple(
            head="恶意' OR DROP--",
            head_type="Person",
            head_properties={},
            relation="knows",
            tail="正常",
            tail_type="Person",
            tail_properties={},
        )
        queries = generate_cypher_safe([triple])
        self.assertEqual(len(queries), 1)
        # 恶意值在参数中而非 Cypher 字符串中
        self.assertIn("$head_name", queries[0].query)
        # 参数化查询下值原样保留（不再转义引号，避免数据损坏）；注入由参数化隔离
        self.assertEqual(queries[0].parameters['head_name'], "恶意' OR DROP--")
        # 确保恶意值没有被直接拼接到 query 字符串（只通过参数传递）
        self.assertNotIn("DROP", queries[0].query)
        self.assertNotIn("恶意", queries[0].query)


class TestProgressTrackerResume(unittest.TestCase):
    """ProgressTracker 断点续传与重启恢复"""

    def test_upsert_no_duplicate_chunks(self):
        """同一 chunk_index 多次 update_chunk_start 不产生重复记录"""
        from utils.progress_tracker import ProgressTracker

        tracker = ProgressTracker()
        tracker.start(total_files=1, total_chunks=3)

        tracker.update_chunk_start(0, "file1", "fid1")
        tracker.update_chunk_start(0, "file1", "fid1")  # 重复调用

        self.assertEqual(len(tracker._progress.chunk_progress), 1)
        self.assertEqual(tracker._progress.chunk_progress[0]['status'], 'processing')

    def test_complete_keeps_status(self):
        """complete() 保持 COMPLETED 状态以便重启后读取三元组"""
        from utils.progress_tracker import ProgressTracker, ProcessStatus

        tracker = ProgressTracker()
        tracker.start(total_files=1, total_chunks=2)
        tracker.update_chunk_start(0, "f1", "fid")
        triples = [{
            "head": "A", "head_type": "T", "head_properties": {},
            "relation": "rel", "tail": "B", "tail_type": "T", "tail_properties": {}
        }]
        tracker.update_chunk_complete(0, triples, 1)
        tracker.complete()

        # 状态应为 COMPLETED，不是 IDLE
        self.assertEqual(tracker._progress.status, ProcessStatus.COMPLETED.value)

    def test_triples_survive_restart(self):
        """重启后三元组不丢失"""
        from utils.progress_tracker import ProgressTracker

        t1 = ProgressTracker()
        t1.start(total_files=1, total_chunks=2)
        t1.update_chunk_start(0, "f1", "fid")
        triples = [{
            "head": "A", "head_type": "T", "head_properties": {},
            "relation": "rel", "tail": "B", "tail_type": "T", "tail_properties": {}
        }]
        t1.update_chunk_complete(0, triples, 1)
        t1.complete()

        # 模拟重启：创建新实例
        t2 = ProgressTracker()
        all_triples = t2.get_all_triples()
        self.assertEqual(len(all_triples), 1)
        self.assertEqual(all_triples[0]['head'], 'A')


class TestExtractorParsing(unittest.TestCase):
    """Extractor 解析与过滤"""

    def test_parse_valid_json(self):
        """解析合法 JSON"""
        from utils.extractor import _parse_llm_response

        response = '{"triples": [{"head": "A", "head_type": "T", "head_properties": {}, "relation": "rel", "tail": "B", "tail_type": "T", "tail_properties": {}}]}'
        result = _parse_llm_response(response)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].head, "A")

    def test_parse_json_with_markdown_fences(self):
        """解析带 Markdown 围栏的 JSON"""
        from utils.extractor import _parse_llm_response

        response = '```json\n{"triples": [{"head": "X", "head_type": "T", "head_properties": {}, "relation": "r", "tail": "Y", "tail_type": "T", "tail_properties": {}}]}\n```'
        result = _parse_llm_response(response)
        self.assertEqual(len(result), 1)

    def test_parse_malformed_json(self):
        """畸形 JSON 不崩溃"""
        from utils.extractor import _parse_llm_response

        self.assertEqual(_parse_llm_response("not json"), [])
        self.assertEqual(_parse_llm_response("{incomplete"), [])

    def test_filter_violates_entity_type(self):
        """过滤违反实体类型的三元组"""
        from utils.extractor import _parse_llm_response, _filter_triples

        response = '{"triples": [{"head": "A", "head_type": "WrongType", "head_properties": {}, "relation": "rel", "tail": "B", "tail_type": "T", "tail_properties": {}}]}'
        parsed = _parse_llm_response(response)
        filtered = _filter_triples(parsed, ["T", "Person"], ["rel"], {"rel": {"head": "T", "tail": "T"}})
        self.assertEqual(len(filtered), 0)

    def test_filter_violates_relation_constraint(self):
        """过滤违反关系约束的三元组"""
        from utils.extractor import _parse_llm_response, _filter_triples

        response = '{"triples": [{"head": "A", "head_type": "T", "head_properties": {}, "relation": "rel", "tail": "B", "tail_type": "Wrong", "tail_properties": {}}]}'
        parsed = _parse_llm_response(response)
        filtered = _filter_triples(parsed, ["T", "Wrong"], ["rel"], {"rel": {"head": "T", "tail": "T"}})
        self.assertEqual(len(filtered), 0)


class TestStateManagerAtomicity(unittest.TestCase):
    """StateManager 原子写与并发安全"""

    def test_atomic_write_creates_temp_file(self):
        """保存后目标文件存在，临时文件被清理"""
        from utils import state_manager as sm

        sm.state_manager.save("test_key", {"a": 1})

        target = sm.state_manager.data_dir / "test_key.json"
        self.assertTrue(target.exists())
        # 不应残留 .tmp 文件
        tmp = sm.state_manager.data_dir / "test_key.json.tmp"
        self.assertFalse(tmp.exists())

    def test_concurrent_writes_no_corruption(self):
        """多线程并发写不损坏文件"""
        from utils import state_manager as sm

        errors = []

        def writer(i):
            try:
                for _ in range(20):
                    sm.state_manager.save(f"key_{i % 3}", {"writer": i, "ts": time.time()})
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [], f"并发写错误: {errors}")
        # 验证文件可正常解析
        for key in ["key_0", "key_1", "key_2"]:
            data = sm.state_manager.load(key)
            self.assertIsNotNone(data)


class TestSharedSupportedExtensions(unittest.TestCase):
    """SUPPORTED_EXTENSIONS 共享一致性"""

    def test_folder_loader_uses_file_manager(self):
        """folder_loader 引用 file_manager 的扩展名列表"""
        from utils.file_manager import FileManager
        from utils.folder_loader import SUPPORTED_EXTENSIONS

        self.assertEqual(SUPPORTED_EXTENSIONS, FileManager.SUPPORTED_EXTENSIONS)
        self.assertIn('.pdf', SUPPORTED_EXTENSIONS)
        self.assertIn('.docx', SUPPORTED_EXTENSIONS)


class TestDocLoaderUnifiedReader(unittest.TestCase):
    """doc_loader 统一读取函数"""

    def test_read_txt_file(self):
        """读取 UTF-8 文本文件"""
        from utils.doc_loader import _read_content

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Hello, 世界! 你好。")
            tmp_path = f.name

        try:
            content = _read_content(tmp_path, "txt")
            self.assertIn("世界", content)
            self.assertIn("你好", content)
        finally:
            Path(tmp_path).unlink()

    def test_read_txt_multiple_encodings(self):
        """读取 GBK 编码文件"""
        from utils.doc_loader import _read_content

        import tempfile
        content_gbk = "你好世界".encode('gbk')
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(content_gbk)
            tmp_path = f.name

        try:
            content = _read_content(tmp_path, "txt")
            self.assertEqual(content, "你好世界")
        finally:
            Path(tmp_path).unlink()

    def test_read_unsupported_type(self):
        """不支持的文件类型返回空字符串"""
        from utils.doc_loader import _read_content

        self.assertEqual(_read_content("nonexistent.xyz", "xyz"), "")

    def test_load_document_nonexistent_path(self):
        """不存在的路径返回错误信息"""
        from utils.doc_loader import load_document

        chunks, error = load_document("/nonexistent/path/file.txt")
        self.assertIsNone(chunks)
        self.assertIn("不存在", error)


class TestChunkIndexGlobalUnique(unittest.TestCase):
    """A1: 多文件抽取时 chunk_index 必须全局唯一，否则会覆盖丢失三元组"""

    def test_multi_file_chunk_index_unique(self):
        """两个文件的 chunk_index 不应都从 0 开始重复"""
        from utils.file_manager import FileInfo, file_manager

        f1 = FileInfo(id="f1", name="a.txt", path="/tmp/a.txt",
                      chunks=["a1", "a2", "a3"], chunks_count=3, status="parsed")
        f2 = FileInfo(id="f2", name="b.txt", path="/tmp/b.txt",
                      chunks=["b1", "b2"], chunks_count=2, status="parsed")
        file_manager._files = [f1, f2]

        chunks = file_manager.get_all_chunks()
        indices = [c[2] for c in chunks]

        # 全局唯一连续递增，不出现重复的 0,1
        self.assertEqual(indices, [0, 1, 2, 3, 4])
        self.assertEqual(len(set(indices)), len(indices))
        # 文件归属正确
        self.assertEqual([c[0] for c in chunks], ["f1", "f1", "f1", "f2", "f2"])

    def test_resume_global_index_stable(self):
        """续传时全局索引与已完成记录对齐，不会误判跳过"""
        from utils.file_manager import FileInfo, file_manager
        from utils.progress_tracker import progress_tracker

        f1 = FileInfo(id="f1", name="a.txt", path="/tmp/a.txt",
                      chunks=["a1", "a2"], chunks_count=2, status="parsed")
        f2 = FileInfo(id="f2", name="b.txt", path="/tmp/b.txt",
                      chunks=["b1"], chunks_count=1, status="parsed")
        file_manager._files = [f1, f2]
        chunks = file_manager.get_all_chunks()  # 全局索引 0,1,2

        progress_tracker.start(total_files=2, total_chunks=3)
        # 完成第一个文件的两块（全局 0,1）
        progress_tracker.update_chunk_start(0, "a.txt", "f1")
        progress_tracker.update_chunk_complete(0, [], 0)
        progress_tracker.update_chunk_start(1, "a.txt", "f1")
        progress_tracker.update_chunk_complete(1, [], 0)

        pending = progress_tracker.get_pending_chunks()
        # 仅全局索引 2（f2 的块）待处理，不会把 f2 的块误判为已完成
        self.assertEqual(pending, [2])


class TestExtractorJsonRobustness(unittest.TestCase):
    """A2: 含冒号等合法字符的 JSON 不被正则破坏，解析失败有日志"""

    def test_colon_in_value_not_corrupted(self):
        """值中的时间/URL 冒号不被破坏（旧正则会损坏并静默丢弃）"""
        from utils.extractor import _parse_llm_response

        response = (
            '{"triples": [{"head": "A", "head_type": "T", '
            '"head_properties": {"time": "12:30:00", "url": "https://x.com/v1"}, '
            '"relation": "r", "tail": "B", "tail_type": "T", "tail_properties": {}}]}'
        )
        result = _parse_llm_response(response)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].head_properties["time"], "12:30:00")
        self.assertEqual(result[0].head_properties["url"], "https://x.com/v1")

    def test_trailing_comma_repaired(self):
        from utils.extractor import _parse_llm_response

        response = '{"triples": [{"head":"A","head_type":"T","head_properties":{},"relation":"r","tail":"B","tail_type":"T","tail_properties":{},}],}'
        self.assertEqual(len(_parse_llm_response(response)), 1)

    def test_unquoted_keys_repaired(self):
        from utils.extractor import _parse_llm_response

        response = '{triples: [{head: "A", head_type: "T", head_properties: {}, relation: "r", tail: "B", tail_type: "T", tail_properties: {}}]}'
        self.assertEqual(len(_parse_llm_response(response)), 1)

    def test_comments_stripped(self):
        from utils.extractor import _parse_llm_response

        response = (
            '{\n  "triples": [ // 注释\n'
            '    {"head":"A","head_type":"T","head_properties":{},'
            '"relation":"r","tail":"B","tail_type":"T","tail_properties":{}}\n  ]\n}'
        )
        self.assertEqual(len(_parse_llm_response(response)), 1)

    def test_malformed_returns_empty(self):
        from utils.extractor import _parse_llm_response

        self.assertEqual(_parse_llm_response("not json at all"), [])
        self.assertEqual(_parse_llm_response(""), [])


class TestCypherPropertyKeySanitization(unittest.TestCase):
    """A4: 属性键来自 LLM 输出，必须清洗以防 Cypher 注入"""

    def test_malicious_property_key_neutralized(self):
        from utils.cypher_generator import generate_cypher_safe
        from utils.extractor import KnowledgeGraphTriple

        triple = KnowledgeGraphTriple(
            head="A", head_type="Person",
            head_properties={"name) DETACH DELETE h//": "evil"},
            relation="knows", tail="B", tail_type="Person", tail_properties={},
        )
        queries = generate_cypher_safe([triple])
        q = queries[0].query

        # 恶意键被清洗为单个合法标识符 nameDETACHDELETEh（破坏性字符 ) / 空格已移除）
        self.assertNotIn("name)", q)
        # 不存在可执行的 DETACH DELETE 子句（命令需独立词，此处仅作为标识符的一部分）
        self.assertNotIn(" DETACH DELETE", q)
        self.assertIn("nameDETACHDELETEh", q)
        # 属性值通过参数传递，不拼入查询串
        self.assertNotIn("evil", q)


class TestSanitizeStringNoCorruption(unittest.TestCase):
    """A8: 参数化值不再被转义引号损坏"""

    def test_apostrophe_preserved(self):
        from utils.cypher_generator import sanitize_string
        self.assertEqual(sanitize_string("O'Brien"), "O'Brien")

    def test_control_chars_removed(self):
        from utils.cypher_generator import sanitize_string
        self.assertEqual(sanitize_string("a\x00b\x01c"), "abc")

    def test_empty_input(self):
        from utils.cypher_generator import sanitize_string
        self.assertEqual(sanitize_string(""), "")
        self.assertEqual(sanitize_string(None), "")


class TestInvokeWithRetry(unittest.TestCase):
    """A5: 瞬时异常重试，非瞬时异常立即抛出"""

    def test_transient_then_success(self):
        import utils.extractor as ex
        from utils.extractor import _invoke_with_retry

        class FakeLLM:
            def __init__(self):
                self.calls = 0

            def invoke(self, prompt):
                self.calls += 1
                if self.calls < 3:
                    raise TimeoutError("simulated timeout")
                return type("R", (), {"content": "ok"})()

        # 屏蔽真实 sleep，避免拖慢测试
        real_sleep = ex.time.sleep
        ex.time.sleep = lambda s: None
        try:
            llm = FakeLLM()
            r = _invoke_with_retry(llm, "p", max_retries=3)
            self.assertEqual(r.content, "ok")
            self.assertEqual(llm.calls, 3)
        finally:
            ex.time.sleep = real_sleep

    def test_non_transient_raises_immediately(self):
        import utils.extractor as ex
        from utils.extractor import _invoke_with_retry, ExtractionError

        class FakeLLM:
            def __init__(self):
                self.calls = 0

            def invoke(self, prompt):
                self.calls += 1
                raise ValueError("bad config")  # 非瞬时

        real_sleep = ex.time.sleep
        ex.time.sleep = lambda s: None
        try:
            llm = FakeLLM()
            with self.assertRaises(ValueError):
                _invoke_with_retry(llm, "p", max_retries=3)
            self.assertEqual(llm.calls, 1)  # 未重试
        finally:
            ex.time.sleep = real_sleep


class TestUploadedFileDeletion(unittest.TestCase):
    """A7: 移除上传文件时删除磁盘文件，但不删文件夹导入的原始文件"""

    def test_remove_file_deletes_upload_from_disk(self):
        from utils.file_manager import FileInfo, file_manager
        from utils import state_manager as sm

        upload_dir = sm.state_manager.upload_dir
        p = upload_dir / "test_file.txt"
        p.write_text("hello", encoding="utf-8")

        fi = FileInfo(id="f1", name="test_file.txt", path=str(p),
                      source="upload", chunks=["hello"], chunks_count=1, status="parsed")
        file_manager._files = [fi]
        self.assertTrue(p.exists())

        ok = file_manager.remove_file("f1")
        self.assertTrue(ok)
        self.assertFalse(p.exists())

    def test_folder_file_not_deleted(self):
        """文件夹导入的原始文件不被删除"""
        import tempfile
        from utils.file_manager import FileInfo, file_manager

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
            tf.write(b"data")
            tf_path = tf.name
        try:
            fi = FileInfo(id="ff", name="x.txt", path=tf_path, source="folder",
                          original_path=tf_path, chunks=["data"], chunks_count=1, status="parsed")
            file_manager._files = [fi]
            file_manager.remove_file("ff")
            self.assertTrue(Path(tf_path).exists())  # 原始文件仍在
        finally:
            Path(tf_path).unlink(missing_ok=True)

    def test_clear_all_deletes_uploads(self):
        from utils.file_manager import FileInfo, file_manager
        from utils import state_manager as sm

        upload_dir = sm.state_manager.upload_dir
        p = upload_dir / "c.txt"
        p.write_text("c", encoding="utf-8")
        fi = FileInfo(id="fc", name="c.txt", path=str(p), source="upload",
                      chunks=["c"], chunks_count=1, status="parsed")
        file_manager._files = [fi]

        file_manager.clear_all()
        self.assertFalse(p.exists())


class TestExecuteCypherReturnContract(unittest.TestCase):
    """A3: execute_cypher 必须如实返回成功/失败，调用方据此判断"""

    def test_returns_false_on_session_failure(self):
        from utils.neo4j_manager import Neo4jManager
        from utils.cypher_generator import CypherQuery

        mgr = Neo4jManager("bolt://x", "u", "p", max_retries=0)

        class FakeSession:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def run(self, *a, **k):
                raise RuntimeError("connection dead")

        class FakeDriver:
            def session(self):
                return FakeSession()

            def close(self):
                pass

        mgr._driver = FakeDriver()
        result = mgr.execute_cypher([CypherQuery(query="RETURN 1", parameters={})])
        self.assertFalse(result)

    def test_returns_true_on_success(self):
        from utils.neo4j_manager import Neo4jManager
        from utils.cypher_generator import CypherQuery

        mgr = Neo4jManager("bolt://x", "u", "p", max_retries=0)

        class FakeSession:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def run(self, *a, **k):
                pass

        class FakeDriver:
            def session(self):
                return FakeSession()

            def close(self):
                pass

        mgr._driver = FakeDriver()
        result = mgr.execute_cypher([CypherQuery(query="RETURN 1", parameters={})])
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()