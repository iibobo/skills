---
name: render-flowcharts
description: 创建或修改 Mermaid 流程图，梳理处理步骤、条件判断、分支、循环、异常与子流程，生成可迁移的离线 HTML 并支持 SVG 导出。用于业务流程、算法和控制逻辑；跨参与者消息先后使用 render-sequence-diagrams，静态类型关系使用 render-class-diagrams。
---

# 绘制可移植流程图

先读[流程图规范](references/flowchart-guidelines.md)。需要语法与分图示例时读[示例](assets/example.md)；修改页面交互时读[展示模板](assets/viewer.html)。

## 绘制与更新

1. 从任务与当前项目确定入口、输入、完成条件和范围。真实程序核对关键判断、循环、提前返回与异常处理；遵循目标仓库的代码定位规则。业务设计说明规则来源，概念方案标明假设和待实现部分。
2. 在用户指定位置编写 `<topic>.md`，用标题分隔各个 `flowchart TB` 代码块；宽而短的场景可用 `LR`。按规范区分起止、步骤、判断和子流程，为每条判断出口标注具体条件。正文注明源码或业务规则依据及省略范围。
3. 运行本技能内的生成器，`<skill-directory>` 指当前 `SKILL.md` 所在目录：

   ```bash
   python3 <skill-directory>/scripts/render_diagrams.py /path/to/topic.md
   # 输出到其他目录：追加 --output /path/to/output/topic.html
   # 明确更新已有产物：追加 --overwrite
   ```

   生成器提取带方向的 `flowchart` 或 `graph` 代码块并原样保存；语法和视觉效果需要浏览器渲染核对。运行需要 Python 3.9+ 标准库，查看需要现代浏览器；Mermaid.js 与许可证随技能提供，无需联网或安装 Node.js。
4. 浏览器逐图沿每条分支检查可达性、条件覆盖、循环出口和异常终点；检查节点、标签和线条有无遮挡，验证多图切换、适应宽度、缩放及 SVG 导出。窄屏可横向滚动；复杂图按业务阶段拆分并注明衔接点。
5. 返回 Markdown、HTML 和相邻 `<topic>.assets/` 目录路径；搬移时同时提供 HTML 与资源目录。用户只要 Mermaid 片段时尊重该交付范围。

## 完成条件

- 每条业务分支与循环出口有依据，提前返回、失败和取消路径按范围交代清楚；设计假设与已实现行为区分。
- 判断出口可读、无意外孤立节点；非终止流程注明持续运行语义，普通场景从入口可到达明确终点。箭头交叉或回边不会掩盖含义。
- HTML 图数据与输入代码块一致，资源目录的 `source.md` 与输入一致。所有新图均实际渲染；导出 SVG 独立查看仍有文字与样式。
- 技能资源改动后，单独复制技能到干净目录生成，再单独搬移产物验证离线资源；仅报告实测范围。
- 源码依据写在 Markdown 正文；本技能不接入 IDEA 类图导航协议。
