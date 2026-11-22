# 安装与调用

## 选择安装方式

插件安装适合通过市场管理整个集合；独立安装适合复制和修改单个技能。同一 Agent 选择一种方式，避免插件副本与独立副本重复出现。本仓库的插件名为 `iibobo-skills`，市场名为 `iibobo`。

下面以已检出本仓库为前提，本地命令均从仓库根目录执行。需要从 GitHub 安装时，须先确保远端已包含当前插件文件；本地修改不会自动同步到远端。

## 插件安装

### Codex

添加本地市场并安装插件：

```bash
codex plugin marketplace add "$PWD"
codex plugin add iibobo-skills@iibobo
```

安装后开启新会话，使用 `$iibobo-skills:render-class-diagrams` 绘制类图，或 `$iibobo-skills:render-sequence-diagrams` 绘制时序图。这些命令修改个人 Codex 插件配置。

从 GitHub 安装时，将添加市场的命令替换为：

```bash
codex plugin marketplace add iibobo/skills
```

更新 Git 市场快照时运行 `codex plugin marketplace upgrade iibobo`，再运行上面的插件安装命令。命令语法已对照 Codex CLI 0.162.0 帮助和 [OpenAI 官方插件文档](https://developers.openai.com/plugins/build/plugins)核对；本地安装的实测范围见[验证记录](verification.md)。

### Claude Code

添加本地市场并安装到项目范围：

```bash
claude plugin marketplace add "$PWD" --scope project
claude plugin install iibobo-skills@iibobo --scope project
```

安装后开启新会话，使用 `/iibobo-skills:render-class-diagrams` 绘制类图，或 `/iibobo-skills:render-sequence-diagrams` 绘制时序图。这些命令写入项目的 Claude Code 设置；提交设置前检查其中的本机路径。个人安装可将两个 `--scope project` 均替换为 `--scope user`。

从 GitHub 安装时，将添加市场的命令替换为：

```bash
claude plugin marketplace add iibobo/skills --scope project
```

更新时先运行 `claude plugin marketplace update iibobo`，再运行 `claude plugin update iibobo-skills@iibobo --scope project`；个人安装使用 `--scope user`。

命令已对照 Claude Code 2.1.295 帮助核对；插件格式参见[清单参考](https://code.claude.com/docs/en/plugins-reference)和[市场指南](https://code.claude.com/docs/en/plugin-marketplaces)。

## 项目开发与临时加载

### Codex 项目发现

本仓库的 `.agents/skills/render-class-diagrams` 和 `.agents/skills/render-sequence-diagrams` 分别以相对符号链接指向对应的 `skills/engineering/<技能名>` 正式目录。检出本仓库后，在该项目的新会话中使用：

```text
$iibobo-skills:render-class-diagrams 为指定模块绘制类与接口关系图
$iibobo-skills:render-sequence-diagrams 为指定请求链路绘制时序图
```

本仓库同时带有插件清单，Codex CLI 0.162.0 实测将仓库技能展示为上述带插件前缀的名称；其他宿主以技能选择器展示的名称为准。

### Claude Code 临时加载

在仓库根目录临时加载，仅对该次会话有效：

```bash
claude --plugin-dir "$PWD"
```

在会话中使用 `/iibobo-skills:render-class-diagrams` 或 `/iibobo-skills:render-sequence-diagrams`。

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
