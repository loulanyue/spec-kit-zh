# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""CLI 输出快照测试 (P3-16)

测试各子命令输出：品牌守护、中文化断言。
Run: pytest tests/test_cli_output.py -v
"""

import pytest
from typer.testing import CliRunner
from specify_cli import app

runner = CliRunner()

# 任何在验收标准中不允许出现的旧品牌字符串
OLD_BRAND = "Specify CLI"


def _strip_brand(text: str) -> str:
    """剔除合法品牌名称后返回文本，用于检测裸旧品牌名。"""
    return text.replace("specify-cli-zh", "").replace("specify-zh", "")


# ── 品牌守护 ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("subcommand", [
    [],
    ["--help"],
    ["check"],
    ["version"],
    ["doctor"],
    ["init", "--help"],
    ["extension", "--help"],
])
def test_no_old_brand_in_output(subcommand):
    """任意子命令输出不得包含裸旧品牌名 'Specify CLI'（不带 -zh）。"""
    result = runner.invoke(app, subcommand)
    sanitized = _strip_brand(result.output)
    assert OLD_BRAND not in sanitized, (
        f"命令 {['specify-zh'] + subcommand} 的输出包含旧品牌名 '{OLD_BRAND}':\n{result.output}"
    )


# ── check 命令 ─────────────────────────────────────────────────────────────────

def test_check_exits_zero():
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0


def test_check_output_contains_brand():
    """check 输出应包含正确品牌名 specify-zh。"""
    result = runner.invoke(app, ["check"])
    assert "specify-zh" in result.output, f"check 输出缺少品牌名:\n{result.output}"


def test_check_output_no_old_brand():
    """check 输出不包含旧英文品牌 'Specify CLI'。"""
    result = runner.invoke(app, ["check"])
    sanitized = _strip_brand(result.output)
    assert OLD_BRAND not in sanitized


# ── doctor 命令 ────────────────────────────────────────────────────────────────

def test_doctor_output_no_old_brand():
    """doctor 输出不包含旧英文品牌 'Specify CLI'。"""
    result = runner.invoke(app, ["doctor"])
    sanitized = _strip_brand(result.output)
    assert OLD_BRAND not in sanitized


def test_doctor_output_contains_brand():
    """doctor 输出应包含正确品牌名 specify-zh 或 specify-cli-zh。"""
    result = runner.invoke(app, ["doctor"])
    assert ("specify-zh" in result.output or "specify-cli-zh" in result.output), (
        f"doctor 输出缺少品牌名:\n{result.output}"
    )


# ── version 命令 ───────────────────────────────────────────────────────────────

def test_version_exits_zero():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0


def test_version_output_contains_dist_name():
    """version 输出应包含分发包名 specify-cli-zh。"""
    result = runner.invoke(app, ["version"])
    assert "specify-cli-zh" in result.output, (
        f"version 输出应含 specify-cli-zh\n{result.output}"
    )


def test_version_output_no_old_brand():
    result = runner.invoke(app, ["version"])
    sanitized = _strip_brand(result.output)
    assert OLD_BRAND not in sanitized


# ── extension 子命令 ───────────────────────────────────────────────────────────

def test_extension_help_exits_zero():
    result = runner.invoke(app, ["extension", "--help"])
    assert result.exit_code == 0


def test_extension_help_no_old_brand():
    """extension --help 不包含旧品牌名称。"""
    result = runner.invoke(app, ["extension", "--help"])
    sanitized = _strip_brand(result.output)
    assert OLD_BRAND not in sanitized
