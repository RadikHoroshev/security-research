#!/usr/bin/env python3
"""
huntr_logger.py — Real-time logging for Huntr bug bounty process

Использование:
  python3 intel/huntr_logger.py --log "subfinder found 45 subdomains" --agent gemini --tool subfinder --target target.com
  python3 intel/huntr_logger.py --vuln "XSS in login" --severity HIGH --target https://target.com --agent qwen
  python3 intel/huntr_logger.py --status                    # Показать статус
  python3 intel/huntr_logger.py --today                     # Отчёт за сегодня
"""

import json
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

KB_DIR = Path(__file__).parent.parent / "knowledge_base"
WORKFLOWS = KB_DIR / "workflows"
RESEARCH = KB_DIR / "research"
METRICS_FILE = KB_DIR / "research" / "huntr_metrics.json"

def log_action(agent, action, tool="", target="", result="", status="success"):
    """Log an agent action to JSONL file."""
    WORKFLOWS.mkdir(parents=True, exist_ok=True)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    logfile = WORKFLOWS / f"huntr_{today}.jsonl"
    
    entry = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "agent": agent,
        "action": action,
        "tool": tool,
        "target": target,
        "result": result[:500],
        "status": status
    }
    
    with open(logfile, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    # Update metrics
    update_metrics(entry)
    
    # Index in ChromaDB
    try:
        import subprocess
        ingestor = Path(__file__).parent / "rag_ingestor.py"
        if ingestor.exists():
            subprocess.run(["python3.11", str(ingestor), "--ingest"], 
                          capture_output=True, timeout=30)
    except:
        pass
    
    print(f"✅ Logged: [{agent}] {action} → {status}")
    return entry

def log_vulnerability(agent, title, severity, target, description="", poc="", bounty=""):
    """Log a found vulnerability as markdown file."""
    RESEARCH.mkdir(parents=True, exist_ok=True)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    filename = f"vuln_{today}_{int(time.time())}.md"
    filepath = RESEARCH / filename
    
    content = f"""---
title: "{title}"
type: vulnerability
category: unknown
severity: {severity}
target: "{target}"
date: {today}
agent: {agent}
status: found
bounty_estimate: "{bounty}"
---

# {title}

**Severity:** {severity}
**Target:** {target}
**Found by:** {agent}
**Date:** {today}

## Описание
{description}

## Proof of Concept
```
{poc}
```

## Влияние
[Описать потенциальный ущерб]

## Рекомендации
[Как исправить]
"""
    filepath.write_text(content)
    print(f"🐛 Vulnerability logged: {filepath.name}")
    
    # Log action too
    log_action(agent, "vulnerability_found", tool="manual", target=target, 
              result=f"{severity}: {title}", status="vulnerability_found")
    return filepath

def update_metrics(entry):
    """Update Huntr metrics file."""
    metrics = {}
    if METRICS_FILE.exists():
        try:
            metrics = json.loads(METRICS_FILE.read_text())
        except:
            metrics = {"actions": [], "vulns": [], "targets": {}}
    
    metrics.setdefault("actions", []).append(entry["timestamp"])
    metrics.setdefault("vulns", []).append(entry) if entry.get("status") == "vulnerability_found" else None
    metrics["last_updated"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    METRICS_FILE.write_text(json.dumps(metrics, indent=2))

def show_status():
    """Show current Huntr process status."""
    print("\n🎯 HUNTR PROCESS STATUS")
    print("="*50)
    
    # Count today's actions
    today = datetime.utcnow().strftime("%Y-%m-%d")
    logfile = WORKFLOWS / f"huntr_{today}.jsonl"
    
    actions = 0
    vulns = 0
    if logfile.exists():
        with open(logfile) as f:
            for line in f:
                actions += 1
                if "vulnerability_found" in line:
                    vulns += 1
    
    print(f"📅 Today ({today}):")
    print(f"  Actions logged: {actions}")
    print(f"  Vulnerabilities found: {vulns}")
    
    # Count all vulns
    vuln_files = list(RESEARCH.glob("vuln_*.md"))
    print(f"\n🐛 Total vulnerability reports: {len(vuln_files)}")
    
    # ChromaDB status
    try:
        import chromadb
        c = chromadb.PersistentClient(path=str(Path(__file__).parent.parent / "var" / "chromadb"))
        col = c.get_or_create_collection("knowledge_base")
        print(f"📚 ChromaDB documents: {col.count()}")
    except:
        print("📚 ChromaDB: not available")
    
    print("="*50)

def show_today_report():
    """Show detailed report for today."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    logfile = WORKFLOWS / f"huntr_{today}.jsonl"
    
    if not logfile.exists():
        print(f"No actions logged today ({today})")
        return
    
    print(f"\n📋 TODAY'S REPORT — {today}")
    print("="*60)
    
    with open(logfile) as f:
        for line in f:
            entry = json.loads(line)
            ts = entry.get("timestamp", "?")[:19]
            agent = entry.get("agent", "?")
            action = entry.get("action", "?")
            tool = entry.get("tool", "")
            target = entry.get("target", "")
            status = entry.get("status", "?")
            
            icon = "✅" if status == "success" else "🐛" if "vuln" in status else "❌"
            print(f"{icon} [{ts}] {agent}: {action} ({tool}) → {target}")
            if entry.get("result"):
                print(f"   Result: {entry['result'][:100]}")
    
    print("="*60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Huntr Bug Bounty Logger")
    parser.add_argument("--log", type=str, help="Log an action")
    parser.add_argument("--agent", type=str, default="unknown", help="Agent name")
    parser.add_argument("--tool", type=str, default="", help="Tool used")
    parser.add_argument("--target", type=str, default="", help="Target")
    parser.add_argument("--result", type=str, default="", help="Result")
    parser.add_argument("--status", type=str, default="success", help="Status")
    parser.add_argument("--vuln", type=str, help="Log vulnerability")
    parser.add_argument("--severity", type=str, default="MEDIUM", help="Severity")
    parser.add_argument("--poc", type=str, default="", help="Proof of Concept")
    parser.add_argument("--bounty", type=str, default="", help="Bounty estimate")
    parser.add_argument("--today", action="store_true", help="Show today's report")
    parser.add_argument("--status-only", action="store_true", help="Show status")
    args = parser.parse_args()
    
    if args.vuln:
        log_vulnerability(args.agent, args.vuln, args.severity, args.target, 
                         description=args.result, poc=args.poc, bounty=args.bounty)
    elif args.log:
        log_action(args.agent, args.log, args.tool, args.target, args.result, args.status)
    elif args.today:
        show_today_report()
    elif args.status_only:
        show_status()
    else:
        print("Usage:")
        print("  python3 huntr_logger.py --log 'action' --agent qwen --tool nuclei --target x.com")
        print("  python3 huntr_logger.py --vuln 'XSS found' --severity HIGH --target https://x.com")
        print("  python3 huntr_logger.py --today")
        print("  python3 huntr_logger.py --status-only")
