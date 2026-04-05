# 📡 SYSTEM CHANNEL TEST — Universal Task for ALL Agents

**Type:** Comprehensive channel test  
**Priority:** CRITICAL  
**Language:** English  
**Deadline:** Complete within this session  
**Applies to:** ALL agents (Qwen, Gemini, Codex, Jules, Ollama, AnythingLLM, Copilot, Agent Bridge, Security Team, WARP, Kiro, OpenCode, Obsidian, Context Injector)

---

## MISSION

Test ALL your communication channels. Verify you can reach other agents. Save results. Report back.

---

## STEP 1 — Self-Test

Verify YOU are operational:
- Can you respond?
- Can you read files?
- Can you execute commands?

Record: PASS or FAIL for each.

---

## STEP 2 — Test ALL Known Channels

For EACH channel below, test if YOU can reach it:

| Channel | How to Test | Expected |
|---|---|---|
| **Ollama API** | `curl -s http://localhost:11434/api/tags` | 200, models listed |
| **AnythingLLM RAG** | `curl -s http://localhost:3001/api/v1/workspaces -H "Authorization: Bearer 9MMMM0Y-2YC4FGE-JD7VX41-5MY20RT"` | 200, workspaces listed |
| **Agent Bridge** | `python3 intel/agent_bridge_mcp.py` (or read if available) | MCP tools available |
| **Goose Relay** | `goose run -t "Say HELLO"` | Response from Goose |
| **Jules** | `jules remote list --session` | Session list |
| **Qwen CLI** | `qwen --version` | Version number |
| **Codex CLI** | `codex --version` | Version number |
| **Gemini CLI** | `gemini --version` | Version number |
| **Copilot CLI** | `gh copilot suggest --help` | Help text |
| **Security Team** | `python3 security-team/mcp/server.py` | MCP server starts |
| **Heartbeat** | `python3 intel/heartbeat.py --state` | Health state JSON |
| **Queue Watcher** | `python3 intel/queue_watcher.py --status` | Queue status |
| **KB Sync** | `python3 intel/kb_sync_daemon.py --status` | Today's actions |
| **OpenCode** | `curl -s -o /dev/null -w 200 http://localhost:4096` | 200 |
| **WARP** | `cat .env.warp` (exists check) | File exists |

For each channel record:
- ✅ REACHABLE — you got a valid response
- ❌ UNREACHABLE — timeout, error, or not found
- ⚠️ DEGRADED — partial response, warnings

---

## STEP 3 — Test Inter-Agent Communication

Pick at least 3 OTHER agents and try to reach them directly:

Example:
```bash
# Try to call Qwen
qwen -y -p "Reply QWEN_OK"

# Try to call Ollama  
curl -s http://localhost:11434/api/generate -d '{"model":"qwen2.5-coder:7b","prompt":"OK","stream":false}'

# Try to read another agent's test result (if exists)
cat intel/inbox/*_result_*.md 2>/dev/null | head -5
```

Record which agents you could reach and which you couldn't.

---

## STEP 4 — Propose Redundant Channels

For YOUR role, propose at least 2 backup communication methods:

Example format:
```
My primary channel: [how I normally communicate]
Backup 1: [alternative method] — reliability: HIGH/MEDIUM/LOW
Backup 2: [alternative method] — reliability: HIGH/MEDIUM/LOW
Fallback: [last resort] — reliability: HIGH/MEDIUM/LOW
```

Also propose a **universal relay protocol** that ALL agents should support:
- File-based (outbox/inbox pattern)
- API-based (REST endpoint)
- MCP-based (through Agent Bridge)
- CLI-based (direct command)

---

## STEP 5 — Save Results

Write to: `intel/inbox/test_<YOUR_AGENT_NAME>.md`

Use this exact format:

```markdown
# 📡 Channel Test Results — [YOUR_AGENT_NAME]

**Date:** YYYY-MM-DD HH:MM UTC
**Agent:** [name]
**Role:** [your role in system]

## 1. Self-Test

| Test | Result |
|---|---|
| Respond | ✅/❌ |
| File access | ✅/❌ |
| Execute | ✅/❌ |

## 2. Channel Matrix

| Channel | Status | Latency | Notes |
|---|---|---|---|
| Ollama API | ✅/❌/⚠️ | X ms | |
| AnythingLLM | ✅/❌/⚠️ | X ms | |
| Agent Bridge | ✅/❌/⚠️ | X ms | |
| ... | ... | ... | ... |

## 3. Inter-Agent Reachability

| Agent | Reachable? | Method Used |
|---|---|---|
| Qwen | ✅/❌ | qwen -p "..." |
| Ollama | ✅/❌ | curl localhost:11434 |
| ... | ... | ... |

## 4. Redundant Channels Proposal

**Primary:** [description]
**Backup 1:** [description]
**Backup 2:** [description]
**Fallback:** [description]

**Universal Relay Protocol:**
- File-based: ✅ recommended / ❌ not suitable because...
- API-based: ✅ recommended / ❌ not suitable because...
- MCP-based: ✅ recommended / ❌ not suitable because...
- CLI-based: ✅ recommended / ❌ not suitable because...

## 5. Issues Found

| Severity | Issue | Impact | Suggested Fix |
|---|---|---|---|
| CRITICAL/HIGH/MEDIUM/LOW | ... | ... | ... |

## 6. Recommendations

1. ...
2. ...
3. ...
```

---

## STEP 6 — Read Other Agents' Results

```bash
ls intel/inbox/test_*.md
cat intel/inbox/test_*.md
```

Note any discrepancies. If your results differ from others for the same channel — explain why.

---

## STEP 7 — Commit Results

```bash
cd /Users/code/project
git add intel/inbox/test_*.md
git commit -m "📡 Channel test results — [YOUR_AGENT_NAME]"
git push
```

---

*This test creates the foundation for the universal communication relay module.*
*Results will be compiled into: intel/inbox/CHANNEL_TEST_SUMMARY.md*
