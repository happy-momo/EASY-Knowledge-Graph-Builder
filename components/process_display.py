"""
处理进度和结果展示组件（重构版）
移除emoji，使用SVG图标，高对比度配色
"""

import streamlit as st
from typing import Dict, List, Optional
import time
from html import escape as html_escape

from utils.progress_tracker import ProgressTracker, ProcessProgress


# SVG Icons
_ICONS = {
    "processing": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>',
    "check": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    "error": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
    "file": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
    "cube": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>',
    "search": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    "refresh": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>',
}


def render_processing_page(progress: ProcessProgress):
    """渲染处理进度页面"""

    st.markdown(
        '<h3 style="color: var(--text-primary); margin-bottom: 1rem;">'
        '<span style="display: inline-flex; align-items: center; gap: 0.5rem;">'
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>'
        '知识抽取处理中'
        '</span>'
        '</h3>',
        unsafe_allow_html=True
    )

    # 进度条
    render_progress_indicator(progress)

    # 当前处理信息
    render_current_processing(progress)

    # 实时三元组预览
    if progress.chunk_progress:
        render_recent_triples(progress.chunk_progress[-5:])


def render_progress_indicator(progress: ProcessProgress):
    """渲染进度指示器"""

    # 主进度条
    progress_percent = progress.progress_percent

    st.markdown(
        f'<div style="margin: 2rem 0;">'
        f'<div style="display: flex; justify-content: space-between; margin-bottom: 0.75rem;">'
        f'<span style="color: var(--text-primary); font-size: 0.9rem; font-weight: 500;">处理进度</span>'
        f'<span style="color: var(--color-primary-600); font-weight: 600; font-size: 1.1rem;">{progress_percent:.1f}%</span>'
        f'</div>'
        f'<div style="height: 10px; background: #E2E8F0; border-radius: 10px; overflow: hidden;">'
        f'<div style="width: {progress_percent}%; height: 100%; background: var(--color-primary-600); border-radius: 10px; transition: width 0.3s ease;"></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # 统计信息
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("处理分块", f"{progress.processed_chunks}/{progress.total_chunks}")
    with col2:
        st.metric("已抽取三元组", progress.total_triples)
    with col3:
        if progress.processed_chunks > 0:
            avg = progress.total_triples / progress.processed_chunks
            st.metric("平均效率", f"{avg:.1f} 三元组/块")
        else:
            st.metric("平均效率", "-")
    with col4:
        st.metric("已耗时", progress.elapsed_time_str)


def render_current_processing(progress: ProcessProgress):
    """渲染当前处理信息"""

    if progress.current_file:
        st.markdown("---")
        st.markdown(
            f'<div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">'
            f'{_ICONS["file"]}'
            f'<span style="color: var(--text-primary); font-weight: 500;">当前文件:</span>'
            f'<code>{html_escape(progress.current_file)}</code>'
            f'</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div style="display: flex; align-items: center; gap: 0.5rem;">'
            f'{_ICONS["cube"]}'
            f'<span style="color: var(--text-primary); font-weight: 500;">当前分块:</span>'
            f'<span style="color: var(--text-primary);">{progress.current_chunk + 1 if progress.current_chunk is not None else "-"}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

        # 加载动画
        st.markdown(
            '<div class="loading-container" style="padding: 1rem;">'
            '<div class="loading-spinner" style="width: 32px; height: 32px;"></div>'
            '<div class="loading-text" style="font-size: 0.95rem; color: var(--text-primary);">正在使用LLM抽取知识...</div>'
            '</div>',
            unsafe_allow_html=True
        )


def render_recent_triples(chunk_progress: List[Dict]):
    """渲染最近抽取的三元组"""

    st.markdown("---")
    st.markdown("<h4 style='color: var(--text-primary); margin-bottom: 0.75rem;'>最近抽取的三元组</h4>", unsafe_allow_html=True)

    triples_to_show = []
    for chunk in reversed(chunk_progress):
        if chunk.get('triples'):
            triples_to_show.extend(chunk['triples'][:3])
        if len(triples_to_show) >= 5:
            break

    if triples_to_show:
        for i, triple in enumerate(triples_to_show[:5]):
            render_triple_preview(triple, i)
    else:
        st.info("等待抽取结果...")


def render_triple_preview(triple: Dict, index: int):
    """渲染三元组预览卡片"""

    # 对三元组值进行HTML转义，防止注入
    head = html_escape(str(triple.get('head', 'N/A')))
    relation = html_escape(str(triple.get('relation', 'N/A')))
    tail = html_escape(str(triple.get('tail', 'N/A')))

    st.markdown(
        f'<div class="triple-card" style="--index: {index}; padding: 0.75rem; margin-bottom: 0.5rem;">'
        f'<div style="display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; font-size: 0.9rem;">'
        f'<div style="color: var(--color-primary-700); font-weight: 500; min-width: 80px;">{head}</div>'
        f'<div style="color: var(--text-primary); font-size: 0.85rem;">--{relation}--&gt;</div>'
        f'<div style="color: var(--color-primary-700); font-weight: 500; min-width: 80px;">{tail}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )


def render_completion_page(stats: Dict):
    """渲染完成页面"""

    # 成功徽章动画
    st.markdown(
        '<div style="text-align: center; margin-bottom: 2rem;">'
        '<div class="completion-checkmark">'
        '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'
        '</div>'
        f'<h2 style="color: var(--text-primary); margin-bottom: 0.5rem;">处理完成</h2>'
        f'<p style="color: var(--text-primary); font-size: 1rem;">共处理 {stats["total_chunks"]} 个文本块，提取了 {stats["total_triples"]} 个三元组。</p>'
        '</div>',
        unsafe_allow_html=True
    )

    # 统计卡片
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("处理文件", stats.get('total_files', 0))
    with col2:
        st.metric("处理分块", stats.get('total_chunks', 0))
    with col3:
        st.metric("三元组数", stats.get('total_triples', 0))
    with col4:
        st.metric("平均效率", f"{stats.get('avg_triples', 0):.1f} 三元组/块")

    # 操作建议
    st.markdown("---")
    st.markdown("<h4 style='color: var(--text-primary); margin-bottom: 1rem;'>下一步</h4>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f'<div class="info-card" style="margin-bottom: 1rem;">'
            f'<div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">'
            f'{_ICONS["search"]}'
            f'<span style="font-weight: 600; color: var(--text-primary);">查看知识图谱</span>'
            f'</div>'
            f'<p style="color: var(--text-primary); font-size: 0.9rem; margin: 0;">打开 Neo4j Browser 查看生成的知识图谱：<br>访问 <code>http://localhost:7474</code><br>运行查询查看节点和关系</p>'
            f'</div>',
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f'<div class="info-card" style="margin-bottom: 1rem; border-left-color: #059669;">'
            f'<div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">'
            f'{_ICONS["refresh"]}'
            f'<span style="font-weight: 600; color: var(--text-primary);">继续处理</span>'
            f'</div>'
            f'<p style="color: var(--text-primary); font-size: 0.9rem; margin: 0;">导入更多文档进行扩展<br>修改Schema重新抽取<br>导出知识图谱数据</p>'
            f'</div>',
            unsafe_allow_html=True
        )

    # 重新开始按钮
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("开始新的任务", type="primary", use_container_width=True):
            return "restart"

    return None


def render_error_page(error_message: str, traceback: str = None):
    """渲染错误页面"""

    st.markdown(
        '<div style="text-align: center; margin-bottom: 2rem;">'
        '<div style="width: 64px; height: 64px; border-radius: 50%; background: #FEE2E2; display: flex; align-items: center; justify-content: center; margin: 0 auto 1.5rem;">'
        '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>'
        '</div>'
        '<h2 style="color: var(--text-primary); margin-bottom: 0.5rem;">处理出错</h2>'
        '<p style="color: var(--text-primary); font-size: 1rem;">处理过程中发生错误</p>'
        '</div>',
        unsafe_allow_html=True
    )

    st.error(f"错误详情：{error_message}")

    if traceback:
        with st.expander("查看详细错误信息"):
            st.code(traceback, language="python")

    # 重试按钮
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("重试", type="primary", use_container_width=True):
            return "retry"

    return None


def render_loading_animation(message: str = "正在处理..."):
    """渲染加载动画"""

    st.markdown(
        f'<div class="loading-container">'
        f'<div class="loading-spinner"></div>'
        f'<div class="loading-text">{html_escape(message)}</div>'
        f'</div>',
        unsafe_allow_html=True
    )


def render_skeleton_loading():
    """渲染骨架屏加载"""

    st.markdown(
        '<div style="padding: 1rem;">'
        '<div class="skeleton" style="height: 20px; width: 60%; margin-bottom: 1rem;"></div>'
        '<div class="skeleton" style="height: 100px; width: 100%; margin-bottom: 1rem;"></div>'
        '<div class="skeleton" style="height: 20px; width: 80%; margin-bottom: 0.5rem;"></div>'
        '<div class="skeleton" style="height: 20px; width: 70%;"></div>'
        '</div>',
        unsafe_allow_html=True
    )
