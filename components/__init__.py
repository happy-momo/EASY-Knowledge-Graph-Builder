"""
组件模块
"""

# 原有组件
from .ui_components import (
    display_header,
    display_step_navigation,
    display_loading_status,
    display_triple_cards,
    display_neo4j_config,
    display_build_button
)

# 新组件
from .step_navigation import (
    render_step_navigation,
    render_step_title,
    render_progress_bar,
    render_navigation_buttons,
    get_step_name,
    get_step_index
)

from .welcome_page import (
    render_welcome_page,
    render_help_section,
    render_docker_help
)

from .schema_templates import (
    render_schema_selection,
    render_template_selection,
    render_yaml_upload,
    render_manual_input,
    render_schema_preview,
    validate_schema
)

from .file_import import (
    render_file_import_section,
    render_file_list,
    get_all_chunks_for_processing,
    has_files_loaded,
    get_total_chunks
)

from .config_page import (
    render_config_section,
    render_llm_config,
    render_neo4j_config,
    render_review_mode_config,
    validate_config,
    render_config_summary,
    save_config_to_state,
    load_config_from_state
)

from .review_panel import (
    init_review_state,
    render_review_panel,
    render_triple_edit_modal,
    apply_review_action,
    save_review_state,
    load_review_state,
    TripleReviewState
)

from .process_display import (
    render_processing_page,
    render_progress_indicator,
    render_current_processing,
    render_recent_triples,
    render_completion_page,
    render_error_page,
    render_loading_animation
)


__all__ = [
    # 原有
    "display_header",
    "display_step_navigation",
    "display_loading_status",
    "display_triple_cards",
    "display_neo4j_config",
    "display_build_button",

    # 步骤导航
    "render_step_navigation",
    "render_step_title",
    "render_progress_bar",
    "render_navigation_buttons",
    "get_step_name",
    "get_step_index",

    # 欢迎页
    "render_welcome_page",
    "render_help_section",
    "render_docker_help",

    # Schema
    "render_schema_selection",
    "render_template_selection",
    "render_yaml_upload",
    "render_manual_input",
    "render_schema_preview",
    "validate_schema",

    # 文件导入
    "render_file_import_section",
    "render_file_list",
    "get_all_chunks_for_processing",
    "has_files_loaded",
    "get_total_chunks",

    # 配置
    "render_config_section",
    "render_llm_config",
    "render_neo4j_config",
    "render_review_mode_config",
    "validate_config",
    "render_config_summary",
    "save_config_to_state",
    "load_config_from_state",

    # 审核
    "init_review_state",
    "render_review_panel",
    "render_triple_edit_modal",
    "apply_review_action",
    "save_review_state",
    "load_review_state",
    "TripleReviewState",

    # 处理显示
    "render_processing_page",
    "render_progress_indicator",
    "render_current_processing",
    "render_recent_triples",
    "render_completion_page",
    "render_error_page",
    "render_loading_animation"
]