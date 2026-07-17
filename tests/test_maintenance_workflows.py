# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""Regression tests for repository maintenance workflow contracts."""

from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent


def test_upstream_sync_uses_canonical_issue_label() -> None:
    """Issue lookup and creation must share one label to preserve deduplication."""
    workflow = (REPO_ROOT / ".github" / "workflows" / "upstream-sync.yml").read_text(
        encoding="utf-8"
    )

    assert "labels: 'upstream-sync'" in workflow
    assert "labels: ['upstream-sync']" in workflow
    assert "labels: '上游同步'" not in workflow
