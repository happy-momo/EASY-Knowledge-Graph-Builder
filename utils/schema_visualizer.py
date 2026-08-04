"""
Schema 结构图可视化（纯 Python 自包含 SVG，无外部依赖）

将 Schema 的实体类型与关系约束渲染为力导向风格的环形结构图：
- 实体 = 着色节点（悬浮显示属性 tooltip）
- 关系 = 带箭头的曲线 + 关系名标签（自环单独绘制）

仅依赖标准库，确保开箱即用与系统稳定。
"""

import math
from html import escape as html_escape
from typing import Dict, List, Tuple, Optional

# 与 schema_templates 一致的调色板（背景色 + 文字色）
_COLOR_BG = [
    '#EEF2FF', '#FEF3C7', '#ECFDF5', '#FFF7ED', '#FDF2F8',
    '#F0F9FF', '#F5F3FF', '#FFFBEB', '#F0FDF4', '#FEF2F2',
]
_COLOR_TEXT = [
    '#3730A3', '#92400E', '#065F46', '#9A3412', '#9D174D',
    '#0369A1', '#6D28D9', '#854D0E', '#166534', '#991B1B',
]
_EDGE_COLOR = '#94A3B8'   # 关系曲线颜色（中性灰蓝）
_LABEL_BG = '#FFFFFF'
_NODE_RADIUS = 26
# 直接使用 hex 而非 var(--text-*)：SVG 表现属性 fill="var(...)" 在旧版
# Safari/Firefox 上不解析（回退为黑色），用固定值保证跨浏览器颜色一致
_TEXT_PRIMARY = '#111827'     # = --text-primary (neutral-900)
_TEXT_SECONDARY = '#4B5563'   # = --text-secondary (neutral-600)


def _entity_colors(index: int) -> Tuple[str, str]:
    bg = _COLOR_BG[index % len(_COLOR_BG)]
    text = _COLOR_TEXT[index % len(_COLOR_TEXT)]
    return bg, text


def _text_width(text: str, font_size: float) -> float:
    """
    估算文本像素宽度（跨字体近似）：
    - CJK / 全角标点按全宽（≈ font_size）计
    - ASCII 按半宽（≈ 0.6 * font_size）计
    避免 early 版本按 ASCII 字符数算宽导致中文标签底框装不下而溢出。
    """
    width = 0.0
    for ch in text:
        if ord(ch) > 0x2E80 or ch in '，。：；！？、（）【】《》“”‘’':
            width += font_size
        else:
            width += font_size * 0.6
    return width


def _fit_text(text: str, max_px: float, font_size: float) -> str:
    """按像素宽度截断文本，超出部分用省略号替代"""
    if _text_width(text, font_size) <= max_px:
        return text
    ellipsis = '…'
    ellipsis_w = _text_width(ellipsis, font_size)
    i = len(text)
    while i > 0 and _text_width(text[:i], font_size) + ellipsis_w > max_px:
        i -= 1
    return (text[:i] + ellipsis) if i > 0 else ellipsis


def _node_positions(n: int, cx: float, cy: float, radius: float) -> List[Tuple[float, float]]:
    """在圆周上均匀分布 n 个节点（n=1 时置于中心）"""
    if n <= 0:
        return []
    if n == 1:
        return [(cx, cy)]
    positions = []
    for i in range(n):
        # 从顶部(-90°)开始顺时针
        angle = math.radians(-90 + i * 360.0 / n)
        positions.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return positions


def _shorten_to_boundary(xa: float, ya: float, xb: float, yb: float,
                         r: float) -> Tuple[float, float, float, float, float, float, float]:
    """计算从 A 边界到 B 边界的线段端点，以及单位向量与长度"""
    dx, dy = xb - xa, yb - ya
    length = math.hypot(dx, dy)
    if length == 0:
        return xa, ya, xb, yb, 1.0, 0.0, 0.0
    ux, uy = dx / length, dy / length
    start = (xa + ux * r, ya + uy * r)
    end = (xb - ux * r, yb - uy * r)
    return start[0], start[1], end[0], end[1], ux, uy, length


