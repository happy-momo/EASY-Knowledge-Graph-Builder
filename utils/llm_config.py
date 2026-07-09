"""
标准化 LLM 配置模块

兼容任意厂商的通用 API 配置方式。
用户只需输入：API 端点、API Key、模型名称
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from enum import Enum


class LLMProvider(Enum):
    """LLM 提供商枚举"""
    ZHIPU = "zhipu"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    ALIBABA = "alibaba"
    META = "meta"
    DEEPSEEK = "deepseek"
    MOONSHOT = "moonshot"
    CUSTOM = "custom"


# 各提供商的默认 API 配置
PROVIDER_DEFAULTS = {
    "zhipu": {
        "api_endpoint": "https://open.bigmodel.cn/api/paas/v4/",
        "chat_class": "ChatOpenAI",  # 使用 OpenAI 兼容接口
        "chat_module": "langchain_openai",
    },
    "openai": {
        "api_endpoint": "https://api.openai.com/v1/",
        "chat_class": "ChatOpenAI",
        "chat_module": "langchain_openai",
    },
    "anthropic": {
        "api_endpoint": "https://api.anthropic.com/",
        "chat_class": "ChatAnthropic",
        "chat_module": "langchain_anthropic",
    },
    "google": {
        "api_endpoint": "",  # Google 使用单独的 SDK，不需要 API 端点
        "chat_class": "ChatGoogleGenerativeAI",
        "chat_module": "langchain_google_genai",
    },
    "alibaba": {
        "api_endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1/",
        "chat_class": "ChatOpenAI",  # 使用 OpenAI 兼容接口
        "chat_module": "langchain_openai",
    },
    "meta": {
        "api_endpoint": "https://api.llama.com/",
        "chat_class": "ChatOpenAI",  # 使用 OpenAI 兼容接口
        "chat_module": "langchain_openai",
    },
    "deepseek": {
        "api_endpoint": "https://api.deepseek.com/",
        "chat_class": "ChatOpenAI",  # 使用 OpenAI 兼容接口
        "chat_module": "langchain_openai",
    },
    "moonshot": {
        "api_endpoint": "https://api.moonshot.cn/v1/",
        "chat_class": "ChatOpenAI",  # 使用 OpenAI 兼容接口
        "chat_module": "langchain_openai",
    },
    "custom": {
        "api_endpoint": "",
        "chat_class": "ChatOpenAI",  # 默认使用 OpenAI 兼容接口
        "chat_module": "langchain_openai",
    },
}


@dataclass
class LLMConfig:
    """标准化 LLM 配置"""
    # 必填
    api_endpoint: str       # API 端点 URL（Google 等特殊厂商可留空）
    api_key: str            # API Key
    model_name: str         # 模型名称

    # 可选
    provider: str = "custom"  # 提供商标识
    temperature: float = 0.1
    max_tokens: int = 2048
    timeout: int = 60

    # 高级配置
    api_version: str = ""     # API 版本（如需要）
    organization: str = ""    # 组织 ID（如需要）

    # 额外参数（传递给特定厂商的 SDK）
    extra_params: Dict = field(default_factory=dict)

    def __post_init__(self):
        """验证配置"""
        if not self.api_key:
            raise ValueError("API Key 不能为空")
        if not self.model_name:
            raise ValueError("模型名称不能为空")

        # Google 不需要 API 端点，其他厂商需要
        if self.provider != "google" and not self.api_endpoint:
            raise ValueError("API 端点不能为空")

        # 自动补全协议
        if self.api_endpoint and not self.api_endpoint.startswith(('http://', 'https://')):
            self.api_endpoint = 'https://' + self.api_endpoint

        # 自动设置 provider 的默认值
        if self.provider == "custom" and self.api_endpoint:
            # 根据端点自动推断 provider
            if "bigmodel.cn" in self.api_endpoint:
                self.provider = "zhipu"
            elif "openai.com" in self.api_endpoint:
                self.provider = "openai"
            elif "anthropic.com" in self.api_endpoint:
                self.provider = "anthropic"
            elif "dashscope" in self.api_endpoint:
                self.provider = "alibaba"
            elif "deepseek.com" in self.api_endpoint:
                self.provider = "deepseek"
            elif "moonshot.cn" in self.api_endpoint:
                self.provider = "moonshot"

    def get_chat_config(self) -> Dict:
        """
        获取初始化 LangChain Chat 模型所需的配置

        Returns:
            包含 chat_module、chat_class 和初始化参数的字典
        """
        provider_defaults = PROVIDER_DEFAULTS.get(self.provider, PROVIDER_DEFAULTS["custom"])

        # 基础配置
        config = {
            "chat_module": provider_defaults["chat_module"],
            "chat_class": provider_defaults["chat_class"],
            "model": self.model_name,
            "temperature": self.temperature,
        }

        # 根据不同厂商添加特定参数
        if self.provider == "anthropic":
            config["anthropic_api_key"] = self.api_key
            config["anthropic_api_url"] = self.api_endpoint if self.api_endpoint else None
            if self.max_tokens:
                config["max_tokens"] = self.max_tokens
        elif self.provider == "google":
            config["google_api_key"] = self.api_key
            if self.max_tokens:
                config["max_output_tokens"] = self.max_tokens
        else:
            # OpenAI 兼容接口（包括智谱、阿里云、DeepSeek 等）
            config["api_key"] = self.api_key
            config["base_url"] = self.api_endpoint
            if self.max_tokens:
                config["max_tokens"] = self.max_tokens

        # 添加额外参数
        config.update(self.extra_params)

        return config

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'api_endpoint': self.api_endpoint,
            'api_key': self.api_key,
            'model_name': self.model_name,
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
        """从字典创建"""
        return cls(
            api_endpoint=data.get('api_endpoint', ''),
            api_key=data.get('api_key', ''),
            model_name=data.get('model_name', ''),
            provider=data.get('provider', 'custom'),
            temperature=data.get('temperature', 0.1),
            max_tokens=data.get('max_tokens', 2048),
            timeout=data.get('timeout', 60),
            api_version=data.get('api_version', ''),
            organization=data.get('organization', ''),
            extra_params=data.get('extra_params', {})
        )


# 预设配置模板（方便用户快速选择）
PRESET_CONFIGS = {
    "zhipu_glm4": {
        "name": "智谱 AI - GLM-4",
        "provider": "zhipu",
        "api_endpoint": "https://open.bigmodel.cn/api/paas/v4/",
        "model_name": "glm-4",
        "description": "智谱 AI 的 GLM-4 模型，适合中文场景"
    },
    "zhipu_glm4_flash": {
        "name": "智谱 AI - GLM-4-Flash",
        "provider": "zhipu",
        "api_endpoint": "https://open.bigmodel.cn/api/paas/v4/",
        "model_name": "glm-4-flash",
        "description": "智谱 AI 的 GLM-4-Flash 模型，速度快"
    },
    "openai_gpt4": {
        "name": "OpenAI - GPT-4",
        "provider": "openai",
        "api_endpoint": "https://api.openai.com/v1/",
        "model_name": "gpt-4",
        "description": "OpenAI GPT-4 模型"
    },
    "openai_gpt35": {
        "name": "OpenAI - GPT-3.5-Turbo",
        "provider": "openai",
        "api_endpoint": "https://api.openai.com/v1/",
        "model_name": "gpt-3.5-turbo",
        "description": "OpenAI GPT-3.5-Turbo 模型"
    },
    "openai_gpt4o": {
        "name": "OpenAI - GPT-4o",
        "provider": "openai",
        "api_endpoint": "https://api.openai.com/v1/",
        "model_name": "gpt-4o",
        "description": "OpenAI GPT-4o 模型，多模态能力"
    },
    "anthropic_claude3": {
        "name": "Anthropic - Claude 3",
        "provider": "anthropic",
        "api_endpoint": "https://api.anthropic.com/",
        "model_name": "claude-3-opus-20240229",
        "description": "Anthropic Claude 3 Opus 模型"
    },
    "anthropic_claude3_sonnet": {
        "name": "Anthropic - Claude 3 Sonnet",
        "provider": "anthropic",
        "api_endpoint": "https://api.anthropic.com/",
        "model_name": "claude-3-sonnet-20240229",
        "description": "Anthropic Claude 3 Sonnet 模型"
    },
    "google_gemini": {
        "name": "Google - Gemini Pro",
        "provider": "google",
        "api_endpoint": "",
        "model_name": "gemini-pro",
        "description": "Google Gemini Pro 模型"
    },
    "alibaba_qwen": {
        "name": "阿里云 - 通义千问",
        "provider": "alibaba",
        "api_endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1/",
        "model_name": "qwen-turbo",
        "description": "阿里云通义千问模型"
    },
    "deepseek_chat": {
        "name": "深度求索 - DeepSeek Chat",
        "provider": "deepseek",
        "api_endpoint": "https://api.deepseek.com/",
        "model_name": "deepseek-chat",
        "description": "深度求索 DeepSeek Chat 模型"
    },
    "moonshot_v1": {
        "name": "月之暗面 - Kimi",
        "provider": "moonshot",
        "api_endpoint": "https://api.moonshot.cn/v1/",
        "model_name": "moonshot-v1-8k",
        "description": "月之暗面 Kimi 大模型"
    },
    "custom": {
        "name": "自定义配置",
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
        provider=preset['provider']
    )


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
    if config.provider != "google" and not config.api_endpoint:
        return False, "API 端点不能为空"

    # 验证端点 URL 格式
    if config.api_endpoint and not config.api_endpoint.startswith(('http://', 'https://')):
        return False, "API 端点必须以 http://或 https://开头"

    return True, ""


def get_api_key_from_env(provider: str) -> Optional[str]:
    """
    从环境变量获取 API Key

    Args:
        provider: 提供商名称

    Returns:
        API Key 或 None
    """
    env_mapping = {
        "zhipu": ["ZHIPU_API_KEY", "GLM_API_KEY"],
        "openai": ["OPENAI_API_KEY"],
        "anthropic": ["ANTHROPIC_API_KEY"],
        "google": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "alibaba": ["DASHSCOPE_API_KEY", "ALIBABA_API_KEY", "QWEN_API_KEY"],
        "meta": ["META_API_KEY", "LLAMA_API_KEY"],
        "deepseek": ["DEEPSEEK_API_KEY"],
        "moonshot": ["MOONSHOT_API_KEY", "KIMI_API_KEY"],
    }

    env_keys = env_mapping.get(provider, [])
    for key in env_keys:
        value = os.environ.get(key)
        if value:
            return value

    return None


def get_required_package(provider: str) -> str:
    """
    获取指定提供商所需的 LangChain 包名

    Args:
        provider: 提供商名称

    Returns:
        pip install 命令所需的包名
    """
    provider_defaults = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["custom"])
    return provider_defaults.get("chat_module", "langchain_openai")


def get_package_install_hint(provider: str) -> str:
    """
    获取安装指定提供商所需包的命令提示

    Args:
        provider: 提供商名称

    Returns:
        安装命令字符串
    """
    package = get_required_package(provider)
    return f"pip install {package}"


def create_chat_model(config: LLMConfig):
    """
    根据配置动态创建 LangChain Chat 模型

    Args:
        config: LLM 配置

    Returns:
        LangChain Chat 模型实例

    Raises:
        ImportError: 当缺少必要的 langchain 包时
        ValueError: 当配置无效时
    """
    chat_config = config.get_chat_config()
    chat_module = chat_config.pop("chat_module")
    chat_class_name = chat_config.pop("chat_class")

    try:
        if chat_module == "langchain_openai":
            from langchain_openai import ChatOpenAI
            # 添加 timeout 参数
            chat_config["timeout"] = config.timeout
            return ChatOpenAI(**chat_config)

        elif chat_module == "langchain_anthropic":
            from langchain_anthropic import ChatAnthropic
            # 添加 timeout 参数
            chat_config["timeout"] = config.timeout
            return ChatAnthropic(**chat_config)

        elif chat_module == "langchain_google_genai":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(**chat_config)

        else:
            # 默认使用 OpenAI 兼容接口
            from langchain_openai import ChatOpenAI
            chat_config["timeout"] = config.timeout
            return ChatOpenAI(**chat_config)

    except ImportError as e:
        raise ImportError(f"缺少必要的 LangChain 包：{e}\n请安装：pip install {chat_module}")


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
