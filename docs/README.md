<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# 文档说明

此目录包含 Spec Kit 的文档源码，使用 [DocFX](https://dotnet.github.io/docfx/) 构建。

## 本地构建

如需在本地构建文档：

1. 安装 DocFX：

   ```bash
   dotnet tool install -g docfx
   ```

2. 构建文档：

   ```bash
   cd docs
   docfx docfx.json --serve
   ```

3. 在浏览器中打开 `http://localhost:8080` 查看文档。

## 目录结构

- `docfx.json` - DocFX 配置文件
- `index.md` - 文档首页
- `toc.yml` - 目录配置
- `installation.md` - 安装指南
- `quickstart.md` - 快速开始指南
- `_site/` - 生成后的文档输出目录（已加入 git ignore）

## 部署

文档工作流定义在 `.github/workflows/docs.yml` 中：

- 对 pull request：构建 DocFX 站点，验证文档变更不会破坏生成流程。
- 对 `main` 分支：构建 DocFX 站点，并将 `docs/_site` 发布到 GitHub Pages。
- 对手动触发：可通过 GitHub Actions 的 `workflow_dispatch` 重新构建并部署当前 `main` 分支文档。

如需发布到 GitHub Pages，请在仓库设置中将 Pages 的部署来源设置为 **GitHub Actions**。
