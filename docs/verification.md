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

## 时序图布局与真实源码导航复核

日期：2026-11-22（Asia/Shanghai）。正式时序图技能源码与此前修复的安装缓存曾存在差异，现已将紧凑标签布局、完整参与者名称、65 单位框高、统一缩放、上下镜像、符号键导航、映射哈希与覆盖校验同步到正式目录，再同步安装缓存。未修改版本或发布远端。

- `npm run check` 通过：类图 5 项、时序图 8 项、流程图 6 项；两项 Claude 插件严格验证通过，保留既有 README 安装命令建议。
- Spring AI 2.0.2 七图在实际 IDEA 新版插件会话中检查：首次 116/124 opened，包含 4 项未索引的 QuestionAnswerAdvisor 和 4 项多模块同名控制器歧义。导入项目已有 source-navigation POM 后自动检查为 120/124 opened、4 ambiguous、0 not_found。
- 对第 6、7 图的上下四个 KnowledgeController 入口分别选择 chapter-07-rag 候选，观察到四次最终 opened，IDEA 编辑器确认为第 7 章源码。自动报告保留 ambiguous，交互选择单独记载，不宣称自动验收 100%。报告位于验证项目 design/sequence-source-open-audit.json 与 sequence-source-manual-open-audit.json。
- 本次未为消除歧义写死机器文件 URL，也未将未索引类型替换为其他类。

## 流程图查看器样式统一

日期为 2026-11-23（Asia/Shanghai）。流程图技能的正式源码与本机安装副本已同步。公共界面沿用时序图的紧凑布局与类图的紫色界面配色。流程图保留原生 SVG 标签与 Dagre 布局。

- Node 24.21.0 和 Python 3.14.0 下通过 `npm run check`，覆盖类图 6 项、时序图 9 项和流程图 7 项。技能结构校验也通过。
- Chrome 158.0.8127.36 离线打开迁移后的 Spring AI 五图，逐张校验渲染与独立 SVG。比较流程图、时序图的页头、选中标签、面板、工具栏和画布样式。
- 验证按钮与键盘切图、窄屏选中标签定位、工具栏折叠、适应画布、固定比例、Shift + 滚轮、浏览器与屏幕全屏，以及退出全屏后的导航恢复。
- 放大后的画布平移在 Chrome 158.0.8127.36 使用实际输入事件复验。300% 下验证普通滚轮、触控滑动和鼠标左键双向拖动，覆盖普通视图、浏览器全屏和屏幕全屏，并确认松手后停止拖动。
- 连线复验覆盖 Spring AI 五图的原生 SVG 导出。相邻的斜线保持单段，绕行的多段连线由水平与垂直段组成；流式响应图的文本片段分支与回边分别通过单段斜线检查。

## 时序图和流程图图例

日期为 2026-11-23（Asia/Shanghai）。两个技能的模板均在页头右上方提供默认折叠的符号说明，按图类型显示对应示例。

- Chrome 158.0.8127.36 离线查看迁移后的两份页面。已核对鼠标与键盘展开、Esc 与点击外部关闭、短窄窗口内滚动，以及展开后画布高度保持原值。
- Spring AI 示例的 5 张流程图与 7 张时序图均重新渲染，时序图保留源码导航入口。

## 流程图旁路与圆角

Chrome 158.0.8127.36 离线复验 Spring AI 五图的标签、箭头、交互和 SVG 导出。总览的 Advisor 异常连线从节点右边引出，省去起点折返；必要转弯使用小圆角，流式响应图的文本片段分支和回边仍是单段斜线。

## 基础流程图模板

参考 ISO 5807 和 Visio 基础流程图符号，更新流程图技能的默认可复制示例和查看器图例。Chrome 158.0.8127.36 离线验证订单模板的输入输出形状，以及通知投递示例的重试回路、箭头和 SVG 导出。

## 图表交付目录布局

HTML 统一位于交付目录顶层。类图、时序图和流程图的 Markdown、运行资源、符号映射与审计文件按模块归档。Chrome 158.0.8127.36 离线打开迁移后的 Spring AI 输出目录，全部 18 张图均加载成功，类图与时序图的源码导航入口可见。项目 Markdown 与 HTML 的本地引用均可解析。

