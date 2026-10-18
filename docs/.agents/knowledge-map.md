# Knowledge Map

本仓文档索引与跨文档编辑契约的唯一入口。

## 文档索引

| 文档 | 职责 |
|---|---|
| [`README.md`](../../README.md) | 英文 profile 主页（月度构建产物：13 FIG + 75 DATA 标记） |
| [`docs/i18n/zh-CN/README.md`](../i18n/zh-CN/README.md) | 中文镜像主页（与英文版逐行结构镜像） |
| [`docs/motion-constraints.md`](../motion-constraints.md) | SVG 动效/布局闸门的「为什么」层（闸门机械强制在 `scripts/build_profile_svgs.py`，冲突时以闸门为准） |
| [`docs/.agents/issue.md`](issue.md) | Issue 台账（头部索引 + 详情锚点） |

## 双语镜像编辑契约卡

改任一 README 前必读。两份文件是**逐行结构镜像**：marker 行号、结构骨架行号（details/summary/锚点/表格/代码块）、总行数必须逐位一致；合法差异仅三类——正文语言、img `src` 绝对化（中文版仓库外渲染所需）、语言切换行相对路径。

1. **机器领地，永不手改**：`<!-- FIG:k -->…<!-- /FIG:k -->` 体（img/alt/src 每次刷新从零重建，手改必被覆盖）；`<!-- DATA:k -->值<!-- /DATA:k -->` 的值。生成器为 [`scripts/build_profile_svgs.py`](../../scripts/build_profile_svgs.py)。
2. **标记即契约**：key 必须 ∈ `FACT_KEYS`/`FIG_SPEC`；两文件 (kind,key) 有序流必须全等且非空（`audit_parity`）；增删/换序标记须两文件同步，且计数变化需同步 `tests/test_contract.py` 的 75/13 硬编码断言。
3. **含 marker 的行谨慎编辑**：值以外的行内文字可改，但 marker 本身与其相对顺序不可动；`DATA:cur_year`/`DATA:cur_total` 是月度刷新「当年数字不回退」守卫的状态源，永不删除。
4. **锚点三方同名同序**（无机器守卫，纯人工契约）：`<summary><a name="X">` ×13、两条簇导航 `<sub>` 行的 `#user-content-X` 链接、FIG key `X` 三者集合与顺序一致；GitHub 对手写 `name` 自动加 `user-content-` 前缀，链接侧必须手写该前缀。
5. **冻结面绕行**：mermaid 块、upstream/census/道法术表格、IEEE 脚注、recompute 命令块承载既有契约，结构性重构一律绕行。
6. **编辑后验证**（仓库根）：
   ```bash
   python3 -m unittest discover tests                  # 31 用例（含 Golden Master）
   python3 scripts/build_profile_svgs.py --lint        # 零网络，同 PR CI lint job
   ```
   另以行号镜像检查护航第 4 条人工契约（marker 行号 diff、骨架行号 diff、行数相等）。
7. **散文重复收敛原则**：同一事实多处手写 = 漂移风险（先例：九厂商清单曾单侧漏一家，PR #7 只修了数据）；收敛时指定唯一权威位置（如承诺性陈述放项目卡），其余降为回指；机器供数（DATA/alt）的重复无漂移风险，不做收敛。
