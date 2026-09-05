#!/usr/bin/env python3
"""Profile figure generator + fact refresher for both READMEs.

Caliber rule (structural, do not weaken): every number a visitor could check is
collected at the anonymous / public caliber — the contributions page as a
logged-out visitor sees it, `is:public` search, public REST endpoints. The
GITHUB_TOKEN is used only for API quota, never to widen the caliber. Draft
releases are excluded: they are invisible to an anonymous visitor but visible
to a push-capable token, so counting them would make a local run and a CI run
disagree.

Private-limited figures (public/private splits) are hand-written in the READMEs
with as-of dates and are never touched here.

Motion rule (see docs/motion-constraints.md): animations are one-shot entrances
only. Default state == final state (`animation … both` with explicit 0%/100%
opacity:0 keyframes; base rules carry opacity:0), wrapped in
`@media (prefers-reduced-motion:no-preference)` — static is the default, motion
is the progressive enhancement. No loops, ever.

Substitution rule: the READMEs are the pipeline's only state store, so every
marker must SURVIVE its own substitution. Regions are delimited comment pairs
(`<!-- DATA:k -->…<!-- /DATA:k -->`, `<!-- FIG:k -->…<!-- /FIG:k -->`) whose
delimiters are rewritten back verbatim, and `substitute()` is asserted to be a
fixed point. A bare consumable token is what silently killed the v4 refresh.

Marker direction: markers found in the READMEs must be derivable (FACT_KEYS /
FIG_SPEC), and the two files must carry the identical marker set in the
identical order. Deliberately NOT the reverse — a derivable fact nobody
references is fine, so deleting a content block from both READMEs needs no
change here.

Stdlib only. On any inconsistency: exit 1 WITHOUT writing anything —
stale-but-true beats fresh-but-wrong.

Usage:
  build_profile_svgs.py           collect, validate, write
  build_profile_svgs.py --check   collect, validate, diff against disk, write nothing
  build_profile_svgs.py --lint    marker/parity audit only, zero network calls
"""

import difflib
import json
import html
import math
import pathlib
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
EN, ZH = "README.md", "docs/i18n/zh-CN/README.md"
README_FILES = [EN, ZH]
ACC_REPO = "analysis_claude_code"
MIN_SOURCE_COMMITS = 10  # "source repository" = non-fork repo with >= N commits authored by USER
FIRST_YEAR = 2016
RHYTHM_ORIGIN = 4  # hour axis starts at 04:00 so the night block stays contiguous
DIFY_OWNER = "langgenius"  # the one upstream ecosystem the READMEs name by hand
CONVENTIONAL = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([^)]*\))?(!)?:\s*\S"
)

# Every fact the READMEs may reference. Lint audits markers against this with
# zero network calls; the collector must produce exactly this set (see the
# FACT_KEYS closure guard) so contract and derivation can never drift.
# Declaring a fact nobody references is deliberately fine — that is what makes
# deleting a content block from both READMEs a markdown-only edit.
FACT_KEYS = frozenset({
    "asof", "cur_year", "cur_total",
    "commits_total", "src_repos", "streak", "conv_pct",
    "peak_h", "peak_x", "peak_n", "peak_pct",
    "pub_prs", "neg_pr", "neg_median", "pct_hour",
    "own_stars", "acc_stars", "total_stars",
    "rel_total", "rel_repos",
    "ext_prs", "ext_merged", "ext_dify", "ext_first", "ext_last",
    "archived_n", "archived_names",
    # v5 figures
    "pc_cell", "pc_val", "pc_empty", "wknd_pct",
    "win_from", "win_to", "win_days", "win_months",
    "p90", "lat_max", "pr_closed", "pr_unmerged",
    "top_type", "top_type_pct", "nonconf_pct", "nonconf_n",
    "lang_top", "lang_top_pct", "lang_naive", "lang_naive_pct",
    "rel_last_name", "rel_last_tag",
    "streak_from", "streak_to", "active_days", "active_pct",
    "wd_days", "we_days", "we_peak_h",
    # v5 content modules (per-project sub-lines)
    "neg_commits", "rel_cp", "rel_hg", "rel_gmab",
})

# Figure key -> (filename, rendered width). Also the assets-closure contract:
# an SVG in assets/ that this script did not render aborts the run, so the
# workflow can safely `git add -A assets`.
FIG_SPEC = {
    "mark": ("mark.svg", 256),
    "growth": ("growth.svg", 700),
    "rhythm": ("rhythm.svg", 700),
    "ground": ("ground.svg", 700),
    "punchcard": ("punchcard.svg", 700),
    "surplus": ("surplus.svg", 700),
    "accrual": ("accrual.svg", 700),
    "lifecycles": ("lifecycles.svg", 700),
    "cadence": ("cadence.svg", 700),
    "streak": ("streak.svg", 700),
    "latency": ("latency.svg", 700),
    "grammar": ("grammar.svg", 700),
    "tongues": ("tongues.svg", 700),
    "upstream": ("upstream.svg", 700),
}

# The zh README is read outside its own repo (it renders on the profile via the
# EN file's siblings), so it must reference figures absolutely.
SRC_PREFIX = {
    EN: "assets/",
    ZH: f"https://raw.githubusercontent.com/{USER}/threefish-ai/master/assets/",
}

MARKER = re.compile(r"<!-- (/?)(DATA|FIG):([a-z0-9_]+) -->")


def die(msg):
    print(f"ABORT: {msg}", file=sys.stderr)
    sys.exit(1)


MODE = "write"
for _arg in sys.argv[1:]:
    if _arg in ("--lint", "--check"):
        MODE = _arg[2:]
    else:
        die(f"unknown argument {_arg!r} — expected --lint or --check")


# -------------------------------------------------------------- markers ----
def scan_markers(text, f):
    """Ordered [(kind, key)] of the regions in one file, with well-formedness
    guards. Runs on the text as it came off disk, BEFORE any substitution, so a
    generated region can never satisfy the audit on markers it introduced."""
    order, opened = [], None
    for slash, kind, key in MARKER.findall(text):
        known = FACT_KEYS if kind == "DATA" else set(FIG_SPEC)
        if key not in known:
            die(f"{f}: <!-- {kind}:{key} --> is not derivable — "
                "value would rot unrefreshed, refusing")
        if slash:
            if opened != (kind, key):
                die(f"{f}: <!-- /{kind}:{key} --> does not close {opened} — "
                    "malformed region, refusing")
            opened = None
        else:
            if opened is not None:
                die(f"{f}: <!-- {kind}:{key} --> opened inside {opened} — "
                    "nested region, refusing")
            opened = (kind, key)
            order.append((kind, key))
    if opened is not None:
        die(f"{f}: unclosed region {opened} — malformed region, refusing")
    return order


def audit_parity(orders):
    """The two READMEs must carry the identical marker sequence. Asserts a
    NON-ZERO count first: two empty streams compare equal, which is exactly how
    the consumed-alt-token bug stayed invisible to a naive diff."""
    a, b = orders[EN], orders[ZH]
    if not a:
        die(f"{EN}: no refreshable regions found — the contract is empty, refusing")
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            die(f"region {i} differs: {EN} has {x[0]}:{x[1]}, {ZH} has {y[0]}:{y[1]}"
                " — bilingual drift, refusing")
    if len(a) != len(b):
        long_f, extra = (EN, a[len(b):]) if len(a) > len(b) else (ZH, b[len(a):])
        die(f"{long_f} has {len(extra)} extra region(s) "
            f"{[f'{k}:{v}' for k, v in extra]} — bilingual drift, refusing")


def audit_assets():
    """Keeps the script the single source of truth for assets/, so the workflow
    can safely `git add -A assets`."""
    rendered = {fname for fname, _ in FIG_SPEC.values()}
    stray = sorted(p.name for p in pathlib.Path("assets").glob("*.svg")
                   if p.name not in rendered)
    if stray:
        die(f"assets/ contains ungenerated SVG(s) {stray} — "
            "'git add -A assets' would commit them, refusing")


def read_readmes():
    texts = {}
    for f in README_FILES:
        p = pathlib.Path(f)
        if not p.is_file():
            die(f"{f} not found — run this script from the repository root")
        texts[f] = p.read_text(encoding="utf-8")
    return texts


def substitute(text, f, facts, alts):
    """Rewrite every region body while rewriting its delimiters back verbatim.

    Idempotent by construction: each pass rebuilds the body from `facts`/`alts`,
    never from the previous output, so escaping cannot compound. The `\\2`
    backreference forces the closing marker to name the same key as the open.
    """
    text = re.sub(
        r"(<!-- DATA:([a-z0-9_]+) -->).*?(<!-- /DATA:\2 -->)",
        lambda m: f"{m.group(1)}{facts[m.group(2)]}{m.group(3)}",
        text, flags=re.S)

    def fig(m):
        fname, width = FIG_SPEC[m.group(2)]
        alt = html.escape(alts[m.group(2)], quote=True)
        img = f'<img src="{SRC_PREFIX[f]}{fname}" width="{width}" alt="{alt}" />'
        return f"{m.group(1)}{img}{m.group(3)}"

    return re.sub(
        r"(<!-- FIG:([a-z0-9_]+) -->).*?(<!-- /FIG:\2 -->)",
        fig, text, flags=re.S)


if MODE == "lint":
    _orders = {f: scan_markers(t, f) for f, t in read_readmes().items()}
    audit_parity(_orders)
    audit_assets()
    _d = sum(1 for k, _ in _orders[EN] if k == "DATA")
    _g = sum(1 for k, _ in _orders[EN] if k == "FIG")
    print(f"OK  lint: {_d} DATA + {_g} FIG regions, identical set and order in "
          f"both READMEs; assets/ clean")
    sys.exit(0)


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

if sum(values) <= 0:
    die("yearly contribution totals are all zero — page parse broken")

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
    if len(page1) < 100:
        commits = page1
    else:  # keep page1; only the pages after it are new requests
        commits = page1 + gh_paginate(
            f"repos/{USER}/{name}/commits?author={USER}&per_page=100&page=2"
        )
    repo_commits[name] = commits
    print(f"  {name}: {len(commits)} authored commits")

src_repos = len(repo_commits)
all_commits = [c for lst in repo_commits.values() for c in lst]
commits_total = len(all_commits)
if commits_total < 100:
    die(f"only {commits_total} authored commits collected — parse likely broken")

