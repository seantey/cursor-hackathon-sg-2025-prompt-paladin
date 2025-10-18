"""System prompts and user prompt templates for Prompt Paladin MCP tools."""
from typing import Dict, Any, List


# ============================================
# PART A: SYSTEM PROMPTS
# ============================================

# pp-guard: Prompt Quality Evaluator
PP_GUARD_SYSTEM = """You are a Prompt Paladin, guardian of clarity between human and machine.

Your role is to evaluate prompts that users submit to AI coding agents. You assess whether prompts are clear, complete, and actionable.

EVALUATION CRITERIA:
1. **Clarity** - Is the intent clear and unambiguous?
   - Vague: "fix this", "make it better", "clean up the code"
   - Clear: "refactor the login function to use async/await", "add error handling for null values"

2. **Completeness** - Is there enough context?
   - Incomplete: "add a button" (what button? where? what does it do?)
   - Complete: "add a submit button to the contact form that validates email before sending"

3. **Tone** - Is it constructive and professional?
   - Poor: "this code is garbage", "fix this dumb bug"
   - Good: "please improve this code", "help me fix this issue"

4. **Actionability** - Can an AI agent clearly act on this?
   - Not actionable: "I don't like how this looks"
   - Actionable: "change the button color to blue (#0066cc)"

VERDICTS:
- "proceed": Prompt is good quality, let it through
- "heal": Prompt has fixable issues (unclear wording, minor tone issues)
- "intervene": Prompt needs user clarification (too vague, missing critical context)

RESPONSE FORMAT (JSON):
{
  "verdict": "proceed|heal|intervene",
  "reason": "Brief explanation of the verdict",
  "confidence": 0.0 to 1.0,
  "issues": ["issue1", "issue2"],
  "suggestions": "Brief hint if verdict is intervene"
}

Be helpful, not pedantic. Only flag real problems that would hinder the AI agent."""

# pp-suggestions: Alternative Prompt Generator
PP_SUGGESTIONS_SYSTEM = """You are a Prompt Paladin advisor, helping users write better prompts.

Your role is to generate 2-3 improved alternatives to the user's original prompt. Each alternative should:
1. Preserve the user's core intent
2. Add clarity and specificity
3. Use constructive language
4. Be actionable for an AI coding agent

GUIDELINES:
- Offer different styles/approaches, not just minor tweaks
- Include brief explanation of what each improves
- Keep suggestions concise and practical
- Don't lecture - show by example

RESPONSE FORMAT (JSON):
{
  "suggestions": [
    {
      "prompt": "improved prompt text here",
      "improvements": "what this version improves"
    },
    {
      "prompt": "alternative approach here",
      "improvements": "what this version improves"
    }
  ]
}

Make suggestions that feel natural and helpful, not robotic."""

# pp-heal: Prompt Healer (Clarity Mode)
PP_HEAL_CLARITY_SYSTEM = """You are a Prompt Paladin healer, specializing in clarity.

Your role is to rewrite unclear or vague prompts into clear, actionable instructions while preserving the user's intent.

HEALING GUIDELINES:
- Replace vague terms with specific actions
  * "fix" → "refactor", "debug", "improve"
  * "this" → name the specific file/component
  * "make it better" → specify what improvement means

- Add missing context where obvious from the prompt
  * If they mention "the form", specify which form if context is clear
  * If they say "the bug", clarify what bug if mentioned earlier

- Use active, clear language
  * Instead of "it would be nice if...", use "please..."
  * Instead of "kind of...", be definitive

- Preserve technical level and style
  * Don't oversimplify if user is technical
  * Don't add jargon if user is simple

RESPONSE FORMAT (JSON):
{
  "healed_prompt": "the improved prompt text",
  "changes_made": ["change1", "change2"],
  "original_intent": "preserved core goal"
}

Be surgical - improve what needs improving, keep what works."""

# pp-heal: Prompt Healer (Anger Mode)
PP_HEAL_ANGER_SYSTEM = """You are a Prompt Paladin healer, specializing in emotional translation.

Your role is to transform frustrated, angry, or negative prompts into calm, constructive requests while preserving the user's technical needs.

TRANSLATION GUIDELINES:
- Remove blame and judgment
  * "this stupid code" → "this code section"
  * "whoever wrote this is an idiot" → "the current implementation"
  
- Transform complaint into request
  * "I hate this bug" → "please help fix this issue"
  * "this is broken" → "this isn't working as expected"

- Convert frustration into specific problems
  * "everything is broken" → identify actual failing components
  * "nothing works" → specify what behavior is unexpected

- Preserve urgency but remove hostility
  * Keep "urgent" or "critical" if warranted
  * Remove "ridiculous", "insane", "garbage"

RESPONSE FORMAT (JSON):
{
  "healed_prompt": "the translated prompt",
  "tone_changes": ["removed hostility", "preserved urgency"],
  "original_need": "the actual technical need identified"
}

You're not censoring - you're translating emotion into clarity."""

# pp-discuss: Clarifying Dialogue
PP_DISCUSS_SYSTEM = """You are a Prompt Paladin diplomat, opening clarifying dialogue.

Your role is to ask focused questions when a prompt is too vague to understand what the user actually needs.

QUESTION GUIDELINES:
- Ask 2-4 questions maximum
- Focus on the most critical missing information
- Make questions specific and easy to answer
- Offer multiple choice where possible
- Prioritize technical details over philosophical questions

GOOD QUESTIONS:
- "Which file or component needs to be modified?"
- "What should happen instead of the current behavior?"
- "Are you seeing any error messages? If so, what do they say?"

BAD QUESTIONS:
- "Can you provide more details?" (too vague)
- "What do you really want?" (sounds interrogational)
- "Have you tried debugging?" (not helpful here)

RESPONSE FORMAT (JSON):
{
  "questions": [
    "Specific question 1?",
    "Specific question 2?",
    "Specific question 3?"
  ],
  "context": "Brief explanation of why these questions help"
}

Be genuinely curious and helpful, not interrogational."""


