"""
步骤导航组件

动态显示当前步骤进度，支持步骤回退。
"""

import streamlit as st
from typing import List, Dict, Optional
from html import escape as html_escape

from config.app_config import STEPS


def render_step_navigation(current_step: int, completed_steps: List[int] = None):
    """
    渲染步骤导航栏

    Args:
        current_step: 当前步骤索引 (0-6)
        completed_steps: 已完成的步骤列表
    """
    if completed_steps is None:
        completed_steps = []

    # 构建导航HTML
    nav_html = '<div class="steps-container"><div class="step-nav">'

    for i, step in enumerate(STEPS):
        # 确定步骤状态
        if i in completed_steps:
            status_class = "completed"
        elif i == current_step:
            status_class = "active"
        else:
            status_class = ""

        # 步骤编号显示
        if status_class == "completed":
            number_display = "✓"
        else:
            number_display = str(i + 1)

        # 标题状态类
        title_class = "active" if i == current_step else ""

        nav_html += f'<div class="step-item" data-step="{i}">'
        nav_html += f'<div class="step-number {status_class}">{number_display}</div>'
        nav_html += f'<div class="step-title {title_class}">{step["title"]}</div>'
        nav_html += f'<div class="step-description">{step["description"]}</div>'
        nav_html += '</div>'

    nav_html += '</div></div>'

    st.markdown(nav_html, unsafe_allow_html=True)


def render_step_title(step_index: int):
    """
    渲染步骤标题

    Args:
        step_index: 步骤索引
    """
    if 0 <= step_index < len(STEPS):
        step = STEPS[step_index]
        st.markdown(
            f'<div class="step-header" style="margin-bottom: 1.5rem;">'
            f'<h2 style="margin-bottom: 0.25rem;">{step["title"]}</h2>'
            f'<p style="color: var(--text-muted); font-size: 0.95rem;">{step["description"]}</p>'
            f'</div>',
            unsafe_allow_html=True
        )


def render_progress_bar(progress_percent: float, message: str = ""):
    """
    渲染进度条

    Args:
        progress_percent: 进度百分比 (0-100)
        message: 进度消息
    """
    progress_value = progress_percent / 100

    st.markdown(
        f'<div class="progress-wrapper" style="margin: 1rem 0;">'
        f'<div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">'
        f'<span style="color: var(--text-secondary); font-size: 0.9rem;">{html_escape(message)}</span>'
        f'<span style="color: var(--accent-primary); font-weight: 600;">{progress_percent:.1f}%</span>'
        f'</div>'
        f'<div class="progress-animated" style="height: 8px; background: var(--bg-secondary); border-radius: 10px; overflow: hidden;">'
        f'<div style="width: {progress_percent}%; height: 100%; background: var(--gradient-primary); border-radius: 10px; transition: width 0.3s ease;"></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )


def render_navigation_buttons(current_step: int, can_proceed: bool = True,
                              show_back: bool = True, show_next: bool = True,
                              next_label: str = "下一步", back_label: str = "上一步"):
    """
    渲染导航按钮

    Args:
        current_step: 当前步骤
        can_proceed: 是否可以继续
        show_back: 是否显示返回按钮
        show_next: 是否显示下一步按钮
        next_label: 下一步按钮文字
        back_label: 返回按钮文字
    """
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if show_back and current_step > 0:
            if st.button(f"← {back_label}", key=f"back_{current_step}", use_container_width=True):
                return "back"

    with col3:
        if show_next and can_proceed:
            if st.button(f"{next_label} →", key=f"next_{current_step}",
                        type="primary", use_container_width=True):
                return "next"

    return None


def get_step_name(step_index: int) -> str:
    """获取步骤名称"""
    if 0 <= step_index < len(STEPS):
        return STEPS[step_index]['name']
    return "unknown"


def get_step_index(step_name: str) -> int:
    """根据名称获取步骤索引"""
    for i, step in enumerate(STEPS):
        if step['name'] == step_name:
            return i
    return 0