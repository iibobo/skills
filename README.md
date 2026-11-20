# iibobo skills

可复用的 Agent 技能集合。目前包含离线 Mermaid 类图的绘制、源码定位和可迁移 HTML 输出工作流。

## 技能

### Model-invoked

以下技能可由匹配的任务自动触发，也可显式调用。

- [render-class-diagrams](skills/engineering/render-class-diagrams/SKILL.md)：绘制类与接口关系图，生成带离线资源的可迁移 HTML；参见[使用说明](docs/engineering/render-class-diagrams.md)。

## 安装与调用

统一操作说明见[安装文档](docs/installation.md)，涵盖 Codex 项目发现、用户级安装和 Claude Code 插件安装。

本项目的 Codex CLI 0.162.0 实测发现名为 `$iibobo-skills:render-class-diagrams`；直接安装技能目录时使用 `$render-class-diagrams`。Claude Code 插件名为 `iibobo-skills`，本仓库的市场名为 `iibobo`。

## 目录

```text
skills/engineering/              正式技能及其完整运行资源
.agents/skills/                  Codex 项目开发链接
.claude-plugin/                  插件与单插件市场清单
docs/engineering/                面向使用者的技能说明
scripts/                        结构校验和版本同步
.github/workflows/check.yml      持续集成检查
```

正式技能以 `skills/<分类>/<名称>/` 为唯一内容来源。项目发现链接与插件发布列表分别维护。只有出现对应技能时才新增 `productivity`、`in-progress`、`misc` 或 `deprecated` 分类。

## 维护与版本

```bash
npm ci
npm run check
claude plugin validate . --strict
claude plugin validate .claude-plugin/plugin.json --strict
```

新增正式技能时，更新插件清单、根目录和分类索引、`docs/<分类>/<名称>.md`，并添加 `.agents/skills/<名称>` 项目链接。具体约束见 [AGENTS.md](AGENTS.md)。

`package.json` 是版本来源。准备版本时运行 `npm version patch --no-git-tag-version`（按需换为 `minor` 或 `major`）；生命周期脚本先校验，再同步插件版本。检查版本文件、锁文件和变更后再提交；远程推送和发布另行执行。本项目通过技能目录和插件分发，npm 包保持私有。

平台结构校验与真实加载的验证范围见[验证记录](docs/verification.md)。
