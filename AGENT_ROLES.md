# Agent Role Assignments (Dynamic)

**Версия:** 1.1 — Active Agents Only  
**Дата:** 2026-04-03  
**Сессия:** Bug Bounty — mlflow/mlflow

---

## Текущие Назначения Ролей

| Этап | Задача | Назначенный Агент | Альтернатива | Статус |
|------|--------|------------------|--------------|--------|
| **Phase 1** | find_targets | `gemini-cli` | `goose` (browser) | ✅ DONE |
| **Phase 2** | clone_and_scan | `qwen-desktop` | `goose` (terminal) | 🔄 READY |
| **Phase 3** | deep_analysis | `qwen-desktop` | — | ⏳ PENDING |
| **Phase 4** | poc_generation | `qwen-desktop` | — | ⏳ PENDING |
| **Phase 5** | report_submit | `gemini-cli` + `jules-cli` | — | ⏳ PENDING |

---

## Как Изменить Назначение

1. Открой `queue/{phase}_{task}.json`
2. Измени поле `"assigned_agent"`:
```json
{
  "phase": 2,
  "task": "clone_and_scan",
  "assigned_agent": "goose",  // ← измени с "qwen-desktop" на "goose"
  ...
}
```
3. Сохрани файл — агент подхватит задачу при следующем запуске.

---

## Доступные Агенты для Назначения (Активные)

```json
{
  "agents": {
    "trae": {
      "type": "ide_assistant",
      "roles": ["Orchestrator", "CodeAuthor", "Architect", "Validator", "Researcher"],
      "strengths": ["complex_refactoring", "codebase_exploration", "multi_agent_orchestration", "security_audits"]
    },
    "qwen-desktop": {
      "type": "cli",
      "command": "qwen -p \"PROMPT\"",
      "roles": ["Analyst", "ExploitDev", "Reviewer"],
      "strengths": ["code_analysis", "poc_generation", "deep_reasoning"]
    },
    "gemini-cli": {
      "type": "cli",
      "command": "gemini -p \"PROMPT\" --yolo",
      "roles": ["Recon", "Reporter", "DuplicateCheck"],
      "strengths": ["web_search", "huntr_integration", "report_writing"]
    },
    "jules-cli": {
      "type": "cli",
      "command": "jules \"PROMPT\"",
      "roles": ["Scribe", "Logger", "DocWriter"],
      "strengths": ["documentation", "session_logging", "github_ops"]
    },
    "goose": {
      "type": "orchestrator",
      "command": "goose run FILE.md",
      "roles": ["Coordinator", "Executor"],
      "strengths": ["terminal", "browser", "filesystem", "github"]
    }
  },
  "pending": {
    "claude-mcp": {
      "status": "excluded",
      "reason": "Not yet connected — will be added after initial tests",
      "type": "mcp_client",
      "potential_roles": ["Architect", "Validator", "Strategist"]
    }
  }
}
```

---

**Примечание:** Этот файл генерируется динамически. Для добавления нового агента создай `intel/agents/{agent_id}.md` и обнови секцию "Доступные Агенты".
