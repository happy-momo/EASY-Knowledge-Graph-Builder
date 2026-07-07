"""
Schema模板选择组件
"""

import streamlit as st
import yaml
from typing import Dict, Any, Optional, Tuple

from config.app_config import SCHEMA_TEMPLATES, HELP_TEXTS


def render_schema_selection() -> Tuple[Optional[Dict], str]:
    """
    渲染Schema选择界面

    Returns:
        (schema_dict, schema_yaml_str) 或 (None, "")
    """
    st.markdown("### 选择Schema配置方式")

    # 选择方式
    selection_mode = st.radio(
        "配置方式",
        options=["template", "upload", "manual"],
        format_func=lambda x: {
            "template": "📋 选择预设模板",
            "upload": "📄 上传YAML文件",
            "manual": "✏️ 手动输入"
        }[x],
        horizontal=True,
        key="schema_mode"
    )

    st.markdown("---")

    schema_dict = None
    schema_yaml_str = ""

    if selection_mode == "template":
        # 模板选择
        schema_dict, schema_yaml_str = render_template_selection()

    elif selection_mode == "upload":
        # 上传文件
        schema_dict, schema_yaml_str = render_yaml_upload()

    else:
        # 手动输入
        schema_dict, schema_yaml_str = render_manual_input()

    return schema_dict, schema_yaml_str


def render_template_selection() -> Tuple[Optional[Dict], str]:
    """渲染模板选择界面"""

    # 模板卡片
    template_names = list(SCHEMA_TEMPLATES.keys())
    cols = st.columns(2)

    for i, name in enumerate(template_names):
        template = SCHEMA_TEMPLATES[name]
        col = cols[i % 2]

        with col:
            # 模板卡片
            is_selected = st.session_state.get('selected_template') == name

            card_html = f"""
            <div class="selection-card {'selected' if is_selected else ''}"
                 style="padding: 1rem; margin-bottom: 0.75rem;">
                <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">
                    {name}
                </div>
                <div style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">
                    {template['description']}
                </div>
                <div style="color: var(--text-secondary); font-size: 0.8rem;">
                    实体: {len(template['entities'])}种 | 关系: {len(template['relationships'])}种
                </div>
            </div>
            """

            if st.button(f"选择", key=f"template_{name}", use_container_width=True):
                st.session_state['selected_template'] = name
                st.rerun()

            st.markdown(card_html, unsafe_allow_html=True)

    # 获取选中的模板
    selected_name = st.session_state.get('selected_template')
    if selected_name and selected_name in SCHEMA_TEMPLATES:
        schema_dict = SCHEMA_TEMPLATES[selected_name]
        schema_yaml_str = yaml.dump(schema_dict, allow_unicode=True, sort_keys=False)

        # 显示预览
        st.markdown("**Schema预览：**")
        render_schema_preview(schema_dict)

        return schema_dict, schema_yaml_str

    return None, ""


def render_yaml_upload() -> Tuple[Optional[Dict], str]:
    """渲染YAML上传界面"""

    uploaded_file = st.file_uploader(
        "上传YAML Schema文件",
        type=["yaml", "yml"],
        help=HELP_TEXTS.get("schema_yaml", "")
    )

    if uploaded_file:
        try:
            schema_dict = yaml.safe_load(uploaded_file)

            # 验证基本结构
            if 'entities' not in schema_dict:
                st.error("Schema必须包含 'entities' 字段")
                return None, ""

            schema_yaml_str = yaml.dump(schema_dict, allow_unicode=True, sort_keys=False)

            # 显示解析结果
            st.success(f"✅ 解析成功：{uploaded_file.name}")
            render_schema_preview(schema_dict)

            return schema_dict, schema_yaml_str

        except yaml.YAMLError as e:
            st.error(f"YAML解析错误: {e}")
            return None, ""

    return None, ""


def render_manual_input() -> Tuple[Optional[Dict], str]:
    """渲染手动输入界面"""

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

    yaml_input = st.text_area(
        "输入YAML Schema",
        value=default_yaml,
        height=250,
        help="定义实体类型、属性和关系类型"
    )

    if st.button("解析Schema", key="parse_manual_schema"):
        try:
            schema_dict = yaml.safe_load(yaml_input)

            if not schema_dict or 'entities' not in schema_dict:
                st.error("Schema格式不正确，必须包含 'entities' 字段")
                return None, ""

            st.success("✅ 解析成功")
            render_schema_preview(schema_dict)

            return schema_dict, yaml_input

        except yaml.YAMLError as e:
            st.error(f"YAML解析错误: {e}")
            return None, ""

    return None, ""


def render_schema_preview(schema_dict: Dict):
    """
    渲染Schema预览

    Args:
        schema_dict: Schema字典
    """
    entities = schema_dict.get('entities', [])
    relationships = schema_dict.get('relationships', [])

    # 终端风格显示
    terminal_html = """
    <div class="terminal-container">
        <div class="terminal-header">
            <div class="terminal-dot close"></div>
            <div class="terminal-dot minimize"></div>
            <div class="terminal-dot maximize"></div>
            <div class="terminal-title">Schema Analysis</div>
        </div>
        <div class="terminal">
            <span class="command">$</span> <span class="path">analyze-schema</span>
            <br><br>
            <span class="success">✓</span> <span class="info">Schema loaded successfully</span>
            <br><br>
    """

    # 实体列表
    terminal_html += '<span class="info">Entities defined:</span><br>'
    for i, entity in enumerate(entities):
        props = entity.get('properties', [])
        props_str = ', '.join(props[:3])
        if len(props) > 3:
            props_str += f'... (+{len(props)-3})'
        terminal_html += f'<span class="sentence">[{i+1:2d}] {entity["name"]} ({props_str})</span><br>'

    terminal_html += '<br>'

    # 关系列表
    terminal_html += '<span class="info">Relationships defined:</span><br>'
    for i, rel in enumerate(relationships):
        terminal_html += f'<span class="sentence">[{i+1:2d}] {rel["head"]} --{rel["relation"]}--> {rel["tail"]}</span><br>'

    terminal_html += """
        </div>
    </div>
    """

    st.markdown(terminal_html, unsafe_allow_html=True)

    # 统计信息
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

    Args:
        schema_dict: Schema字典

    Returns:
        (是否有效, 错误信息)
    """
    if not schema_dict:
        return False, "Schema为空"

    if 'entities' not in schema_dict:
        return False, "缺少 'entities' 字段"

    entities = schema_dict['entities']
    if not isinstance(entities, list) or len(entities) == 0:
        return False, "'entities' 必须是非空列表"

    # 检查实体格式
    entity_names = set()
    for entity in entities:
        if 'name' not in entity:
            return False, "实体缺少 'name' 字段"
        entity_names.add(entity['name'])

    # 检查关系格式
    relationships = schema_dict.get('relationships', [])
    for rel in relationships:
        if 'head' not in rel or 'relation' not in rel or 'tail' not in rel:
            return False, f"关系格式不正确: {rel}"

        # 检查关系引用的实体是否存在
        if rel['head'] not in entity_names:
            return False, f"关系引用的实体 '{rel['head']}' 不存在"
        if rel['tail'] not in entity_names:
            return False, f"关系引用的实体 '{rel['tail']}' 不存在"

    return True, ""