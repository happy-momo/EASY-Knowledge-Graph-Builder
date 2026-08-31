"""
标准化 LLM 配置模块 — 双路由设计

路径 A（OpenAI 兼容）：国内厂商及自定义模型，使用 ChatOpenAI + base_url
路径 B（原生 LangChain）：全球主流厂商，使用 init_chat_model 自动路由

用户只需输入：API 端点、API Key、模型名称
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from enum import Enum

logger = logging.getLogger(__name__)


# ==================== 厂家类型枚举 ====================

class VendorType(Enum):
    """厂家接口类型"""
    OPENAI_COMPATIBLE = "openai_compatible"  # 路径 A：OpenAI 兼容接口
    NATIVE_LANGCHAIN = "native_langchain"    # 路径 B：原生 LangChain 包


# ==================== 双路由厂商注册表 ====================

# 路径 A：OpenAI 兼容厂商注册表（使用 ChatOpenAI + base_url）
OPENAI_COMPATIBLE_VENDORS = {
    "zhipu": {
        "display_name": "智谱 AI",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "model_examples": "glm-4, glm-4-flash",
        "env_keys": ["ZHIPU_API_KEY", "GLM_API_KEY"],
    },
    "alibaba": {
        "display_name": "阿里云 (通义千问)",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/",
        "model_examples": "qwen-turbo, qwen-plus",
        "env_keys": ["DASHSCOPE_API_KEY", "ALIBABA_API_KEY", "QWEN_API_KEY"],
    },
    "deepseek": {
        "display_name": "深度求索 (DeepSeek)",
        "base_url": "https://api.deepseek.com/",
        "model_examples": "deepseek-chat, deepseek-coder",
        "env_keys": ["DEEPSEEK_API_KEY"],
    },
    "moonshot": {
        "display_name": "月之暗面 (Kimi)",
        "base_url": "https://api.moonshot.cn/v1/",
        "model_examples": "moonshot-v1-8k, moonshot-v1-32k",
        "env_keys": ["MOONSHOT_API_KEY", "KIMI_API_KEY"],
    },
    "custom": {
        "display_name": "自定义 (OpenAI 兼容)",
        "base_url": "",
        "model_examples": "任意模型名称",
        "env_keys": [],
    },
}

# 路径 B：原生 LangChain 厂商注册表（使用 init_chat_model）
NATIVE_LANGCHAIN_VENDORS = {
    "openai": {
        "display_name": "OpenAI",
        "model_provider": "openai",
        "base_url": "https://api.openai.com/v1/",
        "model_examples": "gpt-4, gpt-4o, gpt-3.5-turbo",
        "env_keys": ["OPENAI_API_KEY"],
    },
    "anthropic": {
        "display_name": "Anthropic (Claude)",
        "model_provider": "anthropic",
        "base_url": "https://api.anthropic.com/",
        "model_examples": "claude-3-opus-20240229, claude-3-sonnet-20240229",
        "env_keys": ["ANTHROPIC_API_KEY"],
    },
    "google": {
        "display_name": "Google (Gemini)",
        "model_provider": "google-genai",
        "base_url": "",
        "model_examples": "gemini-pro, gemini-1.5-pro",
        "env_keys": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
    },
}


# ==================== 便捷查询函数 ====================

def get_vendor_info(vendor_type: str, provider: str) -> Optional[dict]:
    """
    获取厂商信息（统一入口）

    Args:
        vendor_type: "openai_compatible" 或 "native_langchain"
        provider: 厂商标识

    Returns:
        厂商信息字典，未找到返回 None
    """
    if vendor_type == "openai_compatible":
        return OPENAI_COMPATIBLE_VENDORS.get(provider)
    elif vendor_type == "native_langchain":
        return NATIVE_LANGCHAIN_VENDORS.get(provider)
    return None


def get_all_vendor_options() -> List[Dict]:
    """
    获取所有可选厂商（按路径分组）

    Returns:
        列表，每项包含 vendor_type, provider, display_name, base_url, model_examples
    """
    options = []
    for provider, info in OPENAI_COMPATIBLE_VENDORS.items():
        options.append({
            "vendor_type": "openai_compatible",
            "provider": provider,
            "display_name": info["display_name"],
            "base_url": info.get("base_url", ""),
            "model_examples": info.get("model_examples", ""),
        })
    for provider, info in NATIVE_LANGCHAIN_VENDORS.items():
        options.append({
            "vendor_type": "native_langchain",
            "provider": provider,
            "display_name": info["display_name"],
            "base_url": info.get("base_url", ""),
            "model_examples": info.get("model_examples", ""),
        })
    return options


def get_default_base_url(vendor_type: str, provider: str) -> str:
    """
    获取厂商默认 base_url

    Args:
        vendor_type: "openai_compatible" 或 "native_langchain"
        provider: 厂商标识

    Returns:
        默认 base_url，未找到返回空字符串
    """
    info = get_vendor_info(vendor_type, provider)
    return info.get("base_url", "") if info else ""


def get_vendor_type_label(vendor_type: str) -> str:
    """获取厂家类型的显示标签"""
    labels = {
        "openai_compatible": "OpenAI 兼容接口",
        "native_langchain": "原生 LangChain",
    }
    return labels.get(vendor_type, vendor_type)


# ==================== 统一服务商列表（用户视角，隐藏路由细节） ====================

# 推荐顺序：国内常用优先，再全球主流，最后自定义
_UNIFIED_VENDOR_ORDER = [
    ("zhipu", "openai_compatible"),
    ("alibaba", "openai_compatible"),
    ("deepseek", "openai_compatible"),
    ("moonshot", "openai_compatible"),
    ("openai", "native_langchain"),
    ("anthropic", "native_langchain"),
    ("google", "native_langchain"),
    ("custom", "openai_compatible"),
]


def get_unified_vendor_list() -> List[Dict]:
    """
    获取统一的服务商列表（按推荐顺序），合并双路由注册表。

    每项字段：
        label           显示名称（用户唯一可见标识）
        vendor_type     路由类型（内部使用）
        provider        厂商标识（内部使用）
        base_url        默认端点
        model_examples  示例模型
        env_keys        环境变量名列表
        is_google       是否为 Google（无需端点）
        is_custom       是否为自定义（端点必填）
    """
    result = []
    for provider, vendor_type in _UNIFIED_VENDOR_ORDER:
        info = get_vendor_info(vendor_type, provider)
        if not info:
            continue
        result.append({
            "label": info["display_name"],
            "vendor_type": vendor_type,
            "provider": provider,
            "base_url": info.get("base_url", ""),
            "model_examples": info.get("model_examples", ""),
            "env_keys": info.get("env_keys", []),
            "is_google": (vendor_type == "native_langchain" and provider == "google"),
            "is_custom": (provider == "custom"),
        })
    return result


def resolve_vendor(label: str) -> Optional[Dict]:
    """根据显示名称解析服务商路由信息"""
    for v in get_unified_vendor_list():
        if v["label"] == label:
            return v
    return None


def get_vendor_label(vendor_type: str, provider: str) -> Optional[str]:
    """根据路由信息反查显示名称（用于从缓存恢复选中项）"""
    for v in get_unified_vendor_list():
        if v["vendor_type"] == vendor_type and v["provider"] == provider:
            return v["label"]
    return None


# ==================== LLM 配置数据类 ====================

@dataclass
class LLMConfig:
    """标准化 LLM 配置"""
    # 必填
    api_endpoint: str       # API 端点 URL（Google 等特殊厂商可留空）
    api_key: str            # API Key
    model_name: str         # 模型名称

    # 路由关键字段
    vendor_type: str = "openai_compatible"  # "openai_compatible" | "native_langchain"
    provider: str = "custom"                # 具体厂商标识

    # 可选
    temperature: float = 0.1
    max_tokens: int = 2048
    timeout: int = 60

    # 高级配置
    api_version: str = ""     # API 版本（如需要）
    organization: str = ""    # 组织 ID（如需要）

    # 额外参数（传递给特定厂商的 SDK）
    extra_params: Dict = field(default_factory=dict)

    def __post_init__(self):
        """验证配置并自动补全"""
        if not self.api_key:
            raise ValueError("API Key 不能为空")
        if not self.model_name:
            raise ValueError("模型名称不能为空")

        # Google 不需要 API 端点，其他厂商需要
        if not (self.vendor_type == "native_langchain" and self.provider == "google") and not self.api_endpoint:
            raise ValueError("API 端点不能为空")

        # 自动补全协议
        if self.api_endpoint and not self.api_endpoint.startswith(('http://', 'https://')):
            self.api_endpoint = 'https://' + self.api_endpoint

        # 自动推断 vendor_type（兼容旧配置：只有 provider 没有 vendor_type 的情况）
        if self.vendor_type == "openai_compatible" and self.provider in NATIVE_LANGCHAIN_VENDORS:
            # 如果 provider 属于路径 B 但 vendor_type 还是默认值，自动修正
            self.vendor_type = "native_langchain"

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'api_endpoint': self.api_endpoint,
            'api_key': self.api_key,
            'model_name': self.model_name,
            'vendor_type': self.vendor_type,
            'provider': self.provider,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'timeout': self.timeout,
            'api_version': self.api_version,
            'organization': self.organization,
            'extra_params': self.extra_params
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'LLMConfig':
        """从字典创建（向后兼容：旧配置无 vendor_type 字段时自动推断）"""
        provider = data.get('provider', 'custom')
        vendor_type = data.get('vendor_type', '')

        # 向后兼容：旧配置没有 vendor_type，根据 provider 推断
        if not vendor_type:
            if provider in NATIVE_LANGCHAIN_VENDORS:
                vendor_type = "native_langchain"
            else:
                vendor_type = "openai_compatible"

        return cls(
            api_endpoint=data.get('api_endpoint', ''),
            api_key=data.get('api_key', ''),
            model_name=data.get('model_name', ''),
            vendor_type=vendor_type,
            provider=provider,
            temperature=data.get('temperature', 0.1),
            max_tokens=data.get('max_tokens', 2048),
            timeout=data.get('timeout', 60),
            api_version=data.get('api_version', ''),
            organization=data.get('organization', ''),
            extra_params=data.get('extra_params', {})
        )


# ==================== 预设配置模板 ====================

PRESET_CONFIGS = {
    "zhipu_glm4": {
        "name": "智谱 AI - GLM-4",
        "vendor_type": "openai_compatible",
        "provider": "zhipu",
        "api_endpoint": "https://open.bigmodel.cn/api/paas/v4/",
        "model_name": "glm-4",
        "description": "智谱 AI 的 GLM-4 模型，适合中文场景"
    },
    "zhipu_glm4_flash": {
        "name": "智谱 AI - GLM-4-Flash",
        "vendor_type": "openai_compatible",
        "provider": "zhipu",
        "api_endpoint": "https://open.bigmodel.cn/api/paas/v4/",
        "model_name": "glm-4-flash",
        "description": "智谱 AI 的 GLM-4-Flash 模型，速度快"
    },
    "openai_gpt4": {
        "name": "OpenAI - GPT-4",
        "vendor_type": "native_langchain",
        "provider": "openai",
        "api_endpoint": "https://api.openai.com/v1/",
        "model_name": "gpt-4",
        "description": "OpenAI GPT-4 模型"
    },
    "openai_gpt4o": {
        "name": "OpenAI - GPT-4o",
        "vendor_type": "native_langchain",
        "provider": "openai",
        "api_endpoint": "https://api.openai.com/v1/",
        "model_name": "gpt-4o",
        "description": "OpenAI GPT-4o 模型，多模态能力"
    },
    "anthropic_claude3": {
        "name": "Anthropic - Claude 3",
        "vendor_type": "native_langchain",
        "provider": "anthropic",
        "api_endpoint": "https://api.anthropic.com/",
        "model_name": "claude-3-opus-20240229",
        "description": "Anthropic Claude 3 Opus 模型"
    },
    "anthropic_claude3_sonnet": {
        "name": "Anthropic - Claude 3 Sonnet",
        "vendor_type": "native_langchain",
        "provider": "anthropic",
        "api_endpoint": "https://api.anthropic.com/",
        "model_name": "claude-3-sonnet-20240229",
        "description": "Anthropic Claude 3 Sonnet 模型"
    },
    "google_gemini": {
        "name": "Google - Gemini Pro",
        "vendor_type": "native_langchain",
        "provider": "google",
        "api_endpoint": "",
        "model_name": "gemini-pro",
        "description": "Google Gemini Pro 模型"
    },
    "alibaba_qwen": {
        "name": "阿里云 - 通义千问",
        "vendor_type": "openai_compatible",
        "provider": "alibaba",
        "api_endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1/",
        "model_name": "qwen-turbo",
        "description": "阿里云通义千问模型"
    },
    "deepseek_chat": {
        "name": "深度求索 - DeepSeek Chat",
        "vendor_type": "openai_compatible",
        "provider": "deepseek",
        "api_endpoint": "https://api.deepseek.com/",
        "model_name": "deepseek-chat",
        "description": "深度求索 DeepSeek Chat 模型"
    },
    "moonshot_v1": {
        "name": "月之暗面 - Kimi",
        "vendor_type": "openai_compatible",
        "provider": "moonshot",
        "api_endpoint": "https://api.moonshot.cn/v1/",
        "model_name": "moonshot-v1-8k",
        "description": "月之暗面 Kimi 大模型"
    },
    "custom": {
        "name": "自定义配置",
        "vendor_type": "openai_compatible",
        "provider": "custom",
        "api_endpoint": "",
        "model_name": "",
        "description": "配置任意兼容 OpenAI API 的模型"
    }
}


def get_preset_configs() -> Dict:
    """获取所有预设配置"""
    return PRESET_CONFIGS


def get_preset_config(key: str) -> Optional[Dict]:
    """获取指定预设配置"""
    return PRESET_CONFIGS.get(key)


def create_llm_config_from_preset(preset_key: str, api_key: str) -> LLMConfig:
    """
    从预设创建 LLM 配置

    Args:
        preset_key: 预设配置键名
        api_key: API Key

    Returns:
        LLMConfig 对象
    """
    preset = get_preset_config(preset_key)
    if not preset:
        raise ValueError(f"未知的预设配置：{preset_key}")

    return LLMConfig(
        api_endpoint=preset['api_endpoint'],
        api_key=api_key,
        model_name=preset['model_name'],
        vendor_type=preset.get('vendor_type', 'openai_compatible'),
        provider=preset.get('provider', 'custom')
    )


# ==================== 验证与环境检测 ====================

def validate_llm_config(config: LLMConfig) -> tuple:
    """
    验证 LLM 配置

    Returns:
        (是否有效，错误信息)
    """
    if not config.api_key:
        return False, "API Key 不能为空"

    if not config.model_name:
        return False, "模型名称不能为空"

    # Google 不需要 API 端点，其他厂商需要
    if not (config.vendor_type == "native_langchain" and config.provider == "google") and not config.api_endpoint:
        return False, "API 端点不能为空"

    # 验证端点 URL 格式
    if config.api_endpoint and not config.api_endpoint.startswith(('http://', 'https://')):
        return False, "API 端点必须以 http://或 https://开头"

    return True, ""


def get_api_key_from_env(provider: str) -> Optional[str]:
    """
    从环境变量获取 API Key（合并两个注册表）

    Args:
        provider: 提供商名称

    Returns:
        API Key 或 None
    """
    # 先查路径 A
    info_a = OPENAI_COMPATIBLE_VENDORS.get(provider)
    if info_a:
        for key in info_a.get("env_keys", []):
            value = os.environ.get(key)
            if value:
                return value

    # 再查路径 B
    info_b = NATIVE_LANGCHAIN_VENDORS.get(provider)
    if info_b:
        for key in info_b.get("env_keys", []):
            value = os.environ.get(key)
            if value:
                return value

    return None


def get_required_package(vendor_type: str, provider: str) -> str:
    """
    获取指定厂商所需的 LangChain 包名

    Args:
        vendor_type: "openai_compatible" 或 "native_langchain"
        provider: 厂商标识

    Returns:
        pip install 命令所需的包名
    """
    if vendor_type == "openai_compatible":
        return "langchain-openai"
    else:
        # 路径 B：根据 provider 返回对应原生包
        package_map = {
            "openai": "langchain-openai",
            "anthropic": "langchain-anthropic",
            "google": "langchain-google-genai",
        }
        return package_map.get(provider, "langchain-openai")


def get_package_install_hint(vendor_type: str, provider: str) -> str:
    """
    获取安装指定厂商所需包的命令提示
    """
    package = get_required_package(vendor_type, provider)
    return f"pip install {package}"


# ==================== 模型创建（双路由核心） ====================

def create_chat_model(config: LLMConfig, http_client=None):
    """
    根据配置动态创建 LangChain Chat 模型（双路由）

    路径 A（OpenAI 兼容）：使用 ChatOpenAI + base_url
    路径 B（原生 LangChain）：使用 init_chat_model 自动路由

    Args:
        config: LLM 配置
        http_client: 可选的复用 httpx.Client（路径 A）。批量抽取时由外层
            创建一次并传入，避免每个分块都新建一个连接池导致文件描述符泄漏。
            为 None 时按原行为自建（适用于单次调用/连接测试）。

    Returns:
        LangChain Chat 模型实例

    Raises:
        ImportError: 当缺少必要的 langchain 包时
        ValueError: 当配置无效时
    """
    if config.vendor_type == "openai_compatible":
        # ===== 路径 A：OpenAI 兼容接口 =====
        logger.info(f"Using OpenAI-Compatible route for {config.provider} - {config.model_name}")
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError("缺少必要的包：langchain-openai\n请安装：pip install langchain-openai")

        kwargs = {
            "model": config.model_name,
            "api_key": config.api_key,
            "base_url": config.api_endpoint,
            "temperature": config.temperature,
            "timeout": config.timeout,
        }
        if config.max_tokens:
            kwargs["max_tokens"] = config.max_tokens
        if config.organization:
            kwargs["organization"] = config.organization
        kwargs.update(config.extra_params)

        # 修复 httpx + h2(HTTP/2) 导致部分国内厂商 SSL 连接失败的问题
        # 当 h2 包已安装时，httpx 默认尝试 HTTP/2 协商，部分厂商 SSL 不兼容
        # 解决方案：注入自定义 httpx.Client，强制使用 HTTP/1.1
        if http_client is not None:
            kwargs["http_client"] = http_client
            logger.debug("Reusing provided httpx client (HTTP/1.1 only)")
        else:
            try:
                import httpx
                kwargs["http_client"] = httpx.Client(
                    transport=httpx.HTTPTransport(),
                    timeout=httpx.Timeout(config.timeout, connect=10.0),
                )
                logger.debug("Injected custom httpx client (HTTP/1.1 only) for compatibility")
            except ImportError:
                # httpx 不可用时走默认行为
                pass

        return ChatOpenAI(**kwargs)

    else:
        # ===== 路径 B：原生 LangChain 包 =====
        vendor_info = NATIVE_LANGCHAIN_VENDORS.get(config.provider, {})
        model_provider = vendor_info.get("model_provider", config.provider)
        logger.info(f"Using Native LangChain route for {config.provider} - {config.model_name} (provider={model_provider})")

        try:
            from langchain.chat_models import init_chat_model
        except ImportError:
            raise ImportError(
                "缺少必要的包：langchain-core >= 0.2.0\n"
                "请安装：pip install langchain-core>=0.2.0"
            )

        kwargs = {
            "model": config.model_name,
            "model_provider": model_provider,
            "api_key": config.api_key,
            "temperature": config.temperature,
        }
        if config.max_tokens:
            kwargs["max_tokens"] = config.max_tokens
        if config.api_endpoint:
            kwargs["base_url"] = config.api_endpoint
        if config.organization:
            kwargs["organization"] = config.organization
        kwargs.update(config.extra_params)

        return init_chat_model(**kwargs)


# ==================== 连接测试 ====================

def test_llm_connection(config: LLMConfig) -> tuple:
    """
    测试 LLM 连接

    Args:
        config: LLM 配置

    Returns:
        (是否成功，错误信息)
    """
    try:
        llm = create_chat_model(config)

        # 简单的测试调用
        response = llm.invoke("Hello")

        # 获取模型名称
        model_name = config.model_name
        if hasattr(response, 'response_metadata'):
            model_name = response.response_metadata.get('model_name', model_name)

        return True, f"连接成功 ({model_name})"

    except ImportError as e:
        return False, f"缺少必要的包：{e}"
    except Exception as e:
        return False, str(e)
