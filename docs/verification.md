# 验证记录

日期：2026-11-21（Asia/Shanghai）。本记录对应将现有项目技能整理为 `iibobo-skills` 插件的初始结构。

## 已通过

| 检查 | 实测结果 |
| --- | --- |
| 原文件完整性 | 迁移前后 12 个技能文件的 SHA-256 全部一致。 |
| 项目发现链接 | `.agents/skills/render-class-diagrams` 解析到正式技能目录。 |
| 可重复依赖安装 | `npm ci --offline --ignore-scripts --no-audit --no-fund` 使用已有缓存成功安装锁定依赖。 |
| 仓库结构 | `npm run check-plugin` 通过，正式技能数为 1；覆盖清单、索引、说明页、调用策略和版本一致性。 |
| 既有生成器测试 | `npm run check` 中现有 5 项 Python 测试全部通过。 |
| 平台严格校验 | `claude plugin validate . --strict` 和 `claude plugin validate .claude-plugin/plugin.json --strict` 均通过，无错误或警告。CLI 另提供了 README 安装命令建议；统一命令维护在安装文档中。 |
| Claude Code 发现 | `claude --plugin-dir "$PWD" plugin details iibobo-skills` 显示 1 个技能 `render-class-diagrams`，并列出调用时的 token 成本。 |
| Codex 发现 | 使用临时 `CODEX_HOME` 启动 app-server，并请求 `skills/list`；发现 `iibobo-skills:render-class-diagrams`，`scope=repo`、`enabled=true`，无解析错误。 |
| 非正式技能边界 | 在临时仓库副本添加 `skills/in-progress/unshipped-fixture`，不加入清单和项目发现链接。仓库结构检查通过，Claude Code 和 Codex 均发现正式技能且没有列出该 fixture。 |
| 独立技能与产物迁移 | 将技能单独复制到干净临时目录，使用其 `assets/example.md` 生成 2 张类图。类图数据和 Markdown 快照与输入一致。随后移除技能副本，迁移输出目录，HTML 引用的脚本和资源仍全部存在。 |
| 版本同步 | 在临时副本将包版本改为 `0.1.1`，运行同步脚本及结构检查均通过；实际仓库保持 `0.1.0`。 |

本地工具版本：Node.js 24.21.0、npm 11.19.0、Claude Code 2.1.295、Codex CLI 0.162.0。

## 验证范围

发现检查验证了真实 CLI 的加载结果。自动调用策略保留原技能默认值：frontmatter 没有限制模型调用，picker 配置也没有禁止隐式调用。Codex 在本仓库中展示的名称包含插件前缀；单独复制技能目录安装时使用技能本名。

尝试了 Claude Code 的显式技能调用，但当前模型连接约 52 秒内没有返回模型结果，随后终止；工具报告 API 耗时和 token 使用均为 0。本次不将完整模型调用记为通过。Codex 使用真实发现接口完成加载检查，未另外执行模型推理。

浏览器工具的 URL 策略禁止打开本地 `file:` 页面，因此本次没有视觉检查或重新确认布局、交互、SVG 导出。技能资源与执行内容保持原样；产物迁移验证仅覆盖生成结果、输入一致性和资源完整性。

GitHub Actions 工作流已经配置依赖安装、仓库检查、项目链接检查和两个平台严格校验；尚未在远端执行。本地未执行市场注册、持久安装、远程推送或发布。
