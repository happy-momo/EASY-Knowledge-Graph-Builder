"""
文件导入和管理组件（专业版）
使用高对比度配色和清晰的视觉层次
"""

import streamlit as st
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from html import escape as html_escape

from utils.file_manager import FileInfo, file_manager
from utils.folder_loader import scan_folder, load_folder, validate_folder, get_folder_info
from utils.doc_loader import load_document
from components.icons import file_type_icon

# 每页显示的文件数
PAGE_SIZE = 5


def render_file_import_section() -> Tuple[List[FileInfo], bool]:
    """
    渲染文件导入界面（专业版）
    """
    st.markdown('<h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">文件导入</h3>', unsafe_allow_html=True)

    import_mode = st.radio(
        "导入方式",
        options=["upload", "folder"],
        format_func=lambda x: {
            "upload": "上传单个文件",
            "folder": "导入文件夹"
        }[x],
        horizontal=True,
        key="file_import_mode"
    )

    st.markdown('<hr style="border: none; border-top: 1px solid #E2E8F0; margin: 1rem 0;">', unsafe_allow_html=True)

    files_changed = False

    if import_mode == "upload":
        files_changed = render_single_file_upload()
    else:
        files_changed = render_folder_import()

    render_file_list()

    return file_manager.get_files(), files_changed


def render_single_file_upload() -> bool:
    """渲染单文件上传（专业版）"""
    st.markdown('<p style="color: var(--text-primary); font-weight: 600; margin-bottom: 0.25rem;">选择文件</p>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "选择文件",
        type=["pdf", "docx", "doc", "xlsx", "xls", "txt"],
        help="支持PDF、Word、Excel和文本文件",
        label_visibility="collapsed"
    )

    col1, col2 = st.columns(2)
    with col1:
        max_chunk_size = st.number_input(
            "最大分块大小",
            min_value=500,
            max_value=4000,
            value=2000,
            step=100,
            help="建议2000-3000字符"
        )
    with col2:
        min_chunk_size = st.number_input(
            "最小分块大小",
            min_value=100,
            max_value=1000,
            value=500,
            step=50
        )

    if uploaded_file:
        with st.spinner("正在解析文档..."):
            chunks, err = load_document(uploaded_file, max_chunk_size, min_chunk_size)

            if err:
                st.error(f"解析失败: {err}")
                return False

            file_info = file_manager.add_uploaded_file(uploaded_file, chunks)
            st.success(f"已添加: {uploaded_file.name} ({len(chunks)}个分块)")
            return True

    return False


def render_folder_import() -> bool:
    """渲染文件夹导入（专业版）"""
    st.markdown('<p style="color: var(--text-primary); font-weight: 600; margin-bottom: 0.25rem;">文件夹路径</p>', unsafe_allow_html=True)

    folder_path = st.text_input(
        "文件夹路径",
        placeholder="/path/to/documents",
        help="输入包含文档的文件夹路径",
        label_visibility="collapsed"
    )

    recursive = st.checkbox("递归扫描子文件夹", value=True)

    col1, col2 = st.columns(2)
    with col1:
        max_chunk_size = st.number_input(
            "最大分块大小",
            min_value=500,
            max_value=4000,
            value=2000,
            step=100
        )
    with col2:
        min_chunk_size = st.number_input(
            "最小分块大小",
            min_value=100,
            max_value=1000,
            value=500,
            step=50
        )

    if folder_path:
        is_valid, error_msg = validate_folder(folder_path)

        if not is_valid:
            st.error(error_msg)
            return False

        folder_info = get_folder_info(folder_path)
        st.markdown((
            f'**{folder_info["name"]}**\n'
            f'- 支持的文件: {folder_info["supported_files_count"]}个\n'
            f'- 总文件: {folder_info["all_files_count"]}个\n'
            f"- 文件类型: {', '.join(f'{k}: {v}' for k, v in folder_info['type_counts'].items() if v > 0)}"
        ))

        if st.button("导入文件夹中的所有文件", type="primary"):
            with st.spinner("正在扫描和解析文件..."):
                progress_bar = st.progress(0)
                status_text = st.empty()

                scanned_files = scan_folder(folder_path, recursive)
                total_files = len(scanned_files)

                imported_count = 0
                error_count = 0

                for i, file_info in enumerate(scanned_files):
                    status_text.text(f"正在处理: {file_info['name']}...")

                    try:
                        chunks, err = load_document(
                            file_info['path'],
                            max_chunk_size,
                            min_chunk_size
                        )
                        if err:
                            error_count += 1
                            continue

                        file_manager.add_local_file(
                            file_info['path'],
                            chunks,
                            source="folder",
                            folder_path=folder_path
                        )
                        imported_count += 1

                    except Exception:
                        error_count += 1

                    progress_bar.progress((i + 1) / total_files)

                status_text.empty()
                progress_bar.empty()

                if imported_count > 0:
                    st.success(f"成功导入 {imported_count} 个文件")
                if error_count > 0:
                    st.warning(f"{error_count} 个文件导入失败")

                return imported_count > 0

    return False


