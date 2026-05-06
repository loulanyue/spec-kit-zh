<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# 常见问题与排错 (Troubleshooting)

在安装和使用 `specify-cli-zh` 的过程中，如果您遇到以下问题，请参考相应的解决方案。

### 1. 安装时报错 `error: Executable already exists`

当您使用 `uv tool install` 等命令尝试更新或安装时，可能会因为已有旧版可执行文件而失败。
**解决方案**：强制覆盖安装：
```bash
uv tool install specify-cli-zh --from git+https://github.com/loulanyue/spec-kit-zh.git --force
```

### 2. GitHub API 获取失败 / 限流 (Rate Limit)

当您在无认证环境中频繁运行 `init` 命令或 `check` 命令时，GitHub API 可能会拒绝请求（提示 rate limit 等）。
**解决方案**：配置 GitHub Token 以显著提升限流阈值：
```bash
# 生成您的 Personal Access Token 后
export GITHUB_TOKEN=ghp_xxxxxxxxx

# 如果您安装了 GitHub CLI，也可以直接授权：
gh auth login
```

### 3. `ModuleNotFoundError: No module named 'typer'`

如果您使用 `pip install` 或者直接运行 Python 脚本，可能会因为环境隔离未包含对应依赖而出现 `ModuleNotFoundError`。
**解决方案**：建议通过 `uv tool` 来执行全局隔离安装：
```bash
uv tool install specify-cli-zh --from git+https://github.com/loulanyue/spec-kit-zh.git
```

### 4. 初始化提示 "当前目录非空" 目录冲突

当您试图在已经有文件的目录初始化 `spec-kit` 模板时，工具会执行安全阻断。
**解决方案**：如果您确认要在已有代码库中植入 `spec-kit` 流程，请明确指定 `--here` 参数：
```bash
specify-zh init --here
```

### 5. "Agent 检测失败" / 未安装提示

初始化过程中，CLI 发现未安装对应的 AI Agent 的前端工具。
**解决方案**：请依照提示中的链接进行安装，常见工具安装命令如下：
- **Claude Code**: `npm install -g @anthropic-ai/claude-code`
- **Gemini CLI**: `npm install -g @google/gemini-cli`
如果您不需要检测，可追加 `--ignore-agent-tools` 强行跳过。

### 6. 初始化时网络超时 (Timeout) 或连接中断

访问 GitHub 进行模板下载时遇到受限网络。
**解决方案**：配置您的终端网络代理：
```bash
export HTTPS_PROXY=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
```
或直接使用本地离线模板方案：将模板手动下载到本地解压后执行 `specify-zh init --template-dir <本地路径>`。

### 7. Codex CLI 提示 `Unrecognized command`

如果 Codex CLI 中输入 `/speckit.constitution`、`/speckit:constitution` 或 `/prompts:speckit-constitution` 后仍提示命令不识别，通常是 prompts 未同步到 Codex 的全局目录，或当前 Codex 会话还没有重新加载 prompts。

**解决方案**：在项目根目录重新同步 Codex prompts：

```bash
specify-zh codex-sync --project .
```

同步完成后，重启当前 Codex 会话，再使用以下命令格式：

```text
/prompts:speckit-constitution 创建强调代码质量、测试标准、用户体验一致性与性能要求的项目原则
```

如需确认文件是否存在，可以检查：

```bash
ls -la ~/.codex/prompts/
ls -la .codex/prompts/
```
