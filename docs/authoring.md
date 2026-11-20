# 技能编写与分发约定

## 内容与调用

正式技能放在 `skills/engineering/` 或 `skills/productivity/`。需要其他领域分类时，同步调整 `scripts/check-plugin.mjs` 的分类常量。测试中的技能放在 `in-progress`，低频维护和退役技能分别放在 `misc`、`deprecated`；对应目录在有内容时再创建。

每个技能目录包含 `SKILL.md` 和 `agents/openai.yaml`，目录名与 frontmatter 的 `name` 一致。运行时需要的规范、脚本、模板和许可证均放在该技能内。对特定分支才有用的参考材料，用说明读取条件的相对链接引出。

默认支持自动发现和显式调用。仅允许用户显式调用的技能，同时设置 `disable-model-invocation: true` 和 `policy.allow_implicit_invocation: false`。根索引与正式分类索引按 `Model-invoked`、`User-invoked` 分组。

## 晋升与发现

添加正式技能或晋升测试技能时，同时更新以下位置：

- `.claude-plugin/plugin.json` 中的显式 `skills` 目录数组。
- 根 `README.md` 和分类 `README.md` 中指向 `SKILL.md` 的链接。
- `docs/<bucket>/<name>.md`，包含用途、适用时机、常见问题、成功表现和定位。
- `.agents/skills/<name>` 项目发现链接，指向同一仓库内的内容源。

非正式技能保留分类索引，不进入插件数组、根技能清单或正式技能说明页。单技能集合使用 README 导航；技能增多到需要选择工作流时再引入路由技能。

## 版本与验证

`package.json` 拥有版本号，`scripts/sync-plugin-version.mjs` 在 npm 版本生命周期中同步插件清单。依赖变更提交锁文件，CI 使用 `npm ci`。

结构检查证明清单、索引、调用策略和版本一致；平台验证证明当前 CLI 接受格式。真实发现、调用和浏览器行为分别记录证据，结果写入 `docs/verification.md` 并注明工具版本与验证范围。

新增发布流程时延续 npm 的版本来源；需要自动版本 PR 时再接入 Changesets。远端推送、标签、市场注册和持久安装按具体任务授权执行。
