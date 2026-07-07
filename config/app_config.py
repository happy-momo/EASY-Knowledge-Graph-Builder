# 应用配置文件

from typing import Dict, List, Any

# ==================== 页面配置 ====================
PAGE_CONFIG = {
    "page_title": "KG AI Builder",
    "layout": "wide",
    "page_icon": "🔗",
    "initial_sidebar_state": "collapsed"
}

# ==================== 默认配置 ====================
DEFAULT_CONFIG = {
    "neo4j_uri": "bolt://localhost:7687",
    "neo4j_user": "neo4j",
    "neo4j_password": "",
    "text_chunk_size": 2000,
    "text_min_chunk_size": 500,
    "llm_temperature": 0.1,
    "review_mode": "auto"  # auto 或 manual
}

# ==================== 状态键名 ====================
SESSION_STATE_KEYS = {
    "current_step": "current_step",
    "schema_config": "schema_config",
    "uploaded_files": "uploaded_files",
    "llm_model": "llm_model",
    "llm_api_key": "llm_api_key",
    "neo4j_uri": "neo4j_uri",
    "neo4j_user": "neo4j_user",
    "neo4j_password": "neo4j_password",
    "review_mode": "review_mode",
    "build_state": "building",
    "build_success": "build_success",
    "current_chunk_index": "current_chunk_index",
    "total_chunks": "total_chunks",
    "processing_start_time": "processing_start_time",
    "total_triples": "total_triples",
    "triples_for_review": "triples_for_review",
    "reviewed_triples": "reviewed_triples",
    "error_message": "error_message",
    "error_stack": "error_stack"
}

# ==================== 步骤定义 ====================
STEPS = [
    {"id": 0, "name": "welcome", "title": "欢迎", "description": "开始使用"},
    {"id": 1, "name": "schema", "title": "Schema", "description": "定义知识结构"},
    {"id": 2, "name": "files", "title": "文件", "description": "导入文档"},
    {"id": 3, "name": "config", "title": "配置", "description": "连接设置"},
    {"id": 4, "name": "process", "title": "抽取", "description": "知识提取"},
    {"id": 5, "name": "review", "title": "审核", "description": "确认结果"},
    {"id": 6, "name": "complete", "title": "完成", "description": "查看结果"}
]

# ==================== LLM 模型配置 ====================
LLM_OPTIONS = [
    {
        "name": "GLM-4-Flash (智谱AI)",
        "key": "glm4_flash",
        "model_name": "glm-4-flash",
        "provider": "zhipu",
        "api_key_label": "智谱AI API Key",
        "api_env_key": "ZHIPU_API_KEY"
    },
    {
        "name": "GLM-4 (智谱AI)",
        "key": "glm4",
        "model_name": "glm-4",
        "provider": "zhipu",
        "api_key_label": "智谱AI API Key",
        "api_env_key": "ZHIPU_API_KEY"
    },
    {
        "name": "GPT-4 (OpenAI)",
        "key": "gpt4",
        "model_name": "gpt-4",
        "provider": "openai",
        "api_key_label": "OpenAI API Key",
        "api_env_key": "OPENAI_API_KEY"
    },
    {
        "name": "GPT-3.5-Turbo (OpenAI)",
        "key": "gpt35",
        "model_name": "gpt-3.5-turbo",
        "provider": "openai",
        "api_key_label": "OpenAI API Key",
        "api_env_key": "OPENAI_API_KEY"
    },
    {
        "name": "GPT-4-Turbo (OpenAI)",
        "key": "gpt4_turbo",
        "model_name": "gpt-4-turbo",
        "provider": "openai",
        "api_key_label": "OpenAI API Key",
        "api_env_key": "OPENAI_API_KEY"
    },
    {
        "name": "Claude 3-Opus (Anthropic)",
        "key": "claude3_opus",
        "model_name": "claude-3-opus-20240229",
        "provider": "anthropic",
        "api_key_label": "Anthropic API Key",
        "api_env_key": "ANTHROPIC_API_KEY"
    },
    {
        "name": "Claude 3-Sonnet (Anthropic)",
        "key": "claude3_sonnet",
        "model_name": "claude-3-sonnet-20240229",
        "provider": "anthropic",
        "api_key_label": "Anthropic API Key",
        "api_env_key": "ANTHROPIC_API_KEY"
    },
    {
        "name": "Claude 3-Haiku (Anthropic)",
        "key": "claude3_haiku",
        "model_name": "claude-3-haiku-20240307",
        "provider": "anthropic",
        "api_key_label": "Anthropic API Key",
        "api_env_key": "ANTHROPIC_API_KEY"
    },
    {
        "name": "Gemini-Pro (Google)",
        "key": "gemini_pro",
        "model_name": "gemini-pro",
        "provider": "google",
        "api_key_label": "Google API Key",
        "api_env_key": "GOOGLE_API_KEY"
    },
    {
        "name": "Qwen-Turbo (阿里云通义千问)",
        "key": "qwen_turbo",
        "model_name": "qwen-turbo",
        "provider": "alibaba",
        "api_key_label": "阿里云 API Key",
        "api_env_key": "DASHSCOPE_API_KEY"
    },
    {
        "name": "Qwen-Plus (阿里云通义千问)",
        "key": "qwen_plus",
        "model_name": "qwen-plus",
        "provider": "alibaba",
        "api_key_label": "阿里云 API Key",
        "api_env_key": "DASHSCOPE_API_KEY"
    }
]

