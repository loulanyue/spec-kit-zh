"""Agent configurations and helper functions for specify-cli-zh."""

from __future__ import annotations

from pathlib import Path

# Agents that use TOML configuration / command format
TOML_AGENTS = {"gemini", "qwen", "tabnine"}

# Agent configuration with name, folder, install URL, CLI tool requirement, and commands subdirectory
AGENT_CONFIG = {
    "copilot": {
        "name": "GitHub Copilot",
        "folder": ".github/",
        "commands_subdir": "agents",  # Special: uses agents/ not commands/
        "install_url": None,  # IDE-based, no CLI check needed
        "requires_cli": False,
    },
    "claude": {
        "name": "Claude Code",
        "folder": ".claude/",
        "commands_subdir": "commands",
        "install_url": "https://docs.anthropic.com/en/docs/claude-code/setup",
        "requires_cli": True,
    },
    "gemini": {
        "name": "Gemini CLI",
        "folder": ".gemini/",
        "commands_subdir": "commands",
        "install_url": "https://github.com/google-gemini/gemini-cli",
        "requires_cli": True,
    },
    "cursor-agent": {
        "name": "Cursor",
        "folder": ".cursor/",
        "commands_subdir": "commands",
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "qwen": {
        "name": "Qwen Code",
        "folder": ".qwen/",
        "commands_subdir": "commands",
        "install_url": "https://github.com/QwenLM/qwen-code",
        "requires_cli": True,
    },
    "opencode": {
        "name": "opencode",
        "folder": ".opencode/",
        "commands_subdir": "command",  # Special: singular 'command' not 'commands'
        "install_url": "https://opencode.ai",
        "requires_cli": True,
    },
    "codex": {
        "name": "Codex CLI",
        "folder": ".codex/",
        "commands_subdir": "prompts",  # Special: uses prompts/ not commands/
        "install_url": "https://github.com/openai/codex",
        "requires_cli": True,
    },
    "windsurf": {
        "name": "Windsurf",
        "folder": ".windsurf/",
        "commands_subdir": "workflows",  # Special: uses workflows/ not commands/
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "kilocode": {
        "name": "Kilo Code",
        "folder": ".kilocode/",
        "commands_subdir": "workflows",  # Special: uses workflows/ not commands/
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "auggie": {
        "name": "Auggie CLI",
        "folder": ".augment/",
        "commands_subdir": "commands",
        "install_url": "https://docs.augmentcode.com/cli/setup-auggie/install-auggie-cli",
        "requires_cli": True,
    },
    "codebuddy": {
        "name": "CodeBuddy",
        "folder": ".codebuddy/",
        "commands_subdir": "commands",
        "install_url": "https://www.codebuddy.ai/cli",
        "requires_cli": True,
    },
    "qodercli": {
        "name": "Qoder CLI",
        "folder": ".qoder/",
        "commands_subdir": "commands",
        "install_url": "https://qoder.com/cli",
        "requires_cli": True,
    },
    "roo": {
        "name": "Roo Code",
        "folder": ".roo/",
        "commands_subdir": "commands",
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "kiro-cli": {
        "name": "Kiro CLI",
        "folder": ".kiro/",
        "commands_subdir": "prompts",  # Special: uses prompts/ not commands/
        "install_url": "https://kiro.dev/docs/cli/",
        "requires_cli": True,
    },
    "amp": {
        "name": "Amp",
        "folder": ".agents/",
        "commands_subdir": "commands",
        "install_url": "https://ampcode.com/manual#install",
        "requires_cli": True,
    },
    "shai": {
        "name": "SHAI",
        "folder": ".shai/",
        "commands_subdir": "commands",
        "install_url": "https://github.com/ovh/shai",
        "requires_cli": True,
    },
    "tabnine": {
        "name": "Tabnine CLI",
        "folder": ".tabnine/agent/",
        "commands_subdir": "commands",
        "install_url": "https://docs.tabnine.com/main/getting-started/tabnine-cli",
        "requires_cli": True,
    },
    "agy": {
        "name": "Antigravity",
        "folder": ".agent/",
        "commands_subdir": "workflows",  # Special: uses workflows/ not commands/
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "bob": {
        "name": "IBM Bob",
        "folder": ".bob/",
        "commands_subdir": "commands",
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "vibe": {
        "name": "Mistral Vibe",
        "folder": ".vibe/",
        "commands_subdir": "prompts",
        "install_url": "https://github.com/mistralai/mistral-vibe",
        "requires_cli": True,
    },
    "trae": {
        "name": "Trae (ByteDance)",
        "folder": ".trae/",
        "commands_subdir": "workflows",
        "install_url": "https://www.trae.ai/",
        "requires_cli": False,
    },
    "generic": {
        "name": "Generic (bring your own agent)",
        "folder": None,  # Set dynamically via --ai-commands-dir
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": False,
    },
}

AI_ASSISTANT_ALIASES = {
    "kiro": "kiro-cli",
    "lingma": "qwen",
    "kimi": "generic",
}


def _build_ai_assistant_help() -> str:
    """根据 AGENT_CONFIG 动态构建 --ai 帮助文本，避免与运行时配置脱节。"""
    non_generic_agents = sorted(agent for agent in AGENT_CONFIG if agent != "generic")
    base_help = (
        f"可选 AI 助手: {', '.join(non_generic_agents)}, "
        "或 generic（需搭配 --ai-commands-dir）。"
    )

    if not AI_ASSISTANT_ALIASES:
        return base_help

    alias_phrases = []
    for alias, target in sorted(AI_ASSISTANT_ALIASES.items()):
        alias_phrases.append(f"将 '{alias}' 作为 '{target}' 的别名")

    if len(alias_phrases) == 1:
        aliases_text = alias_phrases[0]
    else:
        aliases_text = ", ".join(alias_phrases[:-1]) + " and " + alias_phrases[-1]

    return base_help + " 可使用 " + aliases_text + "。"


AI_ASSISTANT_HELP = _build_ai_assistant_help()

SCRIPT_TYPE_CHOICES = {"sh": "POSIX Shell (bash/zsh)", "ps": "PowerShell"}

CLAUDE_LOCAL_PATH = Path.home() / ".claude" / "local" / "claude"

# Agent-specific skill directory overrides for agents whose skills directory
# doesn't follow the standard <agent_folder>/skills/ pattern
AGENT_SKILLS_DIR_OVERRIDES = {
    "codex": ".agents/skills",  # Codex agent layout override
    "trae": ".trae/skills",
}

# Default skills directory for agents not in AGENT_CONFIG
DEFAULT_SKILLS_DIR = ".agents/skills"

# Enhanced descriptions for each spec-kit command skill
SKILL_DESCRIPTIONS = {
    "specify": "Create or update feature specifications from natural language descriptions. Use when starting new features or refining requirements. Generates spec.md with user stories, functional requirements, and acceptance criteria following spec-driven development methodology.",
    "plan": "Generate technical implementation plans from feature specifications. Use after creating a spec to define architecture, tech stack, and implementation phases. Creates plan.md with detailed technical design.",
    "tasks": "Break down implementation plans into actionable task lists. Use after planning to create a structured task breakdown. Generates tasks.md with ordered, dependency-aware tasks.",
    "implement": "Execute all tasks from the task breakdown to build the feature. Use after task generation to systematically implement the planned solution following TDD approach where applicable.",
    "analyze": "Perform cross-artifact consistency analysis across spec.md, plan.md, and tasks.md. Use after task generation to identify gaps, duplications, and inconsistencies before implementation.",
    "clarify": "Structured clarification workflow for underspecified requirements. Use before planning to resolve ambiguities through coverage-based questioning. Records answers in spec clarifications section.",
    "constitution": "Create or update project governing principles and development guidelines. Use at project start to establish code quality, testing standards, and architectural constraints that guide all development.",
    "checklist": "Generate custom quality checklists for validating requirements completeness and clarity. Use to create unit tests for English that ensure spec quality before implementation.",
    "taskstoissues": "Convert tasks from tasks.md into GitHub issues. Use after task breakdown to track work items in GitHub project management.",
    "converge": "Assess the current codebase against the feature's spec, plan, and tasks, then append any remaining unbuilt work as new tasks to tasks.md so implement can complete it. Use after partial or complete implementation passes to achieve spec-code convergence.",
}


def _get_skills_dir(project_path: Path, selected_ai: str) -> Path:
    """Resolve the agent-specific skills directory for the given AI assistant.

    Uses ``AGENT_SKILLS_DIR_OVERRIDES`` first, then falls back to
    ``AGENT_CONFIG[agent]["folder"] + "skills"``, and finally to
    ``DEFAULT_SKILLS_DIR``.
    """
    if selected_ai in AGENT_SKILLS_DIR_OVERRIDES:
        return project_path / AGENT_SKILLS_DIR_OVERRIDES[selected_ai]

    agent_config = AGENT_CONFIG.get(selected_ai, {})
    agent_folder = agent_config.get("folder", "")
    if agent_folder:
        return project_path / agent_folder.rstrip("/") / "skills"

    return project_path / DEFAULT_SKILLS_DIR


__all__ = [
    "AGENT_CONFIG",
    "AGENT_SKILLS_DIR_OVERRIDES",
    "AI_ASSISTANT_ALIASES",
    "AI_ASSISTANT_HELP",
    "CLAUDE_LOCAL_PATH",
    "DEFAULT_SKILLS_DIR",
    "SCRIPT_TYPE_CHOICES",
    "SKILL_DESCRIPTIONS",
    "TOML_AGENTS",
    "_build_ai_assistant_help",
    "_get_skills_dir",
]
