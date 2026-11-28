# 时序图规范

## 消息与控制结构

- 每图表达一个可走读的场景，从入口到结果。参与者用稳定的英文 ID 显式声明，按调用方向排列。子图标出与总览的衔接点。
- 核对同步、返回、异步投递的区别。用 `A->>B: method(args)` 表示同步调用，`B-->>A: 结果` 表示返回，`A-)B: 事件` 表示投递。收到消息与处理结束分别建模。并行应有实现依据，返回 Publisher 或 Future 的时间只能说明对象返回的时点。
- `alt/else/end` 用于互斥路径，`opt/end` 用于可选分支，`loop/end` 写明迭代条件，`par/and/end` 用于并行，`critical/option/end` 用于需要互斥或原子处理的临界区。激活区间成对结束，异常分支写明触发条件与调用方处理。
- 默认用 `autonumber`。用 `Note over A,B: 说明` 标出事务或边界。用 `participant Model as nowrap: ChatModelCallAdvisor` 保留类型名，组合角色可在职责分隔处用 `<br/>`。用实际渲染核对文本、保留字和箭头。

## 源码导航

`--init-source-map` 从同一图源填好 `diagrams`。每项包含原文的 SHA-256 `sourceHash`、按 ID 索引的 `participants`，以及按箭头顺序排列的 `messages`（含 `from`、`to`、`label`）。保留这些字段的原值，图源变化后生成新的模板并核对差异。

- 在 `symbols` 中填写真实的 `className` 与可选 `methods`。方法用 `methodName` 和擦除后的 `parameterTypes` 定位。零参数用 `[]`。重载按调用实参核对，继承方法填写实际声明类。
- 在参与者或消息的 `links` 中添加 `{text, symbol, method?}`。符号键指向 `symbols`，方法键指向对应的 `methods`，`text` 为连续显示片段。返回、外部事件等无准确目标时填写具体 `reason`。长方法名被自动拆行时使用 `A->>B: nowrap: methodName()` 并同步更新模板。
- 传入 `--source-map` 即校验所有图的哈希与覆盖。也可在 Markdown 加 `<!-- sequence-viewer: {"sourceMap":"symbols.json"} -->` 自动读取相对输入文件的映射。若要用 JVM 核对准确签名，将 `symbols` 对象另存为 JSON，传给 `scripts/audit_source_map.py`，并按 `--help` 提供 classpath 和报告路径。

## 验收清单

1. 在同一个浏览器会话逐图确认 `#status` 已隐藏、`#canvas svg` 存在且有尺寸，并核对 `[data-source-symbol]`、消息方法标记及 SVG 的 `data-source-link-error`。有浏览器脚本环境时，可按图序等待 `await select(i)` 后取值，一次返回失败项。
2. 走读消息先后、方向、异常和并发边界。对拥挤、改版或布局不确定的图截图，检查参与者上下镜像、标签和分组。抽查独立 SVG 的文字、样式和源码标记。
3. 目标项目索引完成后，在 IDEA 中用 Diagram Source Navigator 打开本次 HTML，实测参与者与方法入口。仅 `opened` 计为打开成功。`not_found` 核对依赖及版本，`ambiguous` 按实际模块选候选并单独记录结果。普通浏览器和 JVM 签名核对分别说明实测范围。

## 查看器维护

改模板时核对紧凑图例和场景导航、普通视图与全屏、键盘切图、触控与拖动，以及受影响的 SVG 导出。默认两端镜像、参与者框高 65 SVG 单位。以 `<!-- sequence-viewer: {"initialZoom":0.71} -->` 在 Markdown 指定整组初始比例（0.1–3，默认 1）。跨场景保留手动比例。

检查图例与实际图形颜色一致：参与者浅蓝。调用、返回与异步箭头深灰蓝。判断浅黄、循环淡紫、并行青绿。注释浅黄、激活条蓝。若用 `rect rgb(220, 252, 231)` 或 `rect rgb(254, 226, 226)` 标记成功与失败，写清对应结果。

模板维护后运行 `python3 -m unittest discover -s <skill-directory>/tests`。用独立技能生成并迁移产物，复验受影响的渲染、交互和映射入口。需要临时校验脚本时，保存完整脚本并显式传入路径。先检查语法和单图样例，再批量运行。
