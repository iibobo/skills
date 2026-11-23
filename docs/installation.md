# 安装与调用

## 选择安装方式

插件安装适合通过市场管理整个集合；独立安装适合复制和修改单个技能。同一 Agent 选择一种方式，避免插件副本与独立副本重复出现。本仓库的插件名为 `iibobo-skills`，市场名为 `iibobo`。

下面以已检出本仓库为前提，本地命令均从仓库根目录执行。需要从 GitHub 安装时，须先确保远端已包含当前插件文件；本地修改不会自动同步到远端。

三个技能的生成器兼容 Python 3.9+ 标准库。生产环境和新电脑建议安装仍受维护的 Python 版本，例如 Python 3.12 或 3.14。离线页面需要现代浏览器。分发页面时，请保留顶层 HTML 和对应模块目录的相对位置。IDEA 源码跳转需要另装兼容的 Diagram Source Navigator，并在目标项目中索引相关源码或依赖。[Python 版本支持状态](https://devguide.python.org/versions/)

## 从 ZIP 安装

将 `iibobo-skills-<版本>.zip` 解压到一个保留的目录。解压后的顶层目录包含 `plugin.json`、`.claude-plugin/` 和 `skills/`。进入该目录，执行下文对应宿主的本地市场安装命令。通过 ZIP 安装时无需克隆仓库、保留符号链接或运行 `npm ci`。

如果只安装一个技能，将 `render-<图种>-<版本>.zip` 解压后，把完整技能目录复制到 `~/.agents/skills/`（Codex）或 `~/.claude/skills/`（Claude Code）。新会话中分别用 `$render-<图种>` 或 `/render-<图种>` 调用。Windows 上 `~` 对应当前用户主目录。

## 插件安装

### Codex

添加本地市场并安装插件：

```bash
codex plugin marketplace add "$PWD"
codex plugin add iibobo-skills@iibobo
```

安装后开启新会话，使用 `$iibobo-skills:render-class-diagrams` 绘制类图，`$iibobo-skills:render-sequence-diagrams` 绘制时序图，或 `$iibobo-skills:render-flowcharts` 绘制流程图。这些命令修改个人 Codex 插件配置。

从 GitHub 安装时，将添加市场的命令替换为：

```bash
codex plugin marketplace add iibobo/skills
```

更新 Git 市场快照时运行 `codex plugin marketplace upgrade iibobo`，再运行上面的插件安装命令。命令语法已对照 Codex CLI 0.162.0 帮助和 [OpenAI 官方插件文档](https://developers.openai.com/plugins/build/plugins)核对；本地安装的实测范围见[验证记录](verification.md)。

若 Codex 安装中断，或安装列表显示已安装但新会话缺少技能，先运行 `codex plugin list` 确认状态。如果仍有已安装记录，先运行 `codex plugin remove iibobo-skills@iibobo`，再重新执行安装命令。随后开启新会话并确认三个技能都出现在选择器中。通过同一客户端执行卸载和重装，让客户端管理缓存与启用状态。

### Claude Code

添加本地市场并安装到项目范围：

```bash
claude plugin marketplace add "$PWD" --scope project
claude plugin install iibobo-skills@iibobo --scope project
```

安装后开启新会话，使用 `/iibobo-skills:render-class-diagrams` 绘制类图，`/iibobo-skills:render-sequence-diagrams` 绘制时序图，或 `/iibobo-skills:render-flowcharts` 绘制流程图。这些命令写入项目的 Claude Code 设置；提交设置前检查其中的本机路径。个人安装可将两个 `--scope project` 均替换为 `--scope user`。

从 GitHub 安装时，将添加市场的命令替换为：

```bash
claude plugin marketplace add iibobo/skills --scope project
```

更新时先运行 `claude plugin marketplace update iibobo`，再运行 `claude plugin update iibobo-skills@iibobo --scope project`；个人安装使用 `--scope user`。

命令已对照 Claude Code 2.1.295 帮助核对；插件格式参见[清单参考](https://code.claude.com/docs/en/plugins-reference)和[市场指南](https://code.claude.com/docs/en/plugin-marketplaces)。

## 项目开发与临时加载

### Codex 项目发现

本仓库的 `.agents/skills/render-class-diagrams` 、`.agents/skills/render-sequence-diagrams` 和 `.agents/skills/render-flowcharts` 分别以相对符号链接指向对应的 `skills/engineering/<技能名>` 正式目录。检出本仓库后，在该项目的新会话中使用：

```text
$iibobo-skills:render-class-diagrams 为指定模块绘制类与接口关系图
$iibobo-skills:render-sequence-diagrams 为指定请求链路绘制时序图
$iibobo-skills:render-flowcharts 为指定业务逻辑绘制流程图
```

本仓库同时带有插件清单，Codex CLI 0.162.0 实测将仓库技能展示为上述带插件前缀的名称；其他宿主以技能选择器展示的名称为准。

仓库的项目发现需要 Git 检出时保留符号链接。Codex CLI 0.162.0 的市场安装会省略缓存中的项目发现链接，插件通过清单中的实体目录发现技能。若系统或解压工具把链接还原为普通文件，可使用市场插件安装，或从 `skills/engineering/` 复制完整的实体技能目录进行独立安装。

### Claude Code 临时加载

在仓库根目录临时加载，仅对该次会话有效：

```bash
claude --plugin-dir "$PWD"
```

在会话中使用 `/iibobo-skills:render-class-diagrams` 、`/iibobo-skills:render-sequence-diagrams` 或 `/iibobo-skills:render-flowcharts`。

## 独立技能安装（Codex）

安装到用户级、供其他项目使用时，从仓库根目录复制整个技能目录。下面的命令会在目标已存在时停止，先检查目标并自行决定如何更新：

```bash
python3 - <<'PY'
from pathlib import Path
import shutil
source = Path('skills/engineering/render-class-diagrams')
target = Path.home() / '.agents/skills/render-class-diagrams'
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(source, target)
print(target)
PY
```

完成后在目标项目开启新会话，使用 `$render-class-diagrams`。用户级副本需在技能更新后重新同步。

时序图技能的独立安装方式相同：将上述复制脚本中的两处 `render-class-diagrams` 替换为 `render-sequence-diagrams`，安装后使用 `$render-sequence-diagrams`。

流程图技能的独立安装方式相同：将上述复制脚本中的两处 `render-class-diagrams` 替换为 `render-flowcharts`，安装后使用 `$render-flowcharts`。
