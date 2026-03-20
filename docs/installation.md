# 安装指南

## 前置要求

- **Linux/macOS**（也支持 Windows；PowerShell 脚本现已无需 WSL）
- AI 编码助手：[Claude Code](https://www.anthropic.com/claude-code)、[GitHub Copilot](https://code.visualstudio.com/)、[Codebuddy CLI](https://www.codebuddy.ai/cli) 或 [Gemini CLI](https://github.com/google-gemini/gemini-cli)
- 用于包管理的 [uv](https://docs.astral.sh/uv/)
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

## 安装

### 初始化新项目

最简单的开始方式是先初始化一个新项目：

```bash
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify init <PROJECT_NAME>
```

也可以直接在当前目录初始化：

```bash
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify init .
# or use the --here flag
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify init --here
```

### 指定 AI Agent

你可以在初始化时主动指定要使用的 AI Agent：

```bash
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify init <project_name> --ai claude
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify init <project_name> --ai gemini
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify init <project_name> --ai copilot
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify init <project_name> --ai codebuddy
```

### 指定脚本类型（Shell 或 PowerShell）

所有自动化脚本现在都同时提供 Bash（`.sh`）和 PowerShell（`.ps1`）版本。

自动选择规则：

- Windows 默认：`ps`
- 其他操作系统默认：`sh`
- 交互模式下：如果未传 `--script`，会提示你选择

如需强制指定脚本类型：

```bash
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify init <project_name> --script sh
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify init <project_name> --script ps
```

### 跳过 Agent 工具检查

如果你希望直接获取模板，而不检查本机是否已安装对应工具：

```bash
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify init <project_name> --ai claude --ignore-agent-tools
```

## 验证

初始化完成后，你应当能在 AI Agent 中看到以下命令：

- `/speckit.specify` - Create specifications
- `/speckit.plan` - Generate implementation plans  
- `/speckit.tasks` - Break down into actionable tasks

`.specify/scripts` 目录中会同时包含 `.sh` 和 `.ps1` 脚本。

## 故障排除

### Linux 上的 Git Credential Manager

如果你在 Linux 上遇到 Git 认证问题，可以安装 Git Credential Manager：

```bash
#!/usr/bin/env bash
set -e
echo "Downloading Git Credential Manager v2.6.1..."
wget https://github.com/git-ecosystem/git-credential-manager/releases/download/v2.6.1/gcm-linux_amd64.2.6.1.deb
echo "Installing Git Credential Manager..."
sudo dpkg -i gcm-linux_amd64.2.6.1.deb
echo "Configuring Git to use GCM..."
git config --global credential.helper manager
echo "Cleaning up..."
rm gcm-linux_amd64.2.6.1.deb
```
