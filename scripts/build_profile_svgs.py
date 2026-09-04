#!/usr/bin/env python3
"""Regenerate profile figures and refresh DATA blocks in both READMEs.

Caliber rule (structural, do not weaken): every number a visitor could check is
collected at the anonymous / public caliber — the contributions page as a
logged-out visitor sees it, `is:public` search, public REST endpoints. The
GITHUB_TOKEN is used only for API quota, never to widen the caliber, so the
monthly bot run and a human's browser see the same numbers.

Private-limited figures (public/private splits, private review counts) are
hand-written in the READMEs with as-of dates and are never touched here.

Stdlib only. On any inconsistency: exit 1 WITHOUT writing anything —
stale-but-true beats fresh-but-wrong.
"""

import json
import math
import re
import ssl
import statistics
import subprocess
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone

try:  # prefer certifi when present (GitHub runners ship it); else system store
    import certifi

    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = ssl.create_default_context()

USER = "ThreeFish-AI"
TZ = timezone(timedelta(hours=8))
README_FILES = ["README.md", "docs/i18n/zh-CN/README.md"]
ACC_REPO = "analysis_claude_code"
RELEASE_REPOS = ["coding-proxy", "give-me-a-break", "hyper-git", "negentropy"]
MIN_SOURCE_COMMITS = 10  # "source repository" = non-fork repo with >= N commits authored by USER
FIRST_YEAR = 2016
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

CONVENTIONAL = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([^)]*\))?!?:\s*\S"
)


def die(msg):
    print(f"ABORT: {msg}", file=sys.stderr)
    sys.exit(1)


