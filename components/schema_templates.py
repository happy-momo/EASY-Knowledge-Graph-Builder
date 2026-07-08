"""
Schema模板选择组件（专业版）
使用高对比度配色和清晰的视觉层次
"""

import streamlit as st
import yaml
from typing import Dict, Any, Optional, Tuple

from config.app_config import SCHEMA_TEMPLATES, HELP_TEXTS


def render_schema_selection() -> Tuple[Optional[Dict], str]:
    """
    渲染Schema选择界面（专业版）
    """
    st.markdown('<h3 style="color: #000000; margin-bottom: 0.5rem;">选择Schema配置方式</h3>', unsafe_allow_html=True)

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
    """渲染模板选择界面（专业版）"""
    template_names = list(SCHEMA_TEMPLATES.keys())
    cols = st.columns(2)

    for i, name in enumerate(template_names):
        template = SCHEMA_TEMPLATES[name]
        col = cols[i % 2]

        is_selected = st.session_state.get('selected_template') == name

        # 使用 info-card 替代全背景色卡片
        border_color = "#4F46E5" if is_selected else "#E2E8F0"
        left_border = "4px solid #4F46E5" if is_selected else "4px solid transparent"

        card_html = f"""
        <div style="padding: 1rem; margin-bottom: 0.5rem;
                    background: #FFFFFF; border: 1px solid {border_color};
                    border-left: {left_border};
                    border-radius: 10px;
                    box-shadow: {'0 2px 4px rgba(0,0,0,0.06)' if is_selected else '0 1px 2px rgba(0,0,0,0.04)'}">
            <div style="font-weight: 600; color: #000000; margin-bottom: 0.35rem; font-size: 1rem;">
                {name}
            </div>
            <div style="color: #000000; font-size: 0.875rem; margin-bottom: 0.5rem;">
                {template['description']}
            </div>
            <div style="color: #000000; font-size: 0.8rem;">
                实体: {len(template['entities'])}种 | 关系: {len(template['relationships'])}种
            </div>
        </div>
        """.strip()

        if st.button("选择", key=f"template_{name}", use_container_width=True):
            st.session_state['selected_template'] = name
            st.rerun()

        st.markdown(card_html, unsafe_allow_html=True)

    selected_name = st.session_state.get('selected_template')
    if selected_name and selected_name in SCHEMA_TEMPLATES:
        schema_dict = SCHEMA_TEMPLATES[selected_name]
        schema_yaml_str = yaml.dump(schema_dict, allow_unicode=True, sort_keys=False)

        st.markdown('<p style="color: #000000; font-weight: 600; margin: 1rem 0 0.5rem 0;">Schema预览</p>', unsafe_allow_html=True)
        render_schema_preview(schema_dict)

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
            render_schema_preview(schema_dict)

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

    st.markdown('<p style="color: #000000; font-weight: 600; margin-bottom: 0.25rem;">输入YAML Schema</p>', unsafe_allow_html=True)
    yaml_input = st.text_area(
        "",
        value=default_yaml,
        height=250,
        help="定义实体类型、属性和关系类型"
    )

    if st.button("解析Schema", key="parse_manual_schema", type="primary"):
        try:
            schema_dict = yaml.safe_load(yaml_input)

            if not schema_dict or 'entities' not in schema_dict:
                st.error("Schema格式不正确，必须包含 'entities' 字段")
                return None, ""

            st.success("解析成功")
            render_schema_preview(schema_dict)

            return schema_dict, yaml_input

        except yaml.YAMLError as e:
            st.error(f"YAML解析错误: {e}")
            return None, ""

    return None, ""


def render_schema_preview(schema_dict: Dict):
    """渲染Schema预览（专业版）- 使用 info-panel 替代 terminal"""
    entities = schema_dict.get('entities', [])
    relationships = schema_dict.get('relationships', [])

    # 构建 info-panel 内容
    entity_rows = ""
    for i, entity in enumerate(entities):
        props = entity.get('properties', [])
        props_str = ', '.join(props[:3])
        if len(props) > 3:
            props_str += f'... (+{len(props)-3})'
        entity_rows += (
            f'<div style="display: flex; justify-content: space-between; align-items: center; '
            f'padding: 8px 0; border-bottom: 1px solid #F1F5F9;">'
            f'<span style="color: #000000; font-size: 0.875rem; font-weight: 500;">{entity["name"]}</span>'
            f'<span style="color: #000000; font-size: 0.875rem; font-weight: 400;">{props_str}</span>'
            '</div>'
        )

    rel_rows = ""
    for i, rel in enumerate(relationships):
        rel_rows += (
            f'<div style="display: flex; justify-content: space-between; align-items: center; '
            f'padding: 8px 0; border-bottom: 1px solid #F1F5F9;">'
            f'<span style="color: #000000; font-size: 0.875rem; font-weight: 500;">{rel["head"]}</span>'
            f'<span style="color: #000000; font-size: 0.875rem; font-weight: 400;">--{rel["relation"]}--&gt; {rel["tail"]}</span>'
            '</div>'
        )

    panel_html = f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px; margin-bottom: 1rem;">
        <div style="font-weight: 600; color: #000000; font-size: 0.95rem; margin-bottom: 0.75rem;">
            Schema Analysis
        </div>
        <div style="font-weight: 600; color: #000000; font-size: 0.75rem; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em;">
            Entities ({len(entities)})
        </div>
        {entity_rows}
        <div style="font-weight: 600; color: #000000; font-size: 0.75rem; margin: 0.75rem 0 0.5rem 0; text-transform: uppercase; letter-spacing: 0.05em;">
            Relationships ({len(relationships)})
        </div>
        {rel_rows}
    </div>
    """.strip()

    st.markdown(panel_html, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("实体类型", len(entities))
    with col2:
        st.metric("关系类型", len(relationships))
    with col3:
        total_props = sum(len(e.get('properties', [])) for e in entities)
        st.metric("属性总数", total_props)


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
