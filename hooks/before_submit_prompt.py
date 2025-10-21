#!/usr/bin/env python3
"""
Cursor beforeSubmitPrompt hook for Prompt Paladin.

Intercepts prompts before submission, evaluates them using MCP pp-guard tool,
and blocks or allows submission based on quality assessment.
"""
import json
import logging
import os
import signal
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for importing mcp_server modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================
# Logging Setup
# ============================================

# Setup logger that writes to hooks/hook.log
LOG_FILE = Path(__file__).parent / "hook.log"

# Create logger
logger = logging.getLogger("prompt_paladin_hook")
logger.setLevel(logging.DEBUG)

# File handler with rotation (keep last 1MB)
try:
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1024*1024,  # 1MB
        backupCount=3
    )
except Exception:
    # Fallback to basic FileHandler if RotatingFileHandler fails
    file_handler = logging.FileHandler(LOG_FILE)

file_handler.setLevel(logging.DEBUG)

# Formatter with timestamp
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Also log to stderr for debugging (but not to stdout - that's for JSON!)
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.WARNING)  # Only warnings/errors to stderr
stderr_handler.setFormatter(formatter)
logger.addHandler(stderr_handler)

logger.info("=" * 60)
logger.info("Hook starting")


# ============================================
# Helper Functions
# ============================================

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

# ============================================
# Configuration (User-Configurable via .env)
# ============================================

# Load environment variables from .env file
# Future: These could be read from a config API or UI toggles
def load_hook_config():
    """Load configuration from .env file."""
    logger.debug("Loading configuration...")
    
    # Find .env in project root (one level up from hooks/)
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    if env_file.exists():
        logger.debug(f"Loading .env from {env_file}")
        from dotenv import load_dotenv
        load_dotenv(env_file)
    else:
        logger.warning(f".env file not found at {env_file}, using defaults")
    
    config = {
        # When True, automatically heal prompts with verdict="heal"
        # When False, block and show suggestions instead
        "auto_cast_heal": os.getenv("AUTO_CAST_HEAL", "true").lower() == "true",
        
        # When True, pp-heal uses anger translation for negative prompts
        # When False, only uses clarity improvements
        "anger_translator": os.getenv("ANGER_TRANSLATOR", "true").lower() == "true",
        
        # Hard timeout for hook execution (seconds)
        "timeout_secs": float(os.getenv("HOOK_TIMEOUT_SECS", "30.0")),
    }
    
    logger.info(f"Config loaded: auto_cast_heal={config['auto_cast_heal']}, "
                f"anger_translator={config['anger_translator']}, "
                f"timeout={config['timeout_secs']}s")
    
    return config

# Load config once at module level
try:
    CONFIG = load_hook_config()
except Exception as e:
    # Fallback to safe defaults if config loading fails
    logger.error(f"Config load failed: {e}, using defaults")
    CONFIG = {
        "auto_cast_heal": True,
        "anger_translator": True,
        "timeout_secs": 1.8,
    }

# ============================================
# Timeout Handler
# ============================================

class Timeout(Exception):
    """Raised when hook execution exceeds timeout."""
    pass


def _raise_timeout(signum, frame):
    """Signal handler that raises Timeout exception."""
    raise Timeout()


# ============================================
# MCP Tool Calling (Direct Import)
# ============================================

def call_mcp_guard(prompt: str, timeout: float = 25.0) -> dict:
    """
    Call pp-guard tool directly.
    
    Args:
        prompt: User prompt to evaluate
        timeout: Timeout in seconds (unused in direct call, kept for compatibility)
        
    Returns:
        Guard result dict with verdict, reason, confidence, etc.
        On error: Returns {"verdict": "proceed"} to fail open
    """
    start_time = datetime.now()
    logger.debug(f"Calling pp-guard directly (timeout={timeout}s)")
    logger.info(f"Prompt [500 chars]: {truncate_prompt(prompt, 500)}")
    
    try:
        # Import here to avoid issues if imports fail
        from mcp_server.tools import pp_guard
        
        # Call pp_guard directly
        response = pp_guard(prompt=prompt)
        
        # Calculate timing
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Log results
        verdict = response.get('verdict', 'unknown')
        confidence = response.get('confidence', 0.0)
        reason = response.get('reason', 'No reason provided')
        issues = response.get('issues', [])
        suggestions = response.get('suggestions', '')
        
        logger.info(f"pp-guard completed in {elapsed:.3f}s")
        logger.info(f"VERDICT: {verdict} | confidence: {confidence:.2f} | reason: {reason}")
        if issues:
            logger.info(f"Issues: {', '.join(issues)}")
        if suggestions:
            logger.debug(f"Suggestions: {suggestions}")
        
        return response
            
    except Exception as e:
        # Guard failed - fail open
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"pp-guard error after {elapsed:.3f}s: {e}", exc_info=True)
        return {
            "verdict": "proceed",
            "reason": f"Guard error: {str(e)}",
            "confidence": 0.0
        }


