"""
文件管理器

支持文件的增删改查、文件夹扫描、状态更新等操作。
"""

from dataclasses import dataclass, asdict, field, fields
from typing import List, Optional, Dict, Any
from pathlib import Path
import os
import uuid
from datetime import datetime

from utils.state_manager import state_manager


@dataclass
class FileInfo:
    """文件信息数据类"""
    id: str  # 唯一标识
    name: str  # 文件名
    path: str  # 存储路径
    original_path: str = ""  # 原始路径（文件夹导入时）
    size: int = 0  # 文件大小（字节）
    type: str = ""  # 文件类型 (.pdf, .docx, .xlsx)
    chunks_count: int = 0  # 分块数量
    chunks: List[str] = field(default_factory=list)  # 分块内容
    status: str = "pending"  # pending, parsed, processing, completed, error
    error_message: str = ""
    source: str = "upload"  # upload 或 folder
    folder_path: str = ""  # 如果来自文件夹
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    @property
    def size_display(self) -> str:
        """显示友好的文件大小"""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        else:
            return f"{self.size / (1024 * 1024):.1f} MB"

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'FileInfo':
        """从字典创建（容错：忽略未知键，缺失键使用默认值）"""
        valid_fields = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


class FileManager:
    """文件管理器"""

    SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.txt']

    def __init__(self):
        self._files: List[FileInfo] = self._load_files()

    def _load_files(self) -> List[FileInfo]:
        """从持久化存储加载文件列表"""
        data = state_manager.load('files', [])
        return [FileInfo.from_dict(f) for f in data]

    def _save_files(self):
        """保存文件列表到持久化存储"""
        state_manager.save('files', [f.to_dict() for f in self._files])

    def _generate_id(self) -> str:
        """生成唯一ID"""
        return str(uuid.uuid4())[:8]

    def add_uploaded_file(self, uploaded_file, chunks: List[str] = None) -> FileInfo:
        """
        添加上传的文件

        Args:
            uploaded_file: Streamlit上传的文件对象
            chunks: 已解析的分块列表

        Returns:
            文件信息对象
        """
        # 保存文件到本地
        file_path = state_manager.save_uploaded_file(uploaded_file)

        file_info = FileInfo(
            id=self._generate_id(),
            name=uploaded_file.name,
            path=file_path,
            original_path="",
            size=uploaded_file.size,
            type=Path(uploaded_file.name).suffix.lower(),
            chunks_count=len(chunks) if chunks else 0,
            chunks=chunks if chunks else [],
            status="parsed" if chunks else "pending",
            source="upload"
        )

        self._files.append(file_info)
        self._save_files()
        return file_info

    def add_local_file(self, file_path: str, chunks: List[str] = None,
                       source: str = "folder", folder_path: str = "") -> FileInfo:
        """
        添加本地文件（用于文件夹导入）

        Args:
            file_path: 文件路径
            chunks: 已解析的分块列表
            source: 来源类型
            folder_path: 文件夹路径

        Returns:
            文件信息对象
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        file_info = FileInfo(
            id=self._generate_id(),
            name=path.name,
            path=str(path),
            original_path=str(path),
            size=path.stat().st_size,
            type=path.suffix.lower(),
            chunks_count=len(chunks) if chunks else 0,
            chunks=chunks if chunks else [],
            status="parsed" if chunks else "pending",
            source=source,
            folder_path=folder_path
        )

        self._files.append(file_info)
        self._save_files()
        return file_info

    def remove_file(self, file_id: str) -> bool:
        """
        移除文件

        Args:
            file_id: 文件ID

        Returns:
            是否移除成功
        """
        initial_count = len(self._files)
        self._files = [f for f in self._files if f.id != file_id]

        if len(self._files) < initial_count:
            self._save_files()
            return True
        return False

    def remove_by_folder(self, folder_path: str) -> int:
        """
        移除来自指定文件夹的所有文件

        Args:
            folder_path: 文件夹路径

        Returns:
            移除的文件数量
        """
        initial_count = len(self._files)
        self._files = [f for f in self._files if f.folder_path != folder_path]
        removed_count = initial_count - len(self._files)

        if removed_count > 0:
            self._save_files()
        return removed_count

    def clear_all(self) -> int:
        """
        清空所有文件

        Returns:
            清空的文件数量
        """
        count = len(self._files)
        self._files = []
        self._save_files()
        return count

    def get_file(self, file_id: str) -> Optional[FileInfo]:
        """
        获取单个文件

        Args:
            file_id: 文件ID

        Returns:
            文件信息或None
        """
        for f in self._files:
            if f.id == file_id:
                return f
        return None

    def get_files(self) -> List[FileInfo]:
        """获取所有文件"""
        return self._files

    def get_files_by_status(self, status: str) -> List[FileInfo]:
        """
        按状态获取文件

        Args:
            status: 文件状态

        Returns:
            文件列表
        """
        return [f for f in self._files if f.status == status]

    def get_pending_files(self) -> List[FileInfo]:
        """获取待处理文件"""
        return [f for f in self._files if f.status in ('pending', 'parsed')]

    def update_file_status(self, file_id: str, status: str,
                           chunks_count: int = None,
                           chunks: List[str] = None,
                           error_message: str = None):
        """
        更新文件状态

        Args:
            file_id: 文件ID
            status: 新状态
            chunks_count: 分块数量
            chunks: 分块内容
            error_message: 错误信息
        """
        for f in self._files:
            if f.id == file_id:
                f.status = status
                f.updated_at = datetime.now().isoformat()
                if chunks_count is not None:
                    f.chunks_count = chunks_count
                if chunks is not None:
                    f.chunks = chunks
                if error_message is not None:
                    f.error_message = error_message
                break
        self._save_files()

    def update_file_chunks(self, file_id: str, chunks: List[str]):
        """
        更新文件的分块内容

        Args:
            file_id: 文件ID
            chunks: 分块列表
        """
        for f in self._files:
            if f.id == file_id:
                f.chunks = chunks
                f.chunks_count = len(chunks)
                f.status = "parsed"
                f.updated_at = datetime.now().isoformat()
                break
        self._save_files()

    def get_statistics(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计字典
        """
        total_size = sum(f.size for f in self._files)
        total_chunks = sum(f.chunks_count for f in self._files)

        status_counts = {}
        for status in ['pending', 'parsed', 'processing', 'completed', 'error']:
            status_counts[status] = len([f for f in self._files if f.status == status])

        return {
            "total_files": len(self._files),
            "total_size": total_size,
            "total_size_display": self._format_size(total_size),
            "total_chunks": total_chunks,
            "status_counts": status_counts,
            "sources": {
                "upload": len([f for f in self._files if f.source == 'upload']),
                "folder": len([f for f in self._files if f.source == 'folder'])
            }
        }

    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"

    def get_all_chunks(self) -> List[tuple]:
        """
        获取所有文件的分块（用于处理）

        Returns:
            (file_id, file_name, chunk_index, chunk_content) 元组列表
        """
        all_chunks = []
        for file in self._files:
            if file.chunks:
                for i, chunk in enumerate(file.chunks):
                    all_chunks.append((file.id, file.name, i, chunk))
        return all_chunks


# 全局文件管理器实例
file_manager = FileManager()