---
name: render-class-diagrams
description: 绘制或修改 Mermaid 类图，说明类型职责、继承、接口实现和核心方法。可生成支持类与方法源码跳转及 SVG 导出的离线 HTML。
---

# 类图

1. **取证。** 确定模块和源码版本。按项目约定定位。无索引时用 `rg -n` 查包名、类型声明与方法签名，再定点读有歧义的逻辑。记录源码或同版本依赖的出处。
2. **绘制。** 按模块或职责分图。用标题分隔 `classDiagram` 代码块，默认 `direction TB`。每条关系写明含义，用 `note for` 说明职责。按[样式与示例](references/class-diagram-guidelines.md#固定视觉样式)保留类型标记和配色。需要代码块写法时查看[示例](assets/example.md)。用户只要 Mermaid 或 Markdown 时，提交所需内容即可。
3. **生成。** 真实代码的 HTML 默认链接每个类及展示方法。用步骤 1 的证据填写[源码映射](references/class-diagram-guidelines.md#idea-插件源码跳转)，确认重载、声明类和擦除后的参数类型。

   ```bash
   python3 <skill-directory>/scripts/render_diagrams.py /path/to/topic.md \
     --source-map /path/to/symbols.json --require-source-links
   ```

   `<skill-directory>` 是当前技能目录。概念图或用户明确要求纯图时省略两个映射参数。真实代码若有无法核实的目标，报告具体缺项。输出路径用 `--output` 指定。更新时用 `--overwrite` 替换生成资源。
4. **验收并交付。** 按[验收清单](references/class-diagram-guidelines.md#验收清单)逐图检查 SVG、错误状态和预期源码入口。截图用于布局复杂、改版或疑似拥挤的图。改查看器时再查[交互约定](references/class-diagram-guidelines.md#交互约定)。交付顶层 HTML 和整个 `class-diagrams/` 模块（含 Markdown、适用的映射与资源）。单独报告 IDEA 实际打开的结果。

将手写文件放在 `<topic>.assets/` 之外。生成需要 Python 3.9+。查看需要现代浏览器。