def call_mcp_heal(prompt: str, mode: str = "auto", timeout: float = 25.0) -> dict:
    """
    Call pp-heal tool directly.
    
    Args:
        prompt: User prompt to heal
        mode: Healing mode ("clarity", "anger", "auto")
        timeout: Timeout in seconds (unused in direct call, kept for compatibility)
        
    Returns:
        Heal result dict with healed_prompt, changes_made, etc.
        On error: Returns {"healed_prompt": original} to fail open
    """
    start_time = datetime.now()
    logger.debug(f"Calling pp-heal directly with mode={mode} (timeout={timeout}s)")
    logger.info(f"Original prompt [500 chars]: {truncate_prompt(prompt, 500)}")
    
    try:
        # Import here to avoid issues if imports fail
        from mcp_server.tools import pp_heal
        
        # Call pp_heal directly
        response = pp_heal(prompt=prompt, mode=mode)
        
        # Calculate timing
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Log results
        healed_prompt = response.get('healed_prompt', prompt)
        changes_made = response.get('changes_made', [])
        
        logger.info(f"pp-heal completed in {elapsed:.3f}s")
        logger.info(f"Healed prompt [500 chars]: {truncate_prompt(healed_prompt, 500)}")
        logger.info(f"Changes made ({len(changes_made)}): {', '.join(changes_made) if changes_made else 'none'}")
        
        return response
            
    except Exception as e:
        # Heal failed - return original
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"pp-heal error after {elapsed:.3f}s: {e}", exc_info=True)
        return {
            "healed_prompt": prompt,
            "changes_made": [],
            "error": str(e)
        }


# ============================================
# Hook Processing Logic
# ============================================

