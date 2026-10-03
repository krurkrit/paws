# Reference results: Sonnet 5.5 (all arms)

Claude Sonnet 5.5 via Claude Code CLI 2.1.284, `bench/runners/claude.py`, 1 run per cell. Raw data: `2026-10-02-sonnet55-reference.json`.
Paws modes = `src/paws.md` + `Active paws mode: X`; `+skills` adds the matching C#/TypeScript skill.

## Code: 12 C#/TypeScript tasks (total lines)

| Arm | Lines | vs baseline | Cost | vs baseline | Time | vs baseline | Correct |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 1442 | +0% | $0.80 | +0% | 189s | +0% | 12/12 |
| caveman | 1439 | -0% | $0.91 | +13% | 199s | +6% | 12/12 |
| ponytail | 509 | -65% | $0.72 | -10% | 122s | -36% | 12/12 |
| paws-lite+skills | 698 | -52% | $0.68 | -15% | 122s | -35% | 12/12 |
| paws+skills | 642 | -55% | $0.70 | -13% | 135s | -29% | 12/12 |
| paws-ultra+skills | 560 | -61% | $0.65 | -19% | 116s | -39% | 12/12 |

## Answers: 10 non-code tasks (words)

| Arm | Words | vs baseline | Cost | vs baseline | Time | vs baseline | Correct |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 3569 | +0% | $0.46 | +0% | 120s | +0% | 10/10 |
| caveman | 2568 | -28% | $0.42 | -9% | 87s | -28% | 10/10 |
| ponytail | 2259 | -37% | $0.44 | -4% | 66s | -45% | 10/10 |
| paws-lite | 2088 | -41% | $0.38 | -16% | 69s | -42% | 10/10 |
| paws | 1947 | -45% | $0.38 | -17% | 68s | -44% | 10/10 |
| paws-ultra | 1586 | -56% | $0.37 | -19% | 60s | -50% | 10/10 |

Task lists: `bench/results/logs/sonnet55-code.log` and `sonnet55-txt.log`. Rerun an arm with `python bench/runners/claude.py --task <tasks> --arms <arm> --models sonnet55`.
