<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# 本地开发指南

本指南介绍如何在本地迭代 `specify-zh` CLI，而无需先发布版本或合并到 `main`。

> 脚本现在同时提供 Bash（`.sh`）和 PowerShell（`.ps1`）版本。除非显式传入 `--script sh|ps`，否则 CLI 会根据操作系统自动选择。

## 1. 克隆仓库并切换分支

```bash
git clone https://github.com/loulanyue/spec-kit-zh.git
cd spec-kit-zh
# 在功能分支上开发
git checkout -b your-feature-branch
```

## 2. 直接运行 CLI（反馈最快）

你可以通过模块入口直接运行 CLI，无需提前安装：

```bash
# 在仓库根目录执行
python -m src.specify_cli --help
python -m src.specify_cli init demo-project --ai claude --ignore-agent-tools --script sh
```

如果你更喜欢直接调用脚本文件（走 shebang）：

```bash
python src/specify_cli/__init__.py init demo-project --script ps
```

## 3. 使用 Editable Install（隔离环境）

使用 `uv` 创建隔离环境，让依赖解析方式尽量接近真实用户环境：

```bash
# 创建并激活虚拟环境（uv 会自动管理 .venv）
uv venv
source .venv/bin/activate  # or on Windows PowerShell: .venv\Scripts\Activate.ps1

# 以 editable 模式安装项目
uv pip install -e .

# 现在可以直接使用 'specify-zh' 入口命令
specify-zh --help
```

由于采用 editable 模式，修改代码后无需重新安装。

## 4. 直接通过 uvx 从 Git 或本地仓库调用

`uvx` 可以直接从本地路径（或 Git 引用）运行，用来模拟真实用户流程：

```bash
uvx --from . specify-zh init demo-uvx --ai copilot --ignore-agent-tools --script sh
```

你也可以让 uvx 指向某个特定分支，而无需先合并：

```bash
# 先把当前工作分支推送上去
git push origin your-feature-branch
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git@your-feature-branch specify-zh init demo-branch-test --script ps
```

### 4a. 使用绝对路径调用 uvx（可从任意目录运行）

如果你位于其他目录，请使用绝对路径替代 `.`：

```bash
uvx --from /mnt/c/GitHub/spec-kit-zh specify-zh --help
uvx --from /mnt/c/GitHub/spec-kit-zh specify-zh init demo-anywhere --ai copilot --ignore-agent-tools --script sh
```

也可以设置环境变量，方便重复使用：

```bash
export SPEC_KIT_SRC=/mnt/c/GitHub/spec-kit-zh
uvx --from "$SPEC_KIT_SRC" specify-zh init demo-env --ai copilot --ignore-agent-tools --script ps
```

（可选）定义一个 shell 函数：

```bash
specify-dev() { uvx --from /mnt/c/GitHub/spec-kit-zh specify-zh "$@"; }
# Then
specify-dev --help
```

## 5. 运行测试套件

```bash
# 运行全量单元测试（使用 uv 管理依赖）
uv run pytest

# 运行冒烟测试（验证 CLI 入口）
uv run pytest tests/test_smoke.py -v

# 运行测试并生成覆盖率报告
uv run pytest --cov=src/specify_cli --cov-report=term-missing

# 仅运行特定测试文件
uv run pytest tests/test_cli_output.py -v
```

也可以通过 Makefile 快捷方式运行：

```bash
make test       # 运行全量测试
make smoke      # 运行冒烟测试
make coverage   # 生成覆盖率报告
```

## 6. 测试脚本权限逻辑

执行一次 `init` 后，可以检查 POSIX 系统上的 shell 脚本是否具备可执行权限：

```bash
ls -l scripts | grep .sh
# 预期存在 owner execute 位（例如 -rwxr-xr-x）
```

在 Windows 上通常使用 `.ps1` 脚本，因此不需要 `chmod`。

## 7. 运行 Lint 与格式检查

```bash
# 检查代码规范
uv run ruff check src/

# 检查代码格式
uv run ruff format --check src/

# 自动修复可修复的 lint 问题并格式化代码
uv run ruff check src/ --fix
uv run ruff format src/
```

也可以通过 Makefile 快捷方式运行：

```bash
make lint       # 仅检查
make format     # 自动修复 + 格式化
```

## 8. 本地构建 Wheel（可选）

在发布前验证打包产物：

```bash
uv build
ls dist/
```

如果有需要，也可以把构建产物安装到一个临时环境中进行验证。

## 9. 使用临时工作区

如果你想在一个"脏目录"里测试 `init --here`，建议先创建临时工作区：

```bash
mkdir /tmp/spec-test && cd /tmp/spec-test
python -m src.specify_cli init --here --ai claude --ignore-agent-tools --script sh  # if repo copied here
```

