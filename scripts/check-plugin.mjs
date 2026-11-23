#!/usr/bin/env node
// Checks the bucketed, single-plugin repository convention in this skill.
// Copy to scripts/check-plugin.mjs and run from the target repository root.
import { readFileSync, readdirSync, existsSync, realpathSync, lstatSync, readlinkSync } from "node:fs";
import { resolve, relative, isAbsolute, sep } from "node:path";
import { parseDocument } from "yaml";

const root = realpathSync(resolve(process.argv[2] ?? "."));
const promoted = new Set(["engineering", "productivity"]);
const buckets = [...promoted, "in-progress", "misc", "deprecated"];
const failures = [];
const check = (condition, message) => {
  if (!condition) failures.push(message);
};
const read = (path) => readFileSync(resolve(root, path), "utf8");
const json = (path) => JSON.parse(read(path));
const label = (path) => relative(root, path);

function checkDiscoveryLink(name, skill) {
  const link = `.agents/skills/${name}`;
  const path = resolve(root, link);
  if (!lstatSync(path, { throwIfNoEntry: false })?.isSymbolicLink()) {
    failures.push(`${link}: expected a relative symbolic link to ${skill}`);
    return;
  }
  const target = readlinkSync(path);
  const expected = relative(resolve(root, ".agents/skills"), resolve(root, skill)).split(sep).join("/");
  check(target === expected, `${link}: expected target ${expected}, got ${target}`);
  check(existsSync(resolve(path, "SKILL.md")), `${link}: missing linked SKILL.md`);
}

function checkPortableFiles(directory) {
  for (const item of readdirSync(directory, { withFileTypes: true })) {
    const path = resolve(directory, item.name);
    if (item.isSymbolicLink()) {
      failures.push(`${label(path)}: package skill resources as regular files`);
    } else if (item.isDirectory()) {
      checkPortableFiles(path);
    }
  }
}

function yamlFile(source, where) {
  const doc = parseDocument(source, { strict: true, uniqueKeys: true });
  if (doc.errors.length) {
    failures.push(`${where}: ${doc.errors[0].message.split("\n")[0]}`);
    return null;
  }
  return doc.toJS();
}

