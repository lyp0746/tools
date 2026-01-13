#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StreamForge Elite - 全能流媒体终端
基于 yt-dlp 与 FFmpeg 的多站点解析与批量下载工具
功能：拖放导入、批量解析、下载限速、格式预设等
- 键盘快捷键
- 更优化的布局
作者：LYP
GitHub：https://github.com/lyp0746
邮箱：1610369302@qq.com
版本：10.0.0
"""


import json
import os
import sys
import threading
import time
import uuid
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSettings, QUrl, QSize
)
from PyQt5.QtGui import (
    QFont, QColor, QPalette, QDesktopServices, QIcon, QKeySequence
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox, QSpinBox,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QFileDialog, QMessageBox,
    QTabWidget, QGroupBox, QSplitter, QMenu, QAction,
    QSystemTrayIcon, QStyle, QScrollArea, QGridLayout, QProgressBar,
    QDoubleSpinBox, QFrame, QShortcut, QPlainTextEdit
)

# 核心依赖检查
try:
    import yt_dlp
except ImportError:
    app = QApplication(sys.argv)
    QMessageBox.critical(
        None, "关键依赖缺失",
        "未找到 yt-dlp 库。\n\n请在终端运行:\npip install yt-dlp"
    )
    sys.exit(1)

# 应用配置
APP_NAME = "StreamForge Elite"
APP_VERSION = "10.0"
CONFIG_FILE = Path.cwd() / ".streamforge_v10_config.json"
QUEUE_FILE = Path.cwd() / ".streamforge_v10_queue.json"
PRESET_FILE = Path.cwd() / ".streamforge_v10_presets.json"
TEST_URL = "https://www.youtube.com/watch?v=BaW_jenozKc"


# ============================================================================
#                              Worker 线程类
# ============================================================================

class AnalyzerWorker(QThread):
    """解析视频信息的后台线程"""
    finished = pyqtSignal(list, str)  # (results, error_msg)
    progress = pyqtSignal(str, int)  # 进度消息, 百分比
    count_updated = pyqtSignal(int, int)  # 当前数, 总数

    def __init__(self, urls: List[str], proxy: str = "", cookie_browser: str = "None"):
        super().__init__()
        self.urls = urls
        self.proxy = proxy
        self.cookie_browser = cookie_browser
        self.is_stopped = False

    def stop(self):
        self.is_stopped = True

    def run(self):
        all_results = []
        total_urls = len(self.urls)

        for idx, url in enumerate(self.urls, 1):
            if self.is_stopped:
                break

            try:
                opts = {
                    'extract_flat': 'in_playlist',
                    'ignoreerrors': True,
                    'quiet': True,
                    'no_warnings': True
                }

                if self.proxy:
                    opts['proxy'] = self.proxy

                if self.cookie_browser != "None":
                    opts['cookiesfrombrowser'] = (self.cookie_browser,)

                self.progress.emit(f"正在解析 [{idx}/{total_urls}]: {url[:80]}...",
                                 int((idx - 1) / total_urls * 100))

                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                # 处理单视频和播放列表
                entries = []
                if 'entries' in info:
                    entries = [e for e in info['entries'] if e]
                else:
                    entries = [info]

                for ent in entries:
                    if self.is_stopped:
                        break

                    dur = ent.get('duration')
                    dur_str = f"{int(dur) // 60}:{int(dur) % 60:02d}" if dur else "直播/未知"

                    all_results.append({
                        'uuid': str(uuid.uuid4()),
                        'url': ent.get('url') or ent.get('webpage_url') or url,
                        'title': ent.get('title', '未知标题'),
                        'video_id': ent.get('id'),
                        'duration': dur_str,
                        'uploader': ent.get('uploader') or ent.get('channel') or '未知',
                        'thumbnail': ent.get('thumbnail', ''),
                        'view_count': ent.get('view_count', 0),
                        'upload_date': ent.get('upload_date', '')
                    })

                self.count_updated.emit(len(all_results), total_urls)

            except Exception as e:
                self.progress.emit(f"解析失败 [{idx}/{total_urls}]: {str(e)[:100]}",
                                 int(idx / total_urls * 100))

        if not self.is_stopped:
            self.finished.emit(all_results, "")
        else:
            self.finished.emit(all_results, "用户停止")


class DownloadWorker(QThread):
    """下载任务的后台线程"""
    progress = pyqtSignal(str, str, str, str)  # (task_id, progress%, speed, status)
    task_finished = pyqtSignal(str, bool, str)  # (task_id, success, message)
    log = pyqtSignal(str, str)  # (message, level)
    overall_progress = pyqtSignal(int, int)  # 当前完成数, 总数

    def __init__(self, tasks: List[Dict], settings: Dict, save_dir: str):
        super().__init__()
        self.tasks = tasks
        self.settings = settings
        self.save_dir = save_dir
        self.is_stopped = False
        self.completed_count = 0

    def stop(self):
        self.is_stopped = True

    def run(self):
        save_path = Path(self.save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        base_opts = {
            'outtmpl': str(save_path / '%(title)s [%(id)s].%(ext)s'),
            'ignoreerrors': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'concurrent_fragment_downloads': self.settings.get('threads', 8),
            'retries': 10,
            'writethumbnail': self.settings.get('embed_thumb', True),
        }

        if self.settings.get('clean_name', True):
            base_opts['restrictfilenames'] = True

        if self.settings.get('proxy', ''):
            base_opts['proxy'] = self.settings['proxy']

        # 限速
        if self.settings.get('rate_limit', 0) > 0:
            base_opts['ratelimit'] = int(self.settings['rate_limit'] * 1024 * 1024)

        total_tasks = len(self.tasks)

        for task in self.tasks:
            if self.is_stopped:
                break

            tid = task['uuid']
            self.log.emit(f"开始下载: {task['title']}", "INFO")
            self.progress.emit(tid, "0%", "初始化...", "下载中")

            opts = base_opts.copy()

            # Cookie
            if task.get('cookie_browser', 'None') != 'None':
                opts['cookiesfrombrowser'] = (task['cookie_browser'],)

            # 时间切片
            if task.get('time_range'):
                try:
                    start, end = task['time_range'].split('-')
                    opts['download_ranges'] = yt_dlp.utils.download_range_func(
                        None, [[self._parse_time(start), self._parse_time(end)]]
                    )
                    opts['force_keyframes_at_cuts'] = True
                except:
                    pass

            # 字幕
            opts['postprocessors'] = []
            if self.settings.get('embed_sub', True):
                opts['writesubtitles'] = True
                sub_lang = task.get('sub_lang', 'all')
                if sub_lang != 'all':
                    opts['subtitleslangs'] = [sub_lang]
                else:
                    opts['writeautomaticsub'] = True
                opts['postprocessors'].append({'key': 'FFmpegEmbedSubtitle'})

            # 模式配置
            if task['mode'] == 'audio':
                opts['format'] = 'bestaudio/best'
                opts['postprocessors'].append({
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': task['aud_fmt'],
                    'preferredquality': task['aud_br']
                })
            else:
                res_map = {"4K": 2160, "2K": 1440, "1080p": 1080, "720p": 720, "480p": 480, "360p": 360}
                h = res_map.get(task['res'], 1080)
                if task['res'] == "Best":
                    opts['format'] = "bestvideo+bestaudio/best"
                else:
                    opts['format'] = f"bv*[height<={h}]+ba/b[height<={h}]"
                opts['merge_output_format'] = task['vid_fmt']

            # 缩略图 + 元数据
            if self.settings.get('embed_thumb', True):
                opts['postprocessors'].append({'key': 'EmbedThumbnail'})

            opts['postprocessors'].append({'key': 'FFmpegMetadata'})

            # 进度回调
            last_update = [0]

            def progress_hook(d):
                if self.is_stopped:
                    raise yt_dlp.utils.DownloadError("Stopped by user")

                if d['status'] == 'downloading':
                    now = time.time()
                    if now - last_update[0] > 0.5:
                        last_update[0] = now
                        percent = d.get('_percent_str', '?%').strip()
                        speed = d.get('_speed_str', 'N/A')
                        self.progress.emit(tid, percent, speed, "下载中")

                elif d['status'] == 'finished':
                    self.progress.emit(tid, "100%", "处理中...", "后处理")

            opts['progress_hooks'] = [progress_hook]

            # 执行下载
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([task['url']])

                self.completed_count += 1
                self.task_finished.emit(tid, True, "完成")
                self.log.emit(f"下载完成: {task['title']}", "SUCCESS")
                self.overall_progress.emit(self.completed_count, total_tasks)

            except Exception as e:
                if self.is_stopped:
                    self.task_finished.emit(tid, False, "已停止")
                    self.log.emit(f"任务停止: {task['title']}", "WARN")
                else:
                    self.task_finished.emit(tid, False, f"失败: {str(e)[:100]}")
                    self.log.emit(f"下载失败: {task['title']} - {str(e)}", "ERROR")

    def _parse_time(self, time_str: str) -> int:
        """将时间字符串转换为秒"""
        try:
            parts = list(map(int, time_str.strip().split(':')))
            if len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
            elif len(parts) == 2:
                return parts[0] * 60 + parts[1]
            return parts[0]
        except:
            return 0


# ============================================================================
#                              主窗口类
# ============================================================================

class StreamForgeElite(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1400, 900)
        self.resize(1650, 980)

        # 数据存储
        self.analysis_cache: Dict = {}
        self.queue_data: Dict = {}
        self.queue_order: List = []
        self.is_downloading = False
        self.is_analyzing = False

        # Worker 线程
        self.analyzer_worker: Optional[AnalyzerWorker] = None
        self.download_worker: Optional[DownloadWorker] = None

        # 设置
        self.settings = QSettings('StreamForge', 'EliteV10')
        self.dark_mode = self.settings.value('dark_mode', False, bool)

        # 格式预设
        self.format_presets = self.load_presets()

        # 初始化UI
        self.init_ui()
        self.setup_theme()
        self.setup_shortcuts()
        self.load_config()
        self.load_queue()
        self.check_environment()

        # 系统托盘
        self.setup_tray()

    def init_ui(self):
        """初始化界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # 顶部工具栏
        self.create_toolbar(main_layout)

        # URL输入区
        self.create_url_input(main_layout)

        # 解析进度条
        self.progress_analyze = QProgressBar()
        self.progress_analyze.setVisible(False)
        self.progress_analyze.setMaximumHeight(8)
        self.progress_analyze.setTextVisible(False)
        main_layout.addWidget(self.progress_analyze)

        # 主分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter, stretch=1)

        # 左侧设置面板（可滚动）
        left_panel = self.create_left_panel_scrollable()
        splitter.addWidget(left_panel)

        # 右侧任务面板
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # 初始分割比例 - 给右侧更多空间
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)
        splitter.setSizes([450, 1200])

        # 底部控制栏
        self.create_bottom_controls(main_layout)

        # 创建菜单栏
        self.create_menubar()

        # 状态栏
        self.statusBar().showMessage("系统就绪 | PyQt5 重构版")

    def create_toolbar(self, layout):
        """创建顶部工具栏"""
        toolbar = QHBoxLayout()
        toolbar.setSpacing(15)

        # 标题
        title = QLabel(f"⚡ {APP_NAME}")
        title_font = QFont("Arial", 20, QFont.Bold)
        title.setFont(title_font)
        toolbar.addWidget(title)

        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setStyleSheet("color: gray; font-size: 11px;")
        toolbar.addWidget(version_label)

        toolbar.addStretch()

        # 格式预设
        toolbar.addWidget(QLabel("快捷预设:"))
        self.combo_preset = QComboBox()
        self.update_preset_combo()
        self.combo_preset.setFixedWidth(150)
        self.combo_preset.currentTextChanged.connect(self.apply_preset)
        toolbar.addWidget(self.combo_preset)

        btn_save_preset = QPushButton("💾")
        btn_save_preset.setFixedSize(35, 35)
        btn_save_preset.setToolTip("保存当前设置为预设")
        btn_save_preset.clicked.connect(self.save_current_preset)
        toolbar.addWidget(btn_save_preset)

        # 主题切换按钮
        self.btn_theme = QPushButton("🌙 深色" if not self.dark_mode else "☀️ 浅色")
        self.btn_theme.setFixedSize(100, 38)
        self.btn_theme.clicked.connect(self.toggle_theme)
        toolbar.addWidget(self.btn_theme)

        # 最小化到托盘
        btn_tray = QPushButton("📌 托盘")
        btn_tray.setFixedSize(80, 38)
        btn_tray.clicked.connect(self.hide)
        toolbar.addWidget(btn_tray)

        layout.addLayout(toolbar)

    def create_url_input(self, layout):
        """创建URL输入区"""
        group = QGroupBox("📎 视频链接输入 (支持拖放)")
        group.setMaximumHeight(140)
        group_layout = QVBoxLayout()
        group_layout.setSpacing(10)

        # URL输入
        input_row = QHBoxLayout()
        self.url_input = QPlainTextEdit()
        self.url_input.setPlaceholderText(
            "粘贴 YouTube、Bilibili、Twitter 等平台的视频/播放列表链接...\n"
            "支持多行输入，每行一个链接"
        )
        self.url_input.setFont(QFont("Consolas", 10))
        self.url_input.setMaximumHeight(70)
        self.url_input.setAcceptDrops(True)
        self.url_input.dragEnterEvent = self.drag_enter_event
        self.url_input.dropEvent = self.drop_event
        input_row.addWidget(self.url_input, stretch=1)

        buttons_col = QVBoxLayout()
        buttons_col.setSpacing(5)

        btn_clear = QPushButton("清空")
        btn_clear.setFixedSize(70, 30)
        btn_clear.clicked.connect(lambda: self.url_input.clear())
        buttons_col.addWidget(btn_clear)

        btn_paste = QPushButton("粘贴")
        btn_paste.setFixedSize(70, 30)
        btn_paste.clicked.connect(self.paste_from_clipboard)
        buttons_col.addWidget(btn_paste)

        input_row.addLayout(buttons_col)
        group_layout.addLayout(input_row)

        # 控制按钮行
        control_row = QHBoxLayout()
        control_row.setSpacing(10)

        self.btn_analyze = QPushButton("🔍 智能解析")
        self.btn_analyze.setFixedSize(140, 40)
        self.btn_analyze.clicked.connect(self.analyze_url)
        self.btn_analyze.setProperty('class', 'accent')
        control_row.addWidget(self.btn_analyze)

        self.btn_stop_analyze = QPushButton("⏹ 停止")
        self.btn_stop_analyze.setFixedSize(90, 40)
        self.btn_stop_analyze.setVisible(False)
        self.btn_stop_analyze.clicked.connect(self.stop_analyze)
        self.btn_stop_analyze.setProperty('class', 'danger')
        control_row.addWidget(self.btn_stop_analyze)

        control_row.addSpacing(20)

        self.chk_clipboard = QCheckBox("剪贴板监听")
        self.chk_clipboard.stateChanged.connect(self.toggle_clipboard_monitor)
        control_row.addWidget(self.chk_clipboard)

        self.chk_auto_add = QCheckBox("解析后自动添加")
        control_row.addWidget(self.chk_auto_add)

        control_row.addStretch()

        # 统计标签
        self.label_analyze_stats = QLabel("待解析: 0")
        self.label_analyze_stats.setStyleSheet("font-weight: bold; color: #0078d4;")
        control_row.addWidget(self.label_analyze_stats)

        group_layout.addLayout(control_row)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def create_left_panel_scrollable(self):
        """创建左侧可滚动设置面板"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setMinimumWidth(420)
        scroll.setMaximumWidth(600)

        # 容器
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 1. 格式与画质
        self.create_format_group(layout)

        # 2. 身份验证
        self.create_auth_group(layout)

        # 3. 字幕设置
        self.create_subtitle_group(layout)

        # 4. 时间切片
        self.create_timeslice_group(layout)

        # 5. 网络与加速
        self.create_network_group(layout)

        # 6. 文件与元数据
        self.create_file_group(layout)

        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    def create_format_group(self, layout):
        """格式与画质组"""
        group = QGroupBox("⚙️ 格式与画质")
        group_layout = QVBoxLayout()
        group_layout.setSpacing(12)

        # 视频模式
        video_frame = QFrame()
        video_layout = QGridLayout(video_frame)
        video_layout.setSpacing(10)
        video_layout.setContentsMargins(5, 5, 5, 5)

        self.radio_video = QCheckBox("📹 视频下载")
        self.radio_video.setChecked(True)
        self.radio_video.setFont(QFont("Arial", 10, QFont.Bold))
        self.radio_video.toggled.connect(self.update_format_ui)
        video_layout.addWidget(self.radio_video, 0, 0, 1, 4)

        video_layout.addWidget(QLabel("分辨率:"), 1, 0)
        self.combo_res = QComboBox()
        self.combo_res.addItems(["Best", "4K", "2K", "1080p", "720p", "480p", "360p"])
        self.combo_res.setCurrentText("1080p")
        self.combo_res.setMinimumWidth(110)
        video_layout.addWidget(self.combo_res, 1, 1)

        video_layout.addWidget(QLabel("格式:"), 1, 2)
        self.combo_vid_fmt = QComboBox()
        self.combo_vid_fmt.addItems(["mp4", "mkv", "webm", "avi"])
        self.combo_vid_fmt.setMinimumWidth(90)
        video_layout.addWidget(self.combo_vid_fmt, 1, 3)

        video_frame.setFrameStyle(QFrame.StyledPanel)
        group_layout.addWidget(video_frame)

        # 音频模式
        audio_frame = QFrame()
        audio_layout = QGridLayout(audio_frame)
        audio_layout.setSpacing(10)
        audio_layout.setContentsMargins(5, 5, 5, 5)

        self.radio_audio = QCheckBox("🎵 音频提取")
        self.radio_audio.setFont(QFont("Arial", 10, QFont.Bold))
        self.radio_audio.toggled.connect(self.update_format_ui)
        audio_layout.addWidget(self.radio_audio, 0, 0, 1, 4)

        audio_layout.addWidget(QLabel("格式:"), 1, 0)
        self.combo_aud_fmt = QComboBox()
        self.combo_aud_fmt.addItems(["mp3", "m4a", "flac", "opus", "wav"])
        self.combo_aud_fmt.setMinimumWidth(110)
        audio_layout.addWidget(self.combo_aud_fmt, 1, 1)

        audio_layout.addWidget(QLabel("码率:"), 1, 2)
        self.combo_aud_br = QComboBox()
        self.combo_aud_br.addItems(["320", "256", "192", "128", "96"])
        self.combo_aud_br.setMinimumWidth(90)
        audio_layout.addWidget(self.combo_aud_br, 1, 3)

        audio_frame.setFrameStyle(QFrame.StyledPanel)
        group_layout.addWidget(audio_frame)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def create_auth_group(self, layout):
        """身份验证组"""
        group = QGroupBox("🍪 身份验证")
        group_layout = QVBoxLayout()
        group_layout.setSpacing(10)

        hint = QLabel("从浏览器获取 Cookie (解决会员/年龄限制/高清视频)")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray; font-size: 9px;")
        group_layout.addWidget(hint)

        self.combo_cookie = QComboBox()
        self.combo_cookie.addItems([
            "None (不使用)", "chrome", "firefox", "edge",
            "opera", "brave", "safari", "chromium"
        ])
        self.combo_cookie.setMinimumHeight(30)
        group_layout.addWidget(self.combo_cookie)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def create_subtitle_group(self, layout):
        """字幕设置组"""
        group = QGroupBox("📝 字幕设置")
        group_layout = QVBoxLayout()
        group_layout.setSpacing(10)

        self.chk_embed_sub = QCheckBox("下载字幕并自动内嵌")
        self.chk_embed_sub.setChecked(True)
        group_layout.addWidget(self.chk_embed_sub)

        sub_lang_layout = QHBoxLayout()
        sub_lang_layout.addWidget(QLabel("语言:"))
        self.combo_sub_lang = QComboBox()
        self.combo_sub_lang.addItems([
            "all (全部)", "zh-Hans (简中)", "zh-Hant (繁中)",
            "en (英)", "ja (日)", "ko (韩)", "fr (法)", "es (西)", "de (德)"
        ])
        self.combo_sub_lang.setMinimumHeight(30)
        sub_lang_layout.addWidget(self.combo_sub_lang, stretch=1)
        group_layout.addLayout(sub_lang_layout)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def create_timeslice_group(self, layout):
        """时间切片组"""
        group = QGroupBox("✂️ 视频截取 (可选)")
        group_layout = QVBoxLayout()
        group_layout.setSpacing(10)

        time_layout = QHBoxLayout()
        time_layout.setSpacing(8)

        time_layout.addWidget(QLabel("起始:"))
        self.edit_time_start = QLineEdit()
        self.edit_time_start.setPlaceholderText("00:00:00")
        self.edit_time_start.setFixedWidth(90)
        time_layout.addWidget(self.edit_time_start)

        time_layout.addWidget(QLabel("→"))

        time_layout.addWidget(QLabel("结束:"))
        self.edit_time_end = QLineEdit()
        self.edit_time_end.setPlaceholderText("00:10:00")
        self.edit_time_end.setFixedWidth(90)
        time_layout.addWidget(self.edit_time_end)

        time_layout.addStretch()
        group_layout.addLayout(time_layout)

        hint = QLabel("格式: HH:MM:SS 或 MM:SS (留空表示完整下载)")
        hint.setStyleSheet("color: gray; font-size: 9px;")
        hint.setWordWrap(True)
        group_layout.addWidget(hint)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def create_network_group(self, layout):
        """网络与加速组"""
        group = QGroupBox("🚀 网络与加速")
        group_layout = QVBoxLayout()
        group_layout.setSpacing(12)

        # 并发线程
        thread_layout = QHBoxLayout()
        thread_layout.addWidget(QLabel("并发线程数:"))
        self.spin_threads = QSpinBox()
        self.spin_threads.setRange(1, 32)
        self.spin_threads.setValue(8)
        self.spin_threads.setSuffix(" 线程")
        self.spin_threads.setMinimumWidth(120)
        self.spin_threads.setMinimumHeight(30)
        thread_layout.addWidget(self.spin_threads)
        thread_layout.addStretch()
        group_layout.addLayout(thread_layout)

        # 限速
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("限速 (MB/s):"))
        self.spin_rate_limit = QDoubleSpinBox()
        self.spin_rate_limit.setRange(0, 1000)
        self.spin_rate_limit.setValue(0)
        self.spin_rate_limit.setSuffix(" MB/s")
        self.spin_rate_limit.setSpecialValueText("不限速")
        self.spin_rate_limit.setMinimumWidth(120)
        self.spin_rate_limit.setMinimumHeight(30)
        speed_layout.addWidget(self.spin_rate_limit)
        speed_layout.addStretch()
        group_layout.addLayout(speed_layout)

        # 代理设置
        group_layout.addWidget(QLabel("代理地址 (可选):"))
        self.edit_proxy = QLineEdit()
        self.edit_proxy.setPlaceholderText("例: http://127.0.0.1:7890 或 socks5://...")
        self.edit_proxy.setMinimumHeight(30)
        group_layout.addWidget(self.edit_proxy)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def create_file_group(self, layout):
        """文件与元数据组"""
        group = QGroupBox("🧩 文件与元数据")
        group_layout = QVBoxLayout()
        group_layout.setSpacing(10)

        self.chk_clean_name = QCheckBox("清理文件名 (移除特殊字符)")
        self.chk_clean_name.setChecked(True)
        group_layout.addWidget(self.chk_clean_name)

        self.chk_embed_thumb = QCheckBox("嵌入视频封面缩略图 (需 FFmpeg)")
        self.chk_embed_thumb.setChecked(True)
        group_layout.addWidget(self.chk_embed_thumb)

        self.chk_write_desc = QCheckBox("保存视频描述为 .txt")
        group_layout.addWidget(self.chk_write_desc)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def create_right_panel(self):
        """创建右侧任务面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)

        # Tab 控件
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)

        # Tab 1: 资源选择
        self.tree_inspect = QTreeWidget()
        self.tree_inspect.setHeaderLabels(["UUID", "标题", "时长", "上传者", "播放量"])
        self.tree_inspect.setColumnWidth(0, 0)  # 隐藏UUID列
        self.tree_inspect.setColumnWidth(1, 550)
        self.tree_inspect.setColumnWidth(2, 100)
        self.tree_inspect.setColumnWidth(3, 200)
        self.tree_inspect.setColumnWidth(4, 120)
        self.tree_inspect.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.tree_inspect.setAlternatingRowColors(True)
        self.tree_inspect.header().setStretchLastSection(True)
        self.tree_inspect.setSortingEnabled(True)

        inspect_widget = QWidget()
        inspect_layout = QVBoxLayout(inspect_widget)
        inspect_layout.setContentsMargins(0, 0, 0, 0)
        inspect_layout.setSpacing(8)
        inspect_layout.addWidget(self.tree_inspect)

        inspect_buttons = QHBoxLayout()
        inspect_buttons.setSpacing(10)

        btn_select_all = QPushButton("全选")
        btn_select_all.setFixedSize(70, 35)
        btn_select_all.clicked.connect(self.tree_inspect.selectAll)
        inspect_buttons.addWidget(btn_select_all)

        btn_deselect = QPushButton("取消")
        btn_deselect.setFixedSize(70, 35)
        btn_deselect.clicked.connect(self.tree_inspect.clearSelection)
        inspect_buttons.addWidget(btn_deselect)

        btn_invert = QPushButton("反选")
        btn_invert.setFixedSize(70, 35)
        btn_invert.clicked.connect(self.invert_selection_inspect)
        inspect_buttons.addWidget(btn_invert)

        inspect_buttons.addStretch()

        self.label_inspect_count = QLabel("已解析: 0 项")
        self.label_inspect_count.setStyleSheet("font-weight: bold;")
        inspect_buttons.addWidget(self.label_inspect_count)

        inspect_buttons.addSpacing(15)

        self.btn_add_queue = QPushButton("⬇ 添加到下载队列")
        self.btn_add_queue.setProperty('class', 'accent')
        self.btn_add_queue.setMinimumHeight(40)
        self.btn_add_queue.setMinimumWidth(160)
        self.btn_add_queue.clicked.connect(self.add_to_queue)
        inspect_buttons.addWidget(self.btn_add_queue)

        inspect_layout.addLayout(inspect_buttons)
        self.tabs.addTab(inspect_widget, "1️⃣ 资源选择")

        # Tab 2: 任务队列
        self.tree_queue = QTreeWidget()
        self.tree_queue.setHeaderLabels(["UUID", "标题", "状态", "进度", "速度/信息"])
        self.tree_queue.setColumnWidth(0, 0)  # 隐藏UUID
        self.tree_queue.setColumnWidth(1, 500)
        self.tree_queue.setColumnWidth(2, 100)
        self.tree_queue.setColumnWidth(3, 100)
        self.tree_queue.setColumnWidth(4, 250)
        self.tree_queue.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.tree_queue.setAlternatingRowColors(True)
        self.tree_queue.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_queue.customContextMenuRequested.connect(self.show_queue_context_menu)
        self.tree_queue.header().setStretchLastSection(True)

        queue_widget = QWidget()
        queue_layout = QVBoxLayout(queue_widget)
        queue_layout.setContentsMargins(0, 0, 0, 0)
        queue_layout.setSpacing(8)
        queue_layout.addWidget(self.tree_queue)

        queue_buttons = QHBoxLayout()
        queue_buttons.setSpacing(10)

        btn_clear_done = QPushButton("清空已完成")
        btn_clear_done.setFixedHeight(35)
        btn_clear_done.clicked.connect(self.clear_done_tasks)
        queue_buttons.addWidget(btn_clear_done)

        btn_remove = QPushButton("删除选中")
        btn_remove.setFixedHeight(35)
        btn_remove.clicked.connect(self.remove_selected_tasks)
        queue_buttons.addWidget(btn_remove)

        queue_buttons.addStretch()

        # 队列统计
        self.label_stats = QLabel("总数: 0 | 等待: 0 | 进行: 0 | 完成: 0 | 失败: 0")
        self.label_stats.setStyleSheet("font-weight: bold; font-size: 11px;")
        queue_buttons.addWidget(self.label_stats)

        queue_layout.addLayout(queue_buttons)
        self.tabs.addTab(queue_widget, "2️⃣ 任务队列")

        # Tab 3: 系统日志
        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)
        self.text_log.setFont(QFont("Consolas", 9))

        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(8)
        log_layout.addWidget(self.text_log)

        log_buttons = QHBoxLayout()
        log_buttons.setSpacing(10)

        btn_clear_log = QPushButton("清空日志")
        btn_clear_log.setFixedHeight(35)
        btn_clear_log.clicked.connect(self.text_log.clear)
        log_buttons.addWidget(btn_clear_log)

        btn_export_log = QPushButton("导出日志")
        btn_export_log.setFixedHeight(35)
        btn_export_log.clicked.connect(self.export_log)
        log_buttons.addWidget(btn_export_log)

        log_buttons.addStretch()
        log_layout.addLayout(log_buttons)

        self.tabs.addTab(log_widget, "3️⃣ 系统日志")

        layout.addWidget(self.tabs)
        return widget

    def create_bottom_controls(self, layout):
        """创建底部控制栏"""
        # 保存路径
        path_group = QGroupBox("💾 保存路径")
        path_layout = QHBoxLayout()
        path_layout.setSpacing(10)

        self.edit_save_dir = QLineEdit()
        self.edit_save_dir.setText(str(Path.home() / "Downloads"))
        self.edit_save_dir.setMinimumHeight(35)
        path_layout.addWidget(self.edit_save_dir, stretch=1)

        btn_browse = QPushButton("📂 浏览")
        btn_browse.setFixedSize(100, 38)
        btn_browse.clicked.connect(self.browse_save_dir)
        path_layout.addWidget(btn_browse)

        btn_open_dir = QPushButton("打开文件夹")
        btn_open_dir.setFixedSize(120, 38)
        btn_open_dir.clicked.connect(self.open_save_dir)
        path_layout.addWidget(btn_open_dir)

        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        # 下载进度
        self.progress_download = QProgressBar()
        self.progress_download.setVisible(False)
        self.progress_download.setMaximumHeight(20)
        self.progress_download.setFormat("总进度: %p% (%v/%m)")
        layout.addWidget(self.progress_download)

        # 控制按钮
        controls = QHBoxLayout()
        controls.setSpacing(15)

        # 完成后动作
        controls.addWidget(QLabel("完成后:"))
        self.combo_post_action = QComboBox()
        self.combo_post_action.addItems([
            "无操作", "关闭程序", "关机", "休眠"
        ])
        self.combo_post_action.setFixedWidth(120)
        self.combo_post_action.setMinimumHeight(35)
        controls.addWidget(self.combo_post_action)

        controls.addStretch()

        # 速度显示
        self.label_speed = QLabel("")
        self.label_speed.setStyleSheet("font-weight: bold; color: #0078d4; font-size: 13px;")
        controls.addWidget(self.label_speed)

        controls.addSpacing(20)

        # 停止按钮
        self.btn_stop = QPushButton("⏹ 停止")
        self.btn_stop.setFixedSize(110, 45)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_download)
        self.btn_stop.setProperty('class', 'danger')
        controls.addWidget(self.btn_stop)

        # 开始按钮
        self.btn_start = QPushButton("▶ 开始所有任务")
        self.btn_start.setFixedSize(170, 45)
        self.btn_start.clicked.connect(self.start_download)
        self.btn_start.setProperty('class', 'accent')
        controls.addWidget(self.btn_start)

        layout.addLayout(controls)

    def create_menubar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        action_open_dir = QAction("打开保存目录", self)
        action_open_dir.setShortcut("Ctrl+O")
        action_open_dir.triggered.connect(self.open_save_dir)
        file_menu.addAction(action_open_dir)

        file_menu.addSeparator()

        action_export = QAction("导出任务队列...", self)
        action_export.setShortcut("Ctrl+E")
        action_export.triggered.connect(self.export_queue)
        file_menu.addAction(action_export)

        action_import = QAction("导入任务队列...", self)
        action_import.setShortcut("Ctrl+I")
        action_import.triggered.connect(self.import_queue)
        file_menu.addAction(action_import)

        file_menu.addSeparator()

        action_exit = QAction("退出", self)
        action_exit.setShortcut("Ctrl+Q")
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")

        action_clear_input = QAction("清空输入", self)
        action_clear_input.setShortcut("Ctrl+L")
        action_clear_input.triggered.connect(lambda: self.url_input.clear())
        edit_menu.addAction(action_clear_input)

        action_paste = QAction("粘贴到输入框", self)
        action_paste.setShortcut("Ctrl+V")
        action_paste.triggered.connect(self.paste_from_clipboard)
        edit_menu.addAction(action_paste)

        # 工具菜单
        tools_menu = menubar.addMenu("工具")

        action_check_env = QAction("环境自检", self)
        action_check_env.triggered.connect(self.check_environment_detailed)
        tools_menu.addAction(action_check_env)

        action_self_test = QAction("一键自测", self)
        action_self_test.triggered.connect(self.self_test)
        tools_menu.addAction(action_self_test)

        tools_menu.addSeparator()

        action_manage_presets = QAction("管理格式预设...", self)
        action_manage_presets.triggered.connect(self.manage_presets)
        tools_menu.addAction(action_manage_presets)

        tools_menu.addSeparator()

        action_clear_cache = QAction("清空缓存数据", self)
        action_clear_cache.triggered.connect(self.clear_cache)
        tools_menu.addAction(action_clear_cache)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        action_about = QAction("关于", self)
        action_about.triggered.connect(self.show_about)
        help_menu.addAction(action_about)

        action_docs = QAction("使用文档", self)
        action_docs.triggered.connect(
            lambda: webbrowser.open("https://github.com/yt-dlp/yt-dlp")
        )
        help_menu.addAction(action_docs)

        action_shortcuts = QAction("快捷键", self)
        action_shortcuts.setShortcut("F1")
        action_shortcuts.triggered.connect(self.show_shortcuts)
        help_menu.addAction(action_shortcuts)

    def setup_shortcuts(self):
        """设置快捷键"""
        # Ctrl+Enter: 开始下载
        QShortcut(QKeySequence("Ctrl+Return"), self, self.start_download)

        # Ctrl+Shift+A: 解析URL
        QShortcut(QKeySequence("Ctrl+Shift+A"), self, self.analyze_url)

        # Delete: 删除选中任务
        QShortcut(QKeySequence("Delete"), self, self.remove_selected_tasks)

    def setup_tray(self):
        """设置系统托盘"""
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.tray.setToolTip(f"{APP_NAME} v{APP_VERSION}")

        tray_menu = QMenu()

        action_show = QAction("显示主窗口", self)
        action_show.triggered.connect(self.show)
        tray_menu.addAction(action_show)

        action_quit = QAction("退出", self)
        action_quit.triggered.connect(self.close)
        tray_menu.addAction(action_quit)

        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self.tray_activated)
        self.tray.show()

    def tray_activated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()

    # ========================================================================
    #                              主题相关
    # ========================================================================

    def setup_theme(self):
        """设置应用主题"""
        if self.dark_mode:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

    def toggle_theme(self):
        """切换主题"""
        self.dark_mode = not self.dark_mode
        self.settings.setValue('dark_mode', self.dark_mode)
        self.setup_theme()
        self.btn_theme.setText("☀️ 浅色" if self.dark_mode else "🌙 深色")

    def apply_light_theme(self):
        """浅色主题"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(245, 245, 245))
        palette.setColor(QPalette.WindowText, QColor(40, 40, 40))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(248, 248, 248))
        palette.setColor(QPalette.Text, QColor(40, 40, 40))
        palette.setColor(QPalette.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ButtonText, QColor(40, 40, 40))
        QApplication.setPalette(palette)

        style = """
            QPushButton {
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 6px 14px;
                background: #f5f5f5;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #e5e5e5;
                border: 1px solid #999;
            }
            QPushButton[class="accent"] {
                background: #0078d4;
                color: white;
                border: none;
                font-weight: bold;
            }
            QPushButton[class="accent"]:hover {
                background: #106ebe;
            }
            QPushButton[class="danger"] {
                background: #d13438;
                color: white;
                border: none;
                font-weight: bold;
            }
            QPushButton[class="danger"]:hover {
                background: #a52931;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #d0d0d0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
            }
            QTreeWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px;
            }
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 4px;
            }
        """
        QApplication.instance().setStyleSheet(style)

    def apply_dark_theme(self):
        """深色主题"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(32, 32, 32))
        palette.setColor(QPalette.WindowText, QColor(224, 224, 224))
        palette.setColor(QPalette.Base, QColor(45, 45, 45))
        palette.setColor(QPalette.AlternateBase, QColor(40, 40, 40))
        palette.setColor(QPalette.Text, QColor(224, 224, 224))
        palette.setColor(QPalette.Button, QColor(50, 50, 50))
        palette.setColor(QPalette.ButtonText, QColor(224, 224, 224))
        QApplication.setPalette(palette)

        style = """
            QPushButton {
                border: 1px solid #505050;
                border-radius: 6px;
                padding: 6px 14px;
                background: #404040;
                color: #e0e0e0;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #505050;
                border: 1px solid #707070;
            }
            QPushButton[class="accent"] {
                background: #4cc2ff;
                color: #000;
                border: none;
                font-weight: bold;
            }
            QPushButton[class="accent"]:hover {
                background: #3aaeeb;
            }
            QPushButton[class="danger"] {
                background: #ff99a4;
                color: #000;
                border: none;
                font-weight: bold;
            }
            QPushButton[class="danger"]:hover {
                background: #eb8793;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #505050;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                padding: 15px;
                color: #e0e0e0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
            }
            QTreeWidget {
                border: 1px solid #505050;
                border-radius: 5px;
            }
            QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 4px;
                background: #3a3a3a;
            }
            QProgressBar {
                border: 1px solid #505050;
                border-radius: 5px;
                text-align: center;
                background: #2a2a2a;
            }
            QProgressBar::chunk {
                background-color: #4cc2ff;
                border-radius: 4px;
            }
        """
        QApplication.instance().setStyleSheet(style)

    # ========================================================================
    #                              功能实现
    # ========================================================================

    def log(self, message: str, level: str = "INFO"):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color_map = {
            "INFO": "#0078d4",
            "WARN": "#ffb900",
            "ERROR": "#d13438",
            "SUCCESS": "#107c10"
        }
        color = color_map.get(level, "#333333")

        html = f'<span style="color: gray;">[{timestamp}]</span> '
        html += f'<span style="color: {color}; font-weight: bold;">[{level}]</span> '
        html += f'<span>{message}</span>'

        self.text_log.append(html)

        # 自动滚动到底部
        scrollbar = self.text_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def drag_enter_event(self, event):
        """拖放进入事件"""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def drop_event(self, event):
        """拖放事件"""
        text = event.mimeData().text()
        if text:
            self.url_input.appendPlainText(text)
            self.statusBar().showMessage("已添加拖放的内容")

    def paste_from_clipboard(self):
        """从剪贴板粘贴"""
        text = QApplication.clipboard().text()
        if text:
            self.url_input.appendPlainText(text)
            self.statusBar().showMessage("已粘贴剪贴板内容")

    def analyze_url(self):
        """解析URL"""
        text = self.url_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请输入视频链接")
            return

        # 提取所有有效URL
        lines = text.split('\n')
        urls = []
        for line in lines:
            line = line.strip()
            if line and ('http://' in line or 'https://' in line):
                urls.append(line)

        if not urls:
            QMessageBox.warning(self, "提示", "未找到有效的URL链接")
            return

        self.is_analyzing = True
        self.btn_analyze.setEnabled(False)
        self.btn_stop_analyze.setVisible(True)
        self.progress_analyze.setVisible(True)
        self.progress_analyze.setValue(0)

        self.statusBar().showMessage(f"正在解析 {len(urls)} 个链接...")
        self.tree_inspect.clear()
        self.analysis_cache.clear()

        self.label_analyze_stats.setText(f"待解析: {len(urls)}")

        # 启动解析线程
        self.analyzer_worker = AnalyzerWorker(
            urls,
            self.edit_proxy.text(),
            self.combo_cookie.currentText().split()[0]
        )
        self.analyzer_worker.progress.connect(self.on_analyze_progress)
        self.analyzer_worker.count_updated.connect(self.on_analyze_count_updated)
        self.analyzer_worker.finished.connect(self.on_analyze_finished)
        self.analyzer_worker.start()

    def stop_analyze(self):
        """停止解析"""
        if self.analyzer_worker:
            self.analyzer_worker.stop()
            self.log("用户停止解析", "WARN")

    def on_analyze_progress(self, message: str, percentage: int):
        """解析进度更新"""
        self.log(message, "INFO")
        self.progress_analyze.setValue(percentage)

    def on_analyze_count_updated(self, current: int, total: int):
        """解析计数更新"""
        self.label_analyze_stats.setText(f"已解析: {current} / {total}")

    def on_analyze_finished(self, results: list, error: str):
        """解析完成"""
        self.is_analyzing = False
        self.btn_analyze.setEnabled(True)
        self.btn_stop_analyze.setVisible(False)
        self.progress_analyze.setVisible(False)

        if error and error != "用户停止":
            self.log(f"解析异常: {error}", "ERROR")

        if not results:
            QMessageBox.information(self, "提示", "未找到有效视频资源")
            self.statusBar().showMessage("解析完成，未找到资源")
            return

        # 填充结果
        for item in results:
            self.analysis_cache[item['uuid']] = item

            view_str = f"{item['view_count']:,}" if item['view_count'] > 0 else "未知"

            tree_item = QTreeWidgetItem([
                item['uuid'],
                item['title'],
                item['duration'],
                item['uploader'],
                view_str
            ])
            self.tree_inspect.addTopLevelItem(tree_item)

        self.label_inspect_count.setText(f"已解析: {len(results)} 项")
        self.log(f"解析完成: 发现 {len(results)} 个资源", "SUCCESS")
        self.statusBar().showMessage(f"解析完成: {len(results)} 个资源")
        self.tabs.setCurrentIndex(0)

        # 自动添加到队列
        if self.chk_auto_add.isChecked():
            self.tree_inspect.selectAll()
            self.add_to_queue()

    def invert_selection_inspect(self):
        """反选资源列表"""
        for i in range(self.tree_inspect.topLevelItemCount()):
            item = self.tree_inspect.topLevelItem(i)
            item.setSelected(not item.isSelected())

    def add_to_queue(self):
        """添加到下载队列"""
        selected = self.tree_inspect.selectedItems()
        if not selected:
            QMessageBox.information(self, "提示", "请先选择要下载的资源")
            return

        added = 0
        for item in selected:
            uid = item.text(0)
            meta = self.analysis_cache.get(uid)
            if not meta:
                continue

            # 获取当前配置
            task_id = str(uuid.uuid4())
            task = {
                'uuid': task_id,
                'url': meta['url'],
                'title': meta['title'],
                'video_id': meta.get('video_id'),
                'mode': 'video' if self.radio_video.isChecked() else 'audio',
                'res': self.combo_res.currentText(),
                'vid_fmt': self.combo_vid_fmt.currentText(),
                'aud_fmt': self.combo_aud_fmt.currentText(),
                'aud_br': self.combo_aud_br.currentText(),
                'cookie_browser': self.combo_cookie.currentText().split()[0],
                'sub_lang': self.combo_sub_lang.currentText().split()[0],
                'time_range': None,
                'status': 'Pending'
            }

            # 时间切片
            start = self.edit_time_start.text().strip()
            end = self.edit_time_end.text().strip()
            if start and end:
                task['time_range'] = f"{start}-{end}"

            self.queue_data[task_id] = task
            self.queue_order.append(task_id)

            # 添加到队列树
            info = "截取片段" if task['time_range'] else "完整下载"
            queue_item = QTreeWidgetItem([
                task_id,
                meta['title'],
                "等待中",
                "0%",
                info
            ])
            self.tree_queue.addTopLevelItem(queue_item)
            added += 1

        self.log(f"已添加 {added} 个任务到队列", "SUCCESS")
        self.statusBar().showMessage(f"已添加 {added} 个任务")
        self.tabs.setCurrentIndex(1)
        self.update_queue_stats()
        self.save_queue()

    def start_download(self):
        """开始下载"""
        if self.is_downloading:
            return

        # 获取待下载任务
        pending_tasks = [
            task for task in self.queue_data.values()
            if task['status'] == 'Pending'
        ]

        if not pending_tasks:
            QMessageBox.information(self, "提示", "队列中没有等待执行的任务")
            return

        self.is_downloading = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_download.setVisible(True)
        self.progress_download.setMaximum(len(pending_tasks))
        self.progress_download.setValue(0)
        self.statusBar().showMessage("下载进行中...")

        # 准备设置
        settings = {
            'threads': self.spin_threads.value(),
            'proxy': self.edit_proxy.text(),
            'clean_name': self.chk_clean_name.isChecked(),
            'embed_sub': self.chk_embed_sub.isChecked(),
            'embed_thumb': self.chk_embed_thumb.isChecked(),
            'rate_limit': self.spin_rate_limit.value()
        }

        # 启动下载线程
        self.download_worker = DownloadWorker(
            pending_tasks,
            settings,
            self.edit_save_dir.text()
        )
        self.download_worker.progress.connect(self.on_download_progress)
        self.download_worker.task_finished.connect(self.on_task_finished)
        self.download_worker.log.connect(self.log)
        self.download_worker.overall_progress.connect(self.on_overall_progress)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.start()

    def on_download_progress(self, task_id: str, progress: str, speed: str, status: str):
        """下载进度更新"""
        for i in range(self.tree_queue.topLevelItemCount()):
            item = self.tree_queue.topLevelItem(i)
            if item.text(0) == task_id:
                item.setText(2, status)
                item.setText(3, progress)
                item.setText(4, speed)

                if status == "下载中":
                    for col in range(5):
                        item.setForeground(col, QColor("#0078d4"))
                break

        if speed and speed not in ["初始化...", "处理中..."]:
            self.label_speed.setText(f"⚡ {speed}")

    def on_overall_progress(self, current: int, total: int):
        """总体进度更新"""
        self.progress_download.setValue(current)

    def on_task_finished(self, task_id: str, success: bool, message: str):
        """单个任务完成"""
        task = self.queue_data.get(task_id)
        if task:
            task['status'] = 'Done' if success else 'Error'

        for i in range(self.tree_queue.topLevelItemCount()):
            item = self.tree_queue.topLevelItem(i)
            if item.text(0) == task_id:
                item.setText(2, "完成" if success else "失败")
                item.setText(3, "100%" if success else "-")
                item.setText(4, message)

                color = QColor("#107c10") if success else QColor("#d13438")
                for col in range(5):
                    item.setForeground(col, color)
                break

        self.update_queue_stats()
        self.save_queue()

    def on_download_finished(self):
        """所有下载完成"""
        self.is_downloading = False
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_download.setVisible(False)
        self.label_speed.setText("")
        self.statusBar().showMessage("所有任务处理完毕")
        self.log("所有任务处理完毕", "SUCCESS")

        # 执行完成后动作
        action = self.combo_post_action.currentText()
        if action == "关闭程序":
            QTimer.singleShot(2000, self.close)
        elif action == "关机":
            if sys.platform == "win32":
                os.system("shutdown /s /t 60")
            else:
                os.system("shutdown -h +1")
        elif action == "休眠":
            if sys.platform == "win32":
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

    def stop_download(self):
        """停止下载"""
        if not self.is_downloading:
            return

        reply = QMessageBox.question(
            self, "确认", "确定要停止当前所有任务吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.download_worker:
                self.download_worker.stop()
            self.btn_stop.setEnabled(False)
            self.log("用户请求停止下载", "WARN")

    def remove_selected_tasks(self):
        """删除选中任务"""
        selected = self.tree_queue.selectedItems()
        if not selected:
            return

        reply = QMessageBox.question(
            self, "确认",
            f"确定要删除选中的 {len(selected)} 个任务吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        for item in selected:
            tid = item.text(0)
            if tid in self.queue_data:
                del self.queue_data[tid]
            if tid in self.queue_order:
                self.queue_order.remove(tid)

            index = self.tree_queue.indexOfTopLevelItem(item)
            self.tree_queue.takeTopLevelItem(index)

        self.update_queue_stats()
        self.save_queue()
        self.log(f"已删除 {len(selected)} 个任务", "INFO")

    def clear_done_tasks(self):
        """清空已完成任务"""
        to_remove = []
        for i in range(self.tree_queue.topLevelItemCount()):
            item = self.tree_queue.topLevelItem(i)
            tid = item.text(0)
            task = self.queue_data.get(tid)
            if task and task['status'] == 'Done':
                to_remove.append((i, tid))

        if not to_remove:
            QMessageBox.information(self, "提示", "没有已完成的任务")
            return

        for i, tid in reversed(to_remove):
            self.tree_queue.takeTopLevelItem(i)
            if tid in self.queue_data:
                del self.queue_data[tid]
            if tid in self.queue_order:
                self.queue_order.remove(tid)

        self.update_queue_stats()
        self.save_queue()
        self.log(f"已清空 {len(to_remove)} 个已完成任务", "INFO")

    def show_queue_context_menu(self, position):
        """显示队列右键菜单"""
        item = self.tree_queue.itemAt(position)
        if not item:
            return

        menu = QMenu()

        action_copy_title = QAction("复制标题", self)
        action_copy_title.triggered.connect(lambda: self.copy_queue_info("title"))
        menu.addAction(action_copy_title)

        action_copy_url = QAction("复制链接", self)
        action_copy_url.triggered.connect(lambda: self.copy_queue_info("url"))
        menu.addAction(action_copy_url)

        menu.addSeparator()

        action_requeue = QAction("重新排队", self)
        action_requeue.triggered.connect(self.requeue_selected)
        menu.addAction(action_requeue)

        menu.addSeparator()

        action_remove = QAction("删除", self)
        action_remove.triggered.connect(self.remove_selected_tasks)
        menu.addAction(action_remove)

        menu.addSeparator()

        action_open_dir = QAction("打开保存目录", self)
        action_open_dir.triggered.connect(self.open_save_dir)
        menu.addAction(action_open_dir)

        menu.exec_(self.tree_queue.viewport().mapToGlobal(position))

    def copy_queue_info(self, info_type: str):
        """复制队列信息"""
        selected = self.tree_queue.selectedItems()
        if not selected:
            return

        texts = []
        for item in selected:
            tid = item.text(0)
            task = self.queue_data.get(tid)
            if task:
                if info_type == "title":
                    texts.append(task['title'])
                elif info_type == "url":
                    texts.append(task['url'])

        if texts:
            QApplication.clipboard().setText('\n'.join(texts))
            self.statusBar().showMessage(f"已复制 {len(texts)} 项到剪贴板")

    def requeue_selected(self):
        """重新排队选中任务"""
        selected = self.tree_queue.selectedItems()
        count = 0

        for item in selected:
            tid = item.text(0)
            task = self.queue_data.get(tid)
            if task and task['status'] in ('Error', 'Stopped'):
                task['status'] = 'Pending'
                item.setText(2, "等待中")
                item.setText(3, "0%")
                item.setText(4, "重试")

                for col in range(5):
                    item.setForeground(col, QColor())
                count += 1

        if count:
            self.log(f"已重新排队 {count} 个任务", "INFO")
            self.update_queue_stats()
            self.save_queue()

    def update_queue_stats(self):
        """更新队列统计"""
        total = len(self.queue_data)
        pending = sum(1 for t in self.queue_data.values() if t['status'] == 'Pending')
        running = sum(1 for t in self.queue_data.values() if t['status'] == 'Running')
        done = sum(1 for t in self.queue_data.values() if t['status'] == 'Done')
        error = sum(1 for t in self.queue_data.values() if t['status'] in ('Error', 'Stopped'))

        self.label_stats.setText(
            f"总数: {total} | 等待: {pending} | 进行: {running} | 完成: {done} | 失败: {error}"
        )

    def update_format_ui(self):
        """更新格式UI状态"""
        is_video = self.radio_video.isChecked()
        self.combo_res.setEnabled(is_video)
        self.combo_vid_fmt.setEnabled(is_video)
        self.combo_aud_fmt.setEnabled(not is_video)
        self.combo_aud_br.setEnabled(not is_video)

        if self.sender() == self.radio_video and is_video:
            self.radio_audio.setChecked(False)
        elif self.sender() == self.radio_audio and self.radio_audio.isChecked():
            self.radio_video.setChecked(False)

    def browse_save_dir(self):
        """选择保存目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择保存目录",
            self.edit_save_dir.text()
        )
        if directory:
            self.edit_save_dir.setText(directory)
            self.log(f"保存目录已更改: {directory}", "INFO")

    def open_save_dir(self):
        """打开保存目录"""
        path = self.edit_save_dir.text()
        if not os.path.isdir(path):
            QMessageBox.warning(self, "提示", "保存目录不存在")
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def toggle_clipboard_monitor(self, state):
        """切换剪贴板监听"""
        if state == Qt.Checked:
            self.clipboard_timer = QTimer()
            self.clipboard_timer.timeout.connect(self.check_clipboard)
            self.clipboard_timer.start(1500)
            self.last_clipboard = ""
            self.log("剪贴板监听已启动", "INFO")
        else:
            if hasattr(self, 'clipboard_timer'):
                self.clipboard_timer.stop()
            self.log("剪贴板监听已停止", "INFO")

    def check_clipboard(self):
        """检查剪贴板"""
        try:
            text = QApplication.clipboard().text()
            if text != self.last_clipboard:
                self.last_clipboard = text
                # 简单检测视频链接
                if "http" in text and any(
                        site in text for site in [
                            "youtu", "bilibili", "twitch", "tiktok",
                            "twitter", "instagram", "facebook", "vimeo"
                        ]
                ):
                    self.url_input.setPlainText(text)
                    self.statusBar().showMessage("检测到视频链接，已自动填充")
                    self.log("剪贴板检测到视频链接", "INFO")
        except:
            pass

    def check_environment(self):
        """检查环境"""
        from shutil import which
        if not which("ffmpeg"):
            self.log("警告: 未检测到 FFmpeg，部分功能将受限", "WARN")
            self.statusBar().showMessage("警告: FFmpeg 未安装")

    def check_environment_detailed(self):
        """详细环境检查"""
        messages = []

        # yt-dlp
        try:
            ver = getattr(yt_dlp, '__version__', '未知')
            messages.append(f"✓ yt-dlp 版本: {ver}")
        except:
            messages.append("✗ yt-dlp 检测失败")

        # FFmpeg
        from shutil import which
        if which("ffmpeg"):
            messages.append("✓ FFmpeg: 已安装")
        else:
            messages.append("✗ FFmpeg: 未安装 (影响视频合并、转码、字幕嵌入)")

        # 保存目录
        path = Path(self.edit_save_dir.text())
        try:
            path.mkdir(parents=True, exist_ok=True)
            test_file = path / ".streamforge_test.tmp"
            test_file.write_text("ok")
            test_file.unlink()
            messages.append(f"✓ 保存目录可写: {path}")
        except Exception as e:
            messages.append(f"✗ 保存目录不可写: {e}")

        # Python版本
        messages.append(f"✓ Python 版本: {sys.version.split()[0]}")

        # PyQt5版本
        from PyQt5.QtCore import PYQT_VERSION_STR
        messages.append(f"✓ PyQt5 版本: {PYQT_VERSION_STR}")

        QMessageBox.information(self, "环境检查", "\n".join(messages))

    def self_test(self):
        """一键自测"""
        self.log("开始自测...", "INFO")

        def test():
            try:
                opts = {
                    'skip_download': True,
                    'quiet': True,
                    'no_warnings': True
                }
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(TEST_URL, download=False)
                    title = info.get('title', '未知')

                self.log(f"自测成功: {title}", "SUCCESS")
                QMessageBox.information(
                    self, "自测结果",
                    f"✓ 解析功能正常\n测试视频: {title}\n\n系统运行正常！"
                )
            except Exception as e:
                self.log(f"自测失败: {e}", "ERROR")
                QMessageBox.critical(self, "自测失败", f"解析功能异常:\n{e}")

        threading.Thread(target=test, daemon=True).start()

    def export_log(self):
        """导出日志"""
        path, _ = QFileDialog.getSaveFileName(
            self, "导出日志",
            str(Path.cwd() / f"streamforge_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"),
            "文本文件 (*.txt)"
        )
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.text_log.toPlainText())
                self.log(f"日志已导出: {path}", "SUCCESS")
                QMessageBox.information(self, "成功", f"日志已导出到:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败:\n{e}")

    def export_queue(self):
        """导出队列"""
        if not self.queue_data:
            QMessageBox.information(self, "提示", "当前没有任务可导出")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "导出任务队列",
            str(Path.cwd() / "streamforge_queue.json"),
            "JSON 文件 (*.json)"
        )
        if path:
            try:
                data = {
                    'version': APP_VERSION,
                    'export_time': datetime.now().isoformat(),
                    'order': self.queue_order,
                    'tasks': self.queue_data
                }
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.log(f"队列已导出: {path}", "SUCCESS")
                QMessageBox.information(self, "成功", f"队列已导出到:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败:\n{e}")

    def import_queue(self):
        """导入队列"""
        path, _ = QFileDialog.getOpenFileName(
            self, "导入任务队列",
            str(Path.cwd()),
            "JSON 文件 (*.json)"
        )
        if not path:
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            order = data.get('order', [])
            tasks = data.get('tasks', {})
            added = 0

            for tid in order:
                task = tasks.get(tid)
                if not task:
                    continue

                new_tid = str(uuid.uuid4())
                task['uuid'] = new_tid

                # 重置状态
                if task['status'] in ('Running', 'Error', 'Stopped'):
                    task['status'] = 'Pending'

                self.queue_data[new_tid] = task
                self.queue_order.append(new_tid)

                item = QTreeWidgetItem([
                    new_tid,
                    task['title'],
                    "等待中",
                    "0%",
                    "导入任务"
                ])
                self.tree_queue.addTopLevelItem(item)
                added += 1

            if added:
                self.log(f"已导入 {added} 个任务", "SUCCESS")
                self.update_queue_stats()
                self.save_queue()
                self.tabs.setCurrentIndex(1)
                QMessageBox.information(self, "成功", f"已导入 {added} 个任务")
            else:
                QMessageBox.information(self, "提示", "文件中没有有效任务")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败:\n{e}")

    def clear_cache(self):
        """清空缓存"""
        reply = QMessageBox.question(
            self, "确认",
            "确定要清空所有缓存数据吗？\n包括配置文件、历史队列和格式预设。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                CONFIG_FILE.unlink(missing_ok=True)
                QUEUE_FILE.unlink(missing_ok=True)
                PRESET_FILE.unlink(missing_ok=True)
                self.log("缓存已清空", "SUCCESS")
                QMessageBox.information(self, "成功", "缓存已清空，请重启程序")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清空失败:\n{e}")

    def show_about(self):
        """显示关于"""
        about_text = f"""
            <h2>{APP_NAME}</h2>
            <p><b>版本:</b> {APP_VERSION}</p>
            <p>多站点流媒体解析与批量下载工具</p>
            <p>基于 yt-dlp 与 FFmpeg | PyQt5 重构版</p>
            <br>
            <p><b>新增特性 (v10.0):</b></p>
            <ul>
            <li>✨ 拖放URL导入支持</li>
            <li>✨ 批量URL解析</li>
            <li>✨ 下载限速功能</li>
            <li>✨ 格式预设管理</li>
            <li>✨ 快捷键支持</li>
            <li>✨ 优化的界面布局</li>
            <li>✨ 更好的进度反馈</li>
            </ul>
            <br>
            <p><b>核心功能:</b></p>
            <ul>
            <li>支持 YouTube、Bilibili、Twitter 等数百个网站</li>
            <li>智能解析播放列表和频道</li>
            <li>多线程并发下载加速</li>
            <li>视频/音频格式自由转换</li>
            <li>字幕自动下载与内嵌</li>
            <li>Cookie 身份验证支持会员内容</li>
            <li>视频时间切片功能</li>
            <li>任务队列管理与持久化</li>
            </ul>
            <br>
            <p>© 2024 StreamForge Elite | PyQt5 Edition</p>
            """
        QMessageBox.about(self, "关于", about_text)

    def show_shortcuts(self):
        """显示快捷键"""
        shortcuts_text = """
            <h3>快捷键列表</h3>
            <table border="1" cellpadding="5">
            <tr><th>快捷键</th><th>功能</th></tr>
            <tr><td>Ctrl+Enter</td><td>开始下载</td></tr>
            <tr><td>Ctrl+Shift+A</td><td>解析URL</td></tr>
            <tr><td>Ctrl+L</td><td>清空输入</td></tr>
            <tr><td>Ctrl+V</td><td>粘贴到输入框</td></tr>
            <tr><td>Ctrl+O</td><td>打开保存目录</td></tr>
            <tr><td>Ctrl+E</td><td>导出队列</td></tr>
            <tr><td>Ctrl+I</td><td>导入队列</td></tr>
            <tr><td>Ctrl+Q</td><td>退出程序</td></tr>
            <tr><td>Delete</td><td>删除选中任务</td></tr>
            <tr><td>F1</td><td>显示快捷键</td></tr>
            </table>
            """
        QMessageBox.information(self, "快捷键", shortcuts_text)

    # ========================================================================
    #                              格式预设管理
    # ========================================================================

    def load_presets(self) -> Dict:
        """加载格式预设"""
        if not PRESET_FILE.exists():
            return {
                "默认配置": {
                    "mode": "video",
                    "res": "1080p",
                    "vid_fmt": "mp4",
                    "aud_fmt": "mp3",
                    "aud_br": "320"
                },
                "高清视频": {
                    "mode": "video",
                    "res": "4K",
                    "vid_fmt": "mp4",
                    "aud_fmt": "mp3",
                    "aud_br": "320"
                },
                "高音质音频": {
                    "mode": "audio",
                    "res": "1080p",
                    "vid_fmt": "mp4",
                    "aud_fmt": "flac",
                    "aud_br": "320"
                }
            }

        try:
            with open(PRESET_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def save_presets(self):
        """保存格式预设"""
        try:
            with open(PRESET_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.format_presets, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"保存预设失败: {e}", "ERROR")

    def update_preset_combo(self):
        """更新预设下拉框"""
        current = self.combo_preset.currentText() if hasattr(self, 'combo_preset') else ""
        self.combo_preset.clear()
        self.combo_preset.addItem("-- 选择预设 --")
        self.combo_preset.addItems(list(self.format_presets.keys()))

        if current and current in self.format_presets:
            self.combo_preset.setCurrentText(current)

    def apply_preset(self, preset_name: str):
        """应用预设"""
        if preset_name == "-- 选择预设 --":
            return

        preset = self.format_presets.get(preset_name)
        if not preset:
            return

        if preset['mode'] == 'video':
            self.radio_video.setChecked(True)
            self.combo_res.setCurrentText(preset['res'])
            self.combo_vid_fmt.setCurrentText(preset['vid_fmt'])
        else:
            self.radio_audio.setChecked(True)
            self.combo_aud_fmt.setCurrentText(preset['aud_fmt'])
            self.combo_aud_br.setCurrentText(preset['aud_br'])

        self.log(f"已应用预设: {preset_name}", "INFO")
        self.statusBar().showMessage(f"已应用预设: {preset_name}")

    def save_current_preset(self):
        """保存当前设置为预设"""
        from PyQt5.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "保存预设", "输入预设名称:")
        if not ok or not name:
            return

        preset = {
            "mode": "video" if self.radio_video.isChecked() else "audio",
            "res": self.combo_res.currentText(),
            "vid_fmt": self.combo_vid_fmt.currentText(),
            "aud_fmt": self.combo_aud_fmt.currentText(),
            "aud_br": self.combo_aud_br.currentText()
        }

        self.format_presets[name] = preset
        self.save_presets()
        self.update_preset_combo()
        self.combo_preset.setCurrentText(name)

        self.log(f"已保存预设: {name}", "SUCCESS")
        QMessageBox.information(self, "成功", f"预设 '{name}' 已保存")

    def manage_presets(self):
        """管理预设"""
        from PyQt5.QtWidgets import QListWidget, QDialog, QVBoxLayout, QHBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("管理格式预设")
        dialog.setMinimumSize(400, 300)

        layout = QVBoxLayout(dialog)

        list_widget = QListWidget()
        list_widget.addItems(list(self.format_presets.keys()))
        layout.addWidget(list_widget)

        buttons = QHBoxLayout()

        btn_delete = QPushButton("删除选中")
        btn_delete.clicked.connect(lambda: self.delete_preset(list_widget))
        buttons.addWidget(btn_delete)

        buttons.addStretch()

        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(dialog.accept)
        buttons.addWidget(btn_close)

        layout.addLayout(buttons)

        dialog.exec_()

    def delete_preset(self, list_widget):
        """删除预设"""
        current = list_widget.currentItem()
        if not current:
            return

        name = current.text()

        reply = QMessageBox.question(
            self, "确认",
            f"确定要删除预设 '{name}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if name in self.format_presets:
                del self.format_presets[name]
                self.save_presets()
                self.update_preset_combo()
                list_widget.takeItem(list_widget.row(current))
                self.log(f"已删除预设: {name}", "INFO")

    # ========================================================================
    #                              配置保存/加载
    # ========================================================================

    def save_config(self):
        """保存配置"""
        try:
            config = {
                'save_dir': self.edit_save_dir.text(),
                'proxy': self.edit_proxy.text(),
                'cookie_browser': self.combo_cookie.currentText(),
                'threads': self.spin_threads.value(),
                'rate_limit': self.spin_rate_limit.value(),
                'clean_name': self.chk_clean_name.isChecked(),
                'embed_sub': self.chk_embed_sub.isChecked(),
                'embed_thumb': self.chk_embed_thumb.isChecked(),
                'write_desc': self.chk_write_desc.isChecked(),
                'sub_lang': self.combo_sub_lang.currentText(),
                'mode': 'video' if self.radio_video.isChecked() else 'audio',
                'res': self.combo_res.currentText(),
                'vid_fmt': self.combo_vid_fmt.currentText(),
                'aud_fmt': self.combo_aud_fmt.currentText(),
                'aud_br': self.combo_aud_br.currentText(),
                'post_action': self.combo_post_action.currentText(),
                'auto_add': self.chk_auto_add.isChecked()
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"保存配置失败: {e}", "ERROR")

    def load_config(self):
        """加载配置"""
        if not CONFIG_FILE.exists():
            return

        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)

            self.edit_save_dir.setText(config.get('save_dir', str(Path.home() / "Downloads")))
            self.edit_proxy.setText(config.get('proxy', ''))

            # Cookie 浏览器
            cookie_val = config.get('cookie_browser', 'None')
            for i in range(self.combo_cookie.count()):
                if cookie_val in self.combo_cookie.itemText(i):
                    self.combo_cookie.setCurrentIndex(i)
                    break

            self.spin_threads.setValue(config.get('threads', 8))
            self.spin_rate_limit.setValue(config.get('rate_limit', 0))
            self.chk_clean_name.setChecked(config.get('clean_name', True))
            self.chk_embed_sub.setChecked(config.get('embed_sub', True))
            self.chk_embed_thumb.setChecked(config.get('embed_thumb', True))
            self.chk_write_desc.setChecked(config.get('write_desc', False))
            self.chk_auto_add.setChecked(config.get('auto_add', False))

            # 字幕语言
            sub_lang_val = config.get('sub_lang', 'all')
            for i in range(self.combo_sub_lang.count()):
                if sub_lang_val in self.combo_sub_lang.itemText(i):
                    self.combo_sub_lang.setCurrentIndex(i)
                    break

            if config.get('mode') == 'video':
                self.radio_video.setChecked(True)
            else:
                self.radio_audio.setChecked(True)

            self.combo_res.setCurrentText(config.get('res', '1080p'))
            self.combo_vid_fmt.setCurrentText(config.get('vid_fmt', 'mp4'))
            self.combo_aud_fmt.setCurrentText(config.get('aud_fmt', 'mp3'))
            self.combo_aud_br.setCurrentText(config.get('aud_br', '320'))
            self.combo_post_action.setCurrentText(config.get('post_action', '无操作'))

            self.log("配置已加载", "INFO")
        except Exception as e:
            self.log(f"加载配置失败: {e}", "ERROR")

    def save_queue(self):
        """保存队列"""
        try:
            data = {
                'order': self.queue_order,
                'tasks': self.queue_data,
                'saved_at': datetime.now().isoformat()
            }
            with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"保存队列失败: {e}", "ERROR")

    def load_queue(self):
        """加载队列"""
        if not QUEUE_FILE.exists():
            return

        try:
            with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            order = data.get('order', [])
            tasks = data.get('tasks', {})
            restored = 0

            for tid in order:
                task = tasks.get(tid)
                if not task:
                    continue

                # 将Running状态重置为Pending
                if task['status'] == 'Running':
                    task['status'] = 'Pending'

                self.queue_data[tid] = task
                self.queue_order.append(tid)

                status = task['status']
                status_text = {
                    'Pending': '等待中',
                    'Done': '完成',
                    'Error': '失败',
                    'Stopped': '已停止'
                }.get(status, status)

                prog = "100%" if status == 'Done' else "0%"
                info = "历史任务"

                item = QTreeWidgetItem([
                    tid,
                    task['title'],
                    status_text,
                    prog,
                    info
                ])

                # 设置颜色
                if status == 'Done':
                    for col in range(5):
                        item.setForeground(col, QColor("#107c10"))
                elif status in ('Error', 'Stopped'):
                    for col in range(5):
                        item.setForeground(col, QColor("#d13438"))

                self.tree_queue.addTopLevelItem(item)
                restored += 1

            if restored:
                self.log(f"已恢复 {restored} 个历史任务", "INFO")
                self.update_queue_stats()

        except Exception as e:
            self.log(f"加载队列失败: {e}", "ERROR")

    def closeEvent(self, event):
        """关闭事件"""
        if self.is_downloading:
            reply = QMessageBox.question(
                self, "确认退出",
                "下载正在进行中，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return

            if self.download_worker:
                self.download_worker.stop()
                self.download_worker.wait(3000)

        if self.is_analyzing:
            if self.analyzer_worker:
                self.analyzer_worker.stop()
                self.analyzer_worker.wait(2000)

        self.save_config()
        self.save_queue()
        event.accept()


# ============================================================================
#                                  主程序入口
# ============================================================================

def main():
    # 高DPI支持
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyle('Fusion')

    window = StreamForgeElite()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()