"""
文件夹加载器

扫描文件夹并批量加载文档文件。
"""

import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from utils.doc_loader import load_document
from utils.file_manager import FileManager  # 复用 SUPPORTED_EXTENSIONS


# 支持的文件扩展名（复用 FileManager 定义，避免重复维护）
SUPPORTED_EXTENSIONS = FileManager.SUPPORTED_EXTENSIONS


def scan_folder(folder_path: str, recursive: bool = True) -> List[Dict]:
    """
    扫描文件夹，返回符合条件的文件列表

    Args:
        folder_path: 文件夹路径
        recursive: 是否递归扫描子文件夹

    Returns:
        文件信息列表 [{'path': str, 'name': str, 'size': int, 'type': str, 'relative_path': str}]
    """
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(f"文件夹不存在: {folder_path}")

    if not folder.is_dir():
        raise ValueError(f"路径不是文件夹: {folder_path}")

    files = []

    if recursive:
        # 递归扫描
        for root, dirs, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = Path(root) / filename
                if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    relative_path = str(file_path.relative_to(folder))
                    files.append({
                        'path': str(file_path),
                        'name': filename,
                        'size': file_path.stat().st_size,
                        'type': file_path.suffix.lower(),
                        'relative_path': relative_path
                    })
    else:
        # 仅扫描当前层级
        for file_path in folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append({
                    'path': str(file_path),
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'type': file_path.suffix.lower(),
                    'relative_path': file_path.name
                })

    # 按文件名排序
    files.sort(key=lambda x: x['name'])

    return files


def load_folder(folder_path: str, max_chunk_size: int = 2000,
                min_chunk_size: int = 500, recursive: bool = True) -> Tuple[List[Dict], Dict]:
    """
    加载文件夹中的所有文档

    Args:
        folder_path: 文件夹路径
        max_chunk_size: 最大分块大小
        min_chunk_size: 最小分块大小
        recursive: 是否递归扫描

    Returns:
        (文件列表, 统计信息)
    """
    files = scan_folder(folder_path, recursive)

    loaded_files = []
    total_chunks = 0
    total_chars = 0
    error_files = []

    for file_info in files:
        try:
            # 加载文档
            chunks, err = load_document(
                file_info['path'],
                max_chunk_size,
                min_chunk_size
            )

            if err:
                error_files.append({
                    'name': file_info['name'],
                    'error': err
                })
            else:
                loaded_file = {
                    'path': file_info['path'],
                    'name': file_info['name'],
                    'size': file_info['size'],
                    'type': file_info['type'],
                    'chunks': chunks,
                    'chunks_count': len(chunks),
                    'total_chars': sum(len(c) for c in chunks),
                    'status': 'parsed',
                    'relative_path': file_info['relative_path']
                }
                loaded_files.append(loaded_file)
                total_chunks += len(chunks)
                total_chars += sum(len(c) for c in chunks)

        except Exception as e:
            error_files.append({
                'name': file_info['name'],
                'error': str(e)
            })

    # 统计信息
    statistics = {
        'total_files': len(files),
        'loaded_files': len(loaded_files),
        'error_files': len(error_files),
        'total_chunks': total_chunks,
        'total_chars': total_chars,
        'average_chunk_size': total_chars // total_chunks if total_chunks > 0 else 0,
        'errors': error_files,
        'scanned_at': datetime.now().isoformat()
    }

    return loaded_files, statistics


def get_folder_info(folder_path: str) -> Dict:
    """
    获取文件夹信息（不加载内容）

    Args:
        folder_path: 文件夹路径

    Returns:
        文件夹信息字典
    """
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(f"文件夹不存在: {folder_path}")

    # 统计文件
    supported_files = scan_folder(folder_path, recursive=False)
    all_files = scan_folder(folder_path, recursive=True)

    total_size = sum(f['size'] for f in all_files)

    # 按类型统计
    type_counts = {}
    for ext in SUPPORTED_EXTENSIONS:
        type_counts[ext] = len([f for f in all_files if f['type'] == ext])

    return {
        'path': str(folder),
        'name': folder.name,
        'supported_files_count': len(supported_files),
        'all_files_count': len(all_files),
        'total_size': total_size,
        'type_counts': type_counts,
        'has_subfolders': any(f['relative_path'] != f['name'] for f in all_files)
    }


def validate_folder(folder_path: str) -> Tuple[bool, str]:
    """
    验证文件夹是否有效

    Args:
        folder_path: 文件夹路径

    Returns:
        (是否有效, 错误信息或空字符串)
    """
    folder = Path(folder_path)

    if not folder.exists():
        return False, f"文件夹不存在: {folder_path}"

    if not folder.is_dir():
        return False, f"路径不是文件夹: {folder_path}"

    # 检查是否有支持的文件
    files = scan_folder(folder_path, recursive=False)
    if not files:
        return False, "文件夹中没有支持的文件类型 (PDF, DOCX, XLSX, TXT)"

    return True, ""