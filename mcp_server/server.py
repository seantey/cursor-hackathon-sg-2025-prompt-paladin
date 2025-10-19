"""FastMCP server for Prompt Paladin."""
import logging
import sys
from fastmcp import FastMCP
from typing import Optional, Dict, Any

from .tools import pp_guard, pp_suggestions, pp_heal, pp_discuss, pp_proceed

# Setup logging for MCP server
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stderr)  # Log to stderr so it doesn't interfere with MCP protocol
    ]
)

# Initialize MCP server
mcp = FastMCP("prompt-paladin")


@mcp.tool()
def pp_guard_tool(prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Evaluate prompt quality and determine if it should proceed, be healed, or require intervention.
    
    Args:
        prompt: The user prompt to evaluate
        context: Optional context including conversation_history, active_files, selected_code, etc.
    
    Returns:
        Evaluation result with verdict, reason, confidence, issues
    """
    return pp_guard(prompt, context)


@mcp.tool()
def pp_suggestions_tool(prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate 2-3 improved alternatives to the given prompt.
    
    Args:
        prompt: The original prompt to improve
        context: Optional context
        
    Returns:
        List of improved prompt suggestions with explanations
    """
    return pp_suggestions(prompt, context)


@mcp.tool()
def pp_heal_tool(
    prompt: str,
    mode: str = "auto",
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Automatically rewrite prompt for better clarity or tone.
    
    Args:
        prompt: The prompt to heal
        mode: Healing mode - "clarity", "anger", or "auto" (default)
        context: Optional context
        
    Returns:
        Healed prompt with list of changes made
    """
    return pp_heal(prompt, mode, context)


@mcp.tool()
def pp_discuss_tool(prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate clarifying questions for unclear prompts.
    
    Args:
        prompt: The unclear prompt
        context: Optional context
        
    Returns:
        List of specific questions to clarify user intent
    """
    return pp_discuss(prompt, context)


@mcp.tool()
def pp_proceed_tool(prompt: str) -> Dict[str, Any]:
    """
    Allow user to proceed with original prompt (override).
    
    Args:
        prompt: The original prompt
        
    Returns:
        Acknowledgment of user override
    """
    return pp_proceed(prompt)


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
