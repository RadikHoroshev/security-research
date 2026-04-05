#!/usr/bin/env python3
"""
Task Router — маршрутизация задач по агентам на основе:
- Типа задачи (coding, research, shell, deploy, security)
- Сложности (simple, medium, complex, critical)
- Бюджета агента (сколько токенов осталось)
- Стоимости агента ($/M tokens)

Принцип: простые задачи → дешёвые агенты, сложные → умные агенты
"""

import json
import os
from dataclasses import dataclass, field
from typing import Optional

# =============================================================================
# Конфигурация маршрутизации
# =============================================================================

# Уровень сложности задачи
COMPLEXITY_SIMPLE   = "simple"
COMPLEXITY_MEDIUM   = "medium"
COMPLEXITY_COMPLEX  = "complex"
COMPLEXITY_CRITICAL = "critical"

# Тип задачи
TYPE_CODING    = "coding"
TYPE_RESEARCH  = "research"
TYPE_SHELL     = "shell"
TYPE_DEPLOY    = "deploy"
TYPE_SECURITY  = "security"
TYPE_DOC       = "documentation"
TYPE_DEBUG     = "debugging"
TYPE_REVIEW    = "review"
TYPE_GENERAL   = "general"

# Агент: имя, стоимость $/M input, $/M output, max контекст
@dataclass
class AgentInfo:
    name: str
    cost_input_per_m: float   # $ per 1M input tokens
    cost_output_per_m: float  # $ per 1M output tokens
    max_context: int          # max context tokens
    capabilities: list        # типы задач
    status: str = "online"
    monthly_budget_usd: Optional[float] = None
    tokens_remaining: Optional[int] = None
    priority: int = 1         # 1 =首选, 2 = fallback, 3 = last resort


# =============================================================================
# Матрица агентов (стоимость + возможности)
# =============================================================================

AGENTS = {
    # === БЕСПЛАТНЫЕ (локальные) —首选 для простых задач ===
    "ollama_gemma4": AgentInfo(
        name="Ollama Gemma 4",
        cost_input_per_m=0.00,
        cost_output_per_m=0.00,
        max_context=8192,
        capabilities=[TYPE_GENERAL, TYPE_SHELL, TYPE_DOC],
        status="online",
        priority=1  #首选 — бесплатно!
    ),

    "ollama_qwen14b": AgentInfo(
        name="Ollama Qwen 14B",
        cost_input_per_m=0.00,
        cost_output_per_m=0.00,
        max_context=32768,
        capabilities=[TYPE_CODING, TYPE_REVIEW, TYPE_DEBUG, TYPE_SHELL],
        status="online",
        priority=1  #首选 — бесплатно + код!
    ),

    "ollama_deepseek": AgentInfo(
        name="Ollama DeepSeek R1",
        cost_input_per_m=0.00,
        cost_output_per_m=0.00,
        max_context=8192,
        capabilities=[TYPE_RESEARCH, TYPE_GENERAL],
        status="online",
        priority=1  #首选 — бесплатно + reasoning!
    ),

    # === ДЕШЁВЫЕ ($0.15-0.30/M) — для средних задач ===
    "gemini_cli": AgentInfo(
        name="Gemini CLI",
        cost_input_per_m=0.15,
        cost_output_per_m=0.60,
        max_context=1000000,
        capabilities=[TYPE_GENERAL, TYPE_RESEARCH, TYPE_CODING, TYPE_DOC, TYPE_DEBUG],
        status="online",
        monthly_budget_usd=0.00,  # free tier
        priority=2
    ),

    "qwen_code": AgentInfo(
        name="Qwen Code",
        cost_input_per_m=0.30,
        cost_output_per_m=0.60,
        max_context=256000,
        capabilities=[TYPE_CODING, TYPE_REVIEW, TYPE_DEBUG, TYPE_SHELL, TYPE_DEPLOY, TYPE_SECURITY],
        status="online",
        monthly_budget_usd=10.00,
        priority=2
    ),

    # === СРЕДНИЕ ($0.50-2.00/M) — для сложных задач ===
    "warp_kimi": AgentInfo(
        name="WARP (Kimi)",
        cost_input_per_m=0.00,  # подписка — нужно уточнить
        cost_output_per_m=0.00,
        max_context=0,  # TODO: узнать у WARP
        capabilities=[TYPE_GENERAL, TYPE_CODING, TYPE_RESEARCH],
        status="unknown",  # TODO: проверить
        priority=2
    ),

    "copilot_cli": AgentInfo(
        name="Copilot CLI",
        cost_input_per_m=0.00,  # GitHub Pro подписка
        cost_output_per_m=0.00,
        max_context=8192,
        capabilities=[TYPE_SHELL],
        status="online",
        priority=2
    ),

    # === ДОРОГИЕ ($75-150/M) — только для критичных задач ===
    "codex_cli": AgentInfo(
        name="Codex CLI",
        cost_input_per_m=75.00,
        cost_output_per_m=150.00,
        max_context=128000,
        capabilities=[TYPE_REVIEW, TYPE_CODING, TYPE_SECURITY],
        status="online",
        monthly_budget_usd=5.00,
        priority=3  # last resort — дорого!
    ),

    # === АСИНХРОННЫЕ — для больших задач ===
    "jules": AgentInfo(
        name="Jules",
        cost_input_per_m=0.00,  # Google API
        cost_output_per_m=0.00,
        max_context=200000,
        capabilities=[TYPE_CODING, TYPE_REVIEW, TYPE_DEBUG],
        status="online",
        priority=2  # async — хорош для больших задач
    ),
}


