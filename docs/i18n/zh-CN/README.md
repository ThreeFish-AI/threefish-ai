<div align="center">
  <img src="https://raw.githubusercontent.com/ThreeFish-AI/threefish-ai/master/assets/wave-top.svg" width="100%" alt="" />
</div>

[English](../../../README.md) | [简体中文](./README.md)

<h1 align="center">Aurelius Huang · 阿浩 🐟</h1>

<p align="center"><strong>代码库放任不管会滑向噪声，无人认领的时间会滑向浪费。<br/>同一种失效模式，两个尺度——我两样都做。</strong></p>

<p align="center"><sub>白天做生产级 Agent 基础设施 · 熵减是一门工程纪律，不是一个项目名</sub></p>

<p align="center">
  <a href="https://github.com/ThreeFish-AI/negentropy"><img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" /></a>
  <a href="https://github.com/ThreeFish-AI/hyper-git"><img src="https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript" /></a>
  <a href="https://threefish-ai.github.io"><img src="https://img.shields.io/badge/Notes-threefish-0969DA?style=flat-square&logo=googlechrome&logoColor=white" alt="Notes" /></a>
</p>

> 冬者岁之余，夜者日之余，阴雨者时之余。
>
> <sub>——董遇，三世纪，一个在职之人如何找到读书时间。[^weilue]「三余」（sān yú）与「三鱼」近音——这个 ID 的来历。</sub>

---

## 在做什么

四件工具，各自对准一种熵：