hours = Counter()
weekhours = Counter()   # (weekday 0=Mon, hour) -> n
day_counts = Counter()  # date -> n
lang_of_commit = []     # commit dates for the shared time-domain
types = Counter()       # Conventional Commits type -> n
conv = 0
for c in all_commits:
    a = c["commit"]["author"]
    dt = datetime.strptime(a["date"], "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    ).astimezone(TZ)
    hours[dt.hour] += 1
    weekhours[(dt.weekday(), dt.hour)] += 1
    day_counts[dt.date()] += 1
    lang_of_commit.append(dt.date())
    m = CONVENTIONAL.match(c["commit"]["message"].split("\n")[0])
    if m:
        conv += 1
        types[m.group(1)] += 1

sorted_days = sorted(day_counts)
streak = best = 1
run_start = run_end = sorted_days[0]
best_start = best_end = sorted_days[0]
for prev, cur in zip(sorted_days, sorted_days[1:]):
    if (cur - prev).days == 1:
        streak += 1
        run_end = cur
    else:
        streak = 1
        run_start = cur
    if streak > best:
        best, best_start, best_end = streak, run_start, run_end
streak = best

zero_hours = [h for h in range(24) if hours[h] == 0]

# The shared x-domain for every time-axis figure (accrual, lifecycles, cadence,
# streak): three stacked figures with three silently different ranges is a
# worse honesty failure than any single figure's caveat.
DOMAIN = (min(lang_of_commit), max(lang_of_commit))
WIN_DAYS = (DOMAIN[1] - DOMAIN[0]).days + 1

# Pipeline-closure guard: every authored commit must land in exactly one hour
# bucket. A mismatch means the hour histogram and the repository table below
# would silently disagree with each other.
if sum(hours.values()) != commits_total:
    die(
        f"hour histogram {sum(hours.values())} != repo total {commits_total} — "
        "caliber split, refusing"
    )
if sum(weekhours.values()) != commits_total or sum(day_counts.values()) != commits_total:
    die(f"weekday/day histogram {sum(weekhours.values())}/{sum(day_counts.values())} "
        f"!= repo total {commits_total} — caliber split, refusing")
if sum(types.values()) != conv:
    die(f"commit-type histogram {sum(types.values())} != conventional count {conv} "
        "— CONVENTIONAL regex drift, refusing")

print("collecting: negentropy pull requests …")
pulls = gh_paginate(f"repos/{USER}/negentropy/pulls?state=closed&per_page=100")
merged = [p for p in pulls if p["merged_at"]]
neg_pr = len(merged)
pr_closed = len(pulls)
pr_unmerged = pr_closed - neg_pr
lifetimes = []
for p in merged:
    created = datetime.strptime(p["created_at"], "%Y-%m-%dT%H:%M:%SZ")
    merged_at = datetime.strptime(p["merged_at"], "%Y-%m-%dT%H:%M:%SZ")
    lifetimes.append((merged_at - created).total_seconds() / 60)
lifetimes_sorted = sorted(lifetimes)
neg_median = statistics.median(lifetimes)
pct_hour = sum(1 for m in lifetimes if m <= 60) / len(lifetimes) * 100
p90_lat = lifetimes_sorted[min(len(lifetimes_sorted) - 1, int(round(0.9 * len(lifetimes_sorted))) - 1)]
lat_max_min = lifetimes_sorted[-1]


def human_duration(minutes):
    if minutes < 60:
        return f"{minutes:.0f} min"
    if minutes < 60 * 24:
        return f"{minutes / 60:.1f} h"
    return f"{minutes / 60 / 24:.1f} d"

print("collecting: releases (every source repo, drafts excluded) …")
# Roster derived from the source repos, never hand-listed: a hand-listed roster
# silently rendered a real release as 0 for months. Drafts are excluded because
# they are invisible anonymously but visible to a push-capable token, which
# would make a local run and a CI run disagree.
rel_lists = {}
for name in repo_commits:
    rel_lists[name] = [
        x for x in gh(f"repos/{USER}/{name}/releases?per_page=100") if not x["draft"]
    ]
rel_counts = {k: len(v) for k, v in rel_lists.items()}
rel_total = sum(rel_counts.values())
rel_repos = sum(1 for v in rel_counts.values() if v)

print("collecting: language bytes per source repo (public caliber) …")
# This is exactly the data behind the language bar a logged-out visitor sees on
# each repo page — the one endpoint whose naive answer (HTML, 69.7%) is an
# artifact of a generated static site. The slope figure exists to show both
# conditions instead of silently picking one.
repo_langs = {name: gh(f"repos/{USER}/{name}/languages") for name in repo_commits}
lang_all = Counter()
lang_src = Counter()  # excluding the generated-site repo
GEN_SITE = "threefish-ai.github.io"
for name, by in repo_langs.items():
    for lang, byts in by.items():
        lang_all[lang] += byts
        if name != GEN_SITE:
            lang_src[lang] += byts
zero_byte_repos = [n for n, by in repo_langs.items() if not by]

print("collecting: public PR totals (is:public caliber) …")
pub_prs = gh(
    "search/issues?q=is:pr+author:ThreeFish-AI+is:public&per_page=1"
)["total_count"]
# per_page=30 rather than 1: the same request already carries the items, so the
# upstream ledger below is derived rather than hand-written prose that rots.
ext = gh(
    "search/issues?q=is:pr+author:ThreeFish-AI+is:public+-user:ThreeFish-AI&per_page=30"
)
ext_prs = ext["total_count"]
ext_items = ext["items"]
ext_merged = sum(1 for it in ext_items if it["pull_request"]["merged_at"])
ext_owners = {it["repository_url"].split("/repos/")[1].split("/")[0] for it in ext_items}
ext_dify = sum(
    1 for it in ext_items
    if it["pull_request"]["merged_at"]
    and it["repository_url"].split("/repos/")[1].startswith(f"{DIFY_OWNER}/")
)

archived_names = sorted(
    r["name"] for r in repos if r["archived"] and r["name"] in repo_commits
)

# ------------------------------------------------------------- guards ----
if ext_prs > 10:
    die(f"external public PR count = {ext_prs} — search caliber drifted, refusing")
# The guard above doubles as the ledger's layout contract; keep them together.
if ext_prs != len(ext_items):
    die(f"external PR ledger truncated: total_count {ext_prs} != items "
        f"{len(ext_items)} — raise per_page, refusing")
if ext_merged > ext_prs or ext_dify > ext_merged:
    die(f"ledger arithmetic broken: {ext_dify} dify <= {ext_merged} merged <= "
        f"{ext_prs} total violated, refusing")
if own_stars != total_stars - acc_stars:
    die("star split arithmetic broken")
if len(years) != len(values) or any(v < 0 for v in values):
    die("year series malformed")
if set(rel_counts) != set(repo_commits):
    die(f"release roster {sorted(rel_counts)} != source roster "
        f"{sorted(repo_commits)} — a repo's releases would render as 0, refusing")

# ----------------------------------------------------------- rendering ----
# Design tokens (Primer palette, WCAG-verified: text >= 4.5:1, graphics >= 3:1
# on both GitHub canvases). No opacity layering — solid inks only.
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
LIGHT = dict(bg="#ffffff", ink="#1f2328", lbl="#6e7781", val="#57606a",
             bar="#8c959f", acc="#0969da", rule="#d1d9e0")
DARK = dict(bg="#0d1117", ink="#f0f6fc", lbl="#9198a1", val="#8b949e",
            bar="#6e7681", acc="#58a6ff", rule="#30363d")


def style_sheet(extra=""):
    """Base tokens + dark override (always AFTER base rules) + extras."""
    base = "  .bg{fill:%(bg)s}.ink{fill:%(ink)s}.lbl{fill:%(lbl)s}.val{fill:%(val)s}" \
           ".bar{fill:%(bar)s}.acc{fill:%(acc)s}.accv{fill:%(acc)s;font-weight:600}" \
           ".zero{fill:none;stroke:%(bar)s;stroke-width:1.2}.rule{stroke:%(rule)s}" % LIGHT
    dark = "    .bg{fill:%(bg)s}.ink{fill:%(ink)s}.lbl{fill:%(lbl)s}.val{fill:%(val)s}" \
           ".bar{fill:%(bar)s}.acc{fill:%(acc)s}.accv{fill:%(acc)s;font-weight:600}" \
           ".zero{stroke:%(bar)s}.rule{stroke:%(rule)s}" % DARK
    return ("<style>\n"
            "  text{font-family:%s;font-variant-numeric:tabular-nums}\n"
            "  .tm{text-anchor:middle}.te{text-anchor:end}.ts{text-anchor:start}\n"
            "%s\n"
            "  @media (prefers-color-scheme:dark){\n%s\n  }\n%s"
            "</style>") % (FONT, base, dark, extra)


def svg_open(w, h, aria):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
            'viewBox="0 0 %d %d" role="img" aria-label="%s">' % (w, h, w, h, aria))


def render_growth(values, years, asof, aria):
    """`aria` is passed in, not computed here: under <img> the SVG's internal
    aria-label is ignored and the README's alt attribute is the only
    screen-reader channel, so both languages' alt text is derived once (see
    figure_alt) and this function is merely one of its consumers."""
    W, H = 700, 168
    L, R, BASE = 42.0, 686.0, 126.0
    SPAN, MIN_BAR, ZSLOT = 88.0, 2.5, 4.0       # plot height / bar floor / zero-slot h
    # Anti-inversion invariant: zero slots live strictly BELOW the axis (zero
    # pixels of height above baseline) while every non-zero bar is >= MIN_BAR
    # above it — "nothing" can never render taller than "something".
    ZERO_Y = BASE + 2
    assert ZERO_Y > BASE
    n = len(values)
    pitch = (R - L) / n
    bw = round(pitch * 0.52, 1)
    vmax = max(values) or 1
    bars, labels = [], []
    for i, v in enumerate(values):
        cx = L + pitch * (i + 0.5)
        x = cx - bw / 2
        if v == 0:                               # true zero -> hollow slot BELOW axis
            bars.append('<rect class="zero" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
                        % (x, ZERO_Y, bw, ZSLOT))
            labels.append('<text x="%.1f" y="%.1f" font-size="11.5" class="val tm">0</text>'
                          % (cx, BASE - 8))
            continue
        h = max(math.sqrt(v) / math.sqrt(vmax) * SPAN, MIN_BAR)
        last = i == n - 1
        cls = "acc" if last else "bar"
        bars.append('<rect class="%s" x="%.1f" y="%.2f" width="%.1f" height="%.2f" rx="2"/>'
                    % (cls, x, BASE - h, bw, h))
        dip = " ↓" if (0 < i and v < values[i - 1]) else ""
        labels.append('<text x="%.1f" y="%.1f" font-size="%s" class="%s tm">%s%s</text>'
                      % (cx, BASE - h - (7 if last else 5.5),
                         "15" if last else "11.5", "accv" if last else "val",
                         format(v, ","), dip))
    ticks = "".join('<text x="%.1f" y="142" font-size="10.5" class="lbl tm">%d</text>'
                    % (L + pitch * (i + 0.5), y) for i, y in enumerate(years))
    sweep_x = R - L
    motion = ("\n  .sweep{fill:%s;opacity:0}\n"
              "  @media (prefers-color-scheme:dark){.sweep{fill:%s}}\n"
              "  @media (prefers-reduced-motion:no-preference){\n"
              "    .sweep{animation:swg 1.9s cubic-bezier(.22,1,.36,1) .15s 1 both}\n"
              "    @keyframes swg{0%%{opacity:0;transform:translateX(0)}\n"
              "      10%%{opacity:.7}80%%{opacity:.7;transform:translateX(%dpx)}\n"
              "      100%%{opacity:0;transform:translateX(%dpx)}}\n  }\n"
              ) % (LIGHT["acc"], DARK["acc"], sweep_x, sweep_x)
    s = "\n".join([
        svg_open(W, H, aria),
        style_sheet(motion),
        '<rect class="bg" width="%d" height="%d" rx="6"/>' % (W, H),
        '<line class="rule" x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke-width="1"/>' % (L, BASE, R, BASE),
        "\n".join(bars),
        '<text x="%.0f" y="22" font-size="11" class="lbl ts">contributions per year · square-root scale</text>' % L,
        "\n".join(labels),
        ticks,
        '<text x="%.0f" y="160" font-size="9.5" class="lbl te">as of %s</text>' % (R, asof),
        '<rect class="sweep" x="%.0f" y="30" width="2.5" height="%.0f" rx="1.25"/>' % (L, BASE - 30),
        "</svg>", ""])
    return s


def render_rhythm(hours, asof, aria):
    W, H = 700, 168
    L, R, BASE = 42.0, 686.0, 126.0
    SPAN, MIN_BAR, ZSLOT, ORIGIN = 80.0, 2.5, 4.0, RHYTHM_ORIGIN
    ZERO_Y = BASE + 2
    assert ZERO_Y > BASE                          # zero slots strictly below the axis
    order = [(ORIGIN + k) % 24 for k in range(24)]  # axis 04→03: night block contiguous
    pitch = (R - L) / 24
    bw = round(pitch * 0.6, 1)
    cmax = max(hours.values()) or 1
    peak_h = max(hours, key=lambda h: hours[h])
    peak_i = order.index(peak_h)
    bars = []
    for i, h in enumerate(order):
        v = hours[h]
        x = L + pitch * (i + 0.5) - bw / 2
        if v == 0:
            bars.append('<rect class="zero" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>' % (x, ZERO_Y, bw, ZSLOT))
        else:
            hgt = max(v / cmax * SPAN, MIN_BAR)
            cls = "acc" if h == peak_h else "bar"
            bars.append('<rect class="%s" x="%.1f" y="%.2f" width="%.1f" height="%.2f" rx="2"/>'
                        % (cls, x, BASE - hgt, bw, hgt))
    peak_cx = L + pitch * (peak_i + 0.5)
    peak_v = hours[peak_h]
    ticks = "".join('<text x="%.1f" y="142" font-size="10.5" class="lbl tm">%02d</text>'
                    % (L + pitch * (i + 0.5), h) for i, h in enumerate(order) if i % 4 == 0)
    sweep_dx = round(peak_cx - L, 1)
    motion = ("\n  .sweep{fill:%s;opacity:0}\n"
              "  @media (prefers-color-scheme:dark){.sweep{fill:%s}}\n"
              "  @media (prefers-reduced-motion:no-preference){\n"
              "    .sweep{animation:swr 2.1s cubic-bezier(.22,1,.36,1) .6s 1 both}\n"
              "    @keyframes swr{0%%{opacity:0;transform:translateX(0)}\n"
              "      12%%{opacity:.7}68%%{opacity:.7;transform:translateX(%spx)}\n"
              "      100%%{opacity:0;transform:translateX(%spx)}}\n  }\n"
              ) % (LIGHT["acc"], DARK["acc"], sweep_dx, sweep_dx)
    s = "\n".join([
        svg_open(W, H, aria),
        style_sheet(motion),
        '<rect class="bg" width="%d" height="%d" rx="6"/>' % (W, H),
        '<line class="rule" x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke-width="1"/>' % (L, BASE, R, BASE),
        "\n".join(bars),
        '<text x="%.0f" y="22" font-size="11" class="lbl ts">open-source commits by hour · Asia/Shanghai · axis %02d→%02d</text>' % (L, ORIGIN, (ORIGIN + 23) % 24),
        '<text x="%.1f" y="%.1f" font-size="13" class="accv tm">%d</text>' % (peak_cx, BASE - SPAN - 7, peak_v),
        ticks,
        '<text x="%.0f" y="160" font-size="9.5" class="lbl te">as of %s</text>' % (R, asof),
        '<rect class="sweep" x="%.0f" y="38" width="2.5" height="%.0f" rx="1.25"/>' % (L, BASE - 38),
        "</svg>", ""])
    return s


