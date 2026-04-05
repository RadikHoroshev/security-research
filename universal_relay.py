#!/usr/bin/env python3
"""universal_relay.py — Fault-tolerant inter-agent communication"""
import subprocess, json, time, hashlib, socket, urllib.request, sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
OUTBOX = ROOT / "intel" / "outbox"
INBOX = ROOT / "intel" / "inbox"
LOG = ROOT / "knowledge_base" / "universal_relay.log"

def _log(m):
    t = datetime.utcnow().strftime('%H:%M:%S')
    print(f"  [{t}] {m}")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f: f.write(f"[{datetime.utcnow().isoformat()}Z] {m}\n")

def _cmd(c):
    try: return subprocess.run(c, capture_output=True).returncode == 0
    except: return False

def _port(p):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(2)
        r = s.connect_ex(('localhost', p)); s.close(); return r == 0
    except: return False

def _send_goose(agent, task, timeout):
    r = subprocess.run(["goose", "run", "-t", f"Task for {agent}: {task}\nSave to: intel/inbox/{agent}_result.md"],
        capture_output=True, text=True, timeout=timeout)
    return r.stdout

def _send_file(agent, task, timeout):
    OUTBOX.mkdir(parents=True, exist_ok=True); INBOX.mkdir(parents=True, exist_ok=True)
    tid = hashlib.md5(f"{agent}-{task}-{time.time()}".encode()).hexdigest()[:8]
    (OUTBOX / f"{agent}_{tid}.md").write_text(f"# Task\n\n{task}\n\nSave: intel/inbox/{agent}_result_{tid}.md")
    for _ in range(timeout // 5):
        r = list(INBOX.glob(f"{agent}_result_{tid}*"))
        if r: return r[0].read_text()
        time.sleep(5)
    return f"Timeout"

def _send_cli(agent, task, timeout):
    cmds = {
        "qwen": ["qwen", "-y", "-p", task],
        "gemini": ["gemini", "-p", task, "--yolo"],
        "codex": ["codex", "exec", "--skip-git-repo-check", task],
        "jules": ["jules", "new", "--repo", "RadikHoroshev/multi-agent-system", task],
    }
    c = cmds.get(agent)
    if not c: raise ValueError(f"No CLI for {agent}")
    r = subprocess.run(c, capture_output=True, text=True, timeout=timeout)
    return r.stdout or r.stderr

def _send_ollama(agent, task, timeout):
    models = {"qwen": "qwen2.5-coder:14b", "gemini": "gemma4:latest"}
    m = models.get(agent, "gemma4:latest")
    d = json.dumps({"model": m, "prompt": task, "stream": False}).encode()
    req = urllib.request.Request("http://localhost:11434/api/generate", data=d, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read()).get("response", "")

CHANNELS = {
    "goose_relay": {"p": 1, "test": lambda: _cmd(["goose", "--version"]), "send": _send_goose, "to": 120},
    "file_relay":  {"p": 2, "test": lambda: OUTBOX.exists() and INBOX.exists(), "send": _send_file, "to": 300},
    "direct_cli":  {"p": 3, "test": lambda: True, "send": _send_cli, "to": 60},
    "ollama_api":  {"p": 4, "test": lambda: _port(11434), "send": _send_ollama, "to": 30},
}

AGENTS = {
    "qwen": {"type": "cli", "fb": ["ollama_qwen14b"]},
    "gemini": {"type": "cli", "fb": ["ollama_gemma4"]},
    "codex": {"type": "cli", "fb": ["qwen"]},
    "jules": {"type": "async", "fb": ["qwen"]},
}

def send(agent, task, channel=None, timeout=None):
    t0 = time.time()
    chs = [channel] if channel else [c for c in sorted(CHANNELS, key=lambda x: CHANNELS[x]["p"]) if CHANNELS[c]["test"]()]
    for ch in chs:
        cfg = CHANNELS.get(ch)
        if not cfg: continue
        try:
            r = cfg["send"](agent, task, timeout or cfg["to"])
            ms = int((time.time() - t0) * 1000)
            _log(f"OK {agent} via {ch} ({ms}ms)")
            return {"success": True, "channel": ch, "result": r, "latency_ms": ms, "error": None}
        except Exception as e:
            _log(f"FAIL {agent} via {ch}: {e}")
    ms = int((time.time() - t0) * 1000)
    return {"success": False, "channel": None, "result": None, "latency_ms": ms, "error": "All failed"}

def scan():
    avail, unavail = [], []
    for n, c in CHANNELS.items():
        try:
            if c["test"](): avail.append(n)
            else: unavail.append(n)
        except: unavail.append(n)
    return {"available": avail, "unavailable": unavail, "total": len(CHANNELS), "ok": len(avail)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: scan | send <agent> 'task' | agents")
        sys.exit(0)
    if sys.argv[1] == "scan":
        s = scan()
        print(f"\n📡 Channels: {s['ok']}/{s['total']}")
        for c in s['available']: print(f"  ✅ {c}")
        for c in s['unavailable']: print(f"  ❌ {c}")
    elif sys.argv[1] == "send":
        r = send(sys.argv[2], " ".join(sys.argv[3:]))
        print(f"\n{'✅' if r['success'] else '❌'} {r['channel']} ({r['latency_ms']}ms)")
        if r['result']: print(r['result'][:500])
    elif sys.argv[1] == "agents":
        for n, c in AGENTS.items(): print(f"  • {n} ({c['type']}) fb: {c['fb']}")
