"""
KG AI Builder - 主应用（重构版）

产品化设计，使用新的视觉系统和标准化LLM配置。
"""

import streamlit as st
import yaml
import json
import time
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# 页面配置
from config.app_config import PAGE_CONFIG, STEPS, DEFAULT_CONFIG
st.set_page_config(**PAGE_CONFIG)

# 加载CSS样式
try:
    with open("styles/main.css", "r", encoding="utf-8") as f:
        custom_css = f.read()
    st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("CSS样式文件未找到，使用默认样式")
    custom_css = ""

# 导入新的核心模块
from utils.llm_config import LLMConfig, get_preset_configs, create_llm_config_from_preset
from utils.extractor import extract_triples, KnowledgeGraphTriple, ExtractionError
from utils.cypher_generator import generate_cypher_safe
from utils.neo4j_manager import Neo4jManager
from utils.state_manager import state_manager
from utils.progress_tracker import progress_tracker
from utils.file_manager import file_manager
from utils.env_checker import check_neo4j_connection

# 导入组件
from components import (
    render_step_navigation,
    render_step_title,
    render_navigation_buttons,
    get_step_name,
    get_step_index,
    render_welcome_page,
    render_help_section,
    render_docker_help,
    render_schema_selection,
    validate_schema,
    render_file_import_section,
    has_files_loaded,
    get_all_chunks_for_processing,
    render_config_section,
    validate_config,
    save_config_to_state,
    load_config_from_state,
    init_review_state,
    render_review_panel,
    render_triple_edit_modal,
    apply_review_action,
    save_review_state,
    load_review_state,
    TripleReviewState,
    render_processing_page,
    render_progress_indicator,
    render_completion_page,
    render_error_page,
    render_loading_animation
)


