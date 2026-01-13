#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutomationToolPro - PyQt5专业版
功能：定时任务、文件监控、网页自动化、宏录制、API测试、数据同步、系统监控、日志管理
作者：LYP
GitHub：https://github.com/lyp0746
邮箱：1610369302@qq.com
版本：2.0.0  
"""  

import sys  
import os  
import json  
import time  
import hashlib  
import shutil  
import threading  
import datetime  
import re  
import webbrowser  
import urllib.request  
import urllib.parse  
import urllib.error  
import psutil  
import platform  
from pathlib import Path  
from typing import Dict, List, Any, Callable, Optional  
from dataclasses import dataclass, asdict  
from enum import Enum  

from PyQt5.QtWidgets import (  
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,  
    QTabWidget, QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox,  
    QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox, QDialog,  
    QDialogButtonBox, QGroupBox, QFormLayout, QSpinBox, QCheckBox,  
    QListWidget, QSplitter, QProgressBar, QSystemTrayIcon, QMenu,  
    QAction, QToolBar, QStatusBar, QHeaderView, QStyle, QTreeWidget,  
    QTreeWidgetItem, QDateTimeEdit, QSlider, QRadioButton  
)  
from PyQt5.QtCore import (  
    Qt, QTimer, QThread, pyqtSignal, QDateTime, QSize, QSettings,  
    QPoint, QPropertyAnimation, QEasingCurve  
)  
from PyQt5.QtGui import (  
    QIcon, QFont, QColor, QPalette, QTextCursor, QPixmap, QPainter,  
    QLinearGradient, QBrush  
)  

# ============================================================================  
# 数据模型  
# ============================================================================  

class TaskStatus(Enum):  
    """任务状态枚举"""  
    READY = "就绪"  
    RUNNING = "运行中"  
    PAUSED = "已暂停"  
    COMPLETED = "已完成"  
    FAILED = "失败"  

@dataclass  
class ScheduledTask:  
    """定时任务数据模型"""  
    id: str  
    name: str  
    interval: int  
    action_type: str  
    action_param: str  
    enabled: bool = True  
    last_run: float = 0  
    next_run: float = 0  
    run_count: int = 0  
    status: str = TaskStatus.READY.value  

@dataclass  
class FileMonitorTask:  
    """文件监控任务数据模型"""  
    id: str  
    name: str  
    path: str  
    pattern: str  
    action: str  
    target: str = ""  
    enabled: bool = True  
    trigger_count: int = 0  
    recursive: bool = False  
    ignore_hidden: bool = True  

@dataclass  
class WebScript:  
    """网页自动化脚本数据模型"""  
    id: str  
    name: str  
    url: str  
    actions: List[Dict[str, str]]  
    timeout: int = 30  
    retry_count: int = 0  
    last_run: str = ""  
    run_count: int = 0  
    success_count: int = 0  

@dataclass  
class MacroRecord:  
    """宏录制数据模型"""  
    id: str  
    name: str  
    events: List[Dict[str, Any]]  
    duration: float  
    created: str  
    play_count: int = 0  
    description: str = ""  

@dataclass  
class APITest:  
    """API测试数据模型"""  
    id: str  
    name: str  
    method: str  
    url: str  
    headers: Dict[str, str]  
    body: str = ""  
    timeout: int = 30  
    expected_status: int = 200  
    last_result: Optional[Dict] = None  
    test_count: int = 0  
    success_count: int = 0  

@dataclass  
class SyncTask:  
    """数据同步任务数据模型"""  
    id: str  
    name: str  
    source: str  
    target: str  
    mode: str = "mirror"  
    exclude_patterns: List[str] = None  
    last_sync: str = ""  
    sync_count: int = 0  
    files_synced: int = 0  

# ============================================================================  
# 任务调度器（后台线程）  
# ============================================================================  

class TaskSchedulerThread(QThread):  
    """定时任务调度线程"""  
    task_executed = pyqtSignal(str, bool, str)  # task_id, success, message  
    
    def __init__(self):  
        super().__init__()  
        self.tasks: List[ScheduledTask] = []  
        self.running = False  
        self.lock = threading.Lock()  
        
    def add_task(self, task: ScheduledTask):  
        """添加任务"""  
        with self.lock:  
            if task.next_run == 0:  
                task.next_run = time.time() + task.interval  
            self.tasks.append(task)  
    
    def remove_task(self, task_id: str):  
        """移除任务"""  
        with self.lock:  
            self.tasks = [t for t in self.tasks if t.id != task_id]  
    
    def update_task(self, task: ScheduledTask):  
        """更新任务"""  
        with self.lock:  
            for i, t in enumerate(self.tasks):  
                if t.id == task.id:  
                    self.tasks[i] = task  
                    break  
    
    def toggle_task(self, task_id: str):  
        """切换任务状态"""  
        with self.lock:  
            for task in self.tasks:  
                if task.id == task_id:  
                    task.enabled = not task.enabled  
                    if task.enabled:  
                        task.next_run = time.time() + task.interval  
                    break  
    
    def get_tasks(self) -> List[ScheduledTask]:  
        """获取所有任务"""  
        with self.lock:  
            return self.tasks.copy()  
    
    def run(self):  
        """运行调度循环"""  
        self.running = True  
        while self.running:  
            current_time = time.time()  
            
            with self.lock:  
                for task in self.tasks:  
                    if task.enabled and current_time >= task.next_run:  
                        self._execute_task(task)  
                        task.last_run = current_time  
                        task.next_run = current_time + task.interval  
                        task.run_count += 1  
            
            time.sleep(1)  
    
    def _execute_task(self, task: ScheduledTask):  
        """执行任务"""  
        try:  
            if task.action_type == "message":  
                message = f"[定时提醒] {task.action_param}"  
                self.task_executed.emit(task.id, True, message)  
                
            elif task.action_type == "command":  
                os.system(task.action_param)  
                self.task_executed.emit(task.id, True, f"已执行命令: {task.action_param}")  
                
            elif task.action_type == "url":  
                webbrowser.open(task.action_param)  
                self.task_executed.emit(task.id, True, f"已打开网页: {task.action_param}")  
                
            elif task.action_type == "script":  
                exec(task.action_param)  
                self.task_executed.emit(task.id, True, "脚本执行成功")  
                
        except Exception as e:  
            self.task_executed.emit(task.id, False, f"执行失败: {str(e)}")  
    
    def stop(self):  
        """停止调度器"""  
        self.running = False  

# ============================================================================  
# 文件监控器（后台线程）  
# ============================================================================  

class FileMonitorThread(QThread):  
    """文件监控线程"""  
    file_changed = pyqtSignal(str, str, str)  # monitor_id, file_path, action  
    
    def __init__(self):  
        super().__init__()  
        self.monitors: List[FileMonitorTask] = []  
        self.running = False  
        self.file_states: Dict[str, Dict] = {}  
        self.lock = threading.Lock()  
        
    def add_monitor(self, monitor: FileMonitorTask):  
        """添加监控任务"""  
        with self.lock:  
            self.monitors.append(monitor)  
    
    def remove_monitor(self, monitor_id: str):  
        """移除监控任务"""  
        with self.lock:  
            self.monitors = [m for m in self.monitors if m.id != monitor_id]  
    
    def update_monitor(self, monitor: FileMonitorTask):  
        """更新监控任务"""  
        with self.lock:  
            for i, m in enumerate(self.monitors):  
                if m.id == monitor.id:  
                    self.monitors[i] = monitor  
                    break  
    
    def toggle_monitor(self, monitor_id: str):  
        """切换监控状态"""  
        with self.lock:  
            for monitor in self.monitors:  
                if monitor.id == monitor_id:  
                    monitor.enabled = not monitor.enabled  
                    break  
    
    def get_monitors(self) -> List[FileMonitorTask]:  
        """获取所有监控任务"""  
        with self.lock:  
            return self.monitors.copy()  
    
    def run(self):  
        """运行监控循环"""  
        self.running = True  
        while self.running:  
            with self.lock:  
                for monitor in self.monitors:  
                    if monitor.enabled:  
                        self._check_files(monitor)  
            time.sleep(2)  
    
    def _check_files(self, monitor: FileMonitorTask):  
        """检查文件变化"""  
        try:  
            path = Path(monitor.path)  
            if not path.exists():  
                return  
            
            # 获取匹配的文件  
            if path.is_dir():  
                if monitor.recursive:  
                    files = list(path.rglob(monitor.pattern))  
                else:  
                    files = list(path.glob(monitor.pattern))  
            else:  
                files = [path] if path.match(monitor.pattern) else []  
            
            # 过滤隐藏文件  
            if monitor.ignore_hidden:  
                files = [f for f in files if not f.name.startswith('.')]  
            
            # 检查每个文件  
            for file in files:  
                if not file.is_file():  
                    continue  
                    
                file_key = str(file)  
                try:  
                    file_stat = file.stat()  
                    file_info = {  
                        'size': file_stat.st_size,  
                        'mtime': file_stat.st_mtime  
                    }  
                    
                    # 检测变化  
                    if file_key not in self.file_states:  
                        self.file_states[file_key] = file_info  
                    elif self.file_states[file_key] != file_info:  
                        self._handle_file_change(monitor, file)  
                        self.file_states[file_key] = file_info  
                        monitor.trigger_count += 1  
                        
                except Exception as e:  
                    print(f"检查文件失败 {file}: {str(e)}")  
                    
        except Exception as e:  
            print(f"监控失败 {monitor.path}: {str(e)}")  
    
    def _handle_file_change(self, monitor: FileMonitorTask, file: Path):  
        """处理文件变化"""  
        try:  
            action = monitor.action  
            
            if action == "copy" and monitor.target:  
                target_dir = Path(monitor.target)  
                target_dir.mkdir(parents=True, exist_ok=True)  
                target_file = target_dir / file.name  
                shutil.copy2(file, target_file)  
                self.file_changed.emit(monitor.id, str(file), f"已复制到 {target_file}")  
                
            elif action == "move" and monitor.target:  
                target_dir = Path(monitor.target)  
                target_dir.mkdir(parents=True, exist_ok=True)  
                target_file = target_dir / file.name  
                shutil.move(str(file), str(target_file))  
                self.file_changed.emit(monitor.id, str(file), f"已移动到 {target_file}")  
                
            elif action == "delete":  
                file.unlink()  
                self.file_changed.emit(monitor.id, str(file), "已删除")  
                
            elif action == "execute" and monitor.target:  
                os.system(f"{monitor.target} \"{file}\"")  
                self.file_changed.emit(monitor.id, str(file), f"已执行: {monitor.target}")  
                
            elif action == "compress":  
                import zipfile  
                target_dir = Path(monitor.target) if monitor.target else file.parent  
                zip_file = target_dir / f"{file.stem}.zip"  
                with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:  
                    zf.write(file, file.name)  
                self.file_changed.emit(monitor.id, str(file), f"已压缩到 {zip_file}")  
                
        except Exception as e:  
            self.file_changed.emit(monitor.id, str(file), f"处理失败: {str(e)}")  
    
    def stop(self):  
        """停止监控"""  
        self.running = False  

# ============================================================================  
# 系统监控器（后台线程）  
# ============================================================================  

class SystemMonitorThread(QThread):  
    """系统资源监控线程"""  
    stats_updated = pyqtSignal(dict)  
    
    def __init__(self):  
        super().__init__()  
        self.running = False  
        
    def run(self):  
        """运行监控循环"""  
        self.running = True  
        while self.running:  
            try:  
                stats = {  
                    'cpu_percent': psutil.cpu_percent(interval=1),  
                    'memory': psutil.virtual_memory(),  
                    'disk': psutil.disk_usage('/'),  
                    'network': psutil.net_io_counters(),  
                    'processes': len(psutil.pids()),  
                    'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
                }  
                self.stats_updated.emit(stats)  
            except Exception as e:  
                print(f"系统监控错误: {str(e)}")  
            time.sleep(2)  
    
    def stop(self):  
        """停止监控"""  
        self.running = False  

# ============================================================================  
# 主窗口  
# ============================================================================  

class AutomationToolPro(QMainWindow):  
    """主窗口类"""  
    
    def __init__(self):  
        super().__init__()  
        self.setWindowTitle("AutomationToolPro v2.0 - 专业自动化工具")  
        self.setGeometry(100, 100, 1400, 900)  
        
        # 初始化数据  
        self.config_file = "automation_pro_config.json"  
        self.log_file = "automation_pro.log"  
        
        # 初始化线程  
        self.scheduler_thread = TaskSchedulerThread()  
        self.file_monitor_thread = FileMonitorThread()  
        self.system_monitor_thread = SystemMonitorThread()  
        
        # 连接信号  
        self.scheduler_thread.task_executed.connect(self.on_task_executed)  
        self.file_monitor_thread.file_changed.connect(self.on_file_changed)  
        self.system_monitor_thread.stats_updated.connect(self.on_stats_updated)  
        
        # 创建UI  
        self.init_ui()  
        
        # 加载配置  
        self.load_config()  
        
        # 启动后台线程  
        self.scheduler_thread.start()  
        self.file_monitor_thread.start()  
        self.system_monitor_thread.start()  
        
        # 设置定时器更新UI  
        self.update_timer = QTimer()  
        self.update_timer.timeout.connect(self.update_all_views)  
        self.update_timer.start(1000)  
        
        # 应用样式  
        self.apply_modern_style()  
        
    def init_ui(self):  
        """初始化UI"""  
        # 中心部件  
        central_widget = QWidget()  
        self.setCentralWidget(central_widget)  
        
        # 主布局  
        main_layout = QVBoxLayout(central_widget)  
        main_layout.setContentsMargins(0, 0, 0, 0)  
        
        # 创建工具栏  
        self.create_toolbar()  
        
        # 创建标签页  
        self.tabs = QTabWidget()  
        self.tabs.setTabPosition(QTabWidget.North)  
        self.tabs.setMovable(True)  
        main_layout.addWidget(self.tabs)  
        
        # 添加各个功能标签页  
        self.create_scheduler_tab()  
        self.create_file_monitor_tab()  
        self.create_web_automation_tab()  
        self.create_macro_tab()  
        self.create_api_tester_tab()  
        self.create_sync_tab()  
        self.create_system_monitor_tab()  
        self.create_log_tab()  
        
        # 创建状态栏  
        self.create_statusbar()  
        
        # 创建系统托盘  
        self.create_system_tray()  
        
    def create_toolbar(self):  
        """创建工具栏"""  
        toolbar = QToolBar()  
        toolbar.setMovable(False)  
        toolbar.setIconSize(QSize(24, 24))  
        self.addToolBar(toolbar)  
        
        # 添加工具按钮  
        start_action = QAction("▶️ 启动所有", self)  
        start_action.triggered.connect(self.start_all_services)  
        toolbar.addAction(start_action)  
        
        stop_action = QAction("⏸️ 暂停所有", self)  
        stop_action.triggered.connect(self.stop_all_services)  
        toolbar.addAction(stop_action)  
        
        toolbar.addSeparator()  
        
        save_action = QAction("💾 保存配置", self)  
        save_action.triggered.connect(self.save_config)  
        toolbar.addAction(save_action)  
        
        load_action = QAction("📂 加载配置", self)  
        load_action.triggered.connect(self.load_config)  
        toolbar.addAction(load_action)  
        
        toolbar.addSeparator()  
        
        export_action = QAction("📤 导出日志", self)  
        export_action.triggered.connect(self.export_logs)  
        toolbar.addAction(export_action)  
        
        clear_action = QAction("🗑️ 清空日志", self)  
        clear_action.triggered.connect(self.clear_logs)  
        toolbar.addAction(clear_action)  
        
        toolbar.addSeparator()  
        
        about_action = QAction("ℹ️ 关于", self)  
        about_action.triggered.connect(self.show_about)  
        toolbar.addAction(about_action)  
        
    def create_statusbar(self):  
        """创建状态栏"""  
        self.statusBar = QStatusBar()  
        self.setStatusBar(self.statusBar)  
        
        # 添加状态标签  
        self.status_label = QLabel("就绪")  
        self.statusBar.addWidget(self.status_label)  
        
        self.statusBar.addPermanentWidget(QLabel(" | "))  
        
        self.task_count_label = QLabel("任务: 0")  
        self.statusBar.addPermanentWidget(self.task_count_label)  
        
        self.statusBar.addPermanentWidget(QLabel(" | "))  
        
        self.monitor_count_label = QLabel("监控: 0")  
        self.statusBar.addPermanentWidget(self.monitor_count_label)  
        
        self.statusBar.addPermanentWidget(QLabel(" | "))  
        
        self.cpu_label = QLabel("CPU: 0%")  
        self.statusBar.addPermanentWidget(self.cpu_label)  
        
        self.statusBar.addPermanentWidget(QLabel(" | "))  
        
        self.memory_label = QLabel("内存: 0%")  
        self.statusBar.addPermanentWidget(self.memory_label)  
        
    def create_system_tray(self):  
        """创建系统托盘"""  
        self.tray_icon = QSystemTrayIcon(self)  
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))  
        
        # 托盘菜单  
        tray_menu = QMenu()  
        
        show_action = tray_menu.addAction("显示主窗口")  
        show_action.triggered.connect(self.show)  
        
        tray_menu.addSeparator()  
        
        quit_action = tray_menu.addAction("退出")  
        quit_action.triggered.connect(self.quit_application)  
        
        self.tray_icon.setContextMenu(tray_menu)  
        self.tray_icon.activated.connect(self.on_tray_activated)  
        self.tray_icon.show()  
        
    def create_scheduler_tab(self):  
        """创建定时任务标签页"""  
        widget = QWidget()  
        layout = QVBoxLayout(widget)  
        
        # 工具栏  
        toolbar = QHBoxLayout()  
        
        add_btn = QPushButton("➕ 添加任务")  
        add_btn.clicked.connect(self.add_scheduled_task)  
        toolbar.addWidget(add_btn)  
        
        edit_btn = QPushButton("✏️ 编辑")  
        edit_btn.clicked.connect(self.edit_scheduled_task)  
        toolbar.addWidget(edit_btn)  
        
        delete_btn = QPushButton("🗑️ 删除")  
        delete_btn.clicked.connect(self.delete_scheduled_task)  
        toolbar.addWidget(delete_btn)  
        
        toolbar.addStretch()  
        
        run_btn = QPushButton("▶️ 立即执行")  
        run_btn.clicked.connect(self.run_scheduled_task_now)  
        toolbar.addWidget(run_btn)  
        
        layout.addLayout(toolbar)  
        
        # 任务表格  
        self.task_table = QTableWidget()  
        self.task_table.setColumnCount(8)  
        self.task_table.setHorizontalHeaderLabels([  
            "ID", "任务名称", "间隔(秒)", "动作类型", "下次运行",   
            "状态", "运行次数", "最后运行"  
        ])  
        self.task_table.horizontalHeader().setStretchLastSection(True)  
        self.task_table.setSelectionBehavior(QTableWidget.SelectRows)  
        self.task_table.setEditTriggers(QTableWidget.NoEditTriggers)  
        self.task_table.doubleClicked.connect(self.toggle_scheduled_task)  
        layout.addWidget(self.task_table)  
        
        self.tabs.addTab(widget, "⏰ 定时任务")  
        
    def create_file_monitor_tab(self):  
        """创建文件监控标签页"""  
        widget = QWidget()  
        layout = QVBoxLayout(widget)  
        
        # 工具栏  
        toolbar = QHBoxLayout()  
        
        add_btn = QPushButton("➕ 添加监控")  
        add_btn.clicked.connect(self.add_file_monitor)  
        toolbar.addWidget(add_btn)  
        
        edit_btn = QPushButton("✏️ 编辑")  
        edit_btn.clicked.connect(self.edit_file_monitor)  
        toolbar.addWidget(edit_btn)  
        
        delete_btn = QPushButton("🗑️ 删除")  
        delete_btn.clicked.connect(self.delete_file_monitor)  
        toolbar.addWidget(delete_btn)  
        
        toolbar.addStretch()  
        
        refresh_btn = QPushButton("🔄 刷新")  
        refresh_btn.clicked.connect(self.update_monitor_table)  
        toolbar.addWidget(refresh_btn)  
        
        layout.addLayout(toolbar)  
        
        # 监控表格  
        self.monitor_table = QTableWidget()  
        self.monitor_table.setColumnCount(8)  
        self.monitor_table.setHorizontalHeaderLabels([  
            "ID", "监控名称", "监控路径", "文件模式", "动作",   
            "目标路径", "状态", "触发次数"  
        ])  
        self.monitor_table.horizontalHeader().setStretchLastSection(True)  
        self.monitor_table.setSelectionBehavior(QTableWidget.SelectRows)  
        self.monitor_table.setEditTriggers(QTableWidget.NoEditTriggers)  
        self.monitor_table.doubleClicked.connect(self.toggle_file_monitor)  
        layout.addWidget(self.monitor_table)  
        
        # 监控日志  
        log_group = QGroupBox("监控日志")  
        log_layout = QVBoxLayout(log_group)  
        
        self.monitor_log = QTextEdit()  
        self.monitor_log.setReadOnly(True)  
        self.monitor_log.setMaximumHeight(150)  
        log_layout.addWidget(self.monitor_log)  
        
        layout.addWidget(log_group)  
        
        self.tabs.addTab(widget, "📁 文件监控")  
        
    def create_web_automation_tab(self):  
        """创建网页自动化标签页"""  
        widget = QWidget()  
        layout = QHBoxLayout(widget)  
        
        # 左侧：脚本列表  
        left_widget = QWidget()  
        left_layout = QVBoxLayout(left_widget)  
        
        # 工具栏  
        toolbar = QHBoxLayout()  
        add_btn = QPushButton("➕ 新建")  
        add_btn.clicked.connect(self.add_web_script)  
        toolbar.addWidget(add_btn)  
        
        delete_btn = QPushButton("🗑️ 删除")  
        delete_btn.clicked.connect(self.delete_web_script)  
        toolbar.addWidget(delete_btn)  
        
        toolbar.addStretch()  
        left_layout.addLayout(toolbar)  
        
        self.web_script_list = QListWidget()  
        self.web_script_list.currentRowChanged.connect(self.on_web_script_selected)  
        left_layout.addWidget(self.web_script_list)  
        
        # 右侧：脚本详情和执行  
        right_widget = QWidget()  
        right_layout = QVBoxLayout(right_widget)  
        
        # 脚本信息  
        info_group = QGroupBox("脚本信息")  
        info_layout = QFormLayout(info_group)  
        
        self.web_name_label = QLabel("-")  
        info_layout.addRow("名称:", self.web_name_label)  
        
        self.web_url_label = QLabel("-")  
        info_layout.addRow("URL:", self.web_url_label)  
        
        self.web_actions_label = QLabel("-")  
        info_layout.addRow("动作数:", self.web_actions_label)  
        
        self.web_run_count_label = QLabel("-")  
        info_layout.addRow("运行次数:", self.web_run_count_label)  
        
        right_layout.addWidget(info_group)  
        
        # 执行控制  
        control_layout = QHBoxLayout()  
        
        run_btn = QPushButton("▶️ 执行脚本")  
        run_btn.clicked.connect(self.run_web_script)  
        control_layout.addWidget(run_btn)  
        
        edit_btn = QPushButton("✏️ 编辑")  
        edit_btn.clicked.connect(self.edit_web_script)  
        control_layout.addWidget(edit_btn)  
        
        control_layout.addStretch()  
        right_layout.addLayout(control_layout)  
        
        # 执行日志  
        log_group = QGroupBox("执行日志")  
        log_layout = QVBoxLayout(log_group)  
        
        self.web_log = QTextEdit()  
        self.web_log.setReadOnly(True)  
        log_layout.addWidget(self.web_log)  
        
        right_layout.addWidget(log_group)  
        
        # 添加到分割器  
        splitter = QSplitter(Qt.Horizontal)  
        splitter.addWidget(left_widget)  
        splitter.addWidget(right_widget)  
        splitter.setStretchFactor(0, 1)  
        splitter.setStretchFactor(1, 2)  
        
        layout.addWidget(splitter)  
        
        self.tabs.addTab(widget, "🌐 网页自动化")  
        
    def create_macro_tab(self):  
        """创建宏录制标签页"""  
        widget = QWidget()  
        layout = QVBoxLayout(widget)  
        
        # 录制控制  
        control_group = QGroupBox("录制控制")  
        control_layout = QHBoxLayout(control_group)  
        
        self.macro_record_btn = QPushButton("⏺️ 开始录制")  
        self.macro_record_btn.clicked.connect(self.start_macro_recording)  
        control_layout.addWidget(self.macro_record_btn)  
        
        self.macro_stop_btn = QPushButton("⏹️ 停止录制")  
        self.macro_stop_btn.setEnabled(False)  
        self.macro_stop_btn.clicked.connect(self.stop_macro_recording)  
        control_layout.addWidget(self.macro_stop_btn)  
        
        control_layout.addStretch()  
        
        self.macro_status_label = QLabel("就绪")  
        control_layout.addWidget(self.macro_status_label)  
        
        layout.addWidget(control_group)  
        
        # 模拟事件  
        event_group = QGroupBox("模拟事件（录制时）")  
        event_layout = QHBoxLayout(event_group)  
        
        events = [  
            ("🖱️ 左击", "click_left"),  
            ("🖱️ 右击", "click_right"),  
            ("⌨️ 键盘", "keyboard"),  
            ("↔️ 移动", "move"),  
            ("⏱️ 等待1秒", "wait_1s"),  
            ("⏱️ 等待5秒", "wait_5s"),  
        ]  
        
        self.macro_recording = False  
        self.macro_events = []  
        
        for text, event_type in events:  
            btn = QPushButton(text)  
            btn.clicked.connect(lambda checked, e=event_type: self.record_macro_event(e))  
            event_layout.addWidget(btn)  
        
        event_layout.addStretch()  
        layout.addWidget(event_group)  
        
        # 宏列表  
        list_group = QGroupBox("已保存的宏")  
        list_layout = QVBoxLayout(list_group)  
        
        # 工具栏  
        toolbar = QHBoxLayout()  
        
        play_btn = QPushButton("▶️ 播放")  
        play_btn.clicked.connect(self.play_macro)  
        toolbar.addWidget(play_btn)  
        
        delete_btn = QPushButton("🗑️ 删除")  
        delete_btn.clicked.connect(self.delete_macro)  
        toolbar.addWidget(delete_btn)  
        
        export_btn = QPushButton("📤 导出")  
        export_btn.clicked.connect(self.export_macro)  
        toolbar.addWidget(export_btn)  
        
        import_btn = QPushButton("📥 导入")  
        import_btn.clicked.connect(self.import_macro)  
        toolbar.addWidget(import_btn)  
        
        toolbar.addStretch()  
        list_layout.addLayout(toolbar)  
        
        self.macro_table = QTableWidget()  
        self.macro_table.setColumnCount(6)  
        self.macro_table.setHorizontalHeaderLabels([  
            "ID", "名称", "时长(秒)", "事件数", "创建时间", "播放次数"  
        ])  
        self.macro_table.horizontalHeader().setStretchLastSection(True)  
        self.macro_table.setSelectionBehavior(QTableWidget.SelectRows)  
        self.macro_table.setEditTriggers(QTableWidget.NoEditTriggers)  
        list_layout.addWidget(self.macro_table)  
        
        layout.addWidget(list_group)  
        
        # 播放日志  
        log_group = QGroupBox("播放日志")  
        log_layout = QVBoxLayout(log_group)  
        
        self.macro_log = QTextEdit()  
        self.macro_log.setReadOnly(True)  
        self.macro_log.setMaximumHeight(150)  
        log_layout.addWidget(self.macro_log)  
        
        layout.addWidget(log_group)  
        
        self.tabs.addTab(widget, "🎮 宏录制")  
        
    def create_api_tester_tab(self):  
        """创建API测试标签页"""  
        widget = QWidget()  
        layout = QHBoxLayout(widget)  
        
        # 左侧：测试列表  
        left_widget = QWidget()  
        left_layout = QVBoxLayout(left_widget)  
        
        # 工具栏  
        toolbar = QHBoxLayout()  
        
        add_btn = QPushButton("➕ 新建")  
        add_btn.clicked.connect(self.add_api_test)  
        toolbar.addWidget(add_btn)  
        
        delete_btn = QPushButton("🗑️ 删除")  
        delete_btn.clicked.connect(self.delete_api_test)  
        toolbar.addWidget(delete_btn)  
        
        run_all_btn = QPushButton("▶️ 全部运行")  
        run_all_btn.clicked.connect(self.run_all_api_tests)  
        toolbar.addWidget(run_all_btn)  
        
        toolbar.addStretch()  
        left_layout.addLayout(toolbar)  
        
        self.api_table = QTableWidget()  
        self.api_table.setColumnCount(6)  
        self.api_table.setHorizontalHeaderLabels([  
            "ID", "名称", "方法", "URL", "测试次数", "成功率"  
        ])  
        self.api_table.horizontalHeader().setStretchLastSection(True)  
        self.api_table.setSelectionBehavior(QTableWidget.SelectRows)  
        self.api_table.setEditTriggers(QTableWidget.NoEditTriggers)  
        self.api_table.currentCellChanged.connect(self.on_api_test_selected)  
        left_layout.addWidget(self.api_table)  
        
        # 右侧：测试详情和结果  
        right_widget = QWidget()  
        right_layout = QVBoxLayout(right_widget)  
        
        # 测试信息  
        info_group = QGroupBox("测试信息")  
        info_layout = QFormLayout(info_group)  
        
        self.api_name_label = QLabel("-")  
        info_layout.addRow("名称:", self.api_name_label)  
        
        self.api_method_label = QLabel("-")  
        info_layout.addRow("方法:", self.api_method_label)  
        
        self.api_url_label = QLabel("-")  
        self.api_url_label.setWordWrap(True)  
        info_layout.addRow("URL:", self.api_url_label)  
        
        self.api_status_label = QLabel("-")  
        info_layout.addRow("上次状态:", self.api_status_label)  
        
        right_layout.addWidget(info_group)  
        
        # 执行控制  
        control_layout = QHBoxLayout()  
        
        run_btn = QPushButton("▶️ 运行测试")  
        run_btn.clicked.connect(self.run_api_test)  
        control_layout.addWidget(run_btn)  
        
        edit_btn = QPushButton("✏️ 编辑")  
        edit_btn.clicked.connect(self.edit_api_test)  
        control_layout.addWidget(edit_btn)  
        
        control_layout.addStretch()  
        right_layout.addLayout(control_layout)  
        
        # 测试结果  
        result_group = QGroupBox("测试结果")  
        result_layout = QVBoxLayout(result_group)  
        
        self.api_result = QTextEdit()  
        self.api_result.setReadOnly(True)  
        result_layout.addWidget(self.api_result)  
        
        right_layout.addWidget(result_group)  
        
        # 添加到分割器  
        splitter = QSplitter(Qt.Horizontal)  
        splitter.addWidget(left_widget)  
        splitter.addWidget(right_widget)  
        splitter.setStretchFactor(0, 1)  
        splitter.setStretchFactor(1, 2)  
        
        layout.addWidget(splitter)  
        
        self.tabs.addTab(widget, "🔌 API测试")  
        
    def create_sync_tab(self):  
        """创建数据同步标签页"""  
        widget = QWidget()  
        layout = QVBoxLayout(widget)  
        
        # 工具栏  
        toolbar = QHBoxLayout()  
        
        add_btn = QPushButton("➕ 添加任务")  
        add_btn.clicked.connect(self.add_sync_task)  
        toolbar.addWidget(add_btn)  
        
        edit_btn = QPushButton("✏️ 编辑")  
        edit_btn.clicked.connect(self.edit_sync_task)  
        toolbar.addWidget(edit_btn)  
        
        delete_btn = QPushButton("🗑️ 删除")  
        delete_btn.clicked.connect(self.delete_sync_task)  
        toolbar.addWidget(delete_btn)  
        
        toolbar.addStretch()  
        
        sync_btn = QPushButton("▶️ 执行同步")  
        sync_btn.clicked.connect(self.execute_sync_task)  
        toolbar.addWidget(sync_btn)  
        
        layout.addLayout(toolbar)  
        
        # 同步任务表格  
        self.sync_table = QTableWidget()  
        self.sync_table.setColumnCount(8)  
        self.sync_table.setHorizontalHeaderLabels([  
            "ID", "任务名称", "源路径", "目标路径", "模式",   
            "最后同步", "同步次数", "文件数"  
        ])  
        self.sync_table.horizontalHeader().setStretchLastSection(True)  
        self.sync_table.setSelectionBehavior(QTableWidget.SelectRows)  
        self.sync_table.setEditTriggers(QTableWidget.NoEditTriggers)  
        layout.addWidget(self.sync_table)  
        
        # 同步日志  
        log_group = QGroupBox("同步日志")  
        log_layout = QVBoxLayout(log_group)  
        
        self.sync_log = QTextEdit()  
        self.sync_log.setReadOnly(True)  
        self.sync_log.setMaximumHeight(200)  
        log_layout.addWidget(self.sync_log)  
        
        # 进度条  
        self.sync_progress = QProgressBar()  
        self.sync_progress.setVisible(False)  
        log_layout.addWidget(self.sync_progress)  
        
        layout.addWidget(log_group)  
        
        self.tabs.addTab(widget, "🔄 数据同步")  
        
    def create_system_monitor_tab(self):  
        """创建系统监控标签页"""  
        widget = QWidget()  
        layout = QVBoxLayout(widget)  
        
        # 顶部信息卡片  
        cards_layout = QHBoxLayout()  
        
        # CPU卡片  
        cpu_card = QGroupBox("CPU使用率")  
        cpu_layout = QVBoxLayout(cpu_card)  
        self.cpu_percent_label = QLabel("0%")  
        self.cpu_percent_label.setFont(QFont("Arial", 32, QFont.Bold))  
        self.cpu_percent_label.setAlignment(Qt.AlignCenter)  
        cpu_layout.addWidget(self.cpu_percent_label)  
        self.cpu_cores_label = QLabel(f"核心数: {psutil.cpu_count()}")  
        self.cpu_cores_label.setAlignment(Qt.AlignCenter)  
        cpu_layout.addWidget(self.cpu_cores_label)  
        cards_layout.addWidget(cpu_card)  
        
        # 内存卡片  
        memory_card = QGroupBox("内存使用")  
        memory_layout = QVBoxLayout(memory_card)  
        self.memory_percent_label = QLabel("0%")  
        self.memory_percent_label.setFont(QFont("Arial", 32, QFont.Bold))  
        self.memory_percent_label.setAlignment(Qt.AlignCenter)  
        memory_layout.addWidget(self.memory_percent_label)  
        self.memory_info_label = QLabel("0 GB / 0 GB")  
        self.memory_info_label.setAlignment(Qt.AlignCenter)  
        memory_layout.addWidget(self.memory_info_label)  
        cards_layout.addWidget(memory_card)  
        
        # 磁盘卡片  
        disk_card = QGroupBox("磁盘使用")  
        disk_layout = QVBoxLayout(disk_card)  
        self.disk_percent_label = QLabel("0%")  
        self.disk_percent_label.setFont(QFont("Arial", 32, QFont.Bold))  
        self.disk_percent_label.setAlignment(Qt.AlignCenter)  
        disk_layout.addWidget(self.disk_percent_label)  
        self.disk_info_label = QLabel("0 GB / 0 GB")  
        self.disk_info_label.setAlignment(Qt.AlignCenter)  
        disk_layout.addWidget(self.disk_info_label)  
        cards_layout.addWidget(disk_card)  
        
        # 网络卡片  
        network_card = QGroupBox("网络流量")  
        network_layout = QVBoxLayout(network_card)  
        self.network_sent_label = QLabel("发送: 0 MB")  
        self.network_sent_label.setAlignment(Qt.AlignCenter)  
        network_layout.addWidget(self.network_sent_label)  
        self.network_recv_label = QLabel("接收: 0 MB")  
        self.network_recv_label.setAlignment(Qt.AlignCenter)  
        network_layout.addWidget(self.network_recv_label)  
        cards_layout.addWidget(network_card)  
        
        layout.addLayout(cards_layout)  
        
        # 系统信息  
        info_group = QGroupBox("系统信息")  
        info_layout = QFormLayout(info_group)  
        
        system_info = {  
            "操作系统": f"{platform.system()} {platform.release()}",  
            "主机名": platform.node(),  
            "处理器": platform.processor(),  
            "Python版本": platform.python_version(),  
            "进程数": str(len(psutil.pids()))  
        }  
        
        for key, value in system_info.items():  
            info_layout.addRow(f"{key}:", QLabel(value))  
        
        self.process_count_label = QLabel(str(len(psutil.pids())))  
        info_layout.addRow("当前进程数:", self.process_count_label)  
        
        layout.addWidget(info_group)  
        
        # 进程列表  
        process_group = QGroupBox("前10个进程（按CPU使用率）")  
        process_layout = QVBoxLayout(process_group)  
        
        self.process_table = QTableWidget()  
        self.process_table.setColumnCount(4)  
        self.process_table.setHorizontalHeaderLabels(["PID", "名称", "CPU%", "内存%"])  
        self.process_table.horizontalHeader().setStretchLastSection(True)  
        self.process_table.setSelectionBehavior(QTableWidget.SelectRows)  
        self.process_table.setEditTriggers(QTableWidget.NoEditTriggers)  
        process_layout.addWidget(self.process_table)  
        
        layout.addWidget(process_group)  
        
        self.tabs.addTab(widget, "📊 系统监控")  
        
    def create_log_tab(self):  
        """创建日志标签页"""  
        widget = QWidget()  
        layout = QVBoxLayout(widget)  
        
        # 工具栏  
        toolbar = QHBoxLayout()  
        
        # 日志级别过滤  
        toolbar.addWidget(QLabel("日志级别:"))  
        self.log_level_combo = QComboBox()  
        self.log_level_combo.addItems(["全部", "信息", "警告", "错误"])  
        self.log_level_combo.currentTextChanged.connect(self.filter_logs)  
        toolbar.addWidget(self.log_level_combo)  
        
        # 搜索  
        toolbar.addWidget(QLabel("搜索:"))  
        self.log_search_input = QLineEdit()  
        self.log_search_input.setPlaceholderText("输入关键词...")  
        self.log_search_input.textChanged.connect(self.filter_logs)  
        toolbar.addWidget(self.log_search_input)  
        
        toolbar.addStretch()  
        
        # 操作按钮  
        clear_btn = QPushButton("🗑️ 清空")  
        clear_btn.clicked.connect(self.clear_main_log)  
        toolbar.addWidget(clear_btn)  
        
        export_btn = QPushButton("📤 导出")  
        export_btn.clicked.connect(self.export_main_log)  
        toolbar.addWidget(export_btn)  
        
        auto_scroll_checkbox = QCheckBox("自动滚动")  
        auto_scroll_checkbox.setChecked(True)  
        self.log_auto_scroll = True  
        auto_scroll_checkbox.stateChanged.connect(  
            lambda state: setattr(self, 'log_auto_scroll', state == Qt.Checked)  
        )  
        toolbar.addWidget(auto_scroll_checkbox)  
        
        layout.addLayout(toolbar)  
        
        # 日志显示  
        self.main_log = QTextEdit()  
        self.main_log.setReadOnly(True)  
        self.main_log.setFont(QFont("Courier", 9))  
        layout.addWidget(self.main_log)  
        
        # 统计信息  
        stats_layout = QHBoxLayout()  
        self.log_count_label = QLabel("总计: 0 条")  
        stats_layout.addWidget(self.log_count_label)  
        stats_layout.addStretch()  
        layout.addLayout(stats_layout)  
        
        self.tabs.addTab(widget, "📝 日志")  
        
    # ========================================================================  
    # 定时任务功能实现  
    # ========================================================================  
    
    def add_scheduled_task(self):  
        """添加定时任务"""  
        dialog = ScheduledTaskDialog(self)  
        if dialog.exec_() == QDialog.Accepted:  
            task_data = dialog.get_task_data()  
            task = ScheduledTask(  
                id=self.generate_id(),  
                name=task_data['name'],  
                interval=task_data['interval'],  
                action_type=task_data['action_type'],  
                action_param=task_data['action_param'],  
                enabled=True  
            )  
            self.scheduler_thread.add_task(task)  
            self.update_task_table()  
            self.log_message(f"添加定时任务: {task.name}", "info")  
    
    def edit_scheduled_task(self):  
        """编辑定时任务"""  
        current_row = self.task_table.currentRow()  
        if current_row < 0:  
            QMessageBox.warning(self, "警告", "请先选择一个任务")  
            return  
        
        task_id = self.task_table.item(current_row, 0).text()  
        tasks = self.scheduler_thread.get_tasks()  
        task = next((t for t in tasks if t.id == task_id), None)  
        
        if task:  
            dialog = ScheduledTaskDialog(self, task)  
            if dialog.exec_() == QDialog.Accepted:  
                task_data = dialog.get_task_data()  
                task.name = task_data['name']  
                task.interval = task_data['interval']  
                task.action_type = task_data['action_type']  
                task.action_param = task_data['action_param']  
                self.scheduler_thread.update_task(task)  
                self.update_task_table()  
                self.log_message(f"编辑任务: {task.name}", "info")  
    
    def delete_scheduled_task(self):  
        """删除定时任务"""  
        current_row = self.task_table.currentRow()  
        if current_row < 0:  
            QMessageBox.warning(self, "警告", "请先选择一个任务")  
            return  
        
        reply = QMessageBox.question(  
            self, "确认删除", "确定要删除选中的任务吗？",  
            QMessageBox.Yes | QMessageBox.No  
        )  
        
        if reply == QMessageBox.Yes:  
            task_id = self.task_table.item(current_row, 0).text()  
            task_name = self.task_table.item(current_row, 1).text()  
            self.scheduler_thread.remove_task(task_id)  
            self.update_task_table()  
            self.log_message(f"删除任务: {task_name}", "info")  
    
    def toggle_scheduled_task(self):  
        """切换任务启用状态"""  
        current_row = self.task_table.currentRow()  
        if current_row >= 0:  
            task_id = self.task_table.item(current_row, 0).text()  
            self.scheduler_thread.toggle_task(task_id)  
            self.update_task_table()  
    
    def run_scheduled_task_now(self):  
        """立即执行任务"""  
        current_row = self.task_table.currentRow()  
        if current_row < 0:  
            QMessageBox.warning(self, "警告", "请先选择一个任务")  
            return  
        
        task_id = self.task_table.item(current_row, 0).text()  
        tasks = self.scheduler_thread.get_tasks()  
        task = next((t for t in tasks if t.id == task_id), None)  
        
        if task:  
            # 临时设置下次运行时间为现在  
            task.next_run = time.time()  
            self.log_message(f"手动触发任务: {task.name}", "info")  
    
    def update_task_table(self):  
        """更新任务表格"""  
        tasks = self.scheduler_thread.get_tasks()  
        self.task_table.setRowCount(len(tasks))  
        
        for i, task in enumerate(tasks):  
            next_run = datetime.datetime.fromtimestamp(task.next_run).strftime("%H:%M:%S")  
            status = "✅ 启用" if task.enabled else "⏸️ 暂停"  
            last_run = datetime.datetime.fromtimestamp(task.last_run).strftime("%H:%M:%S") if task.last_run > 0 else "-"  
            
            self.task_table.setItem(i, 0, QTableWidgetItem(task.id))  
            self.task_table.setItem(i, 1, QTableWidgetItem(task.name))  
            self.task_table.setItem(i, 2, QTableWidgetItem(str(task.interval)))  
            self.task_table.setItem(i, 3, QTableWidgetItem(task.action_type))  
            self.task_table.setItem(i, 4, QTableWidgetItem(next_run))  
            self.task_table.setItem(i, 5, QTableWidgetItem(status))  
            self.task_table.setItem(i, 6, QTableWidgetItem(str(task.run_count)))  
            self.task_table.setItem(i, 7, QTableWidgetItem(last_run))  
        
        # 更新状态栏  
        enabled_count = sum(1 for t in tasks if t.enabled)  
        self.task_count_label.setText(f"任务: {enabled_count}/{len(tasks)}")  
    
    def on_task_executed(self, task_id: str, success: bool, message: str):  
        """任务执行回调"""  
        tasks = self.scheduler_thread.get_tasks()  
        task = next((t for t in tasks if t.id == task_id), None)  
        
        if task:  
            level = "info" if success else "error"  
            self.log_message(f"[{task.name}] {message}", level)  
            self.show_notification("任务执行", message)  
    
    # ========================================================================  
    # 文件监控功能实现  
    # ========================================================================  
    
    def add_file_monitor(self):  
        """添加文件监控"""  
        dialog = FileMonitorDialog(self)  
        if dialog.exec_() == QDialog.Accepted:  
            monitor_data = dialog.get_monitor_data()  
            monitor = FileMonitorTask(  
                id=self.generate_id(),  
                name=monitor_data['name'],  
                path=monitor_data['path'],  
                pattern=monitor_data['pattern'],  
                action=monitor_data['action'],  
                target=monitor_data['target'],  
                recursive=monitor_data['recursive'],  
                ignore_hidden=monitor_data['ignore_hidden'],  
                enabled=True  
            )  
            self.file_monitor_thread.add_monitor(monitor)  
            self.update_monitor_table()  
            self.log_message(f"添加文件监控: {monitor.name}", "info")  
    
    def edit_file_monitor(self):  
        """编辑文件监控"""  
        current_row = self.monitor_table.currentRow()  
        if current_row < 0:  
            QMessageBox.warning(self, "警告", "请先选择一个监控")  
            return  
        
        monitor_id = self.monitor_table.item(current_row, 0).text()  
        monitors = self.file_monitor_thread.get_monitors()  
        monitor = next((m for m in monitors if m.id == monitor_id), None)  
        
        if monitor:  
            dialog = FileMonitorDialog(self, monitor)  
            if dialog.exec_() == QDialog.Accepted:  
                monitor_data = dialog.get_monitor_data()  
                monitor.name = monitor_data['name']  
                monitor.path = monitor_data['path']  
                monitor.pattern = monitor_data['pattern']  
                monitor.action = monitor_data['action']  
                monitor.target = monitor_data['target']  
                monitor.recursive = monitor_data['recursive']  
                monitor.ignore_hidden = monitor_data['ignore_hidden']  
                self.file_monitor_thread.update_monitor(monitor)  
                self.update_monitor_table()  
                self.log_message(f"编辑监控: {monitor.name}", "info")  
    
    def delete_file_monitor(self):  
        """删除文件监控"""  
        current_row = self.monitor_table.currentRow()  
        if current_row < 0:  
            QMessageBox.warning(self, "警告", "请先选择一个监控")  
            return  
        
        reply = QMessageBox.question(  
            self, "确认删除", "确定要删除选中的监控吗？",  
            QMessageBox.Yes | QMessageBox.No  
        )  
        
        if reply == QMessageBox.Yes:  
            monitor_id = self.monitor_table.item(current_row, 0).text()  
            monitor_name = self.monitor_table.item(current_row, 1).text()  
            self.file_monitor_thread.remove_monitor(monitor_id)  
            self.update_monitor_table()  
            self.log_message(f"删除监控: {monitor_name}", "info")  
    
    def toggle_file_monitor(self):  
        """切换监控启用状态"""  
        current_row = self.monitor_table.currentRow()  
        if current_row >= 0:  
            monitor_id = self.monitor_table.item(current_row, 0).text()  
            self.file_monitor_thread.toggle_monitor(monitor_id)  
            self.update_monitor_table()  
    
    def update_monitor_table(self):  
        """更新监控表格"""  
        monitors = self.file_monitor_thread.get_monitors()  
        self.monitor_table.setRowCount(len(monitors))  
        
        for i, monitor in enumerate(monitors):  
            status = "✅ 监控中" if monitor.enabled else "⏸️ 暂停"  
            
            self.monitor_table.setItem(i, 0, QTableWidgetItem(monitor.id))  
            self.monitor_table.setItem(i, 1, QTableWidgetItem(monitor.name))  
            self.monitor_table.setItem(i, 2, QTableWidgetItem(monitor.path[:40]))  
            self.monitor_table.setItem(i, 3, QTableWidgetItem(monitor.pattern))  
            self.monitor_table.setItem(i, 4, QTableWidgetItem(monitor.action))  
            self.monitor_table.setItem(i, 5, QTableWidgetItem(monitor.target[:40]))  
            self.monitor_table.setItem(i, 6, QTableWidgetItem(status))  
            self.monitor_table.setItem(i, 7, QTableWidgetItem(str(monitor.trigger_count)))  
        
        # 更新状态栏  
        enabled_count = sum(1 for m in monitors if m.enabled)  
        self.monitor_count_label.setText(f"监控: {enabled_count}/{len(monitors)}")  
    
    def on_file_changed(self, monitor_id: str, file_path: str, action: str):  
        """文件变化回调"""  
        monitors = self.file_monitor_thread.get_monitors()  
        monitor = next((m for m in monitors if m.id == monitor_id), None)  
        
        if monitor:  
            message = f"[{monitor.name}] {file_path} - {action}"  
            self.log_to_monitor(message)  
            self.log_message(message, "info")  
            self.update_monitor_table()  
    
    def log_to_monitor(self, message: str):  
        """记录到监控日志"""  
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")  
        self.monitor_log.append(f"[{timestamp}] {message}")  
        
        # 限制日志行数  
        if self.monitor_log.document().lineCount() > 500:  
            cursor = self.monitor_log.textCursor()  
            cursor.movePosition(QTextCursor.Start)  
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 100)  
            cursor.removeSelectedText()  
    
    # ========================================================================  
    # 网页自动化功能实现  
    # ========================================================================  
    
    def add_web_script(self):  
        """添加网页脚本"""  
        dialog = WebScriptDialog(self)  
        if dialog.exec_() == QDialog.Accepted:  
            script_data = dialog.get_script_data()  
            # 这里简化存储，实际应该用数据结构  
            self.web_script_list.addItem(f"{script_data['name']} - {script_data['url']}")  
            self.log_message(f"添加网页脚本: {script_data['name']}", "info")  
    
    def edit_web_script(self):  
        """编辑网页脚本"""  
        current_row = self.web_script_list.currentRow()  
        if current_row < 0:  
            QMessageBox.warning(self, "警告", "请先选择一个脚本")  
            return  
        
        # 实际应该加载完整数据进行编辑  
        QMessageBox.information(self, "提示", "编辑功能待实现")  
    
    def delete_web_script(self):  
        """删除网页脚本"""  
        current_row = self.web_script_list.currentRow()  
        if current_row < 0:  
            QMessageBox.warning(self, "警告", "请先选择一个脚本")  
            return  
        
        reply = QMessageBox.question(  
            self, "确认删除", "确定要删除选中的脚本吗？",  
            QMessageBox.Yes | QMessageBox.No  
        )  
        
        if reply == QMessageBox.Yes:  
            self.web_script_list.takeItem(current_row)  
            self.log_message("删除网页脚本", "info")  
    
    def run_web_script(self):  
        """运行网页脚本"""  
        current_row = self.web_script_list.currentRow()  
        if current_row < 0:  
            QMessageBox.warning(self, "警告", "请先选择一个脚本")  
            return  
        
        self.web_log.clear()  
        self.web_log.append("开始执行脚本...")  
        self.web_log.append("正在打开浏览器...")  
        
        # 这里应该实际执行脚本  
        QTimer.singleShot(2000, lambda: self.web_log.append("脚本执行完成！"))  
        self.log_message("执行网页脚本", "info")  
    
    def on_web_script_selected(self, index):  
        """网页脚本选择事件"""  
        if index >= 0:  
            # 更新脚本信息显示  
            self.web_name_label.setText("示例脚本")  
            self.web_url_label.setText("https://example.com")  
            self.web_actions_label.setText("5")  
            self.web_run_count_label.setText("0")  
    
    # ========================================================================  
    # 宏录制功能实现  
    # ========================================================================  
    
    def start_macro_recording(self):  
        """开始录制宏"""  
        self.macro_recording = True  
        self.macro_events = []  
        self.macro_start_time = time.time()  
        
        self.macro_record_btn.setEnabled(False)  
        self.macro_stop_btn.setEnabled(True)  
        self.macro_status_label.setText("⏺️ 录制中...")  
        self.macro_status_label.setStyleSheet("color: red; font-weight: bold;")  
        
        self.log_message("开始录制宏", "info")  
    
    def stop_macro_recording(self):  
        """停止录制宏"""  
        if not self.macro_recording:  
            return  
        
        self.macro_recording = False  
        self.macro_record_btn.setEnabled(True)  
        self.macro_stop_btn.setEnabled(False)  
        self.macro_status_label.setText("就绪")  
        self.macro_status_label.setStyleSheet("")  
        
        # 请求保存  
        name, ok = self.get_input_dialog("保存宏", "请输入宏名称:")  
        if ok and name:  
            macro = MacroRecord(  
                id=self.generate_id(),  
                name=name,  
                events=self.macro_events.copy(),  
                duration=time.time() - self.macro_start_time,  
                created=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
            )  
            self.save_macro(macro)  
            self.update_macro_table()  
            self.log_message(f"保存宏: {name}", "info")  
    
    def record_macro_event(self, event_type: str):  
        """记录宏事件"""  
        if not self.macro_recording:  
            QMessageBox.warning(self, "警告", "请先开始录制")  
            return  
        
        event = {  
            'type': event_type,  
            'time': time.time() - self.macro_start_time,  
            'data': f"Event: {event_type}"  
        }  
        self.macro_events.append(event)  
        
        # 显示反馈  
        self.macro_status_label.setText(f"⏺️ 录制中... ({len(self.macro_events)} 事件)")  
    
    def play_macro(self):  
        """播放宏"""  
        current_row = self.macro_table.currentRow()  
        if current_row < 0:  
            QMessageBox.warning(self, "警告", "请先选择一个宏")  
            return  
        
        macro_id = self.macro_table.item(current_row, 0).text()  
        macro = self.load_macro_by_id(macro_id)  
        
        if macro:  
            self.macro_log.clear()  
            self.macro_log.append(f"开始播放宏: {macro.name}")  
            self.macro_log.append(f"总事件数: {len(macro.events)}")  
            
            # 模拟播放  
            for i, event in enumerate(macro.events, 1):  
                QTimer.singleShot(  
                    int(event['time'] * 1000),  
                    lambda idx=i, evt=event: self.macro_log.append(  
                        f"[{idx}/{len(macro.events)}] {evt['type']}: {evt['data']}"  
                    )  
                )  
            
            # 更新播放次数  
            macro.play_count += 1  
            self.save_macro(macro)  
            
            QTimer.singleShot(  
                int(macro.duration * 1000) + 500,  
                lambda: self.macro_log.append("✅ 宏播放完成！")  
            )  
            
            self.log_message(f"播放宏: {macro.name}", "info")  
    
    def delete_macro(self):  
        """删除宏"""  
        current_row = self.macro_table.currentRow()  
        if current_row < 0:  
            QMessageBox.warning(self, "警告", "请先选择一个宏")  
            return  
        
        reply = QMessageBox.question(  
            self, "确认删除", "确定要删除选中的宏吗？",  
            QMessageBox.Yes | QMessageBox.No  
        )  
        
        if reply == QMessageBox.Yes:  
            macro_id = self.macro_table.item(current_row, 0).text()  
            self.delete_macro_by_id(macro_id)  
            self.update_macro_table()  
            self.log_message("删除宏", "info")  
    
    def export_macro(self):  
        """导出宏"""  
        current_row = self.macro_table.currentRow()  
        if current_row < 0:  
            QMessageBox.warning(self, "警告", "请先选择一个宏")  
            return  
        
        file_path, _ = QFileDialog.getSaveFileName(  
            self, "导出宏", "", "JSON文件 (*.json)"  
        )  
        
        if file_path:  
            macro_id = self.macro_table.item(current_row, 0).text()  
            macro = self.load_macro_by_id(macro_id)  
            
            if macro:  
                try:  
                    with open(file_path, 'w', encoding='utf-8') as f:  
                        json.dump(asdict(macro), f, indent=2, ensure_ascii=False)  
                    QMessageBox.information(self, "成功", "宏已导出")  
                    self.log_message(f"导出宏到: {file_path}", "info")  
                except Exception as e:  
                    QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")  
    
    def import_macro(self):  
        """导入宏"""  
        file_path, _ = QFileDialog.getOpenFileName(  
            self, "导入宏", "", "JSON文件 (*.json)"  
        )  
        
        if file_path:  
            try:  
                with open(file_path, 'r', encoding='utf-8') as f:  
                    data = json.load(f)  
                macro = MacroRecord(**data)  
                macro.id = self.generate_id()  # 生成新ID  
                self.save_macro(macro)  
                self.update_macro_table()  
                QMessageBox.information(self, "成功", "宏已导入")  
                self.log_message(f"导入宏: {macro.name}", "info")  
            except Exception as e:  
                QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")  
    
    def update_macro_table(self):  
        """更新宏表格"""  
        macros = self.load_all_macros()  
        self.macro_table.setRowCount(len(macros))  
        
        for i, macro in enumerate(macros):  
            self.macro_table.setItem(i, 0, QTableWidgetItem(macro.id))  
            self.macro_table.setItem(i, 1, QTableWidgetItem(macro.name))  
            self.macro_table.setItem(i, 2, QTableWidgetItem(f"{macro.duration:.2f}"))  
            self.macro_table.setItem(i, 3, QTableWidgetItem(str(len(macro.events))))  
            self.macro_table.setItem(i, 4, QTableWidgetItem(macro.created))  
            self.macro_table.setItem(i, 5, QTableWidgetItem(str(macro.play_count)))  
    
    # ========================================================================  
    # API测试功能实现  
    # ========================================================================  
    
    def add_api_test(self):  
        """添加API测试"""  
        dialog = APITestDialog(self)  
        if dialog.exec_() == QDialog.Accepted:  
            test_data = dialog.get_test_data()  
            test = APITest(  
                id=self.generate_id(),  
                name=test_data['name'],  
                method=test_data['method'],  
                url=test_data['url'],  
                headers=test_data['headers'],  
                body=test_data['body'],  
                timeout=test_data['timeout'],  
                expected_status=test_data['expected_status']  
            )  
            self.save_api_test(test)  
            self.update_api_test_table()  
            self.log_message(f"添加API测试: {test.name}", "info")  
    
    def edit_api_test(self):  
        """编辑API测试"""  
        current_row = self.api_table.currentRow()  
        if current_row < 0:  
            QMessageBox.warning(self, "警告", "请先选择一个测试")  
            return  
        
        test_id = self.api_table.item(current_row, 0).text()  
        test = self.load_api_test_by_id(test_id)  
        
        if test:  
            dialog = APITestDialog(self, test)  
            if dialog.exec_() == QDialog.Accepted:  
                test_data = dialog.get_test_data()  
                test.name = test_data['name']  
                test.method = test_data['method']  
                test.url = test_data['url']  
                test.headers = test_data['headers']  
                test.body = test_data['body']  
                test.timeout = test_data['timeout']  
                test.expected_status = test_data['expected_status']  
                self.save_api_test(test)  
                self.update_api_test_table()  
                self.log_message(f"编辑API测试: {test.name}", "info")  
    
    def delete_api_test(self):  
        """删除API测试"""  
        current_row = self.api_table.currentRow()  
        if current_row < 0:  
            QMessageBox.warning(self, "警告", "请先选择一个测试")  
            return  
        
        reply = QMessageBox.question(  
            self, "确认删除", "确定要删除选中的测试吗？",  
            QMessageBox.Yes | QMessageBox.No  
        )  
        
        if reply == QMessageBox.Yes:  
            test_id = self.api_table.item(current_row, 0).text()  
            self.delete_api_test_by_id(test_id)  
            self.update_api_test_table()  
            self.log_message("删除API测试", "info")  
    
    def run_api_test(self):  
        """运行API测试"""  
        current_row = self.api_table.currentRow()  
        if current_row < 0:  
            QMessageBox.warning(self, "警告", "请先选择一个测试")  
            return  
        
        test_id = self.api_table.item(current_row, 0).text()  
        test = self.load_api_test_by_id(test_id)  
        
        if test:  
            self.api_result.clear()  
            self.api_result.append("正在执行API测试...\n")  
            self.api_result.append("=" * 60)  
            
            # 在新线程中执行  
            thread = threading.Thread(target=self._execute_api_test, args=(test,))  
            thread.daemon = True  
            thread.start()  
    
    def _execute_api_test(self, test: APITest):  
        """执行API测试（后台线程）"""  
        try:  
            start_time = time.time()  
            
            # 准备请求  
            headers = test.headers.copy()  
            data = test.body.encode('utf-8') if test.body else None  
            
            req = urllib.request.Request(  
                test.url,  
                data=data,  
                headers=headers,  
                method=test.method  
            )  
            
            # 发送请求  
            with urllib.request.urlopen(req, timeout=test.timeout) as response:  
                response_time = time.time() - start_time  
                status_code = response.getcode()  
                response_data = response.read().decode('utf-8')  
                
                # 更新UI（需要在主线程）  
                result_text = f"\n✅ 请求成功\n"  
                result_text += f"状态码: {status_code}\n"  
                result_text += f"响应时间: {response_time * 1000:.2f} ms\n"  
                result_text += f"\n响应内容:\n{response_data[:1000]}\n"  
                
                # 更新测试记录  
                test.test_count += 1  
                if status_code == test.expected_status:  
                    test.success_count += 1  
                
                test.last_result = {  
                    'success': True,  
                    'status_code': status_code,  
                    'response_time': response_time,  
                    'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
                }  
                
                self.save_api_test(test)  
                
                # 使用信号更新UI  
                QTimer.singleShot(0, lambda: self.api_result.append(result_text))  
                QTimer.singleShot(0, lambda: self.update_api_test_table())  
                QTimer.singleShot(0, lambda: self.log_message(f"API测试成功: {test.name}", "info"))  
                
        except urllib.error.HTTPError as e:  
            error_text = f"\n❌ HTTP错误\n"  
            error_text += f"状态码: {e.code}\n"  
            error_text += f"错误信息: {str(e)}\n"  
            
            test.test_count += 1  
            test.last_result = {  
                'success': False,  
                'status_code': e.code,  
                'error': str(e),  
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
            }  
            
            self.save_api_test(test)  
            
            QTimer.singleShot(0, lambda: self.api_result.append(error_text))  
            QTimer.singleShot(0, lambda: self.update_api_test_table())  
            QTimer.singleShot(0, lambda: self.log_message(f"API测试失败: {test.name}", "error"))  
            
        except Exception as e:  
            error_text = f"\n❌ 请求失败\n"  
            error_text += f"错误: {str(e)}\n"  
            
            test.test_count += 1  
            test.last_result = {  
                'success': False,  
                'error': str(e),  
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
            }  
            
            self.save_api_test(test)  
            
            QTimer.singleShot(0, lambda: self.api_result.append(error_text))  
            QTimer.singleShot(0, lambda: self.update_api_test_table())  
            QTimer.singleShot(0, lambda: self.log_message(f"API测试异常: {test.name}", "error"))  
    
    def run_all_api_tests(self):  
        """运行所有API测试"""  
        tests = self.load_all_api_tests()  
        if not tests:  
            QMessageBox.information(self, "提示", "没有可运行的测试")  
            return  
        
        reply = QMessageBox.question(  
            self, "确认", f"确定要运行全部 {len(tests)} 个测试吗？",  
            QMessageBox.Yes | QMessageBox.No  
        )  
        
        if reply == QMessageBox.Yes:  
            self.api_result.clear()  
            self.api_result.append(f"开始批量测试 ({len(tests)} 个)...\n")  
            
            for i, test in enumerate(tests, 1):  
                self.api_result.append(f"\n[{i}/{len(tests)}] 测试: {test.name}")  
                time.sleep(0.5)  # 避免请求过快  
                self._execute_api_test(test)  
    
    def on_api_test_selected(self):  
        """API测试选择事件"""  
        current_row = self.api_table.currentRow()  
        if current_row >= 0:  
            test_id = self.api_table.item(current_row, 0).text()  
            test = self.load_api_test_by_id(test_id)  
            
            if test:  
                self.api_name_label.setText(test.name)  
                self.api_method_label.setText(test.method)  
                self.api_url_label.setText(test.url)  
                
                if test.last_result:  
                    if test.last_result.get('success'):  
                        status = f"✅ 成功 (状态码: {test.last_result.get('status_code', 'N/A')})"  
                    else:  
                        status = f"❌ 失败"  
                    self.api_status_label.setText(status)  
                else:  
                    self.api_status_label.setText("未执行")  
    
    def update_api_test_table(self):  
        """更新API测试表格"""  
        tests = self.load_all_api_tests()  
        self.api_table.setRowCount(len(tests))  
        
        for i, test in enumerate(tests):  
            success_rate = f"{(test.success_count / test.test_count * 100):.1f}%" if test.test_count > 0 else "0%"  
            
            self.api_table.setItem(i, 0, QTableWidgetItem(test.id))  
            self.api_table.setItem(i, 1, QTableWidgetItem(test.name))  
            self.api_table.setItem(i, 2, QTableWidgetItem(test.method))  
            self.api_table.setItem(i, 3, QTableWidgetItem(test.url[:50]))  
            self.api_table.setItem(i, 4, QTableWidgetItem(str(test.test_count)))  
            self.api_table.setItem(i, 5, QTableWidgetItem(success_rate))  
    
    # ========================================================================  
    # 数据同步功能实现  
    # ========================================================================  
    
    def add_sync_task(self):  
        """添加同步任务"""  
        dialog = SyncTaskDialog(self)  
        if dialog.exec_() == QDialog.Accepted:  
            task_data = dialog.get_task_data()  
            task = SyncTask(  
                id=self.generate_id(),  
                name=task_data['name'],  
                source=task_data['source'],  
                target=task_data['target'],  
                mode=task_data['mode'],  
                exclude_patterns=task_data['exclude_patterns']  
            )  
            self.save_sync_task(task)  
            self.update_sync_task_table()  
            self.log_message(f"添加同步任务: {task.name}", "info")  
    
    def edit_sync_task(self):  
        """编辑同步任务"""  
        current_row = self.sync_table.currentRow()  
        if current_row < 0:  
            QMessageBox.warning(self, "警告", "请先选择一个任务")  
            return  
        
        task_id = self.sync_table.item(current_row, 0).text()  
        task = self.load_sync_task_by_id(task_id)  
        
        if task:  
            dialog = SyncTaskDialog(self, task)  
            if dialog.exec_() == QDialog.Accepted:  
                task_data = dialog.get_task_data()  
                task.name = task_data['name']  
                task.source = task_data['source']  
                task.target = task_data['target']  
                task.mode = task_data['mode']  
                task.exclude_patterns = task_data['exclude_patterns']  
                self.save_sync_task(task)  
                self.update_sync_task_table()  
                self.log_message(f"编辑同步任务: {task.name}", "info")  
    
    def delete_sync_task(self):  
        """删除同步任务"""  
        current_row = self.sync_table.currentRow()  
        if current_row < 0:  
            QMessageBox.warning(self, "警告", "请先选择一个任务")  
            return  
        
        reply = QMessageBox.question(  
            self, "确认删除", "确定要删除选中的任务吗？",  
            QMessageBox.Yes | QMessageBox.No  
        )  
        
        if reply == QMessageBox.Yes:  
            task_id = self.sync_table.item(current_row, 0).text()  
            self.delete_sync_task_by_id(task_id)  
            self.update_sync_task_table()  
            self.log_message("删除同步任务", "info")  
    
    def execute_sync_task(self):  
        """执行同步任务"""  
        current_row = self.sync_table.currentRow()  
        if current_row < 0:  
            QMessageBox.warning(self, "警告", "请先选择一个任务")  
            return  
        
        task_id = self.sync_table.item(current_row, 0).text()  
        task = self.load_sync_task_by_id(task_id)  
        
        if task:  
            self.sync_log.clear()  
            self.sync_log.append(f"开始同步: {task.name}\n")  
            self.sync_progress.setVisible(True)  
            self.sync_progress.setValue(0)  
            
            # 在新线程中执行  
            thread = threading.Thread(target=self._execute_sync, args=(task,))  
            thread.daemon = True  
            thread.start()  
    
    def _execute_sync(self, task: SyncTask):  
        """执行同步（后台线程）"""  
        try:  
            source = Path(task.source)  
            target = Path(task.target)  
            
            if not source.exists():  
                QTimer.singleShot(0, lambda: self.sync_log.append(f"❌ 源路径不存在: {source}"))  
                QTimer.singleShot(0, lambda: self.sync_progress.setVisible(False))  
                return  
            
            QTimer.singleShot(0, lambda: self.sync_log.append(f"源路径: {source}"))  
            QTimer.singleShot(0, lambda: self.sync_log.append(f"目标路径: {target}"))  
            QTimer.singleShot(0, lambda: self.sync_log.append(f"同步模式: {task.mode}\n"))  
            
            # 创建目标目录  
            target.mkdir(parents=True, exist_ok=True)  
            
            # 统计  
            copied = 0  
            updated = 0  
            deleted = 0  
            skipped = 0  
            
            # 获取所有文件  
            if source.is_file():  
                files = [source]  
            else:  
                files = list(source.rglob('*'))  
            
            total_files = len([f for f in files if f.is_file()])  
            QTimer.singleShot(0, lambda: self.sync_log.append(f"找到 {total_files} 个文件\n"))  
            
            processed = 0  
            
            for file in files:  
                if not file.is_file():  
                    continue  
                
                # 检查排除模式  
                if task.exclude_patterns:  
                    skip = False  
                    for pattern in task.exclude_patterns:  
                        if file.match(pattern):  
                            skip = True  
                            skipped += 1  
                            break  
                    if skip:  
                        continue  
                
                try:  
                    if source.is_file():  
                        rel_path = file.name  
                    else:  
                        rel_path = file.relative_to(source)  
                    
                    dst_file = target / rel_path  
                    
                    # 创建目标目录  
                    dst_file.parent.mkdir(parents=True, exist_ok=True)  
                    
                    # 检查是否需要更新  
                    if not dst_file.exists():  
                        shutil.copy2(file, dst_file)  
                        copied += 1  
                        msg = f"✅ 复制: {rel_path}"  
                    elif file.stat().st_mtime > dst_file.stat().st_mtime:  
                        shutil.copy2(file, dst_file)  
                        updated += 1  
                        msg = f"🔄 更新: {rel_path}"  
                    else:  
                        msg = None  
                    
                    if msg:  
                        QTimer.singleShot(0, lambda m=msg: self.sync_log.append(m))  
                    
                except Exception as e:  
                    QTimer.singleShot(0, lambda f=file, err=str(e):   
                                    self.sync_log.append(f"❌ 失败: {f.name} - {err}"))  
                
                processed += 1  
                progress = int((processed / total_files) * 100)  
                QTimer.singleShot(0, lambda p=progress: self.sync_progress.setValue(p))  
            
            # 镜像模式：删除多余文件  
            if task.mode == "mirror" and source.is_dir():  
                QTimer.singleShot(0, lambda: self.sync_log.append("\n检查多余文件..."))  
                
                for dst_file in target.rglob('*'):  
                    if dst_file.is_file():  
                        rel_path = dst_file.relative_to(target)  
                        src_file = source / rel_path  
                        
                        if not src_file.exists():  
                            dst_file.unlink()  
                            deleted += 1  
                            QTimer.singleShot(0, lambda r=rel_path:   
                                            self.sync_log.append(f"🗑️ 删除: {r}"))  
            
            # 更新任务记录  
            task.last_sync = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
            task.sync_count += 1  
            task.files_synced = copied + updated  
            self.save_sync_task(task)  
            
            # 显示汇总  
            summary = f"\n{'='*60}\n"  
            summary += f"同步完成！\n"  
            summary += f"新增: {copied} | 更新: {updated} | 删除: {deleted} | 跳过: {skipped}\n"  
            summary += f"{'='*60}"  
            
            QTimer.singleShot(0, lambda: self.sync_log.append(summary))  
            QTimer.singleShot(0, lambda: self.sync_progress.setValue(100))  
            QTimer.singleShot(2000, lambda: self.sync_progress.setVisible(False))  
            QTimer.singleShot(0, lambda: self.update_sync_task_table())  
            QTimer.singleShot(0, lambda: self.log_message(f"同步完成: {task.name}", "info"))  
            
        except Exception as e:  
            QTimer.singleShot(0, lambda err=str(e): self.sync_log.append(f"\n❌ 同步失败: {err}"))  
            QTimer.singleShot(0, lambda: self.sync_progress.setVisible(False))  
            QTimer.singleShot(0, lambda err=str(e): self.log_message(f"同步失败: {err}", "error"))  
    
    def update_sync_task_table(self):  
        """更新同步任务表格"""  
        tasks = self.load_all_sync_tasks()  
        self.sync_table.setRowCount(len(tasks))  
        
        for i, task in enumerate(tasks):  
            self.sync_table.setItem(i, 0, QTableWidgetItem(task.id))  
            self.sync_table.setItem(i, 1, QTableWidgetItem(task.name))  
            self.sync_table.setItem(i, 2, QTableWidgetItem(task.source[:30]))  
            self.sync_table.setItem(i, 3, QTableWidgetItem(task.target[:30]))  
            self.sync_table.setItem(i, 4, QTableWidgetItem(task.mode))  
            self.sync_table.setItem(i, 5, QTableWidgetItem(task.last_sync or "未执行"))  
            self.sync_table.setItem(i, 6, QTableWidgetItem(str(task.sync_count)))  
            self.sync_table.setItem(i, 7, QTableWidgetItem(str(task.files_synced)))  
    
    # ========================================================================  
    # 系统监控功能  
    # ========================================================================  
    
    def on_stats_updated(self, stats: Dict):  
        """系统统计更新回调"""  
        # 更新CPU  
        cpu_percent = stats['cpu_percent']  
        self.cpu_percent_label.setText(f"{cpu_percent:.1f}%")  
        self.cpu_label.setText(f"CPU: {cpu_percent:.1f}%")  
        
        # 更新内存  
        memory = stats['memory']  
        memory_percent = memory.percent  
        memory_used = memory.used / (1024**3)  
        memory_total = memory.total / (1024**3)  
        self.memory_percent_label.setText(f"{memory_percent:.1f}%")  
        self.memory_info_label.setText(f"{memory_used:.1f} GB / {memory_total:.1f} GB")  
        self.memory_label.setText(f"内存: {memory_percent:.1f}%")  
        
        # 更新磁盘  
        disk = stats['disk']  
        disk_percent = disk.percent  
        disk_used = disk.used / (1024**3)  
        disk_total = disk.total / (1024**3)  
        self.disk_percent_label.setText(f"{disk_percent:.1f}%")  
        self.disk_info_label.setText(f"{disk_used:.1f} GB / {disk_total:.1f} GB")  
        
        # 更新网络  
        network = stats['network']  
        sent_mb = network.bytes_sent / (1024**2)  
        recv_mb = network.bytes_recv / (1024**2)  
        self.network_sent_label.setText(f"发送: {sent_mb:.1f} MB")  
        self.network_recv_label.setText(f"接收: {recv_mb:.1f} MB")  
        
        # 更新进程数  
        self.process_count_label.setText(str(stats['processes']))  
        
        # 更新进程列表（每5秒一次）  
        if not hasattr(self, '_last_process_update'):  
            self._last_process_update = 0  
        
        if time.time() - self._last_process_update > 5:  
            self._last_process_update = time.time()  
            self.update_process_table()  
    
    def update_process_table(self):  
        """更新进程表格"""  
        try:  
            processes = []  
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):  
                try:  
                    processes.append(proc.info)  
                except (psutil.NoSuchProcess, psutil.AccessDenied):  
                    pass  
            
            # 按CPU使用率排序，取前10  
            processes.sort(key=lambda p: p.get('cpu_percent', 0), reverse=True)  
            top_processes = processes[:10]  
            
            self.process_table.setRowCount(len(top_processes))  
            
            for i, proc in enumerate(top_processes):  
                self.process_table.setItem(i, 0, QTableWidgetItem(str(proc.get('pid', '-'))))  
                self.process_table.setItem(i, 1, QTableWidgetItem(proc.get('name', '-')[:30]))  
                self.process_table.setItem(i, 2, QTableWidgetItem(f"{proc.get('cpu_percent', 0):.1f}"))  
                self.process_table.setItem(i, 3, QTableWidgetItem(f"{proc.get('memory_percent', 0):.1f}"))  
        except Exception as e:  
            print(f"更新进程表格失败: {str(e)}")  
    
    # ========================================================================  
    # 日志功能  
    # ========================================================================  
    
    def log_message(self, message: str, level: str = "info"):  
        """记录日志消息"""  
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
        
        # 设置颜色  
        colors = {  
            "info": "black",  
            "warning": "orange",  
            "error": "red",  
            "success": "green"  
        }  
        color = colors.get(level, "black")  
        
        # 设置图标  
        icons = {  
            "info": "ℹ️",  
            "warning": "⚠️",  
            "error": "❌",  
            "success": "✅"  
        }  
        icon = icons.get(level, "")  
        
        # 格式化消息  
        formatted_message = f'<span style="color: gray;">[{timestamp}]</span> ' \
                          f'<span style="color: {color};">{icon} {message}</span>'  
        
        self.main_log.append(formatted_message)  
        
        # 自动滚动  
        if self.log_auto_scroll:  
            self.main_log.moveCursor(QTextCursor.End)  
        
        # 写入文件  
        try:  
            with open(self.log_file, 'a', encoding='utf-8') as f:  
                f.write(f"[{timestamp}] [{level.upper()}] {message}\n")  
        except Exception as e:  
            print(f"写入日志文件失败: {str(e)}")  
        
        # 更新统计  
        self.log_count_label.setText(f"总计: {self.main_log.document().lineCount()} 条")  
    
    def filter_logs(self):  
        """过滤日志"""  
        # 简化实现：实际应该重新加载并过滤  
        pass  
    
    def clear_main_log(self):  
        """清空主日志"""  
        reply = QMessageBox.question(  
            self, "确认", "确定要清空所有日志吗？",  
            QMessageBox.Yes | QMessageBox.No  
        )  
        
        if reply == QMessageBox.Yes:  
            self.main_log.clear()  
            self.log_count_label.setText("总计: 0 条")  
            self.log_message("日志已清空", "info")  
    
    def export_main_log(self):  
        """导出主日志"""  
        file_path, _ = QFileDialog.getSaveFileName(  
            self, "导出日志",   
            f"automation_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",  
            "文本文件 (*.txt)"  
        )  
        
        if file_path:  
            try:  
                with open(file_path, 'w', encoding='utf-8') as f:  
                    f.write(self.main_log.toPlainText())  
                QMessageBox.information(self, "成功", "日志已导出")  
                self.log_message(f"导出日志到: {file_path}", "info")  
            except Exception as e:  
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")  
    
    def export_logs(self):  
        """导出所有日志"""  
        self.export_main_log()  
    
    def clear_logs(self):  
        """清空所有日志"""  
        self.clear_main_log()  
        self.monitor_log.clear()  
        self.web_log.clear()  
        self.macro_log.clear()  
        self.sync_log.clear()  
    
    # ========================================================================  
    # 辅助功能  
    # ========================================================================  
    
    def generate_id(self) -> str:  
        """生成唯一ID"""  
        return hashlib.md5(f"{time.time()}{os.urandom(8)}".encode()).hexdigest()[:8]  
    
    def get_input_dialog(self, title: str, label: str) -> tuple:  
        """显示输入对话框"""  
        from PyQt5.QtWidgets import QInputDialog  
        text, ok = QInputDialog.getText(self, title, label)  
        return text, ok  
    
    def show_notification(self, title: str, message: str):  
        """显示系统通知"""  
        if self.tray_icon.isVisible():  
            self.tray_icon.showMessage(  
                title, message,  
                QSystemTrayIcon.Information,  
                3000  
            )  
    
    def start_all_services(self):  
        """启动所有服务"""  
        self.scheduler_thread.running = True  
        self.file_monitor_thread.running = True  
        self.log_message("所有服务已启动", "success")  
        self.status_label.setText("运行中")  
    
    def stop_all_services(self):  
        """停止所有服务"""  
        reply = QMessageBox.question(  
            self, "确认", "确定要暂停所有服务吗？",  
            QMessageBox.Yes | QMessageBox.No  
        )  
        
        if reply == QMessageBox.Yes:  
            self.scheduler_thread.running = False  
            self.file_monitor_thread.running = False  
            self.log_message("所有服务已暂停", "warning")  
            self.status_label.setText("已暂停")  
    
    def update_all_views(self):  
        """更新所有视图"""  
        # 定期更新任务和监控表格  
        if not hasattr(self, '_last_table_update'):  
            self._last_table_update = 0  
        
        if time.time() - self._last_table_update > 2:  
            self._last_table_update = time.time()  
            self.update_task_table()  
            self.update_monitor_table()  
    
    def apply_modern_style(self):  
        """应用现代化样式"""  
        style = """  
        QMainWindow {  
            background-color: #f5f5f5;  
        }  
        
        QTabWidget::pane {  
            border: 1px solid #ddd;  
            background-color: white;  
            border-radius: 4px;  
        }  
        
        QTabBar::tab {  
            background-color: #e0e0e0;  
            padding: 10px 20px;  
            margin-right: 2px;  
            border-top-left-radius: 4px;  
            border-top-right-radius: 4px;  
        }  
        
        QTabBar::tab:selected {  
            background-color: white;  
            border-bottom: 2px solid #2196F3;  
        }  
        
        QPushButton {  
            background-color: #2196F3;  
            color: white;  
            border: none;  
            padding: 8px 16px;  
            border-radius: 4px;  
            font-weight: bold;  
        }  
        
        QPushButton:hover {  
            background-color: #1976D2;  
        }  
        
        QPushButton:pressed {  
            background-color: #0D47A1;  
        }  
        
        QPushButton:disabled {  
            background-color: #cccccc;  
        }  
        
        QTableWidget {  
            gridline-color: #e0e0e0;  
            background-color: white;  
            border: 1px solid #ddd;  
            border-radius: 4px;  
        }  
        
        QTableWidget::item:selected {  
            background-color: #E3F2FD;  
            color: black;  
        }  
        
        QHeaderView::section {  
            background-color: #f0f0f0;  
            padding: 8px;  
            border: none;  
            border-right: 1px solid #ddd;  
            border-bottom: 1px solid #ddd;  
            font-weight: bold;  
        }  
        
        QTextEdit, QLineEdit {  
            border: 1px solid #ddd;  
            border-radius: 4px;  
            padding: 4px;  
            background-color: white;  
        }  
        
        QTextEdit:focus, QLineEdit:focus {  
            border: 2px solid #2196F3;  
        }  
        
        QGroupBox {  
            border: 2px solid #e0e0e0;  
            border-radius: 6px;  
            margin-top: 12px;  
            padding-top: 10px;  
            font-weight: bold;  
        }  
        
        QGroupBox::title {  
            subcontrol-origin: margin;  
            left: 10px;  
            padding: 0 5px;  
        }  
        
        QProgressBar {  
            border: 1px solid #ddd;  
            border-radius: 4px;  
            text-align: center;  
            height: 25px;  
        }  
        
        QProgressBar::chunk {  
            background-color: #4CAF50;  
            border-radius: 3px;  
        }  
        
        QComboBox {  
            border: 1px solid #ddd;  
            border-radius: 4px;  
            padding: 5px;  
            background-color: white;  
        }  
        
        QListWidget {  
            border: 1px solid #ddd;  
            border-radius: 4px;  
            background-color: white;  
        }  
        
        QListWidget::item:selected {  
            background-color: #E3F2FD;  
            color: black;  
        }  
        """  
        
        self.setStyleSheet(style)  
    
    def save_config(self):  
        """保存配置"""  
        try:  
            config = {  
                'tasks': [asdict(t) for t in self.scheduler_thread.get_tasks()],  
                'monitors': [asdict(m) for m in self.file_monitor_thread.get_monitors()],  
                'api_tests': [asdict(t) for t in self.load_all_api_tests()],  
                'sync_tasks': [asdict(t) for t in self.load_all_sync_tasks()],  
                'macros': [asdict(m) for m in self.load_all_macros()],  
                'version': '2.0.0'  
            }  
            
            with open(self.config_file, 'w', encoding='utf-8') as f:  
                json.dump(config, f, indent=2, ensure_ascii=False)  
            
            self.log_message("配置已保存", "success")  
            QMessageBox.information(self, "成功", "配置已保存")  
            
        except Exception as e:  
            self.log_message(f"保存配置失败: {str(e)}", "error")  
            QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")  
    
    def load_config(self):  
        """加载配置"""  
        if not os.path.exists(self.config_file):  
            self.log_message("配置文件不存在，使用默认配置", "info")  
            return  
        
        try:  
            with open(self.config_file, 'r', encoding='utf-8') as f:  
                config = json.load(f)  
            
            # 加载任务  
            for task_data in config.get('tasks', []):  
                task = ScheduledTask(**task_data)  
                self.scheduler_thread.add_task(task)  
            
            # 加载监控  
            for monitor_data in config.get('monitors', []):  
                monitor = FileMonitorTask(**monitor_data)  
                self.file_monitor_thread.add_monitor(monitor)  
            
            # 加载其他配置...  
            
            self.log_message("配置已加载", "success")  
            
            # 更新所有视图  
            self.update_task_table()  
            self.update_monitor_table()  
            self.update_api_test_table()  
            self.update_sync_task_table()  
            self.update_macro_table()  
            
        except Exception as e:  
            self.log_message(f"加载配置失败: {str(e)}", "error")  
            QMessageBox.warning(self, "警告", f"加载配置失败: {str(e)}")  
    
    # ========================================================================  
    # 数据持久化（简化实现，实际应使用数据库）  
    # ========================================================================  
    
    def save_macro(self, macro: MacroRecord):  
        """保存宏"""  
        macros = self.load_all_macros()  
        # 更新或添加  
        found = False  
        for i, m in enumerate(macros):  
            if m.id == macro.id:  
                macros[i] = macro  
                found = True  
                break  
        if not found:  
            macros.append(macro)  
        
        self._save_json_data('macros.json', [asdict(m) for m in macros])  
    
    def load_macro_by_id(self, macro_id: str) -> Optional[MacroRecord]:  
        """加载宏"""  
        macros = self.load_all_macros()  
        return next((m for m in macros if m.id == macro_id), None)  
    
    def load_all_macros(self) -> List[MacroRecord]:  
        """加载所有宏"""  
        data = self._load_json_data('macros.json', [])  
        return [MacroRecord(**m) for m in data]  
    
    def delete_macro_by_id(self, macro_id: str):  
        """删除宏"""  
        macros = [m for m in self.load_all_macros() if m.id != macro_id]  
        self._save_json_data('macros.json', [asdict(m) for m in macros])  
    
    def save_api_test(self, test: APITest):  
        """保存API测试"""  
        tests = self.load_all_api_tests()  
        found = False  
        for i, t in enumerate(tests):  
            if t.id == test.id:  
                tests[i] = test  
                found = True  
                break  
        if not found:  
            tests.append(test)  
        
        self._save_json_data('api_tests.json', [asdict(t) for t in tests])  
    
    def load_api_test_by_id(self, test_id: str) -> Optional[APITest]:  
        """加载API测试"""  
        tests = self.load_all_api_tests()  
        return next((t for t in tests if t.id == test_id), None)  
    
    def load_all_api_tests(self) -> List[APITest]:  
        """加载所有API测试"""  
        data = self._load_json_data('api_tests.json', [])  
        return [APITest(**t) for t in data]  
    
    def delete_api_test_by_id(self, test_id: str):  
        """删除API测试"""  
        tests = [t for t in self.load_all_api_tests() if t.id != test_id]  
        self._save_json_data('api_tests.json', [asdict(t) for t in tests])  
    
    def save_sync_task(self, task: SyncTask):  
        """保存同步任务"""  
        tasks = self.load_all_sync_tasks()  
        found = False  
        for i, t in enumerate(tasks):  
            if t.id == task.id:  
                tasks[i] = task  
                found = True  
                break  
        if not found:  
            tasks.append(task)  
        
        self._save_json_data('sync_tasks.json', [asdict(t) for t in tasks])  
    
    def load_sync_task_by_id(self, task_id: str) -> Optional[SyncTask]:  
        """加载同步任务"""  
        tasks = self.load_all_sync_tasks()  
        return next((t for t in tasks if t.id == task_id), None)  
    
    def load_all_sync_tasks(self) -> List[SyncTask]:  
        """加载所有同步任务"""  
        data = self._load_json_data('sync_tasks.json', [])  
        return [SyncTask(**{**t, 'exclude_patterns': t.get('exclude_patterns') or []}) for t in data]  
    
    def delete_sync_task_by_id(self, task_id: str):  
        """删除同步任务"""  
        tasks = [t for t in self.load_all_sync_tasks() if t.id != task_id]  
        self._save_json_data('sync_tasks.json', [asdict(t) for t in tasks])  
    
    def _save_json_data(self, filename: str, data: Any):  
        """保存JSON数据"""  
        try:  
            with open(filename, 'w', encoding='utf-8') as f:  
                json.dump(data, f, indent=2, ensure_ascii=False)  
        except Exception as e:  
            print(f"保存数据失败 {filename}: {str(e)}")  
    
    def _load_json_data(self, filename: str, default: Any = None) -> Any:  
        """加载JSON数据"""  
        if not os.path.exists(filename):  
            return default if default is not None else []  
        
        try:  
            with open(filename, 'r', encoding='utf-8') as f:  
                return json.load(f)  
        except Exception as e:  
            print(f"加载数据失败 {filename}: {str(e)}")  
            return default if default is not None else []  
    
    # ========================================================================  
    # 窗口事件  
    # ========================================================================  
    
    def on_tray_activated(self, reason):  
        """托盘图标激活"""  
        if reason == QSystemTrayIcon.DoubleClick:  
            self.show()  
            self.activateWindow()  
    
    def show_about(self):  
        """显示关于"""  
        about_text = """  
        <h2>AutomationToolPro v2.0</h2>  
        <p><b>专业自动化工具</b></p>  
        <p>基于PyQt5开发的多功能自动化平台</p>  
        <br>  
        <p><b>主要功能：</b></p>  
        <ul>  
            <li>⏰ 定时任务调度</li>  
            <li>📁 文件监控与自动处理</li>  
            <li>🌐 网页自动化</li>  
            <li>🎮 宏录制与回放</li>  
            <li>🔌 API接口测试</li>  
            <li>🔄 数据同步</li>  
            <li>📊 系统资源监控</li>  
            <li>📝 完整日志系统</li>  
        </ul>  
        <br>  
        <p>© 2024 All Rights Reserved</p>  
        """  
        
        QMessageBox.about(self, "关于 AutomationToolPro", about_text)  
    
    def quit_application(self):  
        """退出应用程序"""  
        reply = QMessageBox.question(  
            self, "确认退出", "确定要退出程序吗？",  
            QMessageBox.Yes | QMessageBox.No  
        )  
        
        if reply == QMessageBox.Yes:  
            self.log_message("程序退出", "info")  
            self.save_config()  
            
            # 停止所有线程  
            self.scheduler_thread.stop()  
            self.file_monitor_thread.stop()  
            self.system_monitor_thread.stop()  
            
            # 等待线程结束  
            self.scheduler_thread.wait(1000)  
            self.file_monitor_thread.wait(1000)  
            self.system_monitor_thread.wait(1000)  
            
            QApplication.quit()  
    
    def closeEvent(self, event):  
        """窗口关闭事件"""  
        event.ignore()  
        self.hide()  
        self.show_notification("AutomationToolPro", "程序已最小化到系统托盘")  

# ============================================================================  
# 对话框类  
# ============================================================================  

class ScheduledTaskDialog(QDialog):  
    """定时任务对话框"""  
    
    def __init__(self, parent=None, task: ScheduledTask = None):  
        super().__init__(parent)  
        self.task = task  
        self.setWindowTitle("定时任务" if not task else "编辑任务")  
        self.setMinimumWidth(500)  
        self.init_ui()  
        
        if task:  
            self.load_task_data()  
    
    def init_ui(self):  
        layout = QFormLayout(self)  
        
        self.name_input = QLineEdit()  
        self.name_input.setPlaceholderText("例如：每小时备份")  
        layout.addRow("任务名称:", self.name_input)  
        
        self.interval_input = QSpinBox()  
        self.interval_input.setRange(1, 86400)  
        self.interval_input.setValue(60)  
        self.interval_input.setSuffix(" 秒")  
        layout.addRow("执行间隔:", self.interval_input)  
        
        self.action_type_combo = QComboBox()  
        self.action_type_combo.addItems(["message", "command", "url", "script"])  
        layout.addRow("动作类型:", self.action_type_combo)  
        
        self.action_param_input = QTextEdit()  
        self.action_param_input.setMaximumHeight(100)  
        self.action_param_input.setPlaceholderText("根据动作类型输入相应参数...")  
        layout.addRow("动作参数:", self.action_param_input)  
        
        # 提示信息  
        hint_label = QLabel(  
            "<small>"  
            "• message: 显示提醒消息<br>"  
            "• command: 执行系统命令<br>"  
            "• url: 打开网页<br>"  
            "• script: 执行Python代码"  
            "</small>"  
        )  
        layout.addRow("", hint_label)  
        
        buttons = QDialogButtonBox(  
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel  
        )  
        buttons.accepted.connect(self.accept)  
        buttons.rejected.connect(self.reject)  
        layout.addRow(buttons)  
    
    def load_task_data(self):  
        """加载任务数据"""  
        self.name_input.setText(self.task.name)  
        self.interval_input.setValue(self.task.interval)  
        self.action_type_combo.setCurrentText(self.task.action_type)  
        self.action_param_input.setPlainText(self.task.action_param)  
    
    def get_task_data(self) -> Dict:  
        """获取任务数据"""  
        return {  
            'name': self.name_input.text().strip(),  
            'interval': self.interval_input.value(),  
            'action_type': self.action_type_combo.currentText(),  
            'action_param': self.action_param_input.toPlainText().strip()  
        }  

class FileMonitorDialog(QDialog):  
    """文件监控对话框"""  
    
    def __init__(self, parent=None, monitor: FileMonitorTask = None):  
        super().__init__(parent)  
        self.monitor = monitor  
        self.setWindowTitle("文件监控" if not monitor else "编辑监控")  
        self.setMinimumWidth(550)  
        self.init_ui()  
        
        if monitor:  
            self.load_monitor_data()  
    
    def init_ui(self):  
        layout = QFormLayout(self)  
        
        self.name_input = QLineEdit()  
        self.name_input.setPlaceholderText("例如：文档自动归档")  
        layout.addRow("监控名称:", self.name_input)  
        
        path_layout = QHBoxLayout()  
        self.path_input = QLineEdit()  
        self.path_input.setPlaceholderText("选择要监控的目录或文件...")  
        path_layout.addWidget(self.path_input)  
        
        browse_btn = QPushButton("浏览")  
        browse_btn.clicked.connect(self.browse_path)  
        path_layout.addWidget(browse_btn)  
        
        layout.addRow("监控路径:", path_layout)  
        
        self.pattern_input = QLineEdit()  
        self.pattern_input.setText("*.txt")  
        self.pattern_input.setPlaceholderText("例如：*.txt, *.pdf, *report*")  
        layout.addRow("文件模式:", self.pattern_input)  
        
        self.action_combo = QComboBox()  
        self.action_combo.addItems(["copy", "move", "delete", "execute", "compress"])  
        self.action_combo.currentTextChanged.connect(self.on_action_changed)  
        layout.addRow("执行动作:", self.action_combo)  
        
        target_layout = QHBoxLayout()  
        self.target_input = QLineEdit()  
        self.target_input.setPlaceholderText("目标路径或命令...")  
        target_layout.addWidget(self.target_input)  
        
        target_browse_btn = QPushButton("浏览")  
        target_browse_btn.clicked.connect(self.browse_target)  
        target_layout.addWidget(target_browse_btn)  
        
        layout.addRow("目标/命令:", target_layout)  
        
        self.recursive_check = QCheckBox("递归监控子目录")  
        layout.addRow("", self.recursive_check)  
        
        self.ignore_hidden_check = QCheckBox("忽略隐藏文件")  
        self.ignore_hidden_check.setChecked(True)  
        layout.addRow("", self.ignore_hidden_check)  
        
        buttons = QDialogButtonBox(  
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel  
        )  
        buttons.accepted.connect(self.accept)  
        buttons.rejected.connect(self.reject)  
        layout.addRow(buttons)  
    
    def browse_path(self):  
        """浏览路径"""  
        path = QFileDialog.getExistingDirectory(self, "选择监控目录")  
        if path:  
            self.path_input.setText(path)  
    
    def browse_target(self):  
        """浏览目标路径"""  
        path = QFileDialog.getExistingDirectory(self, "选择目标目录")  
        if path:  
            self.target_input.setText(path)  
    
    def on_action_changed(self, action: str):  
        """动作改变事件"""  
        if action == "delete":  
            self.target_input.setEnabled(False)  
            self.target_input.setPlaceholderText("删除操作不需要目标路径")  
        elif action == "execute":  
            self.target_input.setEnabled(True)  
            self.target_input.setPlaceholderText("输入要执行的命令...")  
        else:  
            self.target_input.setEnabled(True)  
            self.target_input.setPlaceholderText("选择目标目录...")  
    
    def load_monitor_data(self):  
        """加载监控数据"""  
        self.name_input.setText(self.monitor.name)  
        self.path_input.setText(self.monitor.path)  
        self.pattern_input.setText(self.monitor.pattern)  
        self.action_combo.setCurrentText(self.monitor.action)  
        self.target_input.setText(self.monitor.target)  
        self.recursive_check.setChecked(self.monitor.recursive)  
        self.ignore_hidden_check.setChecked(self.monitor.ignore_hidden)  
    
    def get_monitor_data(self) -> Dict:  
        """获取监控数据"""  
        return {  
            'name': self.name_input.text().strip(),  
            'path': self.path_input.text().strip(),  
            'pattern': self.pattern_input.text().strip(),  
            'action': self.action_combo.currentText(),  
            'target': self.target_input.text().strip(),  
                        'recursive': self.recursive_check.isChecked(),
            'ignore_hidden': self.ignore_hidden_check.isChecked()
        }

class WebScriptDialog(QDialog):
    """网页自动化脚本对话框"""
    
    def __init__(self, parent=None, script: WebScript = None):
        super().__init__(parent)
        self.script = script
        self.setWindowTitle("网页脚本" if not script else "编辑脚本")
        self.setMinimumSize(600, 500)
        self.actions = []
        self.init_ui()
        
        if script:
            self.load_script_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 基本信息
        info_group = QGroupBox("基本信息")
        info_layout = QFormLayout(info_group)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如：自动登录")
        info_layout.addRow("脚本名称:", self.name_input)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        info_layout.addRow("起始URL:", self.url_input)
        
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(5, 300)
        self.timeout_input.setValue(30)
        self.timeout_input.setSuffix(" 秒")
        info_layout.addRow("超时时间:", self.timeout_input)
        
        layout.addWidget(info_group)
        
        # 动作列表
        action_group = QGroupBox("动作序列")
        action_layout = QVBoxLayout(action_group)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        add_action_btn = QPushButton("➕ 添加动作")
        add_action_btn.clicked.connect(self.add_action)
        toolbar.addWidget(add_action_btn)
        
        remove_action_btn = QPushButton("➖ 删除")
        remove_action_btn.clicked.connect(self.remove_action)
        toolbar.addWidget(remove_action_btn)
        
        move_up_btn = QPushButton("⬆️ 上移")
        move_up_btn.clicked.connect(self.move_action_up)
        toolbar.addWidget(move_up_btn)
        
        move_down_btn = QPushButton("⬇️ 下移")
        move_down_btn.clicked.connect(self.move_action_down)
        toolbar.addWidget(move_down_btn)
        
        toolbar.addStretch()
        action_layout.addLayout(toolbar)
        
        # 动作列表
        self.action_list = QListWidget()
        action_layout.addWidget(self.action_list)
        
        layout.addWidget(action_group)
        
        # 提示信息
        hint_label = QLabel(
            "<small><b>支持的动作类型：</b><br>"
            "• click: 点击元素<br>"
            "• input: 输入文本<br>"
            "• wait: 等待指定秒数<br>"
            "• screenshot: 截图保存<br>"
            "• execute: 执行JavaScript</small>"
        )
        layout.addWidget(hint_label)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def add_action(self):
        """添加动作"""
        dialog = WebActionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            action_data = dialog.get_action_data()
            self.actions.append(action_data)
            self.update_action_list()
    
    def remove_action(self):
        """删除动作"""
        current_row = self.action_list.currentRow()
        if current_row >= 0:
            self.actions.pop(current_row)
            self.update_action_list()
    
    def move_action_up(self):
        """上移动作"""
        current_row = self.action_list.currentRow()
        if current_row > 0:
            self.actions[current_row], self.actions[current_row - 1] = \
                self.actions[current_row - 1], self.actions[current_row]
            self.update_action_list()
            self.action_list.setCurrentRow(current_row - 1)
    
    def move_action_down(self):
        """下移动作"""
        current_row = self.action_list.currentRow()
        if current_row < len(self.actions) - 1:
            self.actions[current_row], self.actions[current_row + 1] = \
                self.actions[current_row + 1], self.actions[current_row]
            self.update_action_list()
            self.action_list.setCurrentRow(current_row + 1)
    
    def update_action_list(self):
        """更新动作列表"""
        self.action_list.clear()
        for i, action in enumerate(self.actions, 1):
            text = f"{i}. [{action['type']}] {action.get('selector', action.get('value', ''))}"
            self.action_list.addItem(text)
    
    def load_script_data(self):
        """加载脚本数据"""
        self.name_input.setText(self.script.name)
        self.url_input.setText(self.script.url)
        self.timeout_input.setValue(self.script.timeout)
        self.actions = self.script.actions.copy()
        self.update_action_list()
    
    def validate_and_accept(self):
        """验证并接受"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "警告", "请输入脚本名称")
            return
        
        if not self.url_input.text().strip():
            QMessageBox.warning(self, "警告", "请输入URL")
            return
        
        if len(self.actions) == 0:
            QMessageBox.warning(self, "警告", "请至少添加一个动作")
            return
        
        self.accept()
    
    def get_script_data(self) -> Dict:
        """获取脚本数据"""
        return {
            'name': self.name_input.text().strip(),
            'url': self.url_input.text().strip(),
            'timeout': self.timeout_input.value(),
            'actions': self.actions.copy()
        }

