#!/bin/bash
# Install Prompt Paladin hook for Cursor
# This wrapper ensures correct working directory and uses project's Python environment

cd "$(dirname "$0")"
uv run python hooks/install.py "$@"

