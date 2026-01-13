#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SystemMonitorPro - 专业系统监控工具
功能：实时监控、进程管理、日志查看、性能警报、数据导出
作者：LYP
GitHub：https://github.com/lyp0746
邮箱：1610369302@qq.com
版本：2.0.0
8. 深色/浅色主题切换
9. 资源历史记录图表
10. 网络连接监控

Author: LYP
Date: 2025-12-12
Version: 2.0
"""

import sys
import psutil
import platform
import subprocess
import time
import json
import os
import csv
from datetime import datetime
from pathlib import Path
from collections import deque
from typing import Dict, List, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QTextEdit, QLineEdit, QComboBox, QSpinBox, QMessageBox, QFileDialog,
    QProgressBar, QGroupBox, QSplitter, QHeaderView, QListWidget,
    QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QTreeWidget,
    QTreeWidgetItem, QMenu, QAction, QStatusBar, QSystemTrayIcon,
    QSlider, QRadioButton, QButtonGroup, QScrollArea, QFrame, QGridLayout,
    QDoubleSpinBox, QToolBar, QMenuBar
)
from PyQt5.QtCore import (
    Qt, QTimer, pyqtSignal, QThread, QSize, QSettings,
    QPropertyAnimation, QEasingCurve, QPointF
)
from PyQt5.QtGui import (
    QFont, QColor, QIcon, QPixmap, QPainter, QPalette,
    QBrush, QPen, QLinearGradient, QCursor
)
from PyQt5.QtChart import (
    QChart, QChartView, QLineSeries, QValueAxis,
    QAreaSeries, QSplineSeries
)


# ==================== 配置管理 ====================
class Config:
    """应用配置管理"""
    def __init__(self):
        self.settings = QSettings('SystemMonitorPro', 'Settings')
        self.load_defaults()

    def load_defaults(self):
        """加载默认配置"""
        self.monitor_interval = self.settings.value('monitor_interval', 1000, type=int)
        self.process_refresh_interval = self.settings.value('process_refresh', 5000, type=int)
        self.history_length = self.settings.value('history_length', 60, type=int)
        self.theme = self.settings.value('theme', 'light', type=str)

        # 警报阈值
        self.cpu_threshold = self.settings.value('cpu_threshold', 80.0, type=float)
        self.memory_threshold = self.settings.value('memory_threshold', 80.0, type=float)
        self.disk_threshold = self.settings.value('disk_threshold', 90.0, type=float)

        # 启用警报
        self.enable_alerts = self.settings.value('enable_alerts', True, type=bool)

    def save(self):
        """保存配置"""
        self.settings.setValue('monitor_interval', self.monitor_interval)
        self.settings.setValue('process_refresh', self.process_refresh_interval)
        self.settings.setValue('history_length', self.history_length)
        self.settings.setValue('theme', self.theme)
        self.settings.setValue('cpu_threshold', self.cpu_threshold)
        self.settings.setValue('memory_threshold', self.memory_threshold)
        self.settings.setValue('disk_threshold', self.disk_threshold)
        self.settings.setValue('enable_alerts', self.enable_alerts)


# ==================== 系统监控核心 ====================
class SystemMonitor:
    """系统监控核心类 - 增强版"""

    def __init__(self):
        self.last_net_io = psutil.net_io_counters()
        self.last_disk_io = psutil.disk_io_counters()
        self.last_time = time.time()

    def get_cpu_info(self) -> Dict:
        """获取CPU信息"""
        try:
            freq = psutil.cpu_freq()
            return {
                'percent': psutil.cpu_percent(interval=0.1),
                'count_logical': psutil.cpu_count(logical=True),
                'count_physical': psutil.cpu_count(logical=False),
                'freq_current': freq.current if freq else 0,
                'freq_min': freq.min if freq else 0,
                'freq_max': freq.max if freq else 0,
                'per_cpu': psutil.cpu_percent(interval=0.1, percpu=True)
            }
        except Exception as e:
            print(f"CPU信息获取错误: {e}")
            return {'percent': 0, 'count_logical': 0, 'count_physical': 0,
                    'freq_current': 0, 'freq_min': 0, 'freq_max': 0, 'per_cpu': []}

    def get_memory_info(self) -> Dict:
        """获取内存信息"""
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            return {
                'total': mem.total,
                'available': mem.available,
                'used': mem.used,
                'free': mem.free,
                'percent': mem.percent,
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_free': swap.free,
                'swap_percent': swap.percent
            }
        except Exception as e:
            print(f"内存信息获取错误: {e}")
            return {'total': 0, 'available': 0, 'used': 0, 'free': 0, 'percent': 0,
                    'swap_total': 0, 'swap_used': 0, 'swap_free': 0, 'swap_percent': 0}

    def get_disk_info(self) -> Dict:
        """获取磁盘信息"""
        disks = []
        try:
            for partition in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disks.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent
                    })
                except (PermissionError, OSError):
                    continue

            # 磁盘IO速度
            current_io = psutil.disk_io_counters()
            current_time = time.time()
            time_delta = current_time - self.last_time

            if time_delta > 0 and self.last_disk_io:
                read_speed = (current_io.read_bytes - self.last_disk_io.read_bytes) / time_delta
                write_speed = (current_io.write_bytes - self.last_disk_io.write_bytes) / time_delta
            else:
                read_speed = write_speed = 0

            self.last_disk_io = current_io

            return {
                'disks': disks,
                'io_read_bytes': current_io.read_bytes if current_io else 0,
                'io_write_bytes': current_io.write_bytes if current_io else 0,
                'read_speed': read_speed,
                'write_speed': write_speed
            }
        except Exception as e:
            print(f"磁盘信息获取错误: {e}")
            return {'disks': [], 'io_read_bytes': 0, 'io_write_bytes': 0,
                    'read_speed': 0, 'write_speed': 0}

    def get_network_info(self) -> Dict:
        """获取网络信息 - 增强版"""
        try:
            current_io = psutil.net_io_counters()
            current_time = time.time()
            time_delta = current_time - self.last_time

            # 计算网络速度
            if time_delta > 0 and self.last_net_io:
                upload_speed = (current_io.bytes_sent - self.last_net_io.bytes_sent) / time_delta
                download_speed = (current_io.bytes_recv - self.last_net_io.bytes_recv) / time_delta
            else:
                upload_speed = download_speed = 0

            self.last_net_io = current_io
            self.last_time = current_time

            # 网络连接
            try:
                connections = psutil.net_connections(kind='inet')
                connection_stats = {
                    'established': sum(1 for c in connections if c.status == 'ESTABLISHED'),
                    'listen': sum(1 for c in connections if c.status == 'LISTEN'),
                    'time_wait': sum(1 for c in connections if c.status == 'TIME_WAIT'),
                    'total': len(connections)
                }
            except (psutil.AccessDenied, PermissionError):
                connection_stats = {'established': 0, 'listen': 0, 'time_wait': 0, 'total': 0}

            # 网络接口
            interfaces = {}
            for name, addrs in psutil.net_if_addrs().items():
                interfaces[name] = [
                    {'family': addr.family.name, 'address': addr.address}
                    for addr in addrs
                ]

            return {
                'bytes_sent': current_io.bytes_sent,
                'bytes_recv': current_io.bytes_recv,
                'packets_sent': current_io.packets_sent,
                'packets_recv': current_io.packets_recv,
                'upload_speed': upload_speed,
                'download_speed': download_speed,
                'connections': connection_stats,
                'interfaces': interfaces
            }
        except Exception as e:
            print(f"网络信息获取错误: {e}")
            return {
                'bytes_sent': 0, 'bytes_recv': 0, 'packets_sent': 0, 'packets_recv': 0,
                'upload_speed': 0, 'download_speed': 0,
                'connections': {'established': 0, 'listen': 0, 'time_wait': 0, 'total': 0},
                'interfaces': {}
            }

    def get_process_list(self, sort_by='cpu', limit=None) -> List[Dict]:
        """获取进程列表 - 增强版"""
        processes = []
        try:
            for proc in psutil.process_iter([
                'pid', 'name', 'cpu_percent', 'memory_percent',
                'status', 'username', 'create_time', 'num_threads'
            ]):
                try:
                    pinfo = proc.info
                    pinfo['memory_mb'] = proc.memory_info().rss / (1024 * 1024)
                    processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            # 排序
            if sort_by == 'cpu':
                processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            elif sort_by == 'memory':
                processes.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)

            # 限制返回数量
            if limit:
                processes = processes[:limit]

            return processes
        except Exception as e:
            print(f"进程列表获取错误: {e}")
            return []

    def get_process_details(self, pid: int) -> Optional[Dict]:
        """获取进程详细信息"""
        try:
            proc = psutil.Process(pid)
            with proc.oneshot():
                return {
                    'pid': proc.pid,
                    'name': proc.name(),
                    'status': proc.status(),
                    'username': proc.username(),
                    'create_time': datetime.fromtimestamp(proc.create_time()).strftime('%Y-%m-%d %H:%M:%S'),
                    'cpu_percent': proc.cpu_percent(interval=0.1),
                    'memory_percent': proc.memory_percent(),
                    'memory_mb': proc.memory_info().rss / (1024 * 1024),
                    'num_threads': proc.num_threads(),
                    'cmdline': ' '.join(proc.cmdline()),
                    'cwd': proc.cwd() if hasattr(proc, 'cwd') else 'N/A',
                    'exe': proc.exe()
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception) as e:
            print(f"进程详情获取错误: {e}")
            return None

    def get_system_info(self) -> Dict:
        """获取系统信息"""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time

            return {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'hostname': platform.node(),
                'boot_time': boot_time.strftime("%Y-%m-%d %H:%M:%S"),
                'uptime': str(uptime).split('.')[0],
                'python_version': platform.python_version()
            }
        except Exception as e:
            print(f"系统信息获取错误: {e}")
            return {}

    def get_temperature(self) -> Dict:
        """获取硬件温度"""
        temps = {}
        try:
            if hasattr(psutil, 'sensors_temperatures'):
                sensors = psutil.sensors_temperatures()
                if sensors:
                    for name, entries in sensors.items():
                        temps[name] = [
                            {
                                'label': e.label or name,
                                'current': e.current,
                                'high': e.high if e.high else 0,
                                'critical': e.critical if e.critical else 0
                            }
                            for e in entries
                        ]
        except Exception as e:
            print(f"温度信息获取错误: {e}")
        return temps

    def get_battery_info(self) -> Optional[Dict]:
        """获取电池信息"""
        try:
            if hasattr(psutil, 'sensors_battery'):
                battery = psutil.sensors_battery()
                if battery:
                    return {
                        'percent': battery.percent,
                        'power_plugged': battery.power_plugged,
                        'time_left': battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else -1
                    }
        except Exception as e:
            print(f"电池信息获取错误: {e}")
        return None

    def kill_process(self, pid: int, force: bool = False) -> bool:
        """终止进程"""
        try:
            proc = psutil.Process(pid)
            if force:
                proc.kill()
            else:
                proc.terminate()
            proc.wait(timeout=3)
            return True
        except Exception as e:
            print(f"终止进程错误: {e}")
            return False

    def suspend_process(self, pid: int) -> bool:
        """挂起进程"""
        try:
            proc = psutil.Process(pid)
            proc.suspend()
            return True
        except Exception as e:
            print(f"挂起进程错误: {e}")
            return False

    def resume_process(self, pid: int) -> bool:
        """恢复进程"""
        try:
            proc = psutil.Process(pid)
            proc.resume()
            return True
        except Exception as e:
            print(f"恢复进程错误: {e}")
            return False


# ==================== 监控线程 ====================
class MonitorThread(QThread):
    """监控线程 - 增强版"""
    update_signal = pyqtSignal(dict)
    alert_signal = pyqtSignal(str, str)  # 类型，消息

    def __init__(self, config: Config):
        super().__init__()
        self.monitor = SystemMonitor()
        self.config = config
        self.running = True

    def run(self):
        while self.running:
            try:
                data = {
                    'cpu': self.monitor.get_cpu_info(),
                    'memory': self.monitor.get_memory_info(),
                    'disk': self.monitor.get_disk_info(),
                    'network': self.monitor.get_network_info(),
                    'temperature': self.monitor.get_temperature(),
                    'battery': self.monitor.get_battery_info(),
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                }

                self.update_signal.emit(data)

                # 检查警报
                if self.config.enable_alerts:
                    self.check_alerts(data)

                time.sleep(self.config.monitor_interval / 1000.0)
            except Exception as e:
                print(f"监控线程错误: {e}")
                time.sleep(1)

    def check_alerts(self, data: Dict):
        """检查是否需要发出警报"""
        # CPU警报
        if data['cpu']['percent'] > self.config.cpu_threshold:
            self.alert_signal.emit('CPU', f"CPU使用率过高: {data['cpu']['percent']:.1f}%")

        # 内存警报
        if data['memory']['percent'] > self.config.memory_threshold:
            self.alert_signal.emit('Memory', f"内存使用率过高: {data['memory']['percent']:.1f}%")

        # 磁盘警报
        for disk in data['disk']['disks']:
            if disk['percent'] > self.config.disk_threshold:
                self.alert_signal.emit('Disk', f"磁盘 {disk['mountpoint']} 使用率过高: {disk['percent']:.1f}%")

    def stop(self):
        self.running = False


# ==================== 格式化工具 ====================
class FormatUtils:
    """格式化工具类"""

    @staticmethod
    def format_bytes(bytes_value: float) -> str:
        """格式化字节"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"

    @staticmethod
    def format_speed(bytes_per_sec: float) -> str:
        """格式化速度"""
        return f"{FormatUtils.format_bytes(bytes_per_sec)}/s"

    @staticmethod
    def format_time(seconds: int) -> str:
        """格式化时间"""
        if seconds < 0:
            return "充电中"
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"


