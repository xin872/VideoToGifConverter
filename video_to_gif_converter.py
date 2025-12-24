#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GIF Converter
现代化视频转 GIF 转换器 - 带视频预览功能
使用 CustomTkinter 打造的美观界面

依赖安装:
pip install customtkinter
pip install opencv-python
pip install Pillow
"""

import os
import sys
import re
import subprocess
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox, Canvas
from pathlib import Path

# 尝试导入视频播放器依赖
try:
    import cv2
    from PIL import Image, ImageTk
    VIDEO_PLAYER_AVAILABLE = True
except ImportError:
    VIDEO_PLAYER_AVAILABLE = False
    print("=" * 60)
    print("⚠️  警告: opencv-python 或 Pillow 未安装")
    print("=" * 60)
    print("视频预览功能将不可用。")
    print("请运行以下命令安装:")
    print("    pip install opencv-python Pillow")
    print("=" * 60)


class VideoPreviewPlayer:
    """自定义视频播放器 - 使用 OpenCV 和 PIL"""
    
    def __init__(self, canvas, width=800, height=400):
        """初始化视频播放器
        
        Args:
            canvas: tkinter Canvas 组件
            width: 显示宽度
            height: 显示高度
        """
        self.canvas = canvas
        self.display_width = width
        self.display_height = height
        
        # 视频相关
        self.cap = None
        self.video_path = None
        self.fps = 30
        self.total_frames = 0
        self.duration = 0
        
        # 播放控制
        self.is_playing = False
        self.current_frame = 0
        self.update_job = None
        
        # 用于保持图像引用
        self.current_photo = None
    
    def load(self, video_path):
        """加载视频文件
        
        Args:
            video_path: 视频文件路径
        """
        # 释放之前的视频
        if self.cap is not None:
            self.cap.release()
        
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        
        if not self.cap.isOpened():
            raise Exception(f"无法打开视频文件: {video_path}")
        
        # 获取视频信息
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps <= 0:
            self.fps = 30  # 默认帧率
        
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.fps if self.fps > 0 else 0
        
        # 重置状态
        self.current_frame = 0
        self.is_playing = False
        
        # 显示第一帧
        self.seek(0)
    
    def play(self):
        """开始/继续播放"""
        if not self.cap or not self.cap.isOpened():
            return
        
        self.is_playing = True
        self._update_frame()
    
    def pause(self):
        """暂停播放"""
        self.is_playing = False
        if self.update_job:
            self.canvas.after_cancel(self.update_job)
            self.update_job = None
    
    def stop(self):
        """停止播放（暂停的别名，用于兼容）"""
        self.pause()
    
    def seek(self, frame_number):
        """跳转到指定帧
        
        Args:
            frame_number: 目标帧号
        """
        if not self.cap or not self.cap.isOpened():
            return
        
        # 限制范围
        frame_number = max(0, min(frame_number, self.total_frames - 1))
        
        # 设置位置
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        self.current_frame = frame_number
        
        # 读取并显示该帧
        ret, frame = self.cap.read()
        if ret:
            self._display_frame(frame)
    
    def seek_to_time(self, seconds):
        """跳转到指定时间
        
        Args:
            seconds: 目标时间（秒）
        """
        frame_number = int(seconds * self.fps)
        self.seek(frame_number)
    
    def current_duration(self):
        """获取当前播放时间（秒）
        
        Returns:
            当前时间（秒）
        """
        if self.fps > 0:
            return self.current_frame / self.fps
        return 0
    
    def _update_frame(self):
        """更新帧（内部方法）"""
        if not self.is_playing or not self.cap or not self.cap.isOpened():
            return
        
        ret, frame = self.cap.read()
        
        if ret:
            self._display_frame(frame)
            self.current_frame += 1
            
            # 检查是否到达结尾
            if self.current_frame >= self.total_frames:
                self.is_playing = False
                return
            
            # 计算下一帧的延迟
            delay = int(1000 / self.fps)
            self.update_job = self.canvas.after(delay, self._update_frame)
        else:
            # 读取失败，停止播放
            self.is_playing = False
    
    def _display_frame(self, frame):
        """显示帧到 Canvas
        
        Args:
            frame: OpenCV 读取的帧 (BGR 格式)
        """
        # BGR -> RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 获取原始尺寸
        h, w = frame_rgb.shape[:2]
        
        # 计算缩放比例以适应显示区域（保持宽高比）
        scale_w = self.display_width / w
        scale_h = self.display_height / h
        scale = min(scale_w, scale_h)
        
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # 调整大小
        frame_resized = cv2.resize(frame_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # 转换为 PIL Image
        image = Image.fromarray(frame_resized)
        
        # 转换为 ImageTk
        photo = ImageTk.PhotoImage(image=image)
        
        # 清空 Canvas
        self.canvas.delete("all")
        
        # 居中显示
        x = (self.display_width - new_w) // 2
        y = (self.display_height - new_h) // 2
        
        # 在 Canvas 上显示
        self.canvas.create_image(x, y, anchor='nw', image=photo)
        
        # 保持引用，防止被垃圾回收
        self.current_photo = photo
    
    def release(self):
        """释放资源"""
        self.pause()
        if self.cap:
            self.cap.release()
            self.cap = None



class ModernGifConverter:
    """现代化 GIF 转换器主类"""
    
    def __init__(self, root):
        """初始化应用程序"""
        self.root = root
        self.root.title("GIF Converter")
        
        # 设置窗口大小（优化布局）
        window_width = 900
        window_height = 950
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(True, True)  # 允许调整大小
        self.root.minsize(850, 900)  # 设置最小尺寸
        
        # 设置主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 状态变量
        self.is_converting = False
        self.input_file = None
        self.output_file = None
        self.total_duration = 0
        self.is_playing = False
        self.video_player = None
        self.is_seeking = False  # 拖动进度条标志
        self.was_playing_before_seek = False  # 拖动前的播放状态
        self.pause_position = 0  # 暂停时的位置
        
        # 创建 GUI
        self.create_widgets()
        
        # 检测 FFmpeg（在 GUI 创建后）
        self.ffmpeg_path = self.detect_ffmpeg()
        
        # 启动视频进度更新循环
        if VIDEO_PLAYER_AVAILABLE:
            self.start_video_progress_update()
    
    def detect_ffmpeg(self):
        """检测 FFmpeg 可执行文件
        
        优先级：
        1. 程序同级目录下的 ffmpeg.exe
        2. 系统 PATH 中的 ffmpeg
        
        Returns:
            str: FFmpeg 的完整路径或命令名，如果未找到则返回 None
        """
        # 获取程序运行的根目录
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        # 1. 首先检查程序同级目录
        local_ffmpeg = os.path.join(base_path, "ffmpeg.exe")
        if os.path.exists(local_ffmpeg):
            if hasattr(self, 'log_text'):
                self.log(f"✓ 找到 FFmpeg: {local_ffmpeg}")
            return local_ffmpeg
        
        # 2. 尝试使用系统 PATH 中的 ffmpeg
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode == 0:
                if hasattr(self, 'log_text'):
                    self.log("✓ 使用系统 PATH 中的 FFmpeg")
                return "ffmpeg"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # 3. 都找不到，显示错误提示
        error_msg = (
            f"未找到 ffmpeg.exe！\n\n"
            f"请确保 ffmpeg.exe 与本软件放在同一个文件夹内：\n"
            f"{base_path}\n\n"
            f"或者在系统中安装 FFmpeg 并添加到 PATH 环境变量。"
        )
        messagebox.showerror("FFmpeg 未找到", error_msg)
        return None
    
    def validate_number(self, value):
        """验证输入是否为有效数字"""
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def create_widgets(self):
        """创建 GUI 组件"""
        
        # ===== 顶部标题区域 =====
        header_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(10, 5))  # 减小间距
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🎬 GIF Converter",
            font=ctk.CTkFont(size=20, weight="bold"),  # 减小字体
            text_color=("#1f6aa5", "#4a9eff")
        )
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="视频预览 · 交互式裁剪 · 高质量转换",
            font=ctk.CTkFont(size=10),  # 减小字体
            text_color="gray"
        )
        subtitle_label.pack(pady=(2, 0))
        
        separator = ctk.CTkFrame(header_frame, height=1, fg_color=("#d0d0d0", "#3a3a3a"))  # 减小高度
        separator.pack(fill="x", pady=(5, 0))
        
        # ===== 文件选择区域 =====
        file_card = ctk.CTkFrame(self.root, corner_radius=8)
        file_card.pack(fill="x", padx=20, pady=(0, 8))  # 减小间距
        
        file_inner = ctk.CTkFrame(file_card, fg_color="transparent")
        file_inner.pack(fill="x", padx=12, pady=10)  # 减小内边距
        
        file_header = ctk.CTkLabel(
            file_inner,
            text="📁 选择视频文件",
            font=ctk.CTkFont(size=11, weight="bold"),  # 减小字体
            anchor="w"
        )
        file_header.pack(fill="x", pady=(0, 5))  # 减小间距
        
        self.file_label = ctk.CTkLabel(
            file_inner,
            text="未选择文件",
            font=ctk.CTkFont(size=11),  # 减小字体
            anchor="w",
            text_color="gray"
        )
        self.file_label.pack(fill="x", pady=(0, 8))  # 减小间距
        
        select_btn = ctk.CTkButton(
            file_inner,
            text="浏览文件",
            command=self.select_file,
            height=32,  # 减小高度
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),  # 减小字体
            fg_color=("#2fa572", "#2fa572"),
            hover_color=("#26865f", "#26865f")
        )
        select_btn.pack(fill="x")
        
        # ===== 视频预览区域 =====
        if VIDEO_PLAYER_AVAILABLE:
            preview_card = ctk.CTkFrame(self.root, corner_radius=8)
            preview_card.pack(fill="x", padx=20, pady=(0, 8))  # 减小间距
            
            preview_inner = ctk.CTkFrame(preview_card, fg_color="transparent")
            preview_inner.pack(fill="x", padx=12, pady=10)  # 减小内边距
            
            preview_header = ctk.CTkLabel(
                preview_inner,
                text="🎥 视频预览",
                font=ctk.CTkFont(size=11, weight="bold"),  # 减小字体
                anchor="w"
            )
            preview_header.pack(fill="x", pady=(0, 6))  # 减小间距
            
            # 视频播放器容器（黑色背景，固定高度）
            video_container = ctk.CTkFrame(
                preview_inner,
                fg_color="black",
                corner_radius=8,
                height=220  # 进一步减小高度
            )
            video_container.pack(fill="x", pady=(0, 8))  # 减小间距
            video_container.pack_propagate(False)
            
            # Canvas 用于显示视频帧
            self.video_canvas = Canvas(
                video_container,
                bg="black",
                highlightthickness=0
            )
            self.video_canvas.pack(fill="both", expand=True, padx=2, pady=2)
            
            # 初始化自定义视频播放器
            canvas_width = 860
            canvas_height = 216  # 匹配新的容器高度 (220 - 4px padding)
            self.video_player = VideoPreviewPlayer(
                self.video_canvas,
                width=canvas_width,
                height=canvas_height
            )

            
            # 播放控制区域
            controls_frame = ctk.CTkFrame(preview_inner, fg_color="transparent")
            controls_frame.pack(fill="x")
            
            # 进度条（不使用 command，改用事件绑定）
            self.video_progress_slider = ctk.CTkSlider(
                controls_frame,
                from_=0,
                to=1,
                height=18,
                button_length=20
            )
            self.video_progress_slider.pack(fill="x", pady=(0, 10))
            self.video_progress_slider.set(0)
            
            # 绑定拖动事件
            self.video_progress_slider.bind("<ButtonPress-1>", self.on_slider_press)
            self.video_progress_slider.bind("<ButtonRelease-1>", self.on_slider_release)
            self.video_progress_slider.bind("<B1-Motion>", self.on_slider_drag)
            
            # 播放控制栏
            playback_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
            playback_frame.pack(fill="x")
            
            # 左侧：播放按钮和时间
            left_controls = ctk.CTkFrame(playback_frame, fg_color="transparent")
            left_controls.pack(side="left", fill="x", expand=True)
            
            self.play_btn = ctk.CTkButton(
                left_controls,
                text="▶️ 播放",
                command=self.toggle_play_pause,
                width=110,
                height=35,
                corner_radius=8,
                font=ctk.CTkFont(size=13, weight="bold"),
                state="disabled"
            )
            self.play_btn.pack(side="left")
            
            self.time_label = ctk.CTkLabel(
                left_controls,
                text="00:00 / 00:00",
                font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
                text_color=("#1f6aa5", "#4a9eff")
            )
            self.time_label.pack(side="left", padx=(15, 0))
            
            # 右侧：裁剪快捷按钮
            right_controls = ctk.CTkFrame(playback_frame, fg_color="transparent")
            right_controls.pack(side="right")
            
            self.set_start_btn = ctk.CTkButton(
                right_controls,
                text="📍 设为起点",
                command=self.set_start_point,
                width=110,
                height=35,
                corner_radius=8,
                font=ctk.CTkFont(size=12),
                fg_color=("#1f6aa5", "#1f6aa5"),
                hover_color=("#174e7c", "#174e7c"),
                state="disabled"
            )
            self.set_start_btn.pack(side="left", padx=(0, 8))
            
            self.set_end_btn = ctk.CTkButton(
                right_controls,
                text="🎯 设为终点",
                command=self.set_end_point,
                width=110,
                height=35,
                corner_radius=8,
                font=ctk.CTkFont(size=12),
                fg_color=("#1f6aa5", "#1f6aa5"),
                hover_color=("#174e7c", "#174e7c"),
                state="disabled"
            )
            self.set_end_btn.pack(side="left")
        
        # ===== 裁剪参数设置 =====
        trim_card = ctk.CTkFrame(self.root, corner_radius=8)
        trim_card.pack(fill="x", padx=20, pady=(0, 8))  # 减小间距
        
        trim_inner = ctk.CTkFrame(trim_card, fg_color="transparent")
        trim_inner.pack(fill="x", padx=12, pady=10)  # 减小内边距
        
        trim_header = ctk.CTkLabel(
            trim_inner,
            text="✂️ 裁剪设置",
            font=ctk.CTkFont(size=11, weight="bold"),  # 减小字体
            anchor="w"
        )
        trim_header.pack(fill="x", pady=(0, 6))  # 减小间距
        
        # 裁剪参数输入
        vcmd = (self.root.register(self.validate_number), '%P')
        
        params_frame = ctk.CTkFrame(trim_inner, fg_color="transparent")
        params_frame.pack(fill="x")
        
        # 左列：跳过片头
        left_col = ctk.CTkFrame(params_frame, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 6))  # 减小间距
        
        skip_start_label = ctk.CTkLabel(
            left_col,
            text="跳过片头 (秒)",
            font=ctk.CTkFont(size=10),  # 减小字体
            anchor="w"
        )
        skip_start_label.pack(fill="x", pady=(0, 4))  # 减小间距
        
        self.skip_start_entry = ctk.CTkEntry(
            left_col,
            height=30,  # 减小高度
            corner_radius=6,
            font=ctk.CTkFont(size=11),  # 减小字体
            validate='key',
            validatecommand=vcmd
        )
        self.skip_start_entry.insert(0, "0")
        self.skip_start_entry.pack(fill="x")
        
        # 右列：去除片尾
        right_col = ctk.CTkFrame(params_frame, fg_color="transparent")
        right_col.pack(side="left", fill="both", expand=True, padx=(6, 0))  # 减小间距
        
        skip_end_label = ctk.CTkLabel(
            right_col,
            text="去除片尾 (秒)",
            font=ctk.CTkFont(size=10),  # 减小字体
            anchor="w"
        )
        skip_end_label.pack(fill="x", pady=(0, 4))  # 减小间距
        
        self.skip_end_entry = ctk.CTkEntry(
            right_col,
            height=30,  # 减小高度
            corner_radius=6,
            font=ctk.CTkFont(size=11),  # 减小字体
            validate='key',
            validatecommand=vcmd
        )
        self.skip_end_entry.insert(0, "0")
        self.skip_end_entry.pack(fill="x")
        
        # ===== 转换按钮 =====
        convert_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        convert_frame.pack(fill="x", padx=20, pady=(0, 8))  # 减小间距
        
        self.convert_btn = ctk.CTkButton(
            convert_frame,
            text="🚀 开始转换",
            command=self.start_conversion,
            state="disabled",
            height=38,  # 减小高度
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),  # 减小字体
            fg_color=("#1f6aa5", "#1f6aa5"),
            hover_color=("#174e7c", "#174e7c")
        )
        self.convert_btn.pack(fill="x")
        
        # ===== 转换进度 =====
        progress_card = ctk.CTkFrame(self.root, corner_radius=8)
        progress_card.pack(fill="x", padx=20, pady=(0, 8))  # 减小间距
        
        progress_inner = ctk.CTkFrame(progress_card, fg_color="transparent")
        progress_inner.pack(fill="x", padx=12, pady=10)  # 减小内边距
        
        progress_header = ctk.CTkLabel(
            progress_inner,
            text="📊 转换进度",
            font=ctk.CTkFont(size=11, weight="bold"),  # 减小字体
            anchor="w"
        )
        progress_header.pack(fill="x", pady=(0, 6))  # 减小间距
        
        self.conversion_progress_bar = ctk.CTkProgressBar(
            progress_inner,
            height=8,  # 减小高度
            corner_radius=4
        )
        self.conversion_progress_bar.set(0)
        self.conversion_progress_bar.pack(fill="x", pady=(0, 5))  # 减小间距
        
        self.conversion_progress_label = ctk.CTkLabel(
            progress_inner,
            text="0%",
            font=ctk.CTkFont(size=12, weight="bold"),  # 减小字体
            text_color=("#1f6aa5", "#4a9eff")
        )
        self.conversion_progress_label.pack()
        
        # ===== 执行日志 =====
        log_card = ctk.CTkFrame(self.root, corner_radius=8)
        log_card.pack(fill="both", expand=True, padx=20, pady=(0, 15))  # 减小间距
        
        log_inner = ctk.CTkFrame(log_card, fg_color="transparent")
        log_inner.pack(fill="both", expand=True, padx=12, pady=10)  # 减小内边距
        
        log_header = ctk.CTkLabel(
            log_inner,
            text="📝 执行日志",
            font=ctk.CTkFont(size=11, weight="bold"),  # 减小字体
            anchor="w"
        )
        log_header.pack(fill="x", pady=(0, 5))  # 减小间距
        
        self.log_text = ctk.CTkTextbox(
            log_inner,
            height=80,  # 减小高度
            corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=9),  # 减小字体
            wrap="none",
            activate_scrollbars=True
        )
        self.log_text.pack(fill="both", expand=True)
        
        self.log_line_count = 0
        self.max_log_lines = 500
    
    def select_file(self):
        """选择视频文件"""
        filetypes = (
            ("视频文件", "*.mp4 *.avi *.mkv *.mov *.flv *.wmv *.webm"),
            ("所有文件", "*.*")
        )
        
        filename = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=filetypes
        )
        
        if filename:
            self.input_file = filename
            self.file_label.configure(
                text=os.path.basename(filename),
                text_color=("black", "white")
            )
            self.convert_btn.configure(state="normal")
            self.log(f"✓ 已选择文件: {filename}")
            
            # 立即加载视频到预览器
            if VIDEO_PLAYER_AVAILABLE and self.video_player:
                self.load_video_preview(filename)
            
            # 获取视频时长
            self.get_video_duration(filename)
    
    def load_video_preview(self, video_path):
        """加载视频到预览器"""
        try:
            self.video_player.load(video_path)
            
            # 从播放器获取视频时长（更准确）
            if self.video_player.duration > 0:
                self.total_duration = self.video_player.duration
                self.log(f"✓ 视频已加载到预览器 (时长: {self.format_time(self.total_duration)})")
            else:
                self.log("✓ 视频已加载到预览器")
            
            # 启用播放控制
            self.play_btn.configure(state="normal")
            self.set_start_btn.configure(state="normal")
            self.set_end_btn.configure(state="normal")
            
        except Exception as e:
            self.log(f"⚠️ 加载视频预览失败: {str(e)}")
            self.log("   提示: 某些视频格式可能不支持预览，但仍可以转换")
    
    def toggle_play_pause(self):
        """切换播放/暂停（标准播放器行为）"""
        if not self.video_player:
            return
        
        try:
            if self.is_playing:
                # 暂停：使用 pause() 保持画面
                current = self.video_player.current_duration()
                if current is not None:
                    self.pause_position = current
                else:
                    self.pause_position = 0
                
                self.video_player.pause()
                self.play_btn.configure(text="▶️ 播放")
                self.is_playing = False
                self.log(f"⏸️ 已暂停在 {self.format_time(self.pause_position)}")
                
            else:
                # 播放：直接调用 play() 继续
                self.video_player.play()
                self.play_btn.configure(text="⏸️ 暂停")
                self.is_playing = True
                self.log(f"▶️ 继续播放")
                    
        except Exception as e:
            self.log(f"⚠️ 播放控制错误: {str(e)}")
            # 如果出错，尝试重新加载
            if self.input_file:
                try:
                    self.video_player.load(self.input_file)
                    if self.pause_position > 0:
                        self.video_player.seek(int(self.pause_position))
                    self.video_player.play()
                    self.play_btn.configure(text="⏸️ 暂停")
                    self.is_playing = True
                except Exception as e2:
                    self.log(f"⚠️ 重新加载失败: {str(e2)}")
    
    def on_slider_press(self, event):
        """开始拖动进度条"""
        self.is_seeking = True
        # 记录拖动前的播放状态
        self.was_playing_before_seek = self.is_playing
        # 暂停视频（不使用 stop，保持画面）
        if self.is_playing:
            # 记录当前位置
            current = self.video_player.current_duration()
            if current is not None:
                self.pause_position = current
            self.video_player.pause()
            self.is_playing = False
    
    def on_slider_drag(self, event):
        """拖动进度条中（实时显示时间和预览帧）"""
        if self.total_duration > 0 and self.video_player:
            # 获取当前滑块值
            slider_value = self.video_progress_slider.get()
            seek_time = slider_value * self.total_duration
            
            # 实时更新时间显示
            self.time_label.configure(
                text=f"{self.format_time(seek_time)} / {self.format_time(self.total_duration)}"
            )
            
            # 实时预览帧（每隔一定距离才更新，避免过于频繁）
            if hasattr(self, '_last_drag_time'):
                import time
                current_time = time.time()
                if current_time - self._last_drag_time < 0.05:  # 50ms 节流
                    return
                self._last_drag_time = current_time
            else:
                import time
                self._last_drag_time = time.time()
            
            # 跳转到拖动位置显示帧
            frame_number = int(slider_value * self.video_player.total_frames)
            self.video_player.seek(frame_number)
    
    def on_slider_release(self, event):
        """释放进度条（跳转到拖动位置）"""
        if self.video_player and self.total_duration > 0:
            # 获取目标时间和帧号
            slider_value = self.video_progress_slider.get()
            seek_time = slider_value * self.total_duration
            frame_number = int(slider_value * self.video_player.total_frames)
            
            try:
                # 跳转到目标帧
                self.video_player.seek(frame_number)
                
                # 更新暂停位置
                self.pause_position = seek_time
                
                self.log(f"⏩ 跳转到 {self.format_time(seek_time)}")
                
                # 恢复播放状态
                if self.was_playing_before_seek:
                    # 之前在播放，继续播放
                    self.video_player.play()
                    self.is_playing = True
                    self.play_btn.configure(text="⏸️ 暂停")
                else:
                    # 之前是暂停，保持暂停状态
                    self.is_playing = False
                    self.play_btn.configure(text="▶️ 播放")
                    
            except Exception as e:
                self.log(f"⚠️ 跳转失败: {str(e)}")
        
        # 结束拖动
        self.is_seeking = False
    

    
    def start_video_progress_update(self):
        """启动视频进度更新循环"""
        def update():
            # 只在播放且未拖动时更新
            if self.is_playing and self.video_player and self.total_duration > 0 and not self.is_seeking:
                try:
                    current = self.video_player.current_duration()
                    if current is not None:
                        # 检查是否播放到末尾
                        if current >= self.total_duration - 0.5:
                            # 视频结束
                            self.on_video_end()
                        else:
                            # 更新进度条
                            self.video_progress_slider.set(current / self.total_duration)
                            # 更新时间显示
                            self.time_label.configure(
                                text=f"{self.format_time(current)} / {self.format_time(self.total_duration)}"
                            )
                except:
                    pass
            self.root.after(100, update)
        update()
    
    def on_video_end(self):
        """视频播放结束"""
        self.is_playing = False
        self.play_btn.configure(text="▶️ 播放")
        # 进度条设为 100%
        self.video_progress_slider.set(1.0)
        self.time_label.configure(
            text=f"{self.format_time(self.total_duration)} / {self.format_time(self.total_duration)}"
        )
    
    def format_time(self, seconds):
        """格式化时间为 MM:SS"""
        if seconds is None:
            return "00:00"
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def set_start_point(self):
        """设置起点（当前播放位置）"""
        if not self.video_player:
            return
        
        try:
            current_time = self.video_player.current_duration()
            self.log(f"🔍 调试: 当前时间 = {current_time:.2f} 秒, 当前帧 = {self.video_player.current_frame}")
            
            if current_time is not None and current_time >= 0:
                self.skip_start_entry.delete(0, "end")
                self.skip_start_entry.insert(0, str(int(current_time)))
                self.log(f"✂️ 起点设为: {current_time:.2f} 秒")
            else:
                self.log("⚠️ 无法获取当前播放位置")
        except Exception as e:
            self.log(f"⚠️ 设置起点失败: {str(e)}")
    
    def set_end_point(self):
        """设置终点（当前播放位置）"""
        if not self.video_player or self.total_duration == 0:
            return
        
        try:
            current_time = self.video_player.current_duration()
            self.log(f"🔍 调试: 当前时间 = {current_time:.2f} 秒, 总时长 = {self.total_duration:.2f} 秒")
            
            if current_time is not None and current_time >= 0:
                # 计算去除片尾的秒数
                skip_end = self.total_duration - current_time
                if skip_end >= 0:
                    self.skip_end_entry.delete(0, "end")
                    self.skip_end_entry.insert(0, str(int(skip_end)))
                    self.log(f"✂️ 终点设为: {current_time:.2f} 秒 (去除片尾 {skip_end:.2f} 秒)")
                else:
                    self.log("⚠️ 当前位置超过视频总时长")
            else:
                self.log("⚠️ 无法获取当前播放位置")
        except Exception as e:
            self.log(f"⚠️ 设置终点失败: {str(e)}")
    
    def log(self, message):
        """添加日志消息"""
        self.log_text.insert("end", message + "\n")
        self.log_line_count += 1
        
        # 限制日志行数
        if self.log_line_count > self.max_log_lines:
            self.log_text.delete("1.0", "101.0")
            self.log_line_count -= 100
        
        self.log_text.see("end")
        self.root.update_idletasks()
    
    def log_line(self, line):
        """添加单行日志（FFmpeg 输出）"""
        if not line.strip():
            return
        
        self.log_text.insert("end", line + "\n")
        self.log_line_count += 1
        
        if self.log_line_count > self.max_log_lines:
            self.log_text.delete("1.0", "101.0")
            self.log_line_count -= 100
        
        self.log_text.see("end")
    
    def get_video_duration(self, video_path):
        """获取视频总时长（秒）"""
        if not self.ffmpeg_path:
            return None
        
        try:
            cmd = [self.ffmpeg_path, "-i", video_path]
            
            if os.name == 'nt':
                creationflags = subprocess.CREATE_NO_WINDOW
            else:
                creationflags = 0
            
            result = subprocess.run(
                cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore',
                creationflags=creationflags
            )
            
            # 解析时长
            duration_pattern = r"Duration:\s*(\d{2}):(\d{2}):(\d{2}\.\d{2})"
            match = re.search(duration_pattern, result.stderr)
            
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                seconds = float(match.group(3))
                
                total_seconds = hours * 3600 + minutes * 60 + seconds
                self.total_duration = total_seconds
                self.log(f"⏱️ 视频时长: {hours:02d}:{minutes:02d}:{seconds:05.2f} ({total_seconds:.2f} 秒)")
                
                # 更新时间显示
                if VIDEO_PLAYER_AVAILABLE and hasattr(self, 'time_label'):
                    self.time_label.configure(
                        text=f"00:00 / {self.format_time(total_seconds)}"
                    )
                
                return total_seconds
            else:
                self.log("⚠️ 警告: 无法解析视频时长")
                return None
                
        except Exception as e:
            self.log(f"❌ 获取视频时长时出错: {str(e)}")
            return None
    
    def start_conversion(self):
        """开始转换"""
        if not self.ffmpeg_path:
            messagebox.showerror("错误", "FFmpeg 未找到，无法进行转换")
            return
        
        if not self.input_file:
            messagebox.showerror("错误", "请先选择视频文件")
            return
        
        # 暂停视频播放（释放 CPU）
        if VIDEO_PLAYER_AVAILABLE and self.is_playing:
            self.toggle_play_pause()
        
        # 生成输出文件名
        input_path = Path(self.input_file)
        self.output_file = str(input_path.parent / f"{input_path.stem}.gif")
        
        # 禁用控制
        self.convert_btn.configure(state="disabled")
        if VIDEO_PLAYER_AVAILABLE:
            self.play_btn.configure(state="disabled")
            self.set_start_btn.configure(state="disabled")
            self.set_end_btn.configure(state="disabled")
        self.is_converting = True
        
        # 重置进度
        self.conversion_progress_bar.set(0)
        self.conversion_progress_label.configure(text="0%")
        
        # 清空日志
        self.log_text.delete("1.0", "end")
        self.log_line_count = 0
        
        # 启动转换线程
        thread = threading.Thread(target=self.convert_video, daemon=True)
        thread.start()
    
    def convert_video(self):
        """执行视频转换（后台线程）"""
        try:
            # 获取裁剪参数
            try:
                skip_start = float(self.skip_start_entry.get() or 0)
            except ValueError:
                skip_start = 0
            
            try:
                skip_end = float(self.skip_end_entry.get() or 0)
            except ValueError:
                skip_end = 0
            
            # 验证参数
            if self.total_duration is None or self.total_duration <= 0:
                if skip_start > 0 or skip_end > 0:
                    error_msg = (
                        "无法获取视频时长！\n\n"
                        "建议：\n"
                        "- 尝试使用其他视频文件\n"
                        "- 将裁剪参数设为 0 后重试"
                    )
                    self.root.after(0, self.conversion_failed, error_msg)
                    return
                else:
                    self.log("⚠️ 警告: 无法获取视频时长，进度条可能不准确")
                    total_duration = 0
            else:
                total_duration = self.total_duration
            
            start_seek = max(0, skip_start)
            end_to = total_duration - skip_end
            
            if end_to <= start_seek:
                error_msg = (
                    f"裁剪时间不能超过视频总长！\n\n"
                    f"视频总长: {total_duration:.2f} 秒\n"
                    f"跳过片头: {skip_start:.2f} 秒\n"
                    f"去除片尾: {skip_end:.2f} 秒\n"
                    f"有效时长: {end_to - start_seek:.2f} 秒\n\n"
                    f"请调整裁剪参数！"
                )
                self.root.after(0, self.conversion_failed, error_msg)
                return
            
            effective_duration = end_to - start_seek
            self.log(f"✂️ 裁剪设置: 开始={start_seek:.2f}秒, 结束={end_to:.2f}秒, 有效时长={effective_duration:.2f}秒")
            self.log("🎬 开始转换...")
            
            # FFmpeg 命令
            cmd = [
                self.ffmpeg_path,
                "-ss", str(start_seek),
                "-to", str(end_to),
                "-i", self.input_file,
                "-vf", "fps=8,scale=240:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=16[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3",
                "-y",
                self.output_file
            ]
            
            if os.name == 'nt':
                creationflags = subprocess.CREATE_NO_WINDOW
            else:
                creationflags = 0
            
            process = subprocess.Popen(
                cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,
                encoding='utf-8',
                errors='ignore',
                creationflags=creationflags
            )
            
            time_pattern = r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})"
            last_progress = -1
            
            for line in process.stderr:
                line = line.strip()
                
                if line:
                    self.root.after(0, self.log_line, line)
                
                match = re.search(time_pattern, line)
                if match and effective_duration > 0:
                    hours = int(match.group(1))
                    minutes = int(match.group(2))
                    seconds = float(match.group(3))
                    
                    current_time = hours * 3600 + minutes * 60 + seconds
                    progress = min((current_time / effective_duration) * 100, 100)
                    
                    if abs(progress - last_progress) > 0.5:
                        last_progress = progress
                        self.root.after(0, self.update_conversion_progress, progress)
            
            process.wait()
            
            if process.returncode == 0 and os.path.exists(self.output_file):
                self.root.after(0, self.conversion_complete)
            else:
                self.root.after(0, self.conversion_failed, f"FFmpeg 返回错误代码: {process.returncode}")
                
        except Exception as e:
            self.root.after(0, self.conversion_failed, str(e))
    
    def update_conversion_progress(self, progress):
        """更新转换进度"""
        self.conversion_progress_bar.set(progress / 100)
        self.conversion_progress_label.configure(text=f"{progress:.1f}%")
        self.root.update_idletasks()
    
    def conversion_complete(self):
        """转换完成"""
        self.update_conversion_progress(100)
        self.log("✅ 转换完成！")
        self.is_converting = False
        
        # 恢复控制
        self.convert_btn.configure(state="normal")
        if VIDEO_PLAYER_AVAILABLE:
            self.play_btn.configure(state="normal")
            self.set_start_btn.configure(state="normal")
            self.set_end_btn.configure(state="normal")
        
        # 成功对话框
        result = messagebox.askyesno(
            "转换完成",
            f"GIF 文件已生成：\n{self.output_file}\n\n是否打开文件所在文件夹？"
        )
        
        if result:
            output_dir = os.path.dirname(self.output_file)
            os.startfile(output_dir)
    
    def conversion_failed(self, error_msg):
        """转换失败"""
        self.log(f"❌ 转换失败: {error_msg}")
        self.is_converting = False
        
        # 恢复控制
        self.convert_btn.configure(state="normal")
        if VIDEO_PLAYER_AVAILABLE:
            self.play_btn.configure(state="normal")
            self.set_start_btn.configure(state="normal")
            self.set_end_btn.configure(state="normal")
        
        messagebox.showerror("转换失败", f"转换过程中出现错误：\n{error_msg}")


def main():
    """主函数"""
    # 检查依赖
    if not VIDEO_PLAYER_AVAILABLE:
        response = messagebox.askyesno(
            "缺少依赖",
            "检测到 tkvideoplayer 未安装！\n\n"
            "视频预览功能将不可用。\n"
            "是否继续运行程序？\n\n"
            "安装方法：pip install tkvideoplayer"
        )
        if not response:
            return
    
    root = ctk.CTk()
    app = ModernGifConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
