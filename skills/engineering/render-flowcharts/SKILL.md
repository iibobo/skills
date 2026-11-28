---
name: render-flowcharts
description: 绘制或修改 Mermaid 流程图，说明步骤、判断、循环、异常和子流程。可生成支持节点源码跳转及 SVG 导出的离线 HTML。
---

# 流程图

1. **取证。** 确定入口、结果、判断、异常和回边。按项目约定定位。无索引时用 `rg -n` 查声明，再定点读分支或写入代码，记录类名和行号。概念图标明假设。
2. **先定分图和方向。** 主链跨多个处理阶段，或多级判断与回边集中时，在起稿前拆成「总览 + 子流程」，标明展开点。主链短且分支少可直接画。纵向主链用 `TB`，短而宽的链路用 `LR`。批量作图时先渲染最复杂的一张确认尺寸、标签和回线，版式样张可暂不配映射。[规划布局](references/flowchart-guidelines.md#规划布局)
3. **绘制并生成。** 用标题分隔带方向的 `flowchart` 或 `graph` 代码块，判断出口写明条件，循环写明出口。参考[基础模板](assets/example.md)与[符号表](references/flowchart-guidelines.md#符号与标签)。自动布局的关键走线仍有问题时再用[手动对齐](references/flowchart-guidelines.md#手动对齐)。若只要 Mermaid 或 Markdown，提交所需内容即可。

   真实代码的 HTML 默认为入口、关键判断、写入、异常和子流程添加[节点映射](references/flowchart-guidelines.md#源码跳转)。

   ```bash
   python3 <skill-directory>/scripts/render_diagrams.py /path/to/topic.md --require-source-links
   ```

   `<skill-directory>` 是当前技能目录。该开关要求每张图至少有一条映射。仅含概念图、用户要求纯图，或代码图与概念图混排时可省略。混排时逐张核对代码图覆盖。输出路径用 `--output` 指定。更新时用 `--overwrite` 替换生成资源。
4. **验收并交付。** 逐图用 DOM 检查 SVG、错误状态和预期节点入口。只给布局复杂、改版或疑似拥挤的图截图。按[验收清单](references/flowchart-guidelines.md#验收清单)检查方向、端点、回线和标签。交付顶层 HTML 和整个 `flowcharts/` 模块（含 Markdown 与资源）。单独报告 IDEA 实际打开的结果。

将手写文件放在 `<topic>.assets/` 之外。生成需要 Python 3.9+。查看需要现代浏览器。
