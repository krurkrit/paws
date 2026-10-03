# Contributing

Issues and pull requests are welcome. Paws aims to stay short, so a change should earn its words.

## Edit the source, not the output

`src/paws.md` and `src/skills/*` are the only files to edit. `dist/` and `skills/` are generated:

```bash
python scripts/build.py          # regenerate dist/ and skills/
python scripts/build.py --check  # what CI runs; fails if generated files are stale
```

## Changing a rule

Change one rule at a time and back it with numbers (see [Change Paws](README.md#change-paws)):

1. Rerun the fixed task set (see [bench/README.md](bench/README.md)) and compare with `bench/results/`.
2. Keep the change only if code size, answer length, pass rate and cost don't get worse.
3. Put the before/after numbers in the pull request.

## Hooks and manifests

- Hooks in `hooks/` use only Node built-ins. CI runs them against a temp home directory.
- When releasing, bump `version` in both `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`
  (CI checks they match), add a `CHANGELOG.md` entry and tag `vX.Y.Z`.
