# Prompt Paladin Installation Guide

Complete guide for installing Prompt Paladin with optional automatic prompt interception.

---

## Quick Start (MCP Only - Recommended)

The fastest way to use Prompt Paladin is via MCP server only. **No hooks installation required.**

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure API Keys

Create `.env` file (or copy from `env.example`):

```bash
# At least one API key required
ANTHROPIC_API_KEY=your_key_here

# Optional: Other providers
OPENAI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

### 3. Add to Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "prompt-paladin": {
      "command": "/absolute/path/to/project/.venv/bin/python",
      "args": ["-m", "mcp_server.cli", "serve"],
      "cwd": "/absolute/path/to/project"
    }
  }
}
```

Replace `/absolute/path/to/project` with your actual project path.

### 4. Enable in Cursor

1. Open Cursor Settings → Tools & MCP
2. Toggle "prompt-paladin" ON (green dot)
3. Tools are now available: `pp-guard`, `pp-heal`, `pp-clarify`, etc.

### Usage

Manually call tools when needed:
- Use `pp-guard` to check prompt quality before submitting
- Use `pp-heal` to improve problematic prompts
- Use `pp-clarify` to add missing context

**Pros:** Easy to enable/disable, no global side effects
**Cons:** Manual - you must remember to check prompts

---

## Optional: Auto-Prompt Interception

Want **automatic** quality checks before every prompt submission? Install the Cursor hook.

### What It Does

The hook automatically:
- Intercepts prompts before they reach the AI
- Evaluates quality using `pp-guard`
- **Prepends feedback** if issues found (you choose whether to revise or proceed)
- Auto-heals prompts if enabled (optional)

### Installation

**One command:**

```bash
./install_hook.sh
```

That's it! The script will:
- ✅ Check your setup
- ✅ Create proper configuration in `~/.cursor/hooks.json`
- ✅ Preserve any existing hooks from other projects
- ✅ Create a backup before modifying
- ✅ Provide clear success/error messages

**Preview changes first:**

```bash
./install_hook.sh --dry-run
```

**Reinstall if paths changed:**

```bash
./install_hook.sh --force
```

### After Installation

1. **Restart Cursor** completely (⌘ Cmd+Q, then reopen)
2. Submit a prompt to test
3. Check logs: `tail -f hooks/hook.log`

### How It Works

When you submit a prompt with quality issues, you'll see:

```
[PROMPT QUALITY CHECK]
🛑 Prompt is too vague and lacks specific details...

💡 Suggestions:
- Specify what feature you're working on
- Include code context or file names
- Describe the expected behavior

---
Original prompt:
fix this code
```

You can then:
- Revise your prompt based on suggestions
- Proceed anyway if you think it's fine
- The choice is yours!

### Uninstallation

Remove the hook anytime:

```bash
./uninstall_hook.sh
```

This will:
- ✅ Remove only Prompt Paladin's hook
- ✅ Keep hooks from other projects
- ✅ Create a backup before changes
- ✅ Clean up empty structures

**Preview removal:**

```bash
./uninstall_hook.sh --dry-run
```

---

## Comparison: MCP-Only vs With Hooks

| Feature | MCP Only | With Hooks |
|---------|----------|------------|
| **Setup** | Easy (just toggle in Cursor) | One command: `./install_hook.sh` |
| **Enable/Disable** | Toggle in UI (instant) | Install/uninstall (restart needed) |
| **Prompt Checking** | Manual (call `pp-guard`) | Automatic (every prompt) |
| **Side Effects** | None | File in `~/.cursor/` (affects all workspaces) |
| **Uninstall** | Toggle off | Run `./uninstall_hook.sh` |
| **Best For** | Occasional use, quick setup | Power users, team enforcement |

---

## Configuration

### Feature Toggles (`.env`)

```bash
# Auto-heal prompts with minor issues (instead of just warning)
AUTO_CAST_HEAL=true

# Translate hostile language to constructive tone
ANGER_TRANSLATOR=true

# Hook timeout (seconds)
HOOK_TIMEOUT_SECS=30.0
```

### Model Selection

Use faster models for hooks to reduce latency:

```bash
# Fast models (recommended for hooks)
PP_GUARD_MODEL=claude-haiku-4-5    # Fast, cost-effective
PP_HEAL_MODEL=claude-haiku-4-5

# Or use quality models (slower)
PP_GUARD_MODEL=claude-3-5-sonnet-20241022
```

---

## Idempotency Guarantees

The install/uninstall scripts are **idempotent** - safe to run multiple times:

**Install script:**
- ✅ Running twice → "Already installed" (no changes)
- ✅ Running after path changes → Updates paths automatically
- ✅ Running with `--force` → Reinstalls

