# render-flowcharts

## What it does

绘制或修改 Mermaid 流程图，表达处理步骤、条件判断、分支、循环、异常和子流程。输出 Markdown、可离线查看的 HTML 与相邻资源目录；页面支持多图切换、缩放、适应宽度及 SVG 导出。

## When to reach for it

梳理业务规则、算法和控制逻辑，核对不同条件下的处理路径时使用。跨参与者消息顺序选择 [render-sequence-diagrams](render-sequence-diagrams.md)，静态类型关系选择 [render-class-diagrams](render-class-diagrams.md)。

生成需要 Python 3.9+，查看需要现代浏览器；运行库随技能提供，无需联网或安装 Node.js。真实系统根据源码或业务规则作图，概念设计会说明假设和省略范围。

## Common questions

- **如何调用？** Codex 插件中使用 `$iibobo-skills:render-flowcharts`，独立安装时使用 `$render-flowcharts`；Claude Code 插件中使用 `/iibobo-skills:render-flowcharts`。安装和更新见[安装文档](../installation.md)。
- **怎样描述任务？** 例如：“根据当前订单处理逻辑画流程图，标出库存不足、保存失败和重试出口，输出离线 HTML。”
- **支持哪些源码？** 支持带方向的 `flowchart` 和兼容别名 `graph` Mermaid 代码块；可使用纵向或横向布局。
- **能否只要 Mermaid？** 可以，明确要求片段或 Markdown 即可。
- **如何搬移？** 同时复制 `.html` 与同名 `.assets/` 目录。技能文件夹也可单独复制使用。
- **支持 IDEA 跳转吗？** 当前流程图不接入类图导航协议；源码和规则依据写在 Markdown 正文。

## It's working if

每个判断出口的条件清晰，循环有停止条件或明确的持续运行语义，错误和提前返回路径有交代。所有图均能渲染、切换和缩放，导出 SVG 可独立查看；产物迁移后可离线打开，图源码与 Markdown 一致。

## Where it fits

这是 `engineering` 分类中的正式技能，支持自动发现和显式调用。[SKILL.md](../../skills/engineering/render-flowcharts/SKILL.md) 维护执行步骤，规范、示例、脚本、模板与运行库保留在技能目录内，可与其他绘图技能分别分发。
