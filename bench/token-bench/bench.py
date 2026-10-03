#!/usr/bin/env python3
"""Benchmark custom instructions via `claude -p`.

Arms  = src/*.md and bench/instructions/*.md (each becomes CLAUDE.md in a fresh temp project) + "none".
Tasks = fixed fixtures below, each with an objective pass/fail check.
Output: results.csv (one row per run) + summary table (cost per passing run).

Usage:
  python bench.py --selftest                     # no model calls; checks fixtures
  python bench.py --claude <path-to-claude> -n 3 # real run
Add arms by dropping more .md files in bench/instructions/.
"""
import argparse, csv, json, re, shutil, statistics, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).parent
PY = sys.executable

# ---------- tasks ----------
STATS = '''def moving_average(xs, n):
    """Return the average of each window of size n."""
    if n <= 0:
        raise ValueError("n must be positive")
    return [sum(xs[i:i + n]) / n for i in range(len(xs) - n)]
'''
STATS_T = '''import unittest
from stats import moving_average

class T(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(moving_average([1, 2, 3, 4], 2), [1.5, 2.5, 3.5])
    def test_full_window(self):
        self.assertEqual(moving_average([1, 2, 3], 3), [2.0])
    def test_bad_n(self):
        with self.assertRaises(ValueError):
            moving_average([1], 0)
    def test_too_big(self):
        self.assertEqual(moving_average([1], 2), [])
'''
TEXT = '''def title_case(s):
    if not isinstance(s, str):
        raise TypeError("s must be str")
    return " ".join(w.capitalize() for w in s.split())
'''
SLUG_HIDDEN = '''import unittest
from text import slugify

class T(unittest.TestCase):
    def test_a(self): self.assertEqual(slugify("Hello, World!"), "hello-world")
    def test_b(self): self.assertEqual(slugify("  a   b "), "a-b")
    def test_c(self): self.assertEqual(slugify(""), "")
    def test_d(self):
        with self.assertRaises(TypeError): slugify(5)
'''
CALC = '''def add(a, b):
    return a - b

def mul(a, b):
    return a * b
'''
CALC_T = '''import unittest
from calc import add, mul

class T(unittest.TestCase):
    def test_add(self): self.assertEqual(add(2, 3), 5)
    def test_mul(self): self.assertEqual(mul(2, 3), 6)
'''
OTHER = '''def shout(s):
    return s.upper() + "!"
'''
OTHER_T = '''import unittest
from other import shout

class T(unittest.TestCase):
    def test_shout(self): self.assertEqual(shout("a"), "A!")
'''
UNITTEST = [PY, "-m", "unittest", "discover", "-q"]

TASKS = {
    "bugfix": dict(
        files={"stats.py": STATS, "test_stats.py": STATS_T},
        prompt="moving_average drops the last window. Fix it.",
        cmd=UNITTEST),
    "feature": dict(
        files={"text.py": TEXT},
        prompt=("Add slugify(s) to text.py: lowercase, runs of non-alphanumerics "
                "become a single '-', strip leading/trailing '-'. Raise TypeError "
                "if s is not a str."),
        hidden={"test_slug_hidden.py": SLUG_HIDDEN},
        cmd=UNITTEST),
    "qa": dict(
        files={},
        prompt=("Difference between a Docker bind mount and a named volume, "
                "and when to use each?"),
        regex=[r"bind", r"volume", r"(?i)host"]),
    "testscope": dict(
        files={"calc.py": CALC, "test_calc.py": CALC_T,
               "other.py": OTHER, "test_other.py": OTHER_T},
        prompt="add() in calc.py returns the wrong result. Fix it.",
        cmd=UNITTEST),
}
TEST_CMD = re.compile(r"unittest|pytest")
TARGETED = re.compile(r"test_calc|test_stats|::| -k |test_slug")


# ---------- helpers ----------
def write(d: Path, files):
    for name, body in files.items():
        (d / name).write_text(body, encoding="utf-8")


def check(task, d: Path, answer: str) -> bool:
    if "regex" in task:
        return all(re.search(r, answer) for r in task["regex"])
    write(d, task.get("hidden", {}))
    return subprocess.run(task["cmd"], cwd=d, capture_output=True).returncode == 0