def render_schema_graph(schema_dict: Dict, height: int = 440) -> str:
    """
    生成 Schema 结构图（自包含 SVG，包裹在可横向滚动的容器中）

    Args:
        schema_dict: Schema 字典（含 entities / relationships）
        height: SVG 高度（px）

    Returns:
        HTML 字符串（含 <svg>），可通过 st.markdown(..., unsafe_allow_html=True) 渲染
    """
    entities = schema_dict.get('entities', []) or []
    relationships = schema_dict.get('relationships', []) or []

    n = len(entities)
    if n == 0:
        return '<div style="color: var(--text-tertiary); padding: 1rem; text-align: center;">暂无实体，无法生成结构图</div>'

    width = 820
    cx, cy = width / 2, height / 2
    # 节点越多，环越大，避免重叠
    radius = max(120.0, min(n * 26.0, 260.0))

    positions = _node_positions(n, cx, cy, radius)

    # 实体名 -> 索引（用于查找关系端点）
    name_to_idx = {}
    for i, ent in enumerate(entities):
        name_to_idx[ent.get('name', f'entity_{i}')] = i

    svg_parts: List[str] = []
    svg_parts.append(
        f'<svg viewBox="0 0 {width} {height}" width="100%" '
        f'style="max-width:100%; height:auto; font-family: var(--font-sans);" '
        f'xmlns="http://www.w3.org/2000/svg">'
    )

    # 箭头 marker（仅用 marker-end，故 orient="auto" 即可；auto-start-reverse
    # 在旧 Safari<13 不支持，改用 auto 以最大化兼容）
    svg_parts.append(
        '<defs>'
        f'<marker id="schema-arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="7" markerHeight="7" orient="auto">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{_EDGE_COLOR}"/>'
        f'</marker>'
        '</defs>'
    )

    # ---- 先画关系（在节点之下） ----
    for rel in relationships:
        head_name = rel.get('head')
        tail_name = rel.get('tail')
        rel_name = str(rel.get('relation', ''))
        hi = name_to_idx.get(head_name)
        ti = name_to_idx.get(tail_name)
        if hi is None or ti is None:
            continue  # 关系引用了不存在的实体，跳过（validate_schema 会另行提示）

        xh, yh = positions[hi]
        xt, yt = positions[ti]
        safe_rel = html_escape(rel_name)

        if hi == ti:
            # 自环：在节点正上方画一个小环
            loop_top = yh - _NODE_RADIUS - 34
            svg_parts.append(
                f'<path d="M {xh-10:.1f} {yh-_NODE_RADIUS:.1f} '
                f'C {xh-26:.1f} {loop_top:.1f}, {xh+26:.1f} {loop_top:.1f}, '
                f'{xh+10:.1f} {yh-_NODE_RADIUS:.1f}" '
                f'fill="none" stroke="{_EDGE_COLOR}" stroke-width="1.6" '
                f'marker-end="url(#schema-arrow)"/>'
            )
            # 标签：宽度按 CJK 计宽，避免中文关系名溢出白底
            label_w = _text_width(safe_rel, 10) + 12
            svg_parts.append(
                f'<rect x="{xh-label_w/2:.1f}" y="{loop_top-16:.1f}" '
                f'width="{label_w:.1f}" height="16" rx="4" '
                f'fill="{_LABEL_BG}" opacity="0.92"/>'
                f'<text x="{xh:.1f}" y="{loop_top-4:.1f}" text-anchor="middle" '
                f'font-size="10" fill="{_TEXT_SECONDARY}">{safe_rel}</text>'
            )
            continue

        sx, sy, ex, ey, ux, uy, length = _shorten_to_boundary(xh, yh, xt, yt, _NODE_RADIUS)
        if length == 0:
            continue
        # 垂直方向（用于曲线偏移），双向边按索引序号取反方向以错开
        perp_x, perp_y = -uy, ux
        sign = 1.0 if hi < ti else -1.0
        offset = 32.0
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        cpx, cpy = mx + perp_x * offset * sign, my + perp_y * offset * sign

        svg_parts.append(
            f'<path d="M {sx:.1f} {sy:.1f} Q {cpx:.1f} {cpy:.1f} {ex:.1f} {ey:.1f}" '
            f'fill="none" stroke="{_EDGE_COLOR}" stroke-width="1.6" '
            f'marker-end="url(#schema-arrow)"/>'
        )
        # 关系名标签（置于控制点附近，带白底以保证可读；宽度按 CJK 计宽）
        label_w = _text_width(safe_rel, 10) + 12
        svg_parts.append(
            f'<rect x="{cpx-label_w/2:.1f}" y="{cpy-8:.1f}" '
            f'width="{label_w:.1f}" height="16" rx="4" fill="{_LABEL_BG}" opacity="0.92"/>'
            f'<text x="{cpx:.1f}" y="{cpy+4:.1f}" text-anchor="middle" font-size="10" '
            f'fill="{_TEXT_SECONDARY}">{safe_rel}</text>'
        )

    # ---- 再画节点（覆盖在关系之上） ----
    for i, ent in enumerate(entities):
        x, y = positions[i]
        name = str(ent.get('name', f'entity_{i}'))
        props = ent.get('properties', []) or []
        bg, text_color = _entity_colors(i)
        safe_name = html_escape(name)
        # tooltip：悬浮显示属性（用真实换行，多数现代浏览器在 <title> 中支持多行）
        tip = f"{name}\n属性: {', '.join(str(p) for p in props) if props else '无'}"
        # 节点内文字按像素截断到圆内可视宽度（直径 ~52px，留边距），完整名称置于下方
        in_circle = html_escape(_fit_text(name, _NODE_RADIUS * 1.7, 12))
        svg_parts.append(
            f'<g>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{_NODE_RADIUS}" fill="{bg}" '
            f'stroke="{text_color}" stroke-width="2">'
            f'<title>{html_escape(tip)}</title>'
            f'</circle>'
            f'<text x="{x:.1f}" y="{y+4:.1f}" text-anchor="middle" font-size="12" '
            f'font-weight="600" fill="{text_color}">{in_circle}</text>'
            # 完整名称置于节点下方
            f'<text x="{x:.1f}" y="{y+_NODE_RADIUS+15:.1f}" text-anchor="middle" '
            f'font-size="11" fill="{_TEXT_PRIMARY}">{safe_name}</text>'
            f'</g>'
        )

    svg_parts.append('</svg>')

    # 包裹一层可横向滚动的容器，窄屏不溢出
    return (
        '<div class="schema-graph-svg" style="background: var(--bg-elevated); '
        'border: 1px solid var(--border-light); border-radius: var(--radius-md); '
        'padding: 0.5rem; overflow-x: auto;">'
        + ''.join(svg_parts) +
        '</div>'
    )


