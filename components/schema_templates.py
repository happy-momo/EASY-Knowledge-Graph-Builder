"""
Schema模板选择组件（专业版）
使用高对比度配色和清晰的视觉层次
"""

import streamlit as st
import yaml
from typing import Dict, Any, Optional, Tuple
from html import escape as html_escape

from config.app_config import SCHEMA_TEMPLATES, HELP_TEXTS
from utils.schema_visualizer import render_schema_graph, render_schema_details


def render_schema_selection() -> Tuple[Optional[Dict], str]:
    """
    渲染Schema选择界面（专业版）
    """
    st.markdown('<h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">选择Schema配置方式</h3>', unsafe_allow_html=True)

    selection_mode = st.radio(
        "配置方式",
        options=["template", "upload", "manual"],
        format_func=lambda x: {
            "template": "选择预设模板",
            "upload": "上传YAML文件",
            "manual": "手动输入"
        }[x],
        horizontal=True,
        key="schema_mode"
    )

    st.markdown('<hr style="border: none; border-top: 1px solid #E2E8F0; margin: 1rem 0;">', unsafe_allow_html=True)

    schema_dict = None
    schema_yaml_str = ""

    if selection_mode == "template":
        schema_dict, schema_yaml_str = render_template_selection()
    elif selection_mode == "upload":
        schema_dict, schema_yaml_str = render_yaml_upload()
    else:
        schema_dict, schema_yaml_str = render_manual_input()

    return schema_dict, schema_yaml_str


