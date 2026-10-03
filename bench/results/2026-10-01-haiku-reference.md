# Reference results: baseline, caveman, ponytail, yagni

Haiku 4.5 via Claude Code CLI 2.1.284, `bench/runners/claude.py`, 1 run per cell, 12 tasks. Raw data: `2026-10-01-haiku-reference.json`; full run (incl. cinder, lantern v1): `../runs/claude/20261001-210832/`.

Cell = pass (✓/✗) and source LOC. Caveman and ponytail were run as plain instruction text (`--append-system-prompt`), not plugins.

| Task | baseline | caveman | ponytail | yagni |
|---|---|---|---|---|
| safe-path | ✓ 12 | ✓ 7 | ✓ 10 | ✓ 20 |
| critic-email | ✓ 35 | ✓ 5 | ✓ 4 | ✓ 7 |
| rate-limit | ✓ 18 | ✓ 19 | ✓ 16 | ✓ 16 |
| sql-user | ✓ 6 | ✓ 6 | ✓ 7 | ✓ 4 |
| auth-token | ✓ 15 | ✓ 18 | ✓ 18 | ✓ 18 |
| csv-sum | ✓ 15 | ✓ 14 | ✓ 11 | ✓ 16 |
| cache | ✓ 11 | ✓ 11 | ✓ 11 | ✓ 11 |
| reuse-slug | ✓ 23 | ✓ 23 | ✓ 23 | ✓ 23 |
| reuse-money | ✓ 10 | ✓ 10 | ✓ 9 | ✓ 10 |
| trace-transfer | ✗ 18 | ✓ 17 | ✗ 16 | ✗ 17 |
| trace-amount | ✓ 10 | ✓ 10 | ✓ 10 | ✓ 10 |
| todo-null | ✓ 226 | ✓ 90 | ✓ 73 | ✓ 226 |

| Arm | Pass | Total LOC | Cost $ | Instruction hash |
|---|---|---:|---:|---|
| baseline | 11/12 | 399 | 0.57 | - |
| caveman | 12/12 | 230 | 0.49 | 09ebdef35a85 |
| ponytail | 11/12 | 208 | 0.49 | 1316a2f3f957 |
| yagni | 11/12 | 378 | 0.55 | 2922f3732948 |

To compare a new arm against these, rerun the same 12 tasks with the same model:

```bash
python bench/runners/claude.py --task safe-path,critic-email,rate-limit,sql-user,auth-token,csv-sum,cache,reuse-slug,reuse-money,trace-transfer,trace-amount,todo-null --arms <your-arm> --models haiku --runs 1
```

Needs `claude` on PATH (desktop copy: `%APPDATA%\Claude\claude-code\<version>\claude.exe`) and a logged-in session.
