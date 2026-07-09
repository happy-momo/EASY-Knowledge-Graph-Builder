"""
欢迎引导页 - 简化版

用户只需配置：厂商、API 端点、API Key、模型名称
"""

import streamlit as st
from html import escape as html_escape

# SVG 图标
_ICONS = {
    "schema": '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/><path d="M9 14l2 2 4-4"/></svg>',
    "import": '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><polyline points="9 15 12 12 15 15"/></svg>',
    "extract": '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83"/><path d="M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg>',
    "review": '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
    "database": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',
    "zap": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "check": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    "api": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/><line x1="14" y1="4" x2="10" y2="20"/></svg>',
}


def render_welcome_page():
    """渲染欢迎页"""
    from utils.llm_config import PROVIDER_DEFAULTS, LLMConfig, test_llm_connection
    from utils.neo4j_manager import Neo4jManager
    from config.app_config import DEFAULT_CONFIG

    # ---- Hero ----
    st.markdown(
        '<div style="text-align: center; padding: 2rem 0 1.5rem 0;">'
        '<h1 style="font-size: 2rem; margin-bottom: 0.35rem; color: var(--text-primary);">KG AI Builder</h1>'
        '<p style="color: var(--text-secondary); font-size: 0.95rem; margin: 0;">从文本到知识图谱的智能转换</p>'
        '</div>',
        unsafe_allow_html=True
    )

    # ---- 工作流步骤 ----
    steps = [
        ("Schema", "定义结构", "schema"),
        ("导入", "上传文档", "import"),
        ("抽取", "LLM 驱动", "extract"),
        ("入库", "确认存储", "review"),
    ]
    steps_html = '<div style="display: flex; gap: 0.75rem; margin-bottom: 1.5rem;">'
    for title, desc, icon_key in steps:
        steps_html += (
            f'<div class="feature-card" style="flex: 1; padding: 0.75rem;">'
            f'<div style="color: var(--color-primary-600); margin-bottom: 0.5rem;">{_ICONS[icon_key]}</div>'
            f'<div style="font-weight: 600; color: var(--text-primary); font-size: 0.85rem; margin-bottom: 0.15rem;">{title}</div>'
            f'<div style="color: var(--text-tertiary); font-size: 0.75rem;">{desc}</div>'
            f'</div>'
        )
    steps_html += '</div>'
    st.markdown(steps_html, unsafe_allow_html=True)

    # ---- 快速连接区 ----
    st.markdown(
        '<div style="font-weight: 600; color: var(--text-primary); font-size: 0.95rem; margin-bottom: 0.75rem;">'
        f'{_ICONS["zap"]} 快速连接</div>',
        unsafe_allow_html=True
    )

    col_llm, col_neo4j = st.columns(2)

    with col_llm:
        _render_llm_quick_connect(PROVIDER_DEFAULTS, LLMConfig, test_llm_connection)

    with col_neo4j:
        _render_neo4j_quick_connect(DEFAULT_CONFIG, Neo4jManager)

    # ---- 开始按钮 ----
    st.markdown('<hr style="border: none; border-top: 1px solid var(--border-light); margin: 1.25rem 0;">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("开始构建知识图谱", type="primary", use_container_width=True):
            return "start"

    return None


def _render_llm_quick_connect(provider_defaults, LLMConfigCls, test_llm_fn):
    """渲染 LLM 快速连接面板 - 简化版"""
    st.markdown(
        f'<div class="quick-connect-header">{_ICONS["zap"]} LLM 模型</div>',
        unsafe_allow_html=True
    )

    # 厂商选择
    provider_options = {
        "openai": "OpenAI",
        "zhipu": "智谱 AI",
        "alibaba": "阿里云通义千问",
        "deepseek": "深度求索",
        "moonshot": "月之暗面 Kimi",
        "anthropic": "Anthropic Claude",
        "google": "Google Gemini",
        "custom": "自定义",
    }

    selected_provider = st.selectbox(
        "厂商",
        options=list(provider_options.keys()),
        format_func=lambda x: provider_options[x],
        key="quick_llm_provider"
    )

    # 获取默认值
    defaults = provider_defaults.get(selected_provider, provider_defaults["custom"])

    # API 端点
    default_endpoint = defaults.get("api_endpoint", "")
    api_endpoint = st.text_input(
        "API 端点",
        value=default_endpoint if selected_provider != "custom" else "https://",
        key="quick_llm_endpoint"
    )

    # 模型名称
    default_model = ""
    if selected_provider == "openai":
        default_model = "gpt-4o"
    elif selected_provider == "zhipu":
        default_model = "glm-4"
    elif selected_provider == "alibaba":
        default_model = "qwen-turbo"
    elif selected_provider == "deepseek":
        default_model = "deepseek-chat"
    elif selected_provider == "moonshot":
        default_model = "moonshot-v1-8k"
    elif selected_provider == "anthropic":
        default_model = "claude-3-opus-20240229"
    elif selected_provider == "google":
        default_model = "gemini-pro"

    model_name = st.text_input(
        "模型名称",
        value=default_model,
        key="quick_llm_model"
    )

    # API Key
    from utils.llm_config import get_api_key_from_env
    env_key = get_api_key_from_env(selected_provider)
    if env_key:
        st.markdown(
            '<div style="background: var(--color-success-bg); border: 1px solid var(--color-success); '
            'border-radius: var(--radius-sm); padding: 6px 10px; font-size: 0.8rem; color: var(--text-success);">'
            f'✓ 已检测到 API Key ({env_key[:8]}...)'
            '</div>',
            unsafe_allow_html=True
        )
        api_key = st.text_input("API Key", value=env_key, type="password", key="quick_llm_apikey")
    else:
        api_key = st.text_input("API Key", type="password", key="quick_llm_apikey")

    # 测试连接
    if api_endpoint and api_key and model_name:
        if st.button("测试连接", key="quick_test_llm", use_container_width=True):
            with st.spinner("测试中..."):
                config = LLMConfigCls(
                    api_endpoint=api_endpoint,
                    api_key=api_key,
                    model_name=model_name,
                    provider=selected_provider
                )
                success, message = test_llm_fn(config)
                if success:
                    st.success("连接成功")
                else:
                    st.error(f"连接失败：{message[:80]}")

    # 保存配置
    if api_endpoint and api_key and model_name:
        config = LLMConfigCls(
            api_endpoint=api_endpoint,
            api_key=api_key,
            model_name=model_name,
            provider=selected_provider
        )
        st.session_state['quick_llm_config'] = config.to_dict()


def _render_neo4j_quick_connect(DEFAULT_CONFIG, Neo4jManager):
    """渲染 Neo4j 快速连接面板"""
    st.markdown(
        f'<div class="quick-connect-header">{_ICONS["database"]} Neo4j 数据库</div>',
        unsafe_allow_html=True
    )

    neo4j_password = st.text_input(
        "Neo4j 密码",
        type="password",
        placeholder="输入密码",
        key="quick_neo4j_pwd"
    )

    if neo4j_password:
        neo4j_uri = DEFAULT_CONFIG['neo4j_uri']
        neo4j_user = DEFAULT_CONFIG['neo4j_user']

        if st.button("测试连接", key="quick_test_neo4j", use_container_width=True):
            with st.spinner("测试中..."):
                manager = Neo4jManager(neo4j_uri, neo4j_user, neo4j_password)
                success, message = manager.test_connection()
                if success:
                    st.success("连接成功")
                else:
                    st.error(f"连接失败：{message[:80]}")
                manager.close()

        st.session_state['quick_neo4j_config'] = {
            "uri": neo4j_uri,
            "user": neo4j_user,
            "password": neo4j_password
        }


def render_help_section():
    """渲染帮助说明"""
    with st.expander("使用帮助", expanded=False):
        st.markdown("""
        **步骤 1: Schema 配置** — 选择预设模板或上传自定义 YAML 文件

        **步骤 2: 文档导入** — 上传文件或导入文件夹

        **步骤 3: 配置连接** — 选择厂商，输入 API 端点、Key 和模型名称

        **步骤 4: 抽取处理** — LLM 驱动的知识抽取

        **步骤 5: 审核** — 自动或人工审核三元组

        **步骤 6: 完成** — 查看统计，在 Neo4j 中查看知识图谱
        """)
