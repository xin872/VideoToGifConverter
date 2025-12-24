# 视频转 GIF 转换器

一个简洁易用的 Windows 桌面应用程序，用于将视频文件转换为优化的 GIF 动画。

## 功能特点

- ✨ **简洁的 GUI 界面**：基于 Tkinter 的现代化界面
- 📊 **实时进度显示**：进度条和百分比显示转换进度
- 📝 **详细日志输出**：实时显示 FFmpeg 转换日志
- 🔄 **后台转换**：使用多线程，界面不卡顿
- 🎯 **智能优化**：使用优化的 FFmpeg 参数生成小体积高质量 GIF
- 📦 **一键打包**：支持 PyInstaller 打包为独立可执行文件

## 系统要求

- Windows 7 或更高版本
- Python 3.6+ （开发环境）
- FFmpeg 可执行文件

## 快速开始

### 方式一：直接运行 Python 脚本

1. **安装 Python**（如果尚未安装）
   - 从 [python.org](https://www.python.org/downloads/) 下载并安装

2. **准备 FFmpeg**
   - 将 `ffmpeg.exe` 放在与脚本相同的目录下
   - 或者放在 `ffmpeg/bin/` 子目录中

3. **运行程序**
   ```bash
   python video_to_gif_converter.py
   ```

### 方式二：使用打包的可执行文件

1. **打包程序**
   ```bash
   # 安装 PyInstaller
   pip install -r requirements.txt
   
   # 运行打包脚本
   build.bat
   ```

2. **运行程序**
   - 打包完成后，在 `dist` 目录下找到 `VideoToGifConverter.exe`
   - 确保 `ffmpeg.exe` 与 `VideoToGifConverter.exe` 在同一目录
   - 双击运行

## 使用说明

1. **选择视频**
   - 点击"选择视频"按钮
   - 选择要转换的视频文件（支持 MP4, AVI, MKV, MOV 等格式）

2. **开始转换**
   - 点击"开始转换"按钮
   - 程序会自动分析视频时长并开始转换
   - 实时进度条显示转换进度

3. **查看结果**
   - 转换完成后会弹出提示框
   - 可选择直接打开文件所在文件夹
   - GIF 文件与原视频在同一目录，文件名相同（扩展名为 .gif）

## 转换参数说明

程序使用以下 FFmpeg 参数进行转换：

```bash
ffmpeg -i input.mkv \
  -vf "fps=8,scale=240:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=16[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3" \
  output.gif
```

参数解释：
- `fps=8`：设置帧率为 8 FPS（降低文件大小）
- `scale=240:-1`：缩放宽度为 240px，高度自动计算
- `flags=lanczos`：使用高质量的 Lanczos 缩放算法
- `palettegen=max_colors=16`：生成 16 色调色板（减小文件大小）
- `paletteuse=dither=bayer:bayer_scale=3`：使用 Bayer 抖动算法优化色彩

## 项目结构

```
video/
├── video_to_gif_converter.py  # 主程序
├── requirements.txt            # Python 依赖
├── build.bat                   # 打包脚本
├── README.md                   # 说明文档
└── ffmpeg.exe                  # FFmpeg 可执行文件（需自行下载）
```

## 技术细节

### 进度条实现原理

1. **获取视频时长**
   - 使用 `ffmpeg -i` 命令获取视频信息
   - 从 stderr 输出中解析 `Duration` 字段
   - 格式：`Duration: HH:MM:SS.ms`

2. **解析转换进度**
   - 实时读取 FFmpeg 的 stderr 输出
   - 使用正则表达式匹配 `time=HH:MM:SS.ms` 字段
   - 计算当前时间与总时长的比例

3. **更新 GUI**
   - 在后台线程中执行转换
   - 使用 `root.after()` 在主线程中更新 GUI
   - 避免界面冻结

### PyInstaller 兼容性

- 使用 `sys.frozen` 检测打包环境
- 正确处理打包后的文件路径
- 使用 `--onefile` 和 `--windowed` 参数

## 常见问题

**Q: 提示找不到 ffmpeg.exe？**  
A: 请确保 ffmpeg.exe 与程序在同一目录下。

**Q: 转换速度很慢？**  
A: 这是正常的，GIF 转换需要生成调色板并进行抖动处理。视频越长，转换时间越长。

**Q: 生成的 GIF 文件很大？**  
A: 可以尝试：
- 减少帧率（修改 `fps=8` 为更小的值）
- 缩小尺寸（修改 `scale=240` 为更小的值）
- 减少颜色数（修改 `max_colors=16` 为更小的值）

**Q: Windows 提示安全警告？**  
A: 这是因为可执行文件没有数字签名。选择"仍要运行"即可。

## 许可证

本项目仅供学习和个人使用。

## 致谢

- [FFmpeg](https://ffmpeg.org/) - 强大的多媒体处理工具
- [Tkinter](https://docs.python.org/3/library/tkinter.html) - Python 标准 GUI 库
- [PyInstaller](https://www.pyinstaller.org/) - Python 打包工具
