<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# 常见问题与排错 (Troubleshooting)

在安装和使用 `specify-cli-zh` 的过程中，如果您遇到以下问题，请参考相应的解决方案。

---

## 安装类问题

### 1. 安装时报错 `error: Executable already exists`

当您使用 `uv tool install` 等命令尝试更新或安装时，可能会因为已有旧版可执行文件而失败。

**解决方案**：强制覆盖安装：

```bash
uv tool install specify-cli-zh --from git+https://github.com/loulanyue/spec-kit-zh.git --force
```

### 2. `specify-zh` 命令找不到（command not found）

使用 `uv tool install` 安装后，系统找不到 `specify-zh` 命令。

**解决方案**：确保 `uv` 的工具目录已添加到 `PATH`：

```bash
# 查看 uv 工具目录位置
uv tool dir

# 将其加入 PATH（以 ~/.bashrc 为例）
export PATH="$(uv tool dir)/bin:$PATH"
```

也可以重新打开终端，让 shell 重新加载配置。对于 macOS 用户，如果使用 Zsh，请确认 `~/.zshrc` 中有对应的 PATH 设置。

### 3. `ModuleNotFoundError: No module named 'typer'`

如果您使用 `pip install` 或者直接运行 Python 脚本，可能会因为环境隔离未包含对应依赖而出现 `ModuleNotFoundError`。

**解决方案**：建议通过 `uv tool` 来执行全局隔离安装：

```bash
uv tool install specify-cli-zh --from git+https://github.com/loulanyue/spec-kit-zh.git
```

如需在项目开发环境中调试，使用 `uv sync` 安装所有依赖后再用 `uv run` 执行。

### 4. `uv` 本身找不到或版本过低

**解决方案**：安装或升级 `uv`：

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 检查版本（要求 >= 0.4）
uv --version
```

---

## 网络类问题

### 5. 初始化时网络超时 (Timeout) 或连接中断

访问 GitHub 进行模板下载时遇到受限网络。

**解决方案**：配置您的终端网络代理：

```bash
export HTTPS_PROXY=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export ALL_PROXY=socks5://127.0.0.1:7890
```

或直接使用本地离线模板方案：将模板手动下载到本地解压后执行：

```bash
specify-zh init --template-dir <本地解压路径>
```

详见 [国内网络加速指引](./china-network.md)。

### 6. GitHub API 获取失败 / 限流 (Rate Limit)

当您在无认证环境中频繁运行 `init` 命令或 `check` 命令时，GitHub API 可能会拒绝请求（提示 rate limit 等）。

**解决方案**：配置 GitHub Token 以显著提升限流阈值：

```bash
# 生成您的 Personal Access Token 后
export GITHUB_TOKEN=ghp_xxxxxxxxx

# 如果您安装了 GitHub CLI，也可以直接授权：
gh auth login
```

### 7. `SSL: CERTIFICATE_VERIFY_FAILED` 错误

在企业内网或特殊代理环境中，可能出现 SSL 证书验证失败。

**解决方案**：

```bash
# 方案一：指定信任证书（推荐企业环境）
export REQUESTS_CA_BUNDLE=/path/to/your/ca-bundle.crt

# 方案二：使用 uv 的 truststore 支持（已内置于 specify-cli-zh 依赖）
# 无需额外配置，truststore >= 0.10.4 会自动使用系统证书链

