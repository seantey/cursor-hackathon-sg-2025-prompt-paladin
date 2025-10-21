#!/bin/bash
# Uninstall Prompt Paladin hook from Cursor
# This wrapper ensures correct working directory and uses project's Python environment

cd "$(dirname "$0")"
uv run python hooks/uninstall.py "$@"

