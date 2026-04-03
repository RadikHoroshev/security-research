#!/bin/bash
# Full huntr pipeline: find target → clone → scan → wait for qwen → report
# Usage: bash run_pipeline.sh [github_org/repo]
# If no arg — reads recommended target from phase1_targets.json

set -e
INTEL=/Users/code/project/intel
PYTHON=/Users/code/.pyenv/versions/3.11.9/bin/python3

# ── Phase 1: Target selection ──────────────────────────────────────────────
if [ -n "$1" ]; then
    REPO="$1"
    echo "{\"phase\":1,\"agent\":\"manual\",\"status\":\"ok\",\"ts\":$(date +%s),\"data\":{\"recommended\":{\"repo\":\"$REPO\",\"url\":\"https://github.com/$REPO\"}}}" \
        > $INTEL/results/phase1_targets.json
else
    echo "▶ Phase 1: Finding targets..."
    $PYTHON $INTEL/scripts/find_targets.py --min-reward 200
fi

REPO=$(python3 -c "import json; d=json.load(open('$INTEL/results/phase1_targets.json')); print(d['data']['recommended']['repo'])")
echo "✓ Target: $REPO"

# ── Phase 2: Clone ─────────────────────────────────────────────────────────
TARGET_DIR="/tmp/$(echo $REPO | tr '/' '-')"
if [ ! -d "$TARGET_DIR" ]; then
    echo "▶ Cloning $REPO..."
    git clone --depth=1 "https://github.com/$REPO" "$TARGET_DIR"
fi
echo "✓ Cloned → $TARGET_DIR"

# ── Phase 3: Auto-scan ────────────────────────────────────────────────────
echo "▶ Phase 3: Auto-scan..."
TS=$(date +%s)

# Secrets
SECRETS=$(gitleaks detect --source "$TARGET_DIR" -q 2>/dev/null | grep -c "Finding" || echo 0)

# SAST (Python if exists)
if find "$TARGET_DIR" -name "*.py" -maxdepth 3 | grep -q .; then
    BANDIT=$(bandit -r "$TARGET_DIR" -ll -f json 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    r=d.get('results',[])
    h=[x for x in r if x['issue_severity']=='HIGH']
    print(json.dumps({'high':len(h),'files':list(set(x['filename'].split('$TARGET_DIR/')[-1] for x in h))[:5]}))
except: print('{\"high\":0,\"files\":[]}')
" 2>/dev/null || echo '{"high":0,"files":[]}')
else
    BANDIT='{"high":0,"files":[],"note":"no python files"}'
fi

# npm audit (Node if exists)
if [ -f "$TARGET_DIR/package.json" ]; then
    NPM=$(cd "$TARGET_DIR" && npm audit --json 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    v=d.get('vulnerabilities',{})
    print(json.dumps({'critical':sum(1 for x in v.values() if x.get('severity')=='critical'),'high':sum(1 for x in v.values() if x.get('severity')=='high')}))
except: print('{\"critical\":0,\"high\":0}')
" || echo '{"critical":0,"high":0}')
else
    NPM='{"critical":0,"high":0}'
fi

echo "{\"phase\":3,\"agent\":\"scan\",\"status\":\"ok\",\"ts\":$TS,\"data\":{\"repo\":\"$REPO\",\"dir\":\"$TARGET_DIR\",\"secrets\":$SECRETS,\"bandit\":$BANDIT,\"npm_audit\":$NPM}}" \
    > $INTEL/results/phase3_scan.json
echo "✓ Scan → $INTEL/results/phase3_scan.json"
cat $INTEL/results/phase3_scan.json | python3 -m json.tool

# ── Phase 2b: Print qwen task ──────────────────────────────────────────────
cat > $INTEL/queue/phase2_current.txt << EOF
Analyze the repository at $TARGET_DIR (already cloned).

Find exploitable vulnerabilities:
1. RCE: eval/exec/subprocess/child_process with USER-CONTROLLED input (trace data flow from HTTP request to dangerous function)
2. Path Traversal: file operations with user-controlled paths, check if normalization is bypassable
3. SSRF: HTTP fetch with user-controlled URL, check for missing blocklist of internal IPs
4. Auth bypass: missing authentication checks on sensitive endpoints
5. Prompt Injection: LLM system prompt built with unsanitized user input

For each finding: verify the FULL DATA FLOW from user input to sink.
Only report if actually exploitable (exploitable:true).

Write ONLY this JSON to $INTEL/results/phase2_qwen.json:
{"phase":2,"agent":"qwen","status":"ok","ts":UNIX_TS,"data":{"findings":[{"file":"path","line":0,"type":"RCE","severity":"High","flow":"user_input → function → sink","snippet":"code","exploitable":true,"notes":"why exploitable"}],"summary":"X exploitable findings"}}
EOF

echo ""
echo "══════════════════════════════════════════════════"
echo "▶ Phase 2: Run this command for qwen:"
echo ""
echo "  qwen \"\$(cat $INTEL/queue/phase2_current.txt)\""
echo ""
echo "Then tell Claude: results ready"
echo "══════════════════════════════════════════════════"
