"""
测试配置：将所有持久化存储隔离到临时目录。

防止测试读写真实 .data/session/ 和 .data/uploads/，避免：
1. 用户数据被测试覆盖或污染
2. 测试间状态泄漏（顺序依赖）
3. 本地开发环境出现意外的"已上传文件"
"""

import pytest
from pathlib import Path


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path):
    """
    自动应用于所有测试：将 StateManager、FileManager、ProgressTracker
    的存储路径重定向到 pytest 提供的 tmp_path。
    """
    data_dir = tmp_path / "session"
    upload_dir = tmp_path / "uploads"
    data_dir.mkdir()
    upload_dir.mkdir()

    # 重定向 StateManager 单例（data_dir 在 __new__ 时已固定为项目根 .data/）
    from utils import state_manager as sm
    sm.state_manager.data_dir = data_dir
    sm.state_manager.upload_dir = upload_dir
    sm.state_manager.config_file = data_dir / "config.json"
    sm.state_manager.files_file = data_dir / "files.json"
    sm.state_manager.progress_file = data_dir / "progress.json"
    sm.state_manager.triples_file = data_dir / "triples.json"
    sm.state_manager.review_file = data_dir / "review.json"

    # 重置 FileManager 单例（导入时已从真实目录加载，需要清空）
    from utils import file_manager as fm
    fm.file_manager._files = []

    # 重置 ProgressTracker 单例
    from utils import progress_tracker as pt
    pt.progress_tracker._progress = pt.ProcessProgress()

    yield
