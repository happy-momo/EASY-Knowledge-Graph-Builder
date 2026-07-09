"""
欢迎引导页 - 简化 LLM 配置 UI
用户只需选择厂商，配置 URL、API Key 和模型名称
"""

import streamlit as st
from html import escape as html_escape

# 统一色彩体系中的 SVG 图标
_ICONS = {
    "schema": '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/><path d="M9 14l2 2 4-4"/></svg>',
    "import": '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><polyline points="9 15 12 12 15 15"/></svg>',
    "extract": '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83"/><path d="M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg>',
    "review": '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
    "database": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',
    "api": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/><line x1="14" y1="4" x2="10" y2="20"/></svg>',
    "check": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    "plug": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22v-5"/><path d="M9 7V2"/><path d="M15 7V2"/><path d="M6 13V8h12v5a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4z"/></svg>',
    "zap": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
}

# 厂商中文名称映射
PROVIDER_NAMES = {
    "zhipu": "智谱 AI",
    "openai": "OpenAI",
    "anthropic": "Anthropic (Claude)",
    "google": "Google (Gemini)",
    "alibaba": "阿里云 (通义千问)",
    "deepseek": "深度求索 (DeepSeek)",
    "moonshot": "月之暗面 (Kimi)",
    "custom": "自定义",
}