def render_ground(repo_commits, rel, asof, aria):
    W, H = 700, 224
    X_NAME, X_BAR, X_REL, MAXW = 150.0, 160.0, 660.0, 420.0
    rows = sorted(repo_commits.items(), key=lambda kv: -kv[1])
    total = sum(repo_commits.values())
    vmax = max(repo_commits.values()) or 1
    top_share = rows[0][1] / total * 100
    body, i = [], 0
    for name, v in rows:
        y = 36 + i * 24
        w = v / vmax * MAXW
        focus = i == 0
        body.append('<text x="%.0f" y="%.0f" font-size="11.5" class="lbl te">%s</text>' % (X_NAME, y + 9, name))
        body.append('<rect class="%s" x="%.0f" y="%.0f" width="%.1f" height="11" rx="2"/>' % ("acc" if focus else "bar", X_BAR, y, w))
        body.append('<text x="%.1f" y="%.0f" font-size="11.5" class="%s ts">%s</text>' % (X_BAR + w + 8, y + 9, "accv" if focus else "val", format(v, ",")))
        body.append('<text x="%.0f" y="%.0f" font-size="11.5" class="val te">%d</text>' % (X_REL, y + 9, rel.get(name, 0)))
        i += 1
    head = "\n".join([
        '<text x="%.0f" y="20" font-size="10.5" class="lbl te">repository</text>' % X_NAME,
        '<text x="%.0f" y="20" font-size="10.5" class="lbl ts">commits</text>' % X_BAR,
        '<text x="%.0f" y="20" font-size="10.5" class="lbl te">releases</text>' % X_REL,
        '<line class="rule" x1="42" y1="27" x2="686" y2="27" stroke-width="1"/>'])
    rel_total = sum(rel.values())
    footer = ('<text x="%.0f" y="212" font-size="11" class="lbl ts">%s commits · %d '
              'releases · %d source repositories · %s %.1f%%</text>'
              % (X_BAR, format(total, ","), rel_total, len(repo_commits), rows[0][0], top_share))
    s = "\n".join([
        svg_open(W, H, aria),
        style_sheet(),                              # static figure: no motion rules
        '<rect class="bg" width="%d" height="%d" rx="6"/>' % (W, H),
        head, "\n".join(body), footer,
        '<text x="%.0f" y="212" font-size="9.5" class="lbl te">as of %s</text>' % (686, asof),
        "</svg>", ""])
    return s


def render_mark(aria):
    """Three-fish signature mark. The only 'figure' with no data — it IS the name."""
    W, H = 256, 62
    pos = [(24, 34, ".3s"), (110, 26, ".85s"), (196, 35, "1.35s")]
    fish, rip = [], []
    for x0, cy, d in pos:
        fish.append('<path class="fi" d="M %g,%g C %g,%g %g,%g %g,%g C %g,%g %g,%g %g,%g Z"/>'
                    % (x0, cy, x0+11, cy-10.5, x0+33, cy-10.5, x0+44, cy,
                       x0+33, cy+10.5, x0+11, cy+10.5, x0, cy))
        fish.append('<path class="fi" d="M %g,%g L %g,%g L %g,%g L %g,%g Z"/>'
                    % (x0+3, cy, x0-12, cy-7.5, x0-8.5, cy, x0-12, cy+7.5))
        fish.append('<circle class="eye" cx="%.1f" cy="%.1f" r="1.6"/>' % (x0+35.5, cy-3))
        rip.append('<ellipse class="rip" style="--d:%s" cx="%g" cy="%g" rx="28" ry="12"/>' % (d, x0+22, cy))
    st = ("<style>\n"
          "  .fi{fill:none;stroke:%s;stroke-width:1.4;stroke-linecap:round;stroke-linejoin:round}\n"
          "  .eye{fill:%s}\n"
          "  @media (prefers-color-scheme:dark){.fi{stroke:%s}.eye{fill:%s}}\n"
          "  .rip{fill:none;stroke:%s;stroke-width:1.2;opacity:0;"
          "transform-box:fill-box;transform-origin:center}\n"
          "  @media (prefers-color-scheme:dark){.rip{stroke:%s}}\n"
          "  @media (prefers-reduced-motion:no-preference){\n"
          "    .rip{animation:rip 2s ease-out 1 both;animation-delay:var(--d)}\n"
          "    @keyframes rip{0%%{opacity:0;transform:scale(.45)}\n"
          "      45%%{opacity:.5}100%%{opacity:0;transform:scale(1.35)}}\n  }\n</style>") % (
          LIGHT["lbl"], LIGHT["lbl"], DARK["lbl"], DARK["lbl"], LIGHT["acc"], DARK["acc"])
    return "\n".join([
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-label="%s">' % (W, H, W, H, aria),
        st,
        "\n".join(rip), "\n".join(fish), "</svg>", ""])


def landing_motion(cls, kf, cx, cy, dur="1.6s", delay=".4s"):
    """One-shot landing ring: the only sanctioned way to point at a finding.
    Decorative circle, ends invisible (see docs/motion-constraints.md)."""
    extra = ("\n  .%s{fill:none;stroke:%s;stroke-width:1.6;opacity:0;"
             "transform-box:fill-box;transform-origin:center}\n"
             "  @media (prefers-color-scheme:dark){.%s{stroke:%s}}\n"
             "  @media (prefers-reduced-motion:no-preference){\n"
             "    .%s{animation:%s %s cubic-bezier(.22,1,.36,1) %s 1 both}\n"
             "    @keyframes %s{0%%{opacity:0;transform:scale(1.9)}\n"
             "      30%%{opacity:.85}100%%{opacity:0;transform:scale(1)}}\n  }\n"
             ) % (cls, LIGHT["acc"], cls, DARK["acc"], cls, kf, dur, delay, kf)
    ring = '<circle class="%s" cx="%.1f" cy="%.1f" r="11"/>' % (cls, cx, cy)
    return extra, ring


def sweep_y_motion(dy, kf, x0=42, x1=686, y0=30, dur="1.8s", delay=".3s"):
    """One-shot downward scan line for row-oriented figures."""
    extra = ("\n  .sweep{fill:%s;opacity:0}\n"
             "  @media (prefers-color-scheme:dark){.sweep{fill:%s}}\n"
             "  @media (prefers-reduced-motion:no-preference){\n"
             "    .sweep{animation:%s %s cubic-bezier(.22,1,.36,1) %s 1 both}\n"
             "    @keyframes %s{0%%{opacity:0;transform:translateY(0)}\n"
             "      12%%{opacity:.6}72%%{opacity:.6;transform:translateY(%dpx)}\n"
             "      100%%{opacity:0;transform:translateY(%dpx)}}\n  }\n"
             ) % (LIGHT["acc"], DARK["acc"], kf, dur, delay, kf, dy, dy)
    rect = '<rect class="sweep" x="%.0f" y="%.0f" width="%.0f" height="2.2" rx="1.1"/>' % (
        x0, y0, x1 - x0)
    return extra, rect


def month_ticks(domain, L, R, y, step=2):
    """First-of-month x ticks across the shared domain, every `step` months."""
    out, d, k = [], domain[0].replace(day=1), 0
    while d <= domain[1]:
        if k % step == 0:
            x = L + (d - domain[0]).days / max(1, (domain[1] - domain[0]).days) * (R - L)
            out.append('<text x="%.0f" y="%d" font-size="10" class="lbl tm">%d-%02d</text>'
                       % (x, y, d.year, d.month))
        d = (d + timedelta(days=32)).replace(day=1)
        k += 1
    return out


def x_date(d, domain, L, R):
    return L + (d - domain[0]).days / max(1, (domain[1] - domain[0]).days) * (R - L)


def render_punchcard(weekhours, domain, asof, aria):
    """Weekday x hour matrix. Size (not opacity, not a new colour ramp) is the
    value channel: the two WCAG-verified inks stay the only inks."""
    W, H = 700, 200
    L, R = 42.0, 686.0
    TOP, PITCH = 44.0, 17.0
    vmax = max(weekhours.values()) or 1
    peak = max(weekhours, key=lambda k: weekhours[k])
    order = [(RHYTHM_ORIGIN + k) % 24 for k in range(24)]
    pitch = (R - L) / 24
    wk = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
    filled, zeros = [], []
    for wd in range(7):
        cy = TOP + 4 + wd * PITCH + PITCH / 2 - 2
        for i, h in enumerate(order):
            v = weekhours.get((wd, h), 0)
            cx = L + pitch * (i + 0.5)
            if v == 0:
                zeros.append("M%.1f %.1fh3v3h-3z" % (cx - 1.5, cy - 1.5))
            elif (wd, h) != peak:  # the peak cell draws as the accented square
                s = max(round(math.sqrt(v / vmax) * 13, 1), 2.2)
                filled.append("M%.1f %.1fh%.1fv%.1fh-%.1fz" % (cx - s / 2, cy - s / 2, s, s, s))
    pc, pr = landing_motion("ring", "pcr",
                            L + pitch * (order.index(peak[1]) + 0.5),
                            TOP + 4 + peak[0] * PITCH + PITCH / 2 - 2, "1.7s", ".5s")
    s = max(round(math.sqrt(weekhours[peak] / vmax) * 13, 1), 2.2)
    cx = L + pitch * (order.index(peak[1]) + 0.5)
    cy = TOP + 4 + peak[0] * PITCH + PITCH / 2 - 2
    ticks = "".join('<text x="%.0f" y="%d" font-size="10" class="lbl tm">%02d</text>'
                    % (L + pitch * (i + 0.5), 174, h) for i, h in enumerate(order) if i % 4 == 0)
    rows = "".join('<text x="%.0f" y="%.1f" font-size="10" class="lbl te">%s</text>'
                   % (L - 6, TOP + 4 + wd * PITCH + PITCH / 2, wk[wd]) for wd in range(7))
    return "\n".join([
        svg_open(W, H, aria),
        style_sheet(pc),
        '<rect class="bg" width="%d" height="%d" rx="6"/>' % (W, H),
        '<path class="bar" d="%s"/>' % " ".join(filled),
        '<path class="zero" d="%s"/>' % " ".join(zeros),
        '<rect class="acc" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="1"/>' % (cx - s / 2, cy - s / 2, s, s),
        pr,
        rows, ticks,
        '<text x="%.0f" y="20" font-size="11" class="lbl ts">commits by weekday × hour · cell area ∝ count · axis 04→03 · %s → %s</text>'
        % (L, domain[0], domain[1]),
        '<text x="%.0f" y="192" font-size="9.5" class="lbl te">as of %s</text>' % (R, asof),
        "</svg>", ""])


def render_surplus(wd_hour, we_hour, wd_days, we_days, domain, asof, aria):
    """Two normalised step curves. Raw counts would make weekends look dead for
    purely arithmetic reasons (~5 weekdays per 2 weekend days); both curves are
    commits per day of that kind, and the denominators print in-frame."""
    W, H = 700, 178
    L, R, BASE = 42.0, 686.0, 138.0
    SPAN, MIN_BAR = 92.0, 2.0
    order = [(RHYTHM_ORIGIN + k) % 24 for k in range(24)]
    pitch = (R - L) / 24
    wd_rate = [wd_hour[h] / wd_days for h in order]
    we_rate = [we_hour[h] / we_days for h in order]
    rmax = max(wd_rate + we_rate) or 1

    def step_path(rates, cls):
        d = []
        for i, r in enumerate(rates):
            x0 = L + pitch * i
            x1 = L + pitch * (i + 1)
            y = BASE - max(r / rmax * SPAN, MIN_BAR)
            if i == 0:
                d.append("M%.1f %.1f" % (x0, y))
            d.append("H%.1f" % x1)
            if i < 23:
                d.append("V%.1f" % (BASE - max(rates[i + 1] / rmax * SPAN, MIN_BAR)))
        return '<path class="%s" d="%s" fill="none" stroke-width="1.8"/>' % (cls, " ".join(d))

    wp_i = wd_rate.index(max(wd_rate))
    ep_i = we_rate.index(max(we_rate))
    motion = ("\n  .sweep{fill:%s;opacity:0}\n"
              "  @media (prefers-color-scheme:dark){.sweep{fill:%s}}\n"
              "  @media (prefers-reduced-motion:no-preference){\n"
              "    .sweep{animation:sws 2s cubic-bezier(.22,1,.36,1) .5s 1 both}\n"
              "    @keyframes sws{0%%{opacity:0;transform:translateX(0)}\n"
              "      12%%{opacity:.6}70%%{opacity:.6;transform:translateX(%dpx)}\n"
              "      100%%{opacity:0;transform:translateX(%dpx)}}\n  }\n"
              ) % (LIGHT["acc"], DARK["acc"], round(R - L), round(R - L))
    ticks = "".join('<text x="%.0f" y="156" font-size="10" class="lbl tm">%02d</text>'
                    % (L + pitch * (i + 0.5), h) for i, h in enumerate(order) if i % 4 == 0)
    return "\n".join([
        svg_open(W, H, aria),
        style_sheet(motion),
        '<rect class="bg" width="%d" height="%d" rx="6"/>' % (W, H),
        '<line class="rule" x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke-width="1"/>' % (L, BASE, R, BASE),
        step_path(wd_rate, "bar"),
        step_path(we_rate, "acc"),
        '<text x="%.0f" y="20" font-size="11" class="lbl ts">commits per day, weekday vs weekend · axis 04→03 · %s → %s</text>'
        % (L, domain[0], domain[1]),
        '<text x="%.0f" y="36" font-size="10" class="lbl ts">normalised: %d weekdays ÷ %d, %d weekend days ÷ %d</text>'
        % (L, sum(wd_hour.values()), wd_days, sum(we_hour.values()), we_days),
        '<circle class="acc" cx="%.1f" cy="%.1f" r="2.6"/><text x="%.1f" y="%.1f" font-size="11" class="accv tm">%.1f/d</text>'
        % (L + pitch * (ep_i + 0.5), BASE - max(we_rate) / rmax * SPAN - 6,
           L + pitch * (ep_i + 0.5), BASE - max(we_rate) / rmax * SPAN - 10, max(we_rate)),
        '<text x="%.0f" y="172" font-size="9.5" class="lbl te">as of %s</text>' % (R, asof),
        ticks,
        "</svg>", ""])


