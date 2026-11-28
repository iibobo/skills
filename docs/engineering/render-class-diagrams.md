# 类图

## What it does

用 Mermaid 表达类、接口、直接继承和核心方法。真实 Java 代码的 HTML 默认提供类与方法的源码入口。

## When to reach for it

了解模块的类型职责、扩展点或依赖关系时使用。

## Common questions

- **如何处理重载？** 图上可简写。源码映射保留实际声明类与擦除后的参数类型。
- **可只生成 Mermaid 吗？** 可以，在请求中指定格式。安装和调用见[安装文档](../installation.md)。

## It's working if

每条关系有标签和源码依据，适用的类与展示方法均有可核对的入口。

## Where it fits

[技能入口](../../skills/engineering/render-class-diagrams/SKILL.md)包含制图步骤。涉及运行时调用顺序时用[时序图](render-sequence-diagrams.md)。