class WebActionDialog(QDialog):
    """网页动作对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加动作")
        self.setMinimumWidth(400)
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout(self)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["click", "input", "wait", "screenshot", "execute"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        layout.addRow("动作类型:", self.type_combo)
        
        self.selector_input = QLineEdit()
        self.selector_input.setPlaceholderText("例如：#username, .btn-submit")
        layout.addRow("CSS选择器:", self.selector_input)
        
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("根据动作类型输入相应值...")
        layout.addRow("值/参数:", self.value_input)
        
        self.selector_label = layout.labelForField(self.selector_input)
        self.value_label = layout.labelForField(self.value_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.on_type_changed("click")
    
    def on_type_changed(self, action_type: str):
        """动作类型改变"""
        if action_type == "click":
            self.selector_label.setText("CSS选择器:")
            self.selector_input.setEnabled(True)
            self.value_label.setText("值/参数:")
            self.value_input.setEnabled(False)
            self.value_input.setPlaceholderText("点击操作不需要值")
            
        elif action_type == "input":
            self.selector_label.setText("CSS选择器:")
            self.selector_input.setEnabled(True)
            self.value_label.setText("输入内容:")
            self.value_input.setEnabled(True)
            self.value_input.setPlaceholderText("要输入的文本")
            
        elif action_type == "wait":
            self.selector_label.setText("CSS选择器:")
            self.selector_input.setEnabled(False)
            self.selector_input.setPlaceholderText("等待操作不需要选择器")
            self.value_label.setText("等待秒数:")
            self.value_input.setEnabled(True)
            self.value_input.setPlaceholderText("例如：3")
            
        elif action_type == "screenshot":
            self.selector_label.setText("CSS选择器:")
            self.selector_input.setEnabled(False)
            self.selector_input.setPlaceholderText("截图不需要选择器")
            self.value_label.setText("保存路径:")
            self.value_input.setEnabled(True)
            self.value_input.setPlaceholderText("例如：screenshot.png")
            
        elif action_type == "execute":
            self.selector_label.setText("CSS选择器:")
            self.selector_input.setEnabled(False)
            self.selector_input.setPlaceholderText("执行JS不需要选择器")
            self.value_label.setText("JavaScript代码:")
            self.value_input.setEnabled(True)
            self.value_input.setPlaceholderText("例如：alert('Hello');")
    
    def get_action_data(self) -> Dict:
        """获取动作数据"""
        return {
            'type': self.type_combo.currentText(),
            'selector': self.selector_input.text().strip(),
            'value': self.value_input.text().strip()
        }

class APITestDialog(QDialog):
    """API测试对话框"""
    
    def __init__(self, parent=None, test: APITest = None):
        super().__init__(parent)
        self.test = test
        self.setWindowTitle("API测试" if not test else "编辑测试")
        self.setMinimumSize(600, 550)
        self.init_ui()
        
        if test:
            self.load_test_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如：用户登录API")
        basic_layout.addRow("测试名称:", self.name_input)
        
        method_layout = QHBoxLayout()
        self.method_combo = QComboBox()
        self.method_combo.addItems(["GET", "POST", "PUT", "DELETE", "PATCH"])
        method_layout.addWidget(self.method_combo)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://api.example.com/users")
        method_layout.addWidget(self.url_input)
        
        basic_layout.addRow("请求:", method_layout)
        
        layout.addWidget(basic_group)
        
        # Headers
        headers_group = QGroupBox("请求头 (Headers)")
        headers_layout = QVBoxLayout(headers_group)
        
        headers_hint = QLabel("<small>格式: key: value (每行一个)</small>")
        headers_layout.addWidget(headers_hint)
        
        self.headers_input = QTextEdit()
        self.headers_input.setMaximumHeight(100)
        self.headers_input.setPlaceholderText(
            "Content-Type: application/json\n"
            "Authorization: Bearer token123"
        )
        headers_layout.addWidget(self.headers_input)
        
        layout.addWidget(headers_group)
        
        # Body
        body_group = QGroupBox("请求体 (Body)")
        body_layout = QVBoxLayout(body_group)
        
        body_hint = QLabel("<small>JSON格式（仅POST/PUT/PATCH需要）</small>")
        body_layout.addWidget(body_hint)
        
        self.body_input = QTextEdit()
        self.body_input.setMaximumHeight(120)
        self.body_input.setPlaceholderText(
            '{\n'
            '  "username": "user1",\n'
            '  "password": "pass123"\n'
            '}'
        )
        body_layout.addWidget(self.body_input)
        
        layout.addWidget(body_group)
        
        # 验证设置
        validation_group = QGroupBox("验证设置")
        validation_layout = QFormLayout(validation_group)
        
        self.expected_status_input = QSpinBox()
        self.expected_status_input.setRange(100, 599)
        self.expected_status_input.setValue(200)
        validation_layout.addRow("期望状态码:", self.expected_status_input)
        
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(5, 300)
        self.timeout_input.setValue(30)
        self.timeout_input.setSuffix(" 秒")
        validation_layout.addRow("超时时间:", self.timeout_input)
        
        layout.addWidget(validation_group)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_test_data(self):
        """加载测试数据"""
        self.name_input.setText(self.test.name)
        self.method_combo.setCurrentText(self.test.method)
        self.url_input.setText(self.test.url)
        
        # 加载headers
        headers_text = "\n".join([f"{k}: {v}" for k, v in self.test.headers.items()])
        self.headers_input.setPlainText(headers_text)
        
        self.body_input.setPlainText(self.test.body)
        self.expected_status_input.setValue(self.test.expected_status)
        self.timeout_input.setValue(self.test.timeout)
    
    def validate_and_accept(self):
        """验证并接受"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "警告", "请输入测试名称")
            return
        
        if not self.url_input.text().strip():
            QMessageBox.warning(self, "警告", "请输入URL")
            return
        
        self.accept()
    
    def get_test_data(self) -> Dict:
        """获取测试数据"""
        # 解析headers
        headers = {}
        for line in self.headers_input.toPlainText().split('\n'):
            line = line.strip()
            if line and ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
        
        return {
            'name': self.name_input.text().strip(),
            'method': self.method_combo.currentText(),
            'url': self.url_input.text().strip(),
            'headers': headers,
            'body': self.body_input.toPlainText().strip(),
            'expected_status': self.expected_status_input.value(),
            'timeout': self.timeout_input.value()
        }