如果你只想做轻量验证，也可以只复制修改过的 CLI 部分。

## 10. 调试网络 / TLS 跳过场景

如果你在本地实验时需要跳过 TLS 校验：

```bash
specify-zh check --skip-tls
specify-zh init demo --skip-tls --ai gemini --ignore-agent-tools --script ps
```

（仅建议用于本地实验。）

## 11. 快速迭代命令汇总

| 操作 | 命令 |
|------|------|
| 直接运行 CLI | `python -m src.specify_cli --help` |
| Editable install | `uv pip install -e .` 然后 `specify-zh ...` |
| 本地 uvx 运行（仓库根目录） | `uvx --from . specify-zh ...` |
| 本地 uvx 运行（绝对路径） | `uvx --from /mnt/c/GitHub/spec-kit-zh specify-zh ...` |
| Git 分支 uvx | `uvx --from git+URL@branch specify-zh ...` |
| 运行全量测试 | `uv run pytest` 或 `make test` |
| 运行冒烟测试 | `uv run pytest tests/test_smoke.py -v` 或 `make smoke` |
| Lint 检查 | `uv run ruff check src/` 或 `make lint` |
| 构建 wheel | `uv build` |

## 12. 清理

快速清理构建产物和虚拟环境：

```bash
rm -rf .venv dist build *.egg-info
# 或者使用 Makefile 目标（同时清理 __pycache__、.ruff_cache 等）
make clean
```

## 13. 调试技巧

### 使用 Python 内置断点

在代码中插入 `breakpoint()` 即可在运行时进入 `pdb` 交互调试器：

```python
# 示例：在 __init__.py 中某处插入
def init_project(...):
    breakpoint()  # 执行到此处时暂停，进入交互调试
    ...
```

运行 CLI 时会自动进入调试器：

```bash
python -m src.specify_cli init demo-debug --ai claude --ignore-agent-tools
```

调试完成后记得删除 `breakpoint()` 语句。

### 使用 rich 打印调试信息

`specify-cli-zh` 已依赖 `rich`，可直接在代码中使用 `rich.inspect()` 或 `rich.print()` 打印结构化调试信息：

```python
from rich import inspect, print as rprint

# 打印对象的所有属性和方法
inspect(some_object, methods=True)

# 打印带语法高亮的字典
rprint({"key": "value", "nested": {"a": 1}})
```

### 开启详细输出模式

许多 CLI 命令支持 `--verbose` 标志（或设置环境变量），可输出更多调试信息：

```bash
SPECIFY_DEBUG=1 python -m src.specify_cli init demo --ai claude --ignore-agent-tools
```

### pytest 调试技巧

```bash
# 打印 stdout/stderr（默认被 pytest 捕获，-s 取消捕获）
uv run pytest tests/test_cli_output.py -v -s

# 在第一个失败处立即停止（避免等待所有测试完成）
uv run pytest -x --tb=short

# 只运行匹配名称的测试（支持子字符串匹配）
uv run pytest -k "test_init" -v

# 进入 pdb 调试器（在失败处自动断开）
uv run pytest --pdb

# 显示最慢的 10 个测试
uv run pytest --durations=10
```

### 查看 CLI 生成的文件结构

初始化后快速查看生成结构：

```bash
# 查看生成的目录树（需要安装 tree）
tree demo-project/ -a -I ".git"

# 或者使用 find（无需额外工具）
find demo-project/ -not -path '*/.git/*' | sort
```

---

## 14. 常见问题

| 现象 | 处理方式 |
|------|----------|
| `ModuleNotFoundError: typer` | 执行 `uv pip install -e .` |
| 脚本不可执行（Linux） | 重新运行 init，或手动执行 `chmod +x scripts/*.sh` |
| Git 步骤被跳过 | 你可能传了 `--no-git`，或本机未安装 Git |
| 下载到了错误脚本类型 | 显式传入 `--script sh` 或 `--script ps` |
| 企业网络下 TLS 报错 | 尝试 `--skip-tls`（不要用于生产环境） |
| `pytest: command not found` | 使用 `uv run pytest` 或先激活 `.venv` |
| `ruff: command not found` | 使用 `uv run ruff check src/` |
| `breakpoint()` 在 pytest 中不生效 | 追加 `-s` 参数：`uv run pytest -s` |

---

## 15. 下一步

- 更新文档，并使用你修改后的 CLI 重新走一遍 Quick Start
- 满意后提交 PR，参见 [CONTRIBUTING.md](../CONTRIBUTING.md)
- （可选）在变更合入 `main` 后打 Tag 发布，参见 [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md)

