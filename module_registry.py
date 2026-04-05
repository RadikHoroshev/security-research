#!/usr/bin/env python3.11
"""
module_registry.py — Реестр модулей мульти-агентной системы

Каждый агент/сервис = независимый модуль.
Модули можно включать/выключать/заменять на лету БЕЗ перезапуска системы.

Архитектура:
  ┌─────────────────────────────────────────────────────────┐
  │                    MODULE REGISTRY                       │
  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────────────┐ │
  │  │ Ollama  │ │ Proxy   │ │ Panel   │ │ SecurityTeam  │ │
  │  │ (core)  │ │ (core)  │ │ (opt)   │ │ (opt)         │ │
  │  └─────────┘ └─────────┘ └─────────┘ └───────────────┘ │
  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────────────┐ │
  │  │Anything │ │ Obsidian│ │ Copilot │ │ RAG Engine    │ │
  │  │  LLM    │ │         │ │         │ │               │ │
  │  └─────────┘ └─────────┘ └─────────┘ └───────────────┘ │
  └─────────────────────────────────────────────────────────┘

Когда модуль падает:
  1. Registry помечает его offline
  2. Fallback agent автоматически назначается
  3. Задачи перераспределяются
  4. При повторном подключении — автоматическая регистрация
"""

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# ═══════════════════════════════════════════════════════════
# РЕЕСТР МОДУЛЕЙ
# ═══════════════════════════════════════════════════════════

REGISTRY_FILE = os.path.expanduser("~/project/knowledge_base/module_registry.json")