# =============================================================================
# Правила маршрутизации по типу + сложности
# =============================================================================

ROUTING_RULES = {
    # Простые задачи → бесплатные локальные
    (TYPE_GENERAL,  COMPLEXITY_SIMPLE):  ["ollama_gemma4", "gemini_cli"],
    (TYPE_SHELL,    COMPLEXITY_SIMPLE):  ["ollama_gemma4", "copilot_cli", "gemini_cli"],
    (TYPE_DOC,      COMPLEXITY_SIMPLE):  ["ollama_gemma4", "gemini_cli"],

    # Средние → дешёвые облачные
    (TYPE_CODING,   COMPLEXITY_SIMPLE):  ["ollama_qwen14b", "gemini_cli"],
    (TYPE_CODING,   COMPLEXITY_MEDIUM):  ["qwen_code", "ollama_qwen14b", "jules"],
    (TYPE_RESEARCH, COMPLEXITY_MEDIUM):  ["gemini_cli", "ollama_deepseek"],
    (TYPE_DEBUG,    COMPLEXITY_MEDIUM):  ["qwen_code", "ollama_qwen14b"],
    (TYPE_REVIEW,   COMPLEXITY_MEDIUM):  ["ollama_qwen14b", "qwen_code"],

    # Сложные → мощные
    (TYPE_CODING,   COMPLEXITY_COMPLEX): ["qwen_code", "jules", "warp_kimi"],
    (TYPE_SECURITY, COMPLEXITY_COMPLEX): ["qwen_code", "codex_cli"],
    (TYPE_DEPLOY,   COMPLEXITY_COMPLEX): ["qwen_code"],
    (TYPE_RESEARCH, COMPLEXITY_COMPLEX): ["gemini_cli", "warp_kimi"],

    # Критичные → лучшие (даже дорогие)
    (TYPE_CODING,   COMPLEXITY_CRITICAL): ["qwen_code", "codex_cli", "jules"],
    (TYPE_SECURITY, COMPLEXITY_CRITICAL): ["codex_cli", "qwen_code"],
    (TYPE_REVIEW,   COMPLEXITY_CRITICAL): ["codex_cli", "qwen_code"],
}

