# Project Halt: Hook Feedback Display

**Date:** October 21, 2025  
**Status:** ⏸️ Paused - Waiting for Cursor Platform Support  
**Reason:** Cursor's `beforeSubmitPrompt` hook lacks user feedback capability

---

## What We Wanted to Achieve

**Goal:** Automatically intercept bad prompts BEFORE they reach the LLM and show helpful feedback to users.

**Ideal User Experience:**
```
User types: "fix this code"
    ↓
Hook detects vague prompt (3-5 seconds)
    ↓
Cursor shows in UI:
    🛑 Prompt needs improvement
    
    Reason: Too vague - no file or function specified
    
    💡 Suggestions:
    - Specify which file needs fixing
    - Describe what's wrong
    - Include expected behavior
    
    [Edit Prompt] [Submit Anyway]
    ↓
User revises or proceeds
```

---

## What We Built

### ✅ **Working Components**

1. **Robust MCP Server** - Fully functional
   - `pp-guard` - Evaluates prompt quality
   - `pp-heal` - Fixes problematic prompts
   - `pp-clarify` - Asks clarifying questions
   - All tools work perfectly via Cursor's MCP integration

2. **Idempotent Install Scripts**
   - `hooks/install.py` - Safe, Python-based installer
   - `hooks/uninstall.py` - Clean uninstaller
   - Preserves other projects' hooks
   - Creates automatic backups

3. **Hook Implementation**
   - Successfully calls `pp-guard` before submission
   - Correctly evaluates prompt quality
   - Returns verdict in 3-5 seconds
   - Logging works perfectly

4. **Comprehensive Documentation**
   - `INSTALL.md` - Complete setup guide
   - `HOOK_DEBUGGING_DEEP_DIVE.md` - Debugging journey
   - `IMPLEMENTATION_SUMMARY.md` - Technical details

---

## The Limitation We Hit

### Cursor's `beforeSubmitPrompt` Schema

According to Cursor's official documentation:

```javascript
// Input
{
  "prompt": "<user prompt text>",
  "attachments": [...]
}

// Output
{
  "continue": true | false  // ← ONLY THIS!
}
```

