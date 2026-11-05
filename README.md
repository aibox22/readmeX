# readmex

用三条任务流水线，为项目作者创建、审查和美化 README。

> [!NOTE]
> **正在开发和重构的实验版本。** 适合个人项目作者试用；尚不承诺稳定接口或维护周期。

![readmex：创建、审查、优化三条流水线依次点亮](readme/assets/hero.gif)

[查看静态头图](readme/assets/hero.svg)

起稿、证据审查和视觉呈现可以分开执行，也可以合并。快速创建只起稿；审查增加实际执行与逐主张核对；优化再增加配图和移动端验收。适合愿意为事实与显示效果增加检查步骤的作者。生图与 GIF 都需要明确同意。

## 先试一次

加载技能后，在一个没有 README 的小项目中发送：

```text
$readmex 快速写一份中文 README
```

结果写到该项目根目录的 `README.md`。如果项目已有 README，快速创建会转为审查，先交记分卡；单独审查需你同意后才改正文。

| 你想做什么 | 可以这样说 |
|---|---|
| 快速起稿 | `$readmex 快速写一份中文 README` |
| 先看问题 | `$readmex 审查 README，先给记分卡` |
| 整页美化 | `$readmex 美化 README，整页优化` |
| 只做素材 | `$readmex 只制作架构图素材` |
| 完整改写 | `$readmex 完整重写 README，执行全流程` |

只说“写个 README”时，会在开头一次问清路线与必要事实。完整流程遇到已有 README，从审查开始；选择完整改写后会直接继续优化。

## 安装

需要支持 Agent Skills 的 AI 工具。获取[本仓库](https://github.com/aibox22/readmeX)后，首次安装到 Codex 时，在仓库根目录运行以下命令，目标技能目录应尚不存在：

```bash
mkdir -p "$HOME/.codex/skills"
cp -R skills/readmex "$HOME/.codex/skills/readmex"
```

复制的是**整个技能目录**，包含管线、脚本、渲染器和数据。已有旧版时完整替换该目录；其他工具可将同一目录放到其技能目录。安装后，在下一轮消息中调用 `$readmex`；若技能列表尚未更新，可以在请求中直接指定 `~/.codex/skills/readmex/SKILL.md`。

配套检查使用 **Python 3.9+**，图表渲染使用 **Node.js 18+**，渲染器无需安装 npm 依赖。本次本地验证环境为 Python 3.9.6、Node.js 20.20.2；其他版本尚未实测。写作由 AI 执行，`$readmex` 不是终端命令。

## 三条流水线

![readmex 完整流程：创建新稿，核验并改写，再生成视觉素材](readme/assets/workflow.gif)

[查看静态流程图](readme/assets/workflow.svg)

- **创建**：通读项目，写清用途、安装与用例。已有 Logo 放入页头；只有必要时才添加一到两张 Mermaid。
- **审查**：扫描仓库，在干净环境验证安装与首个使用步骤，逐项核对主张，再按读者决策重排正文。
- **优化**：冻结项目故事与视觉规格，把需要保留的 Mermaid 替换为静态 SVG，补上图下说明并检查手机显示。

无现成 README 时按创建→审查→优化执行；已有 README 跳过创建。完整流程已授权改写，单独审查仍先诊断、后确认。

审查包含五项阻断和八项计分：身份、首步、主张、状态、许可证全部通过，且得分至少 **14/16**，再通过冷读者五问，才可声明通过。机械脚本不自动打分，未知事实会降级或删除并记入记分卡。

## 机制与输出

![readmex 结构：SKILL 入口选择流水线，流水线按需调用核验与渲染工具](readme/assets/architecture.svg)

`SKILL.md` 负责路由、开场提问和目录约定；`pipelines/` 描述三条任务；`scripts/` 与渲染器提供机械检查和素材生产。它是交给 AI 执行的技能，不是单条命令即可完成写作的 CLI。

```text
<target>/
├── README.md          # 最终正文
├── readme/assets/     # 正文引用的素材，随仓库提交
└── .readmex/          # 扫描、记分卡、源 JSON 与预览，加入 .gitignore
```

默认使用自带浅色背景的 SVG。源码引用核验当前文件与行号；需要固定提交时也可按提交核验。必要信息始终留在 Markdown，图片失效时仍可读。

明确同意后，GIF 仅用于头图和流程图，并保留同名 SVG。依赖为 Pillow、ffmpeg，以及 `rsvg-convert` 或 macOS `sips`；缺依赖时按平台安装，失败则跳过 GIF。生图单独征得同意，合成后的素材发布为 PNG。

进一步阅读：[技能入口](skills/readmex/SKILL.md) · [审查尺度](skills/readmex/references/review-scorecard.md) · [图表写作与渲染](skills/readmex/references/renderer-authoring.md)。

[MIT 许可证](LICENSE.txt) · [第三方许可通知](skills/readmex/THIRD_PARTY_NOTICES)
