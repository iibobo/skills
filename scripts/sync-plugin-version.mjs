import { readFileSync, writeFileSync } from "node:fs";

const packageFile = new URL("../package.json", import.meta.url);
const pluginFile = new URL("../.claude-plugin/plugin.json", import.meta.url);
const { version } = JSON.parse(readFileSync(packageFile, "utf8"));
const plugin = JSON.parse(readFileSync(pluginFile, "utf8"));
plugin.version = version;
writeFileSync(pluginFile, JSON.stringify(plugin, null, 2) + "\n");
