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

## 构建发布包

从已验收的固定提交或版本标签检出一份干净副本，在仓库根目录执行：

```bash
python3 scripts/check_release.py --install
python3 scripts/package_plugin.py --output dist
```

打包脚本读取正式技能清单和 Git 跟踪的技能文件，生成一个双宿主插件 ZIP 和每个技能的独立 ZIP。整包生成标准 Agent Plugins 清单和 Claude Code 本地市场清单，并将技能放在 ZIP 的 `skills/<name>/`。源仓库仍按分类组织。构建版本取自 `package.json` 同步后的插件清单。同一版本的 ZIP 已存在时，用空目录重新构建。

CI 在 Linux、macOS 和 Windows 上验证独立技能解包及入口文件，对图表技能额外验证生成和迁移。Linux 同时验证双宿主安装与技能发现。公开分发前由项目版权所有者确认插件代码授权，并随包提供许可证及必要的第三方声明。远端推送、标签、市场注册和持久安装按具体任务授权执行。[OpenAI 插件打包规范](https://developers.openai.com/plugins/build/plugins)
