<div align="center">

<!-- FIG:mark --><img src="https://raw.githubusercontent.com/ThreeFish-AI/threefish-ai/master/assets/mark.svg" width="256" alt="三条鱼，作为签名图形。汉语里，董遇的「三余」——冬天、夜晚、雨天（sān yú）——与「三鱼」几乎同音，ID 由此而来。纯装饰，不编码任何数据。" /><!-- /FIG:mark -->

### Aurelius Huang · 阿浩

**熵减——代码库的，与日子的。**

<sub>白天做生产级 Agent 基础设施 · [English](../../../README.md) · [简体中文](./README.md) · [笔记](https://threefish-ai.github.io)</sub>

</div>

> 冬者岁之余，夜者日之余，阴雨者时之余。
>
> <sub>——董遇，三世纪。[^weilue] 余暇本来就在那里，只是几乎所有人都任其蒸发。[negentropy](https://github.com/ThreeFish-AI/negentropy) 之名取自薛定谔的负熵。[^schrodinger]</sub>

---

<!-- FIG:growth --><img src="https://raw.githubusercontent.com/ThreeFish-AI/threefish-ai/master/assets/growth.svg" width="700" alt="2016–2026 逐年贡献柱状图，平方根标度：1, 0, 0, 13, 129, 198, 676, 589, 1,181, 3,193, 9,311。2017、2018 为真实零值，画作基线下方的空槽。2023（589）低于 2022（676）。数据：GitHub。" /><!-- /FIG:growth -->

<sub>十一年，平方根标度。**<!-- DATA:cur_total -->9,311<!-- /DATA:cur_total -->（<!-- DATA:cur_year -->2026<!-- /DATA:cur_year -->）**——此前是两个真正的零，和一次真正的回落。</sub>

<!-- FIG:rhythm --><img src="https://raw.githubusercontent.com/ThreeFish-AI/threefish-ai/master/assets/rhythm.svg" width="700" alt="开源提交按小时分布直方图（共 4,349 条，Asia/Shanghai，横轴自 04:00 起至 03:00，使夜间块连续）。自 04:00 起逐小时数值：0, 0, 0, 11, 44, 232, 338, 319, 186, 184, 265, 285, 262, 292, 242, 206, 214, 348, 460, 329, 91, 36, 3, 2。04:00–06:59 为真实零值（基线下方空槽）。峰值 22:00 共 460 条——占全部提交 10.6%，为平坦基线的 2.54 倍。低于最小可见高度 2.5 像素的柱按最小高度绘制。" /><!-- /FIG:rhythm -->

<sub>余暇的落点：**<!-- DATA:peak_h -->22:00<!-- /DATA:peak_h -->**，平坦基线的 <!-- DATA:peak_x -->2.54×<!-- /DATA:peak_x -->——<!-- DATA:commits_total -->4,349<!-- /DATA:commits_total --> 条开源提交，Asia/Shanghai。黎明是空的，不是缺数据。</sub>

<!-- FIG:punchcard --><img src="https://raw.githubusercontent.com/ThreeFish-AI/threefish-ai/master/assets/punchcard.svg" width="700" alt="开源提交按星期 × 小时的打卡图（共 4,349 条，Asia/Shanghai，列自 04:00 至 03:00，行自周一至周日，窗口 2024-06-22 至 2026-09-01）。格面积与提交数成正比，边长保留一位小数。周一至周日合计：615、557、563、504、602、780、728。最密格 Sunday 22:00，83 条。168 格中 37 格为真实零值，画作空心方框。周末合计 1,508 条，占 34.7%（平坦份额为 28.6%）。数据：GitHub。" /><!-- /FIG:punchcard -->

<sub>二维答案：最密格 **<!-- DATA:pc_cell -->Sun 22:00<!-- /DATA:pc_cell -->**（周日 22:00），<!-- DATA:pc_val -->83<!-- /DATA:pc_val --> 条提交；168 格中 <!-- DATA:pc_empty -->37<!-- /DATA:pc_empty --> 格为真实零值；周末占 <!-- DATA:wknd_pct -->34.7%<!-- /DATA:wknd_pct -->（平坦份额 28.6%）。</sub>

<!-- FIG:surplus --><img src="https://raw.githubusercontent.com/ThreeFish-AI/threefish-ai/master/assets/surplus.svg" width="700" alt="同一小时轴（04:00 至 03:00，Asia/Shanghai，2024-06-22 至 2026-09-01）上的两条阶梯曲线，按「该类日」归一为日均提交，使 572 个工作日与 230 个周末日可比。工作日自 04:00 起逐小时速率：0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 0.5, 0.4, 0.2, 0.2, 0.3, 0.3, 0.3, 0.3, 0.2, 0.2, 0.2, 0.4, 0.5, 0.4, 0.1, 0.0, 0.0, 0.0。周末：0.0, 0.0, 0.0, 0.0, 0.1, 0.2, 0.2, 0.3, 0.3, 0.4, 0.4, 0.4, 0.4, 0.5, 0.5, 0.4, 0.5, 0.6, 0.7, 0.5, 0.2, 0.1, 0.0, 0.0。工作日峰值 22:00（日均 0.5 条）；周末峰值 22:00（日均 0.7 条）。数据：GitHub。" /><!-- /FIG:surplus -->

<sub>工作日对周末，按日均归一（**<!-- DATA:wd_days -->572<!-- /DATA:wd_days --> 个工作日 ÷ <!-- DATA:we_days -->230<!-- /DATA:we_days --> 个周末日**）：形状相同，且周末的日均反而更热——峰值落在 <!-- DATA:we_peak_h -->22:00<!-- /DATA:we_peak_h -->。「白天」是职业描述，不是作息表。</sub>

<!-- FIG:ground --><img src="https://raw.githubusercontent.com/ThreeFish-AI/threefish-ai/master/assets/ground.svg" width="700" alt="各源仓库提交量水平条形图（降序）：negentropy 2,048；agentic-ai-cognizes 945；coding-proxy 638；negentropy-perceives 433；hyper-git 125；threefish-ai.github.io 117；give-me-a-break 43。共 4,349 条提交、29 个 release、7 个源仓库；negentropy 占 47.1%。Release 分布：coding-proxy 12、give-me-a-break 7、hyper-git 7、negentropy 2、negentropy-perceives 1。agentic-ai-cognizes、negentropy-perceives 已归档——毕业并入 negentropy 主干。" /><!-- /FIG:ground -->

<sub>[negentropy](https://github.com/ThreeFish-AI/negentropy) 知识引擎 · [coding-proxy](https://github.com/ThreeFish-AI/coding-proxy) 编码 Agent 故障转移 · [hyper-git](https://github.com/ThreeFish-AI/hyper-git) VS Code 变更列表 · [agents.md](https://github.com/ThreeFish-AI/agents.md) 它们共同遵循的规约</sub>

<!-- FIG:accrual --><img src="https://raw.githubusercontent.com/ThreeFish-AI/threefish-ai/master/assets/accrual.svg" width="700" alt="各源仓库累计提交折线（月分辨率，2024-06-22 至 2026-09-01——约 26 个月窗口，不是上方那张十一年图）。期末合计：agentic-ai-cognizes 945；coding-proxy 638；give-me-a-break 43；hyper-git 125；negentropy 2,048；negentropy-perceives 433；threefish-ai.github.io 117；全部仓库共 4,349。2026-05-18 两个已归档仓库走平、主干继续上升：两个仓库于该日毕业并入 negentropy 主干。数据：GitHub。" /><!-- /FIG:accrual -->

<sub>月度累计：两条曲线在毕业并入主干的那一天走平，而主干继续爬升。窗口 <!-- DATA:win_from -->2024-06-22<!-- /DATA:win_from --> → <!-- DATA:win_to -->2026-09-01<!-- /DATA:win_to -->——**<!-- DATA:win_months -->26<!-- /DATA:win_months --> 个月，不是上方那张十一年图。**</sub>

<!-- FIG:lifecycles --><img src="https://raw.githubusercontent.com/ThreeFish-AI/threefish-ai/master/assets/lifecycles.svg" width="700" alt="仓库生命周期色带，每行一个源仓库，自创建至最后推送，2024-06-22 至 2026-09-01。agentic-ai-cognizes 创建于 2025-10-22，最后推送 2026-05-18，已归档（毕业）；coding-proxy 创建于 2026-03-30，最后推送 2026-08-27，活跃；give-me-a-break 创建于 2026-06-23，最后推送 2026-09-04，活跃；hyper-git 创建于 2026-06-27，最后推送 2026-09-01，活跃；negentropy 创建于 2026-01-31，最后推送 2026-09-04，活跃；negentropy-perceives 创建于 2025-08-26，最后推送 2026-05-18，已归档（毕业）；threefish-ai.github.io 创建于 2024-06-22，最后推送 2026-07-08，活跃。条形终点是最后推送——归档的最近公开代理，因为 GitHub 不公开归档时间戳；归档与否由方形终端图元承载。已被删除的仓库在公开口径下不可见。数据：GitHub。" /><!-- /FIG:lifecycles -->

<sub>仓库即区间，自创建至最后推送；两根同日终止的条就是那次毕业。已删除的仓库在此口径下不可见。</sub>

<!-- FIG:cadence --><img src="https://raw.githubusercontent.com/ThreeFish-AI/threefish-ai/master/assets/cadence.svg" width="700" alt="各仓库公开 release 的点式时间线（共用日期轴，2024-06-22 至 2026-09-01）。coding-proxy 12 个 release，v0.1.1（2026-04-05）至 v0.5.2a8（2026-07-06）；give-me-a-break 7 个 release，v0.1.0（2026-06-27）至 v0.1.6（2026-09-04）；hyper-git 7 个 release，v0.0.6（2026-06-30）至 v0.0.16（2026-09-01）；negentropy 2 个 release，negentropy-v0.0.1-rc.1（2026-06-19）至 negentropy-v0.0.1-rc.2（2026-06-19），全部为预发布；negentropy-perceives 1 个 release，v0.2.0a3（2026-04-20）至 v0.2.0a3（2026-04-20）。空心点为预发布。negentropy 在 2,048 条提交面前只有两个 rc，因为它是部署型服务而非分发包——它的交付单元是已合并 PR，不是 tag。数据：GitHub。" /><!-- /FIG:cadence -->

<sub>Release 有时机，不止有计数——最新一个：**<!-- DATA:rel_last_name -->give-me-a-break<!-- /DATA:rel_last_name --> <!-- DATA:rel_last_tag -->v0.1.6<!-- /DATA:rel_last_tag -->**。negentropy 以已合并 PR 交付，不以 tag。</sub>

<!-- FIG:streak --><img src="https://raw.githubusercontent.com/ThreeFish-AI/threefish-ai/master/assets/streak.svg" width="700" alt="一维 rug 图，取最近 400 天（2025-07-29 至 2026-09-01），每天一根刻度，高度为当日署名提交数的平方根。208 天有至少一条提交（52%）；其余 192 天画作基线下方的细线，每个空档一段。窗口内最长连续区间 88 天（2026-03-19 至 2026-06-14），以括号标出。口径为源仓库内我署名的提交——与本页其他提交图同一总体，且窄于 GitHub 贡献日历（后者还计入私有工作、issue 与 review）。数据：GitHub。" /><!-- /FIG:streak -->

<sub>连续区间的落点：**<!-- DATA:streak -->88<!-- /DATA:streak --> 天，<!-- DATA:streak_from -->2026-03-19<!-- /DATA:streak_from --> → <!-- DATA:streak_to -->2026-06-14<!-- /DATA:streak_to -->**，已加括号标注。rug 图取最近 400 天；整个窗口 <!-- DATA:win_days -->802<!-- /DATA:win_days --> 天中 <!-- DATA:active_days -->249<!-- /DATA:active_days --> 天有提交（<!-- DATA:active_pct -->31%<!-- /DATA:active_pct -->）——口径为源仓库内我署名的提交，窄于上方的 GitHub 贡献日历。</sub>

---

<!-- FIG:latency --><img src="https://raw.githubusercontent.com/ThreeFish-AI/threefish-ai/master/assets/latency.svg" width="700" alt="negentropy 已合并 PR 的生存时间直方图，右侧带 0–100% 阶梯累积曲线。共 1078 个已合并PR，对数分箱：&lt;1m 281、1-2 72、2-5 144、5-15 225、15-60m 177、1-4h 92、4-24h 83、&gt;24h 4。中位 6 min；90 分位 2.8 h；83% 一小时内合并；最长等待 11.9 d。另有 40 个已关闭未合并的 PR，未计入。这是单人自合并仓库：生存时间量的是变更单元有多小，不是评审有多快。数据：GitHub。" /><!-- /FIG:latency -->

<sub>中位数藏掉的部分：p90 **<!-- DATA:p90 -->2.8 h<!-- /DATA:p90 -->**，最长 **<!-- DATA:lat_max -->11.9 d<!-- /DATA:lat_max -->**；已关闭 <!-- DATA:pr_closed -->1118<!-- /DATA:pr_closed --> 个中 <!-- DATA:pr_unmerged -->40<!-- /DATA:pr_unmerged --> 个未合并，未计入。单人自合并：量的是变更单元大小，不是评审速度。</sub>

<!-- FIG:grammar --><img src="https://raw.githubusercontent.com/ThreeFish-AI/threefish-ai/master/assets/grammar.svg" width="700" alt="一百格华夫图，每格代表 4,349 条署名提交主题的百分之一，按 Conventional Commits 前缀分类。fix 827、docs 725、feat 697、refactor 319、chore 255、style 176、test 144、ci 110、build 92、perf 6、revert 2。996 条主题不能解析为 Conventional Commits，画作空心格。着色块为 fix——最大类型，占全部主题的 19.0%。数据：GitHub。" /><!-- /FIG:grammar -->

<sub>让「一百中之七十七」可数：**<!-- DATA:top_type -->fix<!-- /DATA:top_type --> <!-- DATA:top_type_pct -->19.0%<!-- /DATA:top_type_pct -->** 居首；**<!-- DATA:nonconf_n -->996<!-- /DATA:nonconf_n --> 条主题（<!-- DATA:nonconf_pct -->22.9%<!-- /DATA:nonconf_pct -->）不合规**——画作空心格，而不是藏起来。</sub>

<!-- FIG:tongues --><img src="https://raw.githubusercontent.com/ThreeFish-AI/threefish-ai/master/assets/tongues.svg" width="700" alt="源仓库语言字节占比的斜率图，两种口径。左：GitHub 语言端点原样——HTML 67.8%，Python 22.7%，TypeScript 8.3%，Swift 0.5%，CSS 0.2%，C# 0.2%。右：剔除 threefish-ai.github.io（其 HTML 字节是静态站构建产物而非手写源码）——Python 69.1%，TypeScript 25.2%，HTML 2.3%，Swift 1.4%，C# 0.6%，CSS 0.5%。HTML 从第 1 位跌至第 3 位；Python 升至第 1 位。字节数度量的是提交源码体积，不是作者归属或工作量，且含 vendored 文件。每个源仓库均有计入字节。数据：GitHub。" /><!-- /FIG:tongues -->

<sub>两种口径并陈，而非悄悄二选一：GitHub 端点说 **<!-- DATA:lang_naive -->HTML<!-- /DATA:lang_naive --> <!-- DATA:lang_naive_pct -->67.8%<!-- /DATA:lang_naive_pct -->**；剔除那个静态站构建产物仓库后，**<!-- DATA:lang_top -->Python<!-- /DATA:lang_top --> <!-- DATA:lang_top_pct -->69.1%<!-- /DATA:lang_top_pct -->**。字节数度量源码体积，不度量工作量或作者归属。</sub>

<!-- FIG:upstream --><img src="https://raw.githubusercontent.com/ThreeFish-AI/threefish-ai/master/assets/upstream.svg" width="700" alt="提交给他人仓库的公开 PR 点账本，2024-06-26 至 2025-12-06。langgenius/dify#5631，已合并，2024-06-26；langgenius/dify#8921，已合并，2024-09-30；langgenius/dify-plugin-daemon#389，关闭未合并，2025-07-07；langgenius/dify-cloud-kit#3，已合并，2025-07-08；langgenius/dify#22646，已合并，2025-07-18；DayuanJiang/next-ai-draw-io#124，已合并，2025-12-06。它们占 1,849 个公开 PR 的 0.3%；其余都提交给我自己的仓库。数据：GitHub is:public 检索。" /><!-- /FIG:upstream -->

<sub>N = <!-- DATA:ext_prs -->6<!-- /DATA:ext_prs -->，全部具名：<!-- DATA:ext_first -->2024-06-26<!-- /DATA:ext_first --> → <!-- DATA:ext_last -->2025-12-06<!-- /DATA:ext_last -->，<!-- DATA:ext_merged -->5<!-- /DATA:ext_merged --> 个已合并、一个关闭未合并——占全部公开 PR 的千分之几。比例本身就是重点。</sub>

---

<div align="center"><sub><!-- DATA:pub_prs -->1,849<!-- /DATA:pub_prs --> 个公开 PR ·
<!-- DATA:neg_pr -->1,078<!-- /DATA:neg_pr --> 个已在 negentropy 合并，中位 <!-- DATA:neg_median -->6<!-- /DATA:neg_median --> 分钟，<!-- DATA:pct_hour -->83%<!-- /DATA:pct_hour --> 一小时内 ·
<!-- DATA:streak -->88<!-- /DATA:streak --> 天连续提交 ·
<!-- DATA:conv_pct -->77.1%<!-- /DATA:conv_pct --> Conventional Commits ·
<!-- DATA:rel_total -->29<!-- /DATA:rel_total --> 个 release ·
<!-- DATA:src_repos -->7<!-- /DATA:src_repos --> 个源仓库，
<!-- DATA:own_stars -->51<!-- /DATA:own_stars --> 颗真正属于我的星 ·
<!-- DATA:ext_merged -->5<!-- /DATA:ext_merged -->/<!-- DATA:ext_prs -->6<!-- /DATA:ext_prs --> 个上游 PR 已合并——<!-- DATA:ext_dify -->4<!-- /DATA:ext_dify --> 个在 [Dify](https://github.com/langgenius/dify) 生态，一个在生态之外</sub></div>

<details>
<summary><b>诚实性说明</b></summary>

- 头条计数拆分为 5,590 条公开可点击 / 3,640 条私有工作（截至 2026-09）。私有工作计入计数，但不提供链接——所以不配上标题。
- `negentropy` 是单人自合并仓库：PR 是有标题、可回滚的原子变更单元，不是评审门禁。6 分钟中位时长测的是这件事。
- [analysis_claude_code](https://github.com/ThreeFish-AI/analysis_claude_code)（<!-- DATA:acc_stars -->312<!-- /DATA:acc_stars --> 星）大部分**不是**我的作品——它镜像自 [CrazyBoyM](https://github.com/CrazyBoyM) / ShareAI-Lab 的 Claude Code 源码分析，奠基提交属原作者。属于我的部分：研读笔记。
- <!-- DATA:archived_names -->agentic-ai-cognizes, negentropy-perceives<!-- /DATA:archived_names -->（<!-- DATA:archived_n -->2<!-- /DATA:archived_n --> 个源仓库，合计 1,378 条提交）已归档——毕业并入 negentropy 主干：perceives 成为它的内容提取服务，cognizes 成为 `apps/cognizes`。这是预期的生命周期，不是失败。且天然冻结：归档不再变动。
- 第六个上游 PR 被关闭未合并——与上一行同类缺陷，上游以另一条路径修掉了。六个对 <!-- DATA:pub_prs -->1,849<!-- /DATA:pub_prs --> 个公开 PR：我绝大部分公开工作，都发生在我同时也是评审者的仓库里。
- 年度图采用平方根标度以保留早期年份的可见度，因此低估了近年的增长。所有图表由[一个 workflow](https://github.com/ThreeFish-AI/threefish-ai/blob/master/.github/workflows/refresh-profile-data.yml) 每月自 GitHub API 重新生成——截至 <!-- DATA:asof -->2026-09-05<!-- /DATA:asof -->。

</details>

---

[^weilue]: 鱼豢，《魏略·儒宗传》；原书已散佚，赖裴松之注《三国志·魏书·王朗传》转引流传，三国时期（3 世纪）。

[^schrodinger]: E. Schrödinger, *What Is Life? The Physical Aspect of the Living Cell*. Cambridge, U.K.: Cambridge University Press, 1944.

<div align="center"><sub>[笔记](https://threefish-ai.github.io) · [CSDN](https://threefish.blog.csdn.net/) · [@ThreeFish-AI](https://github.com/ThreeFish-AI)</sub></div>
