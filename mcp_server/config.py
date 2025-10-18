"""Configuration system for Prompt Paladin MCP server."""
from dataclasses import dataclass, field
from typing import Dict, Optional
import os

from dotenv import load_dotenv

from .models import ModelProvider, get_provider


@dataclass
class ProviderConfig:
    """Configuration for a specific provider/model."""
    provider: str
    model: str
    api_key: str


@dataclass
class Config:
    """Application configuration loaded from environment."""
    
    # Feature toggles
    auto_cast_heal: bool = True
    anger_translator: bool = True
    
    # Default provider settings
    default_provider: str = "anthropic"
    default_model: str = "claude-3-5-sonnet-20241022"
    
    # API keys
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    
    # Per-tool overrides
    tool_configs: Dict[str, ProviderConfig] = field(default_factory=dict)
    
    # Server settings
    mcp_server_name: str = "prompt-paladin"
    log_level: str = "INFO"


def _get_api_key_for_provider(provider: str, config: Config) -> Optional[str]:
    """Helper to get API key for a given provider name."""
    key_map = {
        "anthropic": config.anthropic_api_key,
        "openai": config.openai_api_key,
        "groq": config.groq_api_key,
    }
    return key_map.get(provider)


def load_config() -> Config:
    """
    Load configuration from environment variables.
    
    Returns:
        Initialized Config object
        
    Raises:
        ValueError: If required configuration is missing
    """
    # Load .env file if present
    load_dotenv()
    
    config = Config()
    
    # Load feature toggles
    config.auto_cast_heal = os.getenv("AUTO_CAST_HEAL", "true").lower() == "true"
    config.anger_translator = os.getenv("ANGER_TRANSLATOR", "true").lower() == "true"
    
    # Load default settings
    config.default_provider = os.getenv("DEFAULT_PROVIDER", "anthropic")
    config.default_model = os.getenv(
        "DEFAULT_MODEL", 
        "claude-3-5-sonnet-20241022"
    )
    
    # Load API keys
    config.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    config.openai_api_key = os.getenv("OPENAI_API_KEY")
    config.groq_api_key = os.getenv("GROQ_API_KEY")
    
    # Load per-tool overrides
    tools = ["pp_guard", "pp_heal", "pp_suggestions", "pp_discuss"]
    for tool in tools:
        tool_upper = tool.upper()
        provider = os.getenv(f"{tool_upper}_PROVIDER", config.default_provider)
        model = os.getenv(f"{tool_upper}_MODEL", config.default_model)
        
        # Get API key for this provider
        api_key = _get_api_key_for_provider(provider, config)
        
        if api_key:
            config.tool_configs[tool] = ProviderConfig(
                provider=provider,
                model=model,
                api_key=api_key
            )
    
    # Validate at least one API key is set
    if not any([
        config.anthropic_api_key,
        config.openai_api_key,
        config.groq_api_key
    ]):
        raise ValueError(
            "At least one API key must be set: "
            "ANTHROPIC_API_KEY, OPENAI_API_KEY, or GROQ_API_KEY"
        )
    
    # Server settings
    config.mcp_server_name = os.getenv("MCP_SERVER_NAME", "prompt-paladin")
    config.log_level = os.getenv("LOG_LEVEL", "INFO")
    
    return config


def get_provider_for_tool(tool_name: str, config: Config) -> ModelProvider:
    """
    Get configured provider instance for a specific tool.
    
    Args:
        tool_name: Name of the tool (e.g., "pp_guard")
        config: Application configuration
        
    Returns:
        Initialized ModelProvider for the tool
    """
    # Check for tool-specific config
    if tool_name in config.tool_configs:
        tool_config = config.tool_configs[tool_name]
        return get_provider(
            tool_config.provider,
            tool_config.api_key,
            tool_config.model
        )
    
    # Fall back to default
    api_key = _get_api_key_for_provider(config.default_provider, config)
    if not api_key:
        raise ValueError(
            f"No API key configured for default provider: {config.default_provider}"
        )
    
    return get_provider(
        config.default_provider,
        api_key,
        config.default_model
    )


