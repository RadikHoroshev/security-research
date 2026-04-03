# Agent Communication Protocol

## Rules
- Agents READ tasks from `queue/*.json`
- Agents WRITE results to `results/*.json`
- Claude reads `results/` — never raw agent output
- Format: compact JSON, no prose, no markdown
- Max result file: 50KB

## File naming
queue/  → {phase}_{task}.json      (written by Claude)
results/ → {phase}_{agent}.json    (written by agents)

## JSON Schema

### Queue task
{"phase":1,"task":"...","target":"...","args":{}}

### Result
{"phase":1,"agent":"qwen","status":"ok","ts":1234567890,"data":{}}

## Status values
ok | fail | partial | skip

## Claude reads results via
cat /Users/code/project/intel/results/*.json
