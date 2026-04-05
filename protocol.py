#!/usr/bin/env python3
"""
protocol.py — Машинный протокол общения между агентами

Формат: однострочный JSON (compact, no spaces)
Каждая строка = одно событие

Типы сообщений:
  CMD    — команда одному или всем агентам
  RES    — результат выполнения
  ALERT  — предупреждение о сбое/галлюцинации
  STATUS — статус агента (online/degraded/offline/sick)
  QUARANTINE — агент помещён в карантин
  RECOVER — агент восстановлен

Примеры:
  {"t":"CMD","to":"warp","a":"audit","id":"cmd001","p":{"steps":["model","mcp","caps"]}}
  {"t":"RES","from":"warp","id":"cmd001","ok":true,"r":"Model: kimi-k2.5..."}
  {"t":"ALERT","from":"qwen","target":"gemini","type":"hallucination","m":"gave wrong API result"}
  {"t":"STATUS","from":"heartbeat","agents":{"qwen":"online","gemini":"sick","jules":"online"}}
"""

import json
import hashlib
import time
from pathlib import Path
from datetime import datetime

MSG_BUS = Path(__file__).parent / "msg_bus"
MSG_BUS.mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════════════
# ENCODE / DECODE
# ═══════════════════════════════════════════════════════════

def cmd(to: str, action: str, params: dict = None, msg_id: str = None) -> str:
    """Создать команду для агента."""
    return json.dumps({
        "t": "CMD",
        "to": to,
        "a": action,
        "id": msg_id or _uid(),
        "p": params or {},
        "ts": int(time.time())
    }, separators=(",", ":"))

def res(from_: str, msg_id: str, ok: bool, result: str = "", error: str = "") -> str:
    """Создать результат."""
    d = {"t": "RES", "from": from_, "id": msg_id, "ok": ok, "ts": int(time.time())}
    if result: d["r"] = result
    if error: d["e"] = error
    return json.dumps(d, separators=(",", ":"))

def alert(from_: str, target: str, atype: str, message: str) -> str:
    """Создать предупреждение о сбое."""
    return json.dumps({
        "t": "ALERT", "from": from_, "target": target,
        "a": atype, "m": message, "ts": int(time.time())
    }, separators=(",", ":"))

def status(from_: str, agents: dict) -> str:
    """Создать статус-сообщение."""
    return json.dumps({
        "t": "STATUS", "from": from_, "agents": agents, "ts": int(time.time())
    }, separators=(",", ":"))

def quarantine(agent: str, reason: str, duration_sec: int = 300) -> str:
    """Поместить агента в карантин."""
    return json.dumps({
        "t": "QUARANTINE", "agent": agent, "reason": reason,
        "dur": duration_sec, "ts": int(time.time())
    }, separators=(",", ":"))

def recover(agent: str) -> str:
    """Восстановить агента из карантина."""
    return json.dumps({
        "t": "RECOVER", "agent": agent, "ts": int(time.time())
    }, separators=(",", ":"))

# ═══════════════════════════════════════════════════════════
# MESSAGE BUS
# ═══════════════════════════════════════════════════════════

def send(msg: str):
    """Отправить сообщение в шину."""
    obj = json.loads(msg)  # validate
    fname = MSG_BUS / f"{obj.get('t','msg')}_{obj.get('id',_uid())}.json"
    fname.write_text(msg)

def send_file(msg: str, agent: str):
    """Отправить сообщение в inbox агента."""
    inbox = Path(__file__).parent.parent / "intel" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    (inbox / f"{agent}_{ts}.msg").write_text(msg)

def read_bus():
    """Прочитать все сообщения из шины."""
    msgs = []
    for f in sorted(MSG_BUS.glob("*.json")):
        try:
            msgs.append(json.loads(f.read_text()))
        except:
            pass
    return msgs

def clear_bus():
    """Очистить шину."""
    for f in MSG_BUS.glob("*.json"):
        f.unlink()

# ═══════════════════════════════════════════════════════════
# QUARANTINE MANAGER
# ═══════════════════════════════════════════════════════════

QUARANTINE_FILE = Path(__file__).parent / "quarantine.json"

def get_quarantine() -> dict:
    if QUARANTINE_FILE.exists():
        return json.loads(QUARANTINE_FILE.read_text())
    return {"agents": {}, "log": []}

def quarantine_agent(agent: str, reason: str, duration_sec: int = 300):
    q = get_quarantine()
    until = int(time.time()) + duration_sec
    q["agents"][agent] = {"until": until, "reason": reason, "reports": 0}
    q["log"].append({"agent": agent, "reason": reason, "until": until, "ts": int(time.time())})
    QUARANTINE_FILE.write_text(json.dumps(q, indent=2))

