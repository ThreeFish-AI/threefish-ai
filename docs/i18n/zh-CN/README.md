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

<!-- FIG:ground --><img src="https://raw.githubusercontent.com/ThreeFish-AI/threefish-ai/master/assets/ground.svg" width="700" alt="各源仓库提交量水平条形图（降序）：negentropy 2,048；agentic-ai-cognizes 945；coding-proxy 638；negentropy-perceives 433；hyper-git 125；threefish-ai.github.io 117；give-me-a-break 43。共 4,349 条提交、29 个 release、7 个源仓库；negentropy 占 47.1%。Release 分布：coding-proxy 12、give-me-a-break 7、hyper-git 7、negentropy 2、negentropy-perceives 1。agentic-ai-cognizes、negentropy-perceives 已归档——毕业并入 negentropy 主干。" /><!-- /FIG:ground -->

<sub>[negentropy](https://github.com/ThreeFish-AI/negentropy) 知识引擎 · [coding-proxy](https://github.com/ThreeFish-AI/coding-proxy) 编码 Agent 故障转移 · [hyper-git](https://github.com/ThreeFish-AI/hyper-git) VS Code 变更列表 · [agents.md](https://github.com/ThreeFish-AI/agents.md) 它们共同遵循的规约</sub>

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
