# Codex-only agentic benchmark

This project adapts [Ponytail's agentic tasks and scorers](https://github.com/DietrichGebert/ponytail/tree/main/benchmarks/agentic) to the `codex exec` CLI. By default it compares paws, Caveman and Ponytail under the same Codex model, plus an instruction-free `baseline`. The earlier benchmark instruction (`custom`) and an instruction-free `baseline` remain selectable. No Claude CLI, Claude login, Claude plugin, or Anthropic key is required.

The Caveman and Ponytail arms load their published instruction text into the task prompt. Their Claude plugin activation hooks do **not** run in Codex. These results compare the text under Codex, not the full Claude plugins or Ponytail's published Claude scores.

## Requirements

Windows PowerShell, Python 3, and an authenticated `codex` CLI. Feature tasks also require Git and the pinned full-stack template fixture (`cd83fc1`), which the setup script downloads with `-WithTemplate`. Codex access and usage limits apply. The included runner and instructions are from Ponytail commit `e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156`.

## Run

Extract the archive and open PowerShell in its directory:

```powershell
.\setup-codex.ps1
.\run-codex.ps1
```

The default trial runs `safe-path` once for each of the four arms using Codex's default model. To select a model and four repetitions:

```powershell
.\run-codex.ps1 -Tasks 'safe-path,critic-email,rate-limit,sql-user,auth-token,csv-sum,cache' -Model 'YOUR_CODEX_MODEL' -Runs 4 -Workers 2
```

Before any comparison cells, the runner asks Codex to edit a disposable file in `runs-codex/_write-check`. If that fails, it stops and reports the CLI error from the write-check logs. The CLI uses `--approve-for-me`, which selects automatic review with workspace-write access; this flag cannot be combined with `--sandbox`. An outer policy can still make the effective workspace read-only. Failed read-only cells are invalid benchmark data.

Feature tasks use the full-stack template:

```powershell
.\setup-codex.ps1 -WithTemplate
.\run-codex.ps1 -Tasks 'tmpl-fe-datepicker,tmpl-fe-colorpicker,tmpl-fe-command,tmpl-fe-dropzone,tmpl-fe-wizard,tmpl-fe-rating,tmpl-be-duplicate,tmpl-be-search,tmpl-be-count,tmpl-be-archive,tmpl-be-bulkdelete,tmpl-be-csv' -Runs 4 -Workers 2
```

To include an instruction-free baseline, pass `-Arms 'baseline,paws,caveman,ponytail'` to `scripts/run-codex.ps1`. Every arm is a file in `bench/instructions/` (the stem is the arm name); see `bench/instruction-comparison.md` for the roster. Results from September 24 used the old names: old `custom`, `old` and `new` arms have been removed. RTK is a command-output proxy, not an instruction text arm, and requires a separate integration benchmark.

Edit or add files in `bench/instructions/` to change arms. Outputs are saved under `bench/runs/codex/<timestamp>/` as `results.json`, `summary.json`, and individual workspaces with Codex JSONL logs. Results are saved after each completed cell, so interrupted runs retain completed scores. Failed cells are marked incorrect and unsafe and carry an `error` field; inspect `_codex.stderr.txt` and `_codex.jsonl` before interpreting their scores.

## Interpretation

Safety tasks execute deterministic normal and adversarial checks. Feature tasks measure changed code and count a nonempty diff as delivered work; they do not prove feature completeness. Source LOC excludes tests. Codex JSONL provides input/output token counts and wall time; this runner does not estimate monetary cost. The benchmark tells every arm to write code without running tests or the app, so the custom instruction's verification clause cannot be evaluated here. Your global `AGENTS.md` files, if any, can also affect every arm. Use the same model and environment across arms.
