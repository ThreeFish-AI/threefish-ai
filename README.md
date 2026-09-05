<div align="center">

<!-- FIG:mark --><img src="assets/mark.svg" width="256" alt="Three fish, drawn as a signature mark. In Mandarin the three surpluses of Dong Yu — winter, night, and rainy days (三余, sān yú) — sound nearly the same as three fish (三鱼). Hence the handle ThreeFish. Purely decorative; no data encoded." /><!-- /FIG:mark -->

### Aurelius Huang · 阿浩

**Entropy reduction — of codebases, and of days.**

<sub>Agentic AI infrastructure at production scale, by day · [English](./README.md) · [简体中文](./docs/i18n/zh-CN/README.md) · [Notes](https://threefish-ai.github.io)</sub>

</div>

> 冬者岁之余，夜者日之余，阴雨者时之余。
>
> <sub>— Dong Yu (董遇), 3rd c.[^weilue] The surplus is already there; almost everyone lets it evaporate. [negentropy](https://github.com/ThreeFish-AI/negentropy) takes its name from Schrödinger's negative entropy.[^schrodinger]</sub>

---

<!-- FIG:growth --><img src="assets/growth.svg" width="700" alt="Column chart, contributions per year 2016 to 2026 on a square-root scale: 1, 0, 0, 13, 129, 198, 676, 589, 1,181, 3,193, 9,311. 2017 and 2018 are exactly zero, drawn as open slots below the axis. 2023 (589) is lower than 2022 (676). Data: GitHub." /><!-- /FIG:growth -->

<sub>Eleven years, square-root scale. **<!-- DATA:cur_total -->9,311<!-- /DATA:cur_total --> in <!-- DATA:cur_year -->2026<!-- /DATA:cur_year -->** — after two years that are genuinely zero and one year that is genuinely down.</sub>

<!-- FIG:rhythm --><img src="assets/rhythm.svg" width="700" alt="Histogram of 4,349 open-source commits by hour of day, Asia/Shanghai, axis running 04:00 through 03:00 so the night block stays contiguous. Values by hour from 04:00: 0, 0, 0, 11, 44, 232, 338, 319, 186, 184, 265, 285, 262, 292, 242, 206, 214, 348, 460, 329, 91, 36, 3, 2. 04:00 to 06:59 are exactly zero, drawn as open slots below the axis. Peak 22:00 with 460 commits, 10.6 percent of all commits, 2.54 times a flat baseline. Bars below the 2.5-pixel minimum height are drawn at that minimum." /><!-- /FIG:rhythm -->

<sub>The surplus, located: **<!-- DATA:peak_h -->22:00<!-- /DATA:peak_h -->**, <!-- DATA:peak_x -->2.54×<!-- /DATA:peak_x --> a flat baseline — <!-- DATA:commits_total -->4,349<!-- /DATA:commits_total --> open-source commits, Asia/Shanghai. Dawn is empty, not missing.</sub>

<!-- FIG:punchcard --><img src="assets/punchcard.svg" width="700" alt="Punchcard of 4,349 open-source commits by weekday and hour, Asia/Shanghai, columns running 04:00 to 03:00 and rows Monday to Sunday, window 2024-06-22 to 2026-09-01. Cell area is proportional to count; cell side rounded to one decimal. Weekday totals Monday to Sunday: 615, 557, 563, 504, 602, 780, 728. Densest cell Sunday at 22:00 with 83 commits. 37 of 168 cells are exactly zero, drawn as open squares. Weekends hold 1,508 commits = 34.7 percent, against a flat share of 28.6. Data: GitHub." /><!-- /FIG:punchcard -->

<sub>The two-dimensional answer: densest cell **<!-- DATA:pc_cell -->Sun 22:00<!-- /DATA:pc_cell -->**, <!-- DATA:pc_val -->83<!-- /DATA:pc_val --> commits; <!-- DATA:pc_empty -->37<!-- /DATA:pc_empty --> of 168 cells are true zeros; weekends hold <!-- DATA:wknd_pct -->34.7%<!-- /DATA:wknd_pct --> against a 28.6% flat share.</sub>

<!-- FIG:surplus --><img src="assets/surplus.svg" width="700" alt="Two step curves on one hour-of-day axis running 04:00 to 03:00, Asia/Shanghai, 2024-06-22 to 2026-09-01, normalised to commits per day of that kind so 572 weekdays and 230 weekend days are comparable. Weekday rate by hour from 04:00: 0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 0.5, 0.4, 0.2, 0.2, 0.3, 0.3, 0.3, 0.3, 0.2, 0.2, 0.2, 0.4, 0.5, 0.4, 0.1, 0.0, 0.0, 0.0. Weekend rate: 0.0, 0.0, 0.0, 0.0, 0.1, 0.2, 0.2, 0.3, 0.3, 0.4, 0.4, 0.4, 0.4, 0.5, 0.5, 0.4, 0.5, 0.6, 0.7, 0.5, 0.2, 0.1, 0.0, 0.0. Weekday peak 22:00 at 0.5 per day; weekend peak 22:00 at 0.7. Data: GitHub." /><!-- /FIG:surplus -->

<sub>Weekday vs weekend, normalised to per-day rates (**<!-- DATA:wd_days -->572<!-- /DATA:wd_days --> weekdays ÷ <!-- DATA:we_days -->230<!-- /DATA:we_days --> weekend days**): same shape, and the weekend actually runs hotter per day — peak at <!-- DATA:we_peak_h -->22:00<!-- /DATA:we_peak_h -->. "By day" is a job description, not a schedule.</sub>

<!-- FIG:ground --><img src="assets/ground.svg" width="700" alt="Horizontal bar chart, commits per source repository, sorted: negentropy 2,048; agentic-ai-cognizes 945; coding-proxy 638; negentropy-perceives 433; hyper-git 125; threefish-ai.github.io 117; give-me-a-break 43. Total 4,349 commits and 29 releases across 7 source repositories; negentropy is 47.1 percent of commits. Releases: coding-proxy 12, give-me-a-break 7, hyper-git 7, negentropy 2, negentropy-perceives 1. agentic-ai-cognizes and negentropy-perceives are archived — they graduated into the negentropy trunk." /><!-- /FIG:ground -->

<sub>[negentropy](https://github.com/ThreeFish-AI/negentropy) knowledge engine · [coding-proxy](https://github.com/ThreeFish-AI/coding-proxy) failover for coding agents · [hyper-git](https://github.com/ThreeFish-AI/hyper-git) changelists for VS Code · [agents.md](https://github.com/ThreeFish-AI/agents.md) the doctrine they are written under</sub>

<!-- FIG:accrual --><img src="assets/accrual.svg" width="700" alt="Cumulative authored commits per source repository at monthly resolution, 2024-06-22 to 2026-09-01 — a window of about 26 months, not the eleven years shown above. Final totals: agentic-ai-cognizes 945, coding-proxy 638, give-me-a-break 43, hyper-git 125, negentropy 2,048, negentropy-perceives 433, threefish-ai.github.io 117; all repos together 4,349. on 2026-05-18 both archived repos flatten and the trunk keeps rising: both graduated into the negentropy trunk that day. Data: GitHub." /><!-- /FIG:accrual -->

<sub>Cumulative, monthly: two curves flatten on the day they graduated into the trunk, which keeps climbing. Window <!-- DATA:win_from -->2024-06-22<!-- /DATA:win_from --> → <!-- DATA:win_to -->2026-09-01<!-- /DATA:win_to --> — **<!-- DATA:win_months -->26<!-- /DATA:win_months --> months, not the eleven years above.**</sub>

<!-- FIG:lifecycles --><img src="assets/lifecycles.svg" width="700" alt="Timeline ribbon, one row per source repository from creation to last push, 2024-06-22 to 2026-09-01. agentic-ai-cognizes created 2025-10-22, last push 2026-05-18, archived (graduated); coding-proxy created 2026-03-30, last push 2026-08-27, active; give-me-a-break created 2026-06-23, last push 2026-09-04, active; hyper-git created 2026-06-27, last push 2026-09-01, active; negentropy created 2026-01-31, last push 2026-09-04, active; negentropy-perceives created 2025-08-26, last push 2026-05-18, archived (graduated); threefish-ai.github.io created 2024-06-22, last push 2026-07-08, active. Bar ends mark last push — the closest public proxy for archival, because GitHub exposes no archive timestamp; archived-ness rides the square terminal glyph instead. Repositories deleted before today are invisible at public caliber. Data: GitHub." /><!-- /FIG:lifecycles -->

<sub>Repositories as intervals, creation to last push; the two same-day endings are the graduation. Deleted repos are invisible at this caliber.</sub>

<!-- FIG:cadence --><img src="assets/cadence.svg" width="700" alt="Dot timeline of 29 public releases across 5 repositories on one shared date axis, 2024-06-22 to 2026-09-01. coding-proxy: 12 releases, v0.1.1 on 2026-04-05 through v0.5.2a8 on 2026-07-06; give-me-a-break: 7 releases, v0.1.0 on 2026-06-27 through v0.1.6 on 2026-09-04; hyper-git: 7 releases, v0.0.6 on 2026-06-30 through v0.0.16 on 2026-09-01; negentropy: 2 releases, negentropy-v0.0.1-rc.1 on 2026-06-19 through negentropy-v0.0.1-rc.2 on 2026-06-19, all pre-releases; negentropy-perceives: 1 releases, v0.2.0a3 on 2026-04-20 through v0.2.0a3 on 2026-04-20. Hollow dots are pre-releases. negentropy shows only its two release candidates against 2,048 commits because it is a deployed service, not a distributed package — its shipping unit is the merged pull request, not the tag. Data: GitHub." /><!-- /FIG:cadence -->

<sub>Releases have timing, not just counts — latest: **<!-- DATA:rel_last_name -->give-me-a-break<!-- /DATA:rel_last_name --> <!-- DATA:rel_last_tag -->v0.1.6<!-- /DATA:rel_last_tag -->**. negentropy ships as merged PRs, not tags.</sub>

<!-- FIG:streak --><img src="assets/streak.svg" width="700" alt="Rug plot, one tick per day over the latest 400 days, 2025-07-29 to 2026-09-01; tick height is the square root of that day&#x27;s authored-commit count. 208 days carry at least one commit (52 percent); the 192 empty ones are drawn as a thin rule below the axis, one segment per gap. The longest unbroken run inside this window is 88 days, 2026-03-19 to 2026-06-14, marked with a bracket. Counted over authored commits in source repositories — the same population as every other commit figure here, and narrower than the GitHub contributions calendar, which also counts private work, issues and reviews. Data: GitHub." /><!-- /FIG:streak -->

<sub>The run, located: **<!-- DATA:streak -->88<!-- /DATA:streak --> days, <!-- DATA:streak_from -->2026-03-19<!-- /DATA:streak_from --> → <!-- DATA:streak_to -->2026-06-14<!-- /DATA:streak_to -->**, bracketed. The rug plots the latest 400 days; of the <!-- DATA:win_days -->802<!-- /DATA:win_days --> days in the whole window, <!-- DATA:active_days -->249<!-- /DATA:active_days --> carried a commit (<!-- DATA:active_pct -->31%<!-- /DATA:active_pct -->) — authored commits in source repos, a narrower population than the GitHub calendar above.</sub>

---

<!-- FIG:latency --><img src="assets/latency.svg" width="700" alt="Histogram of merged pull-request lifetime in negentropy with a step cumulative curve on a right-hand zero-to-hundred-percent axis. 1078 merged pull requests, log-spaced buckets: &lt;1m 281, 1-2 72, 2-5 144, 5-15 225, 15-60m 177, 1-4h 92, 4-24h 83, &gt;24h 4. Median 6 min; 90th percentile 2.8 h; 83 percent merge within an hour; the longest waited 11.9 d. 40 further closed pull requests were never merged and are excluded. This is a solo self-merge repository: the lifetime measures how small a change unit is, not how fast a review is. Data: GitHub." /><!-- /FIG:latency -->

<sub>What the median hides: p90 **<!-- DATA:p90 -->2.8 h<!-- /DATA:p90 -->**, longest **<!-- DATA:lat_max -->11.9 d<!-- /DATA:lat_max -->**; of <!-- DATA:pr_closed -->1118<!-- /DATA:pr_closed --> closed, <!-- DATA:pr_unmerged -->40<!-- /DATA:pr_unmerged --> were never merged and are excluded. Solo self-merge: this measures change-unit size, not review speed.</sub>

<!-- FIG:grammar --><img src="assets/grammar.svg" width="700" alt="Waffle chart of one hundred cells, each cell one percent of 4,349 authored commit subjects classified by Conventional Commits prefix. fix 827, docs 725, feat 697, refactor 319, chore 255, style 176, test 144, ci 110, build 92, perf 6, revert 2. 996 subjects do not parse as Conventional Commits and are drawn as open cells. The accented block is fix, the largest type at 19.0 percent of all subjects. Data: GitHub." /><!-- /FIG:grammar -->

<sub>Seventy-seven of a hundred, made countable: **<!-- DATA:top_type -->fix<!-- /DATA:top_type --> <!-- DATA:top_type_pct -->19.0%<!-- /DATA:top_type_pct -->** leads; **<!-- DATA:nonconf_n -->996<!-- /DATA:nonconf_n --> subjects (<!-- DATA:nonconf_pct -->22.9%<!-- /DATA:nonconf_pct -->) don't parse** — drawn as open cells, not hidden.</sub>

<!-- FIG:tongues --><img src="assets/tongues.svg" width="700" alt="Slope chart of language byte shares over the source repositories under two conditions. Left, as GitHub&#x27;s language endpoint reports it: HTML 67.8 percent, Python 22.7 percent, TypeScript 8.3 percent, Swift 0.5 percent, CSS 0.2 percent, C# 0.2 percent. Right, excluding threefish-ai.github.io, whose bytes of HTML are generated static-site output rather than authored source: Python 69.1 percent, TypeScript 25.2 percent, HTML 2.3 percent, Swift 1.4 percent, C# 0.6 percent, CSS 0.5 percent. HTML falls from rank one to rank three; Python rises to rank one. Byte counts measure committed source size, not authorship or effort, and include vendored files. Every source repo contributes counted bytes. Data: GitHub." /><!-- /FIG:tongues -->

<sub>Both conditions, not a silent pick: GitHub's endpoint says **<!-- DATA:lang_naive -->HTML<!-- /DATA:lang_naive --> <!-- DATA:lang_naive_pct -->67.8%<!-- /DATA:lang_naive_pct -->**; excluding the one generated-site repo, **<!-- DATA:lang_top -->Python<!-- /DATA:lang_top --> <!-- DATA:lang_top_pct -->69.1%<!-- /DATA:lang_top_pct -->**. Bytes measure source size, not effort or authorship.</sub>

<!-- FIG:upstream --><img src="assets/upstream.svg" width="700" alt="Dot ledger of 6 public pull requests to repositories owned by others, 2024-06-26 to 2025-12-06. langgenius/dify#5631, merged, 2024-06-26; langgenius/dify#8921, merged, 2024-09-30; langgenius/dify-plugin-daemon#389, closed unmerged, 2025-07-07; langgenius/dify-cloud-kit#3, merged, 2025-07-08; langgenius/dify#22646, merged, 2025-07-18; DayuanJiang/next-ai-draw-io#124, merged, 2025-12-06. These are 0.3 percent of 1,849 public pull requests; the rest are to my own repositories. Data: GitHub is:public search." /><!-- /FIG:upstream -->

<sub>N = <!-- DATA:ext_prs -->6<!-- /DATA:ext_prs -->, named: <!-- DATA:ext_first -->2024-06-26<!-- /DATA:ext_first --> → <!-- DATA:ext_last -->2025-12-06<!-- /DATA:ext_last -->, <!-- DATA:ext_merged -->5<!-- /DATA:ext_merged --> merged, one closed unmerged — a fraction of a percent of all public PRs. The ratio is the point.</sub>

---

<div align="center"><sub><!-- DATA:pub_prs -->1,849<!-- /DATA:pub_prs --> public pull requests ·
<!-- DATA:neg_pr -->1,078<!-- /DATA:neg_pr --> merged in negentropy, median <!-- DATA:neg_median -->6<!-- /DATA:neg_median --> min, <!-- DATA:pct_hour -->83%<!-- /DATA:pct_hour --> within an hour ·
<!-- DATA:streak -->88<!-- /DATA:streak -->-day streak ·
<!-- DATA:conv_pct -->77.1%<!-- /DATA:conv_pct --> Conventional Commits ·
<!-- DATA:rel_total -->29<!-- /DATA:rel_total --> releases ·
<!-- DATA:src_repos -->7<!-- /DATA:src_repos --> source repos,
<!-- DATA:own_stars -->51<!-- /DATA:own_stars --> stars actually mine ·
<!-- DATA:ext_merged -->5<!-- /DATA:ext_merged --> of <!-- DATA:ext_prs -->6<!-- /DATA:ext_prs --> upstream PRs merged — <!-- DATA:ext_dify -->4<!-- /DATA:ext_dify --> in the [Dify](https://github.com/langgenius/dify) ecosystem, one outside it</sub></div>

<details>
<summary><b>Honesty notes</b></summary>

- The headline count splits 5,590 public and clickable / 3,640 private work (as of 2026-09). Private work counts, but doesn't link — so it gets no headline.
- `negentropy` is a solo, self-merge repo: the PR is a titled, revertible unit of change, not a review gate. That is what the 6-minute median measures.
- [analysis_claude_code](https://github.com/ThreeFish-AI/analysis_claude_code) (<!-- DATA:acc_stars -->312<!-- /DATA:acc_stars --> stars) is mostly **not** my work — it mirrors [CrazyBoyM](https://github.com/CrazyBoyM) / ShareAI-Lab's Claude Code source analysis; the foundational commits are theirs. Mine in it: the reading notes.
- <!-- DATA:archived_names -->agentic-ai-cognizes, negentropy-perceives<!-- /DATA:archived_names --> (<!-- DATA:archived_n -->2<!-- /DATA:archived_n --> source repos, 1,378 commits between them) are archived — they graduated into the negentropy trunk, perceives as its extraction service and cognizes as `apps/cognizes`. Intended lifecycle, not failure. Frozen by definition: archives don't move.
- The sixth upstream PR was closed unmerged — same class of bug as the one above it, fixed upstream by a different route. Six against <!-- DATA:pub_prs -->1,849<!-- /DATA:pub_prs --> public PRs: almost all of my public work happens in repos where I am also the reviewer.
- The yearly figure uses a square-root scale so early years stay visible; it understates recent growth. All figures are regenerated monthly from the GitHub API by [one workflow](https://github.com/ThreeFish-AI/threefish-ai/blob/master/.github/workflows/refresh-profile-data.yml) — as of <!-- DATA:asof -->2026-09-05<!-- /DATA:asof -->.

</details>

---

[^weilue]: Yu Huan, *Weilüe* (魏略), “Biographies of Confucian Scholars”; survives via Pei Songzhi's annotation to Chen Shou, *Records of the Three Kingdoms* (三国志), *Biography of Wang Lang*, 3rd c. CE.

[^schrodinger]: E. Schrödinger, *What Is Life? The Physical Aspect of the Living Cell*. Cambridge, U.K.: Cambridge University Press, 1944.

<div align="center"><sub>[Notes](https://threefish-ai.github.io) · [CSDN](https://threefish.blog.csdn.net/) · [@ThreeFish-AI](https://github.com/ThreeFish-AI)</sub></div>
