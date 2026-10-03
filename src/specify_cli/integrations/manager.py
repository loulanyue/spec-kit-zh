# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""Integration management and agent detection for specify-cli-zh."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from specify_cli.agents import AGENT_CONFIG, AI_ASSISTANT_ALIASES


# Extended agents definition to cover upstream agent catalog
EXTENDED_AGENTS: dict[str, dict[str, Any]] = {
    "cline": {
        "name": "Cline",
        "folder": ".cline/",
        "commands_subdir": "commands",
        "install_url": "https://github.com/cline/cline",
        "requires_cli": False,
    },
    "devin": {
        "name": "Devin AI",
        "folder": ".devin/",
        "commands_subdir": "commands",
        "install_url": "https://devin.ai",
        "requires_cli": False,
    },
    "forge": {
        "name": "Forge",
        "folder": ".forge/",
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": False,
    },
    "goose": {
        "name": "Block Goose",
        "folder": ".goose/",
        "commands_subdir": "commands",
        "install_url": "https://github.com/block/goose",
        "requires_cli": True,
    },
    "junie": {
        "name": "JetBrains Junie",
        "folder": ".junie/",
        "commands_subdir": "commands",
        "install_url": "https://www.jetbrains.com/junie/",
        "requires_cli": False,
    },
    "mcode": {
        "name": "MiniMax Code",
        "folder": ".mcode/",
        "commands_subdir": "commands",
        "install_url": "https://minimax.io",
        "requires_cli": True,
    },
    "muse": {
        "name": "Muse Code",
        "folder": ".muse/",
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": False,
    },
    "rovodev": {
        "name": "Atlassian Rovo Dev",
        "folder": ".rovodev/",
        "commands_subdir": "commands",
        "install_url": "https://www.atlassian.com/software/rovo",
        "requires_cli": False,
    },
    "zed": {
        "name": "Zed Editor",
        "folder": ".zed/",
        "commands_subdir": "prompts",
        "install_url": "https://zed.dev",
        "requires_cli": False,
    },
    "docker-agent": {
        "name": "Docker Agent",
        "folder": ".docker-agent/",
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": False,
    },
    "dsh": {
        "name": "DeepSeek Harness (DSH)",
        "folder": ".dsh/",
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": True,
    },
}


class IntegrationManager:
    """Manages AI coding assistant integrations, detection, and switching."""

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or Path.cwd()

    def get_all_agents(self) -> dict[str, dict[str, Any]]:
        """Return unified mapping of all supported agents."""
        combined = dict(AGENT_CONFIG)
        combined.update(EXTENDED_AGENTS)
        return combined

    def resolve_key(self, key: str) -> str:
        """Resolve alias to canonical key."""
        k = key.lower().strip()
        return AI_ASSISTANT_ALIASES.get(k, k)

    def detect_active_integrations(self) -> list[str]:
        """Detect which AI assistant directories exist in the project."""
        active: list[str] = []
        for key, conf in self.get_all_agents().items():
            folder = conf.get("folder")
            if folder:
                target = self.project_root / folder.strip("/")
                if target.is_dir():
                    active.append(key)
        return active

    def get_info(self, key: str) -> dict[str, Any] | None:
        """Get config dict for a given agent key or alias."""
        canon = self.resolve_key(key)
        agents = self.get_all_agents()
        if canon in agents:
            res = dict(agents[canon])
            res["canonical_key"] = canon
            return res
        return None

    def switch(self, target_key: str, enable_skills: bool = True) -> bool:
        """Switch active integration to target_key by installing prompts/skills."""
        canon = self.resolve_key(target_key)
        info = self.get_info(canon)
        if not info:
            raise ValueError(f"未知的 AI 助手集成: {target_key}")

        folder = info.get("folder")
        if not folder:
            raise ValueError(f"助手 {canon} 未配置目录路径")

        agent_dir = self.project_root / folder.strip("/")
        agent_dir.mkdir(parents=True, exist_ok=True)

        # Scaffolding AI skills / commands
        try:
            from specify_cli.templates import install_ai_skills

            install_ai_skills(self.project_root, canon)
        except Exception:
            pass

        return True
