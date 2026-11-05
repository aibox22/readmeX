# 优化 README

入口已经选定范围、完成扫描并一次问完问题。这里不再提问。合并执行默认整页视觉刷新；单独执行遵循用户选择的整页或仅素材范围。只有明确同意才调用生图或生成 GIF；未回答、拒绝或工具不可用时交付静态 SVG，并在结果中记录原因。

## 1. 先写故事，再冻结视觉

读取 `.readmex/scan.json`、README、真实示例、截图、品牌和源码。先在 `.readmex/optimize/story.md` 写五行：

```text
Audience: 读者
One-sentence value: 一句话价值
Primary proof: 可核对的主要证据
First successful action: 第一次成功使用
Visual theme: 项目自身的视觉主题
```

接着在同一文件冻结背景/前景/主色/强调色/弱化色、系统字体与字号层次、圆角/线宽/网格/间距、一个项目母题和构图。母题来自项目机制或实际产物，例如 CLI 的提示符、数据工具的记录流；不要把同一个装饰模板套到所有项目。没有证据的采用率、速度、稳定性和兼容性不得写进故事。新发现的不可核对主张降级或删除，记入 `.readmex/review/scorecard.md`；单独优化时只记录这些证据与处理结果，不假装已经完成整套审查或给出分数。

读 [优化视觉精选](../references/optimize-visual.md) 后再设计。整页模式保留审查已经验证的事实、命令和读者漏斗，缩短重复文案，把关键说明留在 Markdown。素材模式只产生请求的素材和可复制的嵌入建议，不改写 README，也不自动扩展范围。已被 README 引用的素材可在原路径更新；新建且尚未引用的素材先存 `.readmex/optimize/preview/assets/`，给出复制到 `readme/assets/` 后使用的 Markdown 片段，不把未引用素材发布到 `readme/assets/`。

## 2. 制作项目自身的英雄图

先用项目 Logo、真实输出、截图、示例或核心机制构图。英雄图承担身份和价值说明，不能把项目名称与一句话身份挤出首屏。精确文字由 SVG 排版，正文和命令仍放 Markdown。

整页模式默认发布 `readme/assets/hero.svg`；素材模式遵循上面的暂存规则。明确允许生图时，读 [混合合成](../references/hybrid-svg-production.md)，按已冻结的设计调用可用的 imagegen 技能或生图工具：

- `.readmex/optimize/imagegen/hero-layout.svg`：布局源；
- `.readmex/optimize/imagegen/hero-subject.png`：项目专属素材；
- `.readmex/optimize/imagegen/hero-prompt.txt`：最终提示词；
- `readme/assets/hero.png`：核验过的合成图。

生成素材不得代替更强的真实证据；不要让生图模型生成标题、标签、Logo 或 UI 文字。不要发布依赖本地栅格路径的 SVG。生成失败就继续静态 SVG，把原因写进结果。

## 3. 重写架构与流程图

整页模式删除 README 中所有 Mermaid 块；依据扫描和实际源码重写图，避免照搬旧图。小项目没有值得说明的架构或流程时直接省略。素材模式可读 Mermaid 作为线索，但不修改 README；需要换图时提供静态图及替换建议。

读取 [渲染器写作说明](../references/renderer-authoring.md)、对应 schema 和 example。把 JSON 存为 `.readmex/optimize/diagrams/architecture.json` 或 `workflow.json`，整页模式令 `meta.output` 指向 `readme/assets/architecture.svg` 或 `workflow.svg`；素材模式新图指向 `.readmex/optimize/preview/assets/`：

```bash
node <skill>/bin/render-diagram.mjs <target>/.readmex/optimize/diagrams/architecture.json --repo-root <target>
node <skill>/bin/render-diagram.mjs <target>/.readmex/optimize/diagrams/workflow.json --repo-root <target>
```

源引用默认核对当前工作目录的文件和行号并记录哈希；明确指定提交时按提交核对。任何引用核验失败都停止该图渲染，不发布未核验的替代图，也不把失败说成成功。正常的几何诊断可按说明修复后重跑。图必须是自带浅色背景的静态 SVG，图下配一段 Markdown，解释主阅读路径和必要限制。

## 4. 可选 GIF

只对英雄图和流程图制作 GIF，且运动必须说明真实顺序或状态变化。静态图先验收，GIF 不承担唯一的关键信息。读取 [动画制作](../references/motion-production.md)，把动画 JSON 存到 `.readmex/optimize/motion/`：

```bash
python3 <skill>/scripts/render_motion_gif.py <target>/readme/assets/workflow.svg <target>/readme/assets/workflow.gif --spec <target>/.readmex/optimize/motion/workflow.json
```

始终保留同名 `hero.svg` 或 `workflow.svg`，整页模式在图下给静态版链接以便 README 也能引用回退文件。混合英雄图还需做一个不依赖生成素材、能够独立显示的静态 `hero.svg`；布局源留在中间目录。素材模式新 GIF 与静态回退一起暂存。脚本自动补 Pillow、ffmpeg 和可用 SVG 转 PNG 工具。Linux 需要安装权限时，让用户在其终端确认系统密码，模型不得读取或填写密码；这不是新的设计提问。安装失败或交互不可用就跳过 GIF，记录原因。帧文件使用临时目录，成功和失败都删除，不提交逐帧文件。

## 5. 验收与交付

按 [优化质量条](../references/optimize-visual.md#质量条) 逐项验收。所有完整宽度 SVG 的 viewBox 宽为 1200；主要标签至少 20 SVG 单位，辅助标签至少 18；在 `.readmex/optimize/preview/` 保留 900 与 360 宽的实际渲染预览。手机上仍看不清的必要标签必须简化、拆图或把细节移入 Markdown，不能只靠满足字号数字宣布通过。

整页模式完成后执行：

```bash
python3 <skill>/scripts/readme_view_audit.py <target>/README.md
```

脚本检查本地引用、alt 和 SVG 基础兼容性，不能替代实际视觉预览。素材模式也要在两种宽度检查每张图；可用临时 Markdown 引用待交付素材后运行同一脚本。检查 GIF 的进入、停留、退出和循环边界，确认静止阶段没有抖动。

只把最终 README 引用的文件留在 `readme/assets/`；素材模式待嵌入文件留在 `.readmex/optimize/preview/assets/`，明确列出后续复制路径和嵌入片段，不追加批准问题。中间文件都进 `.readmex/`，删除废弃变体。简要报告改动、预览与审计结果、生图/GIF 是否启用或跳过及原因。不要添加署名，也不提议或创建 showcase PR。
