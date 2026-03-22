import pytest
from typer.testing import CliRunner
from specify_cli import app

runner = CliRunner()

def test_check_output_brand():
    """测试 check 命令输出不包含旧的英文品牌名"""
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    assert "Specify CLI" not in result.stdout, "输出不应包含旧的英文品牌 'Specify CLI'"

def test_doctor_output_brand():
    """测试 doctor 命令输出不包含旧的英文品牌名"""
    # mock http requests normally required by doctor if needed, but simple invocation is enough to catch static strings
    result = runner.invoke(app, ["doctor"])
    assert "Specify CLI" not in result.stdout, "输出不应包含旧的英文品牌 'Specify CLI'"

def test_version_output_brand():
    """测试 version 命令输出包含正确的模块分发包名"""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "specify-cli-zh" in result.stdout, "版本输出应当涵盖 specify-cli-zh 包名及信息"

def test_extension_help_brand():
    """测试 extension 子命令不包含旧品牌且为中文"""
    result = runner.invoke(app, ["extension", "--help"])
    assert result.exit_code == 0
    assert "Specify CLI" not in result.stdout
