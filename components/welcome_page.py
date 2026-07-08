"""
欢迎引导页组件（专业版）
使用SVG图标替代Emoji，高对比度配色，专业视觉层次
"""

import streamlit as st


# SVG Icon library for consistent iconography
_ICONS = {
    "schema": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24"'
        ' fill="none" stroke="#4F46E5" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>'
        '<rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>'
        '<path d="M9 14l2 2 4-4"/>'
        '</svg>'
    ),
    "import": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24"'
        ' fill="none" stroke="#4F46E5" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
        '<polyline points="14 2 14 8 20 8"/>'
        '<line x1="12" y1="18" x2="12" y2="12"/>'
        '<polyline points="9 15 12 12 15 15"/>'
        '</svg>'
    ),
    "extract": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24"'
        ' fill="none" stroke="#4F46E5" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83"/>'
        '<path d="M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>'
        '</svg>'
    ),
    "review": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24"'
        ' fill="none" stroke="#4F46E5" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M9 11l3 3L22 4"/>'
        '<path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>'
        '</svg>'
    ),
    "database": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"'
        ' fill="none" stroke="#000000" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
        '<ellipse cx="12" cy="5" rx="9" ry="3"/>'
        '<path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>'
        '<path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>'
        '</svg>'
    ),
    "api": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"'
        ' fill="none" stroke="#000000" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="16 18 22 12 16 6"/>'
        '<polyline points="8 6 2 12 8 18"/>'
        '<line x1="14" y1="4" x2="10" y2="20"/>'
        '</svg>'
    ),
    "check": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"'
        ' fill="none" stroke="#059669" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="20 6 9 17 4 12"/>'
        '</svg>'
    ),
    "warning": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"'
        ' fill="none" stroke="#D97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
        '<line x1="12" y1="9" x2="12" y2="13"/>'
        '<line x1="12" y1="17" x2="12.01" y2="17"/>'
        '</svg>'
    ),
    "help": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"'
        ' fill="none" stroke="#4F46E5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="10"/>'
        '<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>'
        '<line x1="12" y1="17" x2="12.01" y2="17"/>'
        '</svg>'
    ),
    "docker": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"'
        ' fill="none" stroke="#4F46E5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>'
        '<polyline points="7.5 4.21 12 6.81 16.5 4.21"/>'
        '<polyline points="7.5 19.79 7.5 14.6 3 12"/>'
        '<polyline points="21 12 16.5 14.6 16.5 19.79"/>'
        '<polyline points="3.27 6.96 12 12.01 20.73 6.96"/>'
        '<line x1="12" y1="22.08" x2="12" y2="12"/>'
        '</svg>'
    ),
}


def _icon_svg(icon_name: str) -> str:
    """Get SVG icon as HTML string"""
    return _ICONS.get(icon_name, _ICONS["help"])


