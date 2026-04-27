<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# 国内大模型与 AI 编码工具接入指南

本文档介绍如何将 **specify-cli-zh** 与国内主流大模型及 AI 编码工具结合，实现规范驱动开发（Spec-Driven Development）工作流。

---

## 目录

- [通义灵码（Tongyi Lingma）](#通义灵码)
- [DeepSeek Coder](#deepseek-coder)
- [百度 Comate](#百度-comate)
- [MarsCode（豆包 MarsCode）](#marscode)
- [其他工具适配说明](#其他工具适配说明)

---

## 通义灵码

[通义灵码](https://tongyi.aliyun.com/lingma) 是阿里云推出的 AI 编码助手，支持 VSCode 和 JetBrains 插件。

### 使用方式

通义灵码目前无独立 CLI，通过 IDE 插件接入。使用 `--ai generic` 将 specify-cli-zh 生成的模板适配到通义灵码：

```bash
# 在项目中初始化，将命令模板放入自定义目录
specify-zh init my-project --ai generic --ai-commands-dir .tongyi/prompts/
```

### 推荐 SDD 工作流

1. **初始化项目**：运行 `specify-zh init` 生成 `.specify/` 目录结构
2. **创建规范**：在通义灵码对话框中，将 `templates/commands/specify.md` 的内容作为提示词上下文
3. **生成计划**：使用 `plan.md` 模板提示通义灵码输出技术实施计划
4. **任务分解与实现**：使用 `tasks.md` 和 `implement.md` 模板配合通义灵码完成实现

### 注意事项

- 通义灵码对长上下文提示词支持较好，可直接粘贴完整模板文件内容
- 建议在 IDE 中打开 `.specify/` 目录，方便随时引用规范文件
- 使用中文描述需求，通义灵码中文理解能力强

---

## DeepSeek Coder

[DeepSeek Coder](https://coder.deepseek.com/) 是深度求索推出的代码生成大模型，支持通过 API 调用和官方 Web 界面使用。

### 使用方式

DeepSeek Coder 可通过其 Web 界面或 API 接入，配合 specify-cli-zh 的模板使用：

```bash
# 初始化项目结构
specify-zh init my-project --ai generic --ai-commands-dir .deepseek/prompts/
```

### 推荐 SDD 工作流

1. **生成项目结构**：`specify-zh init` 创建 `.specify/` 和脚本目录
2. **规范撰写**：直接在 DeepSeek Coder 对话中输入需求描述，将 `specify.md` 模板作为系统提示
3. **技术计划**：使用 `plan.md` 模板，DeepSeek Coder 在代码架构分析方面表现优秀
4. **代码实现**：配合 `implement.md` 模板指导代码生成，DeepSeek Coder 对代码质量要求高

### API 集成示例

```python
# 通过 DeepSeek API 调用，配合 SDD 工作流
import openai  # DeepSeek API 兼容 OpenAI 格式

client = openai.OpenAI(
    api_key="your_deepseek_api_key",
    base_url="https://api.deepseek.com"
)

# 加载 specify.md 模板作为 system prompt
with open(".specify/templates/spec-template.md") as f:
    spec_template = f.read()

response = client.chat.completions.create(
    model="deepseek-coder",
    messages=[
        {"role": "system", "content": f"使用如下模板创建规范：\n{spec_template}"},
        {"role": "user", "content": "构建一个用户认证模块"}
    ]
)
```

### 注意事项

- DeepSeek Coder 在中英混合代码注释方面处理较好
- 推荐将规范模板保存为本地文件，通过 API 动态加载
- 国内访问 DeepSeek API 速度快，适合频繁迭代的 SDD 流程

---

## 百度 Comate

[百度 Comate](https://comate.baidu.com/) 是百度推出的 AI 编程助手，支持 VSCode、JetBrains 等主流 IDE 插件。

### 使用方式

```bash
# 使用 generic 模式适配 Comate
specify-zh init my-project --ai generic --ai-commands-dir .comate/prompts/
```

### 推荐 SDD 工作流

1. 使用 `specify-zh init` 生成项目骨架
2. 在 Comate 的「对话模式」中引用 `.specify/` 下的规范文件
3. 使用 Comate 的「内联补全」功能配合 `tasks.md` 逐步实现任务

### 注意事项

- Comate 内嵌了百度文心大模型，中文指令响应流畅
- 在 IDE 插件中直接引用 `.specify/` 目录效果最佳
- 可利用 Comate 的「代码解释」功能验证生成代码是否符合规范

---

## MarsCode

[MarsCode（豆包 MarsCode）](https://www.marscode.com/) 是字节跳动推出的 AI 编程工具，提供 IDE 插件和在线 IDE。

### 使用方式

```bash
# 初始化项目
specify-zh init my-project --ai generic --ai-commands-dir .marscode/prompts/
```

### 推荐 SDD 工作流

1. 在 MarsCode 在线 IDE 中打开项目
2. 通过 MarsCode 的 AI 对话功能，粘贴 specify.md 模板内容作为提示
3. 使用 MarsCode 的代码生成功能配合 `implement.md` 模板实现代码

### 注意事项

- MarsCode 提供了完整的在线 IDE 环境，适合快速原型开发
- 对中文规范描述支持良好，适合国内团队协作

---

## 其他工具适配说明

对于其他未内置支持的国内 AI 编码工具，可使用 `--ai generic` 模式：

```bash
# 通用适配方式
specify-zh init my-project --ai generic --ai-commands-dir .<your-tool>/prompts/
```

### 通用适配步骤

1. 使用 `specify-zh init --ai generic` 生成基础项目结构
2. 将 `templates/commands/` 下的 Markdown 模板文件复制到工具的提示词目录
3. 根据目标工具的参数引用规范，将 `$ARGUMENTS` 替换为该工具的参数占位符
4. 在工具配置中将 `.specify/` 目录加入上下文感知路径

### 提交新工具支持

如果你希望为某个国内 AI 工具添加正式支持，请参阅 [CONTRIBUTING.md](../CONTRIBUTING.md) 并提交 Pull Request。

---

## 相关资源

- [国内网络加速指南](./china-network.md) — PyPI 镜像、GitHub 加速、代理配置
- [安装指南](./installation.md) — specify-cli-zh 安装与验证
- [故障排除](./troubleshooting.md) — 常见问题解决方案
