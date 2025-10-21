#!/bin/bash
# Debug wrapper to capture all output and errors

DEBUG_LOG="/Users/seanmbp/Projects/prompt-paladin/cursor-hackathon-sg-2025-prompt-paladin/hooks/debug.log"

echo "=== DEBUG: $(date) ===" >> "$DEBUG_LOG" 2>&1
echo "PWD: $PWD" >> "$DEBUG_LOG" 2>&1
echo "Args: $@" >> "$DEBUG_LOG" 2>&1
echo "Stdin available: $([ -t 0 ] && echo 'no' || echo 'yes')" >> "$DEBUG_LOG" 2>&1

# Save stdin to a file for inspection
STDIN_FILE="/tmp/hook_stdin_$$.json"
cat > "$STDIN_FILE"
echo "Stdin saved to: $STDIN_FILE" >> "$DEBUG_LOG" 2>&1
echo "Stdin content:" >> "$DEBUG_LOG" 2>&1
cat "$STDIN_FILE" >> "$DEBUG_LOG" 2>&1
echo "" >> "$DEBUG_LOG" 2>&1

# Run the actual hook and capture everything
cd /Users/seanmbp/Projects/prompt-paladin/cursor-hackathon-sg-2025-prompt-paladin
cat "$STDIN_FILE" | /Users/seanmbp/Projects/prompt-paladin/cursor-hackathon-sg-2025-prompt-paladin/.venv/bin/python \
  /Users/seanmbp/Projects/prompt-paladin/cursor-hackathon-sg-2025-prompt-paladin/hooks/before_submit_prompt.py \
  2>> "$DEBUG_LOG"

EXIT_CODE=$?
echo "Exit code: $EXIT_CODE" >> "$DEBUG_LOG" 2>&1
echo "=== END ===" >> "$DEBUG_LOG" 2>&1

rm -f "$STDIN_FILE"
exit $EXIT_CODE