def process_hook(event: dict, config: dict) -> dict:
    """
    Process Cursor hook event and return response.
    
    Args:
        event: Hook input from stdin {"prompt": "...", "attachments": [...]}
        config: Hook configuration dict
        
    Returns:
        Hook response {"continue": true/false, "prompt"?: "...", "userMessage"?: "..."}
    """
    prompt = event.get("prompt", "").strip()
    logger.info(f"Processing prompt (length: {len(prompt)})")
    logger.info(f"Prompt [500 chars]: {truncate_prompt(prompt, 500)}")
    
    # Handle empty prompts
    if not prompt:
        logger.info("❌ BLOCKED - Empty prompt detected")
        return {
            "continue": False,
            "userMessage": "⚠️ Empty prompt - please provide instructions"
        }
    
    # Call pp-guard to evaluate prompt quality
    guard_result = call_mcp_guard(prompt, timeout=25.0)
    verdict = guard_result.get("verdict", "proceed")
    reason = guard_result.get("reason", "No reason provided")
    confidence = guard_result.get("confidence", 0.0)
    issues = guard_result.get("issues", [])
    
    # Process verdict
    if verdict == "proceed":
        # ✅ Good prompt - allow through
        logger.info("=" * 60)
        logger.info(f"✅ ALLOWED - Verdict: PROCEED")
        logger.info(f"   Reason: {reason}")
        logger.info(f"   Confidence: {confidence:.2f}")
        logger.info("=" * 60)
        return {
            "continue": True,
            "prompt": prompt
        }
    
    elif verdict == "intervene":
        # ❌ Bad prompt - prepend feedback so user can choose
        logger.info("=" * 60)
        logger.info(f"⚠️ FEEDBACK PREPENDED - Verdict: INTERVENE")
        logger.info(f"   Reason: {reason}")
        logger.info(f"   Confidence: {confidence:.2f}")
        if issues:
            logger.info(f"   Issues: {', '.join(issues)}")
        logger.info("=" * 60)
        
        # Get suggestions from guard result
        suggestions = guard_result.get('suggestions', '')
        
        # Format feedback to prepend
        feedback = f"""[PROMPT QUALITY CHECK]
🛑 {reason}

💡 Suggestions:
{suggestions if suggestions else 'Consider adding more context and specifics.'}

---
Original prompt:
"""
        
        # Prepend feedback and allow through (user can choose to revise or proceed)
        return {
            "continue": True,
            "prompt": feedback + prompt
        }
    
    elif verdict == "heal":
        # 🩹 Healable prompt - auto-heal if enabled
        if config["auto_cast_heal"]:
            logger.info("=" * 60)
            logger.info(f"🩹 HEALING - Verdict: HEAL (auto_cast_heal=true)")
            logger.info(f"   Reason: {reason}")
            logger.info(f"   Confidence: {confidence:.2f}")
            if issues:
                logger.info(f"   Issues: {', '.join(issues)}")
            logger.info("=" * 60)
            
            # Auto-heal and allow through
            heal_mode = "auto"  # Will use anger_translator config internally
            heal_result = call_mcp_heal(prompt, mode=heal_mode, timeout=25.0)
            healed_prompt = heal_result.get("healed_prompt", prompt)
            
            logger.info("=" * 60)
            logger.info("✅ ALLOWED - Healed prompt submitted")
            logger.info("=" * 60)
            return {
                "continue": True,
                "prompt": healed_prompt,
                "userMessage": "🩹 Prompt auto-healed for clarity"
            }
        else:
            logger.info("=" * 60)
            logger.info(f"⚠️ FEEDBACK PREPENDED - Verdict: HEAL (auto_cast_heal=false)")
            logger.info(f"   Reason: {reason}")
            logger.info(f"   Confidence: {confidence:.2f}")
            if issues:
                logger.info(f"   Issues: {', '.join(issues)}")
            logger.info("   Note: Auto-healing is disabled, showing suggestions instead")
            logger.info("=" * 60)
            
            # Get suggestions from guard result
            suggestions = guard_result.get('suggestions', '')
            
            # Format feedback to prepend
            feedback = f"""[PROMPT QUALITY CHECK]
💡 {reason}

Suggestions:
{suggestions if suggestions else 'Consider adding more context and specifics.'}

Tip: Enable AUTO_CAST_HEAL in .env for automatic fixes.

---
Original prompt:
"""
            
            # Prepend feedback and allow through (user can choose to revise or proceed)
            return {
                "continue": True,
                "prompt": feedback + prompt
            }
    
    # Unknown verdict - fail open (allow)
    logger.warning("=" * 60)
    logger.warning(f"⚠️ ALLOWED - Unknown verdict: {verdict} (failing open)")
    logger.warning("=" * 60)
    return {
        "continue": True,
        "prompt": prompt
    }


# ============================================
# Main Entry Point
# ============================================

def main():
    """
    Main hook entry point.
    
    Reads JSON from stdin, processes hook, writes JSON to stdout.
    Implements hard timeout and fail-open error handling.
    """
    start_time = datetime.now()
    
    # Install timeout signal handler
    signal.signal(signal.SIGALRM, _raise_timeout)
    signal.alarm(int(CONFIG["timeout_secs"]) + 1)  # Slightly longer than subprocess timeouts
    logger.debug(f"Timeout set to {CONFIG['timeout_secs']}s")
    
    try:
        # Read stdin
        logger.debug("Reading stdin...")
        raw_input = sys.stdin.read()
        logger.debug(f"Received {len(raw_input)} bytes")
        
        # Parse JSON (handle empty/malformed input)
        try:
            event = json.loads(raw_input) if raw_input.strip() else {}
            logger.debug(f"Parsed JSON event: {list(event.keys())}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON input: {e}")
            logger.debug(f"Raw input: {raw_input[:200]}")
            event = {}
        
        # Process hook
        response = process_hook(event, CONFIG)
        
        # Calculate execution time
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Hook completed in {elapsed:.3f}s - continue={response.get('continue')}")
        
        # Write stdout (ONLY valid JSON, no extra output!)
        sys.stdout.write(json.dumps(response))
        sys.stdout.flush()
        
    except Timeout:
        # Hard timeout - fail open
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"HARD TIMEOUT after {elapsed:.3f}s - failing open")
        sys.stdout.write(json.dumps({"continue": True}))
        sys.stdout.flush()
        
    except Exception as e:
        # Any other error - fail open
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"UNHANDLED ERROR after {elapsed:.3f}s: {e}", exc_info=True)
        sys.stdout.write(json.dumps({"continue": True}))
        sys.stdout.flush()


if __name__ == "__main__":
    main()

