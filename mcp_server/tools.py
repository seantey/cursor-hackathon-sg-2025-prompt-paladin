"""MCP tool implementations for Prompt Paladin."""
import json
import logging
from datetime import datetime
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

# Setup logger for MCP tools
logger = logging.getLogger("prompt_paladin.tools")


def truncate_prompt(text: str, max_len: int = 500) -> str:
    """
    Truncate prompt text for logging while preserving readability.
    
    Args:
        text: The prompt text to truncate
        max_len: Maximum length (default: 500 chars)
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def extract_json_from_response(content: str) -> str:
    """
    Extract JSON from LLM response, handling markdown code blocks.
    
    Some models wrap JSON in ```json ... ``` blocks. This function
    strips those if present, or returns the content as-is.
    
    Args:
        content: Raw LLM response content
        
    Returns:
        Clean JSON string
    """
    content = content.strip()
    
    # Check for markdown code blocks
    if content.startswith("```"):
        # Remove opening fence (```json or ```)
        lines = content.split('\n')
        # Remove first line (```json or ```)
        lines = lines[1:]
        # Remove last line if it's closing fence (```)
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = '\n'.join(lines).strip()
    
    return content


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
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("pp_guard: Starting prompt evaluation")
    logger.info(f"Prompt [500 chars]: {truncate_prompt(prompt, 500)}")
    
    try:
        config = load_config()
        provider = get_provider_for_tool("pp_guard", config)
        
        # Use paired template + system prompt
        user_prompt = format_guard_prompt(prompt, context or {})
        
        # Call LLM with paired prompts
        llm_start = datetime.now()
        response = provider.complete(user_prompt, PP_GUARD_SYSTEM)
        llm_elapsed = (datetime.now() - llm_start).total_seconds()
        logger.info(f"LLM call completed in {llm_elapsed:.3f}s")
        
        # Extract and parse JSON from response
        response_content = response.get("content", "")
        logger.debug(f"Response content length: {len(response_content)}")
        
        # Handle markdown code blocks (```json ... ```)
        clean_json = extract_json_from_response(response_content)
        logger.debug(f"Clean JSON length: {len(clean_json)}")
        
        # Parse JSON
        result = json.loads(clean_json)
        
        # Ensure required fields exist
        result.setdefault("verdict", "intervene")
        result.setdefault("confidence", 0.5)
        result.setdefault("issues", [])
        result.setdefault("reason", "No reason provided")
        
        # Log results
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"pp_guard completed in {elapsed:.3f}s")
        logger.info(f"Verdict: {result['verdict']} | Confidence: {result['confidence']:.2f}")
        logger.info(f"Reason: {result['reason']}")
        if result['issues']:
            logger.info(f"Issues: {', '.join(result['issues'])}")
        logger.info("=" * 60)
        
        return result
        
    except Exception as e:
        # CRITICAL: Fail open - never block prompts due to evaluation errors
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"pp_guard error after {elapsed:.3f}s: {e}", exc_info=True)
        logger.info("=" * 60)
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
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("pp_suggestions: Generating prompt alternatives")
    logger.info(f"Original prompt [500 chars]: {truncate_prompt(prompt, 500)}")
    
    try:
        config = load_config()
        provider = get_provider_for_tool("pp_suggestions", config)
        
        # Use paired template + system prompt
        user_prompt = format_suggestions_prompt(prompt, context or {})
        
        # Call LLM with paired prompts
        llm_start = datetime.now()
        response = provider.complete(user_prompt, PP_SUGGESTIONS_SYSTEM)
        llm_elapsed = (datetime.now() - llm_start).total_seconds()
        logger.info(f"LLM call completed in {llm_elapsed:.3f}s")
        
        # Extract and parse JSON (handle markdown code blocks)
        clean_json = extract_json_from_response(response["content"])
        result = json.loads(clean_json)
        
        # Ensure suggestions field exists
        result.setdefault("suggestions", [])
        
        # Log results
        elapsed = (datetime.now() - start_time).total_seconds()
        suggestions = result['suggestions']
        logger.info(f"pp_suggestions completed in {elapsed:.3f}s")
        logger.info(f"Generated {len(suggestions)} suggestion(s)")
        for i, suggestion in enumerate(suggestions, 1):
            logger.info(f"Suggestion {i}: {truncate_prompt(suggestion.get('prompt', ''), 200)}")
        logger.info("=" * 60)
        
        return result
        
    except Exception as e:
        # Fallback: return original prompt as single suggestion
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"pp_suggestions error after {elapsed:.3f}s: {e}", exc_info=True)
        logger.info("=" * 60)
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
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info(f"pp_heal: Starting prompt healing (mode={mode})")
    logger.info(f"Original prompt [500 chars]: {truncate_prompt(prompt, 500)}")
    
    try:
        config = load_config()
        provider = get_provider_for_tool("pp_heal", config)
        
        # Determine which system prompt to use
        if mode == "anger":
            system_prompt = PP_HEAL_ANGER_SYSTEM
            healing_type = "anger translation"
        elif mode == "clarity":
            system_prompt = PP_HEAL_CLARITY_SYSTEM
            healing_type = "clarity improvement"
        elif mode == "auto":
            # Check config and negative tone to decide
            if config.anger_translator and _has_negative_tone(prompt):
                system_prompt = PP_HEAL_ANGER_SYSTEM
                healing_type = "anger translation (auto)"
            else:
                system_prompt = PP_HEAL_CLARITY_SYSTEM
                healing_type = "clarity improvement (auto)"
        else:
            # Default to clarity for unknown modes
            system_prompt = PP_HEAL_CLARITY_SYSTEM
            healing_type = "clarity improvement (default)"
        
        logger.info(f"Healing type: {healing_type}")
        
        # Use paired template + appropriate system prompt
        user_prompt = format_heal_prompt(prompt, context or {})
        
        # Call LLM with paired prompts
        llm_start = datetime.now()
        response = provider.complete(user_prompt, system_prompt)
        llm_elapsed = (datetime.now() - llm_start).total_seconds()
        logger.info(f"LLM call completed in {llm_elapsed:.3f}s")
        
        # Extract and parse JSON (handle markdown code blocks)
        clean_json = extract_json_from_response(response["content"])
        result = json.loads(clean_json)
        
        # Ensure required fields exist
        result.setdefault("healed_prompt", prompt)
        result.setdefault("changes_made", [])
        
        # Log results
        elapsed = (datetime.now() - start_time).total_seconds()
        healed_prompt = result['healed_prompt']
        changes_made = result['changes_made']
        
        logger.info(f"pp_heal completed in {elapsed:.3f}s")
        logger.info(f"Healed prompt [500 chars]: {truncate_prompt(healed_prompt, 500)}")
        logger.info(f"Changes made ({len(changes_made)}): {', '.join(changes_made) if changes_made else 'none'}")
        logger.info("=" * 60)
        
        return result
        
    except Exception as e:
        # Fallback: return original prompt unchanged
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"pp_heal error after {elapsed:.3f}s: {e}", exc_info=True)
        logger.info("=" * 60)
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
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("pp_discuss: Generating clarifying questions")
    logger.info(f"Unclear prompt [500 chars]: {truncate_prompt(prompt, 500)}")
    
    try:
        config = load_config()
        provider = get_provider_for_tool("pp_discuss", config)
        
        # Use paired template + system prompt
        user_prompt = format_discuss_prompt(prompt, context or {})
        
        # Call LLM with paired prompts
        llm_start = datetime.now()
        response = provider.complete(user_prompt, PP_DISCUSS_SYSTEM)
        llm_elapsed = (datetime.now() - llm_start).total_seconds()
        logger.info(f"LLM call completed in {llm_elapsed:.3f}s")
        
        # Extract and parse JSON (handle markdown code blocks)
        clean_json = extract_json_from_response(response["content"])
        result = json.loads(clean_json)
        
        # Ensure required fields exist
        result.setdefault("questions", [])
        result.setdefault("context", "")
        
        # Log results
        elapsed = (datetime.now() - start_time).total_seconds()
        questions = result['questions']
        logger.info(f"pp_discuss completed in {elapsed:.3f}s")
        logger.info(f"Generated {len(questions)} question(s)")
        for i, question in enumerate(questions, 1):
            logger.info(f"Question {i}: {question}")
        logger.info("=" * 60)
        
        return result
        
    except Exception as e:
        # Fallback: return generic clarifying questions
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"pp_discuss error after {elapsed:.3f}s: {e}", exc_info=True)
        logger.info("=" * 60)
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