# Классификатор задач по ключевым словам
KEYWORD_CLASSIFIER = {
    TYPE_CODING:   ["напиши", "создай", "функци", "класс", "код", "имплемент", "рефактор", "write", "code", "function", "class", "implement"],
    TYPE_RESEARCH: ["исслед", "найди", "CVE", "уязвим", "документ", "search", "research", "find", "vulnerability"],
    TYPE_SHELL:    ["команд", "запусти", "скрипт", "bash", "shell", "command", "run", "script"],
    TYPE_SECURITY: ["безопасн", "скан", "аудит", "security", "scan", "audit", "vuln", "exploit"],
    TYPE_DEBUG:    ["баг", "ошибк", "почему", "debug", "bug", "error", "fix", "почини"],
    TYPE_REVIEW:   ["ревью", "проверь", "анализ", "review", "check", "analyze"],
    TYPE_DEPLOY:   ["деплой", "разверн", "deploy", "launch", "push"],
    TYPE_DOC:      ["документ", "описани", "прочитай", "doc", "read", "describe"],
}


# =============================================================================
# API маршрутизатора
# =============================================================================

def classify_task(description: str) -> str:
    """Классифицирует задачу по ключевым словам."""
    text = description.lower()
    scores = {}
    for task_type, keywords in KEYWORD_CLASSIFIER.items():
        scores[task_type] = sum(1 for kw in keywords if kw in text)

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return TYPE_GENERAL
    return best


def estimate_complexity(description: str) -> str:
    """Оценивает сложность задачи по описанию."""
    text = description.lower()
    length = len(text)

    # Ключевые маркеры сложности
    complex_markers = ["архитектур", "весь проект", "полный аудит", "refactor all",
                       "entire codebase", "complete audit", "critical", "production"]
    medium_markers = ["модуль", "несколько файл", "multi-file", "компонент", "feature"]

    for marker in complex_markers:
        if marker in text:
            return COMPLEXITY_COMPLEX

    for marker in medium_markers:
        if marker in text:
            return COMPLEXITY_MEDIUM

    if length > 500:
        return COMPLEXITY_COMPLEX
    elif length > 200:
        return COMPLEXITY_MEDIUM
    else:
        return COMPLEXITY_SIMPLE


def route_task(description: str, budget_file: str = None) -> dict:
    """
    Маршрутизирует задачу к лучшему агенту.

    Returns:
        {
            "task_type": "coding",
            "complexity": "medium",
            "primary_agent": "qwen_code",
            "fallback_agents": ["ollama_qwen14b", "jules"],
            "estimated_cost_usd": 0.15,
            "reason": "..."
        }
    """
    task_type = classify_task(description)
    complexity = estimate_complexity(description)

    # Получаем список агентов из правил
    rule_key = (task_type, complexity)
    agent_names = ROUTING_RULES.get(rule_key, ROUTING_RULES.get((TYPE_GENERAL, complexity), ["ollama_gemma4"]))

    # Фильтруем по бюджету
    available = []
    for name in agent_names:
        agent = AGENTS.get(name)
        if not agent or agent.status != "online":
            continue

        # Проверяем бюджет
        if budget_file and agent.monthly_budget_usd:
            try:
                with open(budget_file) as f:
                    budget = json.load(f)
                usage = budget["agents"].get(name, {}).get("usage_current_period", {})
                spent = usage.get("cost_usd", 0)
                if spent >= agent.monthly_budget_usd:
                    continue  # бюджет исчерпан
            except (FileNotFoundError, json.JSONDecodeError):
                pass

        available.append(agent)

    if not available:
        # Fallback на бесплатный Ollama
        available = [AGENTS["ollama_qwen14b"]]

    primary = available[0]
    fallbacks = [a.name for a in available[1:]]

    # Оценка стоимости (грубо: 5K input + 2K output для medium)
    multipliers = {
        COMPLEXITY_SIMPLE:  (1000, 500),
        COMPLEXITY_MEDIUM:  (5000, 2000),
        COMPLEXITY_COMPLEX: (20000, 8000),
    }
    input_tokens, output_tokens = multipliers.get(complexity, (5000, 2000))
    estimated_cost = (primary.cost_input_per_m * input_tokens / 1_000_000 +
                     primary.cost_output_per_m * output_tokens / 1_000_000)

    return {
        "task_type": task_type,
        "complexity": complexity,
        "primary_agent": primary.name,
        "primary_agent_key": list(AGENTS.keys())[list(AGENTS.values()).index(primary)],
        "fallback_agents": fallbacks,
        "estimated_cost_usd": round(estimated_cost, 4),
        "estimated_tokens": {
            "input": input_tokens,
            "output": output_tokens
        },
        "reason": f"{complexity} {task_type} → {primary.name} (${primary.cost_input_per_m}/$0.00 per M tokens)"
    }


