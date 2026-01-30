#!/usr/bin/env python
"""Unified entry point for Claude Agent SDK CLI.

This script provides a command-line interface to manage sessions
and list available resources.

Usage:
  uv run main.py skills             # List available skills
  uv run main.py agents             # List available agents
  uv run main.py subagents          # List available subagents
  uv run main.py sessions           # List conversation sessions
  uv run main.py --help             # Show help
"""
from cli.main import cli

if __name__ == "__main__":
    cli()
