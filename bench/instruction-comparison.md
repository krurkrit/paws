# Instruction comparison

## Arms

All arms live in `src/paws.md` plus [`bench/instructions/`](instructions); the file stem is the arm name.

| Arm | File | Former name | Mechanism |
|---|---|---|---|
| Paws | `paws.md` | merge of cinder and lantern | Terse replies, read less, root-cause fixes, named safeguards, test only changed code once per round |
| Caveman | `caveman.md` | caveman-SKILL | Terse technical prose |
| Ponytail | `ponytail.md` | skills/ponytail/SKILL | Minimal implementation and reuse |
| Baseline | none | baseline | No additional text |
| RTK | [rtk-ai/rtk](https://github.com/rtk-ai/rtk) | | Command-output proxy; not a prompt arm |

## Explicit property coverage

A check means the instruction explicitly addresses the property. The score counts checks; it is **not** an empirical quality grade.

| Arm | Brief replies | Reuse/small diff | Safeguards | Verification | Downstream effects | Score |
|---|:---:|:---:|:---:|:---:|:---:|---:|
| Paws | ✓ | ✓ | ✓ | ✓ | ✓ | 5/5 |
| Caveman | ✓ |  |  |  |  | 1/5 |
| Ponytail | ✓ | ✓ | ✓ | ✓ |  | 4/5 |
| Baseline |  |  |  |  |  | 0/5 |

The downstream-effects property means explicitly calling for required migrations, configuration, environment variables, or comparable follow-on changes. Cinder and Lantern cover it only loosely (Cinder: "required side effects"; Lantern: root-cause and sibling-caller checks).

## Local Codex benchmark

Pending expanded run. The existing `20260924-080717` safety and `20260924-081736` feature runs contain the earlier `custom` text (since removed), Caveman, and Ponytail arms. Each task was run once with the default Codex model. Safety tasks have deterministic normal and adversarial checks. The feature scorer only counts a nonempty code diff as delivered; it does not verify behavior or completeness. The common `NO_RUN` prompt also prevents the arms from executing their own tests, so verification rules are not directly measured.

## RTK evidence

RTK compresses supported shell-command output, a different mechanism from the instruction arms. Its own documentation says command-output savings are not equivalent to total-token or cost savings: [RTK README](https://github.com/rtk-ai/rtk/blob/develop/README.md#how-savings-work). A separate two-run Codex benchmark on one repository-porting task reported RTK at 76.92% harness score and 7.54M total tokens, versus its no-plugin baseline at 78.85% and 6.66M tokens: [public data and methodology](https://github.com/Tura-AI/benchmark/blob/main/blog_data/token-saving-plugin-eza/README.md). Its authors note the small sample and substantial between-run variation. Those numbers are **not** directly comparable with the local tasks above.
