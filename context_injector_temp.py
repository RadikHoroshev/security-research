def call_agent_with_context(
    agent_type: str,
    task: str,
    agent_name: str = "agent",
    **kwargs
) -> dict:
    """
    Вызвать агента с автоматическим контекстом.

    agent_type: ollama | qwen_cli | gemini_cli | copilot | jules | shell
    task: задача
    agent_name: имя для логов
    """
    # Инжектируем контекст
    ctx = inject_context(task, agent_name)

    # Форми enriched prompt
    enriched_task = f"{ctx['context']}\n\nЗАДАЧА:\n{task}"

    # Вызываем агента
    if agent_type == "ollama":
        model = kwargs.get("model", "qwen2.5-coder:14b")
        result = subprocess.run(
            ["ollama", "run", model, enriched_task],
            capture_output=True, text=True,
            timeout=kwargs.get("timeout", 120)
        )
        output = result.stdout.strip()

    elif agent_type == "qwen_cli":
        result = subprocess.run(
            ["qwen", "--prompt", enriched_task],
            capture_output=True, text=True,
            timeout=kwargs.get("timeout", 300)
        )
        output = result.stdout.strip()

    elif agent_type == "gemini_cli":
        result = subprocess.run(
            ["gemini", "-p", enriched_task, "--yolo"],
            capture_output=True, text=True,
            timeout=kwargs.get("timeout", 180)
        )
        output = result.stdout.strip()

    elif agent_type == "copilot":
        result = subprocess.run(
            [
                "copilot", "-p", enriched_task,
                "--model", "gpt-5-mini",
                "--allow-all", "--allow-all-tools", "--allow-all-urls",
            ],
            capture_output=True, text=True,
            timeout=kwargs.get("timeout", 60)
        )
        output = result.stdout.strip()

    elif agent_type == "jules":
        cmd = ["jules", "new", enriched_task]
        if kwargs.get("repo"):
            cmd.insert(2, "--repo")
            cmd.insert(3, kwargs["repo"])

        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=kwargs.get("timeout", 600)
        )
        output = result.stdout.strip()

    elif agent_type == "shell":
        result = subprocess.run(
            task.split(), capture_output=True, text=True,
            timeout=kwargs.get("timeout", 30)
        )
        output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

    else:
        output = f"Unknown agent type: {agent_type}"

    # Логируем действие
    log_action(agent_name, task, output, "success")

    return {
        "task": task,
        "agent": agent_name,
        "agent_type": agent_type,
        "task_category": ctx["task_category"],
        "context_used": True,
        "context_tokens": ctx["context_tokens_estimate"],
        "past_actions_referenced": ctx["past_actions_count"],
        "errors_avoided": ctx["known_errors_count"],
        "result": output[:5000],
    }
