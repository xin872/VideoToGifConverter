#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GIF Converter - Enhanced Version
现代化视频转 GIF 转换器
支持视频预览和交互式裁剪
"""

import os
import sys
import re
import subprocess
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path

try:
    from tkVideoPlayer import TkinterVideo
    VIDEO_PLAYER_AVAILABLE = True
except ImportError:
    VIDEO_PLAYER_AVAILABLE = False
    print("警告: tkvideoplayer 未安装，视频预览功能将不可用")
    print("请运行: pip install tkvideoplayer")


class ModernGifConverter:
    """现代化 GIF 转换器主类（带视频预览）"""
    
    def __init__(self, root):
        """初始化应用程序"""
        self.root = root
        self.root.title("GIF Converter")
        
        # 设置窗口大小和位置（增大以容纳视频预览）
        window_width = 800
        window_height = 950
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(False, False)
        
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
        
        # 创建 GUI
        self.create_widgets()
        
        # 检测 FFmpeg（在 GUI 创建后）
        self.ffmpeg_path = self.detect_ffmpeg()
        
        # 启动进度更新循环
        if VIDEO_PLAYER_AVAILABLE:
            self.start_progress_update()
        
    def detect_ffmpeg(self):
        """检测 FFmpeg 可执行文件"""
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        # 1. 检查本地 ffmpeg.exe
        local_ffmpeg = os.path.join(base_path, "ffmpeg.exe")
        if os.path.exists(local_ffmpeg):
            if hasattr(self, 'log_text'):
                self.log(f"✓ 找到 FFmpeg: {local_ffmpeg}")
            return local_ffmpeg
        
        # 2. 尝试系统 PATH
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
        
        # 3. 未找到
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
        # ===== Header =====
        header_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(20, 15))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🎬 GIF Converter",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=("#1f6aa5", "#4a9eff")
        )
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="视频预览 · 交互式裁剪 · 高质量转换",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle_label.pack(pady=(3, 0))
        
        separator = ctk.CTkFrame(header_frame, height=2, fg_color=("#d0d0d0", "#3a3a3a"))
        separator.pack(fill="x", pady=(10, 0))
        
        # ===== File Selection =====
        file_card = ctk.CTkFrame(self.root, corner_radius=12)
        file_card.pack(fill="x", padx=30, pady=(0, 12))
        
        file_inner = ctk.CTkFrame(file_card, fg_color="transparent")
        file_inner.pack(fill="x", padx=15, pady=15)
        
        file_header = ctk.CTkLabel(
            file_inner,
            text="📁 选择的文件",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w"
        )
        file_header.pack(fill="x", pady=(0, 6))
        
        self.file_label = ctk.CTkLabel(
            file_inner,
            text="未选择文件",
            font=ctk.CTkFont(size=12),
            anchor="w",
            text_color="gray"
        )
        self.file_label.pack(fill="x", pady=(0, 10))
        
        select_btn = ctk.CTkButton(
            file_inner,
            text="浏览文件",
            command=self.select_file,
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#2fa572", "#2fa572"),
            hover_color=("#26865f", "#26865f")
        )
        select_btn.pack(fill="x")
        
        # ===== Video Preview =====
        if VIDEO_PLAYER_AVAILABLE:
            preview_card = ctk.CTkFrame(self.root, corner_radius=12)
            preview_card.pack(fill="x", padx=30, pady=(0, 12))
            
            preview_inner = ctk.CTkFrame(preview_card, fg_color="transparent")
            preview_inner.pack(fill="both", expand=True, padx=15, pady=15)
            
            preview_header = ctk.CTkLabel(
                preview_inner,
                text="🎥 视频预览",
                font=ctk.CTkFont(size=11, weight="bold"),
                anchor="w"
            )
            preview_header.pack(fill="x", pady=(0, 8))
            
            # 视频播放器容器
            video_container = ctk.CTkFrame(
                preview_inner,
                fg_color="black",
                corner_radius=8,
                height=360
            )
            video_container.pack(fill="x", pady=(0, 10))
            video_container.pack_propagate(False)
            
            # TkVideoPlayer
            self.video_player = TkinterVideo(
                video_container,
                bg="black"
            )
            self.video_player.pack(fill="both", expand=True)
            
            # 播放控制
            controls_frame = ctk.CTkFrame(preview_inner, fg_color="transparent")
            controls_frame.pack(fill="x")
            
            # 进度条
            self.progress_slider = ctk.CTkSlider(
                controls_frame,
                from_=0,
                to=1,
                command=self.seek_video,
                height=16
            )
            self.progress_slider.pack(fill="x", pady=(0, 8))
            self.progress_slider.set(0)
            
            # 播放按钮和时间
            playback_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
            playback_frame.pack(fill="x")
            
            self.play_btn = ctk.CTkButton(
                playback_frame,
                text="▶️ 播放",
                command=self.toggle_play_pause,
                width=100,
                height=32,
                corner_radius=8,
                font=ctk.CTkFont(size=12)
            )
            self.play_btn.pack(side="left")
            
            self.time_label = ctk.CTkLabel(
                playback_frame,
                text="00:00 / 00:00",
                font=ctk.CTkFont(family="Consolas", size=12),
                text_color="gray"
            )
            self.time_label.pack(side="left", padx=(15, 0))
        
        # ===== Interactive Trim Controls =====
        trim_card = ctk.CTkFrame(self.root, corner_radius=12)
        trim_card.pack(fill="x", padx=30, pady=(0, 12))
        
        trim_inner = ctk.CTkFrame(trim_card, fg_color="transparent")
        trim_inner.pack(fill="x", padx=15, pady=15)
        
        trim_header = ctk.CTkLabel(
            trim_inner,
            text="✂️ 交互式裁剪",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w"
        )
        trim_header.pack(fill="x", pady=(0, 10))
        
        # 快捷按钮
        if VIDEO_PLAYER_AVAILABLE:
            quick_btns = ctk.CTkFrame(trim_inner, fg_color="transparent")
            quick_btns.pack(fill="x", pady=(0, 10))
            
            self.set_start_btn = ctk.CTkButton(
                quick_btns,
                text="📍 设为起点",
                command=self.set_start_point,
                height=32,
                corner_radius=8,
                font=ctk.CTkFont(size=12),
                fg_color=("#1f6aa5", "#1f6aa5"),
                hover_color=("#174e7c", "#174e7c")
            )
            self.set_start_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
            
            self.set_end_btn = ctk.CTkButton(
                quick_btns,
                text="🎯 设为终点",
                command=self.set_end_point,
                height=32,
                corner_radius=8,
                font=ctk.CTkFont(size=12),
                fg_color=("#1f6aa5", "#1f6aa5"),
                hover_color=("#174e7c", "#174e7c")
            )
            self.set_end_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        # 裁剪参数
        vcmd = (self.root.register(self.validate_number), '%P')
        
        params_frame = ctk.CTkFrame(trim_inner, fg_color="transparent")
        params_frame.pack(fill="x")
        
        # 左列
        left_col = ctk.CTkFrame(params_frame, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        skip_start_label = ctk.CTkLabel(
            left_col,
            text="跳过片头 (秒)",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        skip_start_label.pack(fill="x", pady=(0, 6))
        
        self.skip_start_entry = ctk.CTkEntry(
            left_col,
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            validate='key',
            validatecommand=vcmd
        )
        self.skip_start_entry.insert(0, "0")
        self.skip_start_entry.pack(fill="x")
        
        # 右列
        right_col = ctk.CTkFrame(params_frame, fg_color="transparent")
        right_col.pack(side="left", fill="both", expand=True, padx=(8, 0))
        
        skip_end_label = ctk.CTkLabel(
            right_col,
            text="去除片尾 (秒)",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        skip_end_label.pack(fill="x", pady=(0, 6))
        
        self.skip_end_entry = ctk.CTkEntry(
            right_col,
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            validate='key',
            validatecommand=vcmd
        )
        self.skip_end_entry.insert(0, "0")
        self.skip_end_entry.pack(fill="x")
        
        # ===== Convert Button =====
        convert_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        convert_frame.pack(fill="x", padx=30, pady=(0, 12))
        
        self.convert_btn = ctk.CTkButton(
            convert_frame,
            text="🚀 开始转换",
            command=self.start_conversion,
            state="disabled",
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=("#1f6aa5", "#1f6aa5"),
            hover_color=("#174e7c", "#174e7c")
        )
        self.convert_btn.pack(fill="x")
        
        # ===== Progress =====
        progress_card = ctk.CTkFrame(self.root, corner_radius=12)
        progress_card.pack(fill="x", padx=30, pady=(0, 12))
        
        progress_inner = ctk.CTkFrame(progress_card, fg_color="transparent")
        progress_inner.pack(fill="x", padx=15, pady=15)
        
        progress_header = ctk.CTkLabel(
            progress_inner,
            text="📊 转换进度",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w"
        )
        progress_header.pack(fill="x", pady=(0, 10))
        
        self.conversion_progress_bar = ctk.CTkProgressBar(
            progress_inner,
            height=8,
            corner_radius=4
        )
        self.conversion_progress_bar.set(0)
        self.conversion_progress_bar.pack(fill="x", pady=(0, 8))
        
        self.conversion_progress_label = ctk.CTkLabel(
            progress_inner,
            text="0%",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#1f6aa5", "#4a9eff")
        )
        self.conversion_progress_label.pack()
        
        # ===== Log =====
        log_card = ctk.CTkFrame(self.root, corner_radius=12)
        log_card.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        
        log_inner = ctk.CTkFrame(log_card, fg_color="transparent")
        log_inner.pack(fill="both", expand=True, padx=15, pady=15)
        
        log_header = ctk.CTkLabel(
            log_inner,
            text="📝 执行日志",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w"
        )
        log_header.pack(fill="x", pady=(0, 8))
        
        self.log_text = ctk.CTkTextbox(
            log_inner,
            height=120,
            corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=10),
            wrap="none",
            activate_scrollbars=True
        )
        self.log_text.pack(fill="both", expand=True)
        
        self.log_line_count = 0
        self.max_log_lines = 500
    
    def select_file(self):
        """选择视频文件"""
        filetypes = (
            ("视频文件", "*.mp4 *.avi *.mkv *.mov *.flv *.wmv"),
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
            
            # 加载视频到预览器
            if VIDEO_PLAYER_AVAILABLE and self.video_player:
                self.load_video_preview(filename)
            
            # 获取视频时长
            self.get_video_duration(filename)
    
    def load_video_preview(self, video_path):
        """加载视频到预览器"""
        try:
            self.video_player.load(video_path)
            self.log("✓ 视频已加载到预览器")
            self.play_btn.configure(state="normal")
            if hasattr(self, 'set_start_btn'):
                self.set_start_btn.configure(state="normal")
                self.set_end_btn.configure(state="normal")
        except Exception as e:
            self.log(f"⚠️ 加载视频预览失败: {str(e)}")
    
    def toggle_play_pause(self):
        """切换播放/暂停"""
        if not self.video_player:
            return
        
        if self.is_playing:
            self.video_player.pause()
            self.play_btn.configure(text="▶️ 播放")
            self.is_playing = False
        else:
            self.video_player.play()
            self.play_btn.configure(text="⏸️ 暂停")
            self.is_playing = True
    
    def seek_video(self, value):
        """拖动进度条"""
        if self.video_player and self.total_duration > 0:
            seek_time = float(value) * self.total_duration
            self.video_player.seek(int(seek_time))
    
    def start_progress_update(self):
        """启动进度更新循环"""
        def update():
            if self.is_playing and self.video_player and self.total_duration > 0:
                try:
                    current = self.video_player.current_duration()
                    self.progress_slider.set(current / self.total_duration)
                    self.time_label.configure(
                        text=f"{self.format_time(current)} / {self.format_time(self.total_duration)}"
                    )
                except:
                    pass
            self.root.after(100, update)
        update()
    
    def format_time(self, seconds):
        """格式化时间为 MM:SS"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def set_start_point(self):
        """设置起点"""
        if not self.video_player:
            return
        
        try:
            current_time = self.video_player.current_duration()
            self.skip_start_entry.delete(0, "end")
            self.skip_start_entry.insert(0, str(int(current_time)))
            self.log(f"✂️ 起点设为: {current_time:.2f} 秒")
        except Exception as e:
            self.log(f"⚠️ 设置起点失败: {str(e)}")
    
    def set_end_point(self):
        """设置终点"""
        if not self.video_player or self.total_duration == 0:
            return
        
        try:
            current_time = self.video_player.current_duration()
            skip_end = self.total_duration - current_time
            self.skip_end_entry.delete(0, "end")
            self.skip_end_entry.insert(0, str(int(skip_end)))
            self.log(f"✂️ 终点设为: {current_time:.2f} 秒 (去除片尾 {skip_end:.2f} 秒)")
        except Exception as e:
            self.log(f"⚠️ 设置终点失败: {str(e)}")
    
    def log(self, message):
        """添加日志"""
        self.log_text.insert("end", message + "\n")
        self.log_line_count += 1
        
        if self.log_line_count > self.max_log_lines:
            self.log_text.delete("1.0", "101.0")
            self.log_line_count -= 100
        
        self.log_text.see("end")
        self.root.update_idletasks()
    
    def log_line(self, line):
        """添加单行日志"""
        if not line.strip():
            return
        
        self.log_text.insert("end", line + "\n")
        self.log_line_count += 1
        
        if self.log_line_count > self.max_log_lines:
            self.log_text.delete("1.0", "101.0")
            self.log_line_count -= 100
        
        self.log_text.see("end")
    
    def get_video_duration(self, video_path):
        """获取视频时长"""
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
        
        # 暂停视频播放
        if VIDEO_PLAYER_AVAILABLE and self.is_playing:
            self.toggle_play_pause()
        
        # 生成输出文件名
        input_path = Path(self.input_file)
        self.output_file = str(input_path.parent / f"{input_path.stem}.gif")
        
        # 禁用控制
        self.convert_btn.configure(state="disabled")
        if VIDEO_PLAYER_AVAILABLE:
            self.play_btn.configure(state="disabled")
            if hasattr(self, 'set_start_btn'):
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
        """执行转换（后台线程）"""
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
        self.convert_btn.configure(state="normal")
        if VIDEO_PLAYER_AVAILABLE:
            self.play_btn.configure(state="normal")
            if hasattr(self, 'set_start_btn'):
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
        self.convert_btn.configure(state="normal")
        if VIDEO_PLAYER_AVAILABLE:
            self.play_btn.configure(state="normal")
            if hasattr(self, 'set_start_btn'):
                self.set_start_btn.configure(state="normal")
                self.set_end_btn.configure(state="normal")
        messagebox.showerror("转换失败", f"转换过程中出现错误：\n{error_msg}")


def main():
    """主函数"""
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
