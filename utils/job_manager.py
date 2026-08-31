"""
抽取任务生命周期管理器（单例）

在 Streamlit 单会话单脚本执行的模型下，同步循环会阻塞整个界面，
导致"卡住时终止按钮点不动"。本模块把阻塞的抽取逻辑放入后台线程，
配合 st.fragment 定时刷新，实现可随时终止的任务。

并发安全约定：
  * 后台工作线程绝不调用任何 st.*。
  * UI 通过共享的 threading.Event 通知工作线程终止。
  * 工作线程结束后把结果写入模块级 job 记录，UI 据此决策下一步。
"""

import threading
import logging
from typing import Optional, Callable, Dict, Any

logger = logging.getLogger(__name__)


class JobManager:
    """抽取任务生命周期管理 - 单例"""

    _instance = None
    _instance_lock = threading.Lock()

    # 任务状态
    IDLE = "idle"          # 无任务
    RUNNING = "running"    # 抽取中
    PAUSING = "pausing"    # 已收到终止请求，等待当前分块结束
    DONE = "done"          # 工作线程已结束（成功/失败/被终止）

    # 结果类型
    RESULT_FINISHED = "finished"   # 全部完成
    RESULT_ABORTED = "aborted"     # 被用户终止（进度已保存）
    RESULT_ERROR = "error"         # 出错

    def __new__(cls):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        """初始化任务状态"""
        self._thread: Optional[threading.Thread] = None
        self._abort_event = threading.Event()
        self._state = self.IDLE
        self._result_type = None
        self._result_detail = ""
        self._state_lock = threading.Lock()

    # ==================== 启动/终止 ====================

    def start(self, target: Callable, *, resume: bool = False, **kwargs):
        """
        启动后台抽取任务

        Args:
            target: 工作线程入口函数（返回时调用 job.set_result）
            resume: 是否为续跑
            **kwargs: 传给 target 的参数字段（不含 job，job 会自动注入）
        """
        with self._state_lock:
            if self._thread and self._thread.is_alive():
                logger.warning("已有任务在运行，忽略重复启动")
                return False

            self._abort_event = threading.Event()
            self._state = self.RUNNING
            self._result_type = None
            self._result_detail = ""

            self._thread = threading.Thread(
                target=target,
                kwargs={**kwargs, "job": self, "resume": resume},
                daemon=True,
                name="extraction-worker"
            )
            self._thread.start()
            logger.info("抽取任务已启动 (resume=%s)", resume)
            return True

    def request_abort(self):
        """请求终止：设置事件，工作线程在下一个迭代点退出"""
        self._abort_event.set()
        with self._state_lock:
            if self._state == self.RUNNING:
                self._state = self.PAUSING
        logger.info("已请求终止抽取任务")

    # ==================== 状态查询 ====================

    def is_running(self) -> bool:
        """是否正在运行（含终止等待期）"""
        return (
            self._thread is not None
            and self._thread.is_alive()
            and self._state in (self.RUNNING, self.PAUSING)
        )

    def is_pausing(self) -> bool:
        """是否正处于终止等待期"""
        return self._state == self.PAUSING and self._thread is not None and self._thread.is_alive()

    def is_done(self) -> bool:
        """是否已结束（成功/失败/被终止）"""
        return self._state == self.DONE and self._thread is not None and not self._thread.is_alive()

    def is_idle(self) -> bool:
        """是否空闲（无任务）"""
        return self._state == self.IDLE and self._thread is None

    def abort_requested(self) -> bool:
        """终止事件是否已触发"""
        return self._abort_event.is_set()

    def get_state(self) -> str:
        """获取任务状态字符串"""
        return self._state

    # ==================== 结果记录（工作线程调用） ====================

    def mark_finished(self):
        """正常完成（工作线程调用）"""
        self._finalize(self.RESULT_FINISHED, "")

    def mark_aborted(self):
        """被用户终止（工作线程调用）"""
        self._finalize(self.RESULT_ABORTED, "已终止，进度已保存")

    def mark_error(self, detail: str = ""):
        """出错（工作线程调用）"""
        self._finalize(self.RESULT_ERROR, detail)

    def _finalize(self, result_type: str, detail: str):
        """统一收尾：记录结果并置 DONE"""
        with self._state_lock:
            self._state = self.DONE
            self._result_type = result_type
            self._result_detail = detail
        logger.info("抽取任务结束: %s - %s", result_type, detail)

    def get_last_result(self) -> Optional[Dict[str, Any]]:
        """获取最近一次任务结果（供 UI 决策）"""
        if self._state != self.DONE:
            return None
        return {
            "result": self._result_type,
            "detail": self._result_detail,
        }

    def reset(self):
        """清空任务引用（供"重新开始"）"""
        with self._state_lock:
            self._thread = None
            self._abort_event = threading.Event()
            self._state = self.IDLE
            self._result_type = None
            self._result_detail = ""


# 全局单例
job_manager = JobManager()