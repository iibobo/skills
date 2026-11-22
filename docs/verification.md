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

## README 组织调整复验

日期：2026-11-21（Asia/Shanghai）。按上游 README 的顺序调整简介、安装入口、使用场景和按领域及调用方式分组的技能索引，并补充统一安装文档；技能内容、运行资源、发现链接和插件清单未变。

- `npm run check` 通过，包含结构检查及 5 项既有 Python 测试。
- 两条 `claude plugin validate ... --strict` 命令均通过，无错误或警告；CLI 仍建议在 README 中直接放安装命令。本仓库按维护约定将命令集中在 `docs/installation.md`，README 链接到该文档。
- 使用临时 `CODEX_HOME`，从仓库外执行本地市场添加、`codex plugin add iibobo-skills@iibobo` 和插件列表查询，均返回成功；安装版本为 `0.1.0`，状态为 `installed=true`、`enabled=true`。临时配置与缓存随验证目录清理，没有修改用户的持久插件配置。
- `claude --plugin-dir "$PWD" plugin details iibobo-skills` 再次列出 1 个技能 `render-class-diagrams`。
- 新补充的安装及更新语法已对照 Codex CLI 0.162.0、Claude Code 2.1.295 帮助核对。GitHub 安装和更新未实际执行；完整模型调用、非正式技能隔离与浏览器交互未重复测试，沿用上文记录的验证边界。

## 源码跳转默认策略修复

日期：2026-11-21（Asia/Shanghai）。技能入口、规范、默认提示与说明页已改为默认创建类及展示方法的源码映射，生成命令同时提供 `--source-map` 和 `--require-source-links`；明确纯图、无真实源码概念示例的例外及源码缺失时的处理。生成器和浏览器资源未修改。

- `npm run check` 通过，包含结构检查及 5 项既有源码链接测试；覆盖准确符号写入和缺少方法映射时拒绝生成。
- `claude plugin validate . --strict` 与 `claude plugin validate .claude-plugin/plugin.json --strict` 均通过，保留既有 README 安装建议。
- `git diff --check` 通过。
- skill-creator 的 `quick_validate.py` 因当前 Python 缺少 PyYAML 未能运行；仓库结构和平台格式检查已完成。
- 本次为技能执行指令调整，未执行独立模型调用或 IDEA 真实打开验证，未重新验证浏览器交互。

## 对话结束提交信息钩子

日期：2026-11-21（Asia/Shanghai）。新增项目级 `.codex/hooks.json`，使用 `UserPromptSubmit` 注入输出约定，`Stop` 检查最终回复并在遗漏时最多补充一次。只提供 message，不执行暂存、提交或推送。

- `npm run check` 通过：5 项既有源码链接测试及 5 项钩子测试。钩子检查包含 stdin/stdout JSON 协议、缺失或空 message、正常 message、无变更说明、防止续接循环，以及从项目子目录执行实际注册命令。
- 两条 `claude plugin validate ... --strict` 均通过，仍有既有 README 安装建议；此校验不验证 Codex 钩子生命周期。
- 实现对照 OpenAI Hooks 官方文档（https://learn.chatgpt.com/docs/hooks）；未执行真实模型回合的端到端触发验证。
- 项目钩子需用户在 Codex 的 Settings → Hooks（CLI 使用 `/hooks`）审阅并信任后才会执行；本次没有修改信任记录或全局配置。

## 提交信息钩子迁移至用户级

日期：2026-11-21（Asia/Shanghai）。按用户要求将上述项目级钩子迁至 `~/.codex/hooks.json`，脚本放在 `~/.codex/hooks/commit-message-hook.py`。保留已有 CodeGraph、RTK 钩子，修改前备份原用户配置。移除仓库注册、脚本、测试及对应 npm 测试入口，避免重复触发及仓库路径依赖。

- 对比备份确认原有钩子条目完整保留。用户级脚本与已测试源码逐字节一致。
- 在 `/private/tmp`（非 Git 项目目录）执行用户配置中新注册的两条实际命令，stdin/stdout JSON 协议及返回结果正确。另通过 4 项提交信息行为测试，覆盖遗漏、正常输出、无变更说明及续接防循环。
- `npm run check` 及两项平台严格校验通过。未在真实模型回合中验证触发；新增用户级钩子仍需在 Settings → Hooks 审阅并信任，本次未修改信任记录。

