"""
统一 SVG 图标库（跨系统/跨浏览器一致）

替代 emoji：emoji 在 Windows/macOS/Linux 上分别由 Segoe UI Emoji、Apple Color
Emoji、Noto Color Emoji 渲染，尺寸、颜色与基线各不相同，会撑大按钮/卡片高度，
导致"同一页面在不同浏览器/系统下元素尺寸不一致"。改用内联 SVG，所有环境下图标
尺寸、颜色、基线完全可控且一致。
"""

from typing import Optional

# 24x24 viewBox，stroke 风格图标路径（线宽统一为 2，圆角端点）
_STROKE_ICONS = {
    "check": '<polyline points="20 6 9 17 4 12"/>',
    "x": '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
    "edit": '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>'
            '<path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "circle": '<circle cx="12" cy="12" r="9"/>',
    "plus": '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
    "warning": '<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
               '<line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "plug": '<path d="M12 22v-5"/><path d="M9 8V2"/><path d="M15 8V2"/>'
            '<path d="M18 8v5a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4V8Z"/>',
    "file": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
             '<polyline points="14 2 14 8 20 8"/>',
    "file-text": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
                 '<polyline points="14 2 14 8 20 8"/>'
                 '<line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/>',
    "spreadsheet": '<rect x="3" y="3" width="18" height="18" rx="2"/>'
                   '<line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/>'
                   '<line x1="9" y1="3" x2="9" y2="21"/>',
    "clipboard": '<rect x="8" y="2" width="8" height="4" rx="1"/>'
                 '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>',
    "link": '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>'
            '<path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    "tag": '<path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>'
           '<line x1="7" y1="7" x2="7.01" y2="7"/>',
    "arrow-left": '<line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>',
    "arrow-right": '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>',
    "search": '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    "refresh": '<polyline points="23 4 23 10 17 10"/>'
               '<path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/>'
                '<path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>'
                '<path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>',
}

# fill 风格图标（实心）
_FILL_ICONS = {
    "play": '<polygon points="6 4 20 12 6 20 6 4"/>',
}


def icon(name: str, size: int = 16, color: str = "currentColor",
         stroke_width: float = 2.0) -> str:
    """
    生成内联 SVG 图标字符串。

    Args:
        name: 图标名（见 _STROKE_ICONS / _FILL_ICONS）
        size: 像素尺寸（正方形）
        color: 描边/填充颜色，默认 currentColor（继承父元素文字色）
        stroke_width: 描边线宽

    Returns:
        SVG 字符串；未知图标名返回空串
    """
    if name in _FILL_ICONS:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="0 0 24 24" fill="{color}" role="img" aria-label="{name}" '
            f'style="vertical-align: middle; flex-shrink: 0;">{_FILL_ICONS[name]}</svg>'
        )
    paths = _STROKE_ICONS.get(name)
    if not paths:
        return ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round" role="img" aria-label="{name}" '
        f'style="vertical-align: middle; flex-shrink: 0;">{paths}</svg>'
    )


def file_type_icon(file_type: str, size: int = 22, color: str = "#4F46E5") -> str:
    """根据文件扩展名返回对应图标"""
    ft = (file_type or "").lower()
    if ft in ('.xlsx', '.xls'):
        return icon("spreadsheet", size=size, color=color)
    if ft in ('.pdf', '.docx', '.doc', '.txt'):
        return icon("file-text", size=size, color=color)
    return icon("file", size=size, color=color)
