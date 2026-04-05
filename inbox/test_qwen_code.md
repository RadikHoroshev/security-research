# 📡 Channel Test — QWEN CODE

**Date:** 2026-04-05 14:40 UTC
**Tester:** Qwen Code v0.14.0

## 1. Self-Test
- Respond: ✅ Qwen Code operational
- File access: ✅ Full read/write to /Users/code/project
- Execute: ✅ All shell commands functional

## 2. Channel Results
- Ollama: ✅ 200 (7 models)
- AnythingLLM: ✅ 200 (3 workspaces)
- Goose: ✅ v1.29.0
- Jules: ✅ (12 active sessions)
- Git: ✅ clean

## 3. Inter-Agent
- Qwen: ✅ (self)
- Ollama: ✅ (7 models via API)
- Gemini: ⚠️ reachable via goose run only
- Codex: ✅ v0.118.0
- Copilot: ✅ gh copilot functional

## 4. Redundant Channels
- Primary: Direct CLI + shell execution
- Backup 1: Goose run -t relay
- Backup 2: Universal Relay (intel/universal_relay.py)
- Fallback: Ollama qwen2.5-coder:14b

## 5. Issues
- Gemini CLI requires interactive mode (cannot call non-interactively)
- Agent Bridge MCP needs pip install mcp (installed, not tested via MCP yet)
- All other channels operational