def render_file_list():
    """渲染已导入文件列表（专业版）- 带搜索和翻页"""
    files = file_manager.get_files()

    if not files:
        st.info("暂无已导入的文件")
        return

    # 标题栏 + 清空按钮
    col_title, col_clear = st.columns([3, 1])
    with col_title:
        st.markdown(f'<h4 style="color: var(--text-primary); margin: 0.5rem 0;">已导入文件 ({len(files)}个)</h4>', unsafe_allow_html=True)
    with col_clear:
        if st.button("清空全部", key="clear_all"):
            file_manager.clear_all()
            st.rerun()

    st.markdown('<hr style="border: none; border-top: 1px solid #E2E8F0; margin: 1rem 0;">', unsafe_allow_html=True)

    # 搜索框
    search_keyword = st.text_input(
        "搜索文件",
        placeholder="输入文件名关键词筛选...",
        key="file_search_keyword",
        label_visibility="collapsed"
    )

    # 按关键词过滤
    if search_keyword.strip():
        keyword = search_keyword.strip().lower()
        filtered_files = [f for f in files if keyword in f.name.lower()]
        if not filtered_files:
            st.warning(f"没有找到包含「{search_keyword.strip()}」的文件")
            return
        st.caption(f"找到 {len(filtered_files)} 个匹配文件")
    else:
        filtered_files = files

    # 翻页状态
    total_pages = max(1, (len(filtered_files) - 1) // PAGE_SIZE + 1)

    if 'file_list_page' not in st.session_state:
        st.session_state.file_list_page = 0

    # 确保页码合法（搜索后可能页数变少）
    if st.session_state.file_list_page >= total_pages:
        st.session_state.file_list_page = max(0, total_pages - 1)

    current_page = st.session_state.file_list_page
    start_idx = current_page * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, len(filtered_files))

    # 渲染当前页文件
    for idx in range(start_idx, end_idx):
        render_file_item(filtered_files[idx])

    # 翻页控件
    if total_pages > 1:
        render_pagination(current_page, total_pages)

    st.markdown('<hr style="border: none; border-top: 1px solid #E2E8F0; margin: 1rem 0;">', unsafe_allow_html=True)
    render_file_statistics(file_manager.get_statistics())


def render_pagination(current_page: int, total_pages: int):
    """渲染翻页控件"""
    col_prev, col_info, col_next = st.columns([1, 2, 1])

    with col_prev:
        if st.button("← 上一页", key="file_prev_page", disabled=(current_page == 0), use_container_width=True):
            st.session_state.file_list_page = current_page - 1
            st.rerun()

    with col_info:
        st.markdown(
            f'<div style="text-align: center; color: var(--text-primary); padding-top: 0.4rem;">第 {current_page + 1} / {total_pages} 页</div>',
            unsafe_allow_html=True
        )

    with col_next:
        if st.button("下一页 →", key="file_next_page", disabled=(current_page >= total_pages - 1), use_container_width=True):
            st.session_state.file_list_page = current_page + 1
            st.rerun()


def render_file_item(file: FileInfo):
    """渲染单个文件条目 - 带分块预览展开"""
    # 文件类型图标用统一 SVG（替代 emoji，跨系统尺寸/颜色一致）
    icon = file_type_icon(file.type)

    status_map = {
        'pending': ('warning', '待处理'),
        'parsed': ('success', '已解析'),
        'processing': ('info', '处理中'),
        'completed': ('success', '已完成'),
        'error': ('error', '错误'),
    }
    status_type, status_label = status_map.get(file.status, ('', file.status))

    folder_info = f' | 文件夹: {html_escape(Path(file.folder_path).name)}' if file.folder_path else ''
    safe_name = html_escape(file.name)

    # 文件信息卡片
    card_html = (
        f'<div class="file-item">'
        f'<div class="file-icon">{icon}</div>'
        f'<div class="file-info">'
        f'<div class="file-name">{safe_name}</div>'
        f'<div class="file-meta">'
        f'{file.size_display} | {file.chunks_count}个分块 | '
        f'<span class="file-status {status_type}">{status_label}</span>'
        f'{folder_info}'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)

    # 操作按钮 + 查看分块
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("移除", key=f"remove_{file.id}", help="移除此文件", use_container_width=True):
            file_manager.remove_file(file.id)
            st.rerun()

    with col2:
        # 用 expander 展示分块内容
        if file.chunks:
            show_chunks = st.button(
                f"查看分块 ({file.chunks_count})",
                key=f"show_chunks_{file.id}",
                use_container_width=True
            )
            if show_chunks:
                st.session_state[f'_chunks_expanded_{file.id}'] = not st.session_state.get(f'_chunks_expanded_{file.id}', False)

    # 展示分块内容
    if file.chunks and st.session_state.get(f'_chunks_expanded_{file.id}', False):
        render_chunks_preview(file)


