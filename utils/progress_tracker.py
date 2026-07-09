"""
进度追踪器

支持处理状态的持久化，实现断点续传功能。
"""

from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional
from enum import Enum
import time
from datetime import datetime

from utils.state_manager import state_manager
import os


class ProcessStatus(Enum):
    """处理状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ChunkProgress:
    """单个分块的处理进度"""
    chunk_index: int
    file_name: str
    file_id: str
    status: str  # pending, processing, completed, error, skipped
    triples_count: int = 0
    triples: List[Dict] = field(default_factory=list)
    error_message: str = None
    start_time: float = None
    end_time: float = None


@dataclass
class ProcessProgress:
    """整体处理进度"""
    status: str = ProcessStatus.IDLE.value
    total_files: int = 0
    total_chunks: int = 0
    processed_chunks: int = 0
    total_triples: int = 0
    current_file: str = None
    current_file_id: str = None
    current_chunk: int = None
    start_time: float = None
    end_time: float = None
    chunk_progress: List[Dict] = field(default_factory=list)

    def __post_init__(self):
        if self.chunk_progress is None:
            self.chunk_progress = []

    @property
    def progress_percent(self) -> float:
        """计算进度百分比"""
        if self.total_chunks == 0:
            return 0
        return round(self.processed_chunks / self.total_chunks * 100, 1)

    @property
    def elapsed_time(self) -> float:
        """计算已耗时"""
        if self.start_time is None:
            return 0
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def elapsed_time_str(self) -> str:
        """格式化已耗时"""
        elapsed = self.elapsed_time
        if elapsed < 60:
            return f"{int(elapsed)}秒"
        elif elapsed < 3600:
            minutes = int(elapsed / 60)
            seconds = int(elapsed % 60)
            return f"{minutes}分{seconds}秒"
        else:
            hours = int(elapsed / 3600)
            minutes = int((elapsed % 3600) / 60)
            return f"{hours}时{minutes}分"

    def get_remaining_chunks(self) -> List[int]:
        """获取未处理的分块索引列表"""
        processed = {cp['chunk_index'] for cp in self.chunk_progress
                     if cp['status'] == 'completed'}
        return [i for i in range(self.total_chunks) if i not in processed]


class ProgressTracker:
    """进度追踪器 - 支持断点续传"""

    def __init__(self):
        self._progress = self._load_progress()

    def _load_progress(self) -> ProcessProgress:
        """从持久化存储加载进度"""
        data = state_manager.load('progress', {})
        if data:
            # 检查状态是否为非IDLE状态（只有RUNNING/PAUSED/ERROR才需要恢复）
            status = data.get('status', ProcessStatus.IDLE.value)
            if status == ProcessStatus.IDLE.value:
                # 如果是IDLE状态，清除进度文件并返回空进度
                state_manager.clear('progress')
                return ProcessProgress()

            # 处理chunk_progress可能为None的情况
            if data.get('chunk_progress') is None:
                data['chunk_progress'] = []
            return ProcessProgress(**data)
        return ProcessProgress()

    def save(self):
        """持久化当前进度"""
        state_manager.save('progress', asdict(self._progress))

    def reset(self):
        """重置进度"""
        self._progress = ProcessProgress()
        self.save()

    def start(self, total_files: int, total_chunks: int):
        """
        开始处理

        Args:
            total_files: 总文件数
            total_chunks: 总分块数
        """
        self._progress.status = ProcessStatus.RUNNING.value
        self._progress.total_files = total_files
        self._progress.total_chunks = total_chunks
        self._progress.start_time = time.time()
        self._progress.processed_chunks = 0
        self._progress.total_triples = 0
        self._progress.chunk_progress = []
        self.save()

    def update_chunk_start(self, chunk_index: int, file_name: str, file_id: str):
        """
        开始处理一个分块

        Args:
            chunk_index: 分块索引
            file_name: 文件名
            file_id: 文件ID
        """
        self._progress.current_file = file_name
        self._progress.current_file_id = file_id
        self._progress.current_chunk = chunk_index

        chunk_prog = {
            'chunk_index': chunk_index,
            'file_name': file_name,
            'file_id': file_id,
            'status': 'processing',
            'triples_count': 0,
            'triples': [],
            'start_time': time.time()
        }
        self._progress.chunk_progress.append(chunk_prog)
        self.save()

    def update_chunk_complete(self, chunk_index: int, triples: List[Dict],
                               triples_count: int):
        """
        分块处理完成

        Args:
            chunk_index: 分块索引
            triples: 抽取的三元组列表
            triples_count: 三元组数量
        """
        # 更新分块进度
        for cp in self._progress.chunk_progress:
            if cp['chunk_index'] == chunk_index:
                cp['status'] = 'completed'
                cp['triples_count'] = triples_count
                cp['triples'] = triples
                cp['end_time'] = time.time()
                break

        # 更新整体进度
        self._progress.processed_chunks += 1
        self._progress.total_triples += triples_count
        self.save()

    def update_chunk_error(self, chunk_index: int, error_message: str):
        """
        分块处理出错

        Args:
            chunk_index: 分块索引
            error_message: 错误信息
        """
        for cp in self._progress.chunk_progress:
            if cp['chunk_index'] == chunk_index:
                cp['status'] = 'error'
                cp['error_message'] = error_message
                cp['end_time'] = time.time()
                break

        self._progress.processed_chunks += 1
        self.save()

    def update_chunk_skip(self, chunk_index: int, reason: str = "已处理"):
        """
        跳过分块（用于断点续传）

        Args:
            chunk_index: 分块索引
            reason: 跳过原因
        """
        for cp in self._progress.chunk_progress:
            if cp['chunk_index'] == chunk_index:
                cp['status'] = 'skipped'
                cp['error_message'] = reason
                break

        self._progress.processed_chunks += 1
        self.save()

    def pause(self):
        """暂停处理"""
        self._progress.status = ProcessStatus.PAUSED.value
        self.save()

    def resume(self):
        """恢复处理"""
        self._progress.status = ProcessStatus.RUNNING.value
        self.save()

    def complete(self):
        """处理完成"""
        self._progress.status = ProcessStatus.COMPLETED.value
        self._progress.end_time = time.time()
        self.save()
        # 完成后重置为IDLE，避免下次启动时检测到未完成的任务
        self._progress.status = ProcessStatus.IDLE.value
        self.save()

    def error(self, message: str = None):
        """处理出错"""
        self._progress.status = ProcessStatus.ERROR.value
        if message:
            # 记录错误信息到最后一个分块
            if self._progress.chunk_progress:
                self._progress.chunk_progress[-1]['error_message'] = message
        self.save()

    def get_progress(self) -> ProcessProgress:
        """获取当前进度"""
        return self._progress

    def can_resume(self) -> bool:
        """是否可以恢复处理"""
        if self._is_progress_stale():
            return False
        return (
            self._progress.status in (
                ProcessStatus.RUNNING.value,
                ProcessStatus.PAUSED.value,
                ProcessStatus.ERROR.value
            )
            and self._progress.processed_chunks < self._progress.total_chunks
            and self._progress.total_chunks > 0
        )

    def _is_progress_stale(self) -> bool:
        """检查进度数据是否过时（超过5分钟）"""
        try:
            data_dir = state_manager.data_dir
            progress_file = data_dir / "progress.json"
            if not progress_file.exists():
                return True
            mtime = os.path.getmtime(progress_file)
            return (time.time() - mtime) > 300  # 5 minutes
        except (OSError, AttributeError):
            return True

    def get_pending_chunks(self) -> List[int]:
        """获取待处理的分块索引"""
        return [
            i for i in range(self._progress.total_chunks)
            if not any(cp['chunk_index'] == i and cp['status'] == 'completed'
                       for cp in self._progress.chunk_progress)
        ]

    def get_all_triples(self) -> List[Dict]:
        """获取所有已抽取的三元组"""
        all_triples = []
        for cp in self._progress.chunk_progress:
            if cp['status'] == 'completed' and cp.get('triples'):
                all_triples.extend(cp['triples'])
        return all_triples

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        completed_chunks = [
            cp for cp in self._progress.chunk_progress
            if cp['status'] == 'completed'
        ]
        error_chunks = [
            cp for cp in self._progress.chunk_progress
            if cp['status'] == 'error'
        ]

        avg_triples_per_chunk = (
            self._progress.total_triples / len(completed_chunks)
            if completed_chunks else 0
        )

        return {
            "total_files": self._progress.total_files,
            "total_chunks": self._progress.total_chunks,
            "processed_chunks": self._progress.processed_chunks,
            "completed_chunks": len(completed_chunks),
            "error_chunks": len(error_chunks),
            "total_triples": self._progress.total_triples,
            "avg_triples_per_chunk": round(avg_triples_per_chunk, 2),
            "progress_percent": self._progress.progress_percent,
            "elapsed_time": self._progress.elapsed_time_str,
            "status": self._progress.status
        }


# 全局进度追踪器实例
progress_tracker = ProgressTracker()