#!/bin/bash
# Wrapper script to debug hook execution from Cursor

# Log file for debugging
LOG_FILE="/Users/seanmbp/Projects/prompt-paladin/cursor-hackathon-sg-2025-prompt-paladin/hooks/cursor_wrapper.log"

# Log that we started
echo "=== Wrapper called at $(date) ===" >> "$LOG_FILE" 2>&1
echo "PWD: $PWD" >> "$LOG_FILE" 2>&1
echo "Args: $@" >> "$LOG_FILE" 2>&1

# Change to project directory
cd /Users/seanmbp/Projects/prompt-paladin/cursor-hackathon-sg-2025-prompt-paladin

# Run the actual hook and capture everything
/Users/seanmbp/Projects/prompt-paladin/cursor-hackathon-sg-2025-prompt-paladin/.venv/bin/python \
  /Users/seanmbp/Projects/prompt-paladin/cursor-hackathon-sg-2025-prompt-paladin/hooks/before_submit_prompt.py \
  2>> "$LOG_FILE"

# Log the exit code
EXIT_CODE=$?
echo "Exit code: $EXIT_CODE" >> "$LOG_FILE" 2>&1
echo "=== Wrapper finished ===" >> "$LOG_FILE" 2>&1

exit $EXIT_CODE

