"""
处理进度和结果展示组件
"""

import streamlit as st
from typing import Dict, List, Optional
import time

from utils.progress_tracker import ProgressTracker, ProcessProgress


def render_processing_page(progress: ProcessProgress):
    """渲染处理进度页面"""

    st.markdown("### ⚙️ 知识抽取处理中")

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

    st.markdown(f"""
    <div style="margin: 2rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.75rem;">
            <span style="color: var(--text-secondary); font-size: 0.9rem;">处理进度</span>
            <span style="color: var(--accent-primary); font-weight: 600; font-size: 1.1rem;">{progress_percent:.1f}%</span>
        </div>
        <div class="progress-animated" style="height: 10px; background: var(--bg-secondary); border-radius: 10px; overflow: hidden;">
            <div style="width: {progress_percent}%; height: 100%; background: var(--gradient-primary); border-radius: 10px; transition: width 0.3s ease;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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
        st.markdown(f"**📄 当前文件:** `{progress.current_file}`")
        st.markdown(f"**📦 当前分块:** {progress.current_chunk + 1 if progress.current_chunk is not None else '-'}")

        # 加载动画
        st.markdown("""
        <div class="loading-container" style="padding: 1rem;">
            <div class="loading-spinner" style="width: 32px; height: 32px;"></div>
            <div class="loading-text" style="font-size: 0.95rem;">正在使用LLM抽取知识...</div>
        </div>
        """, unsafe_allow_html=True)


def render_recent_triples(chunk_progress: List[Dict]):
    """渲染最近抽取的三元组"""

    st.markdown("---")
    st.markdown("#### 最近抽取的三元组")

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

    card_html = f"""
    <div class="triple-card" style="--index: {index}; padding: 0.75rem;">
        <div class="triple-content" style="font-size: 0.9rem;">
            <div style="color: var(--accent-primary); font-weight: 500;">
                {triple.get('head', 'N/A')}
            </div>
            <div style="color: var(--accent-secondary); font-size: 0.85rem;">
                --{triple.get('relation', 'N/A')}-->
            </div>
            <div style="color: var(--accent-primary); font-weight: 500;">
                {triple.get('tail', 'N/A')}
            </div>
        </div>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)


def render_completion_page(stats: Dict):
    """渲染完成页面"""

    st.markdown("### 🎉 处理完成")

    # 成功消息
    st.success(f"""
    ✅ 知识图谱构建完成！

    共处理 {stats['total_chunks']} 个文本块，提取了 {stats['total_triples']} 个三元组。
    """)

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
    st.markdown("#### 下一步")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        🔍 **查看知识图谱**

        打开 Neo4j Browser 查看生成的知识图谱：
        - 访问 `http://localhost:7474`
        - 运行查询查看节点和关系
        """)

    with col2:
        st.markdown("""
        🔄 **继续处理**

        - 导入更多文档进行扩展
        - 修改Schema重新抽取
        - 导出知识图谱数据
        """)

    # 重新开始按钮
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 开始新的任务", type="primary", use_container_width=True):
            return "restart"

    return None


def render_error_page(error_message: str, traceback: str = None):
    """渲染错误页面"""

    st.markdown("### ❌ 处理出错")

    st.error(f"处理过程中发生错误：{error_message}")

    if traceback:
        with st.expander("查看详细错误信息"):
            st.code(traceback, language="python")

    # 重试按钮
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 重试", type="primary", use_container_width=True):
            return "retry"

    return None


def render_loading_animation(message: str = "正在处理..."):
    """渲染加载动画"""

    st.markdown(f"""
    <div class="loading-container">
        <div class="loading-spinner"></div>
        <div class="loading-text">{message}</div>
    </div>
    """, unsafe_allow_html=True)


def render_skeleton_loading():
    """渲染骨架屏加载"""

    st.markdown("""
    <div style="padding: 1rem;">
        <div class="skeleton" style="height: 20px; width: 60%; margin-bottom: 1rem;"></div>
        <div class="skeleton" style="height: 100px; width: 100%; margin-bottom: 1rem;"></div>
        <div class="skeleton" style="height: 20px; width: 80%; margin-bottom: 0.5rem;"></div>
        <div class="skeleton" style="height: 20px; width: 70%;"></div>
    </div>
    """, unsafe_allow_html=True)