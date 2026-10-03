#!/usr/bin/env python3
"""Draw the README benchmark charts (light + dark SVG) and print the README result tables, both
computed from the saved reference results in bench/results/.

  python scripts/charts.py            # writes docs/charts/*.svg
  python scripts/charts.py --tables   # also prints the README result tables (markdown)

Savings are against baseline, per-run averages: a positive number is saved, a negative number (−)
means the arm used more than baseline. One decimal place, dropped when it's .0. Answers (non-code) first, then code: charts put answers left, code right.

Colors come from the dataviz reference palette: Caveman orange and Ponytail aqua (categorical slots
2-3), Paws lite/full/ultra as an ordinal blue ramp (validated with --ordinal in both modes). Every
bar is also labeled by row name. Text is Inter (fallback Noto Sans), numbers JetBrains Mono
(fallback Consolas), both 14px.
"""
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "charts"
RESULTS = ROOT / "bench" / "results"
FS = 14
STYLE = ("<style>"
         ".t{font-family:Inter,'Noto Sans',sans-serif;font-size:14px}"
         ".n{font-family:'JetBrains Mono',Consolas,monospace;font-size:14px}"
         ".b{font-weight:600}"
         "</style>")

THEMES = {
    "light": {"surface": "#fcfcfb", "text": "#0b0b0b", "muted": "#52514e", "axis": "#d6d5d0",
              "caveman": "#eb6834", "ponytail": "#1baf7a",
              "lite": "#86b6ef", "full": "#3987e5", "ultra": "#184f95"},
    "dark": {"surface": "#1a1a19", "text": "#ffffff", "muted": "#c3c2b7", "axis": "#3d3d3a",
             "caveman": "#d95926", "ponytail": "#199e70",
             "lite": "#256abf", "full": "#5598e7", "ultra": "#9ec5f4"},
}
ROWS = [("Caveman", "caveman"), ("Ponytail", "ponytail"),
        ("Paws lite", "lite"), ("Paws full", "full"), ("Paws ultra", "ultra")]
PAWS = ("lite", "full", "ultra")
# benchmark arm names per row: (answer tasks, code tasks); Paws uses its language skills on code
ARMS = [("caveman", "caveman"), ("ponytail", "ponytail"), ("paws-lite", "paws-lite+skills"),
        ("paws", "paws+skills"), ("paws-ultra", "paws-ultra+skills")]
MODELS = [("opus55", "Claude Opus 5.5", "2026-10-03-opus55-reference.json"),
          ("sonnet55", "Claude Sonnet 5.5", "2026-10-02-sonnet55-reference.json"),
          ("haiku45", "Claude Haiku 4.5", "2026-10-02-haiku45-reference.json")]


def fmt(v):
    """One decimal, dropped when .0; a real minus sign for 'used more than baseline'."""
    s = f"{v:.1f}".removesuffix(".0")
    return ("0" if s in ("-0", "0") else s.replace("-", "−")) + "%"


class Ref:
    def __init__(self, path):
        d = json.loads(path.read_text(encoding="utf-8"))
        self.code, self.text = d["code_rows"], d["text_rows"]

    @staticmethod
    def mean(rows, arm, key):
        vals = [x[key] for x in rows if x["arm"] == arm]
        return sum(vals) / len(vals)

    def saved(self, rows, key):
        base = self.mean(rows, "baseline", key)
        arm_i = 0 if rows is self.text else 1
        return [round(100 * (base - self.mean(rows, a[arm_i], key)) / base, 1) for a in ARMS]

    def correct(self, rows, arm):
        c = [x for x in rows if x["arm"] == arm]
        return sum(x["correct"] for x in c), len(c)


def metrics(ref):
    """(chart title, table label, savings), answers first, then code."""
    return [("Answer words", "Answers, 10 non-code tasks (words)", ref.saved(ref.text, "words")),
            ("Answer cost", "Answers cost", ref.saved(ref.text, "cost")),
            ("Answer time", "Answers time", ref.saved(ref.text, "duration_ms")),
            ("Code lines", "Code, 12 C#/TypeScript tasks (lines)", ref.saved(ref.code, "total_loc")),
            ("Code cost", "Code cost", ref.saved(ref.code, "cost")),
            ("Code time", "Code time", ref.saved(ref.code, "duration_ms"))]


def chart_data(ref):
    """Two columns, filled row by row: answers on the left, code on the right."""
    m = metrics(ref)
    answers, code = m[:3], m[3:]
    return {title: vals for pair in zip(answers, code) for title, _, vals in pair}


