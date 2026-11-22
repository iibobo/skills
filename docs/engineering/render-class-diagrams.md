# render-class-diagrams

## What it does

绘制或修改 Mermaid 类与接口关系图，沿用内置配色、方法分类、关系标注和布局规则，输出 Markdown、离线 HTML 及相邻资源目录。默认根据真实源码为类与展示方法创建符号映射，接入调用方的源码导航。

## When to reach for it

需要理解类型继承、接口实现、职责与核心方法，或需要可搬移、无需联网的类图页面时使用。该技能专注于 `classDiagram`；流程图应选择其他工作流。

生成页面需要 Python 3.9+，查看页面需要现代浏览器。HTML 运行资源已经随技能提供。核对真实类型和方法时，还需提供对应源码或依赖版本；IDE 导航需具备接收链接的环境。

## Common questions

- **如何调用？** 在本仓库的 Codex 中使用 `$iibobo-skills:render-class-diagrams`，单独安装技能时使用 `$render-class-diagrams`；在 Claude Code 插件会话中使用 `/iibobo-skills:render-class-diagrams`。完整步骤见[安装文档](../installation.md)。
- **怎样搬移产物？** 同时复制生成的 `.html` 和同名 `.assets/` 目录；它们不再依赖技能安装路径。
- **需要安装 Node.js 或 Mermaid 吗？** 运行生成器不需要；本仓库的插件维护校验才需要 Node.js。
- **会自动创建源码跳转链接吗？** 默认会，生成时提供符号映射并检查类与展示方法的覆盖。缺少源码或准确签名时会报告缺项；用户明确要求纯图或绘制无真实源码的概念示例时可省略。实际打开需通过兼容的 IDEA 插件，目标项目需导入对应源码或依赖。
- **源码跳转等于验证通过吗？** 需要分别验证映射覆盖、IDE 解析和实际打开；仅接受请求不代表已打开源码。

## It's working if

每条继承与实现关系都有源码依据和文字说明，HTML 展示与 Markdown 中的类图一致，移走技能目录后产物仍能离线打开。默认交付还包含通过覆盖检查的符号映射 JSON；IDE 解析及实际打开结果按实测范围记录。

## Where it fits

这是 `engineering` 分类中的正式技能，可由匹配任务自动触发，也可手动调用。[SKILL.md](../../skills/engineering/render-class-diagrams/SKILL.md) 是执行步骤的来源，规范、模板、脚本与第三方许可证均保留在技能目录内。

导航标签支持原生横向滚动、触控板滚动和鼠标惯性拖动。滑动浏览标签，点击选择图表；左右按钮与键盘仍可切图。滚动条隐藏，选中标签平滑进入可见区域，减少动态效果时停用额外惯性。