class ModuleRegistry:
    def __init__(self):
        self.modules = {}
        self.fallbacks = {}
        self.load()

    # ── Определения модулей ────────────────────────────────

    DEFAULT_MODULES = {
        # ── CORE (система не работает без них) ──
        "ollama": {
            "name": "Ollama",
            "type": "core",
            "port": 11434,
            "health_cmd": "curl -s http://localhost:11434/api/tags",
            "fallback": None,  # core — нет fallback
            "capabilities": ["local_models", "inference"],
            "restart_cmd": "ollama serve",
        },
        "proxy": {
            "name": "API Proxy",
            "type": "core",
            "port": 8768,
            "health_cmd": "curl -s http://localhost:8768/status",
            "fallback": None,
            "capabilities": ["api_routing", "key_injection"],
            "restart_cmd": "python3 ~/.secrets/simple_proxy.py &",
        },
        "anythingllm": {
            "name": "AnythingLLM RAG",
            "type": "core",
            "port": 3001,
            "health_cmd": "curl -s http://localhost:3001/api/v1/auth",
            "fallback": "obsidian",  # если RAG упал — ищем в Obsidian
            "capabilities": ["rag_search", "knowledge_base", "embeddings"],
            "restart_cmd": "open -a AnythingLLM",
        },

        # ── OPTIONAL (система работает без них) ──
        "panel": {
            "name": "Security Panel",
            "type": "optional",
            "port": 8765,
            "health_cmd": "curl -s http://localhost:8765/healthz",
            "fallback": None,
            "capabilities": ["security_dashboard"],
            "restart_cmd": "python3 ~/project/security-team/panel_server.py &",
        },
        "security_team": {
            "name": "Security Team",
            "type": "optional",
            "port": None,
            "health_cmd": "python3 ~/project/security-team/dev_env.py doctor --json",
            "fallback": "copilot",  # если Security Team упал — Copilot поможет
            "capabilities": ["vuln_scanning", "code_audit", "recon"],
            "restart_cmd": "cd ~/project/security-team && python3 dev_env.py start",
        },
        "copilot": {
            "name": "GitHub Copilot CLI",
            "type": "optional",
            "port": None,
            "health_cmd": "copilot --version",
            "fallback": "qwen_cli",  # если Copilot упал — Qwen CLI
            "capabilities": ["shell_suggest", "command_explain", "git_help"],
            "restart_cmd": None,  # CLI — не демон
        },
        "obsidian": {
            "name": "Obsidian Vault",
            "type": "optional",
            "port": None,
            "health_cmd": "test -d ~/Documents/Obsidian\\ Vault",
            "fallback": None,
            "capabilities": ["knowledge_base", "notes", "graph"],
            "restart_cmd": "open -a Obsidian",
        },
        "ramdisk": {
            "name": "RAM Disk",
            "type": "optional",
            "port": None,
            "health_cmd": "mount | grep -q AgentRAM",
            "fallback": None,
            "capabilities": ["fast_storage", "temp_files"],
            "restart_cmd": "bash ~/project/scripts/ramdisk.sh mount",
        },
    }

    # ── Fallback цепи для агентов ──────────────────────────
    # Если агент недоступен → задачи идут на fallback
    AGENT_FALLBACK_CHAINS = {
        "coding": [
            {"agent": "qwen2.5-coder:14b", "type": "ollama", "model": "qwen2.5-coder:14b"},
            {"agent": "qwen2.5-coder:7b", "type": "ollama", "model": "qwen2.5-coder:7b"},
            {"agent": "qwen_cli", "type": "cloud", "model": None},
            {"agent": "copilot", "type": "cloud", "model": "gpt-5-mini"},
        ],
        "reasoning": [
            {"agent": "deepseek-r1:8b", "type": "ollama", "model": "deepseek-r1:8b"},
            {"agent": "qwen_cli", "type": "cloud", "model": None},
            {"agent": "gemini_cli", "type": "cloud", "model": None},
        ],
        "general": [
            {"agent": "gemma4:latest", "type": "ollama", "model": "gemma4:latest"},
            {"agent": "gemini_cli", "type": "cloud", "model": None},
            {"agent": "qwen2.5-coder:7b", "type": "ollama", "model": "qwen2.5-coder:7b"},
        ],
        "heavy": [
            {"agent": "qwen3.5:cloud", "type": "ollama", "model": "qwen3.5:cloud"},
            {"agent": "qwen_cli", "type": "cloud", "model": None},
            {"agent": "claude_desktop", "type": "on_demand", "model": None},
        ],
    }

    # ── Загрузка/сохранение ────────────────────────────────

    def load(self):
        if os.path.exists(REGISTRY_FILE):
            with open(REGISTRY_FILE, "r") as f:
                data = json.load(f)
                self.modules = data.get("modules", {})
                self.fallbacks = data.get("fallback_chains", self.AGENT_FALLBACK_CHAINS)
        else:
            # Инициализация из дефолтов
            self.modules = {}
            for name, config in self.DEFAULT_MODULES.items():
                self.modules[name] = {
                    **config,
                    "status": "unknown",
                    "last_check": None,
                    "uptime": None,
                    "failure_count": 0,
                    "last_error": None,
                }
            self.fallbacks = dict(self.AGENT_FALLBACK_CHAINS)
            self.save()

    def save(self):
        os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)
        data = {
            "updated": datetime.now().isoformat(),
            "modules": self.modules,
            "fallback_chains": self.fallbacks,
        }
        with open(REGISTRY_FILE, "w") as f:
            json.dump(data, f, indent=2)

    # ── Health Check ───────────────────────────────────────

    def check_module(self, name: str) -> dict:
        """Проверить здоровье одного модуля."""
        if name not in self.modules:
            return {"status": "unknown", "error": "Module not found"}

        mod = self.modules[name]
        health_cmd = mod.get("health_cmd")
        if not health_cmd:
            return {"status": "unknown", "error": "No health check"}

        start = time.time()
        try:
            result = subprocess.run(
                health_cmd.split(), capture_output=True,
                text=True, timeout=10
            )
            elapsed = time.time() - start

            if result.returncode == 0:
                mod["status"] = "online"
                mod["last_check"] = datetime.now().isoformat()
                mod["last_response_ms"] = round(elapsed * 1000, 1)
                mod["failure_count"] = 0
            else:
                mod["status"] = "offline"
                mod["last_error"] = result.stderr[:200]
                mod["failure_count"] = mod.get("failure_count", 0) + 1
                # Если слишком много ошибок — авто-fallback
                if mod["failure_count"] >= 3 and mod.get("fallback"):
                    mod["status"] = "fallback_active"
                    fallback_name = mod["fallback"]
                    mod["last_error"] += f" → Fallback to {fallback_name}"
        except subprocess.TimeoutExpired:
            mod["status"] = "timeout"
            mod["last_error"] = f"Health check timed out (>10s)"
            mod["failure_count"] = mod.get("failure_count", 0) + 1
        except Exception as e:
            mod["status"] = "error"
            mod["last_error"] = str(e)[:200]
            mod["failure_count"] = mod.get("failure_count", 0) + 1

        self.save()
        return mod

    def check_all(self) -> dict:
        """Проверить все модули."""
        results = {}
        for name in self.modules:
            results[name] = self.check_module(name)
        return results

    # ── Fallback логика ────────────────────────────────────

    def get_available_agent(self, task_type: str) -> Optional[dict]:
        """
        Получить первый доступный агент для типа задачи.
        Автоматически проходит fallback chain.
        """
        chain = self.fallbacks.get(task_type, [])
        if not chain:
            return None

        for agent_config in chain:
            agent_type = agent_config["type"]

            # Проверяем доступность
            if agent_type == "ollama":
                model = agent_config["model"]
                if self._ollama_model_available(model):
                    return agent_config

            elif agent_type == "cloud":
                # Cloud CLI — проверяем что установлен
                if agent_config["agent"] in ["qwen_cli", "copilot", "gemini_cli"]:
                    if self._cli_available(agent_config["agent"]):
                        return agent_config

            elif agent_type == "on_demand":
                # On-demand — проверяем наличие
                if agent_config["agent"] == "claude_desktop":
                    if os.path.exists("/Applications/Claude.app"):
                        return agent_config

        return None

    def _ollama_model_available(self, model: str) -> bool:
        try:
            r = subprocess.run(
                ["ollama", "list"], capture_output=True, text=True, timeout=5
            )
            return model in r.stdout if r.returncode == 0 else False
        except Exception:
            return False

    def _cli_available(self, agent: str) -> bool:
        commands = {
            "qwen_cli": "qwen",
            "copilot": "copilot",
            "gemini_cli": "gemini",
        }
        cmd = commands.get(agent)
        if not cmd:
            return False
        return subprocess.run(
            ["which", cmd], capture_output=True, text=True
        ).returncode == 0

    # ── Динамическое добавление/удаление модулей ──────────

    def register_module(self, name: str, config: dict):
        """Зарегистрировать новый модуль (hot-swap)."""
        self.modules[name] = {
            **config,
            "status": "unknown",
            "last_check": None,
            "failure_count": 0,
            "registered_at": datetime.now().isoformat(),
        }
        self.save()

    def unregister_module(self, name: str):
        """Отключить модуль (hot-remove)."""
        if name in self.modules:
            del self.modules[name]
            self.save()

    # ── Статус ─────────────────────────────────────────────

    def get_status(self) -> dict:
        """Полный статус системы."""
        self.check_all()

        online = sum(1 for m in self.modules.values() if m["status"] == "online")
        offline = sum(1 for m in self.modules.values() if m["status"] in ["offline", "error", "timeout"])
        fallback = sum(1 for m in self.modules.values() if m["status"] == "fallback_active")

        return {
            "total": len(self.modules),
            "online": online,
            "offline": offline,
            "fallback_active": fallback,
            "modules": {
                name: {
                    "status": m["status"],
                    "type": m["type"],
                    "port": m.get("port"),
                    "failure_count": m.get("failure_count", 0),
                    "last_error": (m.get("last_error") or "")[:100],
                }
                for name, m in self.modules.items()
            },
            "updated": datetime.now().isoformat(),
        }


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    registry = ModuleRegistry()

    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "status":
        status = registry.get_status()
        print(f"\n📊 Модули: {status['online']}/{status['total']} онлайн")
        if status['fallback_active']:
            print(f"⚠️ Fallback активных: {status['fallback_active']}")
        print(f"{'─' * 50}")
        for name, info in status["modules"].items():
            icon = {"online": "✅", "offline": "❌", "error": "💥", "timeout": "⏱️", "fallback_active": "🔄"}.get(info["status"], "❓")
            port_info = f":{info['port']}" if info.get('port') else ""
            print(f"  {icon} {name:<20} {info['status']} {port_info}")
            if info.get("failure_count", 0) > 0:
                print(f"     ⚠️ Ошибок: {info['failure_count']} | {info.get('last_error', '')[:80]}")
        print(f"{'─' * 50}")

    elif cmd == "check":
        name = sys.argv[2] if len(sys.argv) > 2 else None
        if name:
            result = registry.check_module(name)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            registry.check_all()
            print("✅ Все модули проверены")

    elif cmd == "available":
        task = sys.argv[2] if len(sys.argv) > 2 else "coding"
        agent = registry.get_available_agent(task)
        if agent:
            print(f"✅ Доступный агент для '{task}': {agent['agent']} ({agent['type']})")
        else:
            print(f"❌ Нет доступных агентов для '{task}'")
            print(f"   Fallback chain: {[a['agent'] for a in registry.fallbacks.get(task, [])]}")

    elif cmd == "fallbacks":
        print("\n🔄 Fallback цепи:")
        for task_type, chain in registry.fallbacks.items():
            agents = [a["agent"] for a in chain]
            print(f"  {task_type}: {' → '.join(agents)}")

    elif cmd == "register":
        # python3 module_registry.py register my_module '{"port": 9999, ...}'
        if len(sys.argv) < 4:
            print("Использование: register <name> '<json_config>'")
            sys.exit(1)
        name = sys.argv[2]
        config = json.loads(sys.argv[3])
        registry.register_module(name, config)
        print(f"✅ Модуль '{name}' зарегистрирован")

    else:
        print("Использование: module_registry.py [status|check|available|fallbacks|register]")
