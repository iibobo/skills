# 安装与调用

## Codex

本仓库的 `.agents/skills/render-class-diagrams` 是指向 `skills/engineering/render-class-diagrams` 的相对符号链接。检出本仓库后，在该项目的新会话中使用：

```text
$iibobo-skills:render-class-diagrams 为指定模块绘制类与接口关系图
```

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

完成后在目标项目开启新会话，使用 `$render-class-diagrams`。用户级副本需在技能更新后重新同步。本仓库同时带有插件清单，Codex CLI 0.162.0 实测将仓库技能展示为上述带插件前缀的名称；其他宿主以技能选择器展示的名称为准。

## Claude Code

在仓库根目录临时加载，仅对该次会话有效：

```bash
claude --plugin-dir "$PWD"
```

在会话中使用 `/iibobo-skills:render-class-diagrams`。

需要持久安装时，从本地仓库注册本项目的市场，并选择项目范围：

```bash
claude plugin marketplace add "$PWD" --scope project
claude plugin install iibobo-skills@iibobo --scope project
```

这些命令写入项目的 Claude Code 设置；提交设置前检查其中的本机路径。若只想在个人设置中安装，将两个 `--scope project` 均替换为 `--scope user`。

仓库中的插件文件推送到 GitHub 后，其他使用者可将第一条命令的 `"$PWD"` 换为 `iibobo/skills`。本地整理不代表远端已经包含这些文件。

命令已对照 Claude Code 2.1.295 的帮助核对；插件格式参见[清单参考](https://code.claude.com/docs/en/plugins-reference)和[市场指南](https://code.claude.com/docs/en/plugin-marketplaces)。Codex 的用户级目录参见 [OpenAI 官方说明](https://developers.openai.com/api/reference/cli)。真实加载结果见[验证记录](verification.md)。
