// UserPromptSubmit: on "paws lite|full|ultra|off" or "stop paws", save the mode so it persists
// across sessions, and tell the model which mode is now active.
const { writeMode, parseSwitch, emit } = require("./paws-mode");

let input = "";
process.stdin.on("data", (c) => (input += c));
process.stdin.on("end", () => {
  let prompt = "";
  try { prompt = JSON.parse(input).prompt || ""; } catch {}
  const mode = parseSwitch(prompt);
  if (!mode) return;
  writeMode(mode);
  emit("UserPromptSubmit", mode === "off"
    ? "paws is now off: ignore the paws rules for the rest of this session"
    : `Active paws mode: ${mode}`);
});
