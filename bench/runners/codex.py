#!/usr/bin/env python3
"""Run Ponytail's agentic tasks with Codex CLI and text-only instruction arms."""

import argparse
import concurrent.futures
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import claude as common
from tasks import TASKS


ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = common.BENCH / "runs" / "codex"
ARMS = {"baseline": None, **common.ARM_FILES}
NO_RUN = common.NO_RUN
CELL_TIMEOUT = common.CELL_TIMEOUT


def codex_command(workdir, model):
    codex = shutil.which("codex")
    if not codex:
        raise RuntimeError("codex CLI not found on PATH")
    cmd = [codex, "exec", "--json", "--ephemeral", "--ignore-user-config",
           "--ignore-rules", "--skip-git-repo-check", "--approve-for-me",
           "-C", str(workdir)]
    if model:
        cmd += ["-m", model]
    return cmd + ["-"]


def prompt_for(task_id, arm):
    instruction = ARMS[arm].read_text(encoding="utf-8") if ARMS[arm] else ""
    parts = [
        "Complete the coding task in the current workspace. Edit the files directly.",
        TASKS[task_id]["prompt"],
        NO_RUN,
    ]
    if instruction:
        parts.insert(0, "Additional instructions for this benchmark arm:\n" + instruction)
    return "\n\n".join(parts)


def read_events(path):
    usage = {}
    final_text = ""
    errors = []
    completed = False
    if not path.exists():
        return usage, final_text, errors
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "turn.completed":
            usage = event.get("usage") or {}
            completed = True
        elif event.get("type") == "item.completed":
            item = event.get("item") or {}
            if item.get("type") == "agent_message":
                final_text = item.get("text") or final_text
        elif event.get("type") in ("turn.failed", "error"):
            errors.append(str(event.get("error") or event.get("message") or "unknown error"))
    return usage, final_text, [] if completed else errors


def score_workspace(task_id, arm, model, workdir):
    row = common.score_workspace(task_id, arm, model, workdir)
    task = TASKS[task_id]
    if not task.get("fixture") and not _has_delivered_code(task, workdir):
        row.update(files=0, src_files=0, total_loc=0, src_loc=0,
                   test_files=0, test_loc=0)
    usage, final_text, errors = read_events(workdir / "_codex.jsonl")
    if TASKS[task_id].get("open") and row["total_loc"] == 0 and final_text:
        total, source = common.chat_code_loc(final_text)
        row.update(total_loc=total, src_loc=source, src_files=int(total > 0))
    row.update(
        in_tokens=usage.get("input_tokens"),
        out_tokens=usage.get("output_tokens"),
        cache_tokens=0,  # Codex input_tokens already includes cached input
        cached_input_tokens=usage.get("cached_input_tokens"),
        cost=None,
        duration_ms=_read_duration(workdir),
        error="; ".join(errors) if errors else None,
    )
    exit_path = workdir / "_codex.exit.txt"
    stderr_path = workdir / "_codex.stderr.txt"
    if (not _has_delivered_code(task, workdir) and stderr_path.exists()
            and "read-only sandbox" in stderr_path.read_text(encoding="utf-8", errors="replace")):
        row["error"] = "Codex workspace was read-only; benchmark cell is invalid"
    if not exit_path.exists() or exit_path.read_text().strip() != "0" or errors:
        row.update(correct=0, safe=0)
        if not row["error"]:
            row["error"] = "Codex did not complete successfully"
    return row


def _has_delivered_code(task, workdir):
    seed = task.get("seed", {})
    for name, content in seed.items():
        path = workdir / name
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            return True
    for path in workdir.rglob("*"):
        if (path.is_file() and path.suffix in common.CODE_EXT
                and path.name not in seed and not path.name.startswith((".", "_"))
                and "__pycache__" not in path.parts):
            return True
    return False


def _read_duration(workdir):
    path = workdir / "_codex.duration_ms.txt"
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


def run_cell(task_id, arm, model, workdir):
    task = TASKS[task_id]
    if task.get("fixture"):
        fixture = Path(task["fixture"])
        if not fixture.is_absolute():
            fixture = common.BENCH / "fixtures" / fixture
        if not fixture.is_dir():
            raise FileNotFoundError(f"Missing fixture: {fixture}; run setup-codex.ps1")
        shutil.copytree(fixture, workdir, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("node_modules", ".git", "build", "dist",
                                                       "dist-ssr", ".vite", "*.log", "__pycache__",
                                                       "storage", ".venv", "venv", ".pytest_cache",
                                                       "*.mp4", "*.mp3", "*.wav", "*.mov",
                                                       "*service-account*.json",
                                                       "nul", "con", "prn", "aux",
                                                       "DatePicker*.tsx", "DatePicker*.jsx"))
        manifest = sorted(str(p.relative_to(workdir)).replace("\\", "/")
                          for p in workdir.rglob("*") if p.is_file())
        (workdir / "_fixture_files.json").write_text(json.dumps(manifest), encoding="utf-8")
    for name, content in task.get("seed", {}).items():
        (workdir / name).write_text(content, encoding="utf-8")
    if task.get("fixture"):
        common._git_snapshot(workdir)

    cmd = codex_command(workdir, model)
    started = time.monotonic()
    with open(workdir / "_codex.jsonl", "wb") as stdout, open(workdir / "_codex.stderr.txt", "wb") as stderr:
        proc = subprocess.Popen(cmd, cwd=workdir, stdin=subprocess.PIPE,
                                stdout=stdout, stderr=stderr,
                                start_new_session=(os.name != "nt"))
        try:
            proc.communicate(prompt_for(task_id, arm).encode("utf-8"), timeout=CELL_TIMEOUT)
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            common._tree_kill(proc)
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()
            exit_code = -1
            stderr.write(f"\n[KILLED after {CELL_TIMEOUT}s timeout]".encode())
    (workdir / "_codex.exit.txt").write_text(str(exit_code), encoding="utf-8")
    (workdir / "_codex.duration_ms.txt").write_text(str(round((time.monotonic() - started) * 1000)), encoding="utf-8")
    return score_workspace(task_id, arm, model or "default", workdir)


