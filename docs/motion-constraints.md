# Motion Constraints — 图表动效约束（单一事实源）

本文件从 `scripts/build_profile_svgs.py` 的写入闸门 `assert_svg_sane` 反推整理而成。
闸门是机械强制，本文件是给人读的「为什么」。两者冲突时，以闸门为准并修本文件。

## 规则

1. **只有一次性入场动效，永远没有循环。**
   闸门拒绝文件中出现 `infinite` 与 `repeatCount="indefinite"`（含 aria 文本里的该词——所以 alt 文案禁写 "infinite"）。

2. **默认态 == 终态。**
   每个动画元素的样式基线携带 `opacity:0`；动画声明为 `… 1 both`；`@keyframes` 必须显式写出
   `0%{…opacity:0}` 与 `100%{…opacity:0}`。动画元素因此**纯装饰**：静止页面就是完整页面。

3. **动效是渐进增强，静态是默认。**
   所有动画规则必须包在 `@media (prefers-reduced-motion:no-preference)` 里。开启减弱动效的用户
   得到的是同一张完整静态图。

4. **一个文件至多一个 `@keyframes`，用 `animation-delay:var(--d)` 错峰。**
   闸门的 keyframe 体提取是非贪婪正则，两个以上 `@keyframes` 会让校验对象互相串块（可达的假通过）。
   `render_mark` 的 `--d` 模式是标准做法。

5. **动画元素不得承载数据或文字。**
   减弱动效的用户会丢掉该元素承载的任何信息点。闸门拒绝任何出现在 `<text>` 上的动画 class。
   动效词汇表：扫掠条（Sweep-X/Sweep-Y）、涟漪（ripple）、落点环（landing ring）、轨迹点（trace
   dot）——全是可丢弃的装饰层。

6. **暗色覆盖必须严格位于基线规则之后。**
   `@media (prefers-color-scheme:dark)` 里对某 class 的覆盖若先于其基线定义，会被基线反向覆盖。

7. **预算与卫生：** 每张 SVG ≤ 8,192 B；带 `role="img"` 与 `aria-label`；无外部资源、无 `@import`。

## 推论：不存在「渐显后停留」

规则 2 强制每个动画元素以不可见收尾（`100%{opacity:0}`），因此：

- **遮罩式 reveal（wipe）结构上不可能。** 一张遮罩若以 `opacity:0` 收尾，静止态会把内容全部
  自行揭开（默认态 ≠ 终态），直接违反规则 2。任何柱体「从左到右渐渐显现」的设想都被此规则
  否决，不要重新论证。
- 想让注意力落到某处，用**落点环**或**扫掠**在终态消失的装饰层表达，而不是让数据本身动。

## 历史脚注

v1 的贡献贪吃蛇（第三方 action 输出动图）因违反规则 1 在 v2 移除。v4 曾把本约束写在
`.context/v4-motion-constraints.md`，而 `.context/` 在 `.gitignore` 中——文档从未入库即丢失；
本文件（v5）是按闸门反推的重建，并修正了脚本 docstring 的悬空引用。

## 布局闸门（v5 追加）

动效之外，`assert_svg_sane` 还机械强制两条**布局**规则。它们与动效规则同源：
图元位置由数据推导，今天排得下的标签，明天的采集就可能排不下——只有闸门能发现。

8. **每个标签必须落在画布内，且不与其他标签重叠。**
   `assert_text_fits` 按 Helvetica 字宽表推算每个 `<text>` 的包围盒（解析 `tm`/`te`/`ts`
   锚点），越界或同基线重叠即拒绝。字宽表乘 `FONT_SLACK`（实测系统字体栈首选的 SF Pro
   比 Helvetica 宽 7–12%），闸门因此**高估**宽度：宁可误报，不可漏过一张已裁剪的图。
   位置推导用 `clamp_start` / `clamp_mid` / `spread_labels`，不要手写坐标硬扛。

9. **描边图元不得挂 fill-only 类。**
   CSS 类规则优先级高于 presentation attribute，因此 `.bar{fill:#8c959f}` 加在
   `<path fill="none" stroke-width="2">` 上，画出的不是灰线而是**无描边的灰色色块**；
   `<line class="acc">` 则完全不可见——XML 合法、标签不越界、体积达标，只有数据没画出来。
   描边一律用 `.bars` / `.accs` / `.inks` / `.vals`（`fill:none;stroke:…`），
   由 `assert_stroked_marks` 强制。