function readmeLink(file, target, mode) {
  if (!existsSync(resolve(root, file))) {
    failures.push(`${file}: missing index`);
    return;
  }
  const source = read(file);
  const needles = [`](${target})`, `](./${target})`];
  const positions = needles.flatMap((needle) => {
    const found = [];
    let at = source.indexOf(needle);
    while (at !== -1) {
      found.push(at);
      at = source.indexOf(needle, at + needle.length);
    }
    return found;
  });
  check(positions.length > 0, `${file}: missing link to ${target}`);
  if (!mode || !positions.length) return;
  const headers = [...source.matchAll(/^(?:#{1,6}\s+|\*\*)(User-invoked|Model-invoked)(?:\*\*)?\s*$/gm)];
  const grouped = positions.some((at) => {
    const header = headers.filter((match) => match.index < at).at(-1);
    return header?.[1] === mode;
  });
  check(grouped, `${file}: ${target} must appear under ${mode}`);
}

try {
  const plugin = json(".claude-plugin/plugin.json");
  const marketplace = json(".claude-plugin/marketplace.json");
  const pkg = json("package.json");
  check(typeof pkg.version === "string" && pkg.version.length > 0, "package.json: missing version");
  check(plugin.version === pkg.version, "package.json and plugin.json versions differ");
  check(Array.isArray(plugin.skills), "plugin.json: skills must be an explicit directory array");
  const paths = Array.isArray(plugin.skills) ? plugin.skills : [];
  check(new Set(paths).size === paths.length, "plugin.json: duplicate skill paths");
  check(Array.isArray(marketplace.plugins) && marketplace.plugins.length === 1,
    "marketplace.json: this checker expects a single-plugin marketplace");
  const entry = marketplace.plugins?.[0];
  check(entry?.name === plugin.name, "marketplace entry and plugin names differ");
  check(entry?.source === "./", "marketplace entry: source must be ./ for this root-plugin convention");

  for (const path of paths) {
    if (typeof path !== "string" || !path.startsWith("./")) {
      failures.push(`plugin.json: expected a ./ skill directory path, got ${JSON.stringify(path)}`);
      continue;
    }
    const absolute = resolve(root, path);
    if (!existsSync(absolute)) {
      failures.push(`plugin.json: missing directory ${path}`);
      continue;
    }
    const fromRoot = relative(root, realpathSync(absolute));
    check(fromRoot !== ".." && !fromRoot.startsWith("../") && !isAbsolute(fromRoot),
      `plugin.json: ${path} resolves outside the plugin`);
    check(existsSync(resolve(absolute, "SKILL.md")), `${path}: missing SKILL.md`);
  }

  const names = new Set();
  const expected = new Set();
  for (const bucket of buckets) {
    const directory = resolve(root, "skills", bucket);
    if (!existsSync(directory)) continue;
    for (const item of readdirSync(directory, { withFileTypes: true })) {
      if (!item.isDirectory() && !item.isSymbolicLink()) continue;
      const skill = `skills/${bucket}/${item.name}`;
      if (!existsSync(resolve(root, skill, "SKILL.md"))) continue;
      check(!item.isSymbolicLink(), `${skill}: package real directories rather than development symlinks`);
      check(!names.has(item.name), `${skill}: skill names must be globally unique`);
      names.add(item.name);
      const match = read(`${skill}/SKILL.md`).match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
      check(Boolean(match), `${skill}/SKILL.md: missing YAML frontmatter`);
      if (!match) continue;
      const data = yamlFile(match[1], `${skill}/SKILL.md`);
      check(data?.name === item.name, `${skill}: frontmatter name must match directory`);
      check(/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(item.name) && item.name.length <= 64,
        `${skill}: use a lowercase hyphenated name of at most 64 characters`);
      check(typeof data?.description === "string" && data.description.trim().length > 0,
        `${skill}: missing description`);
      check(data?.["disable-model-invocation"] === undefined || typeof data["disable-model-invocation"] === "boolean",
        `${skill}: disable-model-invocation must be a boolean`);
      const uiPath = `${skill}/agents/openai.yaml`;
      let ui;
      if (existsSync(resolve(root, uiPath))) ui = yamlFile(read(uiPath), uiPath);
      else failures.push(`${uiPath}: missing invocation metadata`);
      for (const key of ["display_name", "short_description"]) {
        check(typeof ui?.interface?.[key] === "string" && ui.interface[key].trim().length > 0,
          `${uiPath}: missing interface.${key}`);
      }
      const implicit = ui?.policy?.allow_implicit_invocation;
      check(implicit === undefined || typeof implicit === "boolean", `${uiPath}: invocation policy must be a boolean`);
      const explicitOnly = data?.["disable-model-invocation"] === true;
      check(explicitOnly === (implicit === false), `${skill}: Claude Code and Codex invocation policies disagree`);
      const mode = explicitOnly ? "User-invoked" : "Model-invoked";
      readmeLink(`skills/${bucket}/README.md`, `${item.name}/SKILL.md`, promoted.has(bucket) ? mode : null);

      const docs = `docs/${bucket}/${item.name}.md`;
      if (promoted.has(bucket)) {
        expected.add(`./${skill}`);
        checkDiscoveryLink(item.name, skill);
        if (item.isDirectory()) checkPortableFiles(resolve(root, skill));
        readmeLink("README.md", `${skill}/SKILL.md`, mode);
        if (existsSync(resolve(root, docs))) {
          const page = read(docs);
          for (const section of ["What it does", "When to reach for it", "Common questions", "It's working if", "Where it fits"]) {
            check(page.split(/\r?\n/).includes(`## ${section}`), `${docs}: missing ${section}`);
          }
        } else failures.push(`${docs}: missing promoted skill page`);
      } else {
        check(!existsSync(resolve(root, docs)), `${docs}: non-promoted skills have no docs page`);
        const index = read("README.md");
        check(!index.includes(`](${skill}/SKILL.md)`) && !index.includes(`](./${skill}/SKILL.md)`),
          `README.md: non-promoted skill ${skill} is listed`);
      }
    }
  }
  check(expected.size > 0, "plugin: include at least one useful promoted skill");
  for (const path of expected) check(paths.includes(path), `plugin.json: missing promoted skill ${path}`);
  for (const path of paths) check(expected.has(path), `plugin.json: unexpected or non-promoted skill ${path}`);
  if (!failures.length) console.log(`Plugin organisation checks passed (${expected.size} promoted skills).`);
} catch (error) {
  failures.push(`${label(root) || "repository"}: ${error.message}`);
}

if (failures.length) {
  console.error(failures.join("\n"));
  process.exitCode = 1;
}
