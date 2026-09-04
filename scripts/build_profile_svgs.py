#!/usr/bin/env python3
"""v4 profile figure generator + DATA refresher for both READMEs.

Caliber rule (structural, do not weaken): every number a visitor could check is
collected at the anonymous / public caliber — the contributions page as a
logged-out visitor sees it, `is:public` search, public REST endpoints. The
GITHUB_TOKEN is used only for API quota, never to widen the caliber.

Private-limited figures (public/private splits) are hand-written in the READMEs
with as-of dates and are never touched here.

Motion rule (see .context/v4-motion-constraints.md): animations are one-shot
entrances only. Default state == final state (`animation … both` with explicit
0%/100% opacity:0 keyframes; base rules carry opacity:0), wrapped in
`@media (prefers-reduced-motion:no-preference)` — static is the default, motion
is the progressive enhancement. No loops, ever.

Stdlib only. On any inconsistency: exit 1 WITHOUT writing anything —
stale-but-true beats fresh-but-wrong.
"""

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
README_FILES = ["README.md", "docs/i18n/zh-CN/README.md"]
ACC_REPO = "analysis_claude_code"
RELEASE_REPOS = ["coding-proxy", "give-me-a-break", "hyper-git", "negentropy"]
MIN_SOURCE_COMMITS = 10  # "source repository" = non-fork repo with >= N commits authored by USER
FIRST_YEAR = 2016
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

print("collecting: releases …")
rel_counts = {r: len(gh(f"repos/{USER}/{r}/releases?per_page=100")) for r in RELEASE_REPOS}
rel_total = sum(rel_counts.values())

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


def render_growth(values, years, asof):
    """Returns (svg, aria). The aria doubles as the README <img> alt text —
    under <img>, the SVG's internal aria-label is ignored and alt is the
    screen-reader channel, so it must refresh with the data."""
    W, H = 700, 168
    L, R, BASE = 42.0, 686.0, 126.0
    SPAN, MIN_BAR, ZH = 88.0, 2.5, 4.0          # plot height / bar floor / zero-slot h
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
                        % (x, ZERO_Y, bw, ZH))
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
    vals_txt = ", ".join(format(v, ",") for v in values)
    dip_txt = (" %d (%s) is lower than %d (%s)." % (years[-4], format(values[-4], ","),
               years[-5], format(values[-5], ","))) if values[-4] < values[-5] else ""
    aria = ("Column chart, contributions per year %d to %d on a square-root "
            "scale: %s. %d and %d are exactly zero, drawn as open slots below the axis."
            "%s Data: GitHub." % (years[0], years[-1], vals_txt,
                                  years[1], years[2] if n > 2 else years[1], dip_txt))
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
    return s, aria


def render_rhythm(hours, asof):
    W, H = 700, 168
    L, R, BASE = 42.0, 686.0, 126.0
    SPAN, MIN_BAR, ZH, ORIGIN = 80.0, 2.5, 4.0, 4
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
            bars.append('<rect class="zero" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>' % (x, ZERO_Y, bw, ZH))
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
    total = sum(hours.values())
    seq = ", ".join(str(hours[h]) for h in order)
    flat = total / 24
    aria = ("Histogram of %s open-source commits by hour of day, Asia/Shanghai, "
            "axis running %02d:00 through %02d:00 so the night block stays contiguous. "
            "Values by hour from %02d:00: %s. %02d:00 to %02d:59 are exactly zero, drawn "
            "as open slots below the axis. Peak %02d:00 with %d commits, %.1f percent of "
            "all commits, %.2f times a flat baseline. Bars below the %.1f-pixel minimum "
            "height are drawn at that minimum." % (format(total, ","), ORIGIN, (ORIGIN + 23) % 24,
            ORIGIN, seq, ORIGIN, ORIGIN + 2, peak_h, peak_v, peak_v / total * 100,
            peak_v / flat, MIN_BAR))
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
    return s, aria


