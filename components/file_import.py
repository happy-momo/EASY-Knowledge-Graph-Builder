"""
文件导入和管理组件（专业版）
使用高对比度配色和清晰的视觉层次
"""

import streamlit as st
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from utils.file_manager import FileInfo, file_manager
from utils.folder_loader import scan_folder, load_folder, validate_folder, get_folder_info
from utils.doc_loader import load_document


def render_file_import_section() -> Tuple[List[FileInfo], bool]:
    """
    渲染文件导入界面（专业版）
    """
    st.markdown('<h3 style="color: #000000; margin-bottom: 0.5rem;">文件导入</h3>', unsafe_allow_html=True)

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
    st.markdown('<p style="color: #000000; font-weight: 600; margin-bottom: 0.25rem;">选择文件</p>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "",
        type=["pdf", "docx", "doc", "xlsx", "xls", "txt"],
        help="支持PDF、Word、Excel和文本文件"
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
    st.markdown('<p style="color: #000000; font-weight: 600; margin-bottom: 0.25rem;">文件夹路径</p>', unsafe_allow_html=True)

    folder_path = st.text_input(
        "",
        placeholder="/path/to/documents",
        help="输入包含文档的文件夹路径"
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
            f'''**{folder_info["name"]}**\n'''
            f'- 支持的文件: {folder_info["supported_files_count"]}个\n'
            f'- 总文件: {folder_info["all_files_count"]}个\n'
            f"- 文件类型: {', '.join(f'{k}: {v}' for k, v in folder_info['type_counts'].items() if v > 0)}"
        ).strip(), unsafe_allow_html=True)

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
    """渲染已导入文件列表（专业版）"""
    files = file_manager.get_files()

    if not files:
        st.info("暂无已导入的文件")
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f'<h4 style="color: #000000; margin: 0.5rem 0;">已导入文件 ({len(files)}个)</h4>', unsafe_allow_html=True)
    with col2:
        if st.button("清空全部", key="clear_all"):
            file_manager.clear_all()
            st.rerun()

    st.markdown('<hr style="border: none; border-top: 1px solid #E2E8F0; margin: 1rem 0;">', unsafe_allow_html=True)

    for file in files:
        render_file_item(file)

    stats = file_manager.get_statistics()
    st.markdown('<hr style="border: none; border-top: 1px solid #E2E8F0; margin: 1rem 0;">', unsafe_allow_html=True)
    render_file_statistics(stats)


def render_file_item(file: FileInfo):
    """渲染单个文件条目（专业版）"""
    icon_map = {
        '.pdf': '&#128214;',
        '.docx': '&#128196;',
        '.doc': '&#128196;',
        '.xlsx': '&#128197;',
        '.xls': '&#128197;',
        '.txt': '&#128196;',
    }
    icon = icon_map.get(file.type, '&#128196;')

    status_map = {
        'pending': ('warning', '待处理'),
        'parsed': ('success', '已解析'),
        'processing': ('info', '处理中'),
        'completed': ('success', '已完成'),
        'error': ('error', '错误'),
    }
    status_type, status_label = status_map.get(file.status, ('', file.status))

    card_html = f"""
    <div class="file-item">
        <div class="file-icon">{icon}</div>
        <div class="file-info">
            <div class="file-name">{file.name}</div>
            <div class="file-meta">
                {file.size_display} | {file.chunks_count}个分块 |
                <span class="file-status {status_type}">{status_label}</span>
                {' | ' + f'文件夹: {Path(file.folder_path).name}' if file.folder_path else ''}
            </div>
        </div>
    </div>
    """.strip()

    st.markdown(card_html, unsafe_allow_html=True)

    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("移除", key=f"remove_{file.id}", help="移除此文件", use_container_width=True):
            file_manager.remove_file(file.id)
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
        st.markdown('<p style="color: #000000; font-weight: 500; margin: 0.75rem 0 0.25rem 0;">状态分布</p>', unsafe_allow_html=True)
        status_html = ""
        for status, count in status_counts.items():
            if count > 0:
                status_html += (
                    '<span style="margin-right: 1rem;">'
                    f'<span class="file-status {status}">{status}</span>'
                    f'<span style="color: #000000; font-size: 0.9rem; font-weight: 500;">{count}</span>'
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