## 新增时序图技能

日期：2026-11-22（Asia/Shanghai）。新增正式技能 `render-sequence-diagrams`，包含独立规范、双图示例、离线展示模板、Python 生成器及 Mermaid.js 12.3.0 和许可证。已同步插件清单、市场简介、README、分类索引、使用及安装说明、项目发现链接和 CI；版本保持 `0.1.0`，本次未发布或修改用户安装。

- `npm run check` 通过：5 项既有类图源码链接测试及 5 项时序图生成测试。新测试覆盖多图与类型筛选、源码快照、无时序图输入、覆盖保护、HTML/JSON 转义，以及技能独立复制与产物迁移。
- `claude plugin validate . --strict` 与 `claude plugin validate .claude-plugin/plugin.json --strict` 均通过；仍有既有 README 安装命令建议。
- Claude Code 的会话级 `plugin details` 列出两个正式技能；Codex app-server 在临时 `CODEX_HOME` 下的 `skills/list` 返回新技能，`scope=repo`、`enabled=true`，无解析错误。两个项目符号链接均指向正式目录。
- 临时 Git 仓库副本中加入 `skills/in-progress/unshipped-fixture`，结构检查通过；Claude Code 与 Codex 均发现时序图技能且未发现未发布 fixture。初次副本缺少 Git 根及发现链接，Codex 未识别项目技能；补齐隔离副本结构后复验通过。
- 将技能单独复制到临时目录生成两个场景，再删除技能副本并搬移产物。通过 localhost 浏览器实际渲染校验/返回/互斥分支与异步/并行/循环两图；多图切换、100% 与放大、适应宽度操作正常。导出的 `sequence-2.svg` 已独立打开，文字、箭头、分组与颜色完整。页面资源均来自迁移后的相邻资源目录。
- `skill-creator/quick_validate.py` 因当前 Python 缺少 PyYAML 未能运行；仓库 YAML/结构检查及平台校验均已通过。未执行新技能的完整模型调用，不将发现和浏览器验证等同于模型行为验证；尚未在远端运行 CI。
- 语法参考 Mermaid 官方时序图文档（https://mermaid.js.org/syntax/sequenceDiagram.html），本地示例已按内置运行库实际渲染。

## 新增流程图技能

日期：2026-11-22（Asia/Shanghai）。新增正式技能 `render-flowcharts`，包含流程图规范、双图示例、独立离线展示模板、生成器和 Mermaid.js 12.3.0 与许可证；同步清单、市场简介、索引、使用及安装说明、发现链接和 CI。保持版本 `0.1.0`，未发布或更改用户安装。

- `npm run check` 通过：既有类图 5 项、时序图 5 项及流程图 6 项测试。新技能覆盖多图、排除其他图类型、`graph` 别名与五种方向、覆盖保护、转义、快照，以及技能独立复制和产物迁移。
- 两项 `claude plugin validate ... --strict` 均通过；保留既有 README 安装命令建议。三个项目发现链接均指向正式目录。
- Claude Code 的会话级插件清单列出三个正式技能。临时 Git 仓库副本及临时 `CODEX_HOME` 中，Codex app-server 的 `skills/list` 识别 `iibobo-skills:render-flowcharts`，未识别 `in-progress/unshipped-fixture`；Claude Code 同样发现新技能且排除 fixture。没有修改用户持久配置。
- 单独复制技能生成两图，删除技能副本后搬移输出，通过 localhost 浏览器实际渲染订单校验/失败分支及有界重试/子流程示例。多图切换、放大及适应宽度可用；SVG 导出并独立打开后文字、分支标签、边线、回边和分组样式保留。
- 导出初验发现 HTML 标签后，已在 Mermaid 全局配置显式关闭 `htmlLabels` 并重新生成、渲染和导出；复验确认 SVG 含原生 text 元素且无 foreignObject。
- 流程图语法对照 Mermaid 官方文档（https://mermaid.js.org/syntax/flowchart.html），运行时固定使用内置 Dagre 布局。未执行完整模型调用、远端 CI 或 IDEA 导航；这些不作为本次验证通过项。