def table(ref):
    rows = [(label, vals) for _, label, vals in metrics(ref)]
    out = ["| | Caveman | Ponytail | Paws lite | Paws full | Paws ultra |", "|---|---:|---:|---:|---:|---:|"]
    for name, vals in rows:
        best = max(vals)
        out.append(f"| {name} | " + " | ".join(f"**{fmt(v)}**" if v == best else fmt(v) for v in vals) + " |")
    ok = [tuple(map(sum, zip(ref.correct(ref.text, ta), ref.correct(ref.code, ca)))) for ta, ca in ARMS]
    out.append("| Correct | " + " | ".join(f"{a}/{n}" for a, n in ok) + " |")
    return "\n".join(out)


def bar_path(x0, x1, y, h, r=4):
    """Bar anchored square at the zero line (x0), rounded at the data end (x1)."""
    if abs(x1 - x0) < 0.5:
        return ""
    r = min(r, abs(x1 - x0), h / 2)
    if x1 > x0:
        return f"M{x0},{y}H{x1 - r}Q{x1},{y} {x1},{y + r}V{y + h - r}Q{x1},{y + h} {x1 - r},{y + h}H{x0}Z"
    return f"M{x0},{y}H{x1 + r}Q{x1},{y} {x1},{y + r}V{y + h - r}Q{x1},{y + h} {x1 + r},{y + h}H{x0}Z"


def panel(title, values, ox, oy, t, lo, hi, pw):
    label_w, row_h, bar_h = 104, 26, 16
    plot_x, plot_w = ox + label_w, pw - label_w - 64
    sx = lambda v: plot_x + (v - lo) / (hi - lo) * plot_w
    zero = sx(0)
    out = [f'<text class="t b" x="{ox}" y="{oy + FS}" fill="{t["text"]}">{escape(title)}</text>']
    top = oy + 28
    out.append(f'<line x1="{zero}" y1="{top - 4}" x2="{zero}" y2="{top + len(ROWS) * row_h}" stroke="{t["axis"]}" stroke-width="1"/>')
    for i, ((name, key), v) in enumerate(zip(ROWS, values)):
        y, base = top + i * row_h, top + i * row_h + 13
        paws = key in PAWS
        out.append(f'<text class="t{" b" if paws else ""}" x="{plot_x - 10}" y="{base}" text-anchor="end" '
                   f'fill="{t["text"] if paws else t["muted"]}">{name}</text>')
        d = bar_path(zero, sx(v), y, bar_h)
        if d:
            out.append(f'<path d="{d}" fill="{t[key]}"><title>{name}: {fmt(v)} saved vs baseline</title></path>')
        lx, anchor = (sx(v) + 6, "start") if v >= 0 else (sx(v) - 6, "end")
        out.append(f'<text class="n" x="{lx}" y="{base}" text-anchor="{anchor}" fill="{t["text"]}">{fmt(v)}</text>')
    return "\n".join(out)


def chart(title, data, theme):
    t = THEMES[theme]
    vals = [v for vs in data.values() for v in vs]
    hi = max(vals) + 2
    lo = min(vals) - 0.25 * (hi - min(vals)) if min(vals) < 0 else 0   # room for a "−5.3%" label left of the bar
    cols, pw, ph, gap, pad = 2, 440, 176, 32, 24
    rows = (len(data) + cols - 1) // cols
    W, H = pad * 2 + cols * pw + (cols - 1) * gap, 80 + rows * ph
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
             f'role="img" aria-label="{escape(title)}">', STYLE,
             f'<rect width="{W}" height="{H}" rx="8" fill="{t["surface"]}"/>',
             f'<text class="t b" x="{pad}" y="32" fill="{t["text"]}">{escape(title)}</text>']
    lx = pad                                                      # legend: one row, under the title
    for name, key in (("Paws lite", "lite"), ("Paws full", "full"), ("Paws ultra", "ultra"),
                      ("Caveman", "caveman"), ("Ponytail", "ponytail")):
        parts.append(f'<rect x="{lx}" y="46" width="14" height="14" rx="3" fill="{t[key]}"/>'
                     f'<text class="t" x="{lx + 20}" y="58" fill="{t["muted"]}">{name}</text>')
        lx += 20 + round(7.6 * len(name)) + 22
    parts.append(f'<text class="t" x="{W - pad}" y="58" text-anchor="end" fill="{t["muted"]}">'
                 f'% saved vs baseline, higher is better</text>')
    for i, (ptitle, values) in enumerate(data.items()):
        ox, oy = pad + (i % cols) * (pw + gap), 80 + (i // cols) * ph
        parts.append(panel(ptitle, values, ox, oy, t, lo, hi, pw))
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for slug, title, fname in MODELS:
        ref = Ref(RESULTS / fname)
        for theme in THEMES:
            p = OUT / f"{slug}-{theme}.svg"
            p.write_text(chart(f"{title}: savings vs baseline", chart_data(ref), theme), encoding="utf-8")
            print("wrote", p.relative_to(ROOT))
        if "--tables" in sys.argv:
            print(f"\n{title}\n\n{table(ref)}\n")


if __name__ == "__main__":
    main()
