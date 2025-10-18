"""MCP tool implementations for Prompt Paladin."""
import json
from typing import Dict, Any, Optional

from .config import load_config, get_provider_for_tool
from .prompts import (
    PP_GUARD_SYSTEM,
    PP_SUGGESTIONS_SYSTEM,
    PP_HEAL_CLARITY_SYSTEM,
    PP_HEAL_ANGER_SYSTEM,
    PP_DISCUSS_SYSTEM,
    format_guard_prompt,
    format_suggestions_prompt,
    format_heal_prompt,
    format_discuss_prompt,
)


# ============================================
# pp-guard: Primary Gatekeeper
# ============================================

def pp_guard(prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Evaluate prompt quality and determine next action.
    
    Args:
        prompt: The user's prompt to evaluate
        context: Optional context (conversation_history, active_files, etc.)
        
    Returns:
        Dict with verdict, reason, confidence, issues, suggestions
    """
    try:
        config = load_config()
        provider = get_provider_for_tool("pp_guard", config)
        
        # Use paired template + system prompt
        user_prompt = format_guard_prompt(prompt, context or {})
        
        # Call LLM with paired prompts
        response = provider.complete(user_prompt, PP_GUARD_SYSTEM)
        result = json.loads(response["content"])
        
        # Ensure required fields exist
        result.setdefault("verdict", "intervene")
        result.setdefault("confidence", 0.5)
        result.setdefault("issues", [])
        result.setdefault("reason", "No reason provided")
        
        return result
        
    except Exception as e:
        # CRITICAL: Fail open - never block prompts due to evaluation errors
        return {
            "verdict": "proceed",
            "reason": f"Error during evaluation: {str(e)}",
            "confidence": 0.0,
            "issues": ["evaluation_error"],
            "error": str(e)
        }


# ============================================
# pp-suggestions: Alternative Generator
# ============================================

def pp_suggestions(prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate 2-3 improved prompt alternatives.
    
    Args:
        prompt: The original prompt to improve
        context: Optional context
        
    Returns:
        Dict with suggestions array
    """
    try:
        config = load_config()
        provider = get_provider_for_tool("pp_suggestions", config)
        
        # Use paired template + system prompt
        user_prompt = format_suggestions_prompt(prompt, context or {})
        
        # Call LLM with paired prompts
        response = provider.complete(user_prompt, PP_SUGGESTIONS_SYSTEM)
        result = json.loads(response["content"])
        
        # Ensure suggestions field exists
        result.setdefault("suggestions", [])
        
        return result
        
    except Exception as e:
        # Fallback: return original prompt as single suggestion
        return {
            "suggestions": [
                {
                    "prompt": prompt,
                    "improvements": "Error generating suggestions"
                }
            ],
            "error": str(e)
        }


# ============================================
# pp-heal: Prompt Healer
# ============================================

def pp_heal(
    prompt: str,
    mode: str = "auto",
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Automatically heal/improve a prompt.
    
    Args:
        prompt: The prompt to heal
        mode: Healing mode ("clarity", "anger", "auto")
        context: Optional context
        
    Returns:
        Dict with healed_prompt, changes_made, original_intent
    """
    try:
        config = load_config()
        provider = get_provider_for_tool("pp_heal", config)
        
        # Determine which system prompt to use
        if mode == "anger":
            system_prompt = PP_HEAL_ANGER_SYSTEM
        elif mode == "clarity":
            system_prompt = PP_HEAL_CLARITY_SYSTEM
        elif mode == "auto":
            # Check config and negative tone to decide
            if config.anger_translator and _has_negative_tone(prompt):
                system_prompt = PP_HEAL_ANGER_SYSTEM
            else:
                system_prompt = PP_HEAL_CLARITY_SYSTEM
        else:
            # Default to clarity for unknown modes
            system_prompt = PP_HEAL_CLARITY_SYSTEM
        
        # Use paired template + appropriate system prompt
        user_prompt = format_heal_prompt(prompt, context or {})
        
        # Call LLM with paired prompts
        response = provider.complete(user_prompt, system_prompt)
        result = json.loads(response["content"])
        
        # Ensure required fields exist
        result.setdefault("healed_prompt", prompt)
        result.setdefault("changes_made", [])
        
        return result
        
    except Exception as e:
        # Fallback: return original prompt unchanged
        return {
            "healed_prompt": prompt,
            "changes_made": [],
            "error": str(e)
        }


def _has_negative_tone(prompt: str) -> bool:
    """
    Quick heuristic check for negative language.
    
    Args:
        prompt: The prompt to check
        
    Returns:
        True if negative words detected, False otherwise
    """
    negative_words = [
        "stupid", "dumb", "idiotic", "garbage", "trash", "terrible",
        "horrible", "awful", "broken", "useless", "crap", "sucks",
        "hate", "ridiculous", "insane", "moronic"
    ]
    prompt_lower = prompt.lower()
    return any(word in prompt_lower for word in negative_words)


# ============================================
# pp-discuss: Clarifying Questions
# ============================================

def pp_discuss(prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate clarifying questions for unclear prompts.
    
    Args:
        prompt: The unclear prompt
        context: Optional context
        
    Returns:
        Dict with questions array and context
    """
    try:
        config = load_config()
        provider = get_provider_for_tool("pp_discuss", config)
        
        # Use paired template + system prompt
        user_prompt = format_discuss_prompt(prompt, context or {})
        
        # Call LLM with paired prompts
        response = provider.complete(user_prompt, PP_DISCUSS_SYSTEM)
        result = json.loads(response["content"])
        
        # Ensure required fields exist
        result.setdefault("questions", [])
        result.setdefault("context", "")
        
        return result
        
    except Exception as e:
        # Fallback: return generic clarifying questions
        return {
            "questions": [
                "What specific changes would you like to make?",
                "Which files or components need to be modified?",
                "What is the expected behavior or outcome?"
            ],
            "context": "Error generating questions - using fallback questions",
            "error": str(e)
        }


# ============================================
# pp-proceed: User Override
# ============================================

def pp_proceed(prompt: str) -> Dict[str, Any]:
    """
    User chose to proceed with original prompt.
    
    Args:
        prompt: The original prompt (unchanged)
        
    Returns:
        Dict acknowledging user override
    """
    return {
        "verdict": "proceed",
        "note": "User chose to proceed with original prompt",
        "prompt": prompt
    }

