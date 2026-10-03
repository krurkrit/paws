// Shared mode state for the paws hooks: ~/.paws/mode holds lite|full|ultra|off (default full).
const fs = require("fs");
const os = require("os");
const path = require("path");

const FILE = path.join(os.homedir(), ".paws", "mode");
const MODES = ["lite", "full", "ultra", "off"];

function readMode() {
  try {
    const m = fs.readFileSync(FILE, "utf8").trim();
    return MODES.includes(m) ? m : "full";
  } catch {
    return "full";
  }
}

function writeMode(m) {
  fs.mkdirSync(path.dirname(FILE), { recursive: true });
  fs.writeFileSync(FILE, m);
}

// "/paws ultra", "/paws:paws lite", "$paws full", "paws off", "stop paws" -> mode; anything else -> null
function parseSwitch(prompt) {
  if (/^\s*stop paws\b/i.test(prompt)) return "off";
  const m = /^\s*(?:\/paws(?::paws)?|\$paws|paws)\s+(lite|full|ultra|off)\b/i.exec(prompt);
  return m ? m[1].toLowerCase() : null;
}

function emit(event, text) {
  process.stdout.write(JSON.stringify({ hookSpecificOutput: { hookEventName: event, additionalContext: text } }));
}

module.exports = { readMode, writeMode, parseSwitch, emit };
