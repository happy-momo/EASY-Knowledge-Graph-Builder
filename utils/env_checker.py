"""
环境检测工具

检测Neo4j连接状态和API Key配置。
"""

import os
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ConnectionStatus(Enum):
    """连接状态枚举"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class Neo4jStatus:
    """Neo4j连接状态"""
    status: ConnectionStatus
    message: str
    uri: str = ""
    version: str = ""


@dataclass
class APIKeyStatus:
    """API Key状态"""
    provider: str
    configured: bool
    key_prefix: str = ""  # 显示前几个字符
    source: str = ""  # env, file, manual


# API Key环境变量映射
API_KEY_ENV_MAPPING = {
    "zhipu": ["ZHIPU_API_KEY", "GLM_API_KEY"],
    "openai": ["OPENAI_API_KEY"],
    "anthropic": ["ANTHROPIC_API_KEY"],
    "google": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
    "alibaba": ["DASHSCOPE_API_KEY", "ALIBABA_API_KEY", "QWEN_API_KEY"],
    "meta": ["META_API_KEY", "LLAMA_API_KEY"]
}

# 默认Neo4j配置
DEFAULT_NEO4J_URI = "bolt://localhost:7687"
DEFAULT_NEO4J_USER = "neo4j"


def check_neo4j_connection(uri: str = DEFAULT_NEO4J_URI,
                           user: str = DEFAULT_NEO4J_USER,
                           password: str = "") -> Neo4jStatus:
    """
    检测Neo4j连接状态

    Args:
        uri: Neo4j URI
        user: 用户名
        password: 密码

    Returns:
        Neo4j连接状态对象
    """
    try:
        from neo4j import GraphDatabase

        if not password:
            return Neo4jStatus(
                status=ConnectionStatus.DISCONNECTED,
                message="未配置密码",
                uri=uri
            )

        driver = GraphDatabase.driver(uri, auth=(user, password))

        # 尝试连接
        with driver.session() as session:
            result = session.run("CALL db.info() RETURN version")
            record = result.single()
            version = record["version"] if record else "unknown"

        driver.close()

        return Neo4jStatus(
            status=ConnectionStatus.CONNECTED,
            message="连接成功",
            uri=uri,
            version=version
        )

    except ImportError:
        return Neo4jStatus(
            status=ConnectionStatus.ERROR,
            message="neo4j库未安装",
            uri=uri
        )
    except Exception as e:
        error_msg = str(e)

        # 解析常见错误
        if "ServiceUnavailable" in error_msg or "Connection refused" in error_msg:
            message = "无法连接到Neo4j服务，请确认Neo4j是否已启动"
        elif "AuthError" in error_msg or "authentication failed" in error_msg.lower():
            message = "认证失败，请检查用户名和密码"
        elif "Failed to resolve address" in error_msg:
            message = "无法解析地址，请检查URI是否正确"
        else:
            message = f"连接失败: {error_msg[:100]}"

        return Neo4jStatus(
            status=ConnectionStatus.DISCONNECTED,
            message=message,
            uri=uri
        )


def check_api_key(provider: str) -> APIKeyStatus:
    """
    检测API Key是否已配置

    Args:
        provider: 提供商名称 (zhipu, openai, anthropic, google, alibaba, meta)

    Returns:
        API Key状态对象
    """
    provider_lower = provider.lower()

    # 获取该提供商的环境变量名列表
    env_keys = API_KEY_ENV_MAPPING.get(provider_lower, [f"{provider.upper()}_API_KEY"])

    for env_key in env_keys:
        api_key = os.environ.get(env_key)
        if api_key:
            return APIKeyStatus(
                provider=provider,
                configured=True,
                key_prefix=api_key[:8] + "..." if len(api_key) > 8 else "***",
                source="env"
            )

    # 检查.env文件
    try:
        from dotenv import load_dotenv
        load_dotenv()

        for env_key in env_keys:
            api_key = os.environ.get(env_key)
            if api_key:
                return APIKeyStatus(
                    provider=provider,
                    configured=True,
                    key_prefix=api_key[:8] + "..." if len(api_key) > 8 else "***",
                    source="file"
                )
    except ImportError:
        pass

    return APIKeyStatus(
        provider=provider,
        configured=False,
        source=""
    )


def check_all_api_keys() -> Dict[str, APIKeyStatus]:
    """
    检测所有支持的提供商的API Key状态

    Returns:
        提供商 -> API Key状态的字典
    """
    providers = ["zhipu", "openai", "anthropic", "google", "alibaba", "meta"]
    return {provider: check_api_key(provider) for provider in providers}


def get_environment_status() -> Dict:
    """
    获取完整的环境状态

    Returns:
        环境状态字典
    """
    api_keys_status = check_all_api_keys()

    configured_providers = [
        provider for provider, status in api_keys_status.items()
        if status.configured
    ]

    return {
        "api_keys": {
            provider: {
                "configured": status.configured,
                "key_prefix": status.key_prefix,
                "source": status.source
            }
            for provider, status in api_keys_status.items()
        },
        "configured_providers": configured_providers,
        "has_any_api_key": len(configured_providers) > 0,
        "recommendations": get_recommendations(api_keys_status)
    }


def get_recommendations(api_keys_status: Dict[str, APIKeyStatus]) -> list:
    """
    根据API Key状态获取建议

    Args:
        api_keys_status: API Key状态字典

    Returns:
        建议列表
    """
    recommendations = []

    # 检查是否有配置的API Key
    configured = [p for p, s in api_keys_status.items() if s.configured]

    if not configured:
        recommendations.append({
            "type": "warning",
            "message": "未检测到已配置的API Key",
            "action": "请在环境变量中配置API Key或在应用中手动输入"
        })

    # 检查中国用户推荐
    if "zhipu" not in configured and "alibaba" not in configured:
        recommendations.append({
            "type": "info",
            "message": "推荐使用智谱AI或通义千问（国内访问更稳定）",
            "action": "设置 ZHIPU_API_KEY 或 DASHSCOPE_API_KEY 环境变量"
        })

    return recommendations


def format_status_message(status) -> str:
    """
    格式化状态消息

    Args:
        status: 状态对象

    Returns:
        格式化的消息字符串
    """
    if isinstance(status, Neo4jStatus):
        if status.status == ConnectionStatus.CONNECTED:
            return f"Neo4j 已连接 ({status.version})"
        elif status.status == ConnectionStatus.DISCONNECTED:
            return f"Neo4j 未连接 - {status.message}"
        else:
            return f"Neo4j 错误 - {status.message}"

    elif isinstance(status, APIKeyStatus):
        if status.configured:
            return f"{status.provider.upper()} API Key 已配置 ({status.key_prefix})"
        else:
            return f"{status.provider.upper()} API Key 未配置"

    return "未知状态"