def print_routing(description: str, budget_file: str = None):
    """Красивый вывод маршрутизации."""
    result = route_task(description, budget_file)
    print(f"\n{'='*60}")
    print(f"📋 МАРШРУТИЗАЦИЯ ЗАДАЧИ")
    print(f"{'='*60}")
    print(f"Задача: {description[:80]}...")
    print(f"Тип:    {result['task_type']}")
    print(f"Сложность: {result['complexity']}")
    print(f"")
    print(f"🎯 Основной агент: {result['primary_agent']}")
    print(f"💰 Оценка стоимости: ${result['estimated_cost_usd']}")
    print(f"📊 Токены: ~{result['estimated_tokens']['input']} input + ~{result['estimated_tokens']['output']} output")
    if result['fallback_agents']:
        print(f"🔄 Fallback: {', '.join(result['fallback_agents'])}")
    print(f"Причина: {result['reason']}")
    print(f"{'='*60}\n")
    return result


def print_budget_status(budget_file: str = None):
    """Показывает статус бюджета всех агентов."""
    if not budget_file:
        budget_file = os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "token_budget.json")

    try:
        with open(budget_file) as f:
            budget = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️  Файл бюджета не найден")
        return

    print(f"\n{'='*60}")
    print(f"💰 СТАТУС БЮДЖЕТА — {budget.get('current_period', 'N/A')}")
    print(f"{'='*60}")

    for agent_key, agent_data in budget.get("agents", {}).items():
        usage = agent_data.get("usage_current_period", {})
        pricing = agent_data.get("pricing", {})
        monthly = agent_data.get("monthly_budget", {})

        tokens = usage.get("total_tokens", 0)
        cost = usage.get("cost_usd", 0)
        calls = usage.get("calls_count", 0)

        limit_usd = monthly.get("limit_usd")
        limit_tokens = monthly.get("limit_tokens")

        status_icon = "🟢"
        if limit_usd and cost > 0:
            pct = cost / limit_usd * 100
            if pct > 90:
                status_icon = "🔴"
            elif pct > 70:
                status_icon = "🟡"

        cost_str = f"${cost:.4f}" if cost is not None else "подписка"
        limit_str = f"${limit_usd}" if limit_usd else "∞"

        print(f"{status_icon} {agent_data['name']}")
        print(f"   Потрачено: {cost_str} / {limit_str}  |  Токены: {tokens:,}  |  Вызовы: {calls}")
        if pricing.get("notes"):
            print(f"   📝 {pricing['notes']}")
        print()

    print(f"{'='*60}")
    remaining = budget.get("budget_summary", {}).get("days_remaining", "?")
    print(f"Дней в периоде осталось: {remaining}")
    print(f"{'='*60}\n")


# =============================================================================
# CLI интерфейс
# =============================================================================

if __name__ == "__main__":
    import sys

    budget_file = os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "token_budget.json")

    if len(sys.argv) < 2:
        print("Использование:")
        print(f"  python3 task_router.py 'описание задачи'  — маршрутизация")
        print(f"  python3 task_router.py --budget           — статус бюджета")
        print(f"  python3 task_router.py --classify 'текст' — классификация")
        sys.exit(0)

    if sys.argv[1] == "--budget":
        print_budget_status(budget_file)
    elif sys.argv[1] == "--classify":
        text = " ".join(sys.argv[2:])
        task_type = classify_task(text)
        complexity = estimate_complexity(text)
        print(f"Тип: {task_type}, Сложность: {complexity}")
    else:
        description = " ".join(sys.argv[1:])
        print_routing(description, budget_file)
