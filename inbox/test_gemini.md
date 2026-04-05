# 🧪 Gemini CLI — Execution Test Results
**Date:** 2026-04-05 17:47:25

1. echo GEMINI_CLI_OK
`GEMINI_CLI_OK`

2. ls /Users/code/project/knowledge_base/ | head -3
```
AGENT_ONBOARDING.md
AGENT_RULES.md
CENTRAL_MEMORY.md
```

3. curl -s -o /dev/null -w "%{http_code}" http://localhost:11434
`200`

4. curl -s -o /dev/null -w "%{http_code}" http://localhost:3001
`404`

5. goose --version
` 1.29.0`

6. jules remote list --session 2>&1 | head -2
```
           ID                                    Description                                    Repo                Last active                Status         
 12256805939662671599    CHANNEL TEST — Execute and save resultsRead: intel/outbox/C…  RadikHoroshev/multi-a…  5s ago                  In Progress    
```

7. qwen --version
`0.14.0`
