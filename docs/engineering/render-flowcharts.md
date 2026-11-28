# 流程图

## What it does

表达步骤、条件、循环、异常和子流程。真实代码的 HTML 默认支持从关键节点跳到 Java 源码行。

## When to reach for it

解释业务规则、算法或控制逻辑时使用。复杂流程先拆成总览和子流程。

## Common questions

- **支持哪些图源？** 支持带方向的 `flowchart` 或 `graph`。调用方式见[安装文档](../installation.md)。
- **如何配置源码入口？** 在 Mermaid 图块中按节点 ID 填写全限定类名与行号。见[映射示例](../../skills/engineering/render-flowcharts/references/flowchart-guidelines.md#源码跳转)。

## It's working if

各判断有清晰的条件，回边与异常有明确落点，每张图可独立读清。

## Where it fits

[技能入口](../../skills/engineering/render-flowcharts/SKILL.md)包含布局、生成和验收步骤。跨参与者的消息先后使用[时序图](render-sequence-diagrams.md)。