**[negentropy](https://github.com/ThreeFish-AI/negentropy)** —— 个人知识引擎：一个共享内核之上长出六个应用，每一翼都针对信息衰变的一种具体方式——过载、遗忘、浅薄、空谈、晦涩。
<sub>凭据：<!-- DATA:neg_pr -->[1,078 merged pull requests](https://github.com/ThreeFish-AI/negentropy/pulls?q=is%3Apr+is%3Amerged)<!-- /DATA:neg_pr --> · <!-- DATA:neg_commits -->2,048<!-- /DATA:neg_commits --> commits · [CI workflows](https://github.com/ThreeFish-AI/negentropy/actions)</sub>

**[coding-proxy](https://github.com/ThreeFish-AI/coding-proxy)** —— 面向编码 Agent 的多供应商代理。当供应商回以 `429`、`403` 或 `503`，它负责故障转移，而不是把失败抛给你。
<sub>凭据：[12 releases](https://github.com/ThreeFish-AI/coding-proxy/releases) · 最新 `v0.5.2a8` · Python</sub>

**[hyper-git](https://github.com/ThreeFish-AI/hyper-git)** —— 把 IntelliJ 的 changelist 模型重建到 VS Code：多变更列表暂存、手绘提交图、行级提交。
<sub>凭据：[7 releases](https://github.com/ThreeFish-AI/hyper-git/releases) · 最新 `v0.0.16` · 6 视图 · 102 命令 · 403 单元测试</sub>

**[agents.md](https://github.com/ThreeFish-AI/agents.md)** —— 上面三件工具共同遵循的规约：道·心法，法·战略，术·战术。以符号链接接入我工作的每台机器，改它，就是改所有工具的行为。不是宣言——是一个恰好有观点的配置文件。

> **注** —— 这张地图变过一次形状。[negentropy-perceives](https://github.com/ThreeFish-AI/negentropy-perceives) 起初是独立的感知引擎（158 个 merged PR）。现在已归档——因为它毕业并入了主干，活在 [`apps/negentropy-perceives`](https://github.com/ThreeFish-AI/negentropy/tree/master/apps)。这是预期的生命周期，不是失败。

---

## 凭据（Receipts）

以下每个数字，你都可以匿名、一键、亲自核实——或者我明确告诉你它为什么核实不了。

- **<!-- DATA:c2026 -->[9,306 contributions in 2026](https://github.com/ThreeFish-AI?tab=overview&from=2026-01-01&to=2026-12-31)<!-- /DATA:c2026 -->** —— 而我回归 GitHub 的 2020 年是 129 次。API 口径的 9,230 里：**5,590 条公开可点击；3,640 条是私有工作——计入计数，但不提供链接**（2026-09 核实）。十一年全部画在下面，包括空档。
- **<!-- DATA:pub_prs -->[1,849 public pull requests](https://github.com/search?q=is%3Apr+author%3AThreeFish-AI+is%3Apublic&type=pullrequests)<!-- /DATA:pub_prs -->** —— 几乎都在我自己的仓库：即使无人旁观，每个变更也走 PR。`negentropy` 开出到合并的中位时长：**<!-- DATA:neg_median -->6<!-- /DATA:neg_median --> 分钟**，<!-- DATA:pct_hour -->83%<!-- /DATA:pct_hour --> 一小时内合并。单人仓库、自合并工作流——PR 是有标题、可回滚的原子变更单元，不是评审门禁。
- **<!-- DATA:rel_total -->[28 releases](https://github.com/ThreeFish-AI?tab=repositories&type=source)<!-- /DATA:rel_total -->，分布于 <!-- DATA:rel_repos -->4<!-- /DATA:rel_repos --> 个仓库** —— coding-proxy <!-- DATA:rel_cp -->12<!-- /DATA:rel_cp -->、give-me-a-break <!-- DATA:rel_gmab -->7<!-- /DATA:rel_gmab -->、hyper-git <!-- DATA:rel_hg -->7<!-- /DATA:rel_hg -->、negentropy <!-- DATA:rel_neg -->2<!-- /DATA:rel_neg -->。是持续发布，不只是持续提交。
- **<!-- DATA:src_repos -->7<!-- /DATA:src_repos --> 个源仓库，<!-- DATA:own_stars -->51<!-- /DATA:own_stars --> 颗真正属于我的星。** 不是主页侧栏显示的那个总数——见文末说明。
- **六个上游 PR，五个已合并** —— [Dify](https://github.com/langgenius/dify) 生态里的 [Notion 行内容提取](https://github.com/langgenius/dify/pull/22646)、[Postgres 全文检索转义修复](https://github.com/langgenius/dify/pull/8921)、[Notion 同步截断修复](https://github.com/langgenius/dify/pull/5631)、[GCS 双写修复](https://github.com/langgenius/dify-cloud-kit/pull/3)，以及 [一个缺失的 OTLP 依赖](https://github.com/DayuanJiang/next-ai-draw-io/pull/124)；[第六个](https://github.com/langgenius/dify-plugin-daemon/pull/389)仍在 open。

> **我没有计入的数字。** 我的 GitHub 上还有约 2,500 个 PR 与 641 次代码评审在私有仓库里（截至 2026-09）。它们是真的，但你打不开，所以不配上标题。能点开的小数字，胜过打不开的大数字。

<p align="center">
  <img src="https://raw.githubusercontent.com/ThreeFish-AI/threefish-ai/master/assets/contribution-arc.svg" width="100%"
       alt="2016 至 2026 逐年贡献折线图：2020 年前近乎平直，此后逐年陡升，2023 年有一次清晰回落。逐年精确数值标注在图上。" />
</p>

<p align="center"><sub>每一年都在图上，等距横轴、平方根纵轴让早期年份保持可见。是的，2023 低于 2022——<a href="https://github.com/ThreeFish-AI?tab=overview&from=2023-01-01&to=2023-12-31">你自己看</a>。由<a href="https://github.com/ThreeFish-AI/threefish-ai/blob/master/.github/workflows/refresh-profile-data.yml">一个 workflow</a> 每月刷新。</sub></p>

---

## 为什么叫 "ThreeFish"

董遇的回答不是「挤出时间」，而是：余暇本来就在那里，只是几乎所有人都任其蒸发。我把同样的直觉上移一层，作为工程纪律来执行：**熵减**。信息系统放任不管会滑向噪声，和无人认领的时间滑向浪费是同一件事。[negentropy](https://github.com/ThreeFish-AI/negentropy) 的名字直接取自薛定谔的负熵[^schrodinger]——秩序不是一个你能抵达的状态，而是需要持续输入的东西。

这个治学习惯在提交时间戳里长这样：

<p align="center">
  <img src="https://raw.githubusercontent.com/ThreeFish-AI/threefish-ai/master/assets/commit-clock.svg" width="100%"
       alt="按小时分布的提交柱状图（Asia/Shanghai 时区，开源仓库）：晚间最高、深夜达峰、黎明前有一段真实的空档。精确计数见图内标注。" />
</p>

<p align="center"><sub><b><!-- DATA:peak_h -->22:00<!-- /DATA:peak_h --> 是全天最忙的小时——<!-- DATA:peak_n -->460<!-- /DATA:peak_n --> 条提交，<!-- DATA:peak_x -->2.54×<!-- /DATA:peak_x --> 于平坦基线。黎明前的空档是真实的零，不是缺数据。</b><br/>仅计开源提交，<!-- DATA:src_repos -->7<!-- /DATA:src_repos --> 个源仓库，Asia/Shanghai 时区 · 周末占 <!-- DATA:weekend_pct -->34.7%<!-- /DATA:weekend_pct -->——夜晚是余暇，不是熬夜债。</sub></p>

**工作方式** —— 单人仓库，按团队标准治理：

- 每个变更都走 PR，哪怕只有我一个人。<!-- DATA:commits_total -->4,349<!-- /DATA:commits_total --> 条提交中 <!-- DATA:conv_pct -->77.1%<!-- /DATA:conv_pct --> 遵循 Conventional Commits，其中 <!-- DATA:scoped_pct -->98.4%<!-- /DATA:scoped_pct --> 带 scope。类型分布：`fix` <!-- DATA:mix_fix -->24.7%<!-- /DATA:mix_fix --> · **`docs` <!-- DATA:mix_docs -->21.6%<!-- /DATA:mix_docs -->** · `feat` <!-- DATA:mix_feat -->20.8%<!-- /DATA:mix_feat -->——文档提交几乎追平功能提交；这个比例就是这套哲学浓缩成的一个数字。
- 最长连续公开提交：**<!-- DATA:streak -->88<!-- /DATA:streak --> 天**；过去 365 天中 <!-- DATA:active_days -->338<!-- /DATA:active_days --> 天有提交。

<sub>任一数字皆可复算：<code>for r in $(gh api users/ThreeFish-AI/repos --paginate --jq '.[]|select(.fork==false)|.name'); do gh api "/repos/ThreeFish-AI/$r/commits?author=ThreeFish-AI" --paginate --jq '.[].commit.message|split("\n")[0]'; done</code></sub>

---

<details>
<summary><b>关于我主页上星标最多的那个仓库</b></summary>

<br/>

[analysis_claude_code](https://github.com/ThreeFish-AI/analysis_claude_code) 目前 <!-- DATA:acc_stars -->312<!-- /DATA:acc_stars --> 星、112 fork。**其中的逆向工程语料不是我的作品。**它镜像自 [CrazyBoyM](https://github.com/CrazyBoyM) / ShareAI-Lab 对 Claude Code 混淆源码的分析——全部奠基提交（2025 年 6–7 月，早于该仓库出现在我账号下）都出自原作者，该 README 里也有他们的署名。仓库并非经 fork 创建，GitHub 不会显示归属横幅——所以我写在这里。

属于我的部分：研读——一份 Claude Code SDK 研究笔记，以及一篇它如何分解复杂任务的工作流分析。为 Claude Code 内部机制而来的读者，请看这两样；想看这类东西被用来造什么，请看 [coding-proxy](https://github.com/ThreeFish-AI/coding-proxy) 与 [negentropy](https://github.com/ThreeFish-AI/negentropy)。

所以：**<!-- DATA:src_repos -->7<!-- /DATA:src_repos --> 个源仓库、<!-- DATA:own_stars -->51<!-- /DATA:own_stars --> 星、约 1,850 个公开 PR、28 个 release。**我更愿意被这些数字评价。

</details>

---

## 通道

[笔记](https://threefish-ai.github.io) · [CSDN](https://threefish.blog.csdn.net/) · [@ThreeFish-AI](https://github.com/ThreeFish-AI)

<!-- Bilibili / 知乎：确认账号可访问后再启用——在一个讲「可核实」的页面上，死链比没有链接更糟。 -->

---

[^weilue]: 鱼豢，《魏略·儒宗传》；原书已散佚，赖裴松之注《三国志·魏书·王朗传》（附王肃传）转引流传，三国时期（3 世纪）。

[^schrodinger]: E. Schrödinger, *What is Life? The Physical Aspect of the Living Cell*. Cambridge, U.K.: Cambridge University Press, 1944.

<div align="center">
  <sub>首屏数字由<a href="https://github.com/ThreeFish-AI/threefish-ai/blob/master/.github/workflows/refresh-profile-data.yml">一个 workflow</a> 每月自 GitHub API 刷新；手写数字自带 as-of 日期 · <!-- DATA:asof -->last refreshed 2026-09-05<!-- /DATA:asof --></sub><br/>
  <sub>由 <a href="https://github.com/ThreeFish-AI">ThreeFish-AI</a> 用 🧠、❤️ 与不计其数的咖啡构建。</sub>
</div>