# ==================== 状态初始化 ====================
def init_session_state():
    """初始化session_state"""
    defaults = {
        'current_step': 0,
        'completed_steps': [],
        'schema_config': None,
        'schema_yaml': "",
        'config': None,
        'is_processing': False,
        'processing_result': None,
        'review_state': None,
        'llm_config': None
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def load_persisted_state():
    """从持久化存储加载状态"""
    # 加载配置
    saved_config = state_manager.load('config')
    if saved_config and not st.session_state.config:
        st.session_state.config = saved_config

    # 加载LLM配置
    saved_llm = state_manager.load('llm_config')
    if saved_llm:
        st.session_state.llm_config = LLMConfig.from_dict(saved_llm)

    # 检查是否有可恢复的进度（仅在用户确认后恢复）
    if progress_tracker.can_resume() and not st.session_state.get('_resume_shown'):
        # 显示恢复提示，让用户选择是否恢复
        st.session_state._pending_resume = True


def show_resume_prompt():
    """显示恢复提示"""
    if st.session_state.get('_pending_resume') and not st.session_state.get('_resume_shown'):
        # 使用HTML自定义样式，确保文字可见
        st.markdown(
            '<div style="background-color: #fef3c7; border: 1px solid #f59e0b; '
            'border-radius: 8px; padding: 16px; margin: 16px 0; color: #92400e;">'
            '    <p style="margin: 0; font-weight: 600; color: #92400e;">'
            '        ⚠️ 检测到未完成的处理任务'
            '    </p>'
            '    <p style="margin: 8px 0 0 0; color: #92400e;">'
            '        您有未完成的处理任务，是否恢复？'
            '    </p>'
            '</div>',
            unsafe_allow_html=True
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("恢复处理", key="resume_processing"):
                st.session_state.current_step = 4
                st.session_state.is_processing = True
                st.session_state._resume_shown = True
                st.session_state._pending_resume = False
                st.rerun()
        with col2:
            if st.button("重新开始", key="reset_processing"):
                progress_tracker.reset()
                st.session_state._resume_shown = True
                st.session_state._pending_resume = False
                st.rerun()
        return True
    return False


def save_persisted_state():
    """保存状态到持久化存储"""
    if st.session_state.config:
        state_manager.save('config', st.session_state.config)

    if st.session_state.llm_config:
        state_manager.save('llm_config', st.session_state.llm_config.to_dict())


# ==================== 主应用 ====================
def main():
    """主应用流程"""
    # 初始化
    init_session_state()
    load_persisted_state()

    # 检查是否需要显示恢复提示
    if show_resume_prompt():
        return

    # 渲染步骤导航
    render_step_navigation(
        st.session_state.current_step,
        st.session_state.completed_steps
    )

    # 根据当前步骤渲染页面
    current_step = st.session_state.current_step

    step_functions = [
        render_welcome_step,
        render_schema_step,
        render_file_step,
        render_config_step,
        render_process_step,
        render_review_step,
        render_complete_step
    ]

    if 0 <= current_step < len(step_functions):
        step_functions[current_step]()


# ==================== 步骤实现 ====================
def render_welcome_step():
    """步骤0: 欢迎页"""
    render_step_title(0)

    # 渲染欢迎页
    action = render_welcome_page()

    # 渲染帮助
    render_help_section()
    render_docker_help()

    # 处理开始动作
    if action == "start":
        st.session_state.current_step = 1
        st.rerun()


def render_schema_step():
    """步骤1: Schema配置"""
    render_step_title(1)

    # 渲染Schema选择
    schema_dict, schema_yaml = render_schema_selection()

    if schema_dict:
        # 验证Schema
        is_valid, error_msg = validate_schema(schema_dict)

        if is_valid:
            st.session_state.schema_config = schema_dict
            st.session_state.schema_yaml = schema_yaml

            # 导航按钮
            action = render_navigation_buttons(
                current_step=1,
                can_proceed=True,
                show_back=True
            )

            if action == "next":
                st.session_state.completed_steps.append(1)
                st.session_state.current_step = 2
                st.rerun()
            elif action == "back":
                st.session_state.current_step = 0
                st.rerun()
        else:
            st.error(error_msg)


def render_file_step():
    """步骤2: 文件导入"""
    render_step_title(2)

    # 渲染文件导入
    files, changed = render_file_import_section()

    # 检查是否有文件
    can_proceed = has_files_loaded()

    if not can_proceed:
        st.warning("请先导入至少一个文件")

    # 导航按钮
    action = render_navigation_buttons(
        current_step=2,
        can_proceed=can_proceed,
        show_back=True
    )

    if action == "next" and can_proceed:
        st.session_state.completed_steps.append(2)
        st.session_state.current_step = 3
        st.rerun()
    elif action == "back":
        st.session_state.current_step = 1
        st.rerun()


def render_config_step():
    """步骤3: 配置"""
    render_step_title(3)

    # 渲染配置界面
    config = render_config_section()

    # 验证配置
    is_valid, missing = validate_config(config)

    if not is_valid:
        st.warning(f"请完成以下配置: {', '.join(missing)}")

    # 保存配置到state
    st.session_state.config = config
    save_config_to_state(config)
    save_persisted_state()

    # 导航按钮
    action = render_navigation_buttons(
        current_step=3,
        can_proceed=is_valid,
        show_back=True,
        next_label="开始抽取"
    )

    if action == "next" and is_valid:
        st.session_state.completed_steps.append(3)
        st.session_state.current_step = 4
        st.rerun()
    elif action == "back":
        st.session_state.current_step = 2
        st.rerun()


def render_process_step():
    """步骤4: 抽取处理"""
    render_step_title(4)

    # 检查是否可以恢复处理
    can_resume = progress_tracker.can_resume()

    if can_resume:
        st.info("检测到未完成的处理任务，可以继续处理。")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("继续处理", type="primary"):
                start_extraction_process(resume=True)
        with col2:
            if st.button("重新开始"):
                progress_tracker.reset()
                st.rerun()

    elif not st.session_state.is_processing:
        # 开始处理按钮
        if st.button("▶ 开始知识抽取", type="primary", use_container_width=True):
            start_extraction_process()

    else:
        # 显示处理进度
        progress = progress_tracker.get_progress()
        render_processing_page(progress)

        # 如果处理完成
        if progress.status == 'completed':
            st.session_state.is_processing = False
            st.session_state.processing_result = progress.get_statistics()

            # 根据审核模式决定下一步
            if st.session_state.config.get('review_mode') == 'manual':
                st.session_state.current_step = 5
            else:
                st.session_state.completed_steps.append(5)
                st.session_state.current_step = 6

            st.rerun()

        # 如果处理出错
        elif progress.status == 'error':
            st.session_state.is_processing = False
            st.error("处理过程中发生错误")


def start_extraction_process(resume: bool = False):
    """开始抽取处理"""
    # 获取所有分块
    chunks = get_all_chunks_for_processing()

    if not chunks:
        st.error("没有可处理的文本块")
        return

    # 初始化进度
    if not resume:
        progress_tracker.reset()
        progress_tracker.start(
            total_files=len(set(c[0] for c in chunks)),
            total_chunks=len(chunks)
        )

    st.session_state.is_processing = True

    # 获取配置
    config = st.session_state.config
    llm_config_dict = config['llm']

    # 创建LLM配置
    llm_config = LLMConfig(
        api_endpoint=llm_config_dict['api_endpoint'],
        api_key=llm_config_dict['api_key'],
        model_name=llm_config_dict['model_name'],
        provider=llm_config_dict.get('provider', 'custom'),
        temperature=llm_config_dict.get('temperature', 0.1),
        max_tokens=llm_config_dict.get('max_tokens', 2048)
    )

    # 初始化Neo4j连接（自动审核模式）
    neo4j_manager = None
    if config['review_mode'] == 'auto':
        neo4j_config = config['neo4j']
        neo4j_manager = Neo4jManager(
            neo4j_config['uri'],
            neo4j_config['user'],
            neo4j_config['password']
        )

    try:
        # 处理每个分块
        pending_chunks = chunks if not resume else [
            c for c in chunks
            if c[2] in progress_tracker.get_pending_chunks()
        ]

        for file_id, file_name, chunk_index, chunk_content in pending_chunks:
            # 更新进度
            progress_tracker.update_chunk_start(chunk_index, file_name, file_id)

            # 调用LLM抽取
            triples = extract_triples(
                chunk_content,
                st.session_state.schema_yaml,
                llm_config
            )

            if triples:
                # 转换为字典格式
                triples_dict = [
                    {
                        'head': t.head,
                        'head_type': t.head_type,
                        'head_properties': t.head_properties,
                        'relation': t.relation,
                        'tail': t.tail,
                        'tail_type': t.tail_type,
                        'tail_properties': t.tail_properties
                    }
                    for t in triples
                ]

                # 更新进度
                progress_tracker.update_chunk_complete(
                    chunk_index,
                    triples_dict,
                    len(triples)
                )

                # 自动审核模式：直接存入数据库
                if config['review_mode'] == 'auto' and neo4j_manager:
                    cypher_queries = generate_cypher_safe(triples)
                    neo4j_manager.execute_cypher(cypher_queries)

            else:
                progress_tracker.update_chunk_complete(chunk_index, [], 0)

            # 短暂延迟让用户看到进度
            time.sleep(0.1)

        # 完成处理
        progress_tracker.complete()

    except ExtractionError as e:
        progress_tracker.error(str(e))
        st.error(f"抽取失败: {e}")
        st.session_state.is_processing = False

    except Exception as e:
        progress_tracker.error(str(e))
        st.error(f"处理出错: {e}")
        st.session_state.is_processing = False

    finally:
        if neo4j_manager:
            neo4j_manager.close()

    st.rerun()


def render_review_step():
    """步骤5: 人工审核"""
    render_step_title(5)

    # 获取所有三元组
    all_triples = progress_tracker.get_all_triples()

    if not all_triples:
        st.warning("没有需要审核的三元组")
        st.session_state.current_step = 6
        st.rerun()

    # 初始化审核状态
    if st.session_state.review_state is None:
        st.session_state.review_state = init_review_state(all_triples)

    review_state = st.session_state.review_state

    # 渲染审核面板
    action, idx = render_review_panel(review_state)

    # 处理编辑动作
    if action == 'edit' and idx is not None:
        edited_triple = show_edit_modal(idx, review_state.triples[idx])
        if edited_triple:
            apply_review_action(review_state, 'edit', idx, edited_triple)
            save_review_state(review_state)
            st.rerun()

    # 处理其他动作
    elif action in ('confirm', 'delete') and idx is not None:
        apply_review_action(review_state, action, idx)
        save_review_state(review_state)
        st.rerun()

    elif action in ('confirm_all', 'skip_review'):
        apply_review_action(review_state, action, None)
        save_review_state(review_state)

    elif action == 'complete':
        # 保存审核后的三元组到数据库
        save_reviewed_triples(review_state)
        st.session_state.completed_steps.append(5)
        st.session_state.current_step = 6
        st.rerun()


def show_edit_modal(idx: int, triple: Dict) -> Optional[Dict]:
    """显示编辑弹窗"""
    save, edited_triple = render_triple_edit_modal(idx, triple)
    if save:
        return edited_triple
    return None


def save_reviewed_triples(review_state: TripleReviewState):
    """保存审核后的三元组到数据库"""
    triples_to_save = review_state.get_triples_to_save()

    if not triples_to_save:
        return

    # 获取配置
    config = st.session_state.config
    neo4j_config = config['neo4j']

    # 使用Neo4jManager
    with Neo4jManager(
        neo4j_config['uri'],
        neo4j_config['user'],
        neo4j_config['password']
    ) as neo4j_manager:
        # 转换为KnowledgeGraphTriple对象
        triples_obj = []
        for t_dict in triples_to_save:
            triple_obj = KnowledgeGraphTriple(
                head=t_dict['head'],
                head_type=t_dict['head_type'],
                head_properties=t_dict['head_properties'],
                relation=t_dict['relation'],
                tail=t_dict['tail'],
                tail_type=t_dict['tail_type'],
                tail_properties=t_dict['tail_properties']
            )
            triples_obj.append(triple_obj)

        # 生成安全的Cypher查询
        cypher_queries = generate_cypher_safe(triples_obj)
        neo4j_manager.execute_cypher(cypher_queries)


def render_complete_step():
    """步骤6: 完成"""
    render_step_title(6)

    # 获取统计
    stats = st.session_state.processing_result or progress_tracker.get_statistics()

    # 渲染完成页面
    action = render_completion_page(stats)

    if action == "restart":
        # 重置所有状态
        reset_all_state()
        st.rerun()


def reset_all_state():
    """重置所有状态"""
    st.session_state.current_step = 0
    st.session_state.completed_steps = []
    st.session_state.schema_config = None
    st.session_state.schema_yaml = ""
    st.session_state.config = None
    st.session_state.is_processing = False
    st.session_state.processing_result = None
    st.session_state.review_state = None
    st.session_state.llm_config = None

    progress_tracker.reset()
    file_manager.clear_all()
    state_manager.clear()


# ==================== 运行应用 ====================
if __name__ == "__main__":
    main()