def check_write_access(model):
    """Stop before paid cells if the nested Codex session cannot edit its workspace."""
    workdir = RUNS_DIR / "_write-check"
    workdir.mkdir(parents=True, exist_ok=True)
    target = workdir / "preflight.txt"
    target.write_text("PENDING\n", encoding="utf-8")
    stdout_path = workdir / "_codex.jsonl"
    stderr_path = workdir / "_codex.stderr.txt"
    prompt = "Edit preflight.txt in this workspace. Replace PENDING with READY. Make no other changes."
    with open(stdout_path, "wb") as stdout, open(stderr_path, "wb") as stderr:
        proc = subprocess.Popen(codex_command(workdir, model), cwd=workdir,
                                stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                                start_new_session=(os.name != "nt"))
        try:
            proc.communicate(prompt.encode("utf-8"), timeout=CELL_TIMEOUT)
        except subprocess.TimeoutExpired:
            common._tree_kill(proc)
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()
            raise RuntimeError("Codex write check timed out; no benchmark cells were run")
    if proc.returncode or target.read_text(encoding="utf-8").strip() != "READY":
        _, final_text, errors = read_events(stdout_path)
        stderr_tail = "\n".join(stderr_path.read_text(encoding="utf-8", errors="replace").splitlines()[-8:])
        event_errors = "; ".join(dict.fromkeys((errors[0], errors[-1]))) if errors else ""
        raise RuntimeError(
            "Codex could not edit its benchmark workspace; no benchmark cells were run. "
            f"See {workdir} logs.\n"
            + (event_errors or final_text or stderr_tail)[-1200:]
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--task", help="comma-separated task IDs")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--arms", default="paws,caveman,ponytail")
    parser.add_argument("--model", help="Codex model; omit to use the CLI default")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    if args.selftest:
        return 1 if common.selftest() else 0
    task_ids = list(TASKS) if args.all else [t.strip() for t in (args.task or "").split(",") if t.strip()]
    arms = [a.strip() for a in args.arms.split(",")]
    if not task_ids or any(t not in TASKS for t in task_ids):
        parser.error("provide valid task IDs with --task, or use --all")
    if not arms or any(a not in ARMS for a in arms):
        parser.error(f"--arms must use: {', '.join(ARMS)}")
    if args.runs < 1 or args.workers < 1:
        parser.error("--runs and --workers must be positive")
    if not shutil.which("codex"):
        parser.error("codex CLI not found on PATH")
    if common.selftest():
        parser.error("benchmark selftest failed")
    try:
        check_write_access(args.model)
    except RuntimeError as exc:
        parser.exit(1, f"Preflight failed: {exc}\n")
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = RUNS_DIR / stamp
    out_dir.mkdir(parents=True, exist_ok=False)
    specs = [(t, a, args.model, i) for t in task_ids for a in arms for i in range(args.runs)]
    print(f"Running {len(specs)} Codex cells with {args.workers} worker(s)", flush=True)

    def one(spec):
        task, arm, model, repeat = spec
        workspace = out_dir / f"{task}__{arm}__{model or 'default'}__{repeat}"
        workspace.mkdir()
        return run_cell(task, arm, model, workspace)

    results = []
    results_path = out_dir / "results.json"
    summary_path = out_dir / "summary.json"
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(one, spec): spec for spec in specs}
        for future in concurrent.futures.as_completed(futures):
            spec = futures[future]
            try:
                row = future.result()
            except Exception as exc:
                row = {"task": spec[0], "arm": spec[1], "model": spec[2] or "default",
                       "correct": 0, "safe": 0, "total_loc": 0, "src_loc": 0,
                       "src_files": 0, "test_files": 0, "cost": None,
                       "error": str(exc)}
            results.append(row)
            print(f"{len(results)}/{len(specs)} {spec[0]} {spec[1]} correct={row['correct']} safe={row['safe']}", flush=True)
            results_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
            summary_path.write_text(json.dumps(common.aggregate(results), indent=2), encoding="utf-8")
    summary = common.aggregate(results)
    common.print_table(summary)
    print(f"Results: {out_dir}")
    return 0 if all(not r.get("error") for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
