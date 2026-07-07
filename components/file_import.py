"""
文件导入和管理组件
"""

import streamlit as st
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from utils.file_manager import FileInfo, file_manager
from utils.folder_loader import scan_folder, load_folder, validate_folder, get_folder_info
from utils.doc_loader import load_document


def render_file_import_section() -> Tuple[List[FileInfo], bool]:
    """
    渲染文件导入界面

    Returns:
        (文件列表, 是否有变化)
    """
    st.markdown("### 文件导入")

    # 选择导入方式
    import_mode = st.radio(
        "导入方式",
        options=["upload", "folder"],
        format_func=lambda x: {
            "upload": "📄 上传单个文件",
            "folder": "📁 导入文件夹"
        }[x],
        horizontal=True,
        key="file_import_mode"
    )

    st.markdown("---")

    files_changed = False

    if import_mode == "upload":
        files_changed = render_single_file_upload()
    else:
        files_changed = render_folder_import()

    # 显示已导入的文件列表
    render_file_list()

    return file_manager.get_files(), files_changed


def render_single_file_upload() -> bool:
    """渲染单文件上传"""

    uploaded_file = st.file_uploader(
        "选择文件",
        type=["pdf", "docx", "doc", "xlsx", "xls", "txt"],
        help="支持PDF、Word、Excel和文本文件"
    )

    # 分块参数配置
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
            # 加载文档
            chunks, err = load_document(uploaded_file, max_chunk_size, min_chunk_size)

            if err:
                st.error(f"解析失败: {err}")
                return False

            # 添加到文件管理器
            file_info = file_manager.add_uploaded_file(uploaded_file, chunks)

            st.success(f"✅ 已添加: {uploaded_file.name} ({len(chunks)}个分块)")
            return True

    return False


def render_folder_import() -> bool:
    """渲染文件夹导入"""

    # 文件夹路径输入
    folder_path = st.text_input(
        "文件夹路径",
        placeholder="/path/to/documents",
        help="输入包含文档的文件夹路径"
    )

    # 递归选项
    recursive = st.checkbox("递归扫描子文件夹", value=True)

    # 分块参数
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
        # 验证文件夹
        is_valid, error_msg = validate_folder(folder_path)

        if not is_valid:
            st.error(error_msg)
            return False

        # 显示文件夹信息
        folder_info = get_folder_info(folder_path)
        st.info(f"""
        📁 **{folder_info['name']}**
        - 支持的文件: {folder_info['supported_files_count']}个
        - 总文件: {folder_info['all_files_count']}个
        - 文件类型: {', '.join(f'{k}: {v}' for k, v in folder_info['type_counts'].items() if v > 0)}
        """)

        # 导入按钮
        if st.button("导入文件夹中的所有文件", type="primary"):
            with st.spinner("正在扫描和解析文件..."):
                progress_bar = st.progress(0)
                status_text = st.empty()

                # 扫描文件夹
                scanned_files = scan_folder(folder_path, recursive)
                total_files = len(scanned_files)

                imported_count = 0
                error_count = 0

                for i, file_info in enumerate(scanned_files):
                    status_text.text(f"正在处理: {file_info['name']}...")

                    try:
                        # 加载文档
                        chunks, err = load_document(
                            file_info['path'],
                            max_chunk_size,
                            min_chunk_size
                        )

                        if err:
                            error_count += 1
                            continue

                        # 添加到文件管理器
                        file_manager.add_local_file(
                            file_info['path'],
                            chunks,
                            source="folder",
                            folder_path=folder_path
                        )
                        imported_count += 1

                    except Exception:
                        error_count += 1

                    # 更新进度
                    progress_bar.progress((i + 1) / total_files)

                status_text.empty()
                progress_bar.empty()

                if imported_count > 0:
                    st.success(f"✅ 成功导入 {imported_count} 个文件")
                if error_count > 0:
                    st.warning(f"⚠️ {error_count} 个文件导入失败")

                return imported_count > 0

    return False


def render_file_list():
    """渲染已导入文件列表"""

    files = file_manager.get_files()

    if not files:
        st.info("暂无已导入的文件")
        return

    # 标题和清空按钮
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### 📂 已导入文件 ({len(files)}个)")
    with col2:
        if st.button("清空全部", key="clear_all"):
            file_manager.clear_all()
            st.rerun()

    st.markdown("---")

    # 文件列表
    for file in files:
        render_file_item(file)

    # 统计信息
    stats = file_manager.get_statistics()
    st.markdown("---")
    render_file_statistics(stats)


def render_file_item(file: FileInfo):
    """渲染单个文件条目"""

    # 文件类型图标
    icon_map = {
        '.pdf': '📕',
        '.docx': '📘',
        '.doc': '📘',
        '.xlsx': '📗',
        '.xls': '📗',
        '.txt': '📄'
    }
    icon = icon_map.get(file.type, '📄')

    # 状态图标和颜色
    status_map = {
        'pending': ('⏳', 'warning'),
        'parsed': ('✅', 'success'),
        'processing': ('🔄', 'info'),
        'completed': ('✅', 'success'),
        'error': ('❌', 'error')
    }
    status_icon, status_type = status_map.get(file.status, ('⚪', 'secondary'))

    # 文件卡片
    card_html = f"""
    <div class="file-item" style="--delay: {file.id[-1]};">
        <div class="file-icon">{icon}</div>
        <div class="file-info" style="flex: 1;">
            <div class="file-name">{file.name}</div>
            <div class="file-meta">
                {file.size_display} | {file.chunks_count}个分块 | {status_icon}
                {f' | 📁 {Path(file.folder_path).name}' if file.folder_path else ''}
            </div>
        </div>
        <div class="file-status {status_type}">{file.status}</div>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)

    # 移除按钮
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("移除", key=f"remove_{file.id}", help="移除此文件"):
            file_manager.remove_file(file.id)
            st.rerun()


def render_file_statistics(stats: Dict):
    """渲染文件统计"""

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("文件总数", stats['total_files'])
    with col2:
        st.metric("分块总数", stats['total_chunks'])
    with col3:
        st.metric("总大小", stats['total_size_display'])

    # 状态分布
    status_counts = stats['status_counts']
    if any(status_counts.values()):
        st.markdown("**状态分布：**")
        status_html = ""
        for status, count in status_counts.items():
            if count > 0:
                status_html += f"""
                <span style="margin-right: 1rem;">
                    <span class="file-status {status}">{status}</span>
                    <span style="color: var(--text-secondary);">{count}</span>
                </span>
                """
        st.markdown(status_html, unsafe_allow_html=True)


def get_all_chunks_for_processing() -> List[Tuple[str, str, int, str]]:
    """
    获取所有待处理的分块

    Returns:
        [(file_id, file_name, chunk_index, chunk_content)]
    """
    return file_manager.get_all_chunks()


def has_files_loaded() -> bool:
    """检查是否有文件已加载"""
    return len(file_manager.get_files()) > 0


def get_total_chunks() -> int:
    """获取总分块数"""
    stats = file_manager.get_statistics()
    return stats['total_chunks']