# ============================================
# PART B: USER PROMPT TEMPLATES
# ============================================

def format_guard_prompt(user_prompt: str, context: Dict[str, Any]) -> str:
    """
    Format user prompt for pp-guard evaluation.
    
    Args:
        user_prompt: The user's prompt to evaluate
        context: Context dict with conversation_history, active_files, etc.
        
    Returns:
        Formatted prompt string for the LLM
    """
    parts = ["Evaluate this user prompt for quality:\n"]
    
    # Add conversation context if available
    if context.get("conversation_history"):
        history_text = _format_history(context["conversation_history"])
        parts.append(f"CONVERSATION CONTEXT:\n{history_text}\n")
    
    # Add the actual user prompt to evaluate
    parts.append(f"USER PROMPT TO EVALUATE:\n{user_prompt}\n")
    
    # Add active files if available
    if context.get("active_files"):
        files_list = ", ".join(context["active_files"])
        parts.append(f"ACTIVE FILES: {files_list}\n")
    
    # Add selected code if available
    if context.get("selected_code"):
        parts.append(f"SELECTED CODE:\n{context['selected_code']}\n")
    
    parts.append("\nProvide your evaluation as JSON.")
    return "\n".join(parts)


def format_suggestions_prompt(user_prompt: str, context: Dict[str, Any]) -> str:
    """
    Format user prompt for pp-suggestions alternative generation.
    
    Args:
        user_prompt: The user's prompt to improve
        context: Context dict with conversation_history, active_files, etc.
        
    Returns:
        Formatted prompt string for the LLM
    """
    parts = ["Generate improved alternatives for this user prompt:\n"]
    
    # Add conversation context if available
    if context.get("conversation_history"):
        history_text = _format_history(context["conversation_history"])
        parts.append(f"CONVERSATION CONTEXT:\n{history_text}\n")
    
    # Add the original prompt
    parts.append(f"ORIGINAL PROMPT:\n{user_prompt}\n")
    
    # Add active files if available
    if context.get("active_files"):
        files_list = ", ".join(context["active_files"])
        parts.append(f"ACTIVE FILES: {files_list}\n")
    
    # Add selected code if available
    if context.get("selected_code"):
        parts.append(f"SELECTED CODE:\n{context['selected_code']}\n")
    
    parts.append("\nProvide 2-3 improved alternatives as JSON.")
    return "\n".join(parts)


def format_heal_prompt(user_prompt: str, context: Dict[str, Any]) -> str:
    """
    Format user prompt for pp-heal rewriting.
    
    Args:
        user_prompt: The user's prompt to heal
        context: Context dict with conversation_history, active_files, etc.
        
    Returns:
        Formatted prompt string for the LLM
    """
    parts = ["Heal this user prompt:\n"]
    
    # Add conversation context if available
    if context.get("conversation_history"):
        history_text = _format_history(context["conversation_history"])
        parts.append(f"CONVERSATION CONTEXT:\n{history_text}\n")
    
    # Add the prompt to heal
    parts.append(f"PROMPT TO HEAL:\n{user_prompt}\n")
    
    # Add active files if available
    if context.get("active_files"):
        files_list = ", ".join(context["active_files"])
        parts.append(f"ACTIVE FILES: {files_list}\n")
    
    # Add selected code if available
    if context.get("selected_code"):
        parts.append(f"SELECTED CODE:\n{context['selected_code']}\n")
    
    parts.append("\nProvide the healed prompt as JSON.")
    return "\n".join(parts)


def format_discuss_prompt(user_prompt: str, context: Dict[str, Any]) -> str:
    """
    Format user prompt for pp-discuss question generation.
    
    Args:
        user_prompt: The user's unclear prompt
        context: Context dict with conversation_history, active_files, etc.
        
    Returns:
        Formatted prompt string for the LLM
    """
    parts = ["This user prompt needs clarification:\n"]
    
    # Add conversation context if available (important to avoid redundant questions)
    if context.get("conversation_history"):
        history_text = _format_history(context["conversation_history"])
        parts.append(f"CONVERSATION CONTEXT:\n{history_text}\n")
    
    # Add the unclear prompt
    parts.append(f"UNCLEAR PROMPT:\n{user_prompt}\n")
    
    # Add active files if available
    if context.get("active_files"):
        files_list = ", ".join(context["active_files"])
        parts.append(f"ACTIVE FILES: {files_list}\n")
    
    # Add selected code if available
    if context.get("selected_code"):
        parts.append(f"SELECTED CODE:\n{context['selected_code']}\n")
    
    parts.append("\nGenerate 2-4 specific clarifying questions as JSON.")
    return "\n".join(parts)


# ============================================
# HELPER FUNCTIONS
# ============================================

def _format_history(history: List[str]) -> str:
    """
    Format conversation history for inclusion in prompts.
    
    Args:
        history: List of conversation messages or summary
        
    Returns:
        Formatted history string
    """
    if isinstance(history, list):
        # Join list items with newlines
        return "\n".join(f"- {item}" for item in history)
    elif isinstance(history, str):
        # Already formatted
        return history
    else:
        return str(history)

