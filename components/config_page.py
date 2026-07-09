"""
配置页面组件 - 简化版

用户只需配置：厂商、API 端点、API Key、模型名称
"""

import streamlit as st
from typing import Dict, Tuple, List

from utils.llm_config import (
    LLMConfig, get_preset_configs, get_required_package,
    get_api_key_from_env, test_llm_connection
)
from utils.neo4j_manager import Neo4jManager
from config.app_config import DEFAULT_CONFIG, HELP_TEXTS


def render_config_section() -> Dict:
    """渲染配置界面"""
    st.markdown('<h3 style="color: var(--text-primary); margin-bottom: 1rem;">配置设置</h3>', unsafe_allow_html=True)

    llm_config = render_llm_config()
    neo4j_config = render_neo4j_config()
    review_mode = render_review_mode_config()

    return {
        "llm": llm_config,
        "neo4j": neo4j_config,
        "review_mode": review_mode
    }


def render_llm_config() -> Dict:
    """渲染 LLM 配置 - 简化版：厂商 + 端点 + Key + 模型"""
    st.markdown('<h4 style="color: var(--text-primary); margin-bottom: 0.5rem;">LLM 模型配置</h4>', unsafe_allow_html=True)

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
        key="llm_provider"
    )

    # 获取厂商默认值
    from utils.llm_config import PROVIDER_DEFAULTS
    defaults = PROVIDER_DEFAULTS.get(selected_provider, PROVIDER_DEFAULTS["custom"])

    # API 端点
    default_endpoint = defaults.get("api_endpoint", "")
    api_endpoint = st.text_input(
        "API 端点",
        value=default_endpoint if selected_provider != "custom" else "",
        placeholder="https://api.example.com/v1/",
        key="llm_endpoint"
    )

    # API Key
    env_key = get_api_key_from_env(selected_provider)
    if env_key:
        st.markdown(
            '<div style="background-color: #D1FAE5; border: 1px solid #6EE7B7; '
            'border-radius: 6px; padding: 8px 12px; margin: 8px 0; '
            'color: #065F46; font-size: 0.85rem;">'
            f'✓ 已从环境变量检测到 API Key ({env_key[:8]}...)'
            '</div>',
            unsafe_allow_html=True
        )
        api_key = st.text_input(
            "API Key",
            value=env_key,
            type="password",
            key="llm_apikey"
        )
    else:
        api_key = st.text_input(
            "API Key",
            type="password",
            placeholder="输入 API Key",
            key="llm_apikey"
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
        placeholder="如：gpt-4o, glm-4, claude-3-opus...",
        key="llm_model"
    )

    # 显示所需包
    required_package = get_required_package(selected_provider)
    st.caption(f"所需包：`{required_package}`")

    # 测试连接
    if api_endpoint and api_key and model_name:
        if st.button("测试连接", key="test_llm", use_container_width=True):
            with st.spinner("测试中..."):
                config = LLMConfig(
                    api_endpoint=api_endpoint,
                    api_key=api_key,
                    model_name=model_name,
                    provider=selected_provider
                )
                success, message = test_llm_connection(config)
                if success:
                    st.success(message)
                else:
                    st.error(message)

    # 返回配置
    if api_endpoint and api_key and model_name:
        return LLMConfig(
            api_endpoint=api_endpoint,
            api_key=api_key,
            model_name=model_name,
            provider=selected_provider
        ).to_dict()

    return {}


def render_neo4j_config() -> Dict:
    """渲染 Neo4j 配置"""
    st.markdown('<h4 style="color: var(--text-primary); margin-bottom: 0.5rem;">Neo4j 数据库配置</h4>', unsafe_allow_html=True)

    st.info("默认：URI `bolt://localhost:7687`，用户名 `neo4j`，只需设置密码。")

    neo4j_uri = st.text_input("URI", value=DEFAULT_CONFIG['neo4j_uri'], key="neo4j_uri")
    neo4j_user = st.text_input("用户名", value=DEFAULT_CONFIG['neo4j_user'], key="neo4j_user")
    neo4j_password = st.text_input("密码", type="password", placeholder="输入密码", key="neo4j_password")

    if neo4j_password:
        if st.button("测试连接", key="test_neo4j", use_container_width=True):
            with st.spinner("测试中..."):
                manager = Neo4jManager(neo4j_uri, neo4j_user, neo4j_password)
                success, message = manager.test_connection()
                if success:
                    st.success(message)
                else:
                    st.error(message)
                manager.close()

    return {
        "uri": neo4j_uri,
        "user": neo4j_user,
        "password": neo4j_password
    }


def render_review_mode_config() -> str:
    """渲染审核模式配置"""
    st.markdown('<h4 style="color: var(--text-primary); margin-bottom: 0.5rem;">审核模式</h4>', unsafe_allow_html=True)

    review_mode = st.radio(
        "审核模式",
        options=["auto", "manual"],
        format_func=lambda x: {
            "auto": "自动审核 - 抽取后直接入库",
            "manual": "人工审核 - 逐个确认三元组"
        }[x],
        horizontal=True,
        key="review_mode"
    )

    return review_mode


def validate_config(config: Dict) -> Tuple[bool, List[str]]:
    """验证配置"""
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
