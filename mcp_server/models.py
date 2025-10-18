"""Model provider abstraction for different LLM APIs."""
from typing import Protocol, Dict, Any

from anthropic import Anthropic
from openai import OpenAI


class ModelProvider(Protocol):
    """Protocol defining the interface all model providers must implement."""
    
    def complete(self, prompt: str, system: str = "") -> Dict[str, Any]:
        """
        Generate a completion from the model.
        
        Args:
            prompt: The user prompt/question
            system: System message to set context
            
        Returns:
            Dict with 'content', 'model', and 'provider' keys
        """
        ...


class ClaudeProvider:
    """Anthropic Claude API provider."""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize Claude provider.
        
        Args:
            api_key: Anthropic API key
            model: Model identifier (default: claude-3-5-sonnet-20241022)
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
    
    def complete(self, prompt: str, system: str = "") -> Dict[str, Any]:
        """Generate completion using Claude."""
        messages = [{"role": "user", "content": prompt}]
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system if system else None,
            messages=messages
        )
        
        return {
            "content": response.content[0].text,
            "model": self.model,
            "provider": "anthropic"
        }


class OpenAIProvider:
    """OpenAI API provider."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model identifier (default: gpt-4o-mini)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def complete(self, prompt: str, system: str = "") -> Dict[str, Any]:
        """Generate completion using OpenAI."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=2048
        )
        
        return {
            "content": response.choices[0].message.content,
            "model": self.model,
            "provider": "openai"
        }


class GroqProvider:
    """Groq API provider (OpenAI-compatible)."""
    
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize Groq provider.
        
        Args:
            api_key: Groq API key
            model: Model identifier (default: llama-3.3-70b-versatile)
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = model
    
    def complete(self, prompt: str, system: str = "") -> Dict[str, Any]:
        """Generate completion using Groq."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=2048
        )
        
        return {
            "content": response.choices[0].message.content,
            "model": self.model,
            "provider": "groq"
        }


def get_provider(provider_name: str, api_key: str, model: str) -> ModelProvider:
    """
    Factory function to create a model provider instance.
    
    Args:
        provider_name: Name of provider ("anthropic", "openai", "groq")
        api_key: API key for the provider
        model: Model identifier
        
    Returns:
        Initialized provider instance
        
    Raises:
        ValueError: If provider_name is not supported
    """
    providers = {
        "anthropic": ClaudeProvider,
        "openai": OpenAIProvider,
        "groq": GroqProvider,
    }
    
    if provider_name not in providers:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Supported: {', '.join(providers.keys())}"
        )
    
    return providers[provider_name](api_key=api_key, model=model)




