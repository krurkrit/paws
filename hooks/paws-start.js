// SessionStart: inject the paws core rules and the saved mode, so they apply to every request
// (a skill alone loads on demand). Mode "off" injects nothing.
const fs = require("fs");
const path = require("path");
const { readMode, emit } = require("./paws-mode");

const mode = readMode();
if (mode !== "off") {
  const rules = fs.readFileSync(path.join(__dirname, "..", "skills", "paws", "SKILL.md"), "utf8")
    .replace(/^---[\s\S]*?---\s*/, "");
  emit("SessionStart", `${rules}\nActive paws mode: ${mode}`);
}
