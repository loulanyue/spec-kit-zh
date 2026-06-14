# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""Shared brand and project identity constants for specify-cli-zh.

These values are referenced throughout the CLI to ensure consistency in
package names, command names, and display strings.  Centralising them here
means a single-file change is sufficient when the brand evolves.
"""

#: PyPI distribution name (used in ``pip install`` / ``uv tool install`` commands).
DIST_NAME = "specify-cli-zh"

#: The primary CLI entry-point name registered in ``pyproject.toml``.
CMD_NAME = "specify-zh"

#: Human-readable brand string shown in ``--version`` and help output.
BRAND_DISPLAY = "specify-cli-zh"

#: GitHub ``owner/repo`` slug used for release and template API requests.
UPSTREAM_REPO = "loulanyue/spec-kit-zh"

#: One-line tagline shown in rich panel headers and ``check`` command output.
TAGLINE = "specify-cli-zh - 规范驱动开发工具包"