def render_template_selection() -> Tuple[Optional[Dict], str]:
    """渲染模板选择界面（专业版，2 列网格）"""
    template_names = list(SCHEMA_TEMPLATES.keys())
    cols = st.columns(2)

    for i, name in enumerate(template_names):
        template = SCHEMA_TEMPLATES[name]

        with cols[i % 2]:
            is_selected = st.session_state.get('selected_template') == name

            border_color = "var(--color-primary-600)" if is_selected else "var(--border-light)"
            left_border = "var(--color-primary-600)" if is_selected else "transparent"
            shadow = "var(--shadow-md)" if is_selected else "var(--shadow-xs)"

            card_html = (
                f'<div style="padding: 1rem; margin-bottom: 0.5rem; background: var(--bg-elevated); '
                f'border: 1px solid {border_color}; border-left: 4px solid {left_border}; '
                f'border-radius: 10px; box-shadow: {shadow}; transition: all 0.2s ease;">'
                f'<div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.35rem; font-size: 1rem;">{html_escape(name)}</div>'
                f'<div style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 0.5rem;">{html_escape(template.get("description", ""))}</div>'
                f'<div style="color: var(--text-tertiary); font-size: 0.8rem;">实体: {len(template.get("entities", []))}种 | 关系: {len(template.get("relationships", []))}种</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

            if st.button(
                "✓ 已选中" if is_selected else "选择此模板",
                key=f"template_{name}",
                use_container_width=True,
                type="primary" if is_selected else "secondary"
            ):
                st.session_state['selected_template'] = name
                st.rerun()

    selected_name = st.session_state.get('selected_template')
    if selected_name and selected_name in SCHEMA_TEMPLATES:
        schema_dict = SCHEMA_TEMPLATES[selected_name]
        schema_yaml_str = yaml.dump(schema_dict, allow_unicode=True, sort_keys=False)

        st.markdown('<p style="color: var(--text-primary); font-weight: 600; margin: 1rem 0 0.5rem 0;">Schema 可视化</p>', unsafe_allow_html=True)
        render_schema_visualization(schema_dict, schema_yaml_str)

        return schema_dict, schema_yaml_str

    return None, ""


def render_yaml_upload() -> Tuple[Optional[Dict], str]:
    """渲染YAML上传界面（专业版）"""
    uploaded_file = st.file_uploader(
        "上传YAML Schema文件",
        type=["yaml", "yml"],
        help=HELP_TEXTS.get("schema_yaml", "")
    )

    if uploaded_file:
        try:
            schema_dict = yaml.safe_load(uploaded_file)

            if 'entities' not in schema_dict:
                st.error("Schema必须包含 'entities' 字段")
                return None, ""

            schema_yaml_str = yaml.dump(schema_dict, allow_unicode=True, sort_keys=False)
            st.success(f"解析成功：{uploaded_file.name}")
            render_schema_visualization(schema_dict, schema_yaml_str)

            return schema_dict, schema_yaml_str

        except yaml.YAMLError as e:
            st.error(f"YAML解析错误: {e}")
            return None, ""

    return None, ""


def render_manual_input() -> Tuple[Optional[Dict], str]:
    """渲染手动输入界面（专业版）"""
    default_yaml = """entities:
  - name: "Entity1"
    properties:
      - "property1"
      - "property2"
  - name: "Entity2"
    properties:
      - "property1"

relationships:
  - head: "Entity1"
    relation: "relatesTo"
    tail: "Entity2"
"""

    st.markdown('<p style="color: var(--text-primary); font-weight: 600; margin-bottom: 0.25rem;">输入YAML Schema</p>', unsafe_allow_html=True)
    yaml_input = st.text_area(
        "输入YAML Schema",
        value=default_yaml,
        height=250,
        help="定义实体类型、属性和关系类型",
        label_visibility="collapsed"
    )

    if st.button("解析Schema", key="parse_manual_schema", type="primary"):
        try:
            schema_dict = yaml.safe_load(yaml_input)

            if not schema_dict or 'entities' not in schema_dict:
                st.error("Schema格式不正确，必须包含 'entities' 字段")
                return None, ""

            st.success("解析成功")
            render_schema_visualization(schema_dict, yaml_input)

            return schema_dict, yaml_input

        except yaml.YAMLError as e:
            st.error(f"YAML解析错误: {e}")
            return None, ""

    return None, ""


def render_schema_visualization(schema_dict: Dict, schema_yaml_str: str = ""):
    """渲染 Schema 可视化（结构图 / 明细表 / 原始 YAML 三栏切换）"""
    tab_graph, tab_detail, tab_yaml = st.tabs(["📊 结构图", "📋 明细表", "📝 原始 YAML"])

    with tab_graph:
        st.caption("实体为节点，关系为带箭头连线；悬浮节点可查看属性。")
        st.markdown(render_schema_graph(schema_dict), unsafe_allow_html=True)

    with tab_detail:
        render_schema_preview(schema_dict)

    with tab_yaml:
        if schema_yaml_str:
            st.code(schema_yaml_str, language="yaml")
        else:
            st.caption("无 YAML 内容")


def render_schema_preview(schema_dict: Dict):
    """渲染Schema预览 - 紧凑直观的图谱结构展示"""
    entities = schema_dict.get('entities', [])
    relationships = schema_dict.get('relationships', [])

    # ---- 顶部统计条 ----
    total_props = sum(len(e.get('properties', [])) for e in entities)
    stat_html = (
        '<div style="display: flex; gap: 1.5rem; margin-bottom: 0.75rem; font-size: 0.8rem; color: #6B7280;">'
        f'<span>📋 {len(entities)} 个实体</span>'
        f'<span>🔗 {len(relationships)} 个关系</span>'
        f'<span>🏷️ {total_props} 个属性</span>'
        '</div>'
    )
    st.markdown(stat_html, unsafe_allow_html=True)

    # ---- 实体表格 ----
    entity_header = (
        '<div style="display: grid; grid-template-columns: 100px 1fr; gap: 0; '
        'background: #4F46E5; color: #FFFFFF; font-size: 0.75rem; font-weight: 600; '
        'border-radius: 6px 6px 0 0; overflow: hidden;">'
        '<div style="padding: 6px 10px;">实体类型</div>'
        '<div style="padding: 6px 10px;">属性字段</div>'
        '</div>'
    )

    entity_rows = ""
    for i, entity in enumerate(entities):
        props = entity.get('properties', [])
        # 属性标签：每个属性一个小标签
        prop_tags = ""
        for p in props:
            prop_tags += (
                f'<span style="display: inline-block; background: #EEF2FF; color: #3730A3; '
                f'font-size: 0.7rem; padding: 1px 6px; border-radius: 3px; margin: 1px 2px; '
                f'white-space: nowrap;">{html_escape(str(p))}</span>'
            )
        if not prop_tags:
            prop_tags = '<span style="color: #9CA3AF; font-size: 0.7rem;">无属性</span>'

        bg = "#FFFFFF" if i % 2 == 0 else "#F9FAFB"
        entity_rows += (
            f'<div style="display: grid; grid-template-columns: 100px 1fr; gap: 0; background: {bg}; '
            f'border-bottom: 1px solid #F1F5F9; font-size: 0.78rem;">'
            f'<div style="padding: 5px 10px; font-weight: 600; color: #1F2937;">{html_escape(str(entity.get("name", "未命名")))}</div>'
            f'<div style="padding: 5px 10px; line-height: 1.6;">{prop_tags}</div>'
            f'</div>'
        )

    entity_table = (
        '<div style="border: 1px solid #E5E7EB; border-radius: 6px; overflow: hidden; margin-bottom: 0.75rem;">'
        f'{entity_header}{entity_rows}'
        '</div>'
    )
    st.markdown(entity_table, unsafe_allow_html=True)

    # ---- 关系图 ----
    rel_header = (
        '<div style="display: grid; grid-template-columns: 1fr auto 1fr; gap: 0; '
        'background: #4F46E5; color: #FFFFFF; font-size: 0.75rem; font-weight: 600; '
        'border-radius: 6px 6px 0 0; overflow: hidden;">'
        '<div style="padding: 6px 10px;">头实体</div>'
        '<div style="padding: 6px 10px; text-align: center;">关系</div>'
        '<div style="padding: 6px 10px;">尾实体</div>'
        '</div>'
    )

    # 构建实体颜色映射
    entity_color_map = {}
    color_palette = [
        '#EEF2FF', '#FEF3C7', '#ECFDF5', '#FFF7ED', '#FDF2F8',
        '#F0F9FF', '#F5F3FF', '#FFFBEB', '#F0FDF4', '#FEF2F2'
    ]
    text_palette = [
        '#3730A3', '#92400E', '#065F46', '#9A3412', '#9D174D',
        '#0369A1', '#6D28D9', '#854D0E', '#166534', '#991B1B'
    ]
    for i, entity in enumerate(entities):
        entity_color_map[entity.get('name')] = (
            color_palette[i % len(color_palette)],
            text_palette[i % len(text_palette)]
        )

    rel_rows = ""
    for i, rel in enumerate(relationships):
        head_name = html_escape(str(rel.get('head', '?')))
        rel_name = html_escape(str(rel.get('relation', '?')))
        tail_name = html_escape(str(rel.get('tail', '?')))

        head_bg, head_color = entity_color_map.get(rel.get('head'), ('#F3F4F6', '#374151'))
        tail_bg, tail_color = entity_color_map.get(rel.get('tail'), ('#F3F4F6', '#374151'))

        bg = "#FFFFFF" if i % 2 == 0 else "#F9FAFB"
        rel_rows += (
            f'<div style="display: grid; grid-template-columns: 1fr auto 1fr; gap: 0; background: {bg}; '
            f'border-bottom: 1px solid #F1F5F9; font-size: 0.78rem; align-items: center;">'
            f'<div style="padding: 5px 10px;"><span style="background: {head_bg}; color: {head_color}; '
            f'padding: 1px 8px; border-radius: 4px; font-weight: 600;">{head_name}</span></div>'
            f'<div style="padding: 5px 8px; text-align: center; color: #6B7280; font-size: 0.72rem; white-space: nowrap;">'
            f'→ {rel_name} →</div>'
            f'<div style="padding: 5px 10px;"><span style="background: {tail_bg}; color: {tail_color}; '
            f'padding: 1px 8px; border-radius: 4px; font-weight: 600;">{tail_name}</span></div>'
            f'</div>'
        )

    rel_table = (
        '<div style="border: 1px solid #E5E7EB; border-radius: 6px; overflow: hidden;">'
        f'{rel_header}{rel_rows}'
        '</div>'
    )
    st.markdown(rel_table, unsafe_allow_html=True)


def validate_schema(schema_dict: Dict) -> Tuple[bool, str]:
    """
    验证Schema格式
    """
    if not schema_dict:
        return False, "Schema为空"

    if 'entities' not in schema_dict:
        return False, "缺少 'entities' 字段"

    entities = schema_dict['entities']
    if not isinstance(entities, list) or len(entities) == 0:
        return False, "'entities' 必须是非空列表"

    entity_names = set()
    for entity in entities:
        if 'name' not in entity:
            return False, "实体缺少 'name' 字段"
        entity_names.add(entity['name'])

    relationships = schema_dict.get('relationships', [])
    for rel in relationships:
        if 'head' not in rel or 'relation' not in rel or 'tail' not in rel:
            return False, f"关系格式不正确: {rel}"
        if rel['head'] not in entity_names:
            return False, f"关系引用的实体 '{rel['head']}' 不存在"
        if rel['tail'] not in entity_names:
            return False, f"关系引用的实体 '{rel['tail']}' 不存在"

    return True, ""
