"""
步骤导航组件

动态显示当前步骤进度，支持步骤回退和点击跳转。
通过 URL query params (st.query_params) 实现 HTML→Python 通信。
"""

import streamlit as st
import streamlit.components.v1 as components
from typing import List, Dict, Optional

from config.app_config import STEPS


def render_step_navigation(current_step: int, completed_steps: List[int] = None):
    """
    渲染步骤导航栏（可点击跳转）

    已完成或之前的步骤可以点击跳转，当前步骤高亮，未来步骤灰显。

    实现方式：
    1. 用 st.markdown 渲染视觉进度条（HTML+CSS，使用 main.css 样式）
    2. 用 components.html 渲染一个不可见的 JS 层，为进度条步骤绑定点击事件
    3. 点击时 JS 修改父页面 URL 的 ?nav_step=N 参数，触发 Streamlit 刷新
    4. Python 端 handle_step_navigation() 读取 st.query_params 执行跳转

    Args:
        current_step: 当前步骤索引 (0-6)
        completed_steps: 已完成的步骤列表
    """
    if completed_steps is None:
        completed_steps = []

    completed_set = set(completed_steps)

    # ---- 1. 渲染视觉进度条（st.markdown，使用 main.css 样式） ----
    nav_html = '<div class="steps-container"><div class="step-nav">'
    for i, step in enumerate(STEPS):
        if i in completed_set:
            status_class = "completed"
        elif i == current_step:
            status_class = "active"
        else:
            status_class = ""

        number_display = "✓" if status_class == "completed" else str(i + 1)
        title_class = "active" if i == current_step else ""

        # 可点击判断
        can_click = (i in completed_set or i < current_step) and i != current_step
        clickable_attr = 'data-clickable="true"' if can_click else ''

        # 未来步骤灰显
        dim_style = "opacity: 0.45;" if (i > current_step and i not in completed_set) else ""
        cursor_style = "cursor: pointer;" if can_click else "cursor: default;"

        nav_html += (
            f'<div class="step-item" data-step="{i}" {clickable_attr} '
            f'style="{dim_style}{cursor_style}">'
            f'<div class="step-number {status_class}">{number_display}</div>'
            f'<div class="step-title {title_class}">{step["title"]}</div>'
            f'<div class="step-description">{step["description"]}</div>'
            f'</div>'
        )

    nav_html += '</div></div>'
    st.markdown(nav_html, unsafe_allow_html=True)

    # ---- 2. 注入 JS 点击处理（components.html，可执行 <script>） ----
    # 高度为 0，不可见，仅用于执行 JS 绑定点击事件
    js_html = """
<script>
(function() {
    function bindStepClicks() {
        var parent = window.parent.document;
        var items = parent.querySelectorAll('.step-item[data-clickable="true"]');
        items.forEach(function(item) {
            // 避免重复绑定
            if (item.getAttribute('data-nav-bound')) return;
            item.setAttribute('data-nav-bound', 'true');

            item.addEventListener('click', function() {
                var stepIndex = parseInt(this.getAttribute('data-step'));
                // 修改父页面 URL query param，触发 Streamlit 刷新
                var url = new URL(window.parent.location.href);
                url.searchParams.set('nav_step', stepIndex);
                window.parent.location.href = url.toString();
            });
        });
    }

    // 延迟执行，确保 Streamlit DOM 已渲染
    setTimeout(bindStepClicks, 200);
    // MutationObserver 持续监听，处理 Streamlit 重新渲染后的 DOM 更新
    var observer = new MutationObserver(function() {
        setTimeout(bindStepClicks, 100);
    });
    try {
        observer.observe(window.parent.document.body, { childList: true, subtree: true });
    } catch(e) {}
})();
</script>
"""
    components.html(js_html, height=0)


def handle_step_navigation():
    """
    处理步骤导航跳转请求。

    在 app.py 的 main() 中调用，检查 URL query params 中
    是否有 nav_step 参数，如果有则执行跳转并清除参数。

    Returns:
        True 如果执行了跳转，False 否则
    """
    nav_step = st.query_params.get("nav_step")
    if nav_step is not None:
        try:
            target_step = int(nav_step)
            # 清除 query param，避免刷新时重复跳转
            del st.query_params["nav_step"]
            if 0 <= target_step < len(STEPS):
                current = st.session_state.get("current_step", 0)
                if target_step != current:
                    st.session_state.current_step = target_step
                    st.rerun()
                    return True
        except (ValueError, TypeError):
            try:
                del st.query_params["nav_step"]
            except KeyError:
                pass
    return False


def render_step_title(step_index: int):
    """
    渲染步骤标题

    Args:
        step_index: 步骤索引
    """
    if 0 <= step_index < len(STEPS):
        step = STEPS[step_index]
        st.markdown(f"""
        <div class="step-header" style="margin-bottom: 1.5rem;">
            <h2 style="margin-bottom: 0.25rem;">{step['title']}</h2>
            <p style="color: var(--text-muted); font-size: 0.95rem;">{step['description']}</p>
        </div>
        """, unsafe_allow_html=True)


def render_progress_bar(progress_percent: float, message: str = ""):
    """
    渲染进度条

    Args:
        progress_percent: 进度百分比 (0-100)
        message: 进度消息
    """
    progress_value = progress_percent / 100

    st.markdown(f"""
    <div class="progress-wrapper" style="margin: 1rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="color: var(--text-secondary); font-size: 0.9rem;">{message}</span>
            <span style="color: var(--accent-primary); font-weight: 600;">{progress_percent:.1f}%</span>
        </div>
        <div class="progress-animated" style="height: 8px; background: var(--bg-secondary); border-radius: 10px; overflow: hidden;">
            <div style="width: {progress_percent}%; height: 100%; background: var(--gradient-primary); border-radius: 10px; transition: width 0.3s ease;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


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
