"""
配置页面组件（重构版）

使用标准化LLM配置，支持任意厂商模型。
"""

import streamlit as st
import os
from typing import Dict, Tuple, List

from utils.llm_config import (
    LLMConfig, get_preset_configs, create_llm_config_from_preset,
    validate_llm_config, get_api_key_from_env, test_llm_connection
)
from utils.neo4j_manager import Neo4jManager
from config.app_config import DEFAULT_CONFIG, HELP_TEXTS


def render_config_section() -> Dict:
    """
    渲染配置界面

    Returns:
        配置字典
    """
    st.markdown("### 配置设置")

    # LLM配置
    llm_config = render_llm_config_v2()

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


def render_llm_config_v2() -> Dict:
    """渲染标准化LLM配置"""

    st.markdown("#### 🧠 LLM模型配置")

    # 选择配置方式
    config_mode = st.radio(
        "配置方式",
        options=["preset", "custom"],
        format_func=lambda x: {
            "preset": "📋 选择预设配置",
            "custom": "⚙️ 自定义配置"
        }[x],
        horizontal=True,
        key="llm_config_mode"
    )

    if config_mode == "preset":
        return render_preset_config()
    else:
        return render_custom_config()


def render_preset_config() -> Dict:
    """渲染预设配置选择"""

    presets = get_preset_configs()

    # 显示预设卡片
    preset_keys = list(presets.keys())
    preset_names = [presets[k]['name'] for k in preset_keys]

    selected_name = st.selectbox(
        "选择模型",
        options=preset_names,
        index=0,
        help="选择预设的LLM模型配置"
    )

    # 获取选中的预设
    selected_key = preset_keys[preset_names.index(selected_name)]
    preset = presets[selected_key]

    # 显示预设详情
    st.markdown(f"""
    <div class="card" style="padding: var(--space-4);">
        <div style="color: var(--text-secondary); font-size: var(--text-sm);">
            {preset['description']}
        </div>
        <div style="color: var(--text-tertiary); font-size: var(--text-xs); margin-top: var(--space-2);">
            提供商: {preset['provider']} | 模型: {preset['model_name']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # API Key输入
    api_key = render_api_key_input(preset['provider'])

    # 创建配置
    try:
        llm_config = create_llm_config_from_preset(selected_key, api_key)
        return llm_config.to_dict()
    except ValueError as e:
        st.error(str(e))
        return {}


def render_custom_config() -> Dict:
    """渲染自定义配置"""

    st.markdown("**自定义API配置**")

    # API端点
    api_endpoint = st.text_input(
        "API端点",
        placeholder="https://api.example.com/v1/",
        help="输入兼容OpenAI API的端点地址"
    )

    # API Key
    api_key = st.text_input(
        "API Key",
        type="password",
        placeholder="输入API Key",
        help="输入API Key"
    )

    # 模型名称
    model_name = st.text_input(
        "模型名称",
        placeholder="gpt-4 或 glm-4",
        help="输入模型名称"
    )

    # 高级选项
    with st.expander("高级选项"):
        col1, col2 = st.columns(2)
        with col1:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.1,
                step=0.1,
                help="控制输出的随机性"
            )
        with col2:
            max_tokens = st.number_input(
                "最大Token数",
                min_value=256,
                max_value=4096,
                value=2048,
                step=256
            )

    # 测试连接
    if api_endpoint and api_key and model_name:
        if st.button("测试连接", key="test_llm"):
            with st.spinner("测试中..."):
                config = LLMConfig(
                    api_endpoint=api_endpoint,
                    api_key=api_key,
                    model_name=model_name
                )
                success, message = test_llm_connection(config)
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")

    # 创建配置
    if api_endpoint and api_key and model_name:
        try:
            llm_config = LLMConfig(
                api_endpoint=api_endpoint,
                api_key=api_key,
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return llm_config.to_dict()
        except ValueError as e:
            st.error(str(e))

    return {}


def render_api_key_input(provider: str) -> str:
    """渲染API Key输入"""

    # 尝试从环境变量获取
    env_key = get_api_key_from_env(provider)

    if env_key:
        st.success(f"✅ 已从环境变量检测到API Key ({env_key[:8]}...)")
        return env_key

    # 手动输入
    api_key = st.text_input(
        "API Key",
        type="password",
        placeholder=f"输入{provider.upper()} API Key",
        help="支持从环境变量自动读取"
    )

    return api_key


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
            with st.spinner("测试中..."):
                manager = Neo4jManager(neo4j_uri, neo4j_user, neo4j_password)
                success, message = manager.test_connection()
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
                manager.close()

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

    # 检查LLM配置
    llm = config.get('llm', {})
    if not llm.get('api_endpoint'):
        missing.append("API端点")
    if not llm.get('api_key'):
        missing.append("API Key")
    if not llm.get('model_name'):
        missing.append("模型名称")

    # 检查Neo4j密码
    if not config.get('neo4j', {}).get('password'):
        missing.append("Neo4j密码")

    return len(missing) == 0, missing


def render_config_summary(config: Dict):
    """渲染配置摘要"""

    st.markdown("### 配置摘要")

    llm = config.get('llm', {})

    summary_html = f"""
    <div class="terminal">
        <div class="terminal-header">
            <div class="terminal-dot close"></div>
            <div class="terminal-dot minimize"></div>
            <div class="terminal-dot maximize"></div>
            <div class="terminal-title">Configuration</div>
        </div>
        <div class="terminal-body">
            <span class="info">LLM Model:</span> <span class="result">{llm.get('model_name', '未设置')}</span><br>
            <span class="info">Provider:</span> <span class="result">{llm.get('provider', '未设置')}</span><br>
            <span class="info">API Key:</span> <span class="result">{llm.get('api_key', '未设置')[:8] + '...' if llm.get('api_key') else '未设置'}</span><br>
            <span class="info">Neo4j URI:</span> <span class="result">{config.get('neo4j', {}).get('uri', '未设置')}</span><br>
            <span class="info">Review Mode:</span> <span class="result">{config.get('review_mode', '未设置')}</span><br>
        </div>
    </div>
    """

    st.markdown(summary_html, unsafe_allow_html=True)


def save_config_to_state(config: Dict):
    """保存配置到session_state"""
    st.session_state['config'] = config


def load_config_from_state() -> Dict:
    """从session_state加载配置"""
    return st.session_state.get('config', {})