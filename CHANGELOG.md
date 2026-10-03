# Changelog

All notable changes to Paws. Versions follow the `version` in `.claude-plugin/plugin.json`
and `.codex-plugin/plugin.json`.

## [Unreleased]

## [1.0.0] - 2026-10-03

First release.

- Core instruction set (`src/paws.md`): terse replies, build only what's asked, reuse before adding,
  root-cause fixes, safeguards kept, read less, test only changed code.
- Modes `lite`, `full`, `ultra`, `off`, saved to `~/.paws/mode` in plugin installs.
- Language skills for C# and TypeScript, loaded on demand.
- Claude Code and Codex plugins, skills-only and copy-paste installs.
- Plugin directory listing details: icon, documentation, support, privacy policy and terms links.
- Agentic benchmark with reference results for Haiku 4.5, Sonnet 5.5 and Opus 5.5.
- CI: checks generated files, manifests and hooks on every push and pull request.

[Unreleased]: https://github.com/krurkrit/paws/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/krurkrit/paws/releases/tag/v1.0.0
