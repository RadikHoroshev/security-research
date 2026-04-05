#!/usr/bin/env python3.11
"""
copilot_mcp.py — MCP сервер для GitHub Copilot CLI

Позволяет Goose и другим MCP-клиентам:
  - suggest — предложить команду по описанию
  - explain — объяснить команду
  - suggest-git — Git команды
  - shell — выполнить shell-команду через Copilot
"""

import os
import subprocess

from mcp.server.fastmcp import FastMCP

COPILOT_BIN = "/Users/code/.npm-global/bin/copilot"
COPILOT_MODEL = "gpt-5-mini"  # Экономная: 0 Premium requests
GH_COPILOT_BIN = "/Users/code/bin/gh"

mcp = FastMCP("CopilotCLI")


@mcp.tool()
def copilot_suggest(description: str) -> str:
    """Предложить shell-команду по текстовому описанию."""
    try:
        cmd = [
            "copilot", "-p", description,
            "--model", COPILOT_MODEL,
            "--allow-all", "--allow-all-tools", "--allow-all-urls",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return result.stdout.strip()
        return f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Timeout — Copilot слишком долго думает"
    except Exception as e:
        return f"Exception: {str(e)}"


@mcp.tool()
def copilot_explain(command: str) -> str:
    """Объяснить что делает shell-команда."""
    try:
        cmd = [
            "copilot", "-p", f"explain: {command}",
            "--model", COPILOT_MODEL,
            "--allow-all", "--allow-all-tools", "--allow-all-urls",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return result.stdout.strip()
        return f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Timeout — Copilot слишком долго думает"
    except Exception as e:
        return f"Exception: {str(e)}"


@mcp.tool()
def gh_copilot_suggest(description: str) -> str:
    """Предложить команду через GitHub CLI Copilot."""
    try:
        cmd = ["gh", "copilot", "suggest", "--plain", description]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return result.stdout.strip()
        return f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Timeout — Copilot слишком долго думает"
    except Exception as e:
        return f"Exception: {str(e)}"


@mcp.tool()
def gh_copilot_explain(command: str) -> str:
    """Объяснить команду через GitHub CLI Copilot."""
    try:
        cmd = ["gh", "copilot", "explain", "--plain", command]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return result.stdout.strip()
        return f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Timeout — Copilot слишком долго думает"
    except Exception as e:
        return f"Exception: {str(e)}"


@mcp.tool()
def copilot_status() -> dict:
    """Проверить статус Copilot CLI."""
    copilot_ok = os.path.isfile(COPILOT_BIN)
    gh_copilot_ok = os.path.isfile(GH_COPILOT_BIN)

    # Версия
    version = "unknown"
    if copilot_ok:
        try:
            r = subprocess.run(
                [COPILOT_BIN, "--version"],
                capture_output=True, text=True, timeout=5
            )
            version = r.stdout.strip()
        except Exception:
            pass

    return {
        "copilot_cli": {
            "installed": copilot_ok,
            "path": COPILOT_BIN,
            "version": version,
        },
        "gh_copilot": {
            "installed": gh_copilot_ok,
            "path": GH_COPILOT_BIN,
        },
    }


if __name__ == "__main__":
    mcp.run()
