---
name: render-sequence-diagrams
description: 绘制或修改 Mermaid 时序图，说明参与者之间的调用、返回、异步消息、分支与并发。可生成支持源码跳转及 SVG 导出的离线 HTML。
---

# 时序图

1. **取证。** 确定场景、参与者和源码版本。按项目约定定位。无索引时用 `rg -n` 查入口、声明和调用点，再定点读返回、异常及异步边界。按包名、声明和调用实参核对目标类与重载。
2. **绘制。** 用标题分隔 `sequenceDiagram` 代码块。长调用链按可衔接的场景拆分。显式声明参与者，Java 类型别名用 `as nowrap: 完整类型名`。核对[消息语法](references/sequence-diagram-guidelines.md#消息与控制结构)，需要完整示例时打开[示例](assets/example.md)。用户只要 Mermaid 或 Markdown 时，提交所需内容即可。
3. **生成。** 真实代码的 HTML 默认映射参与者和消息方法。首次生成时用模板命令提取每张图的哈希、参与者和消息，填写[源码映射](references/sequence-diagram-guidelines.md#源码导航)后执行生成命令。

   ```bash
   python3 <skill-directory>/scripts/render_diagrams.py /path/to/topic.md \
     --init-source-map /path/to/symbols.json
   python3 <skill-directory>/scripts/render_diagrams.py /path/to/topic.md \
     --source-map /path/to/symbols.json
   ```

   `<skill-directory>` 是当前技能目录。更新映射时复用已核实的符号，用新的模板文件核对变化。模板命令保护已有文件。概念图或用户明确要求纯图时，可直接生成且省略映射参数。输出路径用 `--output` 指定。更新时用 `--overwrite` 替换生成资源。
4. **验收并交付。** 逐图用 DOM 检查 SVG、错误状态和源码入口，截图只看拥挤、换行或有复杂分组的场景。按[验收清单](references/sequence-diagram-guidelines.md#验收清单)核对消息与分组。交付顶层 HTML 和整个 `sequence-diagrams/` 模块（含 Markdown、适用的映射与资源）。单独报告 IDEA 实际打开的结果。

将手写文件放在 `<topic>.assets/` 之外。生成需要 Python 3.9+。查看需要现代浏览器。
