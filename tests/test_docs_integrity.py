# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""单元测试：项目文档完整性与结构验证。

覆盖范围：
- 关键文档文件存在性检查
- TERMINOLOGY.md 结构完整性（三个必要章节）
- RELEASE_CHECKLIST.md 关键检查项存在性
- SECURITY.md 包含响应时效信息
- SUPPORT.md 包含快速参考表
- spec-driven.md 包含 FAQ 章节
- troubleshooting.md 包含分类章节标题
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent


# ── 文档文件存在性 ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "relative_path",
    [
        "README.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "SUPPORT.md",
        "TERMINOLOGY.md",
        "RELEASE_CHECKLIST.md",
        "AGENTS.md",
        "spec-driven.md",
        "docs/troubleshooting.md",
        "docs/installation.md",
        "docs/china-network.md",
        "docs/upgrade.md",
        "docs/domestic-llm.md",
        "docs/quickstart.md",
        "docs/local-development.md",
    ],
)
def test_key_docs_exist(relative_path: str) -> None:
    """确保关键文档文件存在于仓库中。"""
    doc_path = REPO_ROOT / relative_path
    assert doc_path.exists(), f"缺少关键文档：{relative_path}"
    assert doc_path.stat().st_size > 0, f"文档文件为空：{relative_path}"


# ── TERMINOLOGY.md 结构 ──────────────────────────────────────────────────────


def test_terminology_has_core_terms_section() -> None:
    """TERMINOLOGY.md 必须包含核心术语章节。"""
    content = (REPO_ROOT / "TERMINOLOGY.md").read_text(encoding="utf-8")
    assert "## 核心术语" in content, "TERMINOLOGY.md 缺少 '## 核心术语' 章节"


def test_terminology_has_process_terms_section() -> None:
    """TERMINOLOGY.md 必须包含流程术语章节（v0.9.4 新增）。"""
    content = (REPO_ROOT / "TERMINOLOGY.md").read_text(encoding="utf-8")
    assert "## 流程术语" in content, "TERMINOLOGY.md 缺少 '## 流程术语' 章节"


def test_terminology_has_engineering_terms_section() -> None:
    """TERMINOLOGY.md 必须包含代码与工程术语章节（v0.9.4 新增）。"""
    content = (REPO_ROOT / "TERMINOLOGY.md").read_text(encoding="utf-8")
    assert "## 代码与工程术语" in content, "TERMINOLOGY.md 缺少 '## 代码与工程术语' 章节"


def test_terminology_has_preservation_note() -> None:
    """TERMINOLOGY.md 必须包含保留英文的场景说明。"""
    content = (REPO_ROOT / "TERMINOLOGY.md").read_text(encoding="utf-8")
    assert "## 保留英文的场景" in content, "TERMINOLOGY.md 缺少 '## 保留英文的场景' 章节"


# ── RELEASE_CHECKLIST.md 关键检查项 ──────────────────────────────────────────


def test_release_checklist_has_version_section() -> None:
    """发布清单必须包含版本与文档检查章节。"""
    content = (REPO_ROOT / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    assert "版本与文档" in content


def test_release_checklist_has_quality_section() -> None:
    """发布清单必须包含测试与代码质量章节。"""
    content = (REPO_ROOT / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    assert "测试与代码质量" in content or "测试与构建" in content


def test_release_checklist_has_publish_steps() -> None:
    """发布清单必须包含最终验证与发布步骤。"""
    content = (REPO_ROOT / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    assert "最终验证" in content or "最终验证与发布" in content


# ── SECURITY.md 时效承诺 ──────────────────────────────────────────────────────


def test_security_has_sla_timeline() -> None:
    """SECURITY.md 必须包含响应时效信息（工作日）。"""
    content = (REPO_ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "工作日" in content, "SECURITY.md 缺少明确的响应时效（工作日）说明"


def test_security_has_reporting_channel() -> None:
    """SECURITY.md 必须包含漏洞报告渠道。"""
    content = (REPO_ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "opensource-security" in content or "security/advisories" in content


# ── SUPPORT.md 快速参考 ───────────────────────────────────────────────────────


def test_support_has_quick_reference_table() -> None:
    """SUPPORT.md 必须包含快速参考表（v0.9.4 新增）。"""
    content = (REPO_ROOT / "SUPPORT.md").read_text(encoding="utf-8")
    assert "| 你的问题 |" in content or "快速自助参考" in content


# ── spec-driven.md FAQ ────────────────────────────────────────────────────────


def test_spec_driven_has_faq_section() -> None:
    """spec-driven.md 必须包含 FAQ 章节（v0.9.4 新增）。"""
    content = (REPO_ROOT / "spec-driven.md").read_text(encoding="utf-8")
    assert "## 常见问题（FAQ）" in content, "spec-driven.md 缺少 FAQ 章节"


def test_spec_driven_faq_covers_solo_developers() -> None:
    """FAQ 必须包含独立开发者场景的问答。"""
    content = (REPO_ROOT / "spec-driven.md").read_text(encoding="utf-8")
    assert "独立开发者" in content or "个人项目" in content


# ── troubleshooting.md 分类章节 ───────────────────────────────────────────────


def test_troubleshooting_has_install_section() -> None:
    """troubleshooting.md 必须包含安装类问题章节（v0.9.4 新增）。"""
    content = (REPO_ROOT / "docs/troubleshooting.md").read_text(encoding="utf-8")
    assert "安装类问题" in content


def test_troubleshooting_has_network_section() -> None:
    """troubleshooting.md 必须包含网络类问题章节（v0.9.4 新增）。"""
    content = (REPO_ROOT / "docs/troubleshooting.md").read_text(encoding="utf-8")
    assert "网络类问题" in content


def test_troubleshooting_has_codex_section() -> None:
    """troubleshooting.md 必须包含 Codex 专项问题章节（v0.9.4 新增）。"""
    content = (REPO_ROOT / "docs/troubleshooting.md").read_text(encoding="utf-8")
    assert "Codex" in content


# ── domestic-llm.md 工具对比表 ────────────────────────────────────────────────


def test_domestic_llm_has_comparison_table() -> None:
    """domestic-llm.md 必须包含工具对比速查表（v0.9.4 新增）。"""
    content = (REPO_ROOT / "docs/domestic-llm.md").read_text(encoding="utf-8")
    assert "工具对比速查" in content


def test_domestic_llm_has_kiro_section() -> None:
    """domestic-llm.md 必须包含 Kiro CLI 章节（v0.9.4 新增）。"""
    content = (REPO_ROOT / "docs/domestic-llm.md").read_text(encoding="utf-8")
    assert "Kiro CLI" in content
