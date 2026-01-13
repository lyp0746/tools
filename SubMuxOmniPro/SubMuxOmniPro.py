#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SubMuxOmniPro - 视音频全能工具箱
功能：字幕处理、音视频混流、格式转换
作者：LYP
GitHub：https://github.com/lyp0746
邮箱：1610369302@qq.com
版本：3.0.0
6. 增加预览功能和参数预设
7. 支持拖拽文件
8. 增加深色/浅色主题切换
9. 优化界面布局和交互体验
10. 修复潜在 bug 和线程安全问题
"""

import os
import sys
import queue
import threading
import subprocess
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox,
    QSpinBox, QDoubleSpinBox, QSlider, QTextEdit, QFileDialog,
    QMessageBox, QGroupBox, QRadioButton, QButtonGroup, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QFrame,
    QListWidget, QListWidgetItem, QMenu, QAction, QToolButton, QDialog,
    QDialogButtonBox, QGridLayout, QScrollArea, QStatusBar
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize, QSettings, QUrl
)
from PyQt5.QtGui import (
    QIcon, QFont, QColor, QPalette, QDragEnterEvent, QDropEvent, QPixmap
)

APP_NAME = "SubMux Omni Pro"
APP_VERSION = "v3.0"
SETTINGS_FILE = "submux_settings.json"


# ==========================================
# FFmpeg 工作线程
# ==========================================

class FFmpegWorker(QThread):
    """FFmpeg 后台执行线程，解析进度并发送信号"""

    progress_signal = pyqtSignal(int)  # 进度百分比 0-100
    log_signal = pyqtSignal(str)  # 日志消息
    finished_signal = pyqtSignal(bool, str)  # 完成信号 (成功?, 消息)

    def __init__(self, cmd: List[str], task_name: str):
        super().__init__()
        self.cmd = cmd
        self.task_name = task_name
        self.is_cancelled = False
        self.process: Optional[subprocess.Popen] = None

    def run(self):
        """执行 FFmpeg 命令"""
        try:
            self.log_signal.emit(f"=== 开始任务: {self.task_name} ===")
            self.log_signal.emit(f"命令: {' '.join(self.cmd)}\n")

            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self.process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                startupinfo=startupinfo,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )

            duration = None
            for line in self.process.stdout:
                if self.is_cancelled:
                    self.process.terminate()
                    self.finished_signal.emit(False, "任务已取消")
                    return

                # 解析总时长
                if duration is None:
                    dur_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})', line)
                    if dur_match:
                        h, m, s = dur_match.groups()
                        duration = int(h) * 3600 + int(m) * 60 + float(s)

                # 解析当前进度
                time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2}\.\d{2})', line)
                if time_match and duration and duration > 0:
                    h, m, s = time_match.groups()
                    current = int(h) * 3600 + int(m) * 60 + float(s)
                    progress = min(int((current / duration) * 100), 100)
                    self.progress_signal.emit(progress)

                # 输出关键日志
                if 'error' in line.lower() or 'warning' in line.lower():
                    self.log_signal.emit(line.strip())

            self.process.wait()

            if self.process.returncode == 0:
                self.progress_signal.emit(100)
                self.log_signal.emit("✓ 任务成功完成\n")
                self.finished_signal.emit(True, "成功")
            else:
                self.log_signal.emit(f"✗ 任务失败 (退出码: {self.process.returncode})\n")
                self.finished_signal.emit(False, f"失败 (代码 {self.process.returncode})")

        except Exception as e:
            self.log_signal.emit(f"✗ 执行异常: {str(e)}\n")
            self.finished_signal.emit(False, f"异常: {str(e)}")

    def cancel(self):
        """取消任务"""
        self.is_cancelled = True
        if self.process:
            try:
                self.process.terminate()
            except:
                pass


# ==========================================
# 任务队列管理器
# ==========================================

class TaskQueue:
    """任务队列管理"""

    def __init__(self):
        self.tasks: List[Dict] = []
        self.current_task: Optional[Dict] = None
        self.history: List[Dict] = []

    def add_task(self, task: Dict):
        """添加任务到队列"""
        task['id'] = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        task['status'] = '等待中'
        task['progress'] = 0
        task['add_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.tasks.append(task)

    def get_next_task(self) -> Optional[Dict]:
        """获取下一个任务"""
        if self.tasks:
            self.current_task = self.tasks.pop(0)
            self.current_task['status'] = '执行中'
            self.current_task['start_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return self.current_task
        return None

    def finish_current_task(self, success: bool, message: str):
        """完成当前任务"""
        if self.current_task:
            self.current_task['status'] = '成功' if success else '失败'
            self.current_task['message'] = message
            self.current_task['end_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.history.insert(0, self.current_task)
            self.current_task = None

            # 保持历史记录最多 100 条
            if len(self.history) > 100:
                self.history = self.history[:100]

    def clear_queue(self):
        """清空队列"""
        self.tasks.clear()

    def remove_task(self, task_id: str):
        """移除指定任务"""
        self.tasks = [t for t in self.tasks if t['id'] != task_id]


# ==========================================
# 主窗口
# ==========================================

class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()

        self.task_queue = TaskQueue()
        self.current_worker: Optional[FFmpegWorker] = None
        self.settings = self.load_settings()

        # 窗口设置
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.setMinimumSize(1200, 850)
        self.resize(1400, 900)

        # 启用拖拽
        self.setAcceptDrops(True)

        # 初始化 UI
        self.init_ui()
        self.apply_theme(self.settings.get('theme', 'dark'))

        # 检查 FFmpeg
        QTimer.singleShot(500, self.check_ffmpeg)

    def init_ui(self):
        """初始化界面"""
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 顶部工具栏
        self.create_toolbar(main_layout)

        # 主内容区（分割器）
        splitter = QSplitter(Qt.Vertical)

        # 选项卡
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(True)

        # Tab 1: 工具箱
        self.tab_tools = QWidget()
        self.init_tools_tab()
        self.tabs.addTab(self.tab_tools, "🛠️ 全能工具箱")

        # Tab 2: 任务队列
        self.tab_queue = QWidget()
        self.init_queue_tab()
        self.tabs.addTab(self.tab_queue, "📋 任务队列")

        # Tab 3: 历史记录
        self.tab_history = QWidget()
        self.init_history_tab()
        self.tabs.addTab(self.tab_history, "📜 历史记录")

        # Tab 4: 设置
        self.tab_settings = QWidget()
        self.init_settings_tab()
        self.tabs.addTab(self.tab_settings, "⚙️ 设置")

        splitter.addWidget(self.tabs)

        # 底部日志区
        log_widget = self.create_log_area()
        splitter.addWidget(log_widget)

        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        # 进度条（在状态栏中）
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(300)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

    def create_toolbar(self, parent_layout):
        """创建顶部工具栏"""
        toolbar = QFrame()
        toolbar.setFrameShape(QFrame.StyledPanel)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)

        # Logo 和标题
        title = QLabel(f"<h2>{APP_NAME}</h2>")
        toolbar_layout.addWidget(title)

        toolbar_layout.addStretch()

        # 快捷按钮
        btn_check_ffmpeg = QPushButton("🔍 检测 FFmpeg")
        btn_check_ffmpeg.clicked.connect(self.check_ffmpeg)
        toolbar_layout.addWidget(btn_check_ffmpeg)

        btn_clear_log = QPushButton("🗑️ 清空日志")
        btn_clear_log.clicked.connect(self.clear_log)
        toolbar_layout.addWidget(btn_clear_log)

        # 主题切换
        btn_theme = QPushButton("🎨 切换主题")
        btn_theme.clicked.connect(self.toggle_theme)
        toolbar_layout.addWidget(btn_theme)

        btn_about = QPushButton("❓ 关于")
        btn_about.clicked.connect(self.show_about)
        toolbar_layout.addWidget(btn_about)

        parent_layout.addWidget(toolbar)

    def create_log_area(self) -> QWidget:
        """创建日志区域"""
        log_group = QGroupBox("📝 系统日志")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)

        return log_group

    # ==========================================
    # Tab 1: 工具箱
    # ==========================================

    def init_tools_tab(self):
        """初始化工具箱选项卡"""
        layout = QVBoxLayout(self.tab_tools)
        layout.setSpacing(15)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(15)

        # 1. 功能选择
        self.create_task_selector(scroll_layout)

        # 2. 参数设置（动态）
        self.param_group = QGroupBox("2️⃣ 参数设置")
        self.param_layout = QVBoxLayout(self.param_group)
        scroll_layout.addWidget(self.param_group)

        # 3. 文件选择
        self.create_file_selector(scroll_layout)

        # 4. 执行按钮
        self.create_action_buttons(scroll_layout)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # 初始化任务参数
        self.init_task_params()
        self.on_task_changed()

    def create_task_selector(self, parent_layout):
        """创建任务选择器"""
        group = QGroupBox("1️⃣ 功能选择")
        layout = QVBoxLayout(group)

        # 任务定义
        self.TASKS = {
            "merge_soft": ["📄 软字幕封装 (MKV无损)", True, None],
            "merge_hard": ["🔥 硬字幕烧录 (MP4重编码)", True, None],
            "av_merge": ["🎬 音画合并 (视频+音频)", True, "layout_av_merge"],
            "concat": ["🔗 视频拼接 (多合一)", False, None],
            "convert": ["🔄 格式转换 (MP4/MKV/AVI)", False, "layout_convert"],
            "trim": ["✂️ 精确剪辑 (时间范围)", False, "layout_trim"],
            "compress": ["📉 视频压缩 (H.264/H.265)", False, "layout_compress"],
            "resize": ["📏 修改分辨率", False, "layout_resize"],
            "crop": ["🖼️ 画面裁剪 (去黑边)", False, "layout_crop"],
            "watermark": ["📝 添加文字水印", False, "layout_watermark"],
            "color": ["🎨 色彩/亮度调节", False, "layout_color"],
            "rotate": ["🔄 旋转与翻转", False, "layout_rotate"],
            "replace_audio": ["🎵 替换背景音乐", True, None],
            "volume": ["🔊 调整音量", False, "layout_volume"],
            "snapshot": ["📷 提取截图 (JPG/PNG)", False, "layout_snapshot"],
            "extract_audio": ["🎵 提取音频 (MP3/AAC)", False, "layout_extract_audio"],
            "extract_sub": ["📄 提取字幕 (SRT/ASS)", False, None],
            "clean_meta": ["🛡️ 清除元数据 (隐私保护)", False, None],
            "speed": ["⚡ 变速播放 (0.25x-4x)", False, "layout_speed"],
            "gif": ["🎞️ 导出 GIF 动图", False, "layout_gif"],
            "reverse": ["⏪ 视频倒放", False, None],
            "denoise": ["🔇 视频降噪", False, "layout_denoise"],
            "stabilize": ["📹 视频防抖", False, "layout_stabilize"],
        }

        self.task_combo = QComboBox()
        for key, info in self.TASKS.items():
            self.task_combo.addItem(info[0], key)
        self.task_combo.currentIndexChanged.connect(self.on_task_changed)

        layout.addWidget(self.task_combo)

        # 任务描述
        self.task_desc_label = QLabel()
        self.task_desc_label.setWordWrap(True)
        self.task_desc_label.setStyleSheet("QLabel { color: #888; font-size: 10px; padding: 5px; }")
        layout.addWidget(self.task_desc_label)

        parent_layout.addWidget(group)

    def create_file_selector(self, parent_layout):
        """创建文件选择器"""
        group = QGroupBox("3️⃣ 文件来源")
        layout = QVBoxLayout(group)

        # 模式选择
        mode_layout = QHBoxLayout()
        self.mode_group = QButtonGroup()

        self.radio_single = QRadioButton("单文件处理")
        self.radio_single.setChecked(True)
        self.radio_single.toggled.connect(self.on_mode_changed)
        self.mode_group.addButton(self.radio_single)
        mode_layout.addWidget(self.radio_single)

        self.radio_batch = QRadioButton("批量处理/拼接")
        self.radio_batch.toggled.connect(self.on_mode_changed)
        self.mode_group.addButton(self.radio_batch)
        mode_layout.addWidget(self.radio_batch)

        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        # 单文件模式
        self.single_widget = QWidget()
        single_layout = QGridLayout(self.single_widget)
        single_layout.setContentsMargins(0, 0, 0, 0)

        single_layout.addWidget(QLabel("视频文件:"), 0, 0)
        self.video_path = QLineEdit()
        self.video_path.setPlaceholderText("点击浏览或拖拽文件到此处...")
        self.video_path.setAcceptDrops(True)
        self.video_path.dragEnterEvent = self.drag_enter_event
        self.video_path.dropEvent = lambda e: self.drop_event(e, self.video_path)
        single_layout.addWidget(self.video_path, 0, 1)

        btn_browse_video = QPushButton("📂 浏览...")
        btn_browse_video.clicked.connect(lambda: self.browse_file(self.video_path))
        single_layout.addWidget(btn_browse_video, 0, 2)

        layout.addWidget(self.single_widget)

        # 批量模式
        self.batch_widget = QWidget()
        batch_layout = QGridLayout(self.batch_widget)
        batch_layout.setContentsMargins(0, 0, 0, 0)

        batch_layout.addWidget(QLabel("文件夹:"), 0, 0)
        self.dir_path = QLineEdit()
        self.dir_path.setPlaceholderText("选择包含视频文件的文件夹...")
        batch_layout.addWidget(self.dir_path, 0, 1)

        btn_browse_dir = QPushButton("📂 选择...")
        btn_browse_dir.clicked.connect(lambda: self.browse_directory(self.dir_path))
        batch_layout.addWidget(btn_browse_dir, 0, 2)

        batch_layout.addWidget(QLabel("文件格式:"), 1, 0)
        self.ext_filter = QLineEdit("mp4, mkv, mov, avi")
        self.ext_filter.setPlaceholderText("例如: mp4, mkv, mov")
        batch_layout.addWidget(self.ext_filter, 1, 1, 1, 2)

        self.batch_widget.setVisible(False)
        layout.addWidget(self.batch_widget)

        # 辅助文件（字幕/音频）
        self.extra_widget = QWidget()
        extra_layout = QGridLayout(self.extra_widget)
        extra_layout.setContentsMargins(0, 0, 0, 0)

        self.extra_label = QLabel("字幕文件:")
        extra_layout.addWidget(self.extra_label, 0, 0)

        self.extra_path = QLineEdit()
        self.extra_path.setPlaceholderText("选择字幕或音频文件...")
        self.extra_path.setAcceptDrops(True)
        self.extra_path.dragEnterEvent = self.drag_enter_event
        self.extra_path.dropEvent = lambda e: self.drop_event(e, self.extra_path)
        extra_layout.addWidget(self.extra_path, 0, 1)

        btn_browse_extra = QPushButton("📂 浏览...")
        btn_browse_extra.clicked.connect(lambda: self.browse_file(self.extra_path))
        extra_layout.addWidget(btn_browse_extra, 0, 2)

        btn_auto_match = QPushButton("🔍 智能匹配")
        btn_auto_match.setToolTip("自动查找同名的字幕或音频文件")
        btn_auto_match.clicked.connect(self.auto_match_extra)
        extra_layout.addWidget(btn_auto_match, 0, 3)

        self.extra_widget.setVisible(False)
        layout.addWidget(self.extra_widget)

        parent_layout.addWidget(group)

    def create_action_buttons(self, parent_layout):
        """创建操作按钮"""
        btn_layout = QHBoxLayout()

        self.btn_add_queue = QPushButton("➕ 添加到队列")
        self.btn_add_queue.setMinimumHeight(40)
        self.btn_add_queue.clicked.connect(self.add_to_queue)
        btn_layout.addWidget(self.btn_add_queue)

        self.btn_execute = QPushButton("🚀 立即执行")
        self.btn_execute.setMinimumHeight(40)
        self.btn_execute.clicked.connect(self.execute_immediately)
        btn_layout.addWidget(self.btn_execute)

        self.btn_stop = QPushButton("⏹️ 停止")
        self.btn_stop.setMinimumHeight(40)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_current_task)
        btn_layout.addWidget(self.btn_stop)

        parent_layout.addLayout(btn_layout)

    def init_task_params(self):
        """初始化任务参数变量"""
        self.params = {
            'crf': 23,
            'preset': 'medium',
            'codec': 'libx264',
            'output_format': 'mp4',
            'width': 1920,
            'height': 1080,
            'keep_aspect': True,
            'crop_w': 1920,
            'crop_h': 800,
            'crop_x': 0,
            'crop_y': 140,
            'start_time': '00:00:00',
            'end_time': '00:01:00',
            'watermark_text': '水印文本',
            'watermark_pos': 'bottom_right',
            'watermark_font_size': 24,
            'brightness': 0.0,
            'contrast': 1.0,
            'saturation': 1.0,
            'rotate': 'clock_90',
            'volume': '0dB',
            'speed': 1.0,
            'gif_fps': 10,
            'gif_width': 480,
            'snapshot_format': 'jpg',
            'audio_format': 'mp3',
            'audio_bitrate': '192k',
            'av_reencode': False,
            'denoise_strength': 'medium',
            'stabilize_shakiness': 5,
        }

    def on_task_changed(self):
        """任务类型改变时更新界面"""
        # 清空参数区域
        while self.param_layout.count():
            item = self.param_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        task_key = self.task_combo.currentData()
        task_info = self.TASKS.get(task_key)

        if not task_info:
            return

        # 更新任务描述
        descriptions = {
            "merge_soft": "将外部字幕文件封装到视频容器中（推荐 MKV 格式），不重新编码视频，速度极快。",
            "merge_hard": "将字幕永久烧录到视频画面中（适合不支持外挂字幕的播放器），需要重新编码。",
            "av_merge": "将独立的视频流和音频流合并为单个文件（如 YouTube 下载的分离文件）。",
            "concat": "将多个视频文件按顺序拼接成一个完整视频（要求格式、分辨率一致）。",
            "convert": "转换视频容器格式或编码格式，支持 MP4、MKV、AVI 等主流格式。",
            "trim": "精确剪辑视频片段，支持指定起止时间点。",
            "compress": "使用 H.264/H.265 编码压缩视频体积，可调节画质参数。",
            "resize": "修改视频分辨率，可等比缩放或自定义宽高。",
            "crop": "裁剪视频画面，去除黑边或提取特定区域。",
            "watermark": "在视频上添加文字水印，可自定义位置、字体、颜色。",
            "color": "调整视频的亮度、对比度、饱和度等色彩参数。",
            "rotate": "旋转视频画面（90度/180度/270度）或翻转（水平/垂直）。",
            "replace_audio": "替换视频的背景音乐或音轨，保留原始画面。",
            "volume": "调整视频的音量大小（增大或减小 dB）。",
            "snapshot": "从视频中提取指定时间点的截图，支持 JPG/PNG 格式。",
            "extract_audio": "从视频中提取音轨，支持导出为 MP3、AAC、WAV 等格式。",
            "extract_sub": "从视频容器中提取内嵌的字幕轨道（如有）。",
            "clean_meta": "清除视频文件的元数据信息（如 GPS 位置、拍摄设备等），保护隐私。",
            "speed": "改变视频播放速度（0.25x 慢放 ~ 4x 快进），音频同步变速。",
            "gif": "将视频转换为 GIF 动图，可调节帧率和尺寸。",
            "reverse": "倒放视频（时间倒序播放），适合创意视频制作。",
            "denoise": "去除视频噪点，改善画面质量（适合低光环境拍摄的视频）。",
            "stabilize": "视频防抖处理，修正手持拍摄的抖动（需两次处理）。",
        }
        self.task_desc_label.setText(descriptions.get(task_key, ""))

        # 是否需要辅助文件
        needs_extra = task_info[1]
        self.extra_widget.setVisible(needs_extra)

        if needs_extra:
            if task_key in ('av_merge', 'replace_audio'):
                self.extra_label.setText("音频文件:")
                self.extra_path.setPlaceholderText("选择音频文件 (MP3/AAC/WAV/M4A)...")
            else:
                self.extra_label.setText("字幕文件:")
                self.extra_path.setPlaceholderText("选择字幕文件 (SRT/ASS/SSA)...")

        # 动态加载参数界面
        layout_method = task_info[2]
        if layout_method and hasattr(self, layout_method):
            getattr(self, layout_method)()
        else:
            # 默认提示
            label = QLabel("此功能无需额外参数设置")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: #666; padding: 20px;")
            self.param_layout.addWidget(label)

    def on_mode_changed(self):
        """文件模式改变"""
        is_single = self.radio_single.isChecked()
        self.single_widget.setVisible(is_single)
        self.batch_widget.setVisible(not is_single)

    # ==========================================
    # 参数布局方法
    # ==========================================

    def layout_convert(self):
        """格式转换参数"""
        form = QGridLayout()

        form.addWidget(QLabel("输出格式:"), 0, 0)
        format_combo = QComboBox()
        format_combo.addItems(['mp4', 'mkv', 'avi', 'mov', 'flv', 'webm'])
        format_combo.setCurrentText(self.params['output_format'])
        format_combo.currentTextChanged.connect(lambda v: self.params.update({'output_format': v}))
        form.addWidget(format_combo, 0, 1)

        form.addWidget(QLabel("视频编码:"), 1, 0)
        codec_combo = QComboBox()
        codec_combo.addItems(['libx264 (H.264)', 'libx265 (H.265)', 'copy (不重编码)'])
        codec_combo.currentTextChanged.connect(
            lambda v: self.params.update({'codec': v.split()[0]})
        )
        form.addWidget(codec_combo, 1, 1)

        self.param_layout.addLayout(form)

    def layout_compress(self):
        """压缩参数"""
        form = QGridLayout()

        form.addWidget(QLabel("编码器:"), 0, 0)
        codec_combo = QComboBox()
        codec_combo.addItems(['libx264 (H.264 - 兼容性好)', 'libx265 (H.265 - 压缩率高)'])
        codec_combo.currentTextChanged.connect(
            lambda v: self.params.update({'codec': v.split()[0]})
        )
        form.addWidget(codec_combo, 0, 1)

        form.addWidget(QLabel("CRF 画质 (越小越清晰):"), 1, 0)
        crf_slider = QSlider(Qt.Horizontal)
        crf_slider.setRange(18, 35)
        crf_slider.setValue(self.params['crf'])
        crf_label = QLabel(str(self.params['crf']))
        crf_slider.valueChanged.connect(lambda v: (self.params.update({'crf': v}), crf_label.setText(str(v))))

        crf_layout = QHBoxLayout()
        crf_layout.addWidget(crf_slider)
        crf_layout.addWidget(crf_label)
        form.addLayout(crf_layout, 1, 1)

        form.addWidget(QLabel("编码预设 (速度):"), 2, 0)
        preset_combo = QComboBox()
        preset_combo.addItems(
            ['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow'])
        preset_combo.setCurrentText(self.params['preset'])
        preset_combo.currentTextChanged.connect(lambda v: self.params.update({'preset': v}))
        form.addWidget(preset_combo, 2, 1)

        self.param_layout.addLayout(form)

        tip = QLabel("💡 提示: CRF 23 为推荐值，18 为近无损，28 为中等压缩，35 为高度压缩")
        tip.setStyleSheet("color: #888; font-size: 10px;")
        tip.setWordWrap(True)
        self.param_layout.addWidget(tip)

    def layout_trim(self):
        """剪辑参数"""
        form = QGridLayout()

        form.addWidget(QLabel("开始时间 (HH:MM:SS):"), 0, 0)
        start_edit = QLineEdit(self.params['start_time'])
        start_edit.setPlaceholderText("00:00:00")
        start_edit.textChanged.connect(lambda v: self.params.update({'start_time': v}))
        form.addWidget(start_edit, 0, 1)

        form.addWidget(QLabel("结束时间 (HH:MM:SS):"), 1, 0)
        end_edit = QLineEdit(self.params['end_time'])
        end_edit.setPlaceholderText("00:01:00")
        end_edit.textChanged.connect(lambda v: self.params.update({'end_time': v}))
        form.addWidget(end_edit, 1, 1)

        self.param_layout.addLayout(form)

        tip = QLabel("💡 支持格式: HH:MM:SS 或秒数 (如 90 表示 1 分 30 秒)")
        tip.setStyleSheet("color: #888; font-size: 10px;")
        self.param_layout.addWidget(tip)

    def layout_resize(self):
        """分辨率调整参数"""
        form = QGridLayout()

        form.addWidget(QLabel("宽度:"), 0, 0)
        width_spin = QSpinBox()
        width_spin.setRange(128, 7680)
        width_spin.setSingleStep(2)
        width_spin.setValue(self.params['width'])
        width_spin.valueChanged.connect(lambda v: self.params.update({'width': v}))
        form.addWidget(width_spin, 0, 1)

        form.addWidget(QLabel("高度:"), 1, 0)
        height_spin = QSpinBox()
        height_spin.setRange(128, 4320)
        height_spin.setSingleStep(2)
        height_spin.setValue(self.params['height'])
        height_spin.valueChanged.connect(lambda v: self.params.update({'height': v}))
        form.addWidget(height_spin, 1, 1)

        keep_aspect = QCheckBox("保持宽高比")
        keep_aspect.setChecked(self.params['keep_aspect'])
        keep_aspect.stateChanged.connect(lambda s: self.params.update({'keep_aspect': bool(s)}))
        form.addWidget(keep_aspect, 2, 0, 1, 2)

        self.param_layout.addLayout(form)

        # 预设按钮
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("快捷预设:"))
        for name, w, h in [('720p', 1280, 720), ('1080p', 1920, 1080), ('2K', 2560, 1440), ('4K', 3840, 2160)]:
            btn = QPushButton(name)
            btn.clicked.connect(lambda _, w=w, h=h: (width_spin.setValue(w), height_spin.setValue(h)))
            preset_layout.addWidget(btn)
        preset_layout.addStretch()
        self.param_layout.addLayout(preset_layout)

    def layout_crop(self):
        """裁剪参数"""
        form = QGridLayout()

        form.addWidget(QLabel("输出宽度:"), 0, 0)
        crop_w_spin = QSpinBox()
        crop_w_spin.setRange(1, 7680)
        crop_w_spin.setValue(self.params['crop_w'])
        crop_w_spin.valueChanged.connect(lambda v: self.params.update({'crop_w': v}))
        form.addWidget(crop_w_spin, 0, 1)

        form.addWidget(QLabel("输出高度:"), 0, 2)
        crop_h_spin = QSpinBox()
        crop_h_spin.setRange(1, 4320)
        crop_h_spin.setValue(self.params['crop_h'])
        crop_h_spin.valueChanged.connect(lambda v: self.params.update({'crop_h': v}))
        form.addWidget(crop_h_spin, 0, 3)

        form.addWidget(QLabel("起始 X:"), 1, 0)
        crop_x_spin = QSpinBox()
        crop_x_spin.setRange(0, 7680)
        crop_x_spin.setValue(self.params['crop_x'])
        crop_x_spin.valueChanged.connect(lambda v: self.params.update({'crop_x': v}))
        form.addWidget(crop_x_spin, 1, 1)

        form.addWidget(QLabel("起始 Y:"), 1, 2)
        crop_y_spin = QSpinBox()
        crop_y_spin.setRange(0, 4320)
        crop_y_spin.setValue(self.params['crop_y'])
        crop_y_spin.valueChanged.connect(lambda v: self.params.update({'crop_y': v}))
        form.addWidget(crop_y_spin, 1, 3)

        self.param_layout.addLayout(form)

        tip = QLabel("💡 裁剪公式: crop=宽:高:X:Y  (从坐标 X,Y 开始裁剪指定宽高的区域)")
        tip.setStyleSheet("color: #888; font-size: 10px;")
        tip.setWordWrap(True)
        self.param_layout.addWidget(tip)

    def layout_watermark(self):
        """水印参数"""
        form = QGridLayout()

        form.addWidget(QLabel("水印文字:"), 0, 0)
        text_edit = QLineEdit(self.params['watermark_text'])
        text_edit.textChanged.connect(lambda v: self.params.update({'watermark_text': v}))
        form.addWidget(text_edit, 0, 1, 1, 3)

        form.addWidget(QLabel("字体大小:"), 1, 0)
        font_size_spin = QSpinBox()
        font_size_spin.setRange(8, 200)
        font_size_spin.setValue(self.params['watermark_font_size'])
        font_size_spin.valueChanged.connect(lambda v: self.params.update({'watermark_font_size': v}))
        form.addWidget(font_size_spin, 1, 1)

        form.addWidget(QLabel("位置:"), 1, 2)
        pos_combo = QComboBox()
        pos_combo.addItems(['top_left', 'top_right', 'bottom_left', 'bottom_right', 'center'])
        pos_combo.setCurrentText(self.params['watermark_pos'])
        pos_combo.currentTextChanged.connect(lambda v: self.params.update({'watermark_pos': v}))
        form.addWidget(pos_combo, 1, 3)

        self.param_layout.addLayout(form)

    def layout_color(self):
        """色彩调节参数"""
        form = QGridLayout()

        # 亮度
        form.addWidget(QLabel("亮度 (-1.0 ~ 1.0):"), 0, 0)
        bright_slider = QSlider(Qt.Horizontal)
        bright_slider.setRange(-100, 100)
        bright_slider.setValue(int(self.params['brightness'] * 100))
        bright_label = QLabel(f"{self.params['brightness']:.2f}")
        bright_slider.valueChanged.connect(
            lambda v: (self.params.update({'brightness': v / 100}), bright_label.setText(f"{v / 100:.2f}"))
        )
        bright_layout = QHBoxLayout()
        bright_layout.addWidget(bright_slider)
        bright_layout.addWidget(bright_label)
        form.addLayout(bright_layout, 0, 1)

        # 对比度
        form.addWidget(QLabel("对比度 (0.0 ~ 2.0):"), 1, 0)
        contrast_slider = QSlider(Qt.Horizontal)
        contrast_slider.setRange(0, 200)
        contrast_slider.setValue(int(self.params['contrast'] * 100))
        contrast_label = QLabel(f"{self.params['contrast']:.2f}")
        contrast_slider.valueChanged.connect(
            lambda v: (self.params.update({'contrast': v / 100}), contrast_label.setText(f"{v / 100:.2f}"))
        )
        contrast_layout = QHBoxLayout()
        contrast_layout.addWidget(contrast_slider)
        contrast_layout.addWidget(contrast_label)
        form.addLayout(contrast_layout, 1, 1)

        # 饱和度
        form.addWidget(QLabel("饱和度 (0.0 ~ 3.0):"), 2, 0)
        sat_slider = QSlider(Qt.Horizontal)
        sat_slider.setRange(0, 300)
        sat_slider.setValue(int(self.params['saturation'] * 100))
        sat_label = QLabel(f"{self.params['saturation']:.2f}")
        sat_slider.valueChanged.connect(
            lambda v: (self.params.update({'saturation': v / 100}), sat_label.setText(f"{v / 100:.2f}"))
        )
        sat_layout = QHBoxLayout()
        sat_layout.addWidget(sat_slider)
        sat_layout.addWidget(sat_label)
        form.addLayout(sat_layout, 2, 1)

        self.param_layout.addLayout(form)

    def layout_rotate(self):
        """旋转参数"""
        rotate_combo = QComboBox()
        rotate_combo.addItems([
            '顺时针旋转90度',
            '逆时针旋转90度',
            '旋转180度',
            '水平翻转',
            '垂直翻转'
        ])
        rotate_combo.currentTextChanged.connect(
            lambda v: self.params.update({'rotate': {
                '顺时针旋转90度': 'clock_90',
                '逆时针旋转90度': 'cclock_90',
                '旋转180度': 'rotate_180',
                '水平翻转': 'hflip',
                '垂直翻转': 'vflip'
            }.get(v, 'clock_90')})
        )
        self.param_layout.addWidget(rotate_combo)

    def layout_volume(self):
        """音量参数"""
        form = QHBoxLayout()
        form.addWidget(QLabel("音量调节:"))
        vol_combo = QComboBox()
        vol_combo.addItems(['-20dB', '-10dB', '-5dB', '0dB (不变)', '+5dB', '+10dB', '+20dB'])
        vol_combo.setCurrentText(self.params['volume'])
        vol_combo.currentTextChanged.connect(lambda v: self.params.update({'volume': v.split()[0]}))
        form.addWidget(vol_combo)
        form.addStretch()
        self.param_layout.addLayout(form)

    def layout_snapshot(self):
        """截图参数"""
        form = QGridLayout()

        form.addWidget(QLabel("时间点 (HH:MM:SS):"), 0, 0)
        time_edit = QLineEdit(self.params['start_time'])
        time_edit.textChanged.connect(lambda v: self.params.update({'start_time': v}))
        form.addWidget(time_edit, 0, 1)

        form.addWidget(QLabel("输出格式:"), 1, 0)
        format_combo = QComboBox()
        format_combo.addItems(['jpg', 'png', 'bmp'])
        format_combo.setCurrentText(self.params['snapshot_format'])
        format_combo.currentTextChanged.connect(lambda v: self.params.update({'snapshot_format': v}))
        form.addWidget(format_combo, 1, 1)

        self.param_layout.addLayout(form)

    def layout_extract_audio(self):
        """提取音频参数"""
        form = QGridLayout()

        form.addWidget(QLabel("输出格式:"), 0, 0)
        format_combo = QComboBox()
        format_combo.addItems(['mp3', 'aac', 'wav', 'flac', 'opus'])
        format_combo.setCurrentText(self.params['audio_format'])
        format_combo.currentTextChanged.connect(lambda v: self.params.update({'audio_format': v}))
        form.addWidget(format_combo, 0, 1)

        form.addWidget(QLabel("比特率:"), 1, 0)
        bitrate_combo = QComboBox()
        bitrate_combo.addItems(['128k', '192k', '256k', '320k'])
        bitrate_combo.setCurrentText(self.params['audio_bitrate'])
        bitrate_combo.currentTextChanged.connect(lambda v: self.params.update({'audio_bitrate': v}))
        form.addWidget(bitrate_combo, 1, 1)

        self.param_layout.addLayout(form)

    def layout_speed(self):
        """变速参数"""
        form = QGridLayout()

        form.addWidget(QLabel("播放速度:"), 0, 0)
        speed_slider = QSlider(Qt.Horizontal)
        speed_slider.setRange(25, 400)  # 0.25x ~ 4.0x
        speed_slider.setValue(int(self.params['speed'] * 100))
        speed_label = QLabel(f"{self.params['speed']:.2f}x")
        speed_slider.valueChanged.connect(
            lambda v: (self.params.update({'speed': v / 100}), speed_label.setText(f"{v / 100:.2f}x"))
        )

        speed_layout = QHBoxLayout()
        speed_layout.addWidget(speed_slider)
        speed_layout.addWidget(speed_label)
        form.addLayout(speed_layout, 0, 1)

        self.param_layout.addLayout(form)

        # 预设按钮
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("快捷:"))
        for name, val in [('0.5x 慢放', 0.5), ('0.75x', 0.75), ('正常', 1.0), ('1.5x', 1.5), ('2x 快进', 2.0)]:
            btn = QPushButton(name)
            btn.clicked.connect(lambda _, v=val: speed_slider.setValue(int(v * 100)))
            preset_layout.addWidget(btn)
        preset_layout.addStretch()
        self.param_layout.addLayout(preset_layout)

    def layout_gif(self):
        """GIF 导出参数"""
        form = QGridLayout()

        form.addWidget(QLabel("宽度 (像素):"), 0, 0)
        width_spin = QSpinBox()
        width_spin.setRange(80, 1920)
        width_spin.setValue(self.params['gif_width'])
        width_spin.valueChanged.connect(lambda v: self.params.update({'gif_width': v}))
        form.addWidget(width_spin, 0, 1)

        form.addWidget(QLabel("帧率 (fps):"), 1, 0)
        fps_spin = QSpinBox()
        fps_spin.setRange(5, 30)
        fps_spin.setValue(self.params['gif_fps'])
        fps_spin.valueChanged.connect(lambda v: self.params.update({'gif_fps': v}))
        form.addWidget(fps_spin, 1, 1)

        self.param_layout.addLayout(form)

        tip = QLabel("💡 帧率越高越流畅但文件越大，推荐 10-15 fps")
        tip.setStyleSheet("color: #888; font-size: 10px;")
        self.param_layout.addWidget(tip)

    def layout_av_merge(self):
        """音画合并参数"""
        reencode_check = QCheckBox("强制音频重新编码为 AAC (兼容性更好，速度较慢)")
        reencode_check.setChecked(self.params['av_reencode'])
        reencode_check.stateChanged.connect(lambda s: self.params.update({'av_reencode': bool(s)}))
        self.param_layout.addWidget(reencode_check)

        tip = QLabel("💡 默认使用 copy 模式极速合并，如果合并后无声音请勾选重新编码")
        tip.setStyleSheet("color: #888; font-size: 10px;")
        tip.setWordWrap(True)
        self.param_layout.addWidget(tip)

    def layout_denoise(self):
        """降噪参数"""
        form = QHBoxLayout()
        form.addWidget(QLabel("降噪强度:"))
        denoise_combo = QComboBox()
        denoise_combo.addItems(['light', 'medium', 'strong'])
        denoise_combo.setCurrentText(self.params['denoise_strength'])
        denoise_combo.currentTextChanged.connect(lambda v: self.params.update({'denoise_strength': v}))
        form.addWidget(denoise_combo)
        form.addStretch()
        self.param_layout.addLayout(form)

    def layout_stabilize(self):
        """防抖参数"""
        form = QGridLayout()

        form.addWidget(QLabel("抖动程度 (1-10):"), 0, 0)
        shakiness_spin = QSpinBox()
        shakiness_spin.setRange(1, 10)
        shakiness_spin.setValue(self.params['stabilize_shakiness'])
        shakiness_spin.valueChanged.connect(lambda v: self.params.update({'stabilize_shakiness': v}))
        form.addWidget(shakiness_spin, 0, 1)

        self.param_layout.addLayout(form)

        tip = QLabel("⚠️ 防抖需要两次处理（分析+稳定），耗时较长")
        tip.setStyleSheet("color: #f90; font-size: 10px;")
        self.param_layout.addWidget(tip)

    # ==========================================
    # Tab 2: 任务队列
    # ==========================================

    def init_queue_tab(self):
        """初始化任务队列选项卡"""
        layout = QVBoxLayout(self.tab_queue)

        # 工具栏
        toolbar = QHBoxLayout()

        btn_start_queue = QPushButton("▶️ 开始队列")
        btn_start_queue.clicked.connect(self.start_queue)
        toolbar.addWidget(btn_start_queue)

        btn_pause_queue = QPushButton("⏸️ 暂停队列")
        btn_pause_queue.clicked.connect(self.pause_queue)
        toolbar.addWidget(btn_pause_queue)

        btn_clear_queue = QPushButton("🗑️ 清空队列")
        btn_clear_queue.clicked.connect(self.clear_queue)
        toolbar.addWidget(btn_clear_queue)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # 任务列表
        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(6)
        self.queue_table.setHorizontalHeaderLabels(['任务名称', '文件', '状态', '进度', '添加时间', '操作'])
        self.queue_table.horizontalHeader().setStretchLastSection(False)
        self.queue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.queue_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.queue_table.setSelectionBehavior(QTableWidget.SelectRows)

        layout.addWidget(self.queue_table)

    def update_queue_table(self):
        """更新队列表格"""
        self.queue_table.setRowCount(len(self.task_queue.tasks))

        for i, task in enumerate(self.task_queue.tasks):
            self.queue_table.setItem(i, 0, QTableWidgetItem(task.get('task_name', '')))
            self.queue_table.setItem(i, 1, QTableWidgetItem(task.get('file_name', '')))
            self.queue_table.setItem(i, 2, QTableWidgetItem(task.get('status', '')))

            # 进度条
            progress_bar = QProgressBar()
            progress_bar.setValue(task.get('progress', 0))
            self.queue_table.setCellWidget(i, 3, progress_bar)

            self.queue_table.setItem(i, 4, QTableWidgetItem(task.get('add_time', '')))

            # 操作按钮
            btn_remove = QPushButton("移除")
            btn_remove.clicked.connect(lambda _, tid=task['id']: self.remove_queue_task(tid))
            self.queue_table.setCellWidget(i, 5, btn_remove)

    def start_queue(self):
        """开始执行队列"""
        if self.current_worker and self.current_worker.isRunning():
            QMessageBox.warning(self, "提示", "当前有任务正在执行中，请等待完成")
            return

        self.process_next_queue_task()

    def process_next_queue_task(self):
        """处理下一个队列任务"""
        task = self.task_queue.get_next_task()
        if not task:
            self.log("📋 队列已全部完成")
            self.status_bar.showMessage("就绪")
            return

        self.log(f"📋 从队列取出任务: {task['task_name']}")
        self.execute_task(task, from_queue=True)

    def pause_queue(self):
        """暂停队列（停止当前任务）"""
        if self.current_worker:
            self.stop_current_task()

    def clear_queue(self):
        """清空队列"""
        reply = QMessageBox.question(
            self, "确认", "确定要清空任务队列吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.task_queue.clear_queue()
            self.update_queue_table()
            self.log("🗑️ 任务队列已清空")

    def remove_queue_task(self, task_id: str):
        """移除队列任务"""
        self.task_queue.remove_task(task_id)
        self.update_queue_table()

    # ==========================================
    # Tab 3: 历史记录
    # ==========================================

    def init_history_tab(self):
        """初始化历史记录选项卡"""
        layout = QVBoxLayout(self.tab_history)

        # 工具栏
        toolbar = QHBoxLayout()

        btn_clear_history = QPushButton("🗑️ 清空历史")
        btn_clear_history.clicked.connect(self.clear_history)
        toolbar.addWidget(btn_clear_history)

        btn_export_history = QPushButton("💾 导出历史")
        btn_export_history.clicked.connect(self.export_history)
        toolbar.addWidget(btn_export_history)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # 历史列表
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(['任务名称', '文件', '状态', '开始时间', '结束时间', '结果'])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)

        layout.addWidget(self.history_table)

    def update_history_table(self):
        """更新历史记录表格"""
        self.history_table.setRowCount(len(self.task_queue.history))

        for i, task in enumerate(self.task_queue.history):
            self.history_table.setItem(i, 0, QTableWidgetItem(task.get('task_name', '')))
            self.history_table.setItem(i, 1, QTableWidgetItem(task.get('file_name', '')))

            status_item = QTableWidgetItem(task.get('status', ''))
            if task.get('status') == '成功':
                status_item.setForeground(QColor(0, 200, 0))
            else:
                status_item.setForeground(QColor(255, 80, 80))
            self.history_table.setItem(i, 2, status_item)

            self.history_table.setItem(i, 3, QTableWidgetItem(task.get('start_time', '')))
            self.history_table.setItem(i, 4, QTableWidgetItem(task.get('end_time', '')))
            self.history_table.setItem(i, 5, QTableWidgetItem(task.get('message', '')))

    def clear_history(self):
        """清空历史记录"""
        reply = QMessageBox.question(
            self, "确认", "确定要清空历史记录吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.task_queue.history.clear()
            self.update_history_table()
            self.log("🗑️ 历史记录已清空")

    def export_history(self):
        """导出历史记录为 CSV"""
        if not self.task_queue.history:
            QMessageBox.information(self, "提示", "暂无历史记录")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出历史记录", "history.csv", "CSV Files (*.csv)"
        )

        if file_path:
            try:
                import csv
                with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['任务名称', '文件', '状态', '开始时间', '结束时间', '结果'])
                    for task in self.task_queue.history:
                        writer.writerow([
                            task.get('task_name', ''),
                            task.get('file_name', ''),
                            task.get('status', ''),
                            task.get('start_time', ''),
                            task.get('end_time', ''),
                            task.get('message', '')
                        ])
                QMessageBox.information(self, "成功", f"历史记录已导出至:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")

    # ==========================================
    # Tab 4: 设置
    # ==========================================

    def init_settings_tab(self):
        """初始化设置选项卡"""
        layout = QVBoxLayout(self.tab_settings)
        layout.setSpacing(20)

        # FFmpeg 设置
        ffmpeg_group = QGroupBox("FFmpeg 环境")
        ffmpeg_layout = QVBoxLayout(ffmpeg_group)

        ffmpeg_info = QLabel("FFmpeg 是本工具的核心依赖，用于处理视频和音频。")
        ffmpeg_layout.addWidget(ffmpeg_info)

        btn_check = QPushButton("🔍 检测 FFmpeg 环境")
        btn_check.clicked.connect(self.check_ffmpeg)
        ffmpeg_layout.addWidget(btn_check)

        btn_download = QPushButton("📥 下载 FFmpeg (打开官网)")
        btn_download.clicked.connect(lambda: self.open_url("https://ffmpeg.org/download.html"))
        ffmpeg_layout.addWidget(btn_download)

        layout.addWidget(ffmpeg_group)

        # 界面设置
        ui_group = QGroupBox("界面设置")
        ui_layout = QVBoxLayout(ui_group)

        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("主题:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['深色主题', '浅色主题'])
        self.theme_combo.setCurrentText('深色主题' if self.settings.get('theme', 'dark') == 'dark' else '浅色主题')
        self.theme_combo.currentTextChanged.connect(self.on_theme_combo_changed)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        ui_layout.addLayout(theme_layout)

        layout.addWidget(ui_group)

        # 关于
        about_group = QGroupBox("关于")
        about_layout = QVBoxLayout(about_group)

        about_text = QLabel(
            f"<h3>{APP_NAME} {APP_VERSION}</h3>"
            "<p>功能强大的 FFmpeg 图形化前端工具</p>"
            "<p>支持视频编辑、格式转换、字幕处理等 20+ 功能</p>"
            "<p><br>© 2024 All Rights Reserved</p>"
        )
        about_text.setOpenExternalLinks(True)
        about_layout.addWidget(about_text)

        layout.addWidget(about_group)

        layout.addStretch()

    # ==========================================
    # 文件操作
    # ==========================================

    def browse_file(self, line_edit: QLineEdit):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", "所有文件 (*.*)"
        )
        if file_path:
            line_edit.setText(file_path)

    def browse_directory(self, line_edit: QLineEdit):
        """浏览目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if dir_path:
            line_edit.setText(dir_path)

    def drag_enter_event(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def drop_event(self, event: QDropEvent, line_edit: QLineEdit):
        """拖拽放下事件"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            line_edit.setText(file_path)
            event.acceptProposedAction()

    def auto_match_extra(self):
        """智能匹配字幕或音频文件"""
        video_path = self.video_path.text()
        if not video_path or not os.path.exists(video_path):
            QMessageBox.warning(self, "提示", "请先选择视频文件")
            return

        task_key = self.task_combo.currentData()
        video_file = Path(video_path)

        if task_key in ('av_merge', 'replace_audio'):
            # 匹配音频
            exts = ['.mp3', '.aac', '.wav', '.m4a', '.opus', '.flac']
        else:
            # 匹配字幕
            exts = ['.srt', '.ass', '.ssa']

        for ext in exts:
            candidate = video_file.with_suffix(ext)
            if candidate.exists():
                self.extra_path.setText(str(candidate))
                self.log(f"✓ 自动匹配到文件: {candidate.name}")
                return

        QMessageBox.information(self, "提示", "未找到匹配的字幕或音频文件")

    # ==========================================
    # 任务执行
    # ==========================================

    def add_to_queue(self):
        """添加任务到队列"""
        task = self.prepare_task()
        if not task:
            return

        files = task['files']
        task_key = task['task_key']
        task_name = self.TASKS[task_key][0]
        params = task['params']

        # 为每个文件创建队列任务
        for file_path in files:
            queue_task = {
                'task_key': task_key,
                'task_name': task_name,
                'file_path': str(file_path),
                'file_name': file_path.name,
                'params': params.copy(),
            }
            self.task_queue.add_task(queue_task)

        self.update_queue_table()
        self.log(f"✓ 已添加 {len(files)} 个任务到队列")
        QMessageBox.information(self, "成功", f"已添加 {len(files)} 个任务到队列")

    def execute_immediately(self):
        """立即执行任务"""
        task = self.prepare_task()
        if not task:
            return

        if self.current_worker and self.current_worker.isRunning():
            reply = QMessageBox.question(
                self, "确认", "当前有任务正在执行，是否添加到队列？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.add_to_queue()
            return

        self.execute_task(task)

    def prepare_task(self) -> Optional[Dict]:
        """准备任务数据"""
        task_key = self.task_combo.currentData()
        task_info = self.TASKS[task_key]

        # 获取文件列表
        files = []
        if self.radio_single.isChecked():
            video_path = self.video_path.text()
            if not video_path or not os.path.exists(video_path):
                QMessageBox.warning(self, "错误", "请选择有效的视频文件")
                return None
            files.append(Path(video_path))
        else:
            dir_path = self.dir_path.text()
            if not dir_path or not os.path.isdir(dir_path):
                QMessageBox.warning(self, "错误", "请选择有效的文件夹")
                return None

            exts = [x.strip().lower() for x in self.ext_filter.text().split(',')]
            for ext in exts:
                ext = ext if ext.startswith('.') else f'.{ext}'
                files.extend(Path(dir_path).glob(f'*{ext}'))

            if not files:
                QMessageBox.warning(self, "提示", "未找到符合条件的文件")
                return None

        # 检查辅助文件
        if task_info[1]:  # 需要辅助文件
            extra_path = self.extra_path.text()
            if not extra_path or not os.path.exists(extra_path):
                QMessageBox.warning(self, "错误", "请选择辅助文件（字幕或音频）")
                return None

        return {
            'task_key': task_key,
            'task_name': task_info[0],
            'files': files,
            'params': self.params.copy(),
        }

    def execute_task(self, task: Dict, from_queue: bool = False):
        """执行任务"""
        files = task['files']
        task_key = task['task_key']
        params = task['params']

        if task_key == 'concat':
            # 拼接任务：一次性处理所有文件
            self.execute_concat(files, params)
        else:
            # 其他任务：逐个处理文件
            if from_queue:
                # 从队列执行，只处理一个文件
                file_path = Path(task['file_path'])
                self.execute_single_file(task_key, file_path, params, from_queue)
            else:
                # 立即执行，处理所有文件
                self.current_file_index = 0
                self.current_files = files
                self.current_task_key = task_key
                self.current_params = params
                self.execute_next_file()

    def execute_next_file(self):
        """执行下一个文件"""
        if self.current_file_index >= len(self.current_files):
            self.log("✓ 所有文件处理完成")
            self.status_bar.showMessage("就绪")
            self.btn_execute.setEnabled(True)
            self.btn_add_queue.setEnabled(True)
            self.btn_stop.setEnabled(False)
            return

        file_path = self.current_files[self.current_file_index]
        self.execute_single_file(
            self.current_task_key,
            file_path,
            self.current_params,
            from_queue=False
        )

    def execute_single_file(self, task_key: str, file_path: Path, params: Dict, from_queue: bool = False):
        """执行单个文件任务"""
        # 跳过已处理的文件
        if '_out' in file_path.stem or '_joined' in file_path.stem:
            self.log(f"⏭️ 跳过已处理的文件: {file_path.name}")
            if not from_queue:
                self.current_file_index += 1
                self.execute_next_file()
            else:
                self.process_next_queue_task()
            return

        self.log(f"🎬 开始处理: {file_path.name}")
        self.status_bar.showMessage(f"正在处理: {file_path.name}")

        # 生成 FFmpeg 命令
        cmd, output_file = self.build_ffmpeg_command(task_key, file_path, params)

        if not cmd:
            self.log("❌ 命令生成失败")
            if not from_queue:
                self.current_file_index += 1
                self.execute_next_file()
            else:
                self.task_queue.finish_current_task(False, "命令生成失败")
                self.process_next_queue_task()
            return

        # 创建工作线程
        self.current_worker = FFmpegWorker(cmd, f"{task_key}: {file_path.name}")
        self.current_worker.progress_signal.connect(self.on_progress_update)
        self.current_worker.log_signal.connect(self.log)
        self.current_worker.finished_signal.connect(
            lambda success, msg: self.on_task_finished(success, msg, from_queue)
        )

        # 更新 UI
        self.btn_execute.setEnabled(False)
        self.btn_add_queue.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 启动线程
        self.current_worker.start()

    def execute_concat(self, files: List[Path], params: Dict):
        """执行拼接任务"""
        if len(files) < 2:
            QMessageBox.warning(self, "错误", "拼接任务至少需要 2 个文件")
            return

        files = sorted(files, key=lambda x: x.name)
        list_file = files[0].parent / "filelist.txt"
        output_file = files[0].parent / f"{files[0].parent.name}_joined.mp4"

        try:
            with open(list_file, 'w', encoding='utf-8') as f:
                for file_path in files:
                    f.write(f"file '{file_path.name}'\n")

            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', str(list_file),
                '-c', 'copy',
                '-y', str(output_file)
            ]

            self.current_worker = FFmpegWorker(cmd, f"拼接 {len(files)} 个文件")
            self.current_worker.progress_signal.connect(self.on_progress_update)
            self.current_worker.log_signal.connect(self.log)
            self.current_worker.finished_signal.connect(
                lambda success, msg: (
                    self.on_task_finished(success, msg, False),
                    list_file.unlink(missing_ok=True)
                )
            )

            self.btn_execute.setEnabled(False)
            self.btn_add_queue.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            self.current_worker.start()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"拼接任务失败:\n{str(e)}")
            list_file.unlink(missing_ok=True)

    def build_ffmpeg_command(self, task_key: str, input_file: Path, params: Dict) -> Tuple[
        Optional[List[str]], Optional[str]]:
        """构建 FFmpeg 命令"""
        cmd = ['ffmpeg', '-i', str(input_file)]
        vf = []  # 视频滤镜
        af = []  # 音频滤镜

        # 输出文件名后缀
        suffix_map = {
            'merge_soft': '_merged.mkv',
            'merge_hard': '_hard.mp4',
            'av_merge': '_merged.mp4',
            'compress': '_compressed.mp4',
            'convert': f"_converted.{params['output_format']}",
            'trim': '_trimmed.mp4',
            'crop': '_cropped.mp4',
            'resize': '_resized.mp4',
            'watermark': '_watermark.mp4',
            'color': '_color.mp4',
            'rotate': '_rotated.mp4',
            'replace_audio': '_new_audio.mp4',
            'volume': '_volume.mp4',
            'snapshot': f".{params['snapshot_format']}",
            'extract_audio': f".{params['audio_format']}",
            'extract_sub': '.srt',
            'clean_meta': '_clean.mp4',
            'speed': '_speed.mp4',
            'gif': '.gif',
            'reverse': '_reverse.mp4',
            'denoise': '_denoise.mp4',
            'stabilize': '_stable.mp4',
        }

        suffix = suffix_map.get(task_key, '_out.mp4')
        if suffix.startswith('.'):
            output_file = str(input_file.with_suffix(suffix))
        else:
            output_file = str(input_file.with_name(input_file.stem + suffix))

        # 根据任务类型构建命令
        try:
            if task_key == 'merge_soft':
                extra = self.extra_path.text()
                cmd.extend([
                    '-i', extra,
                    '-c', 'copy',
                    '-c:s', 'srt',
                    '-metadata:s:s:0', 'language=chi',
                    '-y', output_file
                ])

            elif task_key == 'merge_hard':
                extra = self.extra_path.text()
                path_esc = extra.replace('\\', '/').replace(':', '\\:')
                vf.append(f"subtitles='{path_esc}'")

            elif task_key == 'av_merge':
                extra = self.extra_path.text()
                cmd = [
                    'ffmpeg', '-i', str(input_file), '-i', extra,
                    '-c:v', 'copy',
                ]
                if params.get('av_reencode'):
                    cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
                else:
                    cmd.extend(['-c:a', 'copy'])
                cmd.extend([
                    '-map', '0:v:0', '-map', '1:a:0',
                    '-shortest',
                    '-y', output_file
                ])
                return cmd, output_file

            elif task_key == 'compress':
                codec = params['codec']
                crf = params['crf']
                preset = params['preset']
                cmd.extend([
                    '-c:v', codec,
                    '-crf', str(crf),
                    '-preset', preset,
                    '-c:a', 'aac', '-b:a', '128k'
                ])

            elif task_key == 'convert':
                codec = params['codec']
                if codec == 'copy':
                    cmd.extend(['-c', 'copy'])
                else:
                    cmd.extend(['-c:v', codec, '-c:a', 'aac'])

            elif task_key == 'trim':
                cmd = [
                    'ffmpeg',
                    '-ss', params['start_time'],
                    '-to', params['end_time'],
                    '-i', str(input_file),
                    '-c:v', 'libx264', '-crf', '23',
                    '-c:a', 'aac',
                    '-y', output_file
                ]
                return cmd, output_file

            elif task_key == 'resize':
                w = params['width']
                h = params['height']
                if params['keep_aspect']:
                    vf.append(f"scale={w}:-2")
                else:
                    vf.append(f"scale={w}:{h}")

            elif task_key == 'crop':
                crop_str = f"{params['crop_w']}:{params['crop_h']}:{params['crop_x']}:{params['crop_y']}"
                vf.append(f"crop={crop_str}")

            elif task_key == 'watermark':
                text = params['watermark_text'].replace("'", "").replace(":", "\\:")
                font_size = params['watermark_font_size']
                pos = params['watermark_pos']

                # 位置映射
                pos_map = {
                    'top_left': 'x=20:y=20',
                    'top_right': 'x=w-tw-20:y=20',
                    'bottom_left': 'x=20:y=h-th-20',
                    'bottom_right': 'x=w-tw-20:y=h-th-20',
                    'center': 'x=(w-tw)/2:y=(h-th)/2'
                }
                pos_str = pos_map.get(pos, 'x=20:y=20')

                # 尝试使用系统字体
                font_path = ""
                if os.name == 'nt':
                    font_path = "C:/Windows/Fonts/msyh.ttc"
                if font_path and os.path.exists(font_path):
                    font_path = font_path.replace('\\', '/').replace(':', '\\:')
                    vf.append(
                        f"drawtext=fontfile='{font_path}':text='{text}':"
                        f"fontsize={font_size}:{pos_str}:"
                        f"fontcolor=white:box=1:boxcolor=black@0.5"
                    )
                else:
                    vf.append(
                        f"drawtext=text='{text}':"
                        f"fontsize={font_size}:{pos_str}:"
                        f"fontcolor=white:box=1:boxcolor=black@0.5"
                    )

            elif task_key == 'color':
                eq_str = (
                    f"eq=brightness={params['brightness']}:"
                    f"contrast={params['contrast']}:"
                    f"saturation={params['saturation']}"
                )
                vf.append(eq_str)

            elif task_key == 'rotate':
                rotate_map = {
                    'clock_90': 'transpose=1',
                    'cclock_90': 'transpose=2',
                    'rotate_180': 'transpose=1,transpose=1',
                    'hflip': 'hflip',
                    'vflip': 'vflip'
                }
                vf.append(rotate_map.get(params['rotate'], 'transpose=1'))

            elif task_key == 'replace_audio':
                extra = self.extra_path.text()
                cmd = [
                    'ffmpeg', '-i', str(input_file), '-i', extra,
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-map', '0:v:0', '-map', '1:a:0',
                    '-shortest',
                    '-y', output_file
                ]
                return cmd, output_file

            elif task_key == 'volume':
                af.append(f"volume={params['volume']}")

            elif task_key == 'snapshot':
                cmd = [
                    'ffmpeg',
                    '-ss', params['start_time'],
                    '-i', str(input_file),
                    '-vframes', '1',
                    '-q:v', '2',
                    '-y', output_file
                ]
                return cmd, output_file

            elif task_key == 'extract_audio':
                audio_format = params['audio_format']
                bitrate = params['audio_bitrate']

                codec_map = {
                    'mp3': 'libmp3lame',
                    'aac': 'aac',
                    'wav': 'pcm_s16le',
                    'flac': 'flac',
                    'opus': 'libopus'
                }

                cmd.extend([
                    '-vn',
                    '-acodec', codec_map.get(audio_format, 'libmp3lame'),
                    '-b:a', bitrate,
                    '-y', output_file
                ])

            elif task_key == 'extract_sub':
                # 提取第一个字幕轨
                cmd.extend([
                    '-map', '0:s:0',
                    '-c', 'copy',
                    '-y', output_file
                ])

            elif task_key == 'clean_meta':
                cmd.extend([
                    '-map_metadata', '-1',
                    '-c', 'copy',
                    '-y', output_file
                ])

            elif task_key == 'speed':
                speed = params['speed']
                if speed <= 0:
                    self.log("❌ 倍速必须大于 0")
                    return None, None

                vf.append(f"setpts={1.0 / speed:.4f}*PTS")

                # atempo 支持 0.5-2.0，超出范围需要级联
                if 0.5 <= speed <= 2.0:
                    af.append(f"atempo={speed:.2f}")
                else:
                    # 级联多个 atempo
                    current = speed
                    while current > 2.0:
                        af.append("atempo=2.0")
                        current /= 2.0
                    while current < 0.5:
                        af.append("atempo=0.5")
                        current /= 0.5
                    if current != 1.0:
                        af.append(f"atempo={current:.2f}")

            elif task_key == 'gif':
                width = params['gif_width']
                fps = params['gif_fps']
                vf.append(f"fps={fps},scale={width}:-1:flags=lanczos")
                cmd.extend(['-an', '-c:v', 'gif'])

            elif task_key == 'reverse':
                vf.append("reverse")
                af.append("areverse")

            elif task_key == 'denoise':
                strength_map = {
                    'light': 'hqdn3d=2:1:2:1',
                    'medium': 'hqdn3d=4:3:6:4.5',
                    'strong': 'hqdn3d=8:6:12:9'
                }
                vf.append(strength_map.get(params['denoise_strength'], 'hqdn3d=4:3:6:4.5'))

            elif task_key == 'stabilize':
                # 防抖需要两次处理
                shakiness = params['stabilize_shakiness']
                trf_file = input_file.with_suffix('.trf')

                # 第一步：分析
                cmd1 = [
                    'ffmpeg', '-i', str(input_file),
                    '-vf', f"vidstabdetect=shakiness={shakiness}:result={trf_file}",
                    '-f', 'null', '-'
                ]

                self.log("🔍 正在分析视频抖动...")
                result = subprocess.run(cmd1, capture_output=True)

                if result.returncode != 0:
                    self.log("❌ 视频分析失败")
                    return None, None

                # 第二步：稳定
                vf.append(f"vidstabtransform=input={trf_file}:smoothing=30")

            # 组装滤镜
            if vf:
                cmd.extend(['-vf', ','.join(vf)])
            if af:
                cmd.extend(['-af', ','.join(af)])

            # 如果使用了滤镜且未指定编码器，默认使用 libx264
            if (vf or af) and '-c:v' not in cmd and task_key != 'gif':
                cmd.extend(['-c:v', 'libx264', '-crf', '23', '-c:a', 'aac'])

            cmd.extend(['-y', output_file])

            return cmd, output_file

        except Exception as e:
            self.log(f"❌ 命令构建失败: {str(e)}")
            return None, None

    def stop_current_task(self):
        """停止当前任务"""
        if self.current_worker:
            self.current_worker.cancel()
            self.log("⏹️ 任务已停止")

    def on_progress_update(self, progress: int):
        """进度更新"""
        self.progress_bar.setValue(progress)
        self.status_bar.showMessage(f"进度: {progress}%")

    def on_task_finished(self, success: bool, message: str, from_queue: bool):
        """任务完成回调"""
        self.progress_bar.setVisible(False)

        if from_queue:
            # 队列任务完成
            self.task_queue.finish_current_task(success, message)
            self.update_history_table()

            # 继续处理下一个队列任务
            self.process_next_queue_task()
        else:
            # 立即执行任务完成
            self.current_file_index += 1
            self.execute_next_file()

    # ==========================================
    # 其他功能
    # ==========================================

    def check_ffmpeg(self):
        """检测 FFmpeg 环境"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                self.log(f"✅ FFmpeg 检测成功: {version_line}")
                QMessageBox.information(self, "成功", f"FFmpeg 环境正常\n\n{version_line}")
            else:
                self.log("❌ FFmpeg 检测失败")
                QMessageBox.critical(self, "错误", "FFmpeg 检测失败")
        except FileNotFoundError:
            self.log("❌ 未找到 FFmpeg，请先安装并添加到环境变量")
            QMessageBox.critical(
                self, "错误",
                "未检测到 FFmpeg！\n\n"
                "请访问 https://ffmpeg.org/download.html 下载安装\n"
                "并将 FFmpeg 添加到系统环境变量 PATH 中"
            )
        except Exception as e:
            self.log(f"❌ FFmpeg 检测异常: {str(e)}")
            QMessageBox.critical(self, "错误", f"FFmpeg 检测异常:\n{str(e)}")

    def log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def clear_log(self):
        """清空日志"""
        self.log_text.clear()

    def apply_theme(self, theme: str):
        """应用 VS Code 风格深色/浅色主题（修复子控件白底问题）"""
        if theme == 'dark':
            palette = QPalette()
            # 基础窗口与文本
            palette.setColor(QPalette.Window, QColor("#1e1e1e"))
            palette.setColor(QPalette.WindowText, QColor("#d4d4d4"))
            palette.setColor(QPalette.Base, QColor("#1e1e1e"))
            palette.setColor(QPalette.AlternateBase, QColor("#252526"))
            palette.setColor(QPalette.ToolTipBase, QColor("#f5f5f5"))
            palette.setColor(QPalette.ToolTipText, QColor("#333333"))
            palette.setColor(QPalette.Text, QColor("#d4d4d4"))
            palette.setColor(QPalette.Button, QColor("#2d2d30"))
            palette.setColor(QPalette.ButtonText, QColor("#d4d4d4"))
            palette.setColor(QPalette.BrightText, QColor("#ff0000"))
            palette.setColor(QPalette.Link, QColor("#569cd6"))
            palette.setColor(QPalette.Highlight, QColor("#264f78"))
            palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
            self.setPalette(palette)

            # 全局样式表（确保所有 QWidget、QScrollArea、QGroupBox 等背景一致）
            global_style = (
                "QWidget { background-color: #1e1e1e; color: #d4d4d4; }"
                "QMainWindow { background-color: #1e1e1e; }"
                "QGroupBox { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #2a2a2a; margin-top: 6px; }"
                "QScrollArea { background-color: #1e1e1e; }"
                "QScrollArea QWidget { background-color: #1e1e1e; }"
                "QTabWidget::pane { background: #1e1e1e; }"
                "QTabBar::tab { background: #252526; color: #d4d4d4; padding: 6px; }"
                "QTabBar::tab:selected { background: #1e1e1e; }"
                "QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #3c3c3c; }"
                "QTableWidget, QListWidget { background-color: #1e1e1e; color: #d4d4d4; gridline-color: #2a2a2a; }"
                "QHeaderView::section { background-color: #2d2d30; color: #d4d4d4; }"
                "QPushButton { background-color: #0e639c; color: #ffffff; border: 0px solid #3c3c3c; padding: 4px 8px; border-radius: 3px; }"
                "QPushButton:hover { background-color: #1177bb; }"
                "QProgressBar { background: #252526; color: #d4d4d4; border: 1px solid #3c3c3c; }"
                "QStatusBar { background: #1e1e1e; color: #d4d4d4; }"
                "QToolTip { background-color: #f5f5f5; color: #111; }"
            )
            self.setStyleSheet(global_style)

            # 日志区单独确保等宽字体与选中高亮
            self.log_text.setStyleSheet(
                "QTextEdit { background-color: #1e1e1e; color: #d4d4d4; "
                "font-family: Consolas, 'Courier New', monospace; font-size: 11px; }"
                "QTextEdit::selection { background: #264f78; color: #ffffff; }"
            )

        else:
            # 恢复系统默认（浅色）
            self.setPalette(self.style().standardPalette())
            self.setStyleSheet("")
            self.log_text.setStyleSheet("")

        self.settings['theme'] = theme
        self.save_settings()

    def toggle_theme(self):
        """切换主题"""
        current = self.settings.get('theme', 'dark')
        new_theme = 'light' if current == 'dark' else 'dark'
        self.apply_theme(new_theme)
        self.theme_combo.setCurrentText('深色主题' if new_theme == 'dark' else '浅色主题')

    def on_theme_combo_changed(self, text: str):
        """主题下拉框改变"""
        theme = 'dark' if text == '深色主题' else 'light'
        self.apply_theme(theme)

    def load_settings(self) -> Dict:
        """加载设置"""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {'theme': 'dark'}

    def save_settings(self):
        """保存设置"""
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
        except:
            pass

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self, f"关于 {APP_NAME}",
            f"<h2>{APP_NAME} {APP_VERSION}</h2>"
            "<p>功能强大的 FFmpeg 图形化前端工具</p>"
            "<p>支持 20+ 视频处理功能：</p>"
            "<ul>"
            "<li>字幕封装与烧录</li>"
            "<li>音画合并与替换</li>"
            "<li>视频剪辑与拼接</li>"
            "<li>格式转换与压缩</li>"
            "<li>画面裁剪与缩放</li>"
            "<li>水印添加与色彩调节</li>"
            "<li>音频提取与调节</li>"
            "<li>GIF 导出与特效处理</li>"
            "</ul>"
            "<p><br>© 2024 All Rights Reserved</p>"
        )

    def open_url(self, url: str):
        """打开 URL"""
        from PyQt5.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl(url))

    def closeEvent(self, event):
        """关闭事件"""
        if self.current_worker and self.current_worker.isRunning():
            reply = QMessageBox.question(
                self, "确认退出",
                "当前有任务正在执行，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            else:
                self.current_worker.cancel()

        self.save_settings()
        event.accept()


# ==========================================
# 程序入口
# ==========================================

def main():
    """主函数"""
    # Windows 高 DPI 支持
    if os.name == 'nt':
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

    # 设置高 DPI 缩放
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    # 设置应用图标（如果有）
    # app.setWindowIcon(QIcon('icon.png'))

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()