# ==================== 仪表盘部件 ====================
class DashboardWidget(QWidget):
    """仪表盘界面 - 完全重构"""

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.history_data = {
            'cpu': deque(maxlen=config.history_length),
            'memory': deque(maxlen=config.history_length),
            'network_up': deque(maxlen=config.history_length),
            'network_down': deque(maxlen=config.history_length),
            'disk_read': deque(maxlen=config.history_length),
            'disk_write': deque(maxlen=config.history_length)
        }
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)

        # ========== 顶部统计卡片 ==========
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(10)

        self.cpu_card = self.create_stat_card("CPU", "0%", QColor(52, 152, 219))
        self.memory_card = self.create_stat_card("内存", "0%", QColor(46, 204, 113))
        self.disk_card = self.create_stat_card("磁盘", "0%", QColor(155, 89, 182))
        self.network_card = self.create_stat_card("网络", "0 KB/s", QColor(230, 126, 34))

        cards_layout.addWidget(self.cpu_card)
        cards_layout.addWidget(self.memory_card)
        cards_layout.addWidget(self.disk_card)
        cards_layout.addWidget(self.network_card)

        main_layout.addLayout(cards_layout)

        # ========== 图表区域 ==========
        charts_splitter = QSplitter(Qt.Horizontal)

        # CPU & 内存图表
        left_charts = QWidget()
        left_layout = QVBoxLayout(left_charts)

        self.cpu_chart_view = self.create_chart_view("CPU使用率", QColor(52, 152, 219))
        self.memory_chart_view = self.create_chart_view("内存使用率", QColor(46, 204, 113))

        left_layout.addWidget(self.cpu_chart_view)
        left_layout.addWidget(self.memory_chart_view)

        # 网络 & 磁盘图表
        right_charts = QWidget()
        right_layout = QVBoxLayout(right_charts)

        self.network_chart_view = self.create_network_chart()
        self.disk_chart_view = self.create_disk_chart()

        right_layout.addWidget(self.network_chart_view)
        right_layout.addWidget(self.disk_chart_view)

        charts_splitter.addWidget(left_charts)
        charts_splitter.addWidget(right_charts)
        charts_splitter.setSizes([500, 500])

        main_layout.addWidget(charts_splitter, 2)

        # ========== 底部详细信息 ==========
        bottom_splitter = QSplitter(Qt.Horizontal)

        # 系统信息
        system_group = QGroupBox("📋 系统信息")
        system_layout = QVBoxLayout()
        self.system_info = QTextEdit()
        self.system_info.setReadOnly(True)
        self.system_info.setMaximumHeight(150)
        system_layout.addWidget(self.system_info)
        system_group.setLayout(system_layout)

        # 实时信息
        realtime_group = QGroupBox("📊 实时信息")
        realtime_layout = QVBoxLayout()
        self.realtime_info = QTextEdit()
        self.realtime_info.setReadOnly(True)
        self.realtime_info.setMaximumHeight(150)
        realtime_layout.addWidget(self.realtime_info)
        realtime_group.setLayout(realtime_layout)

        # 温度/电池信息
        temp_group = QGroupBox("🌡️ 温度 & 电池")
        temp_layout = QVBoxLayout()
        self.temp_battery_info = QTextEdit()
        self.temp_battery_info.setReadOnly(True)
        self.temp_battery_info.setMaximumHeight(150)
        temp_layout.addWidget(self.temp_battery_info)
        temp_group.setLayout(temp_layout)

        bottom_splitter.addWidget(system_group)
        bottom_splitter.addWidget(realtime_group)
        bottom_splitter.addWidget(temp_group)

        main_layout.addWidget(bottom_splitter, 1)

        self.setLayout(main_layout)

    def create_stat_card(self, title: str, value: str, color: QColor) -> QGroupBox:
        """创建统计卡片"""
        card = QGroupBox(title)
        card.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 14px;
                border: 2px solid {color.name()};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: {color.name()};
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(10)

        # 值标签
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setFont(QFont("Arial", 28, QFont.Bold))
        value_label.setObjectName("value_label")
        value_label.setStyleSheet(f"color: {color.name()};")

        # 进度条
        progress = QProgressBar()
        progress.setObjectName("progress_bar")
        progress.setTextVisible(False)
        progress.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: #ecf0f1;
            }}
            QProgressBar::chunk {{
                background-color: {color.name()};
                border-radius: 3px;
            }}
        """)

        # 详细信息标签
        detail_label = QLabel("")
        detail_label.setAlignment(Qt.AlignCenter)
        detail_label.setObjectName("detail_label")
        detail_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")

        layout.addWidget(value_label)
        layout.addWidget(progress)
        layout.addWidget(detail_label)

        card.setLayout(layout)
        return card

    def create_chart_view(self, title: str, color: QColor) -> QChartView:
        """创建图表视图"""
        chart = QChart()
        chart.setTitle(title)
        chart.setAnimationOptions(QChart.NoAnimation)
        chart.legend().hide()
        chart.setBackgroundRoundness(10)

        series = QSplineSeries()
        series.setColor(color)
        pen = series.pen()
        pen.setWidth(2)
        series.setPen(pen)

        chart.addSeries(series)

        # X轴
        axis_x = QValueAxis()
        axis_x.setRange(0, self.config.history_length)
        axis_x.setLabelFormat("%d")
        axis_x.setTitleText("时间 (秒)")
        axis_x.setTickCount(7)

        # Y轴
        axis_y = QValueAxis()
        axis_y.setRange(0, 100)
        axis_y.setLabelFormat("%.0f%%")
        axis_y.setTickCount(6)

        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)

        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)

        return chart_view

    def create_network_chart(self) -> QChartView:
        """创建网络图表"""
        chart = QChart()
        chart.setTitle("网络速度")
        chart.setAnimationOptions(QChart.NoAnimation)
        chart.setBackgroundRoundness(10)

        # 上传和下载系列
        self.upload_series = QSplineSeries()
        self.upload_series.setName("上传")
        self.upload_series.setColor(QColor(231, 76, 60))

        self.download_series = QSplineSeries()
        self.download_series.setName("下载")
        self.download_series.setColor(QColor(52, 152, 219))

        chart.addSeries(self.upload_series)
        chart.addSeries(self.download_series)

        # X轴
        axis_x = QValueAxis()
        axis_x.setRange(0, self.config.history_length)
        axis_x.setLabelFormat("%d")
        axis_x.setTitleText("时间 (秒)")

        # Y轴
        axis_y = QValueAxis()
        axis_y.setRange(0, 1024)  # KB/s
        axis_y.setLabelFormat("%.0f KB/s")

        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)

        self.upload_series.attachAxis(axis_x)
        self.upload_series.attachAxis(axis_y)
        self.download_series.attachAxis(axis_x)
        self.download_series.attachAxis(axis_y)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)

        return chart_view

    def create_disk_chart(self) -> QChartView:
        """创建磁盘IO图表"""
        chart = QChart()
        chart.setTitle("磁盘IO速度")
        chart.setAnimationOptions(QChart.NoAnimation)
        chart.setBackgroundRoundness(10)

        # 读写系列
        self.disk_read_series = QSplineSeries()
        self.disk_read_series.setName("读取")
        self.disk_read_series.setColor(QColor(46, 204, 113))

        self.disk_write_series = QSplineSeries()
        self.disk_write_series.setName("写入")
        self.disk_write_series.setColor(QColor(155, 89, 182))

        chart.addSeries(self.disk_read_series)
        chart.addSeries(self.disk_write_series)

        # X轴
        axis_x = QValueAxis()
        axis_x.setRange(0, self.config.history_length)
        axis_x.setLabelFormat("%d")
        axis_x.setTitleText("时间 (秒)")

        # Y轴
        axis_y = QValueAxis()
        axis_y.setRange(0, 1024)  # KB/s
        axis_y.setLabelFormat("%.0f KB/s")

        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)

        self.disk_read_series.attachAxis(axis_x)
        self.disk_read_series.attachAxis(axis_y)
        self.disk_write_series.attachAxis(axis_x)
        self.disk_write_series.attachAxis(axis_y)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)

        return chart_view

    def update_data(self, data: Dict):
        """更新所有数据"""
        # 更新统计卡片
        self.update_cpu_card(data['cpu'])
        self.update_memory_card(data['memory'])
        self.update_disk_card(data['disk'])
        self.update_network_card(data['network'])

        # 更新图表
        self.update_charts(data)

        # 更新详细信息
        self.update_realtime_info(data)
        self.update_temp_battery_info(data)

    def update_cpu_card(self, cpu_data: Dict):
        """更新CPU卡片"""
        percent = cpu_data['percent']
        self.cpu_card.findChild(QLabel, "value_label").setText(f"{percent:.1f}%")
        self.cpu_card.findChild(QProgressBar, "progress_bar").setValue(int(percent))
        self.cpu_card.findChild(QLabel, "detail_label").setText(
            f"核心: {cpu_data['count_logical']} | {cpu_data['freq_current']:.0f} MHz"
        )

    def update_memory_card(self, mem_data: Dict):
        """更新内存卡片"""
        percent = mem_data['percent']
        self.memory_card.findChild(QLabel, "value_label").setText(f"{percent:.1f}%")
        self.memory_card.findChild(QProgressBar, "progress_bar").setValue(int(percent))
        self.memory_card.findChild(QLabel, "detail_label").setText(
            f"已用: {FormatUtils.format_bytes(mem_data['used'])} / {FormatUtils.format_bytes(mem_data['total'])}"
        )

    def update_disk_card(self, disk_data: Dict):
        """更新磁盘卡片"""
        if disk_data['disks']:
            percent = disk_data['disks'][0]['percent']
            self.disk_card.findChild(QLabel, "value_label").setText(f"{percent:.1f}%")
            self.disk_card.findChild(QProgressBar, "progress_bar").setValue(int(percent))
            self.disk_card.findChild(QLabel, "detail_label").setText(
                f"读: {FormatUtils.format_speed(disk_data['read_speed'])} | "
                f"写: {FormatUtils.format_speed(disk_data['write_speed'])}"
            )

    def update_network_card(self, net_data: Dict):
        """更新网络卡片"""
        total_speed = net_data['upload_speed'] + net_data['download_speed']
        self.network_card.findChild(QLabel, "value_label").setText(
            FormatUtils.format_speed(total_speed)
        )
        self.network_card.findChild(QLabel, "detail_label").setText(
            f"↑ {FormatUtils.format_speed(net_data['upload_speed'])} | "
            f"↓ {FormatUtils.format_speed(net_data['download_speed'])}"
        )

    def update_charts(self, data: Dict):
        """更新所有图表"""
        # 添加数据到历史记录
        self.history_data['cpu'].append(data['cpu']['percent'])
        self.history_data['memory'].append(data['memory']['percent'])
        self.history_data['network_up'].append(data['network']['upload_speed'] / 1024)  # KB/s
        self.history_data['network_down'].append(data['network']['download_speed'] / 1024)
        self.history_data['disk_read'].append(data['disk']['read_speed'] / 1024)
        self.history_data['disk_write'].append(data['disk']['write_speed'] / 1024)

        # 更新CPU图表
        self.update_single_chart(self.cpu_chart_view, list(self.history_data['cpu']))

        # 更新内存图表
        self.update_single_chart(self.memory_chart_view, list(self.history_data['memory']))

        # 更新网络图表
        self.upload_series.clear()
        self.download_series.clear()
        for i, (up, down) in enumerate(zip(self.history_data['network_up'],
                                           self.history_data['network_down'])):
            self.upload_series.append(i, up)
            self.download_series.append(i, down)

        # 动态调整Y轴范围
        max_net_speed = max(
            max(self.history_data['network_up'], default=0),
            max(self.history_data['network_down'], default=0)
        )
        if max_net_speed > 0:
            self.network_chart_view.chart().axisY().setRange(0, max(max_net_speed * 1.2, 100))

        # 更新磁盘图表
        self.disk_read_series.clear()
        self.disk_write_series.clear()
        for i, (read, write) in enumerate(zip(self.history_data['disk_read'],
                                              self.history_data['disk_write'])):
            self.disk_read_series.append(i, read)
            self.disk_write_series.append(i, write)

        # 动态调整Y轴范围
        max_disk_speed = max(
            max(self.history_data['disk_read'], default=0),
            max(self.history_data['disk_write'], default=0)
        )
        if max_disk_speed > 0:
            self.disk_chart_view.chart().axisY().setRange(0, max(max_disk_speed * 1.2, 100))

    def update_single_chart(self, chart_view: QChartView, data: List[float]):
        """更新单个图表"""
        series = chart_view.chart().series()[0]
        series.clear()
        for i, value in enumerate(data):
            series.append(i, value)

    def update_system_info(self, info: Dict):
        """更新系统信息"""
        html = f"""
        <h3 style='color: #2c3e50;'>系统信息</h3>
        <table style='width:100%; font-size: 12px;'>
            <tr><td><b>操作系统:</b></td><td>{info.get('platform', 'N/A')} {info.get('platform_release', '')}</td></tr>
            <tr><td><b>主机名:</b></td><td>{info.get('hostname', 'N/A')}</td></tr>
            <tr><td><b>架构:</b></td><td>{info.get('architecture', 'N/A')}</td></tr>
            <tr><td><b>处理器:</b></td><td>{info.get('processor', 'N/A')}</td></tr>
            <tr><td><b>启动时间:</b></td><td>{info.get('boot_time', 'N/A')}</td></tr>
            <tr><td><b>运行时长:</b></td><td>{info.get('uptime', 'N/A')}</td></tr>
        </table>
        """
        self.system_info.setHtml(html)

    def update_realtime_info(self, data: Dict):
        """更新实时信息"""
        html = f"""
        <h3 style='color: #2c3e50;'>实时信息</h3>
        <table style='width:100%; font-size: 12px;'>
            <tr><td><b>网络连接:</b></td><td>{data['network']['connections']['total']} (活跃: {data['network']['connections']['established']})</td></tr>
            <tr><td><b>数据上传:</b></td><td>{FormatUtils.format_bytes(data['network']['bytes_sent'])}</td></tr>
            <tr><td><b>数据下载:</b></td><td>{FormatUtils.format_bytes(data['network']['bytes_recv'])}</td></tr>
            <tr><td><b>磁盘读取:</b></td><td>{FormatUtils.format_bytes(data['disk']['io_read_bytes'])}</td></tr>
            <tr><td><b>磁盘写入:</b></td><td>{FormatUtils.format_bytes(data['disk']['io_write_bytes'])}</td></tr>
            <tr><td><b>时间:</b></td><td>{data['timestamp']}</td></tr>
        </table>
        """
        self.realtime_info.setHtml(html)

    def update_temp_battery_info(self, data: Dict):
        """更新温度和电池信息"""
        html = "<h3 style='color: #2c3e50;'>温度 & 电池</h3>"

        # 温度信息
        temps = data.get('temperature', {})
        if temps:
            html += "<b>温度传感器:</b><br>"
            for sensor, entries in temps.items():
                for entry in entries:
                    html += f"<span style='font-size: 11px;'>{entry['label']}: {entry['current']:.1f}°C</span><br>"
        else:
            html += "<span style='color: #7f8c8d; font-size: 11px;'>无温度传感器数据</span><br>"

        # 电池信息
        battery = data.get('battery')
        if battery:
            html += "<br><b>电池状态:</b><br>"
            html += f"<span style='font-size: 11px;'>电量: {battery['percent']:.1f}%</span><br>"
            html += f"<span style='font-size: 11px;'>充电状态: {'充电中' if battery['power_plugged'] else '未充电'}</span><br>"
            if battery['time_left'] > 0:
                html += f"<span style='font-size: 11px;'>剩余时间: {FormatUtils.format_time(battery['time_left'])}</span><br>"
        else:
            html += "<br><span style='color: #7f8c8d; font-size: 11px;'>无电池</span>"

        self.temp_battery_info.setHtml(html)


# ==================== 进程管理部件 ====================
class ProcessManagerWidget(QWidget):
    """进程管理界面 - 完全重构"""

    def __init__(self, monitor: SystemMonitor, parent=None):
        super().__init__(parent)
        self.monitor = monitor
        self.current_sort = 'cpu'
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 工具栏
        toolbar_layout = QHBoxLayout()

        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索进程名称、PID...")
        self.search_input.textChanged.connect(self.filter_processes)
        toolbar_layout.addWidget(self.search_input)

        # 排序选项
        sort_label = QLabel("排序:")
        toolbar_layout.addWidget(sort_label)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["CPU使用率", "内存使用率", "进程名", "PID"])
        self.sort_combo.currentTextChanged.connect(self.on_sort_changed)
        toolbar_layout.addWidget(self.sort_combo)

        # 按钮
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self.refresh_processes)
        toolbar_layout.addWidget(self.refresh_btn)

        self.details_btn = QPushButton("ℹ️ 详情")
        self.details_btn.clicked.connect(self.show_process_details)
        toolbar_layout.addWidget(self.details_btn)

        self.suspend_btn = QPushButton("⏸️ 挂起")
        self.suspend_btn.clicked.connect(self.suspend_process)
        toolbar_layout.addWidget(self.suspend_btn)

        self.resume_btn = QPushButton("▶️ 恢复")
        self.resume_btn.clicked.connect(self.resume_process)
        toolbar_layout.addWidget(self.resume_btn)

        self.kill_btn = QPushButton("❌ 结束")
        self.kill_btn.clicked.connect(self.kill_process)
        self.kill_btn.setStyleSheet("background-color: #e74c3c;")
        toolbar_layout.addWidget(self.kill_btn)

        toolbar_layout.addStretch()

        layout.addLayout(toolbar_layout)

        # 进程表格
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(8)
        self.process_table.setHorizontalHeaderLabels([
            "PID", "进程名", "CPU (%)", "内存 (%)", "内存 (MB)", "线程数", "状态", "用户"
        ])

        # 设置列宽
        header = self.process_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 进程名自适应
        for i in [0, 2, 3, 4, 5, 6, 7]:
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        self.process_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.process_table.setSelectionMode(QTableWidget.SingleSelection)
        self.process_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.process_table.setSortingEnabled(True)
        self.process_table.setAlternatingRowColors(True)
        self.process_table.doubleClicked.connect(self.show_process_details)

        # 右键菜单
        self.process_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.process_table.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.process_table)

        # 统计信息
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("总进程: 0")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()

        layout.addLayout(stats_layout)

        self.setLayout(layout)
        self.refresh_processes()

    def refresh_processes(self):
        """刷新进程列表"""
        processes = self.monitor.get_process_list(sort_by=self.current_sort)

        self.process_table.setSortingEnabled(False)
        self.process_table.setRowCount(len(processes))

        for i, proc in enumerate(processes):
            self.process_table.setItem(i, 0, QTableWidgetItem(str(proc['pid'])))
            self.process_table.setItem(i, 1, QTableWidgetItem(proc['name']))

            # CPU
            cpu_item = QTableWidgetItem(f"{proc.get('cpu_percent', 0):.1f}")
            cpu_item.setData(Qt.UserRole, proc.get('cpu_percent', 0))
            self.process_table.setItem(i, 2, cpu_item)

            # 内存百分比
            mem_percent_item = QTableWidgetItem(f"{proc.get('memory_percent', 0):.1f}")
            mem_percent_item.setData(Qt.UserRole, proc.get('memory_percent', 0))
            self.process_table.setItem(i, 3, mem_percent_item)

            # 内存MB
            mem_mb = proc.get('memory_mb', 0)
            mem_item = QTableWidgetItem(f"{mem_mb:.1f}")
            mem_item.setData(Qt.UserRole, mem_mb)
            self.process_table.setItem(i, 4, mem_item)

            # 线程数
            self.process_table.setItem(i, 5, QTableWidgetItem(str(proc.get('num_threads', 0))))

            # 状态
            status_item = QTableWidgetItem(proc.get('status', 'unknown'))
            if proc.get('status') == 'running':
                status_item.setForeground(QColor(46, 204, 113))
            elif proc.get('status') == 'sleeping':
                status_item.setForeground(QColor(52, 152, 219))
            self.process_table.setItem(i, 6, status_item)

            # 用户
            self.process_table.setItem(i, 7, QTableWidgetItem(proc.get('username', 'N/A')))

        self.process_table.setSortingEnabled(True)
        self.stats_label.setText(f"总进程: {len(processes)}")

    def filter_processes(self, text: str):
        """过滤进程"""
        for i in range(self.process_table.rowCount()):
            match = False
            for j in range(self.process_table.columnCount()):
                item = self.process_table.item(i, j)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.process_table.setRowHidden(i, not match)

    def on_sort_changed(self, text: str):
        """排序改变"""
        if text == "CPU使用率":
            self.current_sort = 'cpu'
        elif text == "内存使用率":
            self.current_sort = 'memory'
        self.refresh_processes()

    def get_selected_pid(self) -> Optional[int]:
        """获取选中的PID"""
        selected = self.process_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择一个进程")
            return None

        row = selected[0].row()
        return int(self.process_table.item(row, 0).text())

    def show_process_details(self):
        """显示进程详情"""
        pid = self.get_selected_pid()
        if not pid:
            return

        details = self.monitor.get_process_details(pid)
        if not details:
            QMessageBox.warning(self, "错误", "无法获取进程详情")
            return

        dialog = ProcessDetailsDialog(details, self)
        dialog.exec_()

    def kill_process(self):
        """结束进程"""
        pid = self.get_selected_pid()
        if not pid:
            return

        name = self.process_table.item(self.process_table.currentRow(), 1).text()

        reply = QMessageBox.question(
            self, "确认结束进程",
            f"确定要结束进程 {name} (PID: {pid}) 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.monitor.kill_process(pid):
                QMessageBox.information(self, "成功", "进程已结束")
                self.refresh_processes()
            else:
                QMessageBox.critical(self, "错误", "无法结束进程，可能需要管理员权限")

    def suspend_process(self):
        """挂起进程"""
        pid = self.get_selected_pid()
        if not pid:
            return

        if self.monitor.suspend_process(pid):
            QMessageBox.information(self, "成功", "进程已挂起")
            self.refresh_processes()
        else:
            QMessageBox.critical(self, "错误", "无法挂起进程")

    def resume_process(self):
        """恢复进程"""
        pid = self.get_selected_pid()
        if not pid:
            return

        if self.monitor.resume_process(pid):
            QMessageBox.information(self, "成功", "进程已恢复")
            self.refresh_processes()
        else:
            QMessageBox.critical(self, "错误", "无法恢复进程")

    def show_context_menu(self, pos):
        """显示右键菜单"""
        if not self.process_table.selectedItems():
            return

        menu = QMenu(self)

        details_action = menu.addAction("📋 查看详情")
        details_action.triggered.connect(self.show_process_details)

        menu.addSeparator()

        suspend_action = menu.addAction("⏸️ 挂起进程")
        suspend_action.triggered.connect(self.suspend_process)

        resume_action = menu.addAction("▶️ 恢复进程")
        resume_action.triggered.connect(self.resume_process)

        menu.addSeparator()

        kill_action = menu.addAction("❌ 结束进程")
        kill_action.triggered.connect(self.kill_process)

        menu.exec_(self.process_table.viewport().mapToGlobal(pos))


# ==================== 进程详情对话框 ====================
class ProcessDetailsDialog(QDialog):
    """进程详情对话框"""

    def __init__(self, details: Dict, parent=None):
        super().__init__(parent)
        self.details = details
        self.setWindowTitle(f"进程详情 - {details['name']} (PID: {details['pid']})")
        self.setMinimumSize(600, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 详情文本
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        html = f"""
        <h2>{self.details['name']}</h2>
        <table style='width:100%; font-size: 12px;'>
            <tr><td width='30%'><b>进程ID (PID):</b></td><td>{self.details['pid']}</td></tr>
            <tr><td><b>状态:</b></td><td>{self.details['status']}</td></tr>
            <tr><td><b>用户:</b></td><td>{self.details['username']}</td></tr>
            <tr><td><b>创建时间:</b></td><td>{self.details['create_time']}</td></tr>
            <tr><td><b>CPU使用率:</b></td><td>{self.details['cpu_percent']:.2f}%</td></tr>
            <tr><td><b>内存使用率:</b></td><td>{self.details['memory_percent']:.2f}%</td></tr>
            <tr><td><b>内存占用:</b></td><td>{self.details['memory_mb']:.2f} MB</td></tr>
            <tr><td><b>线程数:</b></td><td>{self.details['num_threads']}</td></tr>
            <tr><td><b>可执行文件:</b></td><td>{self.details['exe']}</td></tr>
            <tr><td><b>工作目录:</b></td><td>{self.details['cwd']}</td></tr>
        </table>
        <br>
        <h3>命令行参数:</h3>
        <pre style='background-color: #f5f5f5; padding: 10px; border-radius: 5px;'>{self.details['cmdline']}</pre>
        """

        text_edit.setHtml(html)
        layout.addWidget(text_edit)

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)


# ==================== 网络监控部件 ====================
class NetworkMonitorWidget(QWidget):
    """网络监控界面"""

    def __init__(self, monitor: SystemMonitor, parent=None):
        super().__init__(parent)
        self.monitor = monitor
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 网络接口信息
        interface_group = QGroupBox("📡 网络接口")
        interface_layout = QVBoxLayout()

        self.interface_text = QTextEdit()
        self.interface_text.setReadOnly(True)
        self.interface_text.setMaximumHeight(200)
        interface_layout.addWidget(self.interface_text)

        interface_group.setLayout(interface_layout)
        layout.addWidget(interface_group)

        # 网络连接表格
        connections_group = QGroupBox("🌐 网络连接")
        connections_layout = QVBoxLayout()

        # 工具栏
        toolbar = QHBoxLayout()

        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.refresh_connections)
        toolbar.addWidget(refresh_btn)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部", "已建立 (ESTABLISHED)", "监听 (LISTEN)", "等待 (TIME_WAIT)"])
        self.filter_combo.currentTextChanged.connect(self.filter_connections)
        toolbar.addWidget(self.filter_combo)

        toolbar.addStretch()

        connections_layout.addLayout(toolbar)

        # 连接表格
        self.connections_table = QTableWidget()
        self.connections_table.setColumnCount(5)
        self.connections_table.setHorizontalHeaderLabels([
            "本地地址", "远程地址", "状态", "PID", "进程名"
        ])
        self.connections_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.connections_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.connections_table.setAlternatingRowColors(True)

        connections_layout.addWidget(self.connections_table)

        connections_group.setLayout(connections_layout)
        layout.addWidget(connections_group)

        self.setLayout(layout)
        self.refresh_connections()

    def refresh_connections(self):
        """刷新网络连接"""
        try:
            connections = psutil.net_connections(kind='inet')

            self.connections_table.setRowCount(len(connections))

            for i, conn in enumerate(connections):
                # 本地地址
                local_addr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else ""
                self.connections_table.setItem(i, 0, QTableWidgetItem(local_addr))

                # 远程地址
                remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else ""
                self.connections_table.setItem(i, 1, QTableWidgetItem(remote_addr))

                # 状态
                status_item = QTableWidgetItem(conn.status)
                if conn.status == 'ESTABLISHED':
                    status_item.setForeground(QColor(46, 204, 113))
                elif conn.status == 'LISTEN':
                    status_item.setForeground(QColor(52, 152, 219))
                self.connections_table.setItem(i, 2, status_item)

                # PID和进程名
                if conn.pid:
                    self.connections_table.setItem(i, 3, QTableWidgetItem(str(conn.pid)))
                    try:
                        proc = psutil.Process(conn.pid)
                        self.connections_table.setItem(i, 4, QTableWidgetItem(proc.name()))
                    except:
                        self.connections_table.setItem(i, 4, QTableWidgetItem("N/A"))
                else:
                    self.connections_table.setItem(i, 3, QTableWidgetItem(""))
                    self.connections_table.setItem(i, 4, QTableWidgetItem(""))

        except (psutil.AccessDenied, PermissionError):
            QMessageBox.warning(self, "权限不足", "需要管理员权限才能查看网络连接")

    def filter_connections(self, filter_text: str):
        """过滤连接"""
        for i in range(self.connections_table.rowCount()):
            status_item = self.connections_table.item(i, 2)
            if filter_text == "全部":
                self.connections_table.setRowHidden(i, False)
            else:
                status = status_item.text() if status_item else ""
                self.connections_table.setRowHidden(i, filter_text.split()[0] not in filter_text or status not in filter_text)

    def update_interfaces(self, interfaces: Dict):
        """更新网络接口信息"""
        html = "<h3>网络接口:</h3>"

        for name, addrs in interfaces.items():
            html += f"<b>{name}:</b><br>"
            for addr in addrs:
                html += f"  <span style='font-size: 11px;'>{addr['family']}: {addr['address']}</span><br>"
            html += "<br>"

        self.interface_text.setHtml(html)


# ==================== 日志查看器 ====================
class LogViewerWidget(QWidget):
    """日志查看器 - 增强版"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 工具栏
        toolbar = QHBoxLayout()

        self.log_path_input = QLineEdit()
        self.log_path_input.setPlaceholderText("日志文件路径...")

        # 设置默认日志路径
        if platform.system() == 'Windows':
            default_log = str(Path.home() / "AppData" / "Local" / "Temp")
        else:
            default_log = "/var/log/syslog"
        self.log_path_input.setText(default_log)

        toolbar.addWidget(self.log_path_input)

        browse_btn = QPushButton("📁 浏览")
        browse_btn.clicked.connect(self.browse_log_file)
        toolbar.addWidget(browse_btn)

        load_btn = QPushButton("📄 加载")
        load_btn.clicked.connect(self.load_log_file)
        toolbar.addWidget(load_btn)

        self.auto_refresh_check = QCheckBox("自动刷新")
        self.auto_refresh_check.stateChanged.connect(self.toggle_auto_refresh)
        toolbar.addWidget(self.auto_refresh_check)

        export_btn = QPushButton("💾 导出")
        export_btn.clicked.connect(self.export_log)
        toolbar.addWidget(export_btn)

        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.clicked.connect(self.clear_log)
        toolbar.addWidget(clear_btn)

        layout.addLayout(toolbar)

        # 搜索和过滤
        search_layout = QHBoxLayout()

        self.search_log_input = QLineEdit()
        self.search_log_input.setPlaceholderText("🔍 搜索日志...")
        self.search_log_input.returnPressed.connect(self.search_log)
        search_layout.addWidget(self.search_log_input)

        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self.search_log)
        search_layout.addWidget(search_btn)

        self.level_filter = QComboBox()
        self.level_filter.addItems(["全部级别", "ERROR", "WARN", "INFO", "DEBUG"])
        self.level_filter.currentTextChanged.connect(self.apply_filter)
        search_layout.addWidget(self.level_filter)

        layout.addLayout(search_layout)

        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self.log_text)

        # 状态栏
        status_layout = QHBoxLayout()
        self.status_label = QLabel("就绪")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        self.line_count_label = QLabel("行数: 0")
        status_layout.addWidget(self.line_count_label)

        layout.addLayout(status_layout)

        self.setLayout(layout)

        # 自动刷新定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.reload_log)

    def browse_log_file(self):
        """浏览日志文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择日志文件", "",
            "日志文件 (*.log *.txt);;所有文件 (*.*)"
        )
        if file_path:
            self.log_path_input.setText(file_path)
            self.load_log_file()

    def load_log_file(self):
        """加载日志文件"""
        file_path = self.log_path_input.text()
        if not file_path:
            QMessageBox.warning(self, "警告", "请输入日志文件路径")
            return

        if not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", "文件不存在")
            return

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                self.log_text.setPlainText(content)
                self.current_file = file_path

                line_count = content.count('\n')
                self.line_count_label.setText(f"行数: {line_count}")
                self.status_label.setText(f"已加载: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法读取文件: {e}")

    def reload_log(self):
        """重新加载日志"""
        if self.current_file:
            self.log_path_input.setText(self.current_file)
            self.load_log_file()

    def toggle_auto_refresh(self, state):
        """切换自动刷新"""
        if state == Qt.Checked:
            self.refresh_timer.start(2000)  # 每2秒刷新
            self.status_label.setText("自动刷新已启用")
        else:
            self.refresh_timer.stop()
            self.status_label.setText("自动刷新已禁用")

    def clear_log(self):
        """清空日志显示"""
        self.log_text.clear()
        self.line_count_label.setText("行数: 0")
        self.status_label.setText("日志已清空")

    def search_log(self):
        """搜索日志"""
        text = self.search_log_input.text()
        if not text:
            return

        cursor = self.log_text.textCursor()
        cursor.setPosition(0)
        self.log_text.setTextCursor(cursor)

        if self.log_text.find(text):
            self.status_label.setText(f"找到: {text}")
        else:
            self.status_label.setText(f"未找到: {text}")
            QMessageBox.information(self, "搜索结果", "未找到匹配内容")

    def apply_filter(self, level: str):
        """应用日志级别过滤"""
        if level == "全部级别":
            self.status_label.setText("显示所有日志")
            return

        # 这里可以实现更复杂的过滤逻辑
        self.status_label.setText(f"过滤级别: {level}")

    def export_log(self):
        """导出日志"""
        if not self.log_text.toPlainText():
            QMessageBox.warning(self, "警告", "没有可导出的日志")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出日志", "",
            "文本文件 (*.txt);;日志文件 (*.log);;所有文件 (*.*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "成功", "日志已导出")
                self.status_label.setText(f"已导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")


# ==================== 脚本运行器 ====================
class ScriptRunnerWidget(QWidget):
    """自动化脚本运行器 - 增强版"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_script_templates()

    def init_ui(self):
        layout = QVBoxLayout()

        # 工具栏
        toolbar = QHBoxLayout()

        toolbar.addWidget(QLabel("脚本模板:"))

        self.script_combo = QComboBox()
        self.script_combo.currentTextChanged.connect(self.load_template)
        toolbar.addWidget(self.script_combo, 1)

        run_btn = QPushButton("▶️ 运行")
        run_btn.clicked.connect(self.run_script)
        run_btn.setStyleSheet("background-color: #27ae60; font-weight: bold;")
        toolbar.addWidget(run_btn)

        stop_btn = QPushButton("⏹️ 停止")
        stop_btn.clicked.connect(self.stop_script)
        toolbar.addWidget(stop_btn)

        save_btn = QPushButton("💾 保存")
        save_btn.clicked.connect(self.save_script)
        toolbar.addWidget(save_btn)

        load_btn = QPushButton("📂 加载")
        load_btn.clicked.connect(self.load_script)
        toolbar.addWidget(load_btn)

        layout.addLayout(toolbar)

        # 分割器
        splitter = QSplitter(Qt.Vertical)

        # 脚本编辑器
        editor_group = QGroupBox("📝 脚本编辑器")
        editor_layout = QVBoxLayout()

        self.script_editor = QTextEdit()
        self.script_editor.setFont(QFont("Consolas", 10))
        self.script_editor.setPlaceholderText("在此输入脚本命令...\n\n提示:\n- 以 # 开头的行为注释\n- 每行一个命令\n- 支持系统命令")
        self.script_editor.setLineWrapMode(QTextEdit.NoWrap)
        editor_layout.addWidget(self.script_editor)

        editor_group.setLayout(editor_layout)
        splitter.addWidget(editor_group)

        # 输出区域
        output_group = QGroupBox("📤 执行输出")
        output_layout = QVBoxLayout()

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 9))
        output_layout.addWidget(self.output_text)

        output_group.setLayout(output_layout)
        splitter.addWidget(output_group)

        splitter.setSizes([300, 300])
        layout.addWidget(splitter)

        self.setLayout(layout)

        self.running_process = None

    def load_script_templates(self):
        """加载脚本模板"""
        if platform.system() == 'Windows':
            templates = {
                "系统清理": (
                    "# Windows 系统清理脚本\n"
                    "echo 开始清理系统...\n"
                    "del /q /f /s %TEMP%\\*\n"
                    "echo 临时文件已清理\n"
                    "cleanmgr /sagerun:1\n"
                    "echo 清理完成"
                ),
                "磁盘检查": (
                    "# Windows 磁盘检查\n"
                    "chkdsk C: /F\n"
                    "echo 磁盘检查完成"
                ),
                "网络诊断": (
                    "# Windows 网络诊断\n"
                    "ipconfig /all\n"
                    "ping -n 5 8.8.8.8\n"
                    "tracert google.com\n"
                    "netstat -ano"
                ),
                "系统信息": (
                    "# Windows 系统信息\n"
                    "systeminfo\n"
                    "wmic cpu get name\n"
                    "wmic memorychip get capacity"
                )
            }
        else:
            templates = {
                "系统清理": (
                    "# Linux 系统清理脚本\n"
                    "echo '开始清理系统...'\n"
                    "sudo apt-get clean\n"
                    "sudo apt-get autoclean\n"
                    "rm -rf ~/.cache/*\n"
                    "echo '清理完成'"
                ),
                "磁盘检查": (
                    "# Linux 磁盘检查\n"
                    "df -h\n"
                    "du -sh /*\n"
                    "sudo fsck -A"
                ),
                "网络诊断": (
                    "# Linux 网络诊断\n"
                    "ifconfig\n"
                    "ping -c 5 8.8.8.8\n"
                    "traceroute google.com\n"
                    "netstat -tulpn"
                ),
                "系统信息": (
                    "# Linux 系统信息\n"
                    "uname -a\n"
                    "lsb_release -a\n"
                    "cat /proc/cpuinfo | grep 'model name'\n"
                    "free -h"
                ),
                "进程管理": (
                    "# Linux 进程管理\n"
                    "ps aux --sort=-%cpu | head -20\n"
                    "ps aux --sort=-%mem | head -20"
                )
            }

        self.templates = templates
        self.script_combo.addItems(list(templates.keys()) + ["自定义脚本"])

    def load_template(self, template_name: str):
        """加载模板"""
        if template_name in self.templates:
            self.script_editor.setPlainText(self.templates[template_name])

    def run_script(self):
        """运行脚本"""
        script = self.script_editor.toPlainText()
        if not script.strip():
            QMessageBox.warning(self, "警告", "脚本内容为空")
            return

        self.output_text.clear()
        self.output_text.append("=" * 60)
        self.output_text.append(f">>> 开始执行脚本 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.output_text.append("=" * 60)
        self.output_text.append("")

        try:
            # 按行执行命令
            for line in script.split('\n'):
                line = line.strip()

                # 跳过空行和注释
                if not line or line.startswith('#'):
                    if line.startswith('#'):
                        self.output_text.append(f"<span style='color: #7f8c8d;'>{line}</span>")
                    continue

                self.output_text.append(f"<b style='color: #2c3e50;'>$ {line}</b>")
                QApplication.processEvents()  # 更新UI

                try:
                    result = subprocess.run(
                        line,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.stdout:
                        self.output_text.append(result.stdout)
                    if result.stderr:
                        self.output_text.append(f"<span style='color: #e74c3c;'>ERROR: {result.stderr}</span>")

                    self.output_text.append("")

                except subprocess.TimeoutExpired:
                    self.output_text.append("<span style='color: #e74c3c;'>ERROR: 命令执行超时</span>")
                    self.output_text.append("")

            self.output_text.append("=" * 60)
            self.output_text.append(">>> 脚本执行完成")
            self.output_text.append("=" * 60)

        except Exception as e:
            self.output_text.append(f"<span style='color: #e74c3c;'>ERROR: {str(e)}</span>")

    def stop_script(self):
        """停止脚本执行"""
        if self.running_process:
            self.running_process.terminate()
            self.output_text.append("\n<span style='color: #e67e22;'>脚本已被用户终止</span>")

    def save_script(self):
        """保存脚本"""
        if not self.script_editor.toPlainText():
            QMessageBox.warning(self, "警告", "脚本内容为空")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存脚本", "",
            "批处理文件 (*.bat);;Shell脚本 (*.sh);;文本文件 (*.txt);;所有文件 (*.*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.script_editor.toPlainText())
                QMessageBox.information(self, "成功", "脚本已保存")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def load_script(self):
        """加载脚本"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "加载脚本", "",
            "脚本文件 (*.bat *.sh *.txt);;所有文件 (*.*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.script_editor.setPlainText(f.read())
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载失败: {e}")


# ==================== 设置对话框 ====================
class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("⚙️ 设置")
        self.setMinimumSize(500, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 标签页
        tabs = QTabWidget()

        # 常规设置
        general_widget = QWidget()
        general_layout = QFormLayout()

        self.monitor_interval_spin = QSpinBox()
        self.monitor_interval_spin.setRange(500, 10000)
        self.monitor_interval_spin.setSuffix(" ms")
        self.monitor_interval_spin.setValue(self.config.monitor_interval)
        general_layout.addRow("监控刷新间隔:", self.monitor_interval_spin)

        self.process_refresh_spin = QSpinBox()
        self.process_refresh_spin.setRange(1000, 60000)
        self.process_refresh_spin.setSuffix(" ms")
        self.process_refresh_spin.setValue(self.config.process_refresh_interval)
        general_layout.addRow("进程刷新间隔:", self.process_refresh_spin)

        self.history_length_spin = QSpinBox()
        self.history_length_spin.setRange(30, 300)
        self.history_length_spin.setValue(self.config.history_length)
        general_layout.addRow("历史数据长度:", self.history_length_spin)

        general_widget.setLayout(general_layout)
        tabs.addTab(general_widget, "常规")

        # 警报设置
        alert_widget = QWidget()
        alert_layout = QFormLayout()

        self.enable_alerts_check = QCheckBox("启用警报")
        self.enable_alerts_check.setChecked(self.config.enable_alerts)
        alert_layout.addRow("", self.enable_alerts_check)

        self.cpu_threshold_spin = QDoubleSpinBox()
        self.cpu_threshold_spin.setRange(0, 100)
        self.cpu_threshold_spin.setSuffix(" %")
        self.cpu_threshold_spin.setValue(self.config.cpu_threshold)
        alert_layout.addRow("CPU警报阈值:", self.cpu_threshold_spin)

        self.memory_threshold_spin = QDoubleSpinBox()
        self.memory_threshold_spin.setRange(0, 100)
        self.memory_threshold_spin.setSuffix(" %")
        self.memory_threshold_spin.setValue(self.config.memory_threshold)
        alert_layout.addRow("内存警报阈值:", self.memory_threshold_spin)

        self.disk_threshold_spin = QDoubleSpinBox()
        self.disk_threshold_spin.setRange(0, 100)
        self.disk_threshold_spin.setSuffix(" %")
        self.disk_threshold_spin.setValue(self.config.disk_threshold)
        alert_layout.addRow("磁盘警报阈值:", self.disk_threshold_spin)

        alert_widget.setLayout(alert_layout)
        tabs.addTab(alert_widget, "警报")

        # 主题设置
        theme_widget = QWidget()
        theme_layout = QVBoxLayout()

        theme_group = QButtonGroup(self)

        self.light_theme_radio = QRadioButton("浅色主题")
        self.dark_theme_radio = QRadioButton("深色主题")

        if self.config.theme == 'light':
            self.light_theme_radio.setChecked(True)
        else:
            self.dark_theme_radio.setChecked(True)

        theme_group.addButton(self.light_theme_radio)
        theme_group.addButton(self.dark_theme_radio)

        theme_layout.addWidget(self.light_theme_radio)
        theme_layout.addWidget(self.dark_theme_radio)
        theme_layout.addStretch()

        theme_widget.setLayout(theme_layout)
        tabs.addTab(theme_widget, "主题")

        layout.addWidget(tabs)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self.save_and_close)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)

        layout.addWidget(button_box)

        self.setLayout(layout)

    def apply_settings(self):
        """应用设置"""
        self.config.monitor_interval = self.monitor_interval_spin.value()
        self.config.process_refresh_interval = self.process_refresh_spin.value()
        self.config.history_length = self.history_length_spin.value()
        self.config.enable_alerts = self.enable_alerts_check.isChecked()
        self.config.cpu_threshold = self.cpu_threshold_spin.value()
        self.config.memory_threshold = self.memory_threshold_spin.value()
        self.config.disk_threshold = self.disk_threshold_spin.value()

        if self.light_theme_radio.isChecked():
            self.config.theme = 'light'
        else:
            self.config.theme = 'dark'

        self.config.save()

    def save_and_close(self):
        """保存并关闭"""
        self.apply_settings()
        self.accept()


# ==================== 主窗口 ====================
class MainWindow(QMainWindow):
    """主窗口 - 完全重构"""

    def __init__(self):
        super().__init__()
        self.config = Config()
        self.monitor = SystemMonitor()
        self.init_ui()
        self.setup_system_tray()
        self.start_monitoring()
        self.apply_theme()

    def init_ui(self):
        self.setWindowTitle("SystemMonitorPro v2.0 - 专业系统监控工具")
        self.setGeometry(50, 50, 1400, 900)

        # 菜单栏
        self.create_menu_bar()

        # 工具栏
        self.create_toolbar()

        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        # 标签页
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # 仪表盘
        self.dashboard_widget = DashboardWidget(self.config)
        self.tabs.addTab(self.dashboard_widget, "📊 仪表盘")

        # 进程管理
        self.process_widget = ProcessManagerWidget(self.monitor)
        self.tabs.addTab(self.process_widget, "⚙️ 进程管理")

        # 网络监控
        self.network_widget = NetworkMonitorWidget(self.monitor)
        self.tabs.addTab(self.network_widget, "🌐 网络监控")

        # 日志查看
        self.log_widget = LogViewerWidget()
        self.tabs.addTab(self.log_widget, "📄 日志查看")

        # 脚本运行
        self.script_widget = ScriptRunnerWidget()
        self.tabs.addTab(self.script_widget, "🔧 自动化脚本")

        layout.addWidget(self.tabs)
        central_widget.setLayout(layout)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_cpu = QLabel("CPU: 0%")
        self.status_memory = QLabel("内存: 0%")
        self.status_network = QLabel("网络: 0 KB/s")

        self.status_bar.addPermanentWidget(self.status_cpu)
        self.status_bar.addPermanentWidget(self.status_memory)
        self.status_bar.addPermanentWidget(self.status_network)

        self.status_bar.showMessage("系统监控运行中...")

        # 初始化系统信息
        system_info = self.monitor.get_system_info()
        self.dashboard_widget.update_system_info(system_info)

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        export_action = QAction("📊 导出报告", self)
        export_action.triggered.connect(self.export_report)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("❌ 退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图")

        refresh_action = QAction("🔄 刷新", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_all)
        view_menu.addAction(refresh_action)

        # 工具菜单
        tools_menu = menubar.addMenu("工具")

        settings_action = QAction("⚙️ 设置", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        about_action = QAction("ℹ️ 关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        refresh_action = QAction("🔄", self)
        refresh_action.setToolTip("刷新 (F5)")
        refresh_action.triggered.connect(self.refresh_all)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        export_action = QAction("📊", self)
        export_action.setToolTip("导出报告")
        export_action.triggered.connect(self.export_report)
        toolbar.addAction(export_action)

        toolbar.addSeparator()

        settings_action = QAction("⚙️", self)
        settings_action.setToolTip("设置")
        settings_action.triggered.connect(self.show_settings)
        toolbar.addAction(settings_action)

        toolbar.addSeparator()

        # 主题切换
        theme_action = QAction("🌙", self)
        theme_action.setToolTip("切换主题")
        theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(theme_action)

    def setup_system_tray(self):
        """设置系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)

        # 创建托盘菜单
        tray_menu = QMenu()

        show_action = tray_menu.addAction("显示主窗口")
        show_action.triggered.connect(self.show)

        hide_action = tray_menu.addAction("隐藏窗口")
        hide_action.triggered.connect(self.hide)

        tray_menu.addSeparator()

        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self.quit_application)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)

        # 设置图标（这里使用简单的占位符）
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(52, 152, 219))
        self.tray_icon.setIcon(QIcon(pixmap))

        self.tray_icon.show()

    def on_tray_activated(self, reason):
        """托盘图标激活"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()

    def start_monitoring(self):
        """启动监控"""
        # 监控线程
        self.monitor_thread = MonitorThread(self.config)
        self.monitor_thread.update_signal.connect(self.update_dashboard)
        self.monitor_thread.alert_signal.connect(self.show_alert)
        self.monitor_thread.start()

        # 进程刷新定时器
        self.process_timer = QTimer()
        self.process_timer.timeout.connect(self.process_widget.refresh_processes)
        self.process_timer.start(self.config.process_refresh_interval)

    def update_dashboard(self, data: Dict):
        """更新仪表盘"""
        self.dashboard_widget.update_data(data)

        # 更新网络接口
        if data.get('network', {}).get('interfaces'):
            self.network_widget.update_interfaces(data['network']['interfaces'])

        # 更新状态栏
        cpu = data['cpu']['percent']
        mem = data['memory']['percent']
        net_speed = data['network']['upload_speed'] + data['network']['download_speed']

        self.status_cpu.setText(f"CPU: {cpu:.1f}%")
        self.status_memory.setText(f"内存: {mem:.1f}%")
        self.status_network.setText(f"网络: {FormatUtils.format_speed(net_speed)}")

    def show_alert(self, alert_type: str, message: str):
        """显示警报"""
        self.tray_icon.showMessage(
            f"系统警报 - {alert_type}",
            message,
            QSystemTrayIcon.Warning,
            3000
        )

    def refresh_all(self):
        """刷新所有数据"""
        self.process_widget.refresh_processes()
        self.network_widget.refresh_connections()
        self.status_bar.showMessage("数据已刷新", 2000)

    def show_settings(self):
        """显示设置"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_() == QDialog.Accepted:
            # 应用新配置
            self.monitor_thread.config = self.config
            self.process_timer.setInterval(self.config.process_refresh_interval)
            self.apply_theme()
            QMessageBox.information(self, "成功", "设置已保存")

    def toggle_theme(self):
        """切换主题"""
        if self.config.theme == 'light':
            self.config.theme = 'dark'
        else:
            self.config.theme = 'light'
        self.config.save()
        self.apply_theme()

    def apply_theme(self):
        """应用主题"""
        if self.config.theme == 'dark':
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2c3e50;
                    color: #ecf0f1;
                }
                QWidget {
                    background-color: #34495e;
                    color: #ecf0f1;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #7f8c8d;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 15px;
                }
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 8px 15px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QTableWidget {
                    gridline-color: #7f8c8d;
                    background-color: #2c3e50;
                    alternate-background-color: #34495e;
                }
                QHeaderView::section {
                    background-color: #1abc9c;
                    color: white;
                    padding: 5px;
                    border: none;
                    font-weight: bold;
                }
                QTextEdit, QLineEdit {
                    border: 1px solid #7f8c8d;
                    border-radius: 4px;
                    background-color: #2c3e50;
                    color: #ecf0f1;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f5f5f5;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #cccccc;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 15px;
                }
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 8px 15px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #21618c;
                }
                QTableWidget {
                    gridline-color: #d0d0d0;
                    background-color: white;
                    alternate-background-color: #f9f9f9;
                }
                QTableWidget::item:selected {
                    background-color: #3498db;
                    color: white;
                }
                QHeaderView::section {
                    background-color: #34495e;
                    color: white;
                    padding: 5px;
                    border: none;
                    font-weight: bold;
                }
                QTextEdit, QLineEdit {
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    background-color: white;
                }
            """)

    def export_report(self):
        """导出报告"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出报告", "",
            "CSV文件 (*.csv);;JSON文件 (*.json);;文本文件 (*.txt)"
        )

        if not file_path:
            return

        try:
            # 获取当前数据
            cpu_info = self.monitor.get_cpu_info()
            memory_info = self.monitor.get_memory_info()
            disk_info = self.monitor.get_disk_info()
            network_info = self.monitor.get_network_info()
            system_info = self.monitor.get_system_info()

            if file_path.endswith('.json'):
                # JSON格式
                report = {
                    'timestamp': datetime.now().isoformat(),
                    'system': system_info,
                    'cpu': cpu_info,
                    'memory': memory_info,
                    'disk': disk_info,
                    'network': network_info
                }

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)

            elif file_path.endswith('.csv'):
                # CSV格式
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['类别', '项目', '值'])

                    writer.writerow(['系统', '操作系统', system_info.get('platform', 'N/A')])
                    writer.writerow(['系统', '主机名', system_info.get('hostname', 'N/A')])
                    writer.writerow(['CPU', '使用率', f"{cpu_info['percent']}%"])
                    writer.writerow(['CPU', '核心数', cpu_info['count_logical']])
                    writer.writerow(['内存', '使用率', f"{memory_info['percent']}%"])
                    writer.writerow(['内存', '总容量', FormatUtils.format_bytes(memory_info['total'])])
                    writer.writerow(['内存', '已用', FormatUtils.format_bytes(memory_info['used'])])

            else:
                # 文本格式
                report = f"""
SystemMonitorPro 系统报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*60}
系统信息
{'='*60}
操作系统: {system_info.get('platform', 'N/A')} {system_info.get('platform_release', '')}
主机名: {system_info.get('hostname', 'N/A')}
架构: {system_info.get('architecture', 'N/A')}
处理器: {system_info.get('processor', 'N/A')}
启动时间: {system_info.get('boot_time', 'N/A')}
运行时长: {system_info.get('uptime', 'N/A')}

{'='*60}
CPU信息
{'='*60}
使用率: {cpu_info['percent']:.2f}%
核心数 (逻辑): {cpu_info['count_logical']}
核心数 (物理): {cpu_info['count_physical']}
频率: {cpu_info['freq_current']:.0f} MHz

{'='*60}
内存信息
{'='*60}
总容量: {FormatUtils.format_bytes(memory_info['total'])}
已用: {FormatUtils.format_bytes(memory_info['used'])}
可用: {FormatUtils.format_bytes(memory_info['available'])}
使用率: {memory_info['percent']:.2f}%

{'='*60}
磁盘信息
{'='*60}
"""
                for disk in disk_info['disks']:
                    report += f"\n{disk['mountpoint']} ({disk['device']})\n"
                    report += f"  文件系统: {disk['fstype']}\n"
                    report += f"  总容量: {FormatUtils.format_bytes(disk['total'])}\n"
                    report += f"  已用: {FormatUtils.format_bytes(disk['used'])}\n"
                    report += f"  可用: {FormatUtils.format_bytes(disk['free'])}\n"
                    report += f"  使用率: {disk['percent']:.2f}%\n"

                report += f"""
{'='*60}
网络信息
{'='*60}
上传速度: {FormatUtils.format_speed(network_info['upload_speed'])}
下载速度: {FormatUtils.format_speed(network_info['download_speed'])}
总发送: {FormatUtils.format_bytes(network_info['bytes_sent'])}
总接收: {FormatUtils.format_bytes(network_info['bytes_recv'])}
连接数: {network_info['connections']['total']}
"""

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report)

            QMessageBox.information(self, "成功", f"报告已导出到:\n{file_path}")
            self.status_bar.showMessage("报告导出成功", 3000)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出报告失败: {e}")

    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h2>SystemMonitorPro v2.0</h2>
        <p><b>专业系统监控工具</b></p>
        <p>功能特性:</p>
        <ul>
            <li>实时系统监控（CPU、内存、磁盘、网络）</li>
            <li>高级进程管理</li>
            <li>网络连接监控</li>
            <li>日志查看器</li>
            <li>自动化脚本运行器</li>
            <li>性能警报系统</li>
            <li>数据导出功能</li>
            <li>深色/浅色主题</li>
        </ul>
        <p><b>技术栈:</b> Python 3, PyQt5, psutil</p>
        <p><b>作者:</b> AI Assistant</p>
        <p><b>日期:</b> 2025-12-12</p>
        """

        QMessageBox.about(self, "关于 SystemMonitorPro", about_text)

    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(
            self, '确认退出',
            "确定要退出系统监控工具吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.quit_application()
            event.accept()
        else:
            event.ignore()

    def quit_application(self):
        """退出应用"""
        self.monitor_thread.stop()
        self.monitor_thread.wait()
        self.tray_icon.hide()
        QApplication.quit()


# ==================== 主函数 ====================
def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName('SystemMonitorPro')
    app.setApplicationVersion('2.0')

    # 设置应用图标（可选）
    # app.setWindowIcon(QIcon('icon.png'))

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()