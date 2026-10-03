# Reference results (open-ended 'vibe' tasks): baseline, lantern v1, caveman, ponytail

Haiku 4.5, Claude Code CLI 2.1.284, 1 run per cell, source LOC. Raw: `2026-10-01-haiku-vibe-reference.json`; full run (incl. cinder v1): `../runs/claude/20261001-232217/`. No pass/fail check; completeness not judged.

| Task | baseline | lantern | caveman | ponytail |
|---|---|---|---|---|
| vibe-todo | 107 | 109 | 94 | 62 |
| vibe-password | 107 | 83 | 82 | 58 |
| vibe-shortener | 116 | 97 | 52 | 44 |
| vibe-md2html | 123 | 142 | 119 | 51 |
| vibe-csvstats | 41 | 37 | 38 | 30 |
| vibe-langgraph | 78 | 81 | 74 | 39 |
| vibe-restapi | 116 | 82 | 54 | 107 |
| vibe-scraper | 83 | 44 | 90 | 33 |
| vibe-logparse | 47 | 38 | 39 | 23 |
| vibe-rename | 178 | 277 | 219 | 75 |
| vibe-adventure | 228 | 253 | 291 | 141 |
| vibe-jsonconf | 292 | 262 | 130 | 41 |

| Arm | Total LOC | Cost $ | Out tokens | Turns |
|---|---:|---:|---:|---:|
| baseline | 1516 | 0.60 | 44970 | 39 |
| lantern | 1505 | 0.53 | 35276 | 35 |
| caveman | 1282 | 0.51 | 29273 | 37 |
| ponytail | 704 | 0.47 | 25475 | 26 |

Rerun an arm: `python bench/runners/claude.py --task vibe-todo,vibe-password,vibe-shortener,vibe-md2html,vibe-csvstats,vibe-langgraph,vibe-restapi,vibe-scraper,vibe-logparse,vibe-rename,vibe-adventure,vibe-jsonconf --arms <arm> --models haiku`
