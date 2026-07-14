"""
配置页面组件（双路由版）

LLM 配置流程：厂家类型选择 → 具体厂商 → API 端点/Key/模型名称
"""

import streamlit as st
from typing import Dict, Tuple, List

from utils.llm_config import (
    LLMConfig, get_preset_configs, get_api_key_from_env,
    test_llm_connection, get_required_package, get_vendor_info,
    get_default_base_url, get_vendor_type_label,
    OPENAI_COMPATIBLE_VENDORS, NATIVE_LANGCHAIN_VENDORS,
    get_all_vendor_options
)
from utils.neo4j_manager import Neo4jManager
from config.app_config import DEFAULT_CONFIG, HELP_TEXTS


# ==================== LLM 配置 UI ====================

def render_config_section() -> Dict:
    """渲染配置界面"""
    st.markdown('<h3 style="color: var(--text-primary); margin-bottom: 1rem;">配置设置</h3>', unsafe_allow_html=True)

    llm_config = render_llm_config_simple()
    neo4j_config = render_neo4j_config()
    review_mode = render_review_mode_config()

    config = {
        "llm": llm_config,
        "neo4j": neo4j_config,
        "review_mode": review_mode
    }

    return config


def render_llm_config_simple() -> Dict:
    """渲染双路由 LLM 配置界面"""
    st.markdown('<h4 style="color: var(--text-primary); margin-bottom: 0.5rem;">LLM 模型配置</h4>', unsafe_allow_html=True)

    # ---- 从缓存中恢复配置 ----
    cached_llm = {}
    if st.session_state.get('config') and st.session_state.config.get('llm'):
        cached_llm = st.session_state.config['llm']

    # ---- Step 1: 选择厂家类型 ----
    vendor_type_options = {
        "openai_compatible": "🔌 OpenAI 兼容接口（智谱/阿里/DeepSeek/Kimi/自定义）",
        "native_langchain": "🧩 原生 LangChain（OpenAI/Anthropic/Gemini）",
    }

    # 从缓存恢复或默认
    if 'llm_vendor_type' not in st.session_state:
        st.session_state.llm_vendor_type = cached_llm.get('vendor_type', 'openai_compatible')

    selected_vendor_type_display = st.radio(
        "厂家类型",
        options=list(vendor_type_options.keys()),
        format_func=lambda x: vendor_type_options[x],
        index=list(vendor_type_options.keys()).index(st.session_state.llm_vendor_type),
        horizontal=True,
        help="选择接口类型决定模型初始化方式"
    )
    vendor_type = selected_vendor_type_display
    st.session_state.llm_vendor_type = vendor_type

    # ---- Step 2: 选择具体厂商 ----
    if vendor_type == "openai_compatible":
        vendor_registry = OPENAI_COMPATIBLE_VENDORS
    else:
        vendor_registry = NATIVE_LANGCHAIN_VENDORS

    provider_options = list(vendor_registry.keys())
    provider_display_options = [vendor_registry[p]["display_name"] for p in provider_options]

    # 从缓存恢复厂商选择
    provider_key = f"llm_provider_{vendor_type}"
    if provider_key not in st.session_state:
        cached_provider = cached_llm.get('provider', provider_options[0])
        st.session_state[provider_key] = cached_provider if cached_provider in provider_options else provider_options[0]

    # 确保保存的 provider 在当前类型下有效
    saved_provider = st.session_state[provider_key]
    if saved_provider not in provider_options:
        saved_provider = provider_options[0]
        st.session_state[provider_key] = saved_provider

    default_provider_idx = provider_options.index(saved_provider)

    selected_provider_display = st.selectbox(
        "选择厂商",
        options=provider_display_options,
        index=default_provider_idx,
        help="选择具体的 LLM 厂商"
    )
    provider = provider_options[provider_display_options.index(selected_provider_display)]
    st.session_state[provider_key] = provider

    # ---- 获取厂商信息 ----
    vendor_info = vendor_registry[provider]
    default_endpoint = vendor_info.get("base_url", "")
    model_examples = vendor_info.get("model_examples", "")
    required_package = get_required_package(vendor_type, provider)

    # 显示厂商信息卡片
    route_label = get_vendor_type_label(vendor_type)
    st.markdown(f"""
    <div class="info-card" style="margin: 0.75rem 0; border-left-color: var(--color-primary-600);">
        <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.25rem;">
            {vendor_info['display_name']}
        </div>
        <div style="font-size: 0.85rem; color: var(--text-secondary);">
            接口类型：<code style="background: #F3F4F6; padding: 2px 4px; border-radius: 3px;">{route_label}</code>
            &nbsp;|&nbsp; 所需包：<code style="background: #F3F4F6; padding: 2px 4px; border-radius: 3px;">{required_package}</code>
        </div>
        <div style="font-size: 0.8rem; color: var(--text-tertiary); margin-top: 0.25rem;">
            示例模型：{model_examples}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---- Step 3: API 端点 ----
    endpoint_label = "Base URL" if vendor_type == "openai_compatible" else "API 端点"
    endpoint_help = "OpenAI 兼容接口的 Base URL" if vendor_type == "openai_compatible" else "API 端点地址（Google Gemini 可留空）"

    # Google 不需要端点
    is_google = (vendor_type == "native_langchain" and provider == "google")

    # 从缓存恢复端点值
    cached_endpoint = cached_llm.get('api_endpoint', '')
    endpoint_default = cached_endpoint if cached_endpoint else (default_endpoint if default_endpoint else "")

    api_endpoint = st.text_input(
        endpoint_label,
        value=endpoint_default,
        placeholder="https://api.example.com/v1/" if not is_google else "无需填写",
        help=endpoint_help
    )

    # ---- Step 4: API Key ----
    env_key = get_api_key_from_env(provider)
    if env_key:
        st.markdown(
            '<div style="background-color: #D1FAE5; border: 1px solid #6EE7B7; '
            'border-radius: 8px; padding: 10px 16px; margin: 8px 0; '
            'color: #065F46; font-size: 0.9rem;">'
            f'✓ 已从环境变量检测到 API Key ({env_key[:8]}...)'
            '</div>',
            unsafe_allow_html=True
        )

    # 从缓存恢复 API Key
    cached_api_key = cached_llm.get('api_key', '')
    api_key_default = env_key if env_key else cached_api_key

    api_key = st.text_input(
        "API Key",
        type="password",
        placeholder=f"输入{vendor_info['display_name']} API Key",
        value=api_key_default,
        help="支持从环境变量自动读取"
    )

    # ---- Step 5: 模型名称 ----
    # 从缓存恢复模型名称
    cached_model_name = cached_llm.get('model_name', '')

    model_name = st.text_input(
        "模型名称",
        value=cached_model_name,
        placeholder=model_examples,
        help="输入要使用的模型名称"
    )

    # ---- Step 6: 测试连接 ----
    can_test = bool(api_key and model_name and (api_endpoint or is_google))
    if can_test:
        if st.button("测试连接", key="test_llm", type="secondary"):
            with st.spinner("测试中..."):
                config = LLMConfig(
                    api_endpoint=api_endpoint if api_endpoint else "",
                    api_key=api_key,
                    model_name=model_name,
                    vendor_type=vendor_type,
                    provider=provider
                )
                success, message = test_llm_connection(config)
                if success:
                    st.success(message)
                else:
                    st.error(message)

    # ---- 返回配置 ----
    if api_key and model_name and (api_endpoint or is_google):
        try:
            llm_config = LLMConfig(
                api_endpoint=api_endpoint if api_endpoint else "",
                api_key=api_key,
                model_name=model_name,
                vendor_type=vendor_type,
                provider=provider
            )
            return llm_config.to_dict()
        except ValueError as e:
            st.error(str(e))

    return {}


# ==================== Neo4j 配置 UI ====================

def render_neo4j_config() -> Dict:
    """渲染 Neo4j 配置"""
    st.markdown('<h4 style="color: var(--text-primary); margin-bottom: 0.5rem;">Neo4j 数据库配置</h4>', unsafe_allow_html=True)

    # 从缓存恢复 Neo4j 配置
    cached_neo4j = {}
    if st.session_state.get('config') and st.session_state.config.get('neo4j'):
        cached_neo4j = st.session_state.config['neo4j']

    cached_uri = cached_neo4j.get('uri', '')
    cached_user = cached_neo4j.get('user', '')
    cached_password = cached_neo4j.get('password', '')

    # 如果有缓存，提示用户
    if cached_password:
        st.success("✓ 已从上次配置中恢复 Neo4j 连接信息")

    st.info("默认配置：URI `bolt://localhost:7687`，用户名 `neo4j`。大多数情况下只需设置密码。")

    neo4j_uri = st.text_input(
        "URI",
        value=cached_uri if cached_uri else DEFAULT_CONFIG['neo4j_uri'],
        help=HELP_TEXTS.get("neo4j_uri", "")
    )

    neo4j_user = st.text_input(
        "用户名",
        value=cached_user if cached_user else DEFAULT_CONFIG['neo4j_user']
    )

    neo4j_password = st.text_input(
        "密码",
        type="password",
        value=cached_password,
        placeholder="输入 Neo4j 密码",
        help=HELP_TEXTS.get("neo4j_password", "")
    )

    if neo4j_password:
        if st.button("测试连接", key="test_neo4j"):
            with st.spinner("测试中..."):
                manager = Neo4jManager(neo4j_uri, neo4j_user, neo4j_password)
                success, message = manager.test_connection()
                if success:
                    st.success(message)
                else:
                    st.error(message)
                manager.close()

    st.markdown('<hr style="border: none; border-top: 1px solid #E2E8F0; margin: 1rem 0;">', unsafe_allow_html=True)

    return {
        "uri": neo4j_uri,
        "user": neo4j_user,
        "password": neo4j_password
    }


# ==================== 审核模式配置 ====================

def render_review_mode_config() -> str:
    """渲染审核模式配置"""
    st.markdown('<h4 style="color: var(--text-primary); margin-bottom: 0.5rem;">审核设置</h4>', unsafe_allow_html=True)

    # 从缓存恢复审核模式
    cached_review_mode = "auto"
    if st.session_state.get('config') and st.session_state.config.get('review_mode'):
        cached_review_mode = st.session_state.config['review_mode']

    review_mode = st.radio(
        "审核模式",
        options=["auto", "manual"],
        format_func=lambda x: {
            "auto": "自动审核（推荐）- 抽取后直接入库",
            "manual": "人工审核 - 逐个确认三元组"
        }[x],
        index=0 if cached_review_mode == "auto" else 1,
        help=HELP_TEXTS.get("review_mode", "")
    )

    if review_mode == "manual":
        st.info("""
        **人工审核模式**：
        - 抽取完成后展示所有三元组
        - 您可以逐个确认、编辑或删除
        - 只有确认后的三元组才会存入数据库
        """)

    st.markdown('<hr style="border: none; border-top: 1px solid #E2E8F0; margin: 1rem 0;">', unsafe_allow_html=True)

    return review_mode


# ==================== 验证与摘要 ====================

def validate_config(config: Dict) -> Tuple[bool, List[str]]:
    """验证配置是否完整"""
    missing = []

    llm = config.get('llm', {})
    vendor_type = llm.get('vendor_type', 'openai_compatible')
    provider = llm.get('provider', 'custom')
    is_google = (vendor_type == "native_langchain" and provider == "google")

    if not is_google and not llm.get('api_endpoint'):
        missing.append("API 端点")
    if not llm.get('api_key'):
        missing.append("API Key")
    if not llm.get('model_name'):
        missing.append("模型名称")

    if not config.get('neo4j', {}).get('password'):
        missing.append("Neo4j 密码")

    return len(missing) == 0, missing


def render_config_summary(config: Dict):
    """渲染配置摘要"""
    st.markdown('<h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">配置摘要</h3>', unsafe_allow_html=True)

    llm = config.get('llm', {})
    model_name = llm.get('model_name', '未设置')
    provider = llm.get('provider', '未设置')
    vendor_type = llm.get('vendor_type', '未设置')
    api_key_display = (llm.get('api_key', '未设置')[:8] + '...') if llm.get('api_key') else '未设置'
    neo4j_uri = config.get('neo4j', {}).get('uri', '未设置')
    review_mode = config.get('review_mode', '未设置')

    route_label = get_vendor_type_label(vendor_type) if vendor_type != '未设置' else '未设置'

    summary_html = (
        '<div class="info-panel">'
        f'<div class="info-panel-row"><span class="info-panel-label">LLM Model</span><span class="info-panel-value">{model_name}</span></div>'
        f'<div class="info-panel-row"><span class="info-panel-label">接口类型</span><span class="info-panel-value">{route_label}</span></div>'
        f'<div class="info-panel-row"><span class="info-panel-label">Provider</span><span class="info-panel-value">{provider}</span></div>'
        f'<div class="info-panel-row"><span class="info-panel-label">API Key</span><span class="info-panel-value">{api_key_display}</span></div>'
        f'<div class="info-panel-row"><span class="info-panel-label">Neo4j URI</span><span class="info-panel-value">{neo4j_uri}</span></div>'
        f'<div class="info-panel-row"><span class="info-panel-label">Review Mode</span><span class="info-panel-value">{review_mode}</span></div>'
        '</div>'
    )

    st.markdown(summary_html, unsafe_allow_html=True)


def save_config_to_state(config: Dict):
    """保存配置到 session_state"""
    st.session_state['config'] = config


def load_config_from_state() -> Dict:
    """从 session_state 加载配置"""
    return st.session_state.get('config', {})