def render_schema_details(schema_dict: Dict) -> str:
    """
    生成 Schema 明细的纯文本/HTML 摘要（结构图的辅助说明，无表格依赖）

    Returns:
        HTML 字符串
    """
    entities = schema_dict.get('entities', []) or []
    relationships = schema_dict.get('relationships', []) or []

    parts = ['<div style="font-size: 0.85rem; line-height: 1.6;">']
    parts.append('<div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.35rem;">实体类型</div>')
    parts.append('<ul style="margin: 0 0 0.5rem 0; padding-left: 1.2rem; color: var(--text-secondary);">')
    for ent in entities:
        name = html_escape(str(ent.get('name', '未命名')))
        props = ent.get('properties', []) or []
        props_str = ', '.join(html_escape(str(p)) for p in props) if props else '<i>无属性</i>'
        parts.append(f'<li><b style="color: var(--text-primary);">{name}</b> — {props_str}</li>')
    parts.append('</ul>')

    parts.append('<div style="font-weight: 600; color: var(--text-primary); margin: 0.5rem 0 0.35rem;">关系约束</div>')
    parts.append('<ul style="margin: 0; padding-left: 1.2rem; color: var(--text-secondary);">')
    for rel in relationships:
        h = html_escape(str(rel.get('head', '?')))
        r = html_escape(str(rel.get('relation', '?')))
        t = html_escape(str(rel.get('tail', '?')))
        parts.append(f'<li><b style="color: var(--text-primary);">{h}</b> —<span style="color: var(--color-primary-600);"> {r} </span>-> <b style="color: var(--text-primary);">{t}</b></li>')
    parts.append('</ul></div>')
    return ''.join(parts)