# 方案三（仅用于测试，不推荐生产）
export PYTHONHTTPSVERIFY=0
```

---

## 初始化与使用类问题

### 8. 初始化提示 "当前目录非空" 目录冲突

当您试图在已经有文件的目录初始化 `spec-kit` 模板时，工具会执行安全阻断。

**解决方案**：如果您确认要在已有代码库中植入 `spec-kit` 流程，请明确指定 `--here` 参数：

```bash
specify-zh init --here
```

如需完全跳过确认提示，追加 `--force`：

```bash
specify-zh init --here --force --ai copilot
```

### 9. "Agent 检测失败" / 未安装提示

初始化过程中，CLI 发现未安装对应的 AI Agent 的前端工具。

**解决方案**：请依照提示中的链接进行安装，常见工具安装命令如下：

- **Claude Code**: `npm install -g @anthropic-ai/claude-code`
- **Gemini CLI**: `npm install -g @google/gemini-cli`
- **Copilot**: 在 VS Code 中安装 GitHub Copilot 扩展

如果您不需要检测，可追加 `--ignore-agent-tools` 强行跳过。

### 10. 斜杠命令（Slash Commands）安装后不显示

运行 `specify-zh init` 成功，但在 AI 编码工具中看不到 `/speckit.*` 系列命令。

**解决方案**：

1. **完全重启** IDE 或 Agent（不只是重新加载窗口）
2. 验证命令文件已生成：
   ```bash
   ls -la .claude/commands/          # Claude Code
   ls -la ~/.codex/prompts/          # Codex
   ls -la .github/agents/            # GitHub Copilot
   ls -la .gemini/commands/          # Gemini CLI
   ```
3. 如文件缺失，重新运行：
   ```bash
   specify-zh codex-sync             # 仅同步 Codex 提示词
   specify-zh init --here --force    # 完整重新初始化
   ```

### 11. `specify-zh init` 后模板文件版本过旧

使用了旧版本 CLI 初始化的项目，模板内容未跟随新版本更新。

**解决方案**：

```bash
# 升级 CLI
uv tool install specify-cli-zh --from git+https://github.com/loulanyue/spec-kit-zh.git --force

# 重新初始化覆盖旧模板（备份 constitution.md 后执行）
cp .specify/memory/constitution.md /tmp/constitution-backup.md
specify-zh init --here --force --ai <your-agent>
mv /tmp/constitution-backup.md .specify/memory/constitution.md
```

详见 [升级指南](./upgrade.md)。

---

## Codex 专项问题

### 12. Codex 提示词同步失败 (`codex-sync` 报错)

执行 `specify-zh codex-sync` 时报权限或路径错误。

**解决方案**：

1. 确认 `~/.codex/prompts/` 目录存在且有写权限：
   ```bash
   mkdir -p ~/.codex/prompts
   chmod 755 ~/.codex/prompts
   ```
2. 在项目根目录（包含 `spec.md` 或已 `init` 的目录）重新运行：
   ```bash
   specify-zh codex-sync
   ```

### 13. Codex 斜杠命令格式错误

使用了错误的命令格式导致 Codex 无法识别。

**正确格式**：`/prompts:speckit-specify`、`/prompts:speckit-plan`、`/prompts:speckit-tasks`

**错误格式**（常见误用）：

- ❌ `/prompt.speckit.specify`
- ❌ `/prompts.speckit.specify`
- ❌ `/speckit.specify`（仅适用于 Claude Code、Gemini CLI 等，不适用于 Codex）

---

## CI / 测试类问题

### 14. 运行测试时报 `pytest: command not found`

**解决方案**：使用 `uv run` 前缀在项目虚拟环境中运行 pytest：

```bash
uv run pytest
```

或通过 Makefile 快捷方式：

```bash
make test
make coverage  # 同时生成覆盖率报告
```

### 15. 版本号与 CHANGELOG 不一致导致 CI 失败

Brand Guard 流水线检测到 `pyproject.toml` 中的版本号在 `CHANGELOG.md` 中找不到对应条目。

**解决方案**：在发布前按照 [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md) 逐项核对，确保 `CHANGELOG.md` 已添加对应版本的条目，格式示例：

```markdown
## [0.9.4] - 2026-06-15

### Added
- ...
```

### 16. `ruff` lint 检查报告大量错误

运行 `make lint` 或 CI 的 lint 步骤报告多处代码风格问题。

**解决方案**：先尝试自动修复：

```bash
uv run ruff check . --fix
uv run ruff format .
```

对于无法自动修复的错误，查看具体错误码并参考 [Ruff 文档](https://docs.astral.sh/ruff/rules/)。

---

## 获取更多帮助

如以上方案均无法解决您的问题，请通过以下方式获取支持：

- 提交 [GitHub Issue](https://github.com/loulanyue/spec-kit-zh/issues/new)，请附上：
  - `specify-zh --version` 的输出
  - 操作系统和 Python 版本（`python --version`）
  - 完整的错误信息（包括堆栈跟踪）
- 参阅 [SUPPORT.md](../SUPPORT.md) 了解更多支持渠道