def parse_stream(stdout: str):
    bash, final = [], {}
    for line in stdout.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "assistant":
            for c in ev.get("message", {}).get("content", []):
                if c.get("type") == "tool_use" and c.get("name") == "Bash":
                    bash.append(c.get("input", {}).get("command", ""))
        elif ev.get("type") == "result":
            final = ev
    tests = [c for c in bash if TEST_CMD.search(c)]
    full = [c for c in tests if not TARGETED.search(c)]
    u = final.get("usage", {})
    return dict(
        input_tok=u.get("input_tokens", 0),
        cache_read=u.get("cache_read_input_tokens", 0),
        cache_write=u.get("cache_creation_input_tokens", 0),
        output_tok=u.get("output_tokens", 0),
        cost=final.get("total_cost_usd", 0.0),
        turns=final.get("num_turns", 0),
        secs=round(final.get("duration_ms", 0) / 1000, 1),
        test_runs=len(tests), full_suite_runs=len(full),
        answer=final.get("result", "") or "")


def run_one(claude, arm, instr, name, task, model, max_turns):
    with tempfile.TemporaryDirectory(prefix="ibench-") as t:
        d = Path(t)
        write(d, task["files"])
        if instr:
            (d / "CLAUDE.md").write_text(instr, encoding="utf-8")
        cmd = [claude, "-p", "--output-format", "stream-json", "--verbose",
               "--permission-mode", "acceptEdits",
               "--allowedTools", "Bash,Edit,Write,Read,Grep,Glob",
               "--setting-sources", "project,local",
               "--max-turns", str(max_turns)]
        if model:
            cmd += ["--model", model]
        p = subprocess.run(cmd, cwd=d, input=task["prompt"], text=True,
                           capture_output=True, encoding="utf-8", errors="replace")
        if p.returncode != 0 and not p.stdout.strip():
            sys.exit(f"claude failed ({arm}/{name}): {p.stderr.strip()[:500]}")
        m = parse_stream(p.stdout)
        m["passed"] = check(task, d, m.pop("answer"))
        return m


def preflight(claude):
    out = subprocess.run([claude, "--help"], capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stdout
    missing = [f for f in ("--setting-sources", "--allowedTools", "--max-turns",
                           "--output-format", "--permission-mode") if f not in out]
    if missing:
        sys.exit(f"claude lacks flags: {missing}. Adjust run_one().")


def selftest():
    bad = 0
    for name, task in TASKS.items():
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            write(d, task["files"])
            ok = check(task, d, "")  # untouched fixture must FAIL
            print(f"{name:10} untouched -> {'FAIL(ok)' if not ok else 'PASS(bad)'}")
            bad += ok
    sys.exit(1 if bad else 0)


def summarize(rows):
    arms = sorted({r["arm"] for r in rows})
    head = ["arm", "pass%", "out_tok", "in+cache_tok", "cost$", "turns",
            "secs", "full_suite", "$/pass"]
    print("| " + " | ".join(head) + " |")
    print("|" + "---|" * len(head))
    for a in arms:
        rs = [r for r in rows if r["arm"] == a]
        mean = lambda k: statistics.mean(float(r[k]) for r in rs)
        passes = sum(r["passed"] for r in rs)
        cost = sum(float(r["cost"]) for r in rs)
        inp = statistics.mean(float(r["input_tok"]) + float(r["cache_read"])
                              + float(r["cache_write"]) for r in rs)
        per = f"{cost / passes:.3f}" if passes else "n/a"
        print(f"| {a} | {100 * passes / len(rs):.0f} | {mean('output_tok'):.0f} | "
              f"{inp:.0f} | {mean('cost'):.3f} | {mean('turns'):.1f} | "
              f"{mean('secs'):.0f} | {mean('full_suite_runs'):.1f} | {per} |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--claude", default=shutil.which("claude") or "claude")
    ap.add_argument("-n", type=int, default=3, help="runs per arm per task")
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-turns", type=int, default=12)
    ap.add_argument("--tasks", default=",".join(TASKS))
    ap.add_argument("--arms", default=None, help="comma list; default all + none")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
    preflight(a.claude)

    arms = {"none": ""}
    for f in sorted([*(HERE.parents[1] / "src").glob("*.md"), *(HERE.parent / "instructions").glob("*.md")]):
        arms[f.stem] = f.read_text(encoding="utf-8")
    if a.arms:
        arms = {k: v for k, v in arms.items() if k in a.arms.split(",")}

    rows = []
    out = HERE / "results.csv"
    for name in a.tasks.split(","):
        for arm, instr in arms.items():
            for i in range(a.n):
                m = run_one(a.claude, arm, instr, name, TASKS[name], a.model,
                            a.max_turns)
                rows.append(dict(task=name, arm=arm, run=i, **m))
                print(f"{name}/{arm}/{i}: pass={m['passed']} out={m['output_tok']} "
                      f"cost={m['cost']:.3f}", flush=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print()
    summarize(rows)


if __name__ == "__main__":
    main()