def render_accrual(monthly, events, domain, asof, aria):
    """Cumulative lines per repo at monthly resolution. The flat-lining of the
    two archived repos on the graduation date is a graph shape, not a sentence."""
    W, H = 700, 198
    L, R, BASE, TOP = 42.0, 686.0, 158.0, 42.0
    months = []
    d = domain[0].replace(day=1)
    while d <= domain[1]:
        months.append(d)
        d = (d + timedelta(days=32)).replace(day=1)
    names = sorted({n for n, _ in monthly})
    cums = {}
    for name in names:
        c, out = 0, []
        for m0 in months:
            c += monthly.get((name, m0), 0)
            out.append(c)
        cums[name] = out
    totals = [sum(v) for v in zip(*cums.values())] if cums else [0]
    vmax = max(totals) or 1
    x = [L + i / max(1, len(months) - 1) * (R - L) for i in range(len(months))]
    y = ["%.1f" % (BASE - v / vmax * (BASE - TOP)) for v in totals]
    lines = []
    ranked = sorted(cums.items(), key=lambda kv: kv[1][-1])
    label_y = []  # (y, text, cls) — placed after a collision pass
    for name, vals in ranked:
        pts = " ".join(("M%.0f %.1f" if i == 0 else "L%.0f %.1f")
                       % (x[i], BASE - vals[i] / vmax * (BASE - TOP))
                       for i in range(len(vals)))
        lines.append('<path class="bar" d="%s" fill="none" stroke-width="1.1"/>' % pts)
        label_y.append((BASE - vals[-1] / vmax * (BASE - TOP) - 2, name, "val"))
    tot_pts = " ".join(("M%.0f %s" if i == 0 else "L%.0f %s") % (x[i], y[i])
                       for i in range(len(x)))
    lines.append('<path class="acc" d="%s" fill="none" stroke-width="2"/>' % tot_pts)
    label_y.append((TOP + 8, "total %s" % format(totals[-1], ","), "accv"))
    # De-overlap the right-edge labels bottom-up: cumulative lines end low and
    # crowd there, so each label claims its y and the one above is pushed up.
    placed = []
    cap = BASE + 8
    for ly, text, cls in sorted(label_y, key=lambda t: -t[0]):
        ly = min(ly, cap)
        placed.append((ly, text, cls))
        cap = ly - 11
    for ly, text, cls in placed:
        lines.append('<text x="%.0f" y="%.1f" font-size="9" class="%s ts">%s</text>'
                     % (R - 2, ly, cls, text))
    ev = []
    seen = set()
    for dte, label in events:
        if dte in seen or not (domain[0] <= dte <= domain[1]):
            continue
        seen.add(dte)
        ex = x_date(dte, domain, L, R)
        ev.append('<line class="rule" x1="%.1f" y1="%.0f" x2="%.1f" y2="%.0f" stroke-width="1" stroke-dasharray="3 3"/>' % (ex, TOP - 4, ex, BASE))
        ev.append('<text x="%.1f" y="%.0f" font-size="9" class="lbl tm" transform="rotate(-90 %.1f %.0f)">%s</text>'
                  % (ex - 3, BASE - 4, ex - 3, BASE - 4, label))
    motion = ("\n  .trc{fill:%s;opacity:0;offset-path:path('%s')}\n"
              "  @media (prefers-color-scheme:dark){.trc{fill:%s}}\n"
              "  @media (prefers-reduced-motion:no-preference){\n"
              "    .trc{animation:trc 2.6s cubic-bezier(.4,0,.2,1) .4s 1 both}\n"
              "    @keyframes trc{0%%{opacity:0;offset-distance:0%%}\n"
              "      8%%{opacity:.9}88%%{opacity:.9}\n"
              "      100%%{opacity:0;offset-distance:100%%}}\n  }\n"
              ) % (LIGHT["acc"], tot_pts.replace("M", "M").replace("L", " L"), DARK["acc"])
    return "\n".join([
        svg_open(W, H, aria),
        style_sheet(motion),
        '<rect class="bg" width="%d" height="%d" rx="6"/>' % (W, H),
        '<line class="rule" x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke-width="1"/>' % (L, BASE, R, BASE),
        "\n".join(ev),
        "\n".join(lines),
        '<circle class="trc" r="3.2"/>',
        "\n".join(month_ticks(domain, L, R, 176)),
        '<text x="%.0f" y="20" font-size="11" class="lbl ts">cumulative authored commits per repo · monthly · %s → %s · not the eleven years above</text>'
        % (L, domain[0], domain[1]),
        '<text x="%.0f" y="192" font-size="9.5" class="lbl te">as of %s</text>' % (R, asof),
        "</svg>", ""])


def render_lifecycles(spans, domain, asof, aria):
    """Interval ribbon. Bar ends are LAST PUSH — GitHub exposes no public
    archive timestamp, so archived-ness rides the terminal glyph, not the date."""
    W, H = 700, 180
    L, R = 42.0, 686.0
    body = []
    spans = sorted(spans, key=lambda s: s[1])  # by created
    for i, (name, created, pushed, archived) in enumerate(spans):
        y = 40 + i * 18
        x0 = x_date(created, domain, L, R)
        x1 = x_date(max(pushed, domain[0]), domain, L, R)
        cls = "acc" if not archived else "bar"
        body.append('<line class="%s" x1="%.1f" y1="%.0f" x2="%.1f" y2="%.0f" stroke-width="4" stroke-linecap="round"/>'
                    % (cls, x0, y, x1, y))
        if archived:
            body.append('<rect class="ink" x="%.1f" y="%.1f" width="7" height="7"/>' % (x1 - 3.5, y - 3.5))
        body.append('<text x="%.0f" y="%.1f" font-size="9.5" class="lbl te">%s</text>' % (L - 6, y + 3, name))
        body.append('<text x="%.1f" y="%.1f" font-size="8.5" class="lbl ts">%s → %s</text>'
                    % (x0 + 4, y - 5, created.strftime("%Y-%m"), pushed.strftime("%Y-%m")))
    mo, rect = sweep_y_motion(132, "swy")
    return "\n".join([
        svg_open(W, H, aria),
        style_sheet(mo),
        '<rect class="bg" width="%d" height="%d" rx="6"/>' % (W, H),
        "\n".join(body),
        rect,
        "\n".join(month_ticks(domain, L, R, 158)),
        '<text x="%.0f" y="20" font-size="11" class="lbl ts">repository lifespans, creation to last push · ends are last push, not archive dates</text>' % L,
        '<text x="%.0f" y="34" font-size="9.5" class="lbl ts">■ graduated (archived) · bars in blue are live · deleted repos are invisible at public caliber</text>' % L,
        '<text x="%.0f" y="174" font-size="9.5" class="lbl te">as of %s</text>' % (R, asof),
        "</svg>", ""])


