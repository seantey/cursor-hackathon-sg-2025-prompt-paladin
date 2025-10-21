#!/bin/bash
# Wrapper to run the hook from Cursor
# This ensures proper stdin handling and working directory

cd "$(dirname "$0")/.."
exec .venv/bin/python hooks/before_submit_prompt.py

