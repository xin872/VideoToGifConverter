@echo off
REM 视频转 GIF 转换器打包脚本
REM 使用 PyInstaller 将 Python 脚本打包为 Windows 可执行文件

echo ======================================
echo 视频转 GIF 转换器 - 打包脚本
echo ======================================
echo.

REM 检查是否安装了 PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [错误] 未检测到 PyInstaller，正在安装...
    pip install pyinstaller
    if errorlevel 1 (
        echo [错误] PyInstaller 安装失败！
        pause
        exit /b 1
    )
)

echo [1/3] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

echo.
echo [2/3] 开始打包应用程序...
echo.

REM PyInstaller 打包命令
REM --onefile: 打包成单个 exe 文件
REM --windowed: 不显示控制台窗口（GUI 应用）
REM --name: 指定输出文件名
REM --icon: 指定图标（可选，如果有 .ico 文件）
REM --add-data: 添加额外文件（如果需要）

pyinstaller --onefile ^
    --windowed ^
    --name "VideoToGifConverter" ^
    video_to_gif_converter.py

if errorlevel 1 (
    echo.
    echo [错误] 打包失败！
    pause
    exit /b 1
)

echo.
echo [3/3] 复制 ffmpeg.exe 到输出目录...

REM 查找 ffmpeg.exe
if exist ffmpeg.exe (
    copy ffmpeg.exe dist\ffmpeg.exe
    echo 已复制 ffmpeg.exe
) else if exist ffmpeg\bin\ffmpeg.exe (
    copy ffmpeg\bin\ffmpeg.exe dist\ffmpeg.exe
    echo 已从 ffmpeg\bin 复制 ffmpeg.exe
) else (
    echo.
    echo [警告] 未找到 ffmpeg.exe！
    echo 请手动将 ffmpeg.exe 复制到 dist 目录下
    echo.
)

echo.
echo ======================================
echo 打包完成！
echo ======================================
echo.
echo 可执行文件位置: dist\VideoToGifConverter.exe
echo.
echo 注意事项：
echo 1. 请确保 ffmpeg.exe 与 VideoToGifConverter.exe 在同一目录
echo 2. 首次运行时，Windows 可能会显示安全警告，请选择"仍要运行"
echo 3. 如需分发，请将 dist 文件夹中的所有文件一起打包
echo.

pause