def render_welcome_page():
    """渲染欢迎页 - 环境检测 + 快速连接"""

    from utils.env_checker import check_all_api_keys, get_environment_status
    from utils.llm_config import get_preset_configs, get_api_key_from_env, LLMConfig, test_llm_connection
    from utils.neo4j_manager import Neo4jManager
    from config.app_config import DEFAULT_CONFIG

    env_status = get_environment_status()
    api_keys_status = check_all_api_keys()
    configured_any = env_status.get('has_any_api_key', False)

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
        f'{_ICONS["plug"]} 快速连接</div>',
        unsafe_allow_html=True
    )

    col_llm, col_neo4j = st.columns(2)

    # -- LLM 快速连接 --
    with col_llm:
        _render_llm_quick_connect(api_keys_status, configured_any, get_preset_configs, get_api_key_from_env, test_llm_connection, LLMConfig)

    # -- Neo4j 快速连接 --
    with col_neo4j:
        _render_neo4j_quick_connect(DEFAULT_CONFIG, Neo4jManager)

    # ---- 环境状态 ----
    st.markdown(
        '<div style="font-weight: 600; color: var(--text-primary); font-size: 0.95rem; margin: 1rem 0 0.75rem;">'
        f'{_ICONS["api"]} API Key 检测</div>',
        unsafe_allow_html=True
    )

    api_key_html = ""
    for provider, status in api_keys_status.items():
        icon = _ICONS["check"] if status.configured else _ICONS["api"]
        key_info = f" ({status.key_prefix})" if status.key_prefix else ""
        if status.configured:
            bg = "var(--color-success-bg)"
            border = "var(--color-success)"
            icon_color = "var(--color-success)"
        else:
            bg = "var(--bg-secondary)"
            border = "var(--border-light)"
            icon_color = "var(--text-tertiary)"

        api_key_html += (
            f'<div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.75rem; '
            f'background: {bg}; border: 1px solid {border}; border-radius: var(--radius-md); margin-bottom: 0.35rem;">'
            f'<span style="color: {icon_color};">{icon}</span>'
            f'<span style="font-weight: 500; font-size: 0.82rem; color: var(--text-primary);">{provider.upper()}</span>'
            f'<span style="font-size: 0.75rem; color: var(--text-tertiary);">{key_info}</span>'
            f'</div>'
        )
    st.markdown(api_key_html, unsafe_allow_html=True)

    # ---- 建议 ----
    if env_status.get('recommendations'):
        for rec in env_status['recommendations']:
            if rec['type'] == 'warning':
                st.warning(f"{rec['message']} — {rec['action']}")
            else:
                st.info(f"{rec['message']} — {rec['action']}")

    # ---- 开始按钮 ----
    st.markdown('<hr style="border: none; border-top: 1px solid var(--border-light); margin: 1.25rem 0;">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("开始构建知识图谱", type="primary", use_container_width=True):
            return "start"

    return None


def _render_llm_quick_connect(api_keys_status, configured_any, get_preset_configs_fn, get_api_key_fn, test_llm_fn, LLMConfigCls):
    """渲染 LLM 快速连接面板 - 简化版：选择厂商 + API 端点 + API Key + 模型名称"""
    st.markdown(
        f'<div class="quick-connect-header">{_ICONS["zap"]} LLM 模型</div>',
        unsafe_allow_html=True
    )

    presets = get_preset_configs_fn()
    preset_keys = list(presets.keys())

    # 提取唯一的厂商
    unique_providers = {}
    for k in preset_keys:
        provider = presets[k].get('provider', 'custom')
        if provider not in unique_providers:
            unique_providers[provider] = k

    provider_options = list(unique_providers.keys())

    # 自动选中已检测到 API Key 的厂商
    default_idx = 0
    for i, provider in enumerate(provider_options):
        if get_api_key_fn(provider):
            default_idx = i
            break

    selected_provider = st.selectbox(
        "选择厂商",
        options=provider_options,
        format_func=lambda x: PROVIDER_NAMES.get(x, x.upper()),
        index=default_idx,
        key="quick_llm_provider",
        label_visibility="collapsed"
    )

    # 获取该厂商的默认预设
    preset_key = unique_providers.get(selected_provider, "custom")
    preset = presets.get(preset_key, presets["custom"])

    # API 端点（可编辑）
    api_endpoint = st.text_input(
        "API 端点",
        value=preset.get('api_endpoint', ''),
        placeholder="https://api.example.com/v1/",
        key="quick_llm_endpoint",
        label_visibility="collapsed",
        help="选择厂商后自动填充，可手动修改"
    )

    # API Key 输入
    env_key = get_api_key_fn(selected_provider)
    if env_key:
        st.markdown(
            '<div style="background: var(--color-success-bg); border: 1px solid var(--color-success); '
            'border-radius: var(--radius-sm); padding: 6px 10px; font-size: 0.8rem; color: var(--text-success);">'
            f'已从环境变量加载 API Key ({env_key[:8]}...)'
            '</div>',
            unsafe_allow_html=True
        )
        api_key = env_key
    else:
        api_key = st.text_input(
            "API Key",
            type="password",
            placeholder="输入 API Key",
            key="quick_llm_apikey",
            label_visibility="collapsed"
        )

    # 模型名称输入
    model_name = st.text_input(
        "模型名称",
        value=preset.get('model_name', ''),
        placeholder="例如：glm-4, gpt-4, claude-3",
        key="quick_llm_model_name",
        label_visibility="collapsed"
    )

    # 测试按钮
    if api_key and model_name:
        if st.button("测试连接", key="quick_test_llm", use_container_width=True):
            with st.spinner("正在测试..."):
                try:
                    config = LLMConfigCls(
                        api_endpoint=api_endpoint,
                        api_key=api_key,
                        model_name=model_name,
                        provider=selected_provider
                    )
                    success, message = test_llm_fn(config)
                    if success:
                        st.success("连接成功 ✓")
                    else:
                        st.error(f"连接失败：{message[:80]}")
                except Exception as e:
                    st.error(f"配置错误：{str(e)[:80]}")

    # 保存到 session_state 供后续步骤使用
    if api_key and model_name and api_endpoint:
        try:
            config = LLMConfigCls(
                api_endpoint=api_endpoint,
                api_key=api_key,
                model_name=model_name,
                provider=selected_provider
            )
            st.session_state['quick_llm_config'] = config.to_dict()
        except ValueError:
            pass


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
        key="quick_neo4j_pwd",
        label_visibility="collapsed"
    )

    with st.expander("高级设置"):
        neo4j_uri = st.text_input(
            "URI",
            value=DEFAULT_CONFIG['neo4j_uri'],
            key="quick_neo4j_uri"
        )
        neo4j_user = st.text_input(
            "用户名",
            value=DEFAULT_CONFIG['neo4j_user'],
            key="quick_neo4j_user"
        )

    if not neo4j_uri:
        neo4j_uri = DEFAULT_CONFIG['neo4j_uri']
    if not neo4j_user:
        neo4j_user = DEFAULT_CONFIG['neo4j_user']

    if neo4j_password:
        if st.button("测试 Neo4j 连接", key="quick_test_neo4j", use_container_width=True):
            with st.spinner("正在测试..."):
                manager = Neo4jManager(neo4j_uri, neo4j_user, neo4j_password)
                success, message = manager.test_connection()
                if success:
                    st.success("连接成功 ✓")
                else:
                    st.error(f"连接失败：{message[:80]}")
                manager.close()

        # 保存到 session_state
        st.session_state['quick_neo4j_config'] = {
            "uri": neo4j_uri,
            "user": neo4j_user,
            "password": neo4j_password
        }
    else:
        st.caption("输入密码后可测试连接")


def render_help_section():
    """渲染帮助说明"""
    with st.expander("使用帮助", expanded=False):
        st.markdown("""
        **步骤 1: Schema 配置** — 选择预设模板或上传自定义 YAML 文件

        **步骤 2: 文档导入** — 上传单个文件（PDF/DOCX/XLSX/TXT）或导入文件夹批量处理

        **步骤 3: 配置连接** — 选择 LLM 厂商，输入 API 端点、API Key 和模型名称

        **步骤 4: 抽取处理** — 系统逐块处理文本，使用 LLM 抽取三元组

        **步骤 5: 审核入库** — 自动审核模式直接存入数据库，人工审核模式需逐个确认

        **步骤 6: 完成** — 在 Neo4j Browser 中查看知识图谱
        """)


def render_docker_help():
    """渲染 Docker 部署帮助"""
    with st.expander("Docker 部署", expanded=False):
        st.markdown("""
        ```bash
        # 克隆项目
        git clone https://github.com/happy-momo/EASY-Knowledge-Graph-Builder.git
        cd EASY-Knowledge-Graph-Builder

        # 启动 Docker
        docker-compose up -d

        # 访问应用
        # KG Builder: http://localhost:8501
        # Neo4j Browser: http://localhost:7474
        ```
        """)
