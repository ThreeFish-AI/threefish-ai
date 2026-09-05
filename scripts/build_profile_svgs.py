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
    "ext_prs", "ext_merged", "ext_dify",
    "archived_n", "archived_names",
})

# Figure key -> (filename, rendered width). Also the assets-closure contract:
# an SVG in assets/ that this script did not render aborts the run, so the
# workflow can safely `git add -A assets`.
FIG_SPEC = {
    "mark": ("mark.svg", 256),
    "growth": ("growth.svg", 700),
    "rhythm": ("rhythm.svg", 700),
    "ground": ("ground.svg", 700),
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
days = set()
conv = 0
for c in all_commits:
    a = c["commit"]["author"]
    dt = datetime.strptime(a["date"], "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    ).astimezone(TZ)
    hours[dt.hour] += 1
    days.add(dt.date())
    if CONVENTIONAL.match(c["commit"]["message"].split("\n")[0]):
        conv += 1

sorted_days = sorted(days)
streak = best = 1
for prev, cur in zip(sorted_days, sorted_days[1:]):
    streak = streak + 1 if (cur - prev).days == 1 else 1
    best = max(best, streak)
streak = best

zero_hours = [h for h in range(24) if hours[h] == 0]

# Pipeline-closure guard: every authored commit must land in exactly one hour
# bucket. A mismatch means the hour histogram and the repository table below
# would silently disagree with each other.
if sum(hours.values()) != commits_total:
    die(
        f"hour histogram {sum(hours.values())} != repo total {commits_total} — "
        "caliber split, refusing"
    )

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
                "sweep", "fi", "eye", "rip"):
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
}

# Closure between the declared contract and the actual derivation: lint audits
# markers against FACT_KEYS without a network call, so the two must agree.
if set(facts) != set(FACT_KEYS):
    die(f"FACT_KEYS closure broken: declared-not-derived "
        f"{sorted(FACT_KEYS - set(facts))}, derived-not-declared "
        f"{sorted(set(facts) - set(FACT_KEYS))} — refusing")

ground_counts = {k: len(v) for k, v in repo_commits.items()}
ALTS = {
    "growth": {f: growth_alt(f, values, years) for f in README_FILES},
    "rhythm": {f: rhythm_alt(f, hours) for f in README_FILES},
    "ground": {f: ground_alt(f, ground_counts, rel_counts, archived_names)
               for f in README_FILES},
    "mark": {f: mark_alt(f) for f in README_FILES},
}
if set(ALTS) != set(FIG_SPEC):
    die(f"alt text missing for figure(s) {sorted(set(FIG_SPEC) - set(ALTS))} — refusing")

figures = {
    FIG_SPEC["growth"][0]: render_growth(values, years, asof, ALTS["growth"][EN]),
    FIG_SPEC["rhythm"][0]: render_rhythm(hours, asof, ALTS["rhythm"][EN]),
    FIG_SPEC["ground"][0]: render_ground(ground_counts, rel_counts, asof, ALTS["ground"][EN]),
    FIG_SPEC["mark"][0]: render_mark(ALTS["mark"][EN]),
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

# Validate every rendered figure BEFORE anything is written to disk.
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
