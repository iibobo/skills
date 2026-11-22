---
name: render-sequence-diagrams
description: 创建或修改 Mermaid 时序图，梳理调用顺序、同步与异步消息、返回、条件分支、循环和并行交互，生成可迁移的离线 HTML 并支持 SVG 导出。用于请求链路、业务流程和协议交互；静态类与接口关系图使用 render-class-diagrams。
---

# 绘制可移植时序图

先读[时序图规范](references/sequence-diagram-guidelines.md)。需要语法与分图示例时读[示例](assets/example.md)；修改页面交互时读[展示模板](assets/viewer.html)。

## 绘制与更新

1. 从任务与当前项目确定入口、参与者、结束条件及源码/依赖版本。绘制真实系统时核对入口及关键调用、回调和返回；遵循目标仓库的代码定位规则。概念设计标明假设与待实现部分。
2. 在用户指定位置编写 `<topic>.md`，用标题分隔各个 `sequenceDiagram` 代码块。显式声明参与者，源码类名使用 `as nowrap: 完整类名` 避免自动断词，按规范设置框高；消息写清调用或事件及关键数据；区分请求、返回与异步投递，按规范表达分支、循环和并行。正文注明源码依据、错误路径和省略范围。
3. 运行本技能内的生成器，`<skill-directory>` 指当前 `SKILL.md` 所在目录：

   ```bash
   python3 <skill-directory>/scripts/render_diagrams.py /path/to/topic.md \
     --source-map /path/to/symbols.json --require-source-links
   # 输出到其他目录：追加 --output /path/to/output/topic.html
   # 明确更新已有产物：追加 --overwrite
   ```

   真实 Java 系统默认提供源码导航映射，先读规范中的“源码导航”。概念设计或用户明确要求纯图时可省略；无法确认的类型和方法须补齐依据或报告具体缺项。

   生成器只提取时序图并保留其源码；语法和视觉效果需要浏览器实际渲染核对。运行需要 Python 3.9+ 标准库，查看页面需要现代浏览器。Mermaid.js 与许可证随技能提供，无需联网或安装 Node.js。
4. 浏览器逐图检查调用顺序、箭头、返回、激活区间与分支边界，验证页头图例可折叠、单行标签裁切、左右与键盘切换、适应整图、工具栏折叠、缩放、展示模式和 SVG 导出。窄屏画布允许横向滚动；长流程拆成有明确衔接点的子图。记录无法实际验证的项目。
5. 返回 Markdown、HTML、独立符号映射和模块资源目录路径。搬移或分享时同时带上 HTML 和资源目录；用户只要 Mermaid 片段时按指定范围交付。

## 文件布局

HTML 统一放在交付目录顶层。将 Markdown、符号映射（如适用）归入 `sequence-diagrams/`，审计资料按需放进模块内的 `audits/`。运行资源由生成器写入 `sequence-diagrams/<topic>.assets/`。源 Markdown 位于该模块目录时，默认在其上一层生成同名 HTML；`--output` 可指定 HTML 路径。迁移时保持模块目录与 HTML 的相对位置。

## 完成条件

- 真实调用和并发关系有源码或协议依据；概念设计与已实现行为分清。所有展示的错误分支可追溯，未覆盖的错误路径有说明。
- 每张图的起止、参与者、消息方向及分支含义清楚；激活/结束成对，异步投递不暗示处理已完成。
- HTML 的图数据与 Markdown 代码块一致，资源目录中的 `source.md` 与输入一致；所有新图均实际渲染，SVG 独立打开仍有文字与样式。
- 技能资源改动后，单独复制技能到干净目录运行，再迁移产物并脱离原技能目录验证离线资源。
- 只报告实测验证。此技能接入 Diagram Source Navigator 的符号键协议；生成链接、IDE 索引解析和真实 opened 验收分别报告，不能把提示或 accepted 当成成功打开。

## 生成器回归检查

模板或映射协议变更后运行 `python3 -m unittest discover -s <skill-directory>/tests`，覆盖可复现生成、映射失效拒绝和符号引用校验。JVM 签名核对可用 `scripts/audit_source_map.py`，输入映射中的 symbols 对象与当前项目 classpath；这不等于 IDEA opened 验收。
