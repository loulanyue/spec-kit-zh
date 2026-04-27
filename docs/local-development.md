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
export SPEC_KIT_SRC=/mnt/c/GitHub/spec-kit
uvx --from "$SPEC_KIT_SRC" specify-zh init demo-env --ai copilot --ignore-agent-tools --script ps
```

（可选）定义一个 shell 函数：

```bash
specify-dev() { uvx --from /mnt/c/GitHub/spec-kit specify-zh "$@"; }
# Then
specify-dev --help
```

## 5. 测试脚本权限逻辑

执行一次 `init` 后，可以检查 POSIX 系统上的 shell 脚本是否具备可执行权限：

```bash
ls -l scripts | grep .sh
# 预期存在 owner execute 位（例如 -rwxr-xr-x）
```

在 Windows 上通常使用 `.ps1` 脚本，因此不需要 `chmod`。

## 6. 运行 Lint / 基础检查（可自行补充）

当前仓库没有强制内置 lint 配置，但你可以先快速检查模块是否可导入：

```bash
python -c "import specify_cli; print('Import OK')"
```

## 7. 本地构建 Wheel（可选）

在发布前验证打包产物：

```bash
uv build
ls dist/
```

如果有需要，也可以把构建产物安装到一个临时环境中进行验证。

## 8. 使用临时工作区

如果你想在一个“脏目录”里测试 `init --here`，建议先创建临时工作区：

```bash
mkdir /tmp/spec-test && cd /tmp/spec-test
python -m src.specify_cli init --here --ai claude --ignore-agent-tools --script sh  # if repo copied here
```

如果你只想做轻量验证，也可以只复制修改过的 CLI 部分。

## 9. 调试网络 / TLS 跳过场景

如果你在本地实验时需要跳过 TLS 校验：

```bash
specify-zh check --skip-tls
specify-zh init demo --skip-tls --ai gemini --ignore-agent-tools --script ps
```

（仅建议用于本地实验。）

## 10. 快速迭代命令汇总

| 操作 | 命令 |
|------|------|
| 直接运行 CLI | `python -m src.specify_cli --help` |
| Editable install | `uv pip install -e .` 然后 `specify-zh ...` |
| 本地 uvx 运行（仓库根目录） | `uvx --from . specify-zh ...` |
| 本地 uvx 运行（绝对路径） | `uvx --from /mnt/c/GitHub/spec-kit specify-zh ...` |
| Git 分支 uvx | `uvx --from git+URL@branch specify-zh ...` |
| 构建 wheel | `uv build` |

## 11. 清理

快速清理构建产物和虚拟环境：

```bash
rm -rf .venv dist build *.egg-info
```

## 12. 常见问题

| 现象 | 处理方式 |
|------|----------|
| `ModuleNotFoundError: typer` | 执行 `uv pip install -e .` |
| 脚本不可执行（Linux） | 重新运行 init，或手动执行 `chmod +x scripts/*.sh` |
| Git 步骤被跳过 | 你可能传了 `--no-git`，或本机未安装 Git |
| 下载到了错误脚本类型 | 显式传入 `--script sh` 或 `--script ps` |
| 企业网络下 TLS 报错 | 尝试 `--skip-tls`（不要用于生产环境） |

## 13. 下一步

- 更新文档，并使用你修改后的 CLI 重新走一遍 Quick Start
- 满意后提交 PR
- （可选）在变更合入 `main` 后打 Tag 发布
