# 时序图

## What it does

展示参与者之间的调用、返回、异步投递、分支和并行关系。真实代码的 HTML 默认支持参与者和方法跳转。

## When to reach for it

解释请求链路、回调、业务交互或消息消费时使用。

## Common questions

- **如何开始做符号映射？** 用生成器的 `--init-source-map` 提取本次图源的哈希、参与者和消息，再填写实际目标。
- **如何使用？** 按[安装文档](../installation.md)调用。交付格式可指定为 Mermaid、Markdown 或离线 HTML。

## It's working if

每条消息的方向、时点和同步语义都有依据，场景之间有明确衔接，已映射的方法可在页面定位。

## Where it fits

[技能入口](../../skills/engineering/render-sequence-diagrams/SKILL.md)包含生成及验证步骤。只关心单条处理路径的判断规则时用[流程图](render-flowcharts.md)。