def render_chunks_preview(file: FileInfo):
    """渲染文件分块预览"""
    chunks = file.chunks
    chunk_page_size = 3

    # 初始化分块翻页状态
    chunk_page_key = f'_chunk_page_{file.id}'
    if chunk_page_key not in st.session_state:
        st.session_state[chunk_page_key] = 0

    chunk_total_pages = max(1, (len(chunks) - 1) // chunk_page_size + 1)
    chunk_page = st.session_state[chunk_page_key]
    if chunk_page >= chunk_total_pages:
        chunk_page = max(0, chunk_total_pages - 1)
        st.session_state[chunk_page_key] = chunk_page

    start = chunk_page * chunk_page_size
    end = min(start + chunk_page_size, len(chunks))

    for i in range(start, end):
        chunk = chunks[i]
        safe_chunk = html_escape(chunk)
        with st.container():
            st.markdown(
                f'<div style="background: var(--bg-secondary); border: 1px solid var(--border-light); '
                f'border-radius: var(--radius-md); padding: 12px; margin: 4px 0;">'
                f'<div style="display:flex;justify-content:space-between;font-size: 0.8rem; '
                f'color: var(--text-secondary); margin-bottom: 6px;">'
                f'<span>分块 {i + 1}/{len(chunks)}</span>'
                f'<span>{len(chunk)} 字符</span>'
                f'</div>'
                f'<div style="font-size: 0.85rem; color: var(--text-primary); line-height: 1.6; '
                f'white-space: pre-wrap; word-break: break-word; max-height: 220px; overflow-y: auto;">'
                f'{safe_chunk}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    # 分块翻页
    if chunk_total_pages > 1:
        cp1, cp2, cp3 = st.columns([1, 2, 1])
        with cp1:
            if st.button("←", key=f"chunk_prev_{file.id}", disabled=(chunk_page == 0), use_container_width=True):
                st.session_state[chunk_page_key] = chunk_page - 1
                st.rerun()
        with cp2:
            st.markdown(
                f'<div style="text-align: center; color: var(--text-tertiary); font-size: 0.85rem; padding-top: 0.3rem;">分块 {chunk_page + 1}/{chunk_total_pages} 页</div>',
                unsafe_allow_html=True
            )
        with cp3:
            if st.button("→", key=f"chunk_next_{file.id}", disabled=(chunk_page >= chunk_total_pages - 1), use_container_width=True):
                st.session_state[chunk_page_key] = chunk_page + 1
                st.rerun()


def render_file_statistics(stats: Dict):
    """渲染文件统计（专业版）"""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("文件总数", stats['total_files'])
    with col2:
        st.metric("分块总数", stats['total_chunks'])
    with col3:
        st.metric("总大小", stats['total_size_display'])

    status_counts = stats['status_counts']
    if any(status_counts.values()):
        st.markdown('<p style="color: var(--text-primary); font-weight: 500; margin: 0.75rem 0 0.25rem 0;">状态分布</p>', unsafe_allow_html=True)
        status_html = ""
        for status, count in status_counts.items():
            if count > 0:
                status_html += (
                    '<span style="margin-right: 1rem;">'
                    f'<span class="file-status {status}">{status}</span>'
                    f'<span style="color: var(--text-primary); font-size: 0.9rem; font-weight: 500;">{count}</span>'
                    '</span>'
                )
        st.markdown(status_html, unsafe_allow_html=True)


def get_all_chunks_for_processing() -> List[Tuple[str, str, int, str]]:
    """获取所有待处理的分块"""
    return file_manager.get_all_chunks()


def has_files_loaded() -> bool:
    """检查是否有文件已加载"""
    return len(file_manager.get_files()) > 0


def get_total_chunks() -> int:
    """获取总分块数"""
    stats = file_manager.get_statistics()
    return stats['total_chunks']