class SyncTaskDialog(QDialog):
    """同步任务对话框"""
    
    def __init__(self, parent=None, task: SyncTask = None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle("同步任务" if not task else "编辑任务")
        self.setMinimumWidth(550)
        self.init_ui()
        
        if task:
            self.load_task_data()
    
    def init_ui(self):
        layout = QFormLayout(self)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如：文档同步")
        layout.addRow("任务名称:", self.name_input)
        
        # 源路径
        source_layout = QHBoxLayout()
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("选择源目录...")
        source_layout.addWidget(self.source_input)
        
        source_browse_btn = QPushButton("浏览")
        source_browse_btn.clicked.connect(self.browse_source)
        source_layout.addWidget(source_browse_btn)
        
        layout.addRow("源路径:", source_layout)
        
        # 目标路径
        target_layout = QHBoxLayout()
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("选择目标目录...")
        target_layout.addWidget(self.target_input)
        
        target_browse_btn = QPushButton("浏览")
        target_browse_btn.clicked.connect(self.browse_target)
        target_layout.addWidget(target_browse_btn)
        
        layout.addRow("目标路径:", target_layout)
        
        # 同步模式
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "mirror - 镜像同步（删除多余文件）",
            "sync - 增量同步（只复制新文件）",
            "backup - 备份模式（保留历史版本）"
        ])
        layout.addRow("同步模式:", self.mode_combo)
        
        # 排除模式
        exclude_group = QGroupBox("排除模式（可选）")
        exclude_layout = QVBoxLayout(exclude_group)
        
        exclude_hint = QLabel("<small>每行一个模式，例如：*.tmp, .git, __pycache__</small>")
        exclude_layout.addWidget(exclude_hint)
        
        self.exclude_input = QTextEdit()
        self.exclude_input.setMaximumHeight(80)
        self.exclude_input.setPlaceholderText("*.tmp\n.git\n__pycache__")
        exclude_layout.addWidget(self.exclude_input)
        
        layout.addRow(exclude_group)
        
        # 提示信息
        hint_label = QLabel(
            "<small><b>同步模式说明：</b><br>"
            "• mirror: 完全同步，删除目标中多余的文件<br>"
            "• sync: 增量同步，只复制新文件和修改的文件<br>"
            "• backup: 备份模式，保留目标中的所有文件</small>"
        )
        layout.addRow("", hint_label)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def browse_source(self):
        """浏览源路径"""
        path = QFileDialog.getExistingDirectory(self, "选择源目录")
        if path:
            self.source_input.setText(path)
    
    def browse_target(self):
        """浏览目标路径"""
        path = QFileDialog.getExistingDirectory(self, "选择目标目录")
        if path:
            self.target_input.setText(path)
    
    def load_task_data(self):
        """加载任务数据"""
        self.name_input.setText(self.task.name)
        self.source_input.setText(self.task.source)
        self.target_input.setText(self.task.target)
        
        # 设置模式
        mode_map = {
            'mirror': 0,
            'sync': 1,
            'backup': 2
        }
        self.mode_combo.setCurrentIndex(mode_map.get(self.task.mode, 0))
        
        # 设置排除模式
        if self.task.exclude_patterns:
            self.exclude_input.setPlainText("\n".join(self.task.exclude_patterns))
    
    def validate_and_accept(self):
        """验证并接受"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "警告", "请输入任务名称")
            return
        
        if not self.source_input.text().strip():
            QMessageBox.warning(self, "警告", "请选择源路径")
            return
        
        if not self.target_input.text().strip():
            QMessageBox.warning(self, "警告", "请选择目标路径")
            return
        
        if self.source_input.text() == self.target_input.text():
            QMessageBox.warning(self, "警告", "源路径和目标路径不能相同")
            return
        
        self.accept()
    
    def get_task_data(self) -> Dict:
        """获取任务数据"""
        # 解析模式
        mode_text = self.mode_combo.currentText()
        mode = mode_text.split(' - ')[0]
        
        # 解析排除模式
        exclude_patterns = []
        for line in self.exclude_input.toPlainText().split('\n'):
            line = line.strip()
            if line:
                exclude_patterns.append(line)
        
        return {
            'name': self.name_input.text().strip(),
            'source': self.source_input.text().strip(),
            'target': self.target_input.text().strip(),
            'mode': mode,
            'exclude_patterns': exclude_patterns
        }

# ============================================================================
# 主程序入口
# ============================================================================

def main():
    """主程序"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("AutomationToolPro")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("AutomationTools")
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    # 创建并显示主窗口
    window = AutomationToolPro()
    window.show()
    
    # 启动日志
    window.log_message("=" * 60, "info")
    window.log_message("AutomationToolPro v2.0 启动", "success")
    window.log_message(f"系统: {platform.system()} {platform.release()}", "info")
    window.log_message(f"Python: {platform.python_version()}", "info")
    window.log_message("=" * 60, "info")
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()