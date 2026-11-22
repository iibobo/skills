---
name: render-flowcharts
description: 创建或修改 Mermaid 流程图，梳理处理步骤、条件判断、分支、循环、异常与子流程，生成可迁移的离线 HTML 并支持 SVG 导出。用于业务流程、算法和控制逻辑；跨参与者消息先后使用 render-sequence-diagrams，静态类型关系使用 render-class-diagrams。
---

# 绘制可移植流程图

先读[流程图规范](references/flowchart-guidelines.md)。新建简单图时可复用[基础模板](assets/example.md)；需要手动对齐时看规范中的完整示例。修改查看器时读[展示模板](assets/viewer.html)。

## 绘制与更新

1. **核对流程。** 确定入口、输入、目标和结束条件。真实程序核对关键判断、循环、提前返回和异常，遵循项目的代码定位规则。概念设计注明假设。源 Markdown 正文记录源码或规则依据及省略范围。
2. **选择布局方式。** 单主链、少量分支且容易读清时，直接用 Mermaid 起稿并渲染。出现多级判断、回边、多个异常出口或跨层汇合时，先在工作过程中规划骨架：确定主链方向和中心列、并列节点层级、旁路和回线车道、汇合点与终点。图仍拥挤时，按真实业务阶段拆成总览与子流程。业务语义明确时直接完成布局和验证。
3. **绘制并生成。** 在 `<topic>.md` 用标题分隔 Mermaid 代码块。默认 `flowchart TB`，宽而短的链路可用 `LR`。先用自动布局；关键节点漂移、旁路反复拐弯或标签难辨时，按规范添加 `aligned-layout` 并重新渲染。每条判断出口写明条件。

   ```bash
   python3 <skill-directory>/scripts/render_diagrams.py /path/to/topic.md
   # 指定顶层 HTML 路径：追加 --output /path/to/output/topic.html
   # 更新已有产物：追加 --overwrite
   ```

   生成器使用 Python 3.9+ 标准库，提取带方向的 `flowchart` 或 `graph` 代码块并原样保存。Mermaid.js 和许可证随技能打包。
4. **渲染验收。** 在浏览器逐图走读主链、分支、回边和终点。按[验收清单](references/flowchart-guidelines.md#验收清单)核对节点和标签间距、连线端点与 SVG。查看器或资源变更时，验证切图、图例、缩放、拖动、全屏和迁移后的离线打开。报告实际验证范围。
5. **交付。** 提供 Markdown、顶层 HTML 和对应模块目录。用户只要 Mermaid 或 Markdown 时，按指定范围交付。

## 文件布局

HTML 统一放在交付目录顶层。Markdown 与可选映射放入 `flowcharts/`，审计资料按需放进 `flowcharts/audits/`。运行库、许可证和 Markdown 快照由生成器写入 `flowcharts/<topic>.assets/`。源 Markdown 位于 `flowcharts/` 时，默认在它的上一级生成同名 HTML。搬移时保留 HTML 与模块目录的相对位置。
