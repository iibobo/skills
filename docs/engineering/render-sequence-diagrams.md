# render-sequence-diagrams

## What it does

绘制或修改 Mermaid 时序图，说明参与者之间的调用顺序、返回、异步消息、分支、循环及并行处理。输出 Markdown、可离线查看的 HTML 和相邻资源目录，页面支持多图切换、缩放、适应宽度及 SVG 导出。

## When to reach for it

梳理请求链路、业务交互、回调或消息消费流程时使用。需要静态类型继承与接口实现关系时，选择 [render-class-diagrams](render-class-diagrams.md)。

生成需要 Python 3.9+，查看需要现代浏览器；运行库随技能提供，无需联网或安装 Node.js。真实系统的调用顺序需要可读取的源码、协议或跟踪记录作为依据；概念设计会注明假设。

## Common questions

- **如何调用？** Codex 插件中使用 `$iibobo-skills:render-sequence-diagrams`，独立安装时使用 `$render-sequence-diagrams`；Claude Code 插件中使用 `/iibobo-skills:render-sequence-diagrams`。安装和更新见[安装文档](../installation.md)。
- **怎样描述任务？** 例如：“根据当前订单接口源码画创建订单的时序图，包含校验失败和异步通知，输出离线 HTML。”
- **能否只要 Mermaid？** 可以，明确要求片段或 Markdown 即可。
- **如何搬移？** 同时复制 `.html` 与同名 `.assets/` 目录。示例和运行资源均在技能内，单独复制技能也可生成。
- **支持 IDEA 源码跳转吗？** 当前时序图技能不接入 Diagram Source Navigator 的类图导航协议；源码依据在 Markdown 正文列出。

## It's working if

图中每条消息的方向、先后与同步/异步语义有依据，分支和错误处理清楚；所有图能渲染、切换和缩放，导出 SVG 可独立查看。产物迁移后仍能离线打开，Markdown 与页面的图源码一致。

## Where it fits

这是 `engineering` 分类的正式技能，支持自动发现和显式调用。[SKILL.md](../../skills/engineering/render-sequence-diagrams/SKILL.md) 维护执行步骤，规范、模板、脚本和运行库均在该技能目录内；它与类图技能各自独立分发。