**Uninstall script:**
- ✅ Running twice → "Not installed" (no errors)
- ✅ Preserves hooks from other projects
- ✅ Creates backups only when making changes

**Backups:**
- Created automatically before any modification
- Format: `hooks.json.backup.YYYYMMDD_HHMMSS`
- Located in `~/.cursor/`

---

## Troubleshooting

### Hook Not Working

**Check if hook is installed:**
```bash
cat ~/.cursor/hooks.json
```

**Check hook logs:**
```bash
tail -20 /path/to/project/hooks/hook.log
```

**Test manually:**
```bash
echo '{"prompt":"test"}' | .venv/bin/python hooks/before_submit_prompt.py
```

### No Feedback Visible

If prompts are blocked but you don't see feedback:
- Check that you restarted Cursor after installation
- Verify hook logs show "FEEDBACK PREPENDED"
- Try a clearly bad prompt: "fix this code"

### Installation Fails

**Error: "Python venv not found"**
```bash
uv sync  # Create virtual environment first
```

**Error: "Permission denied"**
```bash
ls -la ~/.cursor/
# Ensure you have write permissions
```

**Error: "Corrupted hooks.json"**
```bash
# Back up manually, then remove
mv ~/.cursor/hooks.json ~/.cursor/hooks.json.old
./install_hook.sh
```

### Uninstallation Issues

**Hook still active after uninstall:**
- Restart Cursor completely (⌘ Cmd+Q)
- Verify `~/.cursor/hooks.json` doesn't contain project path

**Accidentally removed other hooks:**
- Restore from backup: `~/.cursor/hooks.json.backup.TIMESTAMP`

---

## Advanced Usage

### Multiple Projects

You can have hooks from multiple projects simultaneously. Each install preserves others:

```bash
# Project A
cd /path/to/project-a
./install_hook.sh

# Project B
cd /path/to/project-b
./install_hook.sh

# Both hooks now active in ~/.cursor/hooks.json
```

### Custom Configuration

Edit `~/.cursor/hooks.json` manually if needed:

```json
{
  "version": 1,
  "hooks": {
    "beforeSubmitPrompt": [
      {
        "command": "/path/to/.venv/bin/python",
        "args": ["/path/to/hooks/before_submit_prompt.py"],
        "cwd": "/path/to/project",
        "env": {
          "CUSTOM_VAR": "value"
        }
      }
    ]
  }
}
```

---

## Testing

### Test Hook Installation

```bash
# Preview what will be installed
./install_hook.sh --dry-run

# Install
./install_hook.sh

# Verify
cat ~/.cursor/hooks.json

# Test
# 1. Restart Cursor
# 2. Submit: "fix this code"
# 3. Should see feedback prepended
```

### Test Hook Functionality

```bash
# Good prompt (should pass)
echo '{"prompt":"Add error handling to the login function in auth.py"}' | \
  .venv/bin/python hooks/before_submit_prompt.py

# Bad prompt (should get feedback)
echo '{"prompt":"fix this"}' | \
  .venv/bin/python hooks/before_submit_prompt.py
```

---

## FAQ

**Q: Do I need hooks to use Prompt Paladin?**
A: No! MCP-only mode works great. Hooks are optional for automatic interception.

**Q: Will hooks affect all my Cursor workspaces?**
A: Yes, `~/.cursor/hooks.json` is global. Use MCP-only if you prefer per-project control.

**Q: Can I temporarily disable the hook?**
A: Yes, run `./uninstall_hook.sh`. To re-enable: `./install_hook.sh`

**Q: What happens if hook fails?**
A: It fails open (allows prompt through). Check `hooks/hook.log` for errors.

**Q: How do I update after pulling new changes?**
A: Run `./install_hook.sh --force` to update paths.

**Q: Can I use different models for hooks vs MCP?**
A: Yes! Set `PP_GUARD_MODEL` for hooks, `DEFAULT_MODEL` for MCP tools.

---

## Next Steps

- Read [HOOK_DEBUGGING_DEEP_DIVE.md](./documentation/guides/HOOK_DEBUGGING_DEEP_DIVE.md) for troubleshooting
- See [MCP_SERVER_SETUP.md](./documentation/guides/MCP_SERVER_SETUP.md) for MCP details
- Check [documentation/guides/](./documentation/guides/) for more guides

---

**Installation Support:**
- Install issues: Check `hooks/hook.log` and script output
- Hook not triggering: See [HOOK_DEBUGGING_DEEP_DIVE.md](./documentation/guides/HOOK_DEBUGGING_DEEP_DIVE.md)
- General questions: See [guide_overview.md](./documentation/guides/guide_overview.md)

**Last Updated:** October 21, 2025

