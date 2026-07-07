"""
欢迎引导页组件
"""

import streamlit as st
from typing import Dict, List, Tuple

from utils.env_checker import check_all_api_keys, format_status_message, get_environment_status


def render_welcome_page():
    """渲染欢迎引导页"""

    # 检测环境状态
    env_status = get_environment_status()
    api_keys_status = check_all_api_keys()

    # 标题区域
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; margin-bottom: 1rem;">
        <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">KG AI Builder</h1>
        <p style="color: var(--text-muted); font-size: 1.1rem;">
            从文本到知识图谱的智能转换
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 功能介绍卡片
    st.markdown("""
    <div style="display: flex; gap: 1rem; margin-bottom: 2rem;">
        <div class="card" style="flex: 1; text-align: center; padding: 1.5rem;">
            <div style="font-size: 2rem; margin-bottom: 0.75rem;">📋</div>
            <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">Schema配置</div>
            <div style="color: var(--text-muted); font-size: 0.85rem;">定义知识结构</div>
        </div>
        <div class="card" style="flex: 1; text-align: center; padding: 1.5rem;">
            <div style="font-size: 2rem; margin-bottom: 0.75rem;">📄</div>
            <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">文档导入</div>
            <div style="color: var(--text-muted); font-size: 0.85rem;">上传或批量处理</div>
        </div>
        <div class="card" style="flex: 1; text-align: center; padding: 1.5rem;">
            <div style="font-size: 2rem; margin-bottom: 0.75rem;">⚙️</div>
            <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">智能抽取</div>
            <div style="color: var(--text-muted); font-size: 0.85rem;">LLM驱动的知识提取</div>
        </div>
        <div class="card" style="flex: 1; text-align: center; padding: 1.5rem;">
            <div style="font-size: 2rem; margin-bottom: 0.75rem;">✅</div>
            <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">审核入库</div>
            <div style="color: var(--text-muted); font-size: 0.85rem;">确认后存入Neo4j</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 环境状态检测
    st.subheader("🔍 环境状态检测")

    # Neo4j状态（暂不检测连接，只显示提示）
    st.markdown("""
    <div class="card" style="padding: 1rem;">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="font-size: 1.5rem;">⚪</div>
            <div style="flex: 1;">
                <div style="font-weight: 500; color: var(--text-primary);">Neo4j 数据库</div>
                <div style="color: var(--text-muted); font-size: 0.85rem;">连接将在配置步骤中检测</div>
            </div>
            <div style="color: var(--text-muted); font-size: 0.85rem;">待检测</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # API Key状态
    st.markdown("**API Key 配置状态**")

    api_key_html = ""
    for provider, status in api_keys_status.items():
        icon = "✅" if status.configured else "⚪"
        key_info = f" ({status.key_prefix})" if status.key_prefix else ""
        source_info = f" [{status.source}]" if status.source else ""

        api_key_html += f"""
        <div class="card" style="padding: 0.75rem 1rem; margin-bottom: 0.5rem;">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <div style="font-size: 1.1rem;">{icon}</div>
                <div style="flex: 1;">
                    <span style="color: var(--text-primary);">{provider.upper()}</span>
                    <span style="color: var(--text-muted); font-size: 0.85rem;">{key_info}{source_info}</span>
                </div>
            </div>
        </div>
        """

    st.markdown(api_key_html, unsafe_allow_html=True)

    # 建议
    if env_status.get('recommendations'):
        for rec in env_status['recommendations']:
            if rec['type'] == 'warning':
                st.warning(rec['message'])
            else:
                st.info(rec['message'])

    st.markdown("---")

    # 开始按钮
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("▶ 开始构建知识图谱", type="primary", use_container_width=True):
            return "start"

    # 底部链接
    st.markdown("""
    <div style="text-align: center; margin-top: 1rem; color: var(--text-muted);">
        <span>📚 <a href="#" style="color: var(--accent-primary);">使用帮助</a></span>
        <span style="margin-left: 2rem;">🐳 <a href="#" style="color: var(--accent-primary);">Docker部署</a></span>
    </div>
    """, unsafe_allow_html=True)

    return None


def render_help_section():
    """渲染帮助说明"""
    with st.expander("📚 使用帮助", expanded=False):
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
    with st.expander("🐳 Docker部署", expanded=False):
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