def check_quarantine() -> list:
    """Проверить и очистить истёкший карантин. Вернуть список sick агентов."""
    q = get_quarantine()
    now = int(time.time())
    sick = []
    freed = []
    for agent, info in list(q["agents"].items()):
        if info["until"] > now:
            sick.append(agent)
        else:
            freed.append(agent)
            del q["agents"][agent]
    if freed:
        q["log"].append({"freed": freed, "ts": now})
        QUARANTINE_FILE.write_text(json.dumps(q, indent=2))
    return sick

def is_sick(agent: str) -> bool:
    return agent in get_quarantine().get("agents", {})

def report_issue(reporter: str, target: str, issue: str):
    """Другой агент сообщает о проблеме."""
    q = get_quarantine()
    if target in q["agents"]:
        q["agents"][target]["reports"] = q["agents"][target].get("reports", 0) + 1
        reports = q["agents"][target]["reports"]
        # 3 репорта от разных агентов = удлиняем карантин
        if reports >= 3:
            q["agents"][target]["until"] = int(time.time()) + 600  # 10 мин
    QUARANTINE_FILE.write_text(json.dumps(q, indent=2))

# ═══════════════════════════════════════════════════════════
# INTERPRETER (для пользователя)
# ═══════════════════════════════════════════════════════════

TYPE_LABELS = {
    "CMD": "📤 Команда",
    "RES": "📥 Результат",
    "ALERT": "⚠️ Сбой",
    "STATUS": "📊 Статус",
    "QUARANTINE": "🔒 Карантин",
    "RECOVER": "✅ Восстановление"
}

def interpret(msg: str) -> str:
    """Перевести машинное сообщение в читаемый вид."""
    try:
        obj = json.loads(msg)
        t = obj.get("t", "?")
        label = TYPE_LABELS.get(t, t)
        ts = datetime.utcfromtimestamp(obj.get("ts", 0)).strftime("%H:%M:%S")

        if t == "CMD":
            return f"{label} [{ts}] → {obj['to']}: {obj['a']} params={obj.get('p',{})}"
        elif t == "RES":
            ok = "✅" if obj.get("ok") else "❌"
            r = obj.get("r", "")[:200]
            e = obj.get("e", "")
            return f"{label} [{ts}] {ok} от {obj['from']}: {r} {e}"
        elif t == "ALERT":
            return f"{label} [{ts}] {obj['from']} → {obj['target']}: {obj['a']} — {obj['m']}"
        elif t == "STATUS":
            agents = obj.get("agents", {})
            summary = ", ".join(f"{k}:{v}" for k, v in agents.items())
            return f"{label} [{ts}] {summary}"
        elif t == "QUARANTINE":
            return f"{label} [{ts}] {obj['agent']} — {obj['reason']} ({obj['dur']}s)"
        elif t == "RECOVER":
            return f"{label} [{ts}] {obj['agent']} вернулся в строй"
        else:
            return json.dumps(obj, indent=2)
    except:
        return f"[parse error] {msg[:200]}"

def interpret_all() -> list:
    """Прочитать и перевести все сообщения из шины."""
    return [interpret(f.read_text()) for f in sorted(MSG_BUS.glob("*.json"))]

# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def _uid():
    return hashlib.md5(f"{time.time()}".encode()).hexdigest()[:8]

# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Protocol — machine-to-machine agent communication")
        print()
        print("Commands:")
        print("  send   <json>      — send message to bus")
        print("  cmd    <agent> <action> [params]  — create + send command")
        print("  alert  <from> <to> <type> <message>  — send alert")
        print("  status <json>      — send status")
        print("  quarantine <agent> <reason> [seconds]  — quarantine agent")
        print("  check              — check quarantine")
        print("  read               — read bus")
        print("  interpret          — translate bus messages")
        print("  clear              — clear bus")
        sys.exit(0)

    sub = sys.argv[1]

    if sub == "send":
        send(" ".join(sys.argv[2:]))
        print("✅ sent")
    elif sub == "cmd":
        agent, action = sys.argv[2], sys.argv[3]
        params = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
        msg = cmd(agent, action, params)
        send(msg)
        print(f"✅ cmd → {agent}: {action}")
    elif sub == "alert":
        msg = alert(sys.argv[2], sys.argv[3], sys.argv[4], " ".join(sys.argv[5:]))
        send(msg)
        print("✅ alert sent")
    elif sub == "quarantine":
        agent = sys.argv[2]
        reason = sys.argv[3]
        dur = int(sys.argv[4]) if len(sys.argv) > 4 else 300
        msg = quarantine(agent, reason, dur)
        send(msg)
        quarantine_agent(agent, reason, dur)
        print(f"🔒 {agent} quarantined for {dur}s: {reason}")
    elif sub == "check":
        sick = check_quarantine()
        if sick:
            print(f"🔒 Sick agents: {', '.join(sick)}")
        else:
            print("✅ All agents healthy")
    elif sub == "read":
        msgs = read_bus()
        for m in msgs:
            print(json.dumps(m))
    elif sub == "interpret":
        for line in interpret_all():
            print(line)
    elif sub == "clear":
        clear_bus()
        print("✅ bus cleared")
