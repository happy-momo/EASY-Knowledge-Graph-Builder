"""
抽取运行组件（后台线程 + fragment 轮询）

由于抽取工作线程不调用任何 st.*，需要用 st.fragment 定时刷新界面，
展示实时进度并渲染可点击的「终止任务」按钮。

职责划分：
  * 本组件只负责"正在运行"时的实时进度 + 终止按钮渲染。
  * 任务结束后的收尾（恢复/已抽结果/跳转）由 app.py 主脚本根据
    job_manager.get_last_result() 处理，避免 fragment 内嵌触发歧义。
"""

import streamlit as st
from typing import Optional

from utils.progress_tracker import progress_tracker
from utils.job_manager import job_manager
from components.process_display import (
    render_progress_indicator,
    render_recent_triples,
)


@st.fragment(run_every=1.0)
def render_processing_fragment():
    """
    渲染抽取实时进度页面（每秒自动刷新）

    - 运行中：进度条 + 指标 + 最近三元组 + 「终止任务」按钮
    - 终止中：显示"正在终止当前分块…"
    - 已结束：把结果写入 session_state 并强制全量重跑，交给主脚本收尾
    """
    progress = progress_tracker.get_progress()

    # ---- 实时进度 ----
    render_progress_indicator(progress)
    if progress.current_file:
        st.caption(f"当前处理: {progress.current_file} (分块 {progress.current_chunk + 1 if progress.current_chunk is not None else '-'})")
    if progress.chunk_progress:
        render_recent_triples(progress.chunk_progress[-5:])

    # ---- 状态分支 ----
    if job_manager.is_running():
        if job_manager.is_pausing():
            st.warning("正在终止当前分块… 结束当前调用后将保存进度，请稍候。")
        else:
            _render_abort_button()

    elif job_manager.is_done():
        # 任务已结束：抑制启动恢复提示，把收尾交给主脚本 render_process_step，
        # 触发全量重跑读取 job_manager.get_last_result() 决策下一步。
        st.session_state['_resume_shown'] = True
        st.session_state['_pending_resume'] = False
        st.rerun()

    # 其它情况（is_idle）不应渲染本 fragment，由主脚本处理


def _render_abort_button():
    """渲染终止任务按钮（醒目红色）"""
    if st.button(
        "⏹ 终止任务",
        type="secondary",
        use_container_width=True,
        help="终止后已处理的分块进度会保存，可稍后恢复继续，不会重复录入",
    ):
        job_manager.request_abort()
        st.rerun()

    st.caption(
        "<span style='color: var(--text-muted);'>终止后进度已保存，可恢复继续，未处理分块不会被重复录入。</span>",
        unsafe_allow_html=True,
    )