def gh(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if r.returncode != 0:
        die(f"gh api {path[:70]} -> {r.stderr.strip()[:160]}")
    return json.loads(r.stdout)


def gh_paginate(path):
    r = subprocess.run(
        ["gh", "api", "--paginate", "--slurp", path], capture_output=True, text=True
    )
    if r.returncode != 0:
        die(f"gh api --paginate {path[:70]} -> {r.stderr.strip()[:160]}")
    out = []
    for page in json.loads(r.stdout):
        out.extend(page)
    return out


def anon_contribution_counts(url, expect_year=None):
    """Parse the anonymous profile contributions page (visitor caliber).

    GitHub retired data-count attributes; exact per-day counts now live in
    <tool-tip> elements ("17 contributions on January 4th.") and the page h2
    carries the year total. We parse both and cross-check them.
    """
    req = urllib.request.Request(
        url, headers={"User-Agent": "threefish-profile-refresh"}
    )
    with urllib.request.urlopen(req, timeout=60, context=SSL_CTX) as r:
        html = r.read().decode("utf-8", "replace")
    days = [
        int(x.replace(",", ""))
        for x in re.findall(r">([\d,]+) contributions? on ", html)
    ]
    m = re.search(r"<h2[^>]*>([\d,]+) contributions in (\d{4})", html)
    if m and expect_year and int(m.group(2)) == expect_year:
        h2_total = int(m.group(1).replace(",", ""))
        if sum(days) != h2_total:
            die(
                f"{url[:70]}: tooltip sum {sum(days)} != h2 total {h2_total} — "
                "page structure changed, refusing"
            )
    return days


# ---------------------------------------------------------------- data ----
print("collecting: yearly contributions (anonymous view) …")
now = datetime.now(TZ)
years, values = [], []
for y in range(FIRST_YEAR, now.year + 1):
    counts = anon_contribution_counts(
        f"https://github.com/users/{USER}/contributions?from={y}-01-01&to={y}-12-31",
        expect_year=y,
    )
    years.append(y)
    values.append(sum(counts))
    print(f"  {y}: {values[-1]:,}")
rolling = anon_contribution_counts(f"https://github.com/users/{USER}/contributions")
active_days = len(rolling)

if sum(values) <= 0:
    die("yearly contribution totals are all zero — page parse broken")
if active_days <= 0:
    die("rolling active days is zero — page parse broken")

print("collecting: repositories …")
repos = [r for r in gh_paginate(f"users/{USER}/repos?per_page=100") if not r["fork"]]
total_stars = sum(r["stargazers_count"] for r in repos)
acc_stars = next((r["stargazers_count"] for r in repos if r["name"] == ACC_REPO), None)
if acc_stars is None:
    die(f"{ACC_REPO} missing from repo list — star split is undefined")
own_stars = total_stars - acc_stars

print("collecting: authored commits per repository (first page probe) …")
repo_commits = {}
for r in repos:
    name = r["name"]
    page1 = gh(f"repos/{USER}/{name}/commits?author={USER}&per_page=100")
    if len(page1) < MIN_SOURCE_COMMITS:
        continue  # below "source repository" threshold
    commits = page1 if len(page1) < 100 else gh_paginate(
        f"repos/{USER}/{name}/commits?author={USER}&per_page=100"
    )
    repo_commits[name] = commits
    print(f"  {name}: {len(commits)} authored commits")

src_repos = len(repo_commits)
all_commits = [c for lst in repo_commits.values() for c in lst]
commits_total = len(all_commits)
if commits_total < 100:
    die(f"only {commits_total} authored commits collected — parse likely broken")

hours = Counter()
days = set()
weekend = 0
conv = 0
scoped = 0
types = Counter()
for c in all_commits:
    a = c["commit"]["author"]
    dt = datetime.strptime(a["date"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(TZ)
    hours[dt.hour] += 1
    days.add(dt.date())
    if dt.weekday() >= 5:
        weekend += 1
    msg = c["commit"]["message"].split("\n")[0]
    m = CONVENTIONAL.match(msg)
    if m:
        conv += 1
        if m.group(2):
            scoped += 1
        types[m.group(1)] += 1

flat = commits_total / 24
peak_h = max(hours, key=lambda h: hours[h])
peak_n = hours[peak_h]
peak_x = peak_n / flat
weekend_pct = weekend / commits_total * 100

sorted_days = sorted(days)
streak = best = 1
for prev, cur in zip(sorted_days, sorted_days[1:]):
    streak = streak + 1 if (cur - prev).days == 1 else 1
    best = max(best, streak)
streak = best

zero_hours = [h for h in range(24) if hours[h] == 0]


def zero_ranges(hs):
    out = []
    for h in hs:
        if out and h == out[-1][1] + 1:
            out[-1][1] = h
        else:
            out.append([h, h])
    return out


print("collecting: negentropy pull requests …")
pulls = gh_paginate(f"repos/{USER}/negentropy/pulls?state=closed&per_page=100")
merged = [p for p in pulls if p["merged_at"]]
neg_pr = len(merged)
lifetimes = []
for p in merged:
    created = datetime.strptime(p["created_at"], "%Y-%m-%dT%H:%M:%SZ")
    merged_at = datetime.strptime(p["merged_at"], "%Y-%m-%dT%H:%M:%SZ")
    lifetimes.append((merged_at - created).total_seconds() / 60)
neg_median = statistics.median(lifetimes)
pct_hour = sum(1 for m in lifetimes if m <= 60) / len(lifetimes) * 100
neg_commits = len(repo_commits.get("negentropy", []))

print("collecting: releases …")
rel_counts = {r: len(gh(f"repos/{USER}/{r}/releases?per_page=100")) for r in RELEASE_REPOS}
rel_total = sum(rel_counts.values())
rel_repos = sum(1 for v in rel_counts.values() if v)

print("collecting: public PR totals (is:public caliber) …")
pub_prs = gh(
    "search/issues?q=is:pr+author:ThreeFish-AI+is:public&per_page=1"
)["total_count"]
ext_prs = gh(
    "search/issues?q=is:pr+author:ThreeFish-AI+is:public+-user:ThreeFish-AI&per_page=1"
)["total_count"]

# ------------------------------------------------------------- guards ----
if ext_prs > 10:
    die(f"external public PR count = {ext_prs} — search caliber drifted, refusing")
if own_stars != total_stars - acc_stars:
    die("star split arithmetic broken")
if len(years) != len(values) or any(v < 0 for v in values):
    die("year series malformed")

# ----------------------------------------------------------- SVG: arc ----
def render_arc(values, years, asof):
    n = len(values)
    x0, x1, y_base, y_top = 56.0, 716.0, 118.0, 30.0
    pitch = (x1 - x0) / (n - 1)
    vmax = max(values) or 1
    pts = [
        (x0 + i * pitch, y_base - (y_base - y_top) * math.sqrt(v) / math.sqrt(vmax))
        for i, v in enumerate(values)
    ]
    pts_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = pts_str + f" {x1:.1f},{y_base} {x0:.1f},{y_base}"
    dots = "\n".join(
        f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="{4 if i == n - 1 else 2.6}"/>'
        for i, (x, y) in enumerate(pts)
    )
    labels = []
    label_years = {2020: 129, 2022: 676, 2023: 589, 2024: 1181, 2025: 3193}
    for i, (x, y) in enumerate(pts):
        y_ = years[i]
        v = values[i]
        if y_ == years[-1]:
            labels.append(
                f'  <text x="{x - 4:.0f}" y="{y - 8:.0f}" font-size="14" font-weight="600" class="hi">{v:,}</text>'
            )
        elif y_ in label_years:
            mark = " ↓" if y_ == 2023 and i > 0 and values[i] < values[i - 1] else ""
            labels.append(
                f'  <text x="{x:.0f}" y="{y - 10:.0f}" font-size="13" class="lbl">{v:,}{mark}</text>'
            )
    ticks = "\n".join(
        f'  <text x="{x:.0f}" y="137" font-size="11" class="lbl">{y}</text>'
        for (x, _), y in zip(pts, years)
        if (y - FIRST_YEAR) % 2 == 0
    )
    vals_txt = ", ".join(f"{v:,}" for v in values)
    dip = ""
    if n >= 8 and values[-4] < values[-5]:
        dip = f" {years[-4]} is lower than {years[-5]}."
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="760" height="150" viewBox="0 0 760 150" role="img"
     aria-label="Contributions per year {years[0]} to {years[-1]}: {vals_txt}. Equal spacing, square-root scale.{dip}">
<style>
  .rule{{stroke:#d1d9e0}}.lbl{{fill:#59636e}}.ln{{stroke:#0969da;fill:none}}.dot{{fill:#0969da}}.hi{{fill:#0969da}}.area{{fill:#0969da;opacity:.08}}
  @media (prefers-color-scheme:dark){{
    .rule{{stroke:#30363d}}.lbl{{fill:#8b949e}}.ln{{stroke:#58a6ff}}.dot{{fill:#58a6ff}}.hi{{fill:#58a6ff}}.area{{fill:#58a6ff;opacity:.10}}
  }}
</style>
<line class="rule" x1="36" y1="118" x2="736" y2="118" stroke-width="1"/>
<polygon class="area" points="{area}"/>
<polyline class="ln" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" points="{pts_str}"/>
<g class="dot">
{dots}
</g>
<g font-family="{FONT}" text-anchor="middle">
{chr(10).join(labels)}
{ticks}
</g>
<text x="736" y="148" text-anchor="end" font-family="{FONT}" font-size="9" class="lbl">as of {asof}</text>
</svg>
'''


# ---------------------------------------------------------- SVG: clock ----
def render_clock(hours, commits_total, src_repos, peak_h, peak_n, zero_hours, asof):
    x0, pitch, bw = 60.0, 27.5, 19.0
    y_base, h_max = 112.0, 76.0
    cmax = max(hours.values()) or 1

    def cls(h):
        if h == peak_h:
            return "peak"
        if hours[h] == 0:
            return "zero"
        if 19 <= h or h <= 3:
            return "night"
        return "day"

    bars = []
    for h in range(24):
        hgt = max(hours[h] / cmax * h_max, 1.5 if hours[h] == 0 else 0)
        y = y_base - hgt
        bars.append(
            f'<rect class="{cls(h)}" x="{x0 + h * pitch - bw / 2 + 1.5:.1f}" y="{y:.1f}" width="{bw}" height="{hgt:.1f}" rx="2"/>'
        )
    zero_txt = ""
    if zero_hours:
        spans = " and ".join(
            f"{a:02d}:00–{b:02d}:59" for a, b in zero_ranges(zero_hours)
        )
        # Centre the annotation over the zero band and lift it above the bars,
        # so it never collides with the hour ticks on the baseline row.
        zx = x0 + (zero_hours[0] + zero_hours[-1]) / 2 * pitch
        zero_txt = (
            f'  <text x="{zx:.0f}" y="96" font-size="10" class="lbl">{spans}</text>\n'
            f'  <text x="{zx:.0f}" y="107" font-size="10" class="lbl">zero commits</text>'
        )
    ticks = "\n".join(
        f'  <text x="{x0 + h * pitch:.0f}" y="130" font-size="9" class="lbl">{h:02d}</text>'
        for h in (0, 6, 12, 18, 23)
    )
    pct = peak_n / commits_total * 100
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="760" height="150" viewBox="0 0 760 150" role="img"
     aria-label="Commits by hour of day, Asia/Shanghai. {commits_total:,} open-source commits across {src_repos} source repositories. Peak {peak_h:02d}:00 with {peak_n} commits, {pct:.1f} percent. {len(zero_hours)} hours have zero commits.">
<style>
  .peak{{fill:#0969da}}.night{{fill:#0969da;opacity:.55}}.day{{fill:#59636e;opacity:.38}}.zero{{fill:#59636e;opacity:.22}}.lbl{{fill:#59636e}}.base{{stroke:#d1d9e0}}
  @media (prefers-color-scheme:dark){{
    .peak{{fill:#58a6ff}}.night{{fill:#58a6ff;opacity:.55}}.day{{fill:#8b949e;opacity:.38}}.zero{{fill:#8b949e;opacity:.22}}.lbl{{fill:#8b949e}}.base{{stroke:#30363d}}
  }}
</style>
<line class="base" x1="40" y1="112" x2="730" y2="112" stroke-width="1"/>
{chr(10).join(bars)}
<g font-family="{FONT}" text-anchor="middle">
  <text x="{x0 + peak_h * pitch:.0f}" y="28" font-size="13" font-weight="600" class="lbl">{peak_n}</text>
{zero_txt}
  <text x="730" y="20" text-anchor="end" font-size="10" class="lbl">{commits_total:,} commits · Asia/Shanghai</text>
{ticks}
</g>
<text x="736" y="148" text-anchor="end" font-family="{FONT}" font-size="9" class="lbl">as of {asof}</text>
</svg>
'''


# -------------------------------------------------------------- write ----
asof = now.strftime("%Y-%m-%d")
current_year = years[-1]
c2026_value = values[-1]

DATA = {
    "c2026": f'[{c2026_value:,} contributions in {current_year}](https://github.com/ThreeFish-AI?tab=overview&from={current_year}-01-01&to={current_year}-12-31)',
    "pub_prs": f'[{pub_prs:,} public pull requests](https://github.com/search?q=is%3Apr+author%3AThreeFish-AI+is%3Apublic&type=pullrequests)',
    "rel_total": f'[{rel_total} releases](https://github.com/ThreeFish-AI?tab=repositories&type=source)',
    "rel_repos": rel_repos,
    "rel_cp": rel_counts["coding-proxy"],
    "rel_gmab": rel_counts["give-me-a-break"],
    "rel_hg": rel_counts["hyper-git"],
    "rel_neg": rel_counts["negentropy"],
    "neg_pr": f'[{neg_pr:,} merged pull requests](https://github.com/ThreeFish-AI/negentropy/pulls?q=is%3Apr+is%3Amerged)',
    "neg_commits": f"{neg_commits:,}",
    "own_stars": own_stars,
    "acc_stars": acc_stars,
    "src_repos": src_repos,
    "commits_total": f"{commits_total:,}",
    "neg_median": f"{neg_median:.0f}",
    "pct_hour": f"{pct_hour:.0f}%",
    "conv_pct": f"{conv / commits_total * 100:.1f}%",
    "scoped_pct": f"{scoped / conv * 100:.1f}%" if conv else "0%",
    "mix_fix": f"{types['fix'] / conv * 100:.1f}%" if conv else "0%",
    "mix_docs": f"{types['docs'] / conv * 100:.1f}%" if conv else "0%",
    "mix_feat": f"{types['feat'] / conv * 100:.1f}%" if conv else "0%",
    "streak": streak,
    "active_days": active_days,
    "peak_h": f"{peak_h:02d}:00",
    "peak_n": peak_n,
    "peak_x": f"{peak_x:.2f}×",
    "weekend_pct": f"{weekend_pct:.1f}%",
    "asof": f"last refreshed {asof}",
}

outputs = {}
for f in README_FILES:
    with open(f, encoding="utf-8") as fh:
        text = fh.read()
    m = re.search(r"<!-- DATA:c2026 -->(.*?)<!-- /DATA:c2026 -->", text, re.S)
    if m:
        nums = re.findall(r"\d[\d,]*", m.group(1))
        if nums and int(nums[0].replace(",", "")) > c2026_value:
            die(
                f"current-year total decreased ({nums[0]} -> {c2026_value}) — "
                "parse likely broken"
            )
    for key, val in DATA.items():
        pat = re.compile(
            r"(<!-- DATA:" + key + r" -->).*?(<!-- /DATA:" + key + r" -->)", re.S
        )
        if not pat.search(text):
            die(f"{f}: DATA block '{key}' not found")
        text = pat.sub(lambda mm: f"{mm.group(1)}{val}{mm.group(2)}", text)
    if re.search(r"<!-- DATA:[a-z0-9_]+ -->\s*$", text, re.M):
        die(f"{f}: unfilled DATA placeholder remains")
    outputs[f] = text

arc_svg = render_arc(values, years, asof)
clock_svg = render_clock(hours, commits_total, src_repos, peak_h, peak_n, zero_hours, asof)

# All guards passed — write everything.
with open("assets/contribution-arc.svg", "w", encoding="utf-8") as fh:
    fh.write(arc_svg)
with open("assets/commit-clock.svg", "w", encoding="utf-8") as fh:
    fh.write(clock_svg)
for f, text in outputs.items():
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(text)

print(
    f"OK  arc({len(values)}y, latest {c2026_value:,})  clock({commits_total:,} commits/{src_repos} repos, peak {peak_h:02d}:00×{peak_n})  "
    f"pub_prs={pub_prs:,}  ext={ext_prs}  own_stars={own_stars}  streak={streak}d  median={neg_median:.0f}min"
)