def render_ground(repo_commits, rel, asof):
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
    aria = ("Horizontal bar chart, commits per source repository, sorted: %s. "
            "Total %s commits and %d releases across %d source repositories; %s is %.1f "
            "percent of commits. Releases: %s. negentropy-perceives is archived — it "
            "graduated into the negentropy trunk." % ("; ".join("%s %s" % (n, format(v, ",")) for n, v in rows),
            format(total, ","), rel_total, len(repo_commits), rows[0][0], top_share,
            ", ".join("%s %d" % (n, c) for n, c in sorted(rel.items(), key=lambda kv: -kv[1]))))
    s = "\n".join([
        svg_open(W, H, aria),
        style_sheet(),                              # static figure: no motion rules
        '<rect class="bg" width="%d" height="%d" rx="6"/>' % (W, H),
        head, "\n".join(body), footer,
        '<text x="%.0f" y="212" font-size="9.5" class="lbl te">as of %s</text>' % (686, asof),
        "</svg>", ""])
    return s, aria


def render_mark():
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
    aria = ("Three fish, drawn as a signature mark. In Mandarin the three surpluses of "
            "Dong Yu — winter, night, and rainy days (三余, sān yú) — sound "
            "nearly the same as three fish (三鱼). Hence the handle ThreeFish. "
            "Purely decorative; no data encoded.")
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
    additive-only motion (base opacity:0 + explicit 0%/100% opacity:0), dark
    override strictly after base rules."""
    assert not BANNED.search(src), f"{name}: infinite/indefinite loop found"
    assert 'role="img"' in src and "aria-label" in src, f"{name}: a11y metadata missing"
    n = len(src.encode("utf-8"))
    assert n <= max_bytes, f"{name}: {n}B over budget"
    assert "@import" not in src and 'href="http' not in src, f"{name}: external resource"
    if "animation:" in src:
        assert "prefers-reduced-motion:no-preference" in src, f"{name}: motion not opt-in"
        for kname in KEYFRAME.findall(src):
            body = re.search(r'@keyframes\s+' + kname + r'\s*\{(.*?)\n\s*\}', src, re.S).group(1)
            assert re.search(r'0%\{[^}]*opacity:\s*0', body), f"{name}: {kname} missing 0%{{opacity:0}}"
            assert re.search(r'100%\{[^}]*opacity:\s*0', body), f"{name}: {kname} missing 100%{{opacity:0}}"
        for cls in set(re.findall(r'\.([\w-]+)\{[^}]*animation:', src)):
            base = re.search(r'\.' + cls + r'\{([^}]*)\}', src)
            assert base and "opacity:0" in base.group(1).replace(" ", ""), \
                f"{name}: .{cls} animates but base state is not opacity:0 (additive rule)"
    dark = src.find("prefers-color-scheme:dark")
    for cls in ("bar", "lbl", "val", "acc"):
        i = src.find(".%s{" % cls)
        if i != -1:
            assert i < dark, f"{name}: .{cls} base rule must precede dark override"
    return n


# ---------------------------------------------------------------- write ----
asof = now.strftime("%Y-%m-%d")
current_year = years[-1]

# DATA values are language-neutral (bare numbers / dates) so one refresh serves
# both README files; link and sentence framing live in the markdown itself.
DATA = {
    "c2026": f"{values[-1]:,}",
    "cur_year": current_year,
    "pub_prs": f"{pub_prs:,}",
    "neg_pr": f"{neg_pr:,}",
    "neg_median": f"{neg_median:.0f}",
    "pct_hour": f"{pct_hour:.0f}%",
    "streak": streak,
    "conv_pct": f"{conv / commits_total * 100:.1f}%",
    "commits_total": f"{commits_total:,}",
    "src_repos": src_repos,
    "own_stars": own_stars,
    "acc_stars": acc_stars,
    "rel_total": rel_total,
    "peak_h": f"{max(hours, key=lambda h: hours[h]):02d}:00",
    "peak_x": f"{max(hours.values()) / (commits_total / 24):.2f}×",
    "asof": asof,
}

growth_svg, growth_aria = render_growth(values, years, asof)
rhythm_svg, rhythm_aria = render_rhythm(hours, asof)
ground_svg, ground_aria = render_ground(
    {k: len(v) for k, v in repo_commits.items()}, rel_counts, asof
)
figures = {
    "growth.svg": growth_svg,
    "rhythm.svg": rhythm_svg,
    "ground.svg": ground_svg,
    "mark.svg": render_mark(),
}

# The README <img> alt is the ONLY channel screen readers get (an SVG loaded
# via <img> has its internal aria-label ignored), so alt carries the full data
# series and must refresh with it. HTML comments cannot live inside attributes,
# so the READMEs carry [GROWTH-ALT]-style tokens replaced here per language.
def aria_zh_growth():
    vals = ", ".join(format(v, ",") for v in values)
    dip = ("%d（%s）低于 %d（%s）。" % (years[-4], format(values[-4], ","),
           years[-5], format(values[-5], ","))) if values[-4] < values[-5] else ""
    return ("%d–%d 逐年贡献柱状图，平方根标度：%s。%d 与 %d 为真实零值，"
            "画作基线下方的空槽。%s数据：GitHub。" % (
                years[0], years[-1], vals, years[1],
                years[2] if len(values) > 2 else years[1], dip))

def aria_zh_rhythm():
    order = [(4 + k) % 24 for k in range(24)]
    seq = ", ".join(str(hours[h]) for h in order)
    peak_hh = max(hours, key=lambda h: hours[h])
    peak_v = hours[peak_hh]
    total = sum(hours.values())
    return ("开源提交按小时分布直方图（共 %s 条，Asia/Shanghai，横轴自 04:00 起至 03:00，"
            "使夜间块连续）。自 04:00 起逐小时数值：%s。04:00–06:59 为真实零值"
            "（基线下方空槽）。峰值 %02d:00 共 %d 条——占全部提交 %.1f%%，"
            "为平坦基线的 %.2f 倍。低于最小可见高度的柱按最小高度绘制。" % (
                format(total, ","), seq, peak_hh, peak_v,
                peak_v / total * 100, peak_v / (total / 24)))

def aria_zh_ground(repo_counts, rel):
    rows = sorted(repo_counts.items(), key=lambda kv: -kv[1])
    total = sum(repo_counts.values())
    rel_total = sum(rel.values())
    share = rows[0][1] / total * 100
    listing = "；".join("%s %s" % (n, format(v, ",")) for n, v in rows)
    rels = "、".join("%s %d" % (n, c) for n, c in sorted(rel.items(), key=lambda kv: -kv[1]))
    return ("各源仓库提交量水平条形图（降序）：%s。共 %s 条提交、%d 个 release、"
            "%d 个源仓库；%s 占 %.1f%%。Release 分布：%s。negentropy-perceives 已归档"
            "——毕业并入 negentropy 主干。" % (
                listing, format(total, ","), rel_total, len(repo_counts),
                rows[0][0], share, rels))

ALT_TOKENS = {
    "README.md": {
        "[GROWTH-ALT]": growth_aria,
        "[RHYTHM-ALT]": rhythm_aria,
        "[GROUND-ALT]": ground_aria,
    },
    "docs/i18n/zh-CN/README.md": {
        "[GROWTH-ALT]": aria_zh_growth(),
        "[RHYTHM-ALT]": aria_zh_rhythm(),
        "[GROUND-ALT]": aria_zh_ground({k: len(v) for k, v in repo_commits.items()}, rel_counts),
    },
}

outputs = {}
for f in README_FILES:
    pathlib.Path(f).read_text(encoding="utf-8")  # existence probe
    with open(f, encoding="utf-8") as fh:
        text = fh.read()
    # Monotonicity guard, year-flip aware: the annual total can only decrease
    # when the README still refers to the *current* year. In January the
    # headline legitimately resets to a small partial-year number.
    mc = re.search(r"<!-- DATA:cur_year -->(\d{4})<!-- /DATA:cur_year -->", text)
    if mc and int(mc.group(1)) == current_year:
        m = re.search(r"<!-- DATA:c2026 -->(.*?)<!-- /DATA:c2026 -->", text, re.S)
        if m:
            nums = re.findall(r"\d[\d,]*", m.group(1))
            if nums and int(nums[0].replace(",", "")) > values[-1]:
                die(
                    f"current-year total decreased ({nums[0]} -> {values[-1]}) — "
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
    for token, alt in ALT_TOKENS[f].items():
        if token not in text:
            die(f"{f}: alt token {token} not found")
        text = text.replace(token, html.escape(alt, quote=True))
    outputs[f] = text

# Validate every rendered figure BEFORE anything is written to disk.
for name, src in figures.items():
    n = assert_svg_sane(src, name)
    print(f"  {name}: {n}B PASS")

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
    f"peak {DATA['peak_h']})  ground({rel_total} releases)  pub_prs={pub_prs:,}  "
    f"ext={ext_prs}  own_stars={own_stars}  streak={streak}d  median={neg_median:.0f}min"
)
