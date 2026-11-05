# README 动画制作

精选自 oil-oil 的 GitHub-safe README motion。入口已确认 GIF 许可；未明确同意就只做静态 SVG。GIF 仅用于 `hero` 与 `workflow`，说明真实的序列、关系或状态改变，且保留同名静态 SVG。

## 动作与规格

从验收过的静态 SVG 开始，只动一到三处有意义的层。进入距离约画布的 4–8%，约 0.7–1.2 秒缓出，停留 1.5–2.5 秒供阅读，再短暂退出返回首帧。停留时像素稳定，避免悬浮、弹跳、闪烁和无意义脉冲。默认从 1200 宽、30 FPS、4–6 秒、192 色、无抖动开始，渐变或 prominent text 可用 256 色。

为动画层设置稳定的 SVG `id`，字体与继承变换可放祖先 group。动画 JSON 存为 `.readmex/optimize/motion/hero.json` 或 `workflow.json`：

```json
{
  "width": 1200,
  "fps": 30,
  "duration": 5.0,
  "colors": 192,
  "dither": "none",
  "clip_to_base_alpha": true,
  "max_size_mb": 2.0,
  "reveals": [
    {"id": "main-flow", "axis": "x", "start": 0.25, "end": 1.25,
     "exit": {"start": 4.1, "end": 4.96}}
  ],
  "layers": [
    {"id": "result", "enter": {"start": 0.4, "end": 1.3, "from": [48, 0]},
     "exit": {"start": 4.1, "end": 4.96, "to": [20, 0]}}
  ]
}
```

位移使用 SVG 坐标，随输出宽度缩放。移动对象有圆角外框时用 `clip_to_base_alpha: true`，保持透明轮廓稳定，避免 GIF 解码残影。保留透明孔洞的素材不应盲目打开这一项。透明键色必须没有出现在可见内容中；脚本遇到冲突或轮廓不稳定时失败，不发布有孔洞的动图。

## 依赖与调用

```bash
python3 <skill>/scripts/render_motion_gif.py <target>/readme/assets/hero.svg <target>/readme/assets/hero.gif --spec <target>/.readmex/optimize/motion/hero.json
```

脚本检查 Pillow、ffmpeg 和 `rsvg-convert` / macOS `sips` 二选一：Pillow 使用当前 Python 的 `pip install --user Pillow`；macOS 用 brew 安装缺少的 ffmpeg / librsvg；Linux 用 apt-get 安装 ffmpeg / librsvg2-bin。需要 sudo 时，仅在用户自己的交互终端确认密码，模型不读取或填写密码；无交互终端或安装失败时跳过 GIF。macOS 的 sips 是系统工具，不尝试单独安装；可用 sips 时不必安装 librsvg。

退出码 `0` 表示成功，`3` 表示缺依赖或依赖安装失败而跳过，其他非零表示素材、规格或渲染失败。跳过时保留静态 SVG，最终报告具体原因。`--no-install` 仅用于已有依赖的离线验证或测试，正式启用 GIF 时默认自动补依赖。

逐层 SVG、PNG 帧和调色板使用临时目录，成功与失败都会删除。编码到临时 GIF，通过核验后才替换发布文件；失败不覆盖既有 GIF。

## 验收与大小

全局调色板和矩形增量编码控制体积；无抖动适合纯色、文字和 UI。不要移动整个背景或不断改变渐变，静止帧一致压缩最好。目标约 2 MB，实际接近 5 MB 时简化动作、缩短时长或改用静态头图与更小的流程 GIF。

检查进入、首次停留、整个停留、退出与循环边界，900/360 宽均可读。用 ffprobe 检查帧数、FPS、时长、尺寸和体积；透明边角与轮廓稳定性也要检查。正文说明和静态 SVG 始终提供完整信息。
