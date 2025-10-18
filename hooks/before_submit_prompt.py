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
import subprocess
import sys
from datetime import datetime
from pathlib import Path

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
# MCP Tool Calling via Subprocess
# ============================================

def call_mcp_guard(prompt: str, timeout: float = 25.0) -> dict:
    """
    Call pp-guard tool via subprocess.
    
    Args:
        prompt: User prompt to evaluate
        timeout: Subprocess timeout in seconds
        
    Returns:
        Guard result dict with verdict, reason, confidence, etc.
        On error: Returns {"verdict": "proceed"} to fail open
    """
    logger.debug(f"Calling pp-guard with timeout={timeout}s")
    logger.debug(f"Prompt (truncated): {prompt[:100]}...")
    
    try:
        # Find project root (one level up from hooks/)
        project_root = Path(__file__).parent.parent
        
        # Build subprocess command to call pp_guard
        cmd = [
            "uv", "run", "python", "-c",
            """
import json
import sys
sys.path.insert(0, '.')
from mcp_server.tools import pp_guard

prompt = sys.argv[1]
result = pp_guard(prompt=prompt)
print(json.dumps(result))
""",
            prompt
        ]
        
        # Run subprocess with timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            cwd=project_root
        )
        
        # Parse JSON output
        if result.returncode == 0 and result.stdout.strip():
            response = json.loads(result.stdout)
            logger.info(f"pp-guard verdict: {response.get('verdict')} "
                       f"(confidence: {response.get('confidence', 0.0)})")
            logger.debug(f"pp-guard reason: {response.get('reason')}")
            return response
        else:
            # Guard failed - fail open
            logger.error(f"pp-guard failed with returncode {result.returncode}")
            logger.error(f"stderr: {result.stderr}")
            return {
                "verdict": "proceed",
                "reason": "Guard evaluation failed",
                "confidence": 0.0
            }
            
    except subprocess.TimeoutExpired:
        logger.warning(f"pp-guard timeout after {timeout}s - failing open")
        return {
            "verdict": "proceed",
            "reason": "Guard timeout",
            "confidence": 0.0
        }
    except Exception as e:
        logger.error(f"pp-guard error: {e}", exc_info=True)
        return {
            "verdict": "proceed",
            "reason": f"Guard error: {str(e)}",
            "confidence": 0.0
        }


def call_mcp_heal(prompt: str, mode: str = "auto", timeout: float = 25.0) -> dict:
    """
    Call pp-heal tool via subprocess.
    
    Args:
        prompt: User prompt to heal
        mode: Healing mode ("clarity", "anger", "auto")
        timeout: Subprocess timeout in seconds
        
    Returns:
        Heal result dict with healed_prompt, changes_made, etc.
        On error: Returns {"healed_prompt": original} to fail open
    """
    logger.debug(f"Calling pp-heal with mode={mode}, timeout={timeout}s")
    
    try:
        # Find project root
        project_root = Path(__file__).parent.parent
        
        # Build subprocess command to call pp_heal
        cmd = [
            "uv", "run", "python", "-c",
            f"""
import json
import sys
sys.path.insert(0, '.')
from mcp_server.tools import pp_heal

prompt = sys.argv[1]
result = pp_heal(prompt=prompt, mode='{mode}')
print(json.dumps(result))
""",
            prompt
        ]
        
        # Run subprocess with timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            cwd=project_root
        )
        
        # Parse JSON output
        if result.returncode == 0 and result.stdout.strip():
            response = json.loads(result.stdout)
            logger.info(f"pp-heal completed ({len(response.get('changes_made', []))} changes)")
            logger.debug(f"Healed prompt: {response.get('healed_prompt', '')[:100]}...")
            return response
        else:
            # Heal failed - return original
            logger.error(f"pp-heal failed with returncode {result.returncode}")
            logger.error(f"stderr: {result.stderr}")
            return {
                "healed_prompt": prompt,
                "changes_made": [],
                "error": "Heal failed"
            }
            
    except subprocess.TimeoutExpired:
        logger.warning(f"pp-heal timeout after {timeout}s")
        return {
            "healed_prompt": prompt,
            "changes_made": [],
            "error": "Heal timeout"
        }
    except Exception as e:
        logger.error(f"pp-heal error: {e}", exc_info=True)
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
    
    # Handle empty prompts
    if not prompt:
        logger.info("Empty prompt detected - blocking")
        return {
            "continue": False,
            "userMessage": "⚠️ Empty prompt - please provide instructions"
        }
    
    # Call pp-guard to evaluate prompt quality
    guard_result = call_mcp_guard(prompt, timeout=25.0)
    verdict = guard_result.get("verdict", "proceed")
    reason = guard_result.get("reason", "No reason provided")
    
    # Process verdict
    if verdict == "proceed":
        # ✅ Good prompt - allow through
        logger.info("Verdict: PROCEED - allowing prompt through")
        return {
            "continue": True,
            "prompt": prompt
        }
    
    elif verdict == "intervene":
        # ❌ Bad prompt - block with explanation
        logger.info(f"Verdict: INTERVENE - blocking prompt ({reason})")
        return {
            "continue": False,
            "userMessage": f"🛑 Prompt needs improvement: {reason}"
        }
    
    elif verdict == "heal":
        # 🩹 Healable prompt - auto-heal if enabled
        if config["auto_cast_heal"]:
            logger.info("Verdict: HEAL - auto-healing enabled, healing prompt")
            # Auto-heal and allow through
            heal_mode = "auto"  # Will use anger_translator config internally
            heal_result = call_mcp_heal(prompt, mode=heal_mode, timeout=25.0)
            healed_prompt = heal_result.get("healed_prompt", prompt)
            
            logger.info("Auto-heal complete - allowing healed prompt through")
            return {
                "continue": True,
                "prompt": healed_prompt,
                "userMessage": "🩹 Prompt auto-healed for clarity"
            }
        else:
            logger.info("Verdict: HEAL - auto-healing disabled, blocking for manual improvement")
            # Auto-heal disabled - block and suggest manual improvement
            return {
                "continue": False,
                "userMessage": f"💡 Prompt could be improved: {reason}\n\nTip: Enable AUTO_CAST_HEAL for automatic fixes"
            }
    
    # Unknown verdict - fail open (allow)
    logger.warning(f"Unknown verdict: {verdict} - failing open")
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