## 流程图布局工作流

日期为 2026-11-23（Asia/Shanghai）。对照 Codex 内置浏览器中当前 Spring AI 的五张流程图，核对主链、并列分支、回线、异常通道及右上图例。把简单图直接起稿、复杂图先排骨架的选择写入技能入口，并整理手动对齐参数及验收清单。

技能的 7 项流程图测试通过。用独立技能副本生成规范中的手动对齐示例，确认 HTML 图数据、Markdown 快照和模块资源相对路径。

## 跨机器安装与项目入口校验

日期为 2026-11-23（Asia/Shanghai）。

- 干净仓库副本通过 `npm run check` 和两项 Claude Code 2.1.295 严格清单校验。移除发现链接、换成可解析的绝对链接，以及在技能资源中加入符号链接，均被结构检查拒绝。
- 使用空的 `CODEX_HOME` 从本地市场安装。Codex CLI 0.162.0 报告已安装且已启用，安装缓存省略了项目发现链接。在仓库外执行 `skills/list` 仍发现全部三个已启用技能，且没有解析错误。Claude Code 的临时加载也列出全部三个技能。
- 分别从 Codex 安装缓存复制三个技能，各自生成两张示例图。移除技能副本并搬移产物后，三个 HTML 引用的本地资源均完整。
- 验证在 macOS 本机的隔离环境完成。GitHub 市场安装、Windows 和 Linux 实机、模型调用及 IDEA 跳转未复测。

## 0.1.1 生成器与发布包回归

日期为 2026-11-23（Asia/Shanghai）。

- `npm run check` 通过，包含技能结构校验和 27 项测试（类图 9 项、时序图 11 项、流程图 7 项）。三组入口通过 `load_tests` 纳入各技能的 `tests/`。新用例覆盖类图覆盖生成时清理旧源码副本、发布失败回滚、行内方法映射，以及时序图无别名参与者、隐式参与者和激活简写。
- Claude Code 2.1.295 的两个严格校验在仓库及解压后的发布包中均通过。Codex CLI 0.162.0 与 Claude Code 2.1.295 在空白配置中从本地 ZIP 解包目录安装 0.1.1，均列出三个技能。Codex 单独使用标准插件清单时也发现三个技能。
- Python 3.12.9 和 3.14.0 下，分别解包三个独立技能生成示例，移除技能目录并迁移生成物后，本地链接和 Markdown 快照校验通过。
- Chrome 158.0.8127.36 禁止 HTTP(S) 请求后，实际渲染迁移后的六张示例图，验证切图和三个 SVG 导出。两个带映射的样例均生成预期的类名及方法链接。IDEA 实际跳转与完整模型调用未复测。
- CI 新增 Linux 双宿主安装校验与 macOS、Windows 独立包校验。上述实测在 macOS 本地完成，远端 CI 和 GitHub 市场安装尚待验证。

## 覆盖生成、源码导航与发布检查

日期为 2026-11-28（Asia/Shanghai）。在 macOS 使用 Node.js 24.21.0、Python 3.14.0、Codex CLI 0.162.0、Claude Code 2.1.295 和 Chrome 158.0.8127.37 验证。

- `npm run check` 通过，覆盖 33 项测试。回归用例核对 HTML 写入失败后旧页面与资源完整、时序图重新生成后旧映射清理、映射文件名冲突及源码链接匹配。
- 两项 Claude Code 严格校验通过。`python3 scripts/check_release.py --install` 验证三个独立技能解包、生成与产物迁移，并在隔离配置中用两个宿主安装和发现三个技能。临时仓库中的纯 Markdown 正式技能通过发布验证，未发布技能的项目发现链接被结构检查拒绝。
- Chrome 从本地 HTML 核对同名参与者的顶部和底部源码入口、多行消息及行尾连字符。显式 `nowrap:` 让被自动拆行的长方法名恢复源码链接。导出的独立 SVG 保留源码链接。
- 流程图缓存完成布线的 SVG。Chrome 本地用 198 条边的图单次比较往返切换，切回耗时由约 782 毫秒降至 9 毫秒。复核返回后图形、缩放、节点源码标记及 SVG 导出仍可用。
- 实际 IDEA 跳转、模型调用和远端 CI 尚待复验。
