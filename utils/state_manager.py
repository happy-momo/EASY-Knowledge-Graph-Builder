"""
持久化状态管理器

解决Streamlit刷新后session_state丢失的问题，通过JSON文件持久化关键状态。
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, List
import threading
import hashlib
from datetime import datetime


class StateManager:
    """持久化状态管理器 - 单例模式"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_storage()
        return cls._instance

    def _init_storage(self):
        """初始化存储目录"""
        # 获取项目根目录
        project_root = Path(__file__).parent.parent
        self.data_dir = project_root / ".data" / "session"
        self.upload_dir = project_root / ".data" / "uploads"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # 状态文件路径
        self.config_file = self.data_dir / "config.json"
        self.files_file = self.data_dir / "files.json"
        self.progress_file = self.data_dir / "progress.json"
        self.triples_file = self.data_dir / "triples.json"
        self.review_file = self.data_dir / "review.json"

    def save(self, key: str, data: Any) -> bool:
        """
        保存状态到文件

        Args:
            key: 状态键名 (config, files, progress, triples, review)
            data: 要保存的数据

        Returns:
            是否保存成功
        """
        try:
            file_path = self.data_dir / f"{key}.json"

            # 添加元数据
            save_data = {
                "data": data,
                "saved_at": datetime.now().isoformat(),
                "version": "v2"
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving state {key}: {e}")
            return False

    def load(self, key: str, default: Any = None) -> Any:
        """
        从文件加载状态

        Args:
            key: 状态键名
            default: 默认值

        Returns:
            加载的数据或默认值
        """
        try:
            file_path = self.data_dir / f"{key}.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    # 返回实际数据部分
                    return saved_data.get("data", default)
            return default
        except Exception as e:
            print(f"Error loading state {key}: {e}")
            return default

    def clear(self, key: str = None):
        """
        清除状态

        Args:
            key: 要清除的键名，None表示清除所有
        """
        try:
            if key:
                file_path = self.data_dir / f"{key}.json"
                if file_path.exists():
                    file_path.unlink()
            else:
                for f in self.data_dir.glob("*.json"):
                    f.unlink()
        except Exception as e:
            print(f"Error clearing state: {e}")

    def save_uploaded_file(self, uploaded_file, custom_name: str = None) -> str:
        """
        保存上传的文件

        Args:
            uploaded_file: Streamlit上传的文件对象
            custom_name: 自定义文件名

        Returns:
            保存的文件路径
        """
        try:
            # 生成唯一文件名避免冲突
            if custom_name:
                filename = custom_name
            else:
                # 使用hash生成唯一标识
                file_hash = hashlib.md5(
                    (uploaded_file.name + str(datetime.now())).encode()
                ).hexdigest()[:8]
                filename = f"{file_hash}_{uploaded_file.name}"

            file_path = self.upload_dir / filename

            # 保存文件内容
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())

            return str(file_path)
        except Exception as e:
            print(f"Error saving uploaded file: {e}")
            return None

    def get_uploaded_file_path(self, filename: str) -> Optional[str]:
        """
        获取已上传文件的路径

        Args:
            filename: 文件名

        Returns:
            文件路径或None
        """
        file_path = self.upload_dir / filename
        if file_path.exists():
            return str(file_path)
        return None

    def delete_uploaded_file(self, filename: str) -> bool:
        """
        删除上传的文件

        Args:
            filename: 文件名

        Returns:
            是否删除成功
        """
        try:
            file_path = self.upload_dir / filename
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting uploaded file: {e}")
            return False

    def list_uploaded_files(self) -> List[str]:
        """
        列出所有上传的文件

        Returns:
            文件名列表
        """
        return [f.name for f in self.upload_dir.iterdir() if f.is_file()]

    def clear_uploaded_files(self):
        """清除所有上传的文件"""
        try:
            for f in self.upload_dir.iterdir():
                if f.is_file():
                    f.unlink()
        except Exception as e:
            print(f"Error clearing uploaded files: {e}")

    def get_state_summary(self) -> Dict:
        """
        获取当前状态摘要

        Returns:
            状态摘要字典
        """
        summary = {
            "has_config": self.config_file.exists(),
            "has_files": self.files_file.exists(),
            "has_progress": self.progress_file.exists(),
            "uploaded_files_count": len(self.list_uploaded_files())
        }

        # 加载进度状态
        progress = self.load('progress')
        if progress:
            summary["progress_status"] = progress.get('status', 'idle')
            summary["progress_percent"] = progress.get('processed_chunks', 0)
            summary["total_chunks"] = progress.get('total_chunks', 0)

        return summary

    def export_session(self) -> Dict:
        """
        导出当前会话的所有状态

        Returns:
            包含所有状态的字典
        """
        return {
            "config": self.load('config'),
            "files": self.load('files'),
            "progress": self.load('progress'),
            "triples": self.load('triples'),
            "review": self.load('review'),
            "exported_at": datetime.now().isoformat()
        }

    def import_session(self, session_data: Dict):
        """
        导入会话状态

        Args:
            session_data: 会话数据字典
        """
        for key in ['config', 'files', 'progress', 'triples', 'review']:
            if key in session_data:
                self.save(key, session_data[key])


# 全局状态管理器实例
state_manager = StateManager()