def render_cadence(rel_lists, domain, asof, aria):
    """Release dots on the shared axis. negentropy's 2 tags against 2,048
    commits need the in-frame note or the figure quietly slanders the trunk."""
    W, H = 700, 180
    L, R = 42.0, 686.0
    lanes = [(n, v) for n, v in sorted(rel_lists.items(), key=lambda kv: -len(kv[1])) if v]
    body = []
    for i, (name, rels) in enumerate(lanes):
        y = 46 + i * 24
        rels = sorted(rels, key=lambda r: r["published_at"])
        body.append('<line class="rule" x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke-width="1"/>' % (L, y, R, y))
        for j, r in enumerate(rels):
            dt = datetime.strptime(r["published_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            cx = x_date(dt.date(), domain, L, R)
            dy = (j % 3 - 1) * 5
            if r["prerelease"]:
                body.append('<circle class="zero" cx="%.1f" cy="%.1f" r="3.4"/>' % (cx, y + dy))
            else:
                body.append('<circle class="%s" cx="%.1f" cy="%.1f" r="3.4"/>'
                            % ("acc" if name == "negentropy" else "bar", cx, y + dy))
        first, last = rels[0], rels[-1]
        for r, anchor in ((first, "start"), (last, "end")):
            dt = datetime.strptime(r["published_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            cx = x_date(dt.date(), domain, L, R)
            anchor_cls = "ts" if anchor == "start" else "te"
            body.append('<text x="%.1f" y="%.1f" font-size="8.5" class="lbl %s">%s</text>'
                        % (cx + (3 if anchor == "start" else -3), y + 15, anchor_cls, r["tag_name"]))
        body.append('<text x="%.0f" y="%.1f" font-size="9.5" class="lbl te">%s · %d</text>'
                    % (L - 6, y + 3, name, len(rels)))
    mo, rect = sweep_y_motion(118, "csw", delay=".5s")
    return "\n".join([
        svg_open(W, H, aria),
        style_sheet(mo),
        '<rect class="bg" width="%d" height="%d" rx="6"/>' % (W, H),
        "\n".join(body),
        rect,
        "\n".join(month_ticks(domain, L, R, 158)),
        '<text x="%.0f" y="20" font-size="11" class="lbl ts">releases on the commit timeline · hollow = pre-release · counts at left</text>' % L,
        '<text x="%.0f" y="34" font-size="9.5" class="lbl ts">negentropy ships as merged PRs, not tags — it is a deployed service, not a distributed package</text>' % L,
        '<text x="%.0f" y="174" font-size="9.5" class="lbl te">as of %s</text>' % (R, asof),
        "</svg>", ""])


def render_streak(day_counts, run, domain, asof, aria):
    """Rug with the best run bracketed, over a ROLLING 400-day window — a fixed
    span bounds the byte count forever. Zero days are drawn as a thin rule below
    the axis per contiguous run, not per-day marks: in a rug the height channel
    IS the encoding, so a zero at height 0 must still read as "nothing", but 550
    individual slots would cost more bytes than the data. Counted over authored
    commits in source repositories — NOT the GitHub calendar, which also counts
    private work, issues and reviews."""
    W, H = 700, 152
    L, R, BASE = 42.0, 686.0, 122.0
    SPAN, RUG_DAYS = 78.0, 400
    dom = (domain[1] - timedelta(days=RUG_DAYS - 1), domain[1])
    in_win = {d: n for d, n in day_counts.items() if dom[0] <= d <= dom[1]}
    vmax = max(in_win.values()) or 1
    ticks, runs = [], []
    d, run0 = dom[0], None
    while d <= dom[1]:
        x = round(x_date(d, dom, L, R))
        v = in_win.get(d, 0)
        if v:
            ticks.append("M%d %dV%d" % (x, BASE, BASE - max(math.sqrt(v / vmax) * SPAN, 2)))
            if run0 is not None:
                runs.append("M%d %dh%d" % (run0, BASE + 3, x - run0))
                run0 = None
        else:
            if run0 is None:
                run0 = x
        d += timedelta(days=1)
    if run0 is not None:
        runs.append("M%d %dH%d" % (run0, BASE + 3, round(R)))
    bx0, bx1 = round(x_date(run[0], dom, L, R)), round(x_date(run[1], dom, L, R))
    motion = ("\n  .tick{stroke:%s;fill:none;stroke-width:1.4}\n"
              "  @media (prefers-color-scheme:dark){.tick{stroke:%s}}\n"
              "  .sweep{fill:%s;opacity:0}\n"
              "  @media (prefers-color-scheme:dark){.sweep{fill:%s}}\n"
              "  @media (prefers-reduced-motion:no-preference){\n"
              "    .sweep{animation:sbs 1.8s cubic-bezier(.22,1,.36,1) .5s 1 both}\n"
              "    @keyframes sbs{0%%{opacity:0;transform:translateX(0)}\n"
              "      15%%{opacity:.65}75%%{opacity:.65;transform:translateX(%dpx)}\n"
              "      100%%{opacity:0;transform:translateX(%dpx)}}\n  }\n"
              ) % (LIGHT["bar"], DARK["bar"], LIGHT["acc"], DARK["acc"],
                   max(bx1 - bx0, 2), max(bx1 - bx0, 2))
    return "\n".join([
        svg_open(W, H, aria),
        style_sheet(motion),
        '<rect class="bg" width="%d" height="%d" rx="6"/>' % (W, H),
        '<line class="rule" x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke-width="1"/>' % (L, BASE, R, BASE),
        '<path class="tick" d="%s"/>' % " ".join(ticks),
        '<path class="zero" d="%s"/>' % " ".join(runs),
        '<line class="acc" x1="%d" y1="30" x2="%d" y2="30" stroke-width="1.6"/>'
        '<line class="acc" x1="%d" y1="26" x2="%d" y2="34" stroke-width="1.6"/>'
        '<line class="acc" x1="%d" y1="26" x2="%d" y2="34" stroke-width="1.6"/>'
        % (bx0, bx1, bx0, bx0, bx1, bx1),
        '<text x="%.0f" y="22" font-size="11" class="accv tm">%d days, %s → %s</text>'
        % ((bx0 + bx1) / 2, (run[1] - run[0]).days + 1, run[0], run[1]),
        '<rect class="sweep" x="%d" y="34" width="2.2" height="%.0f" rx="1.1"/>' % (bx0, BASE - 34),
        "\n".join(month_ticks(dom, L, R, 142, step=3)),
        '<text x="%.0f" y="20" font-size="11" class="lbl ts">one tick per day, latest %d · height ∝ √commits · authored commits in source repos, not the GitHub calendar</text>'
        % (L, RUG_DAYS),
        '<text x="%.0f" y="146" font-size="9.5" class="lbl te">as of %s</text>' % (R, asof),
        "</svg>", ""])


def render_latency(buckets, ecdf, stats, asof, aria):
    """Log-bucket histogram + step ECDF. The in-frame header must carry the
    caliber caveat — outside the fold, a beautiful latency figure reads as a
    velocity brag."""
    W, H = 700, 200
    L, R, BASE = 42.0, 560.0, 158.0
    ER = 686.0  # ECDF right axis
    SPAN, MIN_BAR = 104.0, 2.0
    n = len(buckets)
    pitch = (R - L) / n
    bw = round(pitch * 0.58, 1)
    bmax = max(c for _, c in buckets) or 1
    parts, labels = [], []
    for i, (lab, c) in enumerate(buckets):
        h = max(c / bmax * SPAN, MIN_BAR)
        x = L + pitch * (i + 0.5) - bw / 2
        parts.append('<rect class="bar" x="%.1f" y="%.2f" width="%.1f" height="%.2f" rx="2"/>'
                     % (x, BASE - h, bw, h))
        labels.append('<text x="%.1f" y="%.1f" font-size="9" class="val tm">%d</text>'
                      % (L + pitch * (i + 0.5), BASE - h - 4, c))
        labels.append('<text x="%.1f" y="174" font-size="8.5" class="lbl tm">%s</text>'
                      % (L + pitch * (i + 0.5), lab))
    pts = ["M%.1f %.1f" % (ER, BASE)]
    for i, p in enumerate(ecdf):
        x = L + pitch * (i + 0.5)
        y = BASE - p / 100 * SPAN
        pts.append("L%.1f %.1f" % (x, y))
        pts.append("L%.1f %.1f" % (L + pitch * (i + 1.5) if i + 1 < n else ER, y))
    med_x = L + pitch * (stats["med_i"] + 1.5)
    hr_x = L + pitch * (stats["hour_i"] + 1.5)
    mo, ring = landing_motion("ring", "lnr", med_x, BASE - 10, "1.5s", ".8s")
    return "\n".join([
        svg_open(W, H, aria),
        style_sheet(mo),
        '<rect class="bg" width="%d" height="%d" rx="6"/>' % (W, H),
        '<line class="rule" x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke-width="1"/>' % (L, BASE, ER, BASE),
        '<line class="rule" x1="%.1f" y1="%.0f" x2="%.1f" y2="%.0f" stroke-width="1"/>' % (ER, BASE, ER, BASE - SPAN),
        "\n".join(parts),
        '<path class="acc" d="%s" fill="none" stroke-width="1.8"/>' % " ".join(pts),
        '<line class="acc" x1="%.1f" y1="%.0f" x2="%.1f" y2="%.0f" stroke-width="1" stroke-dasharray="2 3"/>' % (med_x, BASE, med_x, BASE - SPAN - 2),
        '<text x="%.1f" y="%.0f" font-size="10" class="accv tm">median %s</text>' % (med_x, BASE - SPAN + 10, stats["med"]),
        '<line class="val" x1="%.1f" y1="%.0f" x2="%.1f" y2="%.0f" stroke-width="1" stroke-dasharray="2 3"/>' % (hr_x, BASE, hr_x, BASE - SPAN - 2),
        '<text x="%.1f" y="%.0f" font-size="9.5" class="val tm">1 h</text>' % (hr_x, BASE - SPAN + 10),
        ring,
        "\n".join(labels),
        '<text x="%.1f" y="%.0f" font-size="9" class="lbl te">100%%</text>' % (ER + 4, BASE - SPAN),
        '<text x="%.1f" y="%.0f" font-size="9" class="lbl te">0%%</text>' % (ER + 4, BASE),
        '<text x="%.0f" y="20" font-size="11" class="lbl ts">merged-PR lifetime in negentropy · %d merged, %d closed-unmerged excluded · solo self-merge: unit size, not review speed</text>'
        % (L, stats["n"], stats["unmerged"]),
        '<text x="%.0f" y="32" font-size="9.5" class="lbl ts">log buckets; the tail is compressed by design — longest was %s (printed, not just bucketed)</text>'
        % (L, stats["lat_max"]),
        '<text x="%.0f" y="194" font-size="9.5" class="lbl te">as of %s</text>' % (R + 120, asof),
        "</svg>", ""])


def render_grammar(types_sorted, nonconf, total, sub1pct, asof, aria):
    """100-cell waffle: makes "77 of 100" countable. Types under one percent
    earn no cell and are folded into the footer instead of stealing one."""
    W, H = 700, 172
    X0, Y0, P = 150.0, 44.0, 14.0
    cells, legend = [], []
    xi = yi = 0
    total_conf = sum(c for _, c in types_sorted)
    for rank, (name, c) in enumerate(types_sorted):
        n_cells = round(c / total * 100)
        cls = "acc" if rank == 0 else "bar"
        d = []
        for _ in range(n_cells):
            d.append("M%.0f %.0fh10v10h-10z" % (X0 + xi * P, Y0 + yi * P))
            xi += 1
            if xi == 10:
                xi, yi = 0, yi + 1
        if d:
            cells.append('<path class="%s" d="%s"/>' % (cls, " ".join(d)))
        legend.append('<text x="%.0f" y="%.0f" font-size="10" class="%s ts">%s %d</text>'
                      % (X0 + 160, Y0 + rank * 14, "accv" if rank == 0 else "val", name, c))
    zc = nonconf
    d = []
    for _ in range(round(zc / total * 100)):
        d.append("M%.0f %.0fh10v10h-10z" % (X0 + xi * P, Y0 + yi * P))
        xi += 1
        if xi == 10:
            xi, yi = 0, yi + 1
    mo, ring = landing_motion("ring", "grr", X0 + (xi - 0.5) * P - 5, Y0 + yi * P + 5, "1.5s", ".7s")
    return "\n".join([
        svg_open(W, H, aria),
        style_sheet(mo),
        '<rect class="bg" width="%d" height="%d" rx="6"/>' % (W, H),
        "\n".join(cells),
        '<path class="zero" d="%s"/>' % " ".join(d),
        ring,
        "\n".join(legend),
        '<text x="%.0f" y="%.0f" font-size="10" class="val ts">none-parse %d</text>'
        % (X0 + 160, Y0 + len(types_sorted) * 14, nonconf),
        '<text x="%.0f" y="20" font-size="11" class="lbl ts">commit subjects by Conventional Commits type · one cell = one percent of %s</text>'
        % (42, format(total, ",")),
        '<text x="%.0f" y="34" font-size="9.5" class="lbl ts">open cells do not parse as Conventional Commits · %s</text>'
        % (42, sub1pct),
        '<text x="%.0f" y="166" font-size="9.5" class="lbl te">as of %s</text>' % (686, asof),
        "</svg>", ""])


def render_tongues(lang_all, lang_src, gen_site, zero_repos, asof, aria):
    """Slope chart between two rankings. The honesty problem IS the content:
    GitHub's language endpoint says HTML (a generated static site); drop that
    one named repo and it says Python. Both conditions, not a silent pick."""
    W, H = 700, 196
    XL, XR = 210.0, 470.0
    ta = sum(lang_all.values()) or 1
    ts = sum(lang_src.values()) or 1
    names = sorted(set(lang_all) | set(lang_src),
                   key=lambda n: -lang_src.get(n, 0))[:7]
    if "HTML" not in names and lang_all.get("HTML"):
        names.append("HTML")
    TOP, STEP, SPAN = 44.0, 19.0, 116.0
    na = {n: lang_all.get(n, 0) / ta for n in names}
    ns = {n: lang_src.get(n, 0) / ts for n in names}
    ymax = max(list(na.values()) + list(ns.values())) or 1

    def y_of(p):
        return TOP + SPAN - p / ymax * SPAN

    body = []
    for n in names:
        y1, y2 = y_of(na[n]), y_of(ns[n])
        cls = "acc" if n == max(ns, key=ns.get) else "bar"
        body.append('<line class="%s" x1="%.0f" y1="%.1f" x2="%.0f" y2="%.1f" stroke-width="1.6"/>'
                    % (cls, XL, y1, XR, y2))
        body.append('<circle class="%s" cx="%.0f" cy="%.1f" r="2.4"/><circle class="%s" cx="%.0f" cy="%.1f" r="2.4"/>'
                    % (cls, XL, y1, cls, XR, y2))
        body.append('<text x="%.0f" y="%.1f" font-size="10" class="lbl te">%s %.1f%%</text>'
                    % (XL - 8, y1 + 3, n, na[n] * 100))
        body.append('<text x="%.0f" y="%.1f" font-size="10" class="%s ts">%s %.1f%%</text>'
                    % (XR + 8, y2 + 3, "accv" if cls == "acc" else "val", n, ns[n] * 100))
    others_a = 1 - sum(na.values())
    others_s = 1 - sum(ns.values())
    return "\n".join([
        svg_open(W, H, aria),
        style_sheet(),
        '<rect class="bg" width="%d" height="%d" rx="6"/>' % (W, H),
        "\n".join(body),
        '<text x="%.0f" y="%.0f" font-size="10" class="lbl tm">as GitHub counts it</text>' % (XL, 32),
        '<text x="%.0f" y="%.0f" font-size="10" class="lbl tm">excluding %s</text>' % (XR, 32, gen_site),
        '<text x="%.0f" y="176" font-size="9.5" class="lbl ts">others %.1f%% / %.1f%% · bytes measure committed source size, not authorship or effort · %s</text>'
        % (42, others_a * 100, others_s * 100,
           ("no counted bytes: " + ", ".join(zero_repos)) if zero_repos else "no zero-byte source repos"),
        '<text x="%.0f" y="20" font-size="11" class="lbl ts">language byte share under two conditions · %s is generated static-site output</text>' % (42, gen_site),
        '<text x="%.0f" y="190" font-size="9.5" class="lbl te">as of %s</text>' % (686, asof),
        "</svg>", ""])


def render_upstream(items, pub_prs, asof, aria):
    """Named-event ledger. n=6: any aggregate destroys the only value. The
    in-frame denominator is what keeps a full-width figure honest about a
    small number."""
    W, H = 700, 158
    L, R, BASE = 42.0, 686.0, 96.0
    rows = sorted(items, key=lambda it: it["created_at"])
    d0 = datetime.strptime(rows[0]["created_at"], "%Y-%m-%dT%H:%M:%SZ").date()
    d1 = datetime.strptime(rows[-1]["created_at"], "%Y-%m-%dT%H:%M:%SZ").date()
    dom = (d0, d1)
    body, labels = [], []
    for i, it in enumerate(rows):
        dt = datetime.strptime(it["created_at"], "%Y-%m-%dT%H:%M:%SZ").date()
        x = x_date(dt, dom, L, R)
        y = BASE - (i % 2) * 26 - 8
        slug = it["repository_url"].split("/repos/")[1]
        merged = bool(it["pull_request"]["merged_at"])
        body.append('<line class="rule" x1="%.1f" y1="%.0f" x2="%.1f" y2="%.0f" stroke-width="1"/>'
                    % (x, BASE, x, y + (3 if merged else 3)))
        if merged:
            body.append('<circle class="%s" cx="%.1f" cy="%.1f" r="3.6"/>'
                        % ("acc" if slug.split("/")[0] == DIFY_OWNER else "bar", x, y))
        else:
            body.append('<circle class="zero" cx="%.1f" cy="%.1f" r="3.6"/>' % (x, y))
        body.append('<text x="%.1f" y="%.1f" font-size="9" class="%s %s">%s#%d · %s · %s</text>'
                    % (x, y - 7, "val" if merged else "lbl", "tm" if 0 < x < 640 else ("ts" if x <= 42 else "te"),
                       slug, it["number"], "merged" if merged else "closed unmerged",
                       it["created_at"][:10]))
    return "\n".join([
        svg_open(W, H, aria),
        style_sheet(),
        '<rect class="bg" width="%d" height="%d" rx="6"/>' % (W, H),
        '<line class="rule" x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke-width="1"/>' % (L, BASE, R, BASE),
        "\n".join(body),
        "\n".join(labels),
        '<text x="%.0f" y="130" font-size="9.5" class="lbl ts">%d external public PRs — %.1f%% of %s public PRs; the rest are my own repositories</text>'
        % (42, len(rows), len(rows) / pub_prs * 100, format(pub_prs, ",")),
        '<text x="%.0f" y="20" font-size="11" class="lbl ts">pull requests into code I do not own · hollow = closed unmerged · blue = Dify ecosystem</text>' % 42,
        '<text x="%.0f" y="152" font-size="9.5" class="lbl te">as of %s</text>' % (686, asof),
        "</svg>", ""])
# ------------------------------------------------------------ sanitizer ----
BANNED = re.compile(r'infinite|repeatCount\s*=\s*["\']indefinite')
KEYFRAME = re.compile(r'@keyframes\s+(\w+)\s*\{', re.S)


def assert_svg_sane(src: str, name: str, max_bytes=8192):
    """Write-gate: no loops, a11y metadata, size budget, no external resources,
    additive-only motion (base opacity:0 + explicit 0%/100% opacity:0), one
    @keyframes per file, animated classes never carry text, dark override
    strictly after base rules. The prose counterpart of these rules is
    docs/motion-constraints.md."""
    assert not BANNED.search(src), f"{name}: infinite/indefinite loop found"
    assert 'role="img"' in src and "aria-label" in src, f"{name}: a11y metadata missing"
    n = len(src.encode("utf-8"))
    assert n <= max_bytes, f"{name}: {n}B over budget"
    assert "@import" not in src and 'href="http' not in src, f"{name}: external resource"
    if "animation:" in src:
        assert "prefers-reduced-motion:no-preference" in src, f"{name}: motion not opt-in"
        knames = KEYFRAME.findall(src)
        # The body extraction below is a non-greedy regex; with more than one
        # @keyframes a block's assertions can be validated against a blob
        # containing its neighbours (a reachable false-pass). One keyframes per
        # file + animation-delay:var(--d) staggering is the pattern instead.
        assert len(set(knames)) == len(knames), f"{name}: duplicate @keyframes name"
        assert len(knames) <= 1, f"{name}: >1 @keyframes — stagger with animation-delay:var(--d)"
        for kname in knames:
            body = re.search(r'@keyframes\s+' + kname + r'\s*\{(.*?)\n\s*\}', src, re.S).group(1)
            assert re.search(r'0%\{[^}]*opacity:\s*0', body), f"{name}: {kname} missing 0%{{opacity:0}}"
            assert re.search(r'100%\{[^}]*opacity:\s*0', body), f"{name}: {kname} missing 100%{{opacity:0}}"
        for cls in set(re.findall(r'\.([\w-]+)\{[^}]*animation:', src)):
            base = re.search(r'\.' + cls + r'\{([^}]*)\}', src)
            assert base and "opacity:0" in base.group(1).replace(" ", ""), \
                f"{name}: .{cls} animates but base state is not opacity:0 (additive rule)"
            # Reduced-motion users keep the static canvas, so anything animated
            # must be discardable decoration — a <text> (or any data-bearing
            # mark) that fades in and out would erase its datum at rest.
            assert not re.search(r'<text[^>]*class="[^"]*\b%s\b' % cls, src), \
                f"{name}: animated class .{cls} carries text — data must survive reduced-motion"
    # Dark-override ordering: a class's FIRST definition must sit outside every
    # @media(prefers-color-scheme:dark) span. (Comparing against the position of
    # the first dark block anywhere is wrong for classes whose whole rule set —
    # base included — lives in the motion extras appended after the palette.)
    dark_spans = []
    for m in re.finditer(r"@media \(prefers-color-scheme:dark\)\{", src):
        depth, j = 1, m.end()
        while depth and j < len(src):  # brace-balanced: tolerates the inline
            depth += (src[j] == "{") - (src[j] == "}")  # one-line dark format
            j += 1
        dark_spans.append((m.start(), j))
    for cls in ("bg", "ink", "lbl", "val", "bar", "acc", "accv", "zero",
                "sweep", "fi", "eye", "rip", "tick"):
        i = src.find(".%s{" % cls)
        if i != -1:
            assert not any(a <= i <= b for a, b in dark_spans), \
                f"{name}: .{cls} first definition is inside a dark override"
    return n


# ----------------------------------------------------------------- alt ----
# The README <img> alt is the ONLY channel a screen reader gets: an SVG loaded
# via <img> has its internal aria-label ignored. So the alt carries the full
# data series and must refresh with it, in both languages.
#
# Shape claims are derived ONCE here and merely *phrased* per language below.
# The previous design re-derived them inside each language's function, which had
# already drifted: the zero-hour range was hardcoded, and the dip sentence used
# a fixed negative index, so in 2027 the chart would draw a dip arrow its own
# alt text no longer mentioned.
def growth_shape(values, years):
    return {
        "zeros": [years[i] for i, v in enumerate(values) if v == 0],
        "dips": [(years[i], values[i], years[i - 1], values[i - 1])
                 for i in range(1, len(values))
                 if values[i] and values[i] < values[i - 1]],
    }


def zero_runs(hours):
    """Contiguous runs of true-zero hours along the 04→03 axis, as [(lo, hi)]."""
    runs, run = [], []
    for h in [(RHYTHM_ORIGIN + k) % 24 for k in range(24)]:
        if hours[h] == 0:
            run.append(h)
        elif run:
            runs.append((run[0], run[-1]))
            run = []
    return runs + ([(run[0], run[-1])] if run else [])


def _join(parts, sep, last):
    if len(parts) < 2:
        return "".join(parts)
    return sep.join(parts[:-1]) + last + parts[-1]


def growth_alt(f, values, years):
    sh = growth_shape(values, years)
    series = ", ".join(format(v, ",") for v in values)
    z = [str(y) for y in sh["zeros"]]
    if f == EN:
        zc = ("" if not z else
              " %s %s exactly zero, drawn as %s below the axis." % (
                  _join(z, ", ", " and "), "is" if len(z) == 1 else "are",
                  "an open slot" if len(z) == 1 else "open slots"))
        dc = "".join(" %d (%s) is lower than %d (%s)." % (y, format(v, ","), py, format(pv, ","))
                     for y, v, py, pv in sh["dips"])
        return ("Column chart, contributions per year %d to %d on a square-root scale: "
                "%s.%s%s Data: GitHub." % (years[0], years[-1], series, zc, dc))
    zc = "" if not z else "%s 为真实零值，画作基线下方的空槽。" % "、".join(z)
    dc = "".join("%d（%s）低于 %d（%s）。" % (y, format(v, ","), py, format(pv, ","))
                 for y, v, py, pv in sh["dips"])
    return ("%d–%d 逐年贡献柱状图，平方根标度：%s。%s%s数据：GitHub。"
            % (years[0], years[-1], series, zc, dc))


def rhythm_alt(f, hours):
    order = [(RHYTHM_ORIGIN + k) % 24 for k in range(24)]
    seq = ", ".join(str(hours[h]) for h in order)
    total = sum(hours.values())
    ph = max(hours, key=lambda h: hours[h])
    pv = hours[ph]
    runs = zero_runs(hours)
    last = (RHYTHM_ORIGIN + 23) % 24
    if f == EN:
        zc = ("" if not runs else " %s exactly zero, drawn as open slots below the axis." % (
            _join(["%02d:00 to %02d:59" % r for r in runs], ", ", " and ") +
            (" is" if len(runs) == 1 and runs[0][0] == runs[0][1] else " are")))
        return ("Histogram of %s open-source commits by hour of day, Asia/Shanghai, axis "
                "running %02d:00 through %02d:00 so the night block stays contiguous. Values "
                "by hour from %02d:00: %s.%s Peak %02d:00 with %d commits, %.1f percent of "
                "all commits, %.2f times a flat baseline. Bars below the 2.5-pixel minimum "
                "height are drawn at that minimum."
                % (format(total, ","), RHYTHM_ORIGIN, last, RHYTHM_ORIGIN, seq, zc,
                   ph, pv, pv / total * 100, pv / (total / 24)))
    zc = "" if not runs else "%s 为真实零值（基线下方空槽）。" % "、".join(
        "%02d:00–%02d:59" % r for r in runs)
    return ("开源提交按小时分布直方图（共 %s 条，Asia/Shanghai，横轴自 %02d:00 起至 %02d:00，"
            "使夜间块连续）。自 %02d:00 起逐小时数值：%s。%s峰值 %02d:00 共 %d 条——占全部提交 "
            "%.1f%%，为平坦基线的 %.2f 倍。低于最小可见高度 2.5 像素的柱按最小高度绘制。"
            % (format(total, ","), RHYTHM_ORIGIN, last, RHYTHM_ORIGIN, seq, zc,
               ph, pv, pv / total * 100, pv / (total / 24)))


def ground_alt(f, counts, rel, archived):
    rows = sorted(counts.items(), key=lambda kv: -kv[1])
    total = sum(counts.values())
    rtot = sum(rel.values())
    share = rows[0][1] / total * 100
    rel_rows = [(n, c) for n, c in sorted(rel.items(), key=lambda kv: -kv[1]) if c]
    if f == EN:
        arc = ("" if not archived else " %s %s archived — %s graduated into the negentropy trunk."
               % (_join(archived, ", ", " and "), "is" if len(archived) == 1 else "are",
                  "it" if len(archived) == 1 else "they"))
        return ("Horizontal bar chart, commits per source repository, sorted: %s. Total %s "
                "commits and %d releases across %d source repositories; %s is %.1f percent of "
                "commits. Releases: %s.%s"
                % ("; ".join("%s %s" % (n, format(v, ",")) for n, v in rows),
                   format(total, ","), rtot, len(counts), rows[0][0], share,
                   ", ".join("%s %d" % r for r in rel_rows), arc))
    arc = ("" if not archived else "%s 已归档——毕业并入 negentropy 主干。"
           % "、".join(archived))
    return ("各源仓库提交量水平条形图（降序）：%s。共 %s 条提交、%d 个 release、%d 个源仓库；"
            "%s 占 %.1f%%。Release 分布：%s。%s"
            % ("；".join("%s %s" % (n, format(v, ",")) for n, v in rows),
               format(total, ","), rtot, len(counts), rows[0][0], share,
               "、".join("%s %d" % r for r in rel_rows), arc))


def mark_alt(f):
    if f == EN:
        return ("Three fish, drawn as a signature mark. In Mandarin the three surpluses of "
                "Dong Yu — winter, night, and rainy days (三余, sān yú) — sound nearly the "
                "same as three fish (三鱼). Hence the handle ThreeFish. Purely decorative; "
                "no data encoded.")
    return ("三条鱼，作为签名图形。汉语里，董遇的「三余」——冬天、夜晚、雨天（sān yú）"
            "——与「三鱼」几乎同音，ID 由此而来。纯装饰，不编码任何数据。")


# v5 figures. Alt policy: the full series ships only when it has at most 24
# values per series (growth n=11, rhythm n=24, surplus 2×24); above that the
# alt carries extrema, marginals and the zero count instead.
def punchcard_alt(f, weekhours, domain, wknd, wd_days, we_days):
    day_names = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
    wd_tot = [sum(n for (wd, _), n in weekhours.items() if wd == i) for i in range(7)]
    peak = max(weekhours, key=lambda k: weekhours[k])
    empty = sum(1 for wd in range(7) for h in range(24) if not weekhours.get((wd, h)))
    tot = sum(weekhours.values())
    if f == EN:
        return ("Punchcard of %s open-source commits by weekday and hour, Asia/Shanghai, "
                "columns running 04:00 to 03:00 and rows %s to %s, window %s to %s. Cell "
                "area is proportional to count; cell side rounded to one decimal. Weekday "
                "totals Monday to Sunday: %s. Densest cell %s at %02d:00 with %d commits. "
                "%d of 168 cells are exactly zero, drawn as open squares. Weekends hold "
                "%s commits = %.1f percent, against a flat share of %.1f. Data: GitHub."
                % (format(tot, ","), day_names[0], day_names[-1],
                   domain[0], domain[1], ", ".join(str(v) for v in wd_tot),
                   day_names[peak[0]], peak[1], weekhours[peak], empty,
                   format(wknd, ","), wknd / tot * 100, 2 / 7 * 100))
    return ("开源提交按星期 × 小时的打卡图（共 %s 条，Asia/Shanghai，列自 04:00 至 03:00，"
            "行自周一至周日，窗口 %s 至 %s）。格面积与提交数成正比，边长保留一位小数。"
            "周一至周日合计：%s。最密格 %s %02d:00，%d 条。168 格中 %d 格为真实零值，画作空心方框。"
            "周末合计 %s 条，占 %.1f%%（平坦份额为 %.1f%%）。数据：GitHub。"
            % (format(tot, ","), domain[0], domain[1], "、".join(str(v) for v in wd_tot),
               day_names[peak[0]], peak[1], weekhours[peak], empty,
               format(wknd, ","), wknd / tot * 100, 2 / 7 * 100))


def surplus_alt(f, wd_hour, we_hour, wd_days, we_days, domain):
    order = [(RHYTHM_ORIGIN + k) % 24 for k in range(24)]
    wd_seq = ", ".join("%.1f" % (wd_hour[h] / wd_days) for h in order)
    we_seq = ", ".join("%.1f" % (we_hour[h] / we_days) for h in order)
    wp = max(range(24), key=lambda h: wd_hour[h])
    ep = max(range(24), key=lambda h: we_hour[h])
    if f == EN:
        return ("Two step curves on one hour-of-day axis running 04:00 to 03:00, "
                "Asia/Shanghai, %s to %s, normalised to commits per day of that kind so "
                "%d weekdays and %d weekend days are comparable. Weekday rate by hour from "
                "04:00: %s. Weekend rate: %s. Weekday peak %02d:00 at %.1f per day; "
                "weekend peak %02d:00 at %.1f. Data: GitHub."
                % (domain[0], domain[1], wd_days, we_days, wd_seq, we_seq,
                   wp, wd_hour[wp] / wd_days, ep, we_hour[ep] / we_days))
    return ("同一小时轴（04:00 至 03:00，Asia/Shanghai，%s 至 %s）上的两条阶梯曲线，"
            "按「该类日」归一为日均提交，使 %d 个工作日与 %d 个周末日可比。工作日自 04:00 起"
            "逐小时速率：%s。周末：%s。工作日峰值 %02d:00（日均 %.1f 条）；周末峰值 %02d:00"
            "（日均 %.1f 条）。数据：GitHub。"
            % (domain[0], domain[1], wd_days, we_days, wd_seq, we_seq,
               wp, wd_hour[wp] / wd_days, ep, we_hour[ep] / we_days))


def accrual_alt(f, monthly, domain, events, final_total):
    names = sorted({n for n, _ in monthly})
    finals = {n: sum(v for (nm, _), v in monthly.items() if nm == n) for n in names}
    ev = sorted({e[0] for e in events})
    ev_txt = "; ".join("on %s both archived repos flatten and the trunk keeps rising" % d for d in ev)
    if f == EN:
        return ("Cumulative authored commits per source repository at monthly resolution, "
                "%s to %s — a window of about %d months, not the eleven years shown above. "
                "Final totals: %s; all repos together %s. %s: both graduated into the "
                "negentropy trunk that day. Data: GitHub."
                % (domain[0], domain[1], round((domain[1] - domain[0]).days / 30.44),
                   ", ".join("%s %s" % (n, format(finals[n], ",")) for n in names),
                   format(final_total, ","), ev_txt))
    return ("各源仓库累计提交折线（月分辨率，%s 至 %s——约 %d 个月窗口，不是上方那张十一年图）。"
            "期末合计：%s；全部仓库共 %s。%s：两个仓库于该日毕业并入 negentropy 主干。数据：GitHub。"
            % (domain[0], domain[1], round((domain[1] - domain[0]).days / 30.44),
               "；".join("%s %s" % (n, format(finals[n], ",")) for n in names),
               format(final_total, ","),
               "；".join("%s 两个已归档仓库走平、主干继续上升" % d for d in ev)))


def lifecycles_alt(f, spans, domain):
    if f == EN:
        rows = "; ".join("%s created %s, last push %s, %s" % (
            n, c.strftime("%Y-%m-%d"), p.strftime("%Y-%m-%d"),
            "archived (graduated)" if a else "active") for n, c, p, a in spans)
        return ("Timeline ribbon, one row per source repository from creation to last push, "
                "%s to %s. %s. Bar ends mark last push — the closest public proxy for "
                "archival, because GitHub exposes no archive timestamp; archived-ness rides "
                "the square terminal glyph instead. Repositories deleted before today are "
                "invisible at public caliber. Data: GitHub."
                % (domain[0], domain[1], rows))
    rows = "；".join("%s 创建于 %s，最后推送 %s，%s" % (
        n, c.strftime("%Y-%m-%d"), p.strftime("%Y-%m-%d"),
        "已归档（毕业）" if a else "活跃") for n, c, p, a in spans)
    return ("仓库生命周期色带，每行一个源仓库，自创建至最后推送，%s 至 %s。%s。条形终点是"
            "最后推送——归档的最近公开代理，因为 GitHub 不公开归档时间戳；归档与否由方形"
            "终端图元承载。已被删除的仓库在公开口径下不可见。数据：GitHub。"
            % (domain[0], domain[1], rows))


def cadence_alt(f, rel_lists, domain):
    lanes = sorted(((n, sorted(v, key=lambda r: r["published_at"]))
                    for n, v in rel_lists.items() if v),
                   key=lambda kv: (-len(kv[1]), kv[0]))
    if f == EN:
        rows = "; ".join(
            "%s: %d releases, %s on %s through %s on %s%s" % (
                n, len(v), v[0]["tag_name"], v[0]["published_at"][:10],
                v[-1]["tag_name"], v[-1]["published_at"][:10],
                "" if not all(r["prerelease"] for r in v) else ", all pre-releases")
            for n, v in lanes)
        return ("Dot timeline of %d public releases across %d repositories on one shared "
                "date axis, %s to %s. %s. Hollow dots are pre-releases. negentropy shows "
                "only its two release candidates against 2,048 commits because it is a "
                "deployed service, not a distributed package — its shipping unit is the "
                "merged pull request, not the tag. Data: GitHub."
                % (rel_total, len(lanes), domain[0], domain[1], rows))
    rows = "；".join(
        "%s %d 个 release，%s（%s）至 %s（%s）%s" % (
            n, len(v), v[0]["tag_name"], v[0]["published_at"][:10],
            v[-1]["tag_name"], v[-1]["published_at"][:10],
            "" if not all(r["prerelease"] for r in v) else "，全部为预发布")
        for n, v in lanes)
    return ("各仓库公开 release 的点式时间线（共用日期轴，%s 至 %s）。%s。空心点为预发布。"
            "negentropy 在 2,048 条提交面前只有两个 rc，因为它是部署型服务而非分发包——"
            "它的交付单元是已合并 PR，不是 tag。数据：GitHub。"
            % (domain[0], domain[1], rows))


def streak_alt(f, act, zeros, best, dom, rug_days):
    if f == EN:
        return ("Rug plot, one tick per day over the latest %d days, %s to %s; tick height "
                "is the square root of that day's authored-commit count. %d days carry at "
                "least one commit (%.0f percent); the %d empty ones are drawn as a thin "
                "rule below the axis, one segment per gap. The longest unbroken run inside "
                "this window is %d days, %s to %s, marked with a bracket. Counted over "
                "authored commits in source repositories — the same population as every "
                "other commit figure here, and narrower than the GitHub contributions "
                "calendar, which also counts private work, issues and reviews. Data: GitHub."
                % (rug_days, dom[0], dom[1], act, act / rug_days * 100, zeros,
                   (best[1] - best[0]).days + 1, best[0], best[1]))
    return ("一维 rug 图，取最近 %d 天（%s 至 %s），每天一根刻度，高度为当日署名提交数的平方根。"
            "%d 天有至少一条提交（%.0f%%）；其余 %d 天画作基线下方的细线，每个空档一段。窗口内"
            "最长连续区间 %d 天（%s 至 %s），以括号标出。口径为源仓库内我署名的提交——与本页其他"
            "提交图同一总体，且窄于 GitHub 贡献日历（后者还计入私有工作、issue 与 review）。数据：GitHub。"
            % (rug_days, dom[0], dom[1], act, act / rug_days * 100, zeros,
               (best[1] - best[0]).days + 1, best[0], best[1]))


def latency_alt(f, buckets, stats, pct_hour):
    if f == EN:
        rows = ", ".join("%s %d" % (lab, c) for lab, c in buckets)
        return ("Histogram of merged pull-request lifetime in negentropy with a step "
                "cumulative curve on a right-hand zero-to-hundred-percent axis. %d merged "
                "pull requests, log-spaced buckets: %s. Median %s; 90th percentile %s; "
                "%.0f percent merge within an hour; the longest waited %s. %d further "
                "closed pull requests were never merged and are excluded. This is a solo "
                "self-merge repository: the lifetime measures how small a change unit is, "
                "not how fast a review is. Data: GitHub."
                % (stats["n"], rows, stats["med"], stats["p90"], pct_hour,
                   stats["lat_max"], stats["unmerged"]))
    rows = "、".join("%s %d" % (lab, c) for lab, c in buckets)
    return ("negentropy 已合并 PR 的生存时间直方图，右侧带 0–100%% 阶梯累积曲线。共 %d 个已合并"
            "PR，对数分箱：%s。中位 %s；90 分位 %s；%.0f%% 一小时内合并；最长等待 %s。另有 %d 个"
            "已关闭未合并的 PR，未计入。这是单人自合并仓库：生存时间量的是变更单元有多小，"
            "不是评审有多快。数据：GitHub。"
            % (stats["n"], rows, stats["med"], stats["p90"], pct_hour,
               stats["lat_max"], stats["unmerged"]))


def grammar_alt(f, types_sorted, nonconf, total):
    rows = ", ".join("%s %d" % (n, c) for n, c in types_sorted)
    if f == EN:
        return ("Waffle chart of one hundred cells, each cell one percent of %s authored "
                "commit subjects classified by Conventional Commits prefix. %s. %d subjects "
                "do not parse as Conventional Commits and are drawn as open cells. The "
                "accented block is %s, the largest type at %s of all subjects. Data: GitHub."
                % (format(total, ","), rows, nonconf, types_sorted[0][0],
                   f"{types_sorted[0][1] / total * 100:.1f} percent"))
    return ("一百格华夫图，每格代表 %s 条署名提交主题的百分之一，按 Conventional Commits "
            "前缀分类。%s。%d 条主题不能解析为 Conventional Commits，画作空心格。着色块为 "
            "%s——最大类型，占全部主题的 %.1f%%。数据：GitHub。"
            % (format(total, ","), "、".join("%s %d" % (n, c) for n, c in types_sorted),
               nonconf, types_sorted[0][0], types_sorted[0][1] / total * 100))


def tongues_alt(f, lang_all, lang_src, gen_site, zero_repos):
    ta, tsrc = sum(lang_all.values()) or 1, sum(lang_src.values()) or 1
    top_all = lang_all.most_common(6)
    top_src = lang_src.most_common(6)
    if f == EN:
        return ("Slope chart of language byte shares over the source repositories under two "
                "conditions. Left, as GitHub's language endpoint reports it: %s. Right, "
                "excluding %s, whose bytes of %s are generated static-site output rather "
                "than authored source: %s. %s falls from rank one to rank three; %s rises "
                "to rank one. Byte counts measure committed source size, not authorship or "
                "effort, and include vendored files. %s Data: GitHub."
                % (", ".join("%s %.1f percent" % (n, v / ta * 100) for n, v in top_all),
                   gen_site, top_all[0][0] if top_all[0][0] == "HTML" else "its dominant language",
                   ", ".join("%s %.1f percent" % (n, v / tsrc * 100) for n, v in top_src),
                   top_all[0][0], top_src[0][0],
                   ("No counted bytes from: " + ", ".join(zero_repos) + ".")
                   if zero_repos else "Every source repo contributes counted bytes."))
    return ("源仓库语言字节占比的斜率图，两种口径。左：GitHub 语言端点原样——%s。右：剔除 %s"
            "（其 %s 字节是静态站构建产物而非手写源码）——%s。%s 从第 1 位跌至第 3 位；%s 升至"
            "第 1 位。字节数度量的是提交源码体积，不是作者归属或工作量，且含 vendored 文件。%s数据：GitHub。"
            % ("，".join("%s %.1f%%" % (n, v / ta * 100) for n, v in top_all),
               gen_site, "HTML" if lang_all.most_common(1)[0][0] == "HTML" else "其主要语言",
               "，".join("%s %.1f%%" % (n, v / tsrc * 100) for n, v in top_src),
               top_all[0][0], top_src[0][0],
               ("无计入字节的仓库：" + "、".join(zero_repos) + "。") if zero_repos
               else "每个源仓库均有计入字节。"))


def upstream_alt(f, items, pub_prs):
    rows = sorted(items, key=lambda it: it["created_at"])
    if f == EN:
        ledger = "; ".join("%s#%d, %s, %s" % (
            it["repository_url"].split("/repos/")[1], it["number"],
            "merged" if it["pull_request"]["merged_at"] else "closed unmerged",
            it["created_at"][:10]) for it in rows)
        return ("Dot ledger of %d public pull requests to repositories owned by others, "
                "%s to %s. %s. These are %.1f percent of %s public pull requests; the rest "
                "are to my own repositories. Data: GitHub is:public search."
                % (len(rows), rows[0]["created_at"][:10], rows[-1]["created_at"][:10],
                   ledger, len(rows) / pub_prs * 100, format(pub_prs, ",")))
    ledger = "；".join("%s#%d，%s，%s" % (
        it["repository_url"].split("/repos/")[1], it["number"],
        "已合并" if it["pull_request"]["merged_at"] else "关闭未合并",
        it["created_at"][:10]) for it in rows)
    return ("提交给他人仓库的公开 PR 点账本，%s 至 %s。%s。它们占 %s 个公开 PR 的 %.1f%%；"
            "其余都提交给我自己的仓库。数据：GitHub is:public 检索。"
            % (rows[0]["created_at"][:10], rows[-1]["created_at"][:10],
               ledger, format(pub_prs, ","), len(rows) / pub_prs * 100))


# ------------------------------------------------- figure derivations ----
peak_cell = max(weekhours, key=lambda k: weekhours[k])
wknd = sum(n for (wd, _), n in weekhours.items() if wd >= 5)
types_sorted = types.most_common()
rel_last = max(
    ((n, r["tag_name"], r["published_at"]) for n, v in rel_lists.items() for r in v),
    key=lambda t: t[2])[:2]
wd_hour = Counter()
we_hour = Counter()
wd_days = we_days = 0
_d = DOMAIN[0]
while _d <= DOMAIN[1]:  # calendar denominators: every day counts, commit or not
    if _d.weekday() >= 5:
        we_days += 1
    else:
        wd_days += 1
    _d += timedelta(days=1)
for (wd, h), n in weekhours.items():
    (we_hour if wd >= 5 else wd_hour)[h] += n
we_peak = max(we_hour, key=lambda h: we_hour[h])
monthly = Counter()
for name, lst in repo_commits.items():
    for c in lst:
        dt = datetime.strptime(c["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc).astimezone(TZ)
        monthly[(name, dt.date().replace(day=1))] += 1
# Graduation events for the accrual figure: pushed_at of the archived repos is
# the closest public proxy (GitHub exposes no archive timestamp); the renderer
# labels the axis "last push", never "archived on".
grad_events = [
    (datetime.strptime(r["pushed_at"], "%Y-%m-%dT%H:%M:%SZ").date(), "graduated")
    for r in repos if r["archived"] and r["name"] in repo_commits
]
spans = [
    (r["name"],
     datetime.strptime(r["created_at"], "%Y-%m-%dT%H:%M:%SZ").date(),
     datetime.strptime(r["pushed_at"], "%Y-%m-%dT%H:%M:%SZ").date(),
     r["archived"])
    for r in repos if r["name"] in repo_commits
]
LAT_EDGES = [1, 2, 5, 15, 60, 240, 1440, float("inf")]
LAT_LABELS = ["<1m", "1-2", "2-5", "5-15", "15-60m", "1-4h", "4-24h", ">24h"]


def bucket_of(m):
    for i, e in enumerate(LAT_EDGES):
        if m <= e:
            return i
    return len(LAT_EDGES) - 1


lat_buckets = [(LAT_LABELS[i], sum(1 for m in lifetimes if bucket_of(m) == i))
               for i in range(len(LAT_LABELS))]


def ecdf_points():
    cum, out = 0, []
    for i, (_, c) in enumerate(lat_buckets):
        cum += c
        out.append(cum / len(lifetimes) * 100)
    return out


lat_stats = {
    "n": neg_pr,
    "unmerged": pr_unmerged,
    "med": human_duration(neg_median),
    "p90": human_duration(p90_lat),
    "med_i": next(i for i, m in enumerate(LAT_EDGES) if neg_median <= m),
    "hour_i": LAT_EDGES.index(60),
    "lat_max": human_duration(lat_max_min),
}


def windowed_run(dom):
    """Longest streak + activity counts INSIDE the rug's rolling window, so the
    figure's bracket and its alt text can never disagree with its own axis."""
    wd_days = [d for d in sorted(day_counts) if dom[0] <= d <= dom[1]]
    best = b_start = b_end = None
    run = 0
    for prev, cur in zip(wd_days, wd_days[1:]):
        run = run + 1 if (cur - prev).days == 1 else 1
        if run > (best or 0):
            best, b_start, b_end = run, cur - timedelta(days=run - 1), cur
    if wd_days and best is None:
        best, b_start, b_end = 1, wd_days[0], wd_days[0]
    return len(wd_days), best, (b_start, b_end)


RUG_DAYS = 400
rug_dom = (DOMAIN[1] - timedelta(days=RUG_DAYS - 1), DOMAIN[1])
rug_act, rug_best_n, rug_run = windowed_run(rug_dom)


# ---------------------------------------------------------------- write ----
asof = now.strftime("%Y-%m-%d")
current_year = years[-1]

# Facts are language-neutral (bare numbers, dates, proper nouns) so one
# derivation serves both READMEs; sentence framing and links live in the
# markdown, per language. A word in any natural language does not belong here —
# see archived_names, where the extension is derived and the interpretation
# ("graduated, not failed") stays hand-written.
facts = {
    "asof": asof,
    "cur_year": current_year,
    "cur_total": f"{values[-1]:,}",
    "commits_total": f"{commits_total:,}",
    "src_repos": src_repos,
    "streak": streak,
    "conv_pct": f"{conv / commits_total * 100:.1f}%",
    "peak_h": f"{max(hours, key=lambda h: hours[h]):02d}:00",
    "peak_n": f"{max(hours.values()):,}",
    "peak_pct": f"{max(hours.values()) / commits_total * 100:.1f}%",
    "peak_x": f"{max(hours.values()) / (commits_total / 24):.2f}×",
    "pub_prs": f"{pub_prs:,}",
    "neg_pr": f"{neg_pr:,}",
    "neg_median": f"{neg_median:.0f}",
    "pct_hour": f"{pct_hour:.0f}%",
    "own_stars": own_stars,
    "acc_stars": acc_stars,
    "total_stars": total_stars,
    "rel_total": rel_total,
    "rel_repos": rel_repos,
    "ext_prs": ext_prs,
    "ext_merged": ext_merged,
    "ext_dify": ext_dify,
    "archived_n": len(archived_names),
    "archived_names": ", ".join(archived_names),
    "ext_first": min(it["created_at"] for it in ext_items)[:10],
    "ext_last": max(it["created_at"] for it in ext_items)[:10],
    "pc_cell": "%s %02d:00" % (("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")[peak_cell[0]], peak_cell[1]),
    "pc_val": weekhours[peak_cell],
    "pc_empty": sum(1 for wd in range(7) for h in range(24) if not weekhours.get((wd, h))),
    "wknd_pct": f"{wknd / commits_total * 100:.1f}%",
    "win_from": str(DOMAIN[0]),
    "win_to": str(DOMAIN[1]),
    "win_days": WIN_DAYS,
    "win_months": round(WIN_DAYS / 30.44),
    "p90": human_duration(p90_lat),
    "lat_max": human_duration(lat_max_min),
    "pr_closed": pr_closed,
    "pr_unmerged": pr_unmerged,
    "top_type": types_sorted[0][0],
    "top_type_pct": f"{types_sorted[0][1] / commits_total * 100:.1f}%",
    "nonconf_pct": f"{(commits_total - conv) / commits_total * 100:.1f}%",
    "nonconf_n": commits_total - conv,
    "lang_top": lang_src.most_common(1)[0][0],
    "lang_top_pct": f"{lang_src.most_common(1)[0][1] / sum(lang_src.values()) * 100:.1f}%",
    "lang_naive": lang_all.most_common(1)[0][0],
    "lang_naive_pct": f"{lang_all.most_common(1)[0][1] / sum(lang_all.values()) * 100:.1f}%",
    "rel_last_name": rel_last[0],
    "rel_last_tag": rel_last[1],
    "streak_from": str(best_start),
    "streak_to": str(best_end),
    "active_days": len(day_counts),
    "active_pct": f"{len(day_counts) / WIN_DAYS * 100:.0f}%",
    "wd_days": wd_days,
    "we_days": we_days,
    "we_peak_h": f"{we_peak:02d}:00",
    "neg_commits": f"{len(repo_commits.get('negentropy', [])):,}",
    "rel_cp": rel_counts.get("coding-proxy", 0),
    "rel_hg": rel_counts.get("hyper-git", 0),
    "rel_gmab": rel_counts.get("give-me-a-break", 0),
}

# Closure between the declared contract and the actual derivation: lint audits
# markers against FACT_KEYS without a network call, so the two must agree.
if set(facts) != set(FACT_KEYS):
    die(f"FACT_KEYS closure broken: declared-not-derived "
        f"{sorted(FACT_KEYS - set(facts))}, derived-not-declared "
        f"{sorted(set(facts) - set(FACT_KEYS))} — refusing")

ground_counts = {k: len(v) for k, v in repo_commits.items()}
sub1pct = [n for n, c in types_sorted if c / commits_total < 0.01]
sub1_txt = ("%d types under one percent each: %s — folded here, not drawn"
            % (len(sub1pct), ", ".join(sub1pct))) if sub1pct else "no types under one percent"
sub1_txt_zh = ("%d 个类型各不足百分之一：%s——折叠于此，不绘制"
               % (len(sub1pct), "、".join(sub1pct))) if sub1pct else "没有不足百分之一的类型"
ALTS = {
    "growth": {f: growth_alt(f, values, years) for f in README_FILES},
    "rhythm": {f: rhythm_alt(f, hours) for f in README_FILES},
    "ground": {f: ground_alt(f, ground_counts, rel_counts, archived_names)
               for f in README_FILES},
    "mark": {f: mark_alt(f) for f in README_FILES},
    "punchcard": {f: punchcard_alt(f, weekhours, DOMAIN, wknd, wd_days, we_days)
                  for f in README_FILES},
    "surplus": {f: surplus_alt(f, wd_hour, we_hour, wd_days, we_days, DOMAIN)
                for f in README_FILES},
    "accrual": {f: accrual_alt(f, monthly, DOMAIN, grad_events, commits_total)
                for f in README_FILES},
    "lifecycles": {f: lifecycles_alt(f, spans, DOMAIN) for f in README_FILES},
    "cadence": {f: cadence_alt(f, rel_lists, DOMAIN) for f in README_FILES},
    "streak": {f: streak_alt(f, rug_act, RUG_DAYS - rug_act, rug_run, rug_dom, RUG_DAYS)
               for f in README_FILES},
    "latency": {f: latency_alt(f, lat_buckets, lat_stats, pct_hour)
                for f in README_FILES},
    "grammar": {f: grammar_alt(f, types_sorted, commits_total - conv, commits_total)
                for f in README_FILES},
    "tongues": {f: tongues_alt(f, lang_all, lang_src, GEN_SITE, zero_byte_repos)
                for f in README_FILES},
    "upstream": {f: upstream_alt(f, ext_items, pub_prs) for f in README_FILES},
}
if set(ALTS) != set(FIG_SPEC):
    die(f"alt text missing for figure(s) {sorted(set(FIG_SPEC) - set(ALTS))} — refusing")

figures = {
    FIG_SPEC["growth"][0]: render_growth(values, years, asof, ALTS["growth"][EN]),
    FIG_SPEC["rhythm"][0]: render_rhythm(hours, asof, ALTS["rhythm"][EN]),
    FIG_SPEC["ground"][0]: render_ground(ground_counts, rel_counts, asof, ALTS["ground"][EN]),
    FIG_SPEC["mark"][0]: render_mark(ALTS["mark"][EN]),
    FIG_SPEC["punchcard"][0]: render_punchcard(weekhours, DOMAIN, asof, ALTS["punchcard"][EN]),
    FIG_SPEC["surplus"][0]: render_surplus(wd_hour, we_hour, wd_days, we_days, DOMAIN, asof,
                                           ALTS["surplus"][EN]),
    FIG_SPEC["accrual"][0]: render_accrual(monthly, grad_events, DOMAIN, asof, ALTS["accrual"][EN]),
    FIG_SPEC["lifecycles"][0]: render_lifecycles(spans, DOMAIN, asof, ALTS["lifecycles"][EN]),
    FIG_SPEC["cadence"][0]: render_cadence(rel_lists, DOMAIN, asof, ALTS["cadence"][EN]),
    FIG_SPEC["streak"][0]: render_streak(day_counts, rug_run, DOMAIN, asof,
                                         ALTS["streak"][EN]),
    FIG_SPEC["latency"][0]: render_latency(lat_buckets, ecdf_points(), lat_stats, asof,
                                           ALTS["latency"][EN]),
    FIG_SPEC["grammar"][0]: render_grammar(types_sorted, commits_total - conv, commits_total,
                                           sub1_txt if EN else sub1_txt_zh, asof,
                                           ALTS["grammar"][EN]),
    FIG_SPEC["tongues"][0]: render_tongues(lang_all, lang_src, GEN_SITE, zero_byte_repos,
                                           asof, ALTS["tongues"][EN]),
    FIG_SPEC["upstream"][0]: render_upstream(ext_items, pub_prs, asof, ALTS["upstream"][EN]),
}

texts = read_readmes()
orders = {f: scan_markers(t, f) for f, t in texts.items()}
audit_parity(orders)
audit_assets()

outputs = {}
for f, text in texts.items():
    # Monotonicity guard, year-flip aware: the annual total can only decrease
    # when the README still refers to the *current* year. In January the
    # headline legitimately resets to a small partial-year number. The README is
    # the pipeline's only state store, which is why this reads the old value
    # back out of the markdown rather than from a cache.
    mc = re.search(r"<!-- DATA:cur_year -->(\d{4})<!-- /DATA:cur_year -->", text)
    if mc and int(mc.group(1)) == current_year:
        m = re.search(r"<!-- DATA:cur_total -->(.*?)<!-- /DATA:cur_total -->", text, re.S)
        if m:
            nums = re.findall(r"\d[\d,]*", m.group(1))
            if nums and int(nums[0].replace(",", "")) > values[-1]:
                die(f"current-year total decreased ({nums[0]} -> {values[-1]}) — "
                    "parse likely broken")
    alts = {k: ALTS[k][f] for k in ALTS}
    once = substitute(text, f, facts, alts)
    if substitute(once, f, facts, alts) != once:
        die(f"{f}: substitution is not idempotent — anchors are being consumed, "
            "the next run would find nothing, refusing")
    if scan_markers(once, f) != orders[f]:
        die(f"{f}: substitution changed the marker sequence — refusing")
    outputs[f] = once

# Validate every rendered figure BEFORE anything is written to disk. Every
# figure's byte count is structurally bounded (fixed cells, fixed lanes, or a
# rolling window), so the flat 8,192 B ceiling stays binding for all of them.
for name, src in figures.items():
    n = assert_svg_sane(src, name)
    print(f"  {name}: {n}B PASS")

if MODE == "check":
    for f, text in outputs.items():
        on_disk = texts[f]
        if text != on_disk:
            diff = "".join(difflib.unified_diff(
                on_disk.splitlines(keepends=True), text.splitlines(keepends=True),
                fromfile=f"{f} (on disk)", tofile=f"{f} (would write)"))
            print(diff, end="")
    for name, src in figures.items():
        p = pathlib.Path("assets") / name
        if p.is_file() and p.read_text(encoding="utf-8") != src:
            print(f"--- a/assets/{name} (on disk)\n+++ b/assets/{name} (would write)")
    print("OK  check: all guards passed, nothing written "
          f"(re-run without --check to write)")
    sys.exit(0)

# All guards passed — write everything.
pathlib.Path("assets").mkdir(exist_ok=True)
for name, src in figures.items():
    with open(pathlib.Path("assets") / name, "w", encoding="utf-8") as fh:
        fh.write(src)
for f, text in outputs.items():
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(text)

print(
    f"OK  growth(latest {values[-1]:,})  rhythm({commits_total:,} commits/{src_repos} repos, "
    f"peak {facts['peak_h']})  ground({rel_total} releases/{rel_repos} repos with releases)  "
    f"pub_prs={pub_prs:,}  ext={ext_prs} merged={ext_merged} dify={ext_dify}  "
    f"own_stars={own_stars}  streak={streak}d  median={neg_median:.0f}min  "
    f"archived={archived_names}"
)