**What's Missing:**
- ❌ No `userMessage` field (can't show feedback to user)
- ❌ No `reason` field (can't explain why blocked)
- ❌ No `prompt` modification (can't inject feedback)

**Result:** Hook can only **silently block** or **silently allow**. Users see:
```
Submission blocked by hook
A beforeSubmitPrompt hook blocked this submission.
```

No details, no suggestions, no way forward.

---

## Claude Code Has This Feature!

Claude Code's `UserPromptSubmit` hook supports:

```json
{
  "decision": "block",
  "reason": "Explanation shown to user"  // ← THIS IS WHAT WE NEED!
}
```

From Claude Code docs:
> `"block"` prevents the prompt from being processed. **`reason` is shown to the user**

**This is exactly what we need, but it's Claude Code only.**

---

## What We Tried

### Attempt 1: Return userMessage (Failed)
```python
return {
    "continue": False,
    "userMessage": "🛑 Prompt needs improvement: {reason}"
}
```
**Result:** Cursor ignores `userMessage`, shows generic block message

### Attempt 2: Modify Prompt (Failed)
```python
return {
    "continue": True,
    "prompt": "[FEEDBACK PREPENDED]\n{reason}\n\n{original_prompt}"
}
```
**Result:** Cursor ignores modified `prompt`, uses original

### Attempt 3: macOS Notifications (Workaround)
```python
os.system('osascript -e ...')  # Show system notification
return {"continue": False}
```
**Result:** Works but clunky, macOS-only, notifications easily dismissed

---

## Current State

### What Works ✅

1. **MCP Server** - Production ready
   - Manual prompt checking via `pp-guard`
   - Fully visible feedback in chat
   - Toggle on/off in Cursor UI
   - No limitations

2. **Hook Infrastructure** - Complete
   - Idempotent install/uninstall scripts
   - Direct Python call (no wrapper needed after debugging)
   - Proper error handling and logging
   - Ready to use when Cursor adds support

3. **Documentation** - Comprehensive
   - Installation guides
   - Debugging deep-dive
   - Troubleshooting references

### What Doesn't Work ❌

1. **Hook User Feedback** - Blocked by Cursor limitation
   - Can detect bad prompts ✅
   - Can block them ✅
   - Cannot show WHY ❌
   - Cannot show suggestions ❌

---

## Recommended Approach (Current)

### For Users: **MCP-Only Workflow**

**Simple and Effective:**

```
User: "Before I submit, can you check this prompt: fix this code"
    ↓
AI calls pp-guard MCP tool
    ↓
AI: "That prompt is too vague. Suggestions: ..."
    ↓
User: "Okay, revised: Add error handling to login() in auth.py"
    ↓
AI: "Much better! Now I'll help..."
```

**Advantages:**
- ✅ Fully visible feedback
- ✅ Natural conversation flow
- ✅ User has full control
- ✅ No platform limitations
- ✅ Works today

**Disadvantages:**
- 🟡 Manual (user must remember to ask)
- 🟡 Extra back-and-forth
- 🟡 Slower (two LLM calls)

---

## Future: When Cursor Adds Support

When Cursor implements `userMessage` or `reason` field for `beforeSubmitPrompt`, we can:

### Quick Implementation

Just update the hook response format:

```python
# hooks/before_submit_prompt.py
if verdict == "intervene":
    return {
        "continue": False,
        "reason": f"{reason}\n\nSuggestions:\n{suggestions}"
        # or "userMessage": ... if Cursor uses that field name
    }
```

**Everything else is ready:**
- ✅ Install scripts work
- ✅ Hook logic works
- ✅ LLM integration works
- ✅ Just needs 5-line change to response format

---

## What to Monitor

### Track Cursor Updates

Watch for these in Cursor release notes:
- `beforeSubmitPrompt` hook enhancements
- User feedback display when blocking
- Prompt modification support
- Any hook API improvements

### Feature Request to File

Consider filing a feature request with Cursor:

```markdown
Title: Add userMessage/reason support to beforeSubmitPrompt hook

Currently, beforeSubmitPrompt can only return {continue: true/false}.
When blocking (continue: false), users see a generic message with no details.

Request: Add support for userMessage or reason field, similar to:
- beforeShellExecution (has userMessage)
- Claude Code's UserPromptSubmit (has reason field)

Use case: Quality checking prompts, showing suggestions when blocking

Example:
{
  "continue": false,
  "userMessage": "Prompt needs more context. Suggestions: ..."
}
```

---

## Alternative: Switch to Claude Code

If immediate hook feedback is critical, consider:

**Claude Code:**
- ✅ Has `reason` field in `UserPromptSubmit` hook
- ✅ Shows blocking reason to user
- ✅ Same MCP protocol (server works as-is)
- ✅ Hook code needs minimal changes

**Migration:**
1. Point hook at Claude Code config location
2. Change response format to Claude Code schema
3. Test

**Estimated effort:** 1-2 hours

---

## Current Recommendation

**Ship with MCP-Only, document hook limitation:**

### INSTALL.md Updates

```markdown
## Installation Options

### Option 1: MCP Server (Recommended)

Full functionality with visible feedback. Just enable in Cursor.

### Option 2: Hooks (Experimental - Limited)

⚠️ Cursor Limitation: Hooks can block prompts but cannot show why.

Due to Cursor's beforeSubmitPrompt API limitations, blocked prompts 
show a generic message. Check hooks/hook.log for details.

We recommend MCP-only until Cursor adds feedback display support.

Tracked issue: https://github.com/getcursor/cursor/issues/...
```

---

## Code Ready for Future

When Cursor adds support, this works immediately:

**File:** `hooks/before_submit_prompt.py`
**Lines:** 299-327 (intervene verdict handling)

**Current (blocks silently):**
```python
return {
    "continue": False
}
```

**Future (shows feedback):**
```python
return {
    "continue": False,
    "reason": f"{reason}\n\nSuggestions:\n{suggestions}"
    # OR: "userMessage": ... depending on what Cursor implements
}
```

Everything else stays the same - just update the response format.

---

## Files Affected

### Ready to Ship (No Changes Needed)
- `hooks/install.py` ✅
- `hooks/uninstall.py` ✅
- `install_hook.sh` ✅
- `uninstall_hook.sh` ✅
- `hooks/run.sh` ✅
- All MCP server files ✅

### Needs Update (When Cursor Adds Support)
- `hooks/before_submit_prompt.py` - Add `reason` field to response
- `INSTALL.md` - Remove limitation warning
- `README.md` - Update with hook recommendations

### Consider Removing (If Staying MCP-Only)
- `hooks/debug_wrapper.sh` - Debug only
- `hooks/debug.log` - Debug only
- Hook-related docs could be simplified

---

## Decision Point

**Choose one:**

### A. Ship MCP-Only (Recommended)
- Document hook limitation clearly
- Focus on MCP server experience
- Revisit hooks when Cursor adds support

### B. Implement macOS Notifications
- Provides some feedback (via notifications)
- macOS only
- Extra complexity

### C. Wait for Cursor Update
- Don't release until Cursor fixes API
- Could take weeks/months
- Delays project

**Recommended: Option A** - The MCP server provides all functionality with better UX than workarounds.

---

## Next Steps (If Going with Option A)

1. Revert prepending changes (back to simple blocking)
2. Update INSTALL.md to recommend MCP-only
3. Document hook limitation clearly
4. Polish MCP server documentation
5. File feature request with Cursor
6. Ship it! 🚀

---

**Last Updated:** October 21, 2025  
**Status:** Awaiting platform support or decision on workaround  
**Blocker:** Cursor's beforeSubmitPrompt API lacks user feedback mechanism

