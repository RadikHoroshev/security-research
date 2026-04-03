#!/bin/bash
# Phase 3 — Auto scan (run directly, no agent needed)
# Usage: bash /Users/code/project/intel/queue/phase3_scan.sh

TARGET=/tmp/anythingllm
OUT=/Users/code/project/intel/results/phase3_scan.json

git clone --depth=1 https://github.com/Mintplex-Labs/anything-llm $TARGET 2>/dev/null || true

TS=$(date +%s)
SECRETS=$(gitleaks detect --source $TARGET -q 2>/dev/null | grep -c "Finding" || echo 0)
BANDIT=$(bandit -r $TARGET -ll -f json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps({'high':len([x for x in d['results'] if x['issue_severity']=='HIGH']),'medium':len([x for x in d['results'] if x['issue_severity']=='MEDIUM']),'files':list(set(x['filename'] for x in d['results'] if x['issue_severity']=='HIGH'))[:10]}))" 2>/dev/null || echo '{"high":0,"medium":0,"files":[]}')
DEPS=$(cd $TARGET && npm audit --json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); v=d.get('vulnerabilities',{}); print(json.dumps({'critical':sum(1 for x in v.values() if x.get('severity')=='critical'),'high':sum(1 for x in v.values() if x.get('severity')=='high')}))" 2>/dev/null || echo '{"critical":0,"high":0}')

echo "{\"phase\":3,\"agent\":\"scan\",\"status\":\"ok\",\"ts\":$TS,\"data\":{\"secrets\":$SECRETS,\"bandit\":$BANDIT,\"npm_audit\":$DEPS}}" > $OUT
echo "Done → $OUT"
cat $OUT
