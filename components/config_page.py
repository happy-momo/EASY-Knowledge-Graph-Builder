"""
配置页面组件
"""

import streamlit as st
import os
from typing import Dict, Tuple, List

from config.app_config import LLM_OPTIONS, DEFAULT_CONFIG, HELP_TEXTS
from utils.env_checker import check_api_key


def render_config_section() -> Dict:
    """
    渲染配置界面

    Returns:
        配置字典
    """
    st.markdown("### 配置设置")

    # LLM配置
    llm_config = render_llm_config()

    # Neo4j配置
    neo4j_config = render_neo4j_config()

    # 审核模式配置
    review_mode = render_review_mode_config()

    # 合并配置
    config = {
        "llm": llm_config,
        "neo4j": neo4j_config,
        "review_mode": review_mode
    }

    return config


def render_llm_config() -> Dict:
    """渲染LLM配置"""

    st.markdown("#### 🧠 LLM模型配置")

    # 模型选择
    model_options = [opt['name'] for opt in LLM_OPTIONS]
    default_index = 0  # GLM-4-Flash

    selected_name = st.selectbox(
        "选择模型",
        options=model_options,
        index=default_index,
        help=HELP_TEXTS.get("llm_model", "")
    )

    # 找到对应的模型配置
    selected_llm = None
    for opt in LLM_OPTIONS:
        if opt['name'] == selected_name:
            selected_llm = opt
            break

    # API Key输入
    st.markdown(f"**{selected_llm['api_key_label']}**")

    # 尝试从环境变量读取
    env_api_key = os.environ.get(selected_llm['api_env_key'], "")

    # 显示环境变量状态
    api_key_status = check_api_key(selected_llm['provider'])
    if api_key_status.configured:
        st.success(f"✅ 已从环境变量检测到API Key ({api_key_status.key_prefix})")

    # API Key输入框
    api_key = st.text_input(
        "API Key",
        value=env_api_key,
        type="password",
        placeholder="输入API Key",
        help=HELP_TEXTS.get("api_key", "")
    )

    # 如果没有输入，使用环境变量的值
    if not api_key and env_api_key:
        api_key = env_api_key

    st.markdown("---")

    return {
        "model_name": selected_llm['model_name'],
        "provider": selected_llm['provider'],
        "api_key": api_key,
        "api_key_label": selected_llm['api_key_label']
    }


def render_neo4j_config() -> Dict:
    """渲染Neo4j配置"""

    st.markdown("#### 🗄️ Neo4j数据库配置")

    # 默认值提示
    st.info("💡 默认配置：URI `bolt://localhost:7687`，用户名 `neo4j`。大多数情况下只需设置密码。")

    # 高级配置折叠
    show_advanced = st.checkbox("🔧 显示高级配置", value=False)

    # URI和用户名
    if show_advanced:
        col1, col2 = st.columns(2)
        with col1:
            neo4j_uri = st.text_input(
                "URI",
                value=DEFAULT_CONFIG['neo4j_uri'],
                help=HELP_TEXTS.get("neo4j_uri", "")
            )
        with col2:
            neo4j_user = st.text_input(
                "用户名",
                value=DEFAULT_CONFIG['neo4j_user']
            )
    else:
        neo4j_uri = DEFAULT_CONFIG['neo4j_uri']
        neo4j_user = DEFAULT_CONFIG['neo4j_user']

    # 密码（始终显示）
    neo4j_password = st.text_input(
        "密码",
        type="password",
        placeholder="输入Neo4j密码",
        help=HELP_TEXTS.get("neo4j_password", "")
    )

    # 连接测试
    if neo4j_password:
        if st.button("测试连接", key="test_neo4j"):
            from utils.env_checker import check_neo4j_connection
            status = check_neo4j_connection(neo4j_uri, neo4j_user, neo4j_password)

            if status.status.value == "connected":
                st.success(f"✅ 连接成功 (Neo4j {status.version})")
            else:
                st.error(f"❌ {status.message}")

    st.markdown("---")

    return {
        "uri": neo4j_uri,
        "user": neo4j_user,
        "password": neo4j_password
    }


def render_review_mode_config() -> str:
    """渲染审核模式配置"""

    st.markdown("#### ✅ 审核设置")

    # 审核模式选择
    review_mode = st.radio(
        "审核模式",
        options=["auto", "manual"],
        format_func=lambda x: {
            "auto": "✅ 自动审核（推荐）- 抽取后直接入库",
            "manual": "👤 人工审核 - 逐个确认三元组"
        }[x],
        help=HELP_TEXTS.get("review_mode", "")
    )

    if review_mode == "manual":
        st.info("""
        💡 **人工审核模式**：
        - 抽取完成后展示所有三元组
        - 您可以逐个确认、编辑或删除
        - 只有确认后的三元组才会存入数据库
        """)

    st.markdown("---")

    return review_mode


def validate_config(config: Dict) -> Tuple[bool, List[str]]:
    """
    验证配置是否完整

    Args:
        config: 配置字典

    Returns:
        (是否有效, 缺失项列表)
    """
    missing = []

    # 检查API Key
    if not config.get('llm', {}).get('api_key'):
        missing.append("LLM API Key")

    # 检查Neo4j密码
    if not config.get('neo4j', {}).get('password'):
        missing.append("Neo4j密码")

    return len(missing) == 0, missing


def render_config_summary(config: Dict):
    """渲染配置摘要"""

    st.markdown("### 配置摘要")

    summary_html = f"""
    <div class="terminal-container">
        <div class="terminal-header">
            <div class="terminal-dot close"></div>
            <div class="terminal-dot minimize"></div>
            <div class="terminal-dot maximize"></div>
            <div class="terminal-title">Configuration</div>
        </div>
        <div class="terminal">
            <span class="info">LLM Model:</span> <span class="result">{config['llm']['model_name']}</span><br>
            <span class="info">API Key:</span> <span class="result">{config['llm']['api_key'][:8] + '...' if config['llm']['api_key'] else '未设置'}</span><br>
            <span class="info">Neo4j URI:</span> <span class="result">{config['neo4j']['uri']}</span><br>
            <span class="info">Review Mode:</span> <span class="result">{config['review_mode']}</span><br>
        </div>
    </div>
    """

    st.markdown(summary_html, unsafe_allow_html=True)


def save_config_to_state(config: Dict):
    """保存配置到session_state"""
    st.session_state['llm_model'] = config['llm']['model_name']
    st.session_state['llm_api_key'] = config['llm']['api_key']
    st.session_state['neo4j_uri'] = config['neo4j']['uri']
    st.session_state['neo4j_user'] = config['neo4j']['user']
    st.session_state['neo4j_password'] = config['neo4j']['password']
    st.session_state['review_mode'] = config['review_mode']


def load_config_from_state() -> Dict:
    """从session_state加载配置"""
    return {
        "llm": {
            "model_name": st.session_state.get('llm_model', ''),
            "api_key": st.session_state.get('llm_api_key', '')
        },
        "neo4j": {
            "uri": st.session_state.get('neo4j_uri', DEFAULT_CONFIG['neo4j_uri']),
            "user": st.session_state.get('neo4j_user', DEFAULT_CONFIG['neo4j_user']),
            "password": st.session_state.get('neo4j_password', '')
        },
        "review_mode": st.session_state.get('review_mode', 'auto')
    }