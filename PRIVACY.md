# Privacy

Paws is a set of instructions and two small local hooks. It has no server and sends nothing off your machine.

- **Collected or sent:** nothing. Paws makes no network requests and has no analytics or telemetry.
- **Stored:** only the mode you choose (`lite`, `full`, `ultra` or `off`), as one word in `~/.paws/mode`, so it
  carries over to new sessions. Delete the file to reset it.
- **Prompts:** the prompt hook checks each prompt for a mode switch such as `paws ultra`, then discards it.
  Prompt text is never stored.
- **Third parties:** none. Your conversations go only to the coding agent you already use (Claude Code or
  Codex), under that provider's own privacy policy.

Questions: [open an issue](https://github.com/krurkrit/paws/issues).
