"""
配置页面组件（简化版）

LLM 配置简化为：厂商选择、API 端点、API Key、模型名称
"""

import streamlit as st
from typing import Dict, Tuple, List

from utils.llm_config import (
    LLMConfig, get_preset_configs, get_api_key_from_env,
    test_llm_connection, get_required_package, PROVIDER_DEFAULTS
)
from utils.neo4j_manager import Neo4jManager
from config.app_config import DEFAULT_CONFIG, HELP_TEXTS


# 厂商显示名称映射
PROVIDER_DISPLAY_NAMES = {
    "zhipu": "智谱 AI",
    "openai": "OpenAI",
    "anthropic": "Anthropic (Claude)",
    "google": "Google (Gemini)",
    "alibaba": "阿里云 (通义千问)",
    "deepseek": "深度求索 (DeepSeek)",
    "moonshot": "月之暗面 (Kimi)",
    "custom": "自定义",
}

# 厂商模型示例
PROVIDER_MODEL_EXAMPLES = {
    "zhipu": "glm-4, glm-4-flash",
    "openai": "gpt-4, gpt-4o, gpt-3.5-turbo",
    "anthropic": "claude-3-opus-20240229, claude-3-sonnet-20240229",
    "google": "gemini-pro, gemini-1.5-pro",
    "alibaba": "qwen-turbo, qwen-plus",
    "deepseek": "deepseek-chat, deepseek-coder",
    "moonshot": "moonshot-v1-8k, moonshot-v1-32k",
    "custom": "任意模型名称",
}


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
    """渲染简化版 LLM 配置界面"""
    st.markdown('<h4 style="color: var(--text-primary); margin-bottom: 0.5rem;">LLM 模型配置</h4>', unsafe_allow_html=True)

    # 厂商选择
    provider_options = list(PROVIDER_DISPLAY_NAMES.keys())
    provider_display_options = [PROVIDER_DISPLAY_NAMES[p] for p in provider_options]

    selected_display = st.selectbox(
        "选择模型厂商",
        options=provider_display_options,
        index=0,
        help="选择 LLM 模型提供商"
    )
    provider = provider_options[provider_display_options.index(selected_display)]

    # 获取厂商默认配置
    provider_defaults = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["custom"])
    default_endpoint = provider_defaults.get("api_endpoint", "")

    # 获取所需包名
    required_package = get_required_package(provider)

    # 显示厂商信息卡片
    st.markdown(f"""
    <div class="info-card" style="margin: 0.75rem 0; border-left-color: var(--color-primary-600);">
        <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.25rem;">
            {PROVIDER_DISPLAY_NAMES.get(provider, provider)}
        </div>
        <div style="font-size: 0.85rem; color: var(--text-secondary);">
            所需包：<code style="background: #F3F4F6; padding: 2px 4px; border-radius: 3px;">{required_package}</code>
        </div>
        <div style="font-size: 0.8rem; color: var(--text-tertiary); margin-top: 0.25rem;">
            示例模型：{PROVIDER_MODEL_EXAMPLES.get(provider, "")}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # API 端点（带默认值）
    api_endpoint = st.text_input(
        "API 端点",
        value=default_endpoint if default_endpoint else "",
        placeholder="https://api.example.com/v1/",
        help=provider_defaults.get("api_endpoint", "输入 API 端点地址")
    )

    # API Key
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

    api_key = st.text_input(
        "API Key",
        type="password",
        placeholder=f"输入{PROVIDER_DISPLAY_NAMES.get(provider, provider)} API Key",
        value=env_key if env_key else "",
        help="支持从环境变量自动读取"
    )

    # 模型名称
    model_name = st.text_input(
        "模型名称",
        placeholder=PROVIDER_MODEL_EXAMPLES.get(provider, "输入模型名称"),
        help="输入要使用的模型名称"
    )

    # 测试连接按钮
    if api_endpoint and api_key and model_name:
        if st.button("测试连接", key="test_llm", type="secondary"):
            with st.spinner("测试中..."):
                config = LLMConfig(
                    api_endpoint=api_endpoint,
                    api_key=api_key,
                    model_name=model_name,
                    provider=provider
                )
                success, message = test_llm_connection(config)
                if success:
                    st.success(message)
                else:
                    st.error(message)

    # 返回配置
    if api_endpoint and api_key and model_name:
        try:
            llm_config = LLMConfig(
                api_endpoint=api_endpoint,
                api_key=api_key,
                model_name=model_name,
                provider=provider
            )
            return llm_config.to_dict()
        except ValueError as e:
            st.error(str(e))

    return {}


def render_neo4j_config() -> Dict:
    """渲染 Neo4j 配置"""
    st.markdown('<h4 style="color: var(--text-primary); margin-bottom: 0.5rem;">Neo4j 数据库配置</h4>', unsafe_allow_html=True)

    st.info("默认配置：URI `bolt://localhost:7687`，用户名 `neo4j`。大多数情况下只需设置密码。")

    neo4j_uri = st.text_input(
        "URI",
        value=DEFAULT_CONFIG['neo4j_uri'],
        help=HELP_TEXTS.get("neo4j_uri", "")
    )

    neo4j_user = st.text_input(
        "用户名",
        value=DEFAULT_CONFIG['neo4j_user']
    )

    neo4j_password = st.text_input(
        "密码",
        type="password",
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


def render_review_mode_config() -> str:
    """渲染审核模式配置"""
    st.markdown('<h4 style="color: var(--text-primary); margin-bottom: 0.5rem;">审核设置</h4>', unsafe_allow_html=True)

    review_mode = st.radio(
        "审核模式",
        options=["auto", "manual"],
        format_func=lambda x: {
            "auto": "自动审核（推荐）- 抽取后直接入库",
            "manual": "人工审核 - 逐个确认三元组"
        }[x],
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


def validate_config(config: Dict) -> Tuple[bool, List[str]]:
    """验证配置是否完整"""
    missing = []

    llm = config.get('llm', {})
    if not llm.get('api_endpoint'):
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
    api_key_display = (llm.get('api_key', '未设置')[:8] + '...') if llm.get('api_key') else '未设置'
    neo4j_uri = config.get('neo4j', {}).get('uri', '未设置')
    review_mode = config.get('review_mode', '未设置')

    summary_html = (
        '<div class="info-panel">'
        f'<div class="info-panel-row"><span class="info-panel-label">LLM Model</span><span class="info-panel-value">{model_name}</span></div>'
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
