# Repository maintenance

技能内容与运行资源以 `skills/<bucket>/<name>/` 为唯一来源；项目发现入口放在 `.agents/skills/<name>`，使用指向正式目录的相对符号链接。插件清单只引用仓库内的真实技能目录。

新增或调整技能时，先读 [技能编写与分发约定](docs/authoring.md)。安装说明统一维护在 [docs/installation.md](docs/installation.md)，其他文档链接到该文件。

修改清单、路径、调用策略或版本后运行 `npm run check`，并用 `claude plugin validate . --strict` 和 `claude plugin validate .claude-plugin/plugin.json --strict` 检查平台格式。技能资源迁移后，单独复制技能到临时目录验证生成，再单独迁移产物验证离线资源。

<!-- CODEGRAPH_START -->
## CodeGraph

In repositories indexed by CodeGraph (a `.codegraph/` directory exists at the repo root), reach for it BEFORE grep/find or reading files when you need to understand or locate code:

- **MCP tool** (when available): `codegraph_explore` answers most code questions in one call — the relevant symbols' verbatim source plus the call paths between them, including dynamic-dispatch hops grep can't follow. Name a file or symbol in the query to read its current line-numbered source. If it's listed but deferred, load it by name via tool search.
- **Shell** (always works): `codegraph explore "<symbol names or question>"` prints the same output.

If there is no `.codegraph/` directory, skip CodeGraph entirely — indexing is the user's decision.
<!-- CODEGRAPH_END -->

@/Users/lzp/.codex/RTK.md
