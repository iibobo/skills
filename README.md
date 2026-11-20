# iibobo skills

可复用的 Agent 技能集合，把工程任务中的操作步骤、检查标准和运行资源放在一起。目前包含一个技能：绘制或修改 Mermaid 类与接口关系图，生成可迁移的离线 HTML，并可配置源码导航。

每个技能都可以独立安装和使用，也可以通过 `iibobo-skills` 插件一起分发。

仓库内的 `iibobo` 是自建插件市场的名称。将插件文件推送到可访问的 GitHub 仓库后，其他用户可添加该仓库作为市场来源并安装插件；上架 ChatGPT / Codex 公共插件目录还需按[官方流程](https://developers.openai.com/plugins/deploy/submission)单独提交审核。

## 安装与开始使用

1. 按[安装文档](docs/installation.md)选择 Codex 或 Claude Code 插件安装；需要自行修改技能文件时，可选择独立技能安装。同一 Agent 选择一种方式，避免重复发现。
2. 安装后开启新会话，按安装文档中对应的名称显式调用技能；支持自动调用的 Agent 也可根据任务描述选用该技能。插件安装与独立安装的调用名称不同。
3. 例如：“根据当前模块源码绘制类与接口关系图，标注继承和实现关系，输出可离线打开的 HTML。”

安装命令、调用名称、项目开发方式与更新说明统一维护在[安装文档](docs/installation.md)。

生成 HTML 需要 Python 3.9+，查看页面和导出 SVG 需要现代浏览器。技能自带离线渲染资源；绘制真实代码的关系图时，还需提供可读取的源码或对应版本的依赖文件。

## 这些技能解决什么问题

### 读源码时难以看清类型关系

类图工作流要求先核对真实声明，再整理类型职责、核心方法、继承与实现关系。适合梳理模块结构、阅读依赖库和讲解设计。可选的源码导航需要提供符号映射，并配置相应的 IDE 接收环境，具体见[使用说明](docs/engineering/render-class-diagrams.md)。

### 图能生成，却难以搬移和复用

类图技能自带渲染模板和运行资源，统一配色、方法分类和关系标注。生成的 HTML 必须与相邻的同名 `.assets/` 目录一起搬移，才能保留离线查看所需的资源；在页面中可导出当前类图的 SVG。具体要求与成功标准见[使用说明](docs/engineering/render-class-diagrams.md)。

## 技能参考

技能按领域组织，再按调用方式分组。`User-invoked` 仅允许用户显式调用；`Model-invoked` 允许 Agent 在任务匹配时自动使用，也支持用户显式调用。实际发现与调用行为取决于宿主支持和配置，已测范围见[验证记录](docs/verification.md)。目前只有工程领域的 `Model-invoked` 技能。

### Engineering · 工程

用于源码理解、设计表达和工程交付。完整分类索引见[工程技能](skills/engineering/README.md)。

#### Model-invoked

- [render-class-diagrams](skills/engineering/render-class-diagrams/SKILL.md)：绘制类与接口关系图，生成离线 HTML，支持 SVG 导出和可选的源码导航；[使用说明](docs/engineering/render-class-diagrams.md)。

## 仓库维护

目录与发布边界：

```text
skills/engineering/              正式技能及其完整运行资源
.agents/skills/                  Codex 项目开发链接
.claude-plugin/                  插件与单插件市场清单
docs/engineering/                面向使用者的技能说明
scripts/                        结构校验和版本同步
.github/workflows/check.yml      持续集成检查
```

正式技能以 `skills/<分类>/<名称>/` 为唯一内容来源。项目发现链接与插件发布列表分别维护。只有出现对应技能时才新增 `productivity`、`in-progress`、`misc` 或 `deprecated` 分类。

以下命令用于维护仓库，需要 Node.js 22+、npm、Python 3.9+ 和 Claude Code CLI：

```bash
npm ci
npm run check
claude plugin validate . --strict
claude plugin validate .claude-plugin/plugin.json --strict
```

新增正式技能时，更新插件清单、根目录和分类索引、`docs/<分类>/<名称>.md`，并添加 `.agents/skills/<名称>` 项目链接。具体约束见 [AGENTS.md](AGENTS.md)。

`package.json` 是版本来源。准备版本时运行 `npm version patch --no-git-tag-version`（按需换为 `minor` 或 `major`）；生命周期脚本先校验，再同步插件版本。检查版本文件、锁文件和变更后再提交；远程推送和发布另行执行。本项目通过技能目录和插件分发；`package.json` 中的 `private: true` 用于防止误发布到 npm。

平台结构校验与真实加载的验证范围见[验证记录](docs/verification.md)。

本仓库的组织方式参考 [mattpocock/skills 的 README](https://github.com/mattpocock/skills/blob/main/README.md)：先说明安装与使用场景，再按领域和调用方式索引技能。技能编写与晋升规则见[编写约定](docs/authoring.md)。