# ==================== Schema 模板 ====================
SCHEMA_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "人员组织关系": {
        "description": "人员、组织、部门等实体，适合企业人事管理、组织架构分析",
        "entities": [
            {
                "name": "Person",
                "properties": ["name", "age", "gender", "position", "email", "phone"]
            },
            {
                "name": "Organization",
                "properties": ["name", "industry", "location", "founded", "size"]
            },
            {
                "name": "Department",
                "properties": ["name", "function", "budget"]
            },
            {
                "name": "Location",
                "properties": ["name", "type", "country", "city"]
            },
            {
                "name": "Project",
                "properties": ["name", "status", "start_date", "end_date"]
            }
        ],
        "relationships": [
            {"head": "Person", "relation": "worksAt", "tail": "Organization"},
            {"head": "Person", "relation": "belongsTo", "tail": "Department"},
            {"head": "Person", "relation": "livesIn", "tail": "Location"},
            {"head": "Person", "relation": "manages", "tail": "Person"},
            {"head": "Person", "relation": "worksOn", "tail": "Project"},
            {"head": "Department", "relation": "partOf", "tail": "Organization"},
            {"head": "Organization", "relation": "locatedIn", "tail": "Location"},
            {"head": "Organization", "relation": "partnersWith", "tail": "Organization"}
        ]
    },
    "产品供应链": {
        "description": "产品、供应商、制造商等实体，适合供应链分析",
        "entities": [
            {
                "name": "Product",
                "properties": ["name", "category", "price", "sku", "description"]
            },
            {
                "name": "Supplier",
                "properties": ["name", "country", "rating", "lead_time"]
            },
            {
                "name": "Manufacturer",
                "properties": ["name", "location", "capacity", "type"]
            },
            {
                "name": "Customer",
                "properties": ["name", "type", "region", "segment"]
            },
            {
                "name": "Logistics",
                "properties": ["name", "type", "coverage", "speed"]
            },
            {
                "name": "Warehouse",
                "properties": ["name", "location", "capacity", "type"]
            }
        ],
        "relationships": [
            {"head": "Product", "relation": "suppliedBy", "tail": "Supplier"},
            {"head": "Product", "relation": "manufacturedBy", "tail": "Manufacturer"},
            {"head": "Customer", "relation": "purchases", "tail": "Product"},
            {"head": "Product", "relation": "shippedBy", "tail": "Logistics"},
            {"head": "Supplier", "relation": "deliversTo", "tail": "Manufacturer"},
            {"head": "Manufacturer", "relation": "storesAt", "tail": "Warehouse"},
            {"head": "Warehouse", "relation": "serves", "tail": "Customer"}
        ]
    },
    "学术论文引用": {
        "description": "论文、作者、期刊等实体，适合学术文献分析",
        "entities": [
            {
                "name": "Paper",
                "properties": ["title", "year", "venue", "doi", "abstract", "keywords"]
            },
            {
                "name": "Author",
                "properties": ["name", "affiliation", "h_index", "research_area"]
            },
            {
                "name": "Journal",
                "properties": ["name", "impact_factor", "publisher", "field"]
            },
            {
                "name": "Conference",
                "properties": ["name", "year", "location", "field"]
            },
            {
                "name": "Keyword",
                "properties": ["name", "category", "frequency"]
            },
            {
                "name": "Institution",
                "properties": ["name", "country", "type", "rank"]
            }
        ],
        "relationships": [
            {"head": "Paper", "relation": "writtenBy", "tail": "Author"},
            {"head": "Paper", "relation": "publishedIn", "tail": "Journal"},
            {"head": "Paper", "relation": "presentedAt", "tail": "Conference"},
            {"head": "Paper", "relation": "cites", "tail": "Paper"},
            {"head": "Paper", "relation": "hasKeyword", "tail": "Keyword"},
            {"head": "Author", "relation": "affiliatedWith", "tail": "Institution"},
            {"head": "Author", "relation": "collaboratesWith", "tail": "Author"},
            {"head": "Keyword", "relation": "relatedTo", "tail": "Keyword"}
        ]
    },
    "医疗健康知识": {
        "description": "疾病、症状、药物等实体，适合医疗健康领域",
        "entities": [
            {
                "name": "Disease",
                "properties": ["name", "icd_code", "category", "severity", "prevalence"]
            },
            {
                "name": "Symptom",
                "properties": ["name", "severity", "duration", "type"]
            },
            {
                "name": "Drug",
                "properties": ["name", "generic_name", "dosage_form", "approval_status"]
            },
            {
                "name": "Treatment",
                "properties": ["name", "type", "duration", "effectiveness"]
            },
            {
                "name": "Organ",
                "properties": ["name", "system", "function", "location"]
            },
            {
                "name": "Patient",
                "properties": ["name", "age", "gender", "medical_history"]
            }
        ],
        "relationships": [
            {"head": "Disease", "relation": "hasSymptom", "tail": "Symptom"},
            {"head": "Disease", "relation": "treatedBy", "tail": "Treatment"},
            {"head": "Drug", "relation": "treats", "tail": "Disease"},
            {"head": "Disease", "relation": "affects", "tail": "Organ"},
            {"head": "Drug", "relation": "causesSideEffect", "tail": "Symptom"},
            {"head": "Treatment", "relation": "usesDrug", "tail": "Drug"},
            {"head": "Patient", "relation": "diagnosedWith", "tail": "Disease"},
            {"head": "Patient", "relation": "takes", "tail": "Drug"}
        ]
    }
}

# ==================== 帮助文本 ====================
HELP_TEXTS = {
    "schema_template": "选择预设模板快速定义知识图谱结构，无需手动编写YAML",
    "schema_yaml": "上传自定义YAML文件定义实体类型、属性和关系",
    "chunk_size": "文本分块大小影响处理效率和准确性，建议2000-3000字符",
    "llm_model": "不同模型有不同的性能特点，智谱AI和通义千问在国内访问更稳定",
    "api_key": "API Key用于调用LLM服务，可从环境变量自动读取",
    "neo4j_uri": "Neo4j数据库连接地址，默认使用本地7687端口",
    "neo4j_password": "Neo4j数据库密码，首次使用需要设置",
    "review_mode": "自动审核：抽取后直接入库\n人工审核：逐个确认三元组"
}

# ==================== 日志级别 ====================
LOG_LEVEL = "INFO"