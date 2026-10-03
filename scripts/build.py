#!/usr/bin/env python3
"""Generate every paws artifact from src/ (the only place to edit): copy-paste text,
CLAUDE.md/AGENTS.md, and the plugin skills under skills/.

  python scripts/build.py             # write dist/ and skills/
  python scripts/build.py --check     # exit 1 if anything generated is stale (use in CI / pre-commit)
  python scripts/build.py --install DIR [--force]
                                      # copy CLAUDE.md and AGENTS.md into project DIR;
                                      # never overwrites an existing file without --force
"""
import argparse, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "paws.md"
HEADER = "<!-- Generated from src/paws.md by scripts/build.py. Do not edit. -->\n"
FRONT = ("---\nname: paws\ndescription: Always apply to every coding task and answer. Terse replies, "
         "minimal code, root-cause fixes, safeguards kept, tests only for changed code\n"
         "argument-hint: \"[lite|full|ultra|off]\"\n---\n")
PROJECT_FILES = ("dist/claude/CLAUDE.md", "dist/codex/AGENTS.md")


def render():
    core = SRC.read_text(encoding="utf-8").rstrip() + "\n"
    out = {ROOT / "dist/paws.md": core}                                # plain text for custom-instruction boxes
    out.update({ROOT / rel: HEADER + core for rel in PROJECT_FILES})
    out[ROOT / "skills/paws/SKILL.md"] = FRONT + core                   # plugin/skill form (Claude + Codex)
    for f in sorted((ROOT / "src" / "skills").glob("*/SKILL.md")):      # language skills, loaded on demand
        out[ROOT / "skills" / f"paws-{f.parent.name}" / "SKILL.md"] = f.read_text(encoding="utf-8")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--install", metavar="DIR")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    out = render()
    if a.check:
        stale = [str(p.relative_to(ROOT)) for p, t in out.items()
                 if not p.exists() or p.read_text(encoding="utf-8") != t]
        if stale:
            sys.exit("stale (run scripts/build.py): " + ", ".join(stale))
        print("generated files are up to date")
        return
    for p, t in out.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(t, encoding="utf-8")
        print("wrote", p.relative_to(ROOT))
    if a.install:
        dest = Path(a.install)
        for rel in PROJECT_FILES:
            src, target = ROOT / rel, dest / Path(rel).name
            if target.exists() and not a.force:
                print("skip (exists, use --force):", target)
                continue
            shutil.copyfile(src, target)
            print("installed", target)


if __name__ == "__main__":
    main()