def render_welcome_page():
    """渲染欢迎引导页 - 专业版"""

    from utils.env_checker import check_all_api_keys, get_environment_status

    env_status = get_environment_status()
    api_keys_status = check_all_api_keys()

    # Hero 区域 - 使用纯色标题替代渐变文字
    hero_html = f"""
    <div style="text-align: center; padding: 2.5rem 0 2rem 0; margin-bottom: 2rem;">
        <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem; color: #000000;">
            KG AI Builder
        </h1>
        <p style="color: #000000; font-size: 1.15rem; margin: 0;">
            从文本到知识图谱的智能转换
        </p>
    </div>
    """.strip()
    st.markdown(hero_html, unsafe_allow_html=True)

    # 功能介绍卡片 - 使用 feature-card 类
    features = [
        ("Schema配置", "定义知识结构", "schema"),
        ("文档导入", "上传或批量处理", "import"),
        ("智能抽取", "LLM驱动的知识提取", "extract"),
        ("审核入库", "确认后存入Neo4j", "review"),
    ]

    feature_html = '<div style="display: flex; gap: 1rem; margin-bottom: 2rem;">'
    for title, desc, icon_key in features:
        icon_svg = _ICONS.get(icon_key, _ICONS["help"])
        feature_html += (
            '<div class="feature-card" style="flex: 1;">'
            f'<div style="margin-bottom: 0.75rem;">{icon_svg}</div>'
            f'<div style="font-weight: 600; color: #000000; margin-bottom: 0.35rem; font-size: 1rem;">{title}</div>'
            f'<div style="color: #000000; font-size: 0.875rem;">{desc}</div>'
            '</div>'
        )
    feature_html += '</div>'
    st.markdown(feature_html, unsafe_allow_html=True)

    st.markdown('<hr style="border: none; border-top: 1px solid #E2E8F0; margin: 1.5rem 0;">', unsafe_allow_html=True)

    # 环境状态检测
    st.markdown('<h3 style="color: #000000; font-size: 1.1rem; margin-bottom: 1rem;">环境状态检测</h3>', unsafe_allow_html=True)

    # Neo4j 状态 - 使用 info-card
    neo4j_html = f"""
    <div class="info-card" style="margin-bottom: 0.75rem;">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            {_ICONS["database"]}
            <div style="flex: 1;">
                <div style="font-weight: 500; color: #000000;">Neo4j 数据库</div>
                <div style="color: #000000; font-size: 0.85rem;">连接将在配置步骤中检测</div>
            </div>
            <span style="color: #000000; font-size: 0.85rem; font-weight: 500;">待检测</span>
        </div>
    </div>
    """.strip()
    st.markdown(neo4j_html, unsafe_allow_html=True)

    # API Key 状态
    st.markdown('<h4 style="color: #000000; margin: 1rem 0 0.5rem 0; font-size: 0.95rem;">API Key 配置状态</h4>', unsafe_allow_html=True)

    api_key_html = ""
    for provider, status in api_keys_status.items():
        icon = _ICONS["check"] if status.configured else _ICONS["api"]
        key_info = f" ({status.key_prefix})" if status.key_prefix else ""
        source_info = f" [{status.source}]" if status.source else ""
        border_color = "#059669" if status.configured else "#CBD5E1"

        api_key_html += (
            '<div class="info-card" style="margin-bottom: 0.5rem; border-left-color: '
            f'{border_color};">'
            '<div style="display: flex; align-items: center; gap: 0.75rem;">'
            f'{icon}'
            '<div style="flex: 1;">'
            f'<span style="color: #000000; font-weight: 500;">{provider.upper()}</span>'
            f'<span style="color: #000000; font-size: 0.85rem; margin-left: 0.5rem;">{key_info}{source_info}</span>'
            '</div>'
            '</div></div>'
        )

    st.markdown(api_key_html, unsafe_allow_html=True)

    # 建议
    if env_status.get('recommendations'):
        for rec in env_status['recommendations']:
            if rec['type'] == 'warning':
                st.markdown(
                    '<div style="background-color: #FEF3C7; border: 1px solid #F59E0B; '
                    'border-radius: 8px; padding: 12px 16px; margin: 8px 0; '
                    'color: #000000; font-size: 0.9rem;">'
                    f'⚠️ {rec["message"]}'
                    '<br><span style="font-size: 0.8rem; color: #000000;">'
                    f'{rec["action"]}</span></div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div style="background-color: #DBEAFE; border: 1px solid #93C5FD; '
                    'border-radius: 8px; padding: 12px 16px; margin: 8px 0; '
                    'color: #000000; font-size: 0.9rem;">'
                    f'ℹ️ {rec["message"]}'
                    '<br><span style="font-size: 0.8rem; color: #000000;">'
                    f'{rec["action"]}</span></div>',
                    unsafe_allow_html=True
                )

    st.markdown('<hr style="border: none; border-top: 1px solid #E2E8F0; margin: 1.5rem 0;">', unsafe_allow_html=True)

    # 开始按钮
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("开始构建知识图谱", type="primary", use_container_width=True):
            return "start"

    # 底部链接
    footer_html = f"""
    <div style="text-align: center; margin-top: 1.5rem; color: #000000;">
        <span style="margin-right: 2rem;">
            {_ICONS["help"]} <span style="color: #4F46E5; font-weight: 500;">使用帮助</span>
        </span>
        <span>
            {_ICONS["docker"]} <span style="color: #4F46E5; font-weight: 500;">Docker部署</span>
        </span>
    </div>
    """.strip()
    st.markdown(footer_html, unsafe_allow_html=True)

    return None


def render_help_section():
    """渲染帮助说明"""
    with st.expander("使用帮助", expanded=False):
        st.markdown("""
        ### 快速开始指南

        **步骤 1: Schema配置**
        - 选择预设模板或上传自定义YAML文件
        - Schema定义了知识图谱中包含哪些实体类型和关系类型

        **步骤 2: 文档导入**
        - 上传单个文件（PDF/DOCX/XLSX）
        - 或导入整个文件夹批量处理
        - 系统会自动将文档分割成语义块

        **步骤 3: 配置连接**
        - 选择LLM模型并输入API Key
        - 配置Neo4j数据库连接

        **步骤 4: 抽取处理**
        - 系统逐块处理文本，使用LLM抽取三元组
        - 实时显示进度和抽取结果

        **步骤 5: 审核**
        - 自动审核模式：直接存入数据库
        - 人工审核模式：逐个确认三元组

        **步骤 6: 完成**
        - 查看处理统计
        - 在Neo4j Browser中查看知识图谱
        """)


def render_docker_help():
    """渲染Docker部署帮助"""
    with st.expander("Docker部署", expanded=False):
        st.markdown("""
        ### Docker一键部署

        ```bash
        # 克隆项目
        git clone https://github.com/happy-momo/EASY-Knowledge-Graph-Builder.git

        # 进入项目目录
        cd EASY-Knowledge-Graph-Builder

        # 启动Docker
        docker-compose up -d

        # 访问应用
        # KG Builder: http://localhost:8501
        # Neo4j Browser: http://localhost:7474
        ```

        **默认配置：**
        - Neo4j 用户名: neo4j
        - Neo4j 密码: password123
        """)
