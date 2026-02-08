"""
YouTube Downloader Pro - 专业YouTube视频下载工具
基于CustomTkinter和yt-dlp开发，支持批量下载、字幕内嵌、多种格式选择
Version: 2.1.0
github网址： https://github.com/lyp0746
QQ邮箱：1610369302@qq.com
作者：LYP
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import yt_dlp
import threading
import os
import json
from pathlib import Path
from datetime import datetime
import webbrowser

class YouTubeDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 窗口配置
        self.title("YouTube 视频下载器 Pro")
        self.geometry("900x750")
        self.resizable(True, True)
        
        # 设置主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 配置文件路径
        self.config_file = Path.cwd() / ".youtube_downloader_config.json"
        
        # 变量
        self.download_path = ctk.StringVar(value=str(Path.home() / "Downloads"))
        self.url_var = ctk.StringVar()
        self.quality_var = ctk.StringVar(value="最高画质")
        self.format_var = ctk.StringVar(value="MP4")
        self.progress_var = ctk.DoubleVar(value=0)
        self.status_var = ctk.StringVar(value="就绪")
        self.playlist_var = ctk.BooleanVar(value=False)
        self.subtitle_var = ctk.BooleanVar(value=False)
        self.embed_subtitle_var = ctk.BooleanVar(value=True)  # 新增：字幕内嵌开关
        self.thumbnail_var = ctk.BooleanVar(value=False)
        self.proxy_var = ctk.StringVar(value="")
        self.use_proxy_var = ctk.BooleanVar(value=False)
        self.auto_number_var = ctk.BooleanVar(value=True)
        self.speed_limit_var = ctk.StringVar(value="无限制")
        
        self.is_downloading = False
        self.download_thread = None
        self.download_history = []
        
        # 加载配置
        self.load_config()
        
        self.setup_ui()
        
    def setup_ui(self):
        # 创建标签页
        self.tabview = ctk.CTkTabview(self, width=860)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 添加标签页
        self.tabview.add("下载")
        self.tabview.add("批量下载")
        self.tabview.add("设置")
        self.tabview.add("历史记录")
        self.tabview.add("关于")
        
        # 设置各个标签页
        self.setup_download_tab()
        self.setup_batch_tab()
        self.setup_settings_tab()
        self.setup_history_tab()
        self.setup_about_tab()
        
    def setup_download_tab(self):
        tab = self.tabview.tab("下载")
        
        # 主容器
        main_frame = ctk.CTkScrollableFrame(tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 标题
        title_label = ctk.CTkLabel(
            main_frame, 
            text="📥 单视频下载", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # URL 输入区域
        url_frame = ctk.CTkFrame(main_frame)
        url_frame.pack(fill="x", pady=(0, 15))
        
        url_label = ctk.CTkLabel(url_frame, text="视频链接:", font=ctk.CTkFont(size=14))
        url_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        url_input_frame = ctk.CTkFrame(url_frame, fg_color="transparent")
        url_input_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        self.url_entry = ctk.CTkEntry(
            url_input_frame, 
            textvariable=self.url_var,
            placeholder_text="粘贴 YouTube 视频链接...",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # 获取信息按钮
        info_btn = ctk.CTkButton(
            url_input_frame,
            text="📋 获取信息",
            width=100,
            height=40,
            command=self.get_video_info
        )
        info_btn.pack(side="right")
        
        # 播放列表选项
        playlist_checkbox = ctk.CTkCheckBox(
            url_frame,
            text="下载整个播放列表",
            variable=self.playlist_var,
            font=ctk.CTkFont(size=12)
        )
        playlist_checkbox.pack(anchor="w", padx=15, pady=(0, 15))
        
        # 视频信息显示区域
        self.info_frame = ctk.CTkFrame(main_frame)
        self.info_frame.pack(fill="x", pady=(0, 15))
        
        info_title = ctk.CTkLabel(self.info_frame, text="视频信息", font=ctk.CTkFont(size=14, weight="bold"))
        info_title.pack(anchor="w", padx=15, pady=(10, 5))
        
        self.info_text = ctk.CTkTextbox(self.info_frame, height=80, font=ctk.CTkFont(size=11))
        self.info_text.pack(fill="x", padx=15, pady=(0, 10))
        self.info_text.insert("1.0", "点击「获取信息」按钮查看视频详情...")
        self.info_text.configure(state="disabled")
        
        # 设置区域
        settings_frame = ctk.CTkFrame(main_frame)
        settings_frame.pack(fill="x", pady=(0, 15))
        
        settings_title = ctk.CTkLabel(settings_frame, text="下载设置", font=ctk.CTkFont(size=14, weight="bold"))
        settings_title.pack(anchor="w", padx=15, pady=(10, 10))
        
        # 保存路径
        path_inner_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        path_inner_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        path_label = ctk.CTkLabel(path_inner_frame, text="保存位置:", font=ctk.CTkFont(size=12))
        path_label.pack(anchor="w", pady=(0, 5))
        
        path_select_frame = ctk.CTkFrame(path_inner_frame, fg_color="transparent")
        path_select_frame.pack(fill="x")
        
        self.path_entry = ctk.CTkEntry(
            path_select_frame,
            textvariable=self.download_path,
            height=35,
            font=ctk.CTkFont(size=11)
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = ctk.CTkButton(
            path_select_frame,
            text="浏览",
            width=80,
            height=35,
            command=self.browse_folder
        )
        browse_btn.pack(side="left")
        
        open_folder_btn = ctk.CTkButton(
            path_select_frame,
            text="📁",
            width=40,
            height=35,
            command=self.open_download_folder
        )
        open_folder_btn.pack(side="left", padx=(5, 0))
        
        # 画质和格式
        quality_format_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        quality_format_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        # 画质
        quality_frame = ctk.CTkFrame(quality_format_frame, fg_color="transparent")
        quality_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        quality_label = ctk.CTkLabel(quality_frame, text="画质:", font=ctk.CTkFont(size=12))
        quality_label.pack(anchor="w", pady=(0, 5))
        
        quality_menu = ctk.CTkOptionMenu(
            quality_frame,
            variable=self.quality_var,
            values=["最高画质", "2160p (4K)", "1440p (2K)", "1080p", "720p", "480p", "360p", "仅音频"],
            width=150,
            height=35
        )
        quality_menu.pack(fill="x")
        
        # 格式
        format_frame = ctk.CTkFrame(quality_format_frame, fg_color="transparent")
        format_frame.pack(side="right", fill="x", expand=True)
        
        format_label = ctk.CTkLabel(format_frame, text="格式:", font=ctk.CTkFont(size=12))
        format_label.pack(anchor="w", pady=(0, 5))
        
        format_menu = ctk.CTkOptionMenu(
            format_frame,
            variable=self.format_var,
            values=["MP4", "WEBM", "MKV", "MP3", "M4A", "WAV"],
            width=150,
            height=35
        )
        format_menu.pack(fill="x")
        
        # 额外选项
        extra_options_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        extra_options_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        subtitle_checkbox = ctk.CTkCheckBox(
            extra_options_frame,
            text="下载字幕",
            variable=self.subtitle_var,
            font=ctk.CTkFont(size=12)
        )
        subtitle_checkbox.pack(side="left", padx=(0, 20))
        
        # 新增：字幕内嵌选项
        embed_subtitle_checkbox = ctk.CTkCheckBox(
            extra_options_frame,
            text="内嵌字幕到视频",
            variable=self.embed_subtitle_var,
            font=ctk.CTkFont(size=12)
        )
        embed_subtitle_checkbox.pack(side="left", padx=(0, 20))
        
        thumbnail_checkbox = ctk.CTkCheckBox(
            extra_options_frame,
            text="下载缩略图",
            variable=self.thumbnail_var,
            font=ctk.CTkFont(size=12)
        )
        thumbnail_checkbox.pack(side="left", padx=(0, 20))
        
        # 播放列表编号移到第二行
        extra_options_frame2 = ctk.CTkFrame(settings_frame, fg_color="transparent")
        extra_options_frame2.pack(fill="x", padx=15, pady=(0, 15))
        
        auto_number_checkbox = ctk.CTkCheckBox(
            extra_options_frame2,
            text="播放列表自动编号",
            variable=self.auto_number_var,
            font=ctk.CTkFont(size=12)
        )
        auto_number_checkbox.pack(side="left")
        
        # 进度区域
        progress_frame = ctk.CTkFrame(main_frame)
        progress_frame.pack(fill="x", pady=(0, 15))
        
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            variable=self.progress_var,
            height=20
        )
        self.progress_bar.pack(fill="x", padx=15, pady=(15, 10))
        
        self.status_label = ctk.CTkLabel(
            progress_frame,
            textvariable=self.status_var,
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=(0, 15))
        
        # 按钮区域
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 10))
        
        self.download_btn = ctk.CTkButton(
            button_frame,
            text="🚀 开始下载",
            command=self.start_download,
            height=45,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#1f538d",
            hover_color="#14375e"
        )
        self.download_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.cancel_btn = ctk.CTkButton(
            button_frame,
            text="⏹ 取消",
            command=self.cancel_download,
            height=45,
            font=ctk.CTkFont(size=15),
            fg_color="#8B0000",
            hover_color="#660000",
            state="disabled"
        )
        self.cancel_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))
    
    def setup_batch_tab(self):
        tab = self.tabview.tab("批量下载")
        
        main_frame = ctk.CTkFrame(tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 标题
        title_label = ctk.CTkLabel(
            main_frame, 
            text="📋 批量下载", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # 说明
        info_label = ctk.CTkLabel(
            main_frame,
            text="每行输入一个视频链接，支持下载多个视频",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        info_label.pack(pady=(0, 10))
        
        # URL列表输入
        self.batch_text = ctk.CTkTextbox(main_frame, height=300, font=ctk.CTkFont(size=12))
        self.batch_text.pack(fill="both", expand=True, pady=(0, 15))
        
        # 按钮区域
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        import_btn = ctk.CTkButton(
            button_frame,
            text="📂 从文件导入",
            command=self.import_urls,
            height=40
        )
        import_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        clear_btn = ctk.CTkButton(
            button_frame,
            text="🗑 清空",
            command=lambda: self.batch_text.delete("1.0", "end"),
            height=40,
            fg_color="gray40",
            hover_color="gray30"
        )
        clear_btn.pack(side="left", fill="x", expand=True, padx=(5, 5))
        
        self.batch_download_btn = ctk.CTkButton(
            button_frame,
            text="⬇️ 批量下载",
            command=self.start_batch_download,
            height=40,
            fg_color="#1f538d",
            hover_color="#14375e"
        )
        self.batch_download_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))
    
    def setup_settings_tab(self):
        tab = self.tabview.tab("设置")
        
        main_frame = ctk.CTkScrollableFrame(tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 标题
        title_label = ctk.CTkLabel(
            main_frame, 
            text="⚙️ 高级设置", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # 代理设置
        proxy_frame = ctk.CTkFrame(main_frame)
        proxy_frame.pack(fill="x", pady=(0, 15))
        
        proxy_title = ctk.CTkLabel(proxy_frame, text="代理设置", font=ctk.CTkFont(size=16, weight="bold"))
        proxy_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        use_proxy_check = ctk.CTkCheckBox(
            proxy_frame,
            text="使用代理",
            variable=self.use_proxy_var,
            font=ctk.CTkFont(size=12)
        )
        use_proxy_check.pack(anchor="w", padx=15, pady=(0, 10))
        
        proxy_label = ctk.CTkLabel(proxy_frame, text="代理地址 (例: http://127.0.0.1:7890):", font=ctk.CTkFont(size=12))
        proxy_label.pack(anchor="w", padx=15, pady=(0, 5))
        
        proxy_entry = ctk.CTkEntry(
            proxy_frame,
            textvariable=self.proxy_var,
            placeholder_text="http://127.0.0.1:7890",
            height=35,
            font=ctk.CTkFont(size=11)
        )
        proxy_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        # 速度限制
        speed_frame = ctk.CTkFrame(main_frame)
        speed_frame.pack(fill="x", pady=(0, 15))
        
        speed_title = ctk.CTkLabel(speed_frame, text="速度限制", font=ctk.CTkFont(size=16, weight="bold"))
        speed_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        speed_label = ctk.CTkLabel(speed_frame, text="下载速度限制:", font=ctk.CTkFont(size=12))
        speed_label.pack(anchor="w", padx=15, pady=(0, 5))
        
        speed_menu = ctk.CTkOptionMenu(
            speed_frame,
            variable=self.speed_limit_var,
            values=["无限制", "10M", "5M", "2M", "1M", "512K"],
            width=200,
            height=35
        )
        speed_menu.pack(anchor="w", padx=15, pady=(0, 15))
        
        # 文件命名
        naming_frame = ctk.CTkFrame(main_frame)
        naming_frame.pack(fill="x", pady=(0, 15))
        
        naming_title = ctk.CTkLabel(naming_frame, text="文件命名模板", font=ctk.CTkFont(size=16, weight="bold"))
        naming_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        naming_info = ctk.CTkLabel(
            naming_frame,
            text="%(title)s - 标题 | %(uploader)s - 上传者 | %(upload_date)s - 日期",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        naming_info.pack(anchor="w", padx=15, pady=(0, 5))
        
        self.naming_var = ctk.StringVar(value="%(title)s.%(ext)s")
        naming_entry = ctk.CTkEntry(
            naming_frame,
            textvariable=self.naming_var,
            height=35,
            font=ctk.CTkFont(size=11)
        )
        naming_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        # 保存配置按钮
        save_config_btn = ctk.CTkButton(
            main_frame,
            text="💾 保存配置",
            command=self.save_config,
            height=40,
            fg_color="#2d7a3e",
            hover_color="#1f5b2d"
        )
        save_config_btn.pack(fill="x", pady=(10, 0))
    
    def setup_history_tab(self):
        tab = self.tabview.tab("历史记录")
        
        main_frame = ctk.CTkFrame(tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 标题
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 15))
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text="📜 下载历史", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left")
        
        clear_history_btn = ctk.CTkButton(
            title_frame,
            text="🗑 清空历史",
            command=self.clear_history,
            width=100,
            height=30,
            fg_color="gray40",
            hover_color="gray30"
        )
        clear_history_btn.pack(side="right")
        
        # 历史记录列表
        self.history_text = ctk.CTkTextbox(main_frame, font=ctk.CTkFont(size=11))
        self.history_text.pack(fill="both", expand=True)
        
        self.update_history_display()
    
    def setup_about_tab(self):
        tab = self.tabview.tab("关于")
        
        main_frame = ctk.CTkFrame(tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 标题
        title_label = ctk.CTkLabel(
            main_frame, 
            text="YouTube 下载器 Pro", 
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        version_label = ctk.CTkLabel(
            main_frame,
            text="版本 2.1.0 - 支持字幕内嵌",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        version_label.pack(pady=(0, 30))
        
        # 功能介绍
        features_frame = ctk.CTkFrame(main_frame)
        features_frame.pack(fill="x", pady=(0, 20))
        
        features_title = ctk.CTkLabel(
            features_frame,
            text="✨ 主要功能",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        features_title.pack(pady=(15, 10))
        
        features = [
            "• 支持单视频和批量下载",
            "• 多种画质和格式选择",
            "• 下载简体中文字幕（避免429错误）",
            "• 字幕内嵌到视频文件",
            "• 播放列表下载",
            "• 代理设置支持",
            "• 下载速度限制",
            "• 历史记录管理",
            "• 自定义文件命名"
        ]
        
        for feature in features:
            feature_label = ctk.CTkLabel(
                features_frame,
                text=feature,
                font=ctk.CTkFont(size=13),
                anchor="w"
            )
            feature_label.pack(anchor="w", padx=20, pady=2)
        
        ctk.CTkLabel(features_frame, text="").pack(pady=5)
        
        # 技术栈
        tech_frame = ctk.CTkFrame(main_frame)
        tech_frame.pack(fill="x", pady=(0, 20))
        
        tech_title = ctk.CTkLabel(
            tech_frame,
            text="🔧 技术栈",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        tech_title.pack(pady=(15, 10))
        
        tech_label = ctk.CTkLabel(
            tech_frame,
            text="Python 3.x • CustomTkinter • yt-dlp • FFmpeg",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        tech_label.pack(pady=(0, 15))
        
        # 链接
        github_btn = ctk.CTkButton(
            main_frame,
            text="🌟 GitHub",
            command=lambda: webbrowser.open("https://github.com/yt-dlp/yt-dlp"),
            width=200,
            height=40
        )
        github_btn.pack(pady=5)
    
    def get_video_info(self):
        """获取视频信息"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("警告", "请先输入视频链接！")
            return
        
        def fetch_info():
            try:
                self.info_text.configure(state="normal")
                self.info_text.delete("1.0", "end")
                self.info_text.insert("1.0", "正在获取视频信息...\n")
                self.info_text.configure(state="disabled")
                
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android', 'web'],
                        }
                    }
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    info_text = f"标题: {info.get('title', 'N/A')}\n"
                    info_text += f"上传者: {info.get('uploader', 'N/A')}\n"
                    info_text += f"时长: {info.get('duration', 0) // 60} 分 {info.get('duration', 0) % 60} 秒\n"
                    info_text += f"观看次数: {info.get('view_count', 'N/A'):,}\n"
                    info_text += f"发布日期: {info.get('upload_date', 'N/A')}\n"
                    
                    if 'entries' in info:
                        info_text += f"\n这是一个播放列表，包含 {len(info['entries'])} 个视频"
                    
                    self.info_text.configure(state="normal")
                    self.info_text.delete("1.0", "end")
                    self.info_text.insert("1.0", info_text)
                    self.info_text.configure(state="disabled")
                    
            except Exception as e:
                self.info_text.configure(state="normal")
                self.info_text.delete("1.0", "end")
                self.info_text.insert("1.0", f"获取信息失败: {str(e)}")
                self.info_text.configure(state="disabled")
        
        threading.Thread(target=fetch_info, daemon=True).start()
    
    def import_urls(self):
        """从文件导入URL"""
        file_path = filedialog.askopenfilename(
            title="选择文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    urls = f.read()
                    self.batch_text.delete("1.0", "end")
                    self.batch_text.insert("1.0", urls)
            except Exception as e:
                messagebox.showerror("错误", f"读取文件失败: {str(e)}")
    
    def start_batch_download(self):
        """开始批量下载"""
        urls_text = self.batch_text.get("1.0", "end").strip()
        if not urls_text:
            messagebox.showwarning("警告", "请输入至少一个视频链接！")
            return
        
        urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
        
        if messagebox.askyesno("确认", f"将要下载 {len(urls)} 个视频，是否继续？"):
            self.batch_download_btn.configure(state="disabled")
            
            def batch_download():
                for i, url in enumerate(urls, 1):
                    if not self.is_downloading:
                        break
                    
                    self.url_var.set(url)
                    self.status_var.set(f"批量下载 ({i}/{len(urls)})")
                    self.download_video()
                
                self.batch_download_btn.configure(state="normal")
                self.status_var.set("批量下载完成！")
            
            self.is_downloading = True
            threading.Thread(target=batch_download, daemon=True).start()
    
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_path.set(folder)
    
    def open_download_folder(self):
        """打开下载文件夹"""
        path = self.download_path.get()
        if os.path.exists(path):
            os.startfile(path) if os.name == 'nt' else os.system(f'open "{path}"')
        else:
            messagebox.showwarning("警告", "文件夹不存在！")
    
    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                percent_str = d.get('_percent_str', '0%').strip('%')
                percent = float(percent_str) / 100
                self.progress_var.set(percent)
                
                downloaded = d.get('_downloaded_bytes_str', '0B')
                total = d.get('_total_bytes_str', '0B')
                speed = d.get('_speed_str', '0B/s')
                eta = d.get('_eta_str', '未知')
                
                status = f"下载中... {downloaded}/{total} | 速度: {speed} | 预计: {eta}"
                self.status_var.set(status)
            except:
                pass
                
        elif d['status'] == 'finished':
            self.status_var.set("正在处理文件...")
            self.progress_var.set(1.0)
    
    def download_video(self):
        url = self.url_var.get().strip()
        
        if not url:
            messagebox.showerror("错误", "请输入视频链接！")
            self.reset_ui()
            return
        
        quality = self.quality_var.get()
        format_choice = self.format_var.get().lower()
        download_playlist = self.playlist_var.get()
        
        # 基础配置
        ydl_opts = {
            'outtmpl': os.path.join(self.download_path.get(), self.naming_var.get()),
            'progress_hooks': [self.progress_hook],
            'nocheckcertificate': True,
            'noplaylist': not download_playlist,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
            'retries': 10,
            'fragment_retries': 10,
            'socket_timeout': 30,
        }
        
        # 代理设置
        if self.use_proxy_var.get() and self.proxy_var.get():
            ydl_opts['proxy'] = self.proxy_var.get()
        
        # 速度限制
        if self.speed_limit_var.get() != "无限制":
            ydl_opts['ratelimit'] = self.parse_speed_limit(self.speed_limit_var.get())
        
        # 字幕设置 - 优化简体中文字幕下载，避免429错误
        if self.subtitle_var.get():
            # 优先下载简体中文字幕，如果不存在则下载自动生成的字幕
            ydl_opts['writesubtitles'] = True
            ydl_opts['writeautomaticsub'] = True
            # 只尝试下载简体中文，避免过多请求导致429错误
            ydl_opts['subtitleslangs'] = ['zh', 'zh-CN']
            # 添加延迟避免429错误
            ydl_opts['sleep_interval'] = 3
            ydl_opts['max_sleep_interval'] = 8
            ydl_opts['retries'] = 5  # 减少重试次数
            ydl_opts['fragment_retries'] = 5
            
            # 如果选择内嵌字幕
            if self.embed_subtitle_var.get():
                ydl_opts['postprocessors'] = ydl_opts.get('postprocessors', [])
                ydl_opts['postprocessors'].append({
                    'key': 'FFmpegEmbedSubtitle',
                    'already_have_subtitle': False
                })
                # 自动删除单独的字幕文件（可选）
                # ydl_opts['keepvideo'] = False
        
        # 缩略图设置
        if self.thumbnail_var.get():
            ydl_opts['writethumbnail'] = True
        
        # 播放列表编号
        if self.auto_number_var.get() and download_playlist:
            ydl_opts['outtmpl'] = os.path.join(
                self.download_path.get(), 
                '%(playlist_index)s - %(title)s.%(ext)s'
            )
        
        # 格式设置
        if quality == "仅音频" or format_choice in ["mp3", "m4a", "wav"]:
            ydl_opts['format'] = 'bestaudio/best'
            if 'postprocessors' not in ydl_opts:
                ydl_opts['postprocessors'] = []
            ydl_opts['postprocessors'].insert(0, {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format_choice if format_choice != 'mp4' else 'mp3',
                'preferredquality': '192',
            })
        else:
            if quality == "最高画质":
                format_str = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            else:
                height = quality.split('p')[0].split(' ')[-1]
                format_str = f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}]'
            
            ydl_opts['format'] = format_str
            ydl_opts['merge_output_format'] = format_choice if format_choice in ['mp4', 'mkv', 'webm'] else 'mp4'
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.status_var.set("正在获取视频信息...")
                info = ydl.extract_info(url, download=False)
                
                if 'entries' in info and not download_playlist:
                    self.status_var.set("检测到播放列表，仅下载单个视频...")
                    ydl.download([info['entries'][0]['webpage_url']])
                else:
                    ydl.download([url])
                
            if self.is_downloading:
                self.status_var.set("✅ 下载完成！")
                
                # 添加到历史记录
                self.add_to_history(url, info.get('title', 'Unknown'))
                
                messagebox.showinfo("成功", f"视频已保存到:\n{self.download_path.get()}")
                
        except Exception as e:
            if self.is_downloading:
                error_msg = str(e)
                self.status_var.set("❌ 下载失败")
                
                if "403" in error_msg or "429" in error_msg:
                    # 如果是字幕下载的429错误，提供更具体的建议
                    if "subtitles" in error_msg.lower():
                        messagebox.showerror("字幕下载失败", 
                            "YouTube 限制了字幕下载请求。\n\n"
                            "字幕下载建议:\n"
                            "1. 尝试关闭字幕下载选项\n"
                            "2. 使用代理服务器\n"
                            "3. 等待一段时间后重试\n"
                            "4. 该视频可能没有中文字幕")
                    else:
                        messagebox.showerror("下载失败", 
                            "YouTube 阻止了下载请求。\n\n"
                            "建议:\n"
                            "1. 在「设置」中配置代理\n"
                            "2. 更新 yt-dlp: pip install -U yt-dlp\n"
                            "3. 等待几分钟后重试")
                else:
                    messagebox.showerror("错误", f"下载失败:\n{error_msg}")
        
        finally:
            self.reset_ui()
    
    def parse_speed_limit(self, limit_str):
        """解析速度限制"""
        multipliers = {'K': 1024, 'M': 1024*1024}
        num = int(limit_str[:-1])
        unit = limit_str[-1]
        return num * multipliers.get(unit, 1)
    
    def add_to_history(self, url, title):
        """添加到历史记录"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.download_history.insert(0, {
            'url': url,
            'title': title,
            'time': timestamp
        })
        # 只保留最近100条
        self.download_history = self.download_history[:100]
        self.update_history_display()
        self.save_config()
    
    def update_history_display(self):
        """更新历史记录显示"""
        self.history_text.configure(state="normal")
        self.history_text.delete("1.0", "end")
        
        if not self.download_history:
            self.history_text.insert("1.0", "暂无下载历史")
        else:
            for i, item in enumerate(self.download_history, 1):
                self.history_text.insert("end", f"{i}. {item['title']}\n")
                self.history_text.insert("end", f"   {item['url']}\n")
                self.history_text.insert("end", f"   时间: {item['time']}\n\n")
        
        self.history_text.configure(state="disabled")
    
    def clear_history(self):
        """清空历史记录"""
        if messagebox.askyesno("确认", "确定要清空所有历史记录吗？"):
            self.download_history = []
            self.update_history_display()
            self.save_config()
    
    def start_download(self):
        if not self.url_var.get().strip():
            messagebox.showwarning("警告", "请输入视频链接！")
            return
            
        self.is_downloading = True
        self.download_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress_var.set(0)
        
        self.download_thread = threading.Thread(target=self.download_video, daemon=True)
        self.download_thread.start()
    
    def cancel_download(self):
        self.is_downloading = False
        self.status_var.set("下载已取消")
        self.reset_ui()
    
    def reset_ui(self):
        self.is_downloading = False
        self.download_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
    
    def save_config(self):
        """保存配置"""
        config = {
            'download_path': self.download_path.get(),
            'quality': self.quality_var.get(),
            'format': self.format_var.get(),
            'proxy': self.proxy_var.get(),
            'use_proxy': self.use_proxy_var.get(),
            'subtitle': self.subtitle_var.get(),
            'embed_subtitle': self.embed_subtitle_var.get(),  # 新增
            'thumbnail': self.thumbnail_var.get(),
            'auto_number': self.auto_number_var.get(),
            'speed_limit': self.speed_limit_var.get(),
            'naming_template': self.naming_var.get(),
            'history': self.download_history
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("成功", "配置已保存！")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
    
    def load_config(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                self.download_path.set(config.get('download_path', str(Path.home() / "Downloads")))
                self.quality_var.set(config.get('quality', '最高画质'))
                self.format_var.set(config.get('format', 'MP4'))
                self.proxy_var.set(config.get('proxy', ''))
                self.use_proxy_var.set(config.get('use_proxy', False))
                self.subtitle_var.set(config.get('subtitle', False))
                self.embed_subtitle_var.set(config.get('embed_subtitle', True))  # 新增
                self.thumbnail_var.set(config.get('thumbnail', False))
                self.auto_number_var.set(config.get('auto_number', True))
                self.speed_limit_var.set(config.get('speed_limit', '无限制'))
                self.naming_var = ctk.StringVar(value=config.get('naming_template', '%(title)s.%(ext)s'))
                self.download_history = config.get('history', [])
            except:
                pass

if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()