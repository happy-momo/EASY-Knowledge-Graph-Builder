"""
标准化LLM配置模块

兼容任意厂商的通用API配置方式。
用户只需输入：API端点、API Key、模型名称
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from enum import Enum


class LLMProvider(Enum):
    """LLM提供商枚举"""
    ZHIPU = "zhipu"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    ALIBABA = "alibaba"
    META = "meta"
    CUSTOM = "custom"


@dataclass
class LLMConfig:
    """标准化LLM配置"""
    # 必填
    api_endpoint: str       # API端点URL
    api_key: str            # API Key
    model_name: str         # 模型名称

    # 可选
    provider: str = "custom"  # 提供商标识
    temperature: float = 0.1
    max_tokens: int = 2048
    timeout: int = 60

    # 高级配置
    api_version: str = ""     # API版本（如需要）
    organization: str = ""    # 组织ID（如需要）

    def __post_init__(self):
        """验证配置"""
        if not self.api_endpoint:
            raise ValueError("API端点不能为空")
        if not self.api_key:
            raise ValueError("API Key不能为空")
        if not self.model_name:
            raise ValueError("模型名称不能为空")

        # 自动补全协议
        if self.api_endpoint and not self.api_endpoint.startswith(('http://', 'https://')):
            self.api_endpoint = 'https://' + self.api_endpoint

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
            'organization': self.organization
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
            organization=data.get('organization', '')
        )


# 预设配置模板（方便用户快速选择）
PRESET_CONFIGS = {
    "zhipu_glm4": {
        "name": "智谱AI - GLM-4",
        "provider": "zhipu",
        "api_endpoint": "https://open.bigmodel.cn/api/paas/v4/",
        "model_name": "glm-4",
        "description": "智谱AI的GLM-4模型，适合中文场景"
    },
    "zhipu_glm4_flash": {
        "name": "智谱AI - GLM-4-Flash",
        "provider": "zhipu",
        "api_endpoint": "https://open.bigmodel.cn/api/paas/v4/",
        "model_name": "glm-4-flash",
        "description": "智谱AI的GLM-4-Flash模型，速度快"
    },
    "openai_gpt4": {
        "name": "OpenAI - GPT-4",
        "provider": "openai",
        "api_endpoint": "https://api.openai.com/v1/",
        "model_name": "gpt-4",
        "description": "OpenAI GPT-4模型"
    },
    "openai_gpt35": {
        "name": "OpenAI - GPT-3.5-Turbo",
        "provider": "openai",
        "api_endpoint": "https://api.openai.com/v1/",
        "model_name": "gpt-3.5-turbo",
        "description": "OpenAI GPT-3.5-Turbo模型"
    },
    "anthropic_claude3": {
        "name": "Anthropic - Claude 3",
        "provider": "anthropic",
        "api_endpoint": "https://api.anthropic.com/v1/",
        "model_name": "claude-3-opus-20240229",
        "description": "Anthropic Claude 3 Opus模型"
    },
    "google_gemini": {
        "name": "Google - Gemini Pro",
        "provider": "google",
        "api_endpoint": "https://generativelanguage.googleapis.com/v1beta/",
        "model_name": "gemini-pro",
        "description": "Google Gemini Pro模型"
    },
    "alibaba_qwen": {
        "name": "阿里云 - 通义千问",
        "provider": "alibaba",
        "api_endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1/",
        "model_name": "qwen-turbo",
        "description": "阿里云通义千问模型"
    },
    "custom": {
        "name": "自定义配置",
        "provider": "custom",
        "api_endpoint": "",
        "model_name": "",
        "description": "配置任意兼容OpenAI API的模型"
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
    从预设创建LLM配置

    Args:
        preset_key: 预设配置键名
        api_key: API Key

    Returns:
        LLMConfig对象
    """
    preset = get_preset_config(preset_key)
    if not preset:
        raise ValueError(f"未知的预设配置: {preset_key}")

    return LLMConfig(
        api_endpoint=preset['api_endpoint'],
        api_key=api_key,
        model_name=preset['model_name'],
        provider=preset['provider']
    )


def validate_llm_config(config: LLMConfig) -> tuple:
    """
    验证LLM配置

    Returns:
        (是否有效, 错误信息)
    """
    if not config.api_endpoint:
        return False, "API端点不能为空"

    if not config.api_key:
        return False, "API Key不能为空"

    if not config.model_name:
        return False, "模型名称不能为空"

    # 验证端点URL格式
    if not config.api_endpoint.startswith(('http://', 'https://')):
        return False, "API端点必须以http://或https://开头"

    return True, ""


def get_api_key_from_env(provider: str) -> Optional[str]:
    """
    从环境变量获取API Key

    Args:
        provider: 提供商名称

    Returns:
        API Key或None
    """
    env_mapping = {
        "zhipu": ["ZHIPU_API_KEY", "GLM_API_KEY"],
        "openai": ["OPENAI_API_KEY"],
        "anthropic": ["ANTHROPIC_API_KEY"],
        "google": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "alibaba": ["DASHSCOPE_API_KEY", "ALIBABA_API_KEY"],
        "meta": ["META_API_KEY"]
    }

    env_keys = env_mapping.get(provider, [])
    for key in env_keys:
        value = os.environ.get(key)
        if value:
            return value

    return None


def test_llm_connection(config: LLMConfig) -> tuple:
    """
    测试LLM连接

    Args:
        config: LLM配置

    Returns:
        (是否成功, 错误信息)
    """
    try:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=config.model_name,
            openai_api_key=config.api_key,
            openai_api_base=config.api_endpoint,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout
        )

        # 简单的测试调用
        response = llm.invoke("Hello")

        return True, f"连接成功 ({response.response_metadata.get('model_name', config.model_name)})"

    except Exception as e:
        return False, str(e)