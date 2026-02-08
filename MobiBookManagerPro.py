"""
Mobi电子书管理器 - PyQt5版本
功能: 扫描、分析、管理Mobi电子书
版本: 2.0
github网址：https://github.com/lyp0746
QQ邮箱：1610369302@qq.com
作者：LYP
"""

import os
import re
import sys
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QTableWidget,
    QTableWidgetItem, QTabWidget, QProgressBar, QMessageBox,
    QTextEdit, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QGroupBox, QSplitter, QMenu, QAction, QStatusBar,
    QToolBar, QDialog, QDialogButtonBox, QCheckBox, QComboBox
)
from PyQt5.QtCore import (
    QThread, pyqtSignal, Qt, QTimer
)
from PyQt5.QtGui import QIcon, QFont, QColor


# ============================================================
# 核心业务逻辑类
# ============================================================

class MobiMetadataExtractor:
    """Mobi元数据提取器"""

    @staticmethod
    def extract_metadata(file_path: str) -> Optional[Dict[str, str]]:
        """提取mobi文件元数据"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(78)

                if header[60:68] != b'BOOKMOBI':
                    return None

                f.seek(0)
                content = f.read(10000)

                metadata = {}
                exth_pos = content.find(b'EXTH')
                if exth_pos != -1:
                    metadata = MobiMetadataExtractor._parse_exth(content[exth_pos:])

                return metadata

        except Exception as e:
            return None

    @staticmethod
    def _parse_exth(exth_data: bytes) -> Dict[str, Optional[str]]:
        """解析EXTH记录"""
        metadata = {
            'title': None,
            'author': None,
            'publisher': None,
            'subject': None,
            'description': None,
            'asin': None
        }

        try:
            record_types = {
                100: 'author',
                101: 'publisher',
                103: 'description',
                105: 'subject',
                113: 'asin',
                503: 'title',
                518: 'title'
            }

            pos = 12
            if len(exth_data) < pos:
                return metadata

            record_count = int.from_bytes(exth_data[8:12], 'big')

            for _ in range(min(record_count, 100)):
                if pos + 8 > len(exth_data):
                    break

                record_type = int.from_bytes(exth_data[pos:pos + 4], 'big')
                record_length = int.from_bytes(exth_data[pos + 4:pos + 8], 'big')

                if pos + record_length > len(exth_data):
                    break

                if record_type in record_types:
                    try:
                        value = exth_data[pos + 8:pos + record_length].decode('utf-8', errors='ignore').strip('\x00')
                        field_name = record_types[record_type]
                        if not metadata[field_name]:
                            metadata[field_name] = value
                    except:
                        pass

                pos += record_length

        except Exception:
            pass

        return metadata


class BookAnalyzer:
    """书籍分析器"""

    @staticmethod
    def clean_book_name(name: str) -> str:
        """清理书名"""
        if not name:
            return ""

        patterns = [
            r'\s*\([^)]*\)\s*$',
            r'\s*\[[^\]]*\]\s*$',
            r'\s*【[^】]*】\s*$',
            r'\s*[-_]\s*\d+\s*$',
        ]

        cleaned = name
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned)

        return cleaned.strip()

    @staticmethod
    def is_title_mismatch(filename: str, title: str, threshold: float = 0.3) -> bool:
        """判断文件名和标题是否不一致"""
        if not title or title == '未知':
            return False

        clean_filename = Path(filename).stem
        clean_filename = BookAnalyzer.clean_book_name(clean_filename)
        clean_title = BookAnalyzer.clean_book_name(title)

        fn_lower = clean_filename.lower()
        title_lower = clean_title.lower()

        if fn_lower == title_lower:
            return False

        if fn_lower in title_lower or title_lower in fn_lower:
            return False

        fn_words = set(re.findall(r'\w+', fn_lower))
        title_words = set(re.findall(r'\w+', title_lower))

        if fn_words and title_words:
            overlap = len(fn_words & title_words) / max(len(fn_words), len(title_words))
            if overlap > threshold:
                return False

        return True


class ScanWorker(QThread):
    """扫描工作线程"""

    progress_update = pyqtSignal(int, int, str)  # current, total, filename
    scan_complete = pyqtSignal(dict, list, list)  # duplicates, mismatched, failed
    scan_error = pyqtSignal(str)

    def __init__(self, directory: str):
        super().__init__()
        self.directory = directory
        self.book_info = defaultdict(list)
        self.mismatched_books = []
        self.failed_files = []

    def run(self):
        """执行扫描"""
        try:
            mobi_files = list(Path(self.directory).rglob("*.mobi"))
            total = len(mobi_files)

            for idx, file_path in enumerate(mobi_files, 1):
                self.progress_update.emit(idx, total, file_path.name)
                self._process_file(file_path)

            duplicates = {name: info for name, info in self.book_info.items() if len(info) > 1}

            self.scan_complete.emit(duplicates, self.mismatched_books, self.failed_files)

        except Exception as e:
            self.scan_error.emit(str(e))

    def _process_file(self, file_path: Path):
        """处理单个文件"""
        file_size = os.path.getsize(file_path) / (1024 * 1024)

        metadata = MobiMetadataExtractor.extract_metadata(str(file_path))

        if metadata and metadata.get('title'):
            book_name = metadata['title']
            author = metadata.get('author', '未知')
            publisher = metadata.get('publisher', '未知')

            if BookAnalyzer.is_title_mismatch(file_path.name, book_name):
                self.mismatched_books.append({
                    'filename': file_path.name,
                    'title': book_name,
                    'author': author,
                    'path': str(file_path),
                    'size_mb': file_size
                })
        else:
            book_name = file_path.stem
            author = '未知'
            publisher = '未知'
            self.failed_files.append(str(file_path))

        cleaned_name = BookAnalyzer.clean_book_name(book_name)

        self.book_info[cleaned_name].append({
            'path': str(file_path),
            'original_name': book_name,
            'filename': file_path.name,
            'author': author,
            'publisher': publisher,
            'size_mb': file_size
        })


# ============================================================
# PyQt5 GUI界面
# ============================================================

class BookListExportDialog(QDialog):
    """书籍列表导出对话框"""

    def __init__(self, book_info: Dict, parent=None):
        super().__init__(parent)
        self.book_info = book_info
        self.setWindowTitle("导出书籍名称")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # 选项
        options_group = QGroupBox("导出选项")
        options_layout = QVBoxLayout()

        self.include_author_cb = QCheckBox("包含作者信息")
        self.include_author_cb.setChecked(True)

        self.include_count_cb = QCheckBox("包含文件数量")
        self.include_count_cb.setChecked(False)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["按书名排序", "按作者排序"])

        options_layout.addWidget(QLabel("排序方式:"))
        options_layout.addWidget(self.sort_combo)
        options_layout.addWidget(self.include_author_cb)
        options_layout.addWidget(self.include_count_cb)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_export_options(self):
        """获取导出选项"""
        return {
            'include_author': self.include_author_cb.isChecked(),
            'include_count': self.include_count_cb.isChecked(),
            'sort_by': self.sort_combo.currentIndex()
        }


class StatisticsWidget(QWidget):
    """统计信息显示组件"""

    def __init__(self):
        super().__init__()
        self.stat_labels = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        stats = [
            ('总文件数', 'total', '#2196F3'),
            ('唯一书名', 'unique', '#4CAF50'),
            ('重名书籍', 'duplicate', '#FF9800'),
            ('名称不一致', 'mismatch', '#9C27B0'),
            ('读取失败', 'failed', '#F44336')
        ]

        for label, key, color in stats:
            frame = QWidget()
            frame_layout = QVBoxLayout()
            frame_layout.setContentsMargins(10, 5, 10, 5)

            title_label = QLabel(label)
            title_label.setStyleSheet(f"color: gray; font-size: 12px;")

            value_label = QLabel("0")
            value_label.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
            value_label.setAlignment(Qt.AlignCenter)

            frame_layout.addWidget(title_label)
            frame_layout.addWidget(value_label)
            frame.setLayout(frame_layout)

            layout.addWidget(frame)
            self.stat_labels[key] = value_label

        self.setLayout(layout)

    def update_stats(self, stats: Dict):
        """更新统计信息"""
        for key, value in stats.items():
            if key in self.stat_labels:
                self.stat_labels[key].setText(str(value))


class MobiBookManagerWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.directory = None
        self.duplicates = {}
        self.mismatched = []
        self.failed = []
        self.all_books = {}  # 存储所有书籍信息

        self.setup_ui()
        self.setup_connections()
        self.apply_styles()

    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("📚 Mobi电子书管理器 v2.0 - PyQt5")
        self.setGeometry(100, 100, 1400, 900)

        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 工具栏
        self.create_toolbar()

        # 目录选择区域
        dir_widget = self.create_directory_selector()
        main_layout.addWidget(dir_widget)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_label = QLabel("就绪")

        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.progress_bar, 4)
        progress_layout.addWidget(self.progress_label, 1)
        main_layout.addLayout(progress_layout)

        # 统计信息
        self.stats_widget = StatisticsWidget()
        main_layout.addWidget(self.stats_widget)

        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)

        # 创建各个标签页
        self.duplicate_tab = self.create_duplicate_tab()
        self.mismatch_tab = self.create_mismatch_tab()
        self.failed_tab = self.create_failed_tab()
        self.all_books_tab = self.create_all_books_tab()

        self.tab_widget.addTab(self.all_books_tab, "📚 所有书籍")
        self.tab_widget.addTab(self.duplicate_tab, "🔄 重名书籍")
        self.tab_widget.addTab(self.mismatch_tab, "⚠️ 名称不一致")
        self.tab_widget.addTab(self.failed_tab, "❌ 读取失败")

        main_layout.addWidget(self.tab_widget)

        # 底部按钮栏
        button_widget = self.create_button_bar()
        main_layout.addWidget(button_widget)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("准备就绪")

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # 扫描动作
        scan_action = QAction("🔍 开始扫描", self)
        scan_action.triggered.connect(self.start_scan)
        toolbar.addAction(scan_action)

        toolbar.addSeparator()

        # 导出动作
        export_action = QAction("📄 导出报告", self)
        export_action.triggered.connect(self.export_full_report)
        toolbar.addAction(export_action)

        # 导出书籍名称
        export_books_action = QAction("📋 导出书名", self)
        export_books_action.triggered.connect(self.export_book_names)
        toolbar.addAction(export_books_action)

        toolbar.addSeparator()

        # 帮助
        help_action = QAction("❓ 帮助", self)
        help_action.triggered.connect(self.show_help)
        toolbar.addAction(help_action)

    def create_directory_selector(self):
        """创建目录选择器"""
        widget = QGroupBox("扫描目录")
        layout = QHBoxLayout()

        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("请选择Mobi电子书所在目录...")

        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_directory)

        scan_btn = QPushButton("🔍 开始扫描")
        scan_btn.clicked.connect(self.start_scan)
        scan_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

        layout.addWidget(QLabel("目录:"))
        layout.addWidget(self.dir_input, 3)
        layout.addWidget(browse_btn)
        layout.addWidget(scan_btn)

        widget.setLayout(layout)
        return widget

    def create_all_books_tab(self):
        """创建所有书籍标签页"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 搜索栏
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        self.all_books_search = QLineEdit()
        self.all_books_search.setPlaceholderText("输入书名或作者...")
        self.all_books_search.textChanged.connect(self.filter_all_books)
        search_layout.addWidget(self.all_books_search)
        layout.addLayout(search_layout)

        # 树形视图
        self.all_books_tree = QTreeWidget()
        self.all_books_tree.setHeaderLabels(['书名', '作者', '出版社', '文件数', '总大小(MB)'])
        self.all_books_tree.setColumnWidth(0, 300)
        self.all_books_tree.setColumnWidth(1, 150)
        self.all_books_tree.setColumnWidth(2, 150)
        self.all_books_tree.setSortingEnabled(True)
        self.all_books_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.all_books_tree.customContextMenuRequested.connect(self.show_all_books_context_menu)

        layout.addWidget(self.all_books_tree)
        widget.setLayout(layout)
        return widget

    def create_duplicate_tab(self):
        """创建重名书籍标签页"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 搜索栏
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        self.dup_search = QLineEdit()
        self.dup_search.setPlaceholderText("输入书名进行筛选...")
        self.dup_search.textChanged.connect(self.filter_duplicates)
        search_layout.addWidget(self.dup_search)
        layout.addLayout(search_layout)

        # 树形视图
        self.duplicate_tree = QTreeWidget()
        self.duplicate_tree.setHeaderLabels(['书名/文件', '文件名', '作者', '大小(MB)', '路径'])
        self.duplicate_tree.setColumnWidth(0, 300)
        self.duplicate_tree.setColumnWidth(1, 200)
        self.duplicate_tree.setColumnWidth(2, 150)
        self.duplicate_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.duplicate_tree.customContextMenuRequested.connect(self.show_duplicate_context_menu)

        layout.addWidget(self.duplicate_tree)
        widget.setLayout(layout)
        return widget

    def create_mismatch_tab(self):
        """创建名称不一致标签页"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 提示
        info_label = QLabel("💡 以下书籍的文件名与内部标题不一致，可能需要重命名")
        info_label.setStyleSheet("color: #FF9800; padding: 5px;")
        layout.addWidget(info_label)

        # 搜索栏
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        self.mis_search = QLineEdit()
        self.mis_search.setPlaceholderText("输入文件名或标题...")
        self.mis_search.textChanged.connect(self.filter_mismatch)
        search_layout.addWidget(self.mis_search)
        layout.addLayout(search_layout)

        # 表格
        self.mismatch_table = QTableWidget()
        self.mismatch_table.setColumnCount(5)
        self.mismatch_table.setHorizontalHeaderLabels(['文件名', '内部标题', '作者', '大小(MB)', '路径'])
        self.mismatch_table.horizontalHeader().setStretchLastSection(True)
        self.mismatch_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.mismatch_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.mismatch_table.customContextMenuRequested.connect(self.show_mismatch_context_menu)

        layout.addWidget(self.mismatch_table)
        widget.setLayout(layout)
        return widget

    def create_failed_tab(self):
        """创建读取失败标签页"""
        widget = QWidget()
        layout = QVBoxLayout()

        info_label = QLabel("❌ 以下文件无法读取元数据，可能文件损坏或格式不正确")
        info_label.setStyleSheet("color: #F44336; padding: 5px;")
        layout.addWidget(info_label)

        self.failed_text = QTextEdit()
        self.failed_text.setReadOnly(True)
        layout.addWidget(self.failed_text)

        widget.setLayout(layout)
        return widget

    def create_button_bar(self):
        """创建底部按钮栏"""
        widget = QWidget()
        layout = QHBoxLayout()

        export_btn = QPushButton("📄 导出完整报告")
        export_btn.clicked.connect(self.export_full_report)

        delete_script_btn = QPushButton("🗑️ 生成删除脚本")
        delete_script_btn.clicked.connect(self.generate_delete_script)

        rename_script_btn = QPushButton("🔄 生成重命名脚本")
        rename_script_btn.clicked.connect(self.generate_rename_script)

        export_books_btn = QPushButton("📋 导出书名列表")
        export_books_btn.clicked.connect(self.export_book_names)

        layout.addWidget(export_btn)
        layout.addWidget(delete_script_btn)
        layout.addWidget(rename_script_btn)
        layout.addWidget(export_books_btn)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def setup_connections(self):
        """设置信号连接"""
        pass

    def apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                padding: 8px 15px;
                border-radius: 4px;
                background-color: #2196F3;
                color: white;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
            QTreeWidget, QTableWidget {
                border: 1px solid #ddd;
                border-radius: 3px;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
        """)

    def browse_directory(self):
        """浏览目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择Mobi电子书目录"
        )
        if directory:
            self.dir_input.setText(directory)
            self.directory = directory

    def start_scan(self):
        """开始扫描"""
        directory = self.dir_input.text()
        if not directory or not os.path.isdir(directory):
            QMessageBox.warning(self, "错误", "请选择有效的目录")
            return

        self.directory = directory
        self.clear_results()

        # 创建工作线程
        self.scan_worker = ScanWorker(directory)
        self.scan_worker.progress_update.connect(self.update_progress)
        self.scan_worker.scan_complete.connect(self.scan_complete)
        self.scan_worker.scan_error.connect(self.scan_error)
        self.scan_worker.start()

        self.status_bar.showMessage("正在扫描...")

    def update_progress(self, current: int, total: int, filename: str):
        """更新进度"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"{current}/{total}")
        self.status_bar.showMessage(f"正在扫描: {filename}")

    def scan_complete(self, duplicates: Dict, mismatched: List, failed: List):
        """扫描完成"""
        self.duplicates = duplicates
        self.mismatched = mismatched
        self.failed = failed

        # 收集所有书籍信息
        self.all_books = self.scan_worker.book_info

        # 更新统计
        total_files = sum(len(books) for books in self.all_books.values())
        stats = {
            'total': total_files,
            'unique': len(self.all_books),
            'duplicate': len(duplicates),
            'mismatch': len(mismatched),
            'failed': len(failed)
        }
        self.stats_widget.update_stats(stats)

        # 更新显示
        self.populate_all_books()
        self.populate_duplicate_tree()
        self.populate_mismatch_table()
        self.populate_failed_text()

        self.status_bar.showMessage("扫描完成！", 5000)
        self.progress_label.setText("完成")

        QMessageBox.information(
            self, "扫描完成",
            f"扫描完成！\n\n"
            f"总文件数: {stats['total']}\n"
            f"唯一书名: {stats['unique']}\n"
            f"重名书籍: {stats['duplicate']}\n"
            f"名称不一致: {stats['mismatch']}\n"
            f"读取失败: {stats['failed']}"
        )

    def scan_error(self, error: str):
        """扫描错误"""
        QMessageBox.critical(self, "错误", f"扫描失败:\n{error}")
        self.status_bar.showMessage("扫描失败", 5000)

    def clear_results(self):
        """清空结果"""
        self.all_books_tree.clear()
        self.duplicate_tree.clear()
        self.mismatch_table.setRowCount(0)
        self.failed_text.clear()

        stats = {'total': 0, 'unique': 0, 'duplicate': 0, 'mismatch': 0, 'failed': 0}
        self.stats_widget.update_stats(stats)

    def populate_all_books(self):
        """填充所有书籍"""
        self.all_books_tree.clear()

        for book_name, books in sorted(self.all_books.items()):
            total_size = sum(book['size_mb'] for book in books)
            author = books[0]['author'] if books else '未知'
            publisher = books[0]['publisher'] if books else '未知'

            item = QTreeWidgetItem([
                book_name,
                author,
                publisher,
                str(len(books)),
                f"{total_size:.2f}"
            ])

            # 如果有重复,标记颜色
            if len(books) > 1:
                item.setForeground(0, QColor('#FF9800'))

            for book in books:
                child = QTreeWidgetItem([
                    book['filename'],
                    book['author'],
                    book['publisher'],
                    '',
                    f"{book['size_mb']:.2f}"
                ])
                child.setData(0, Qt.UserRole, book['path'])
                item.addChild(child)

            self.all_books_tree.addTopLevelItem(item)

    def populate_duplicate_tree(self):
        """填充重名书籍树"""
        self.duplicate_tree.clear()

        for idx, (book_name, books) in enumerate(sorted(self.duplicates.items()), 1):
            parent = QTreeWidgetItem([f"[{idx}] {book_name} (共{len(books)}个)", '', '', '', ''])
            parent.setForeground(0, QColor('#FF9800'))

            for book in books:
                child = QTreeWidgetItem([
                    '',
                    book['filename'],
                    book['author'],
                    f"{book['size_mb']:.2f}",
                    book['path']
                ])
                child.setData(0, Qt.UserRole, book['path'])
                parent.addChild(child)

            self.duplicate_tree.addTopLevelItem(parent)

    def populate_mismatch_table(self):
        """填充名称不一致表格"""
        self.mismatch_table.setRowCount(len(self.mismatched))

        for row, book in enumerate(self.mismatched):
            self.mismatch_table.setItem(row, 0, QTableWidgetItem(book['filename']))
            self.mismatch_table.setItem(row, 1, QTableWidgetItem(book['title']))
            self.mismatch_table.setItem(row, 2, QTableWidgetItem(book['author']))
            self.mismatch_table.setItem(row, 3, QTableWidgetItem(f"{book['size_mb']:.2f}"))

            path_item = QTableWidgetItem(book['path'])
            path_item.setData(Qt.UserRole, book['path'])
            self.mismatch_table.setItem(row, 4, path_item)

        self.mismatch_table.resizeColumnsToContents()

    def populate_failed_text(self):
        """填充失败文件文本"""
        if self.failed:
            text = "\n".join(f"{i}. {path}" for i, path in enumerate(self.failed, 1))
            self.failed_text.setText(text)
        else:
            self.failed_text.setText("✅ 所有文件都成功读取元数据！")

    def filter_all_books(self):
        """筛选所有书籍"""
        search_text = self.all_books_search.text().lower()

        for i in range(self.all_books_tree.topLevelItemCount()):
            item = self.all_books_tree.topLevelItem(i)
            book_name = item.text(0).lower()
            author = item.text(1).lower()

            visible = not search_text or search_text in book_name or search_text in author
            item.setHidden(not visible)

    def filter_duplicates(self):
        """筛选重名书籍"""
        search_text = self.dup_search.text().lower()

        for i in range(self.duplicate_tree.topLevelItemCount()):
            item = self.duplicate_tree.topLevelItem(i)
            book_name = item.text(0).lower()
            visible = not search_text or search_text in book_name
            item.setHidden(not visible)

    def filter_mismatch(self):
        """筛选名称不一致"""
        search_text = self.mis_search.text().lower()

        for row in range(self.mismatch_table.rowCount()):
            filename = self.mismatch_table.item(row, 0).text().lower()
            title = self.mismatch_table.item(row, 1).text().lower()
            visible = not search_text or search_text in filename or search_text in title
            self.mismatch_table.setRowHidden(row, not visible)

    def show_all_books_context_menu(self, position):
        """显示所有书籍右键菜单"""
        item = self.all_books_tree.itemAt(position)
        if not item:
            return

        menu = QMenu()
        copy_action = menu.addAction("📋 复制路径")
        open_action = menu.addAction("📂 打开文件位置")

        action = menu.exec_(self.all_books_tree.mapToGlobal(position))

        if action == copy_action:
            path = item.data(0, Qt.UserRole)
            if path:
                QApplication.clipboard().setText(path)
                self.status_bar.showMessage("路径已复制到剪贴板", 3000)
        elif action == open_action:
            path = item.data(0, Qt.UserRole)
            if path:
                self.open_file_location(path)

    def show_duplicate_context_menu(self, position):
        """显示重名书籍右键菜单"""
        item = self.duplicate_tree.itemAt(position)
        if not item:
            return

        menu = QMenu()
        copy_action = menu.addAction("📋 复制路径")
        open_action = menu.addAction("📂 打开文件位置")

        action = menu.exec_(self.duplicate_tree.mapToGlobal(position))

        if action == copy_action:
            path = item.data(0, Qt.UserRole) or item.text(4)
            if path:
                QApplication.clipboard().setText(path)
                self.status_bar.showMessage("路径已复制到剪贴板", 3000)
        elif action == open_action:
            path = item.data(0, Qt.UserRole) or item.text(4)
            if path:
                self.open_file_location(path)

    def show_mismatch_context_menu(self, position):
        """显示名称不一致右键菜单"""
        row = self.mismatch_table.rowAt(position.y())
        if row < 0:
            return

        menu = QMenu()
        copy_action = menu.addAction("📋 复制路径")
        open_action = menu.addAction("📂 打开文件位置")

        action = menu.exec_(self.mismatch_table.mapToGlobal(position))

        if action == copy_action:
            path = self.mismatch_table.item(row, 4).text()
            QApplication.clipboard().setText(path)
            self.status_bar.showMessage("路径已复制到剪贴板", 3000)
        elif action == open_action:
            path = self.mismatch_table.item(row, 4).text()
            self.open_file_location(path)

    def open_file_location(self, path: str):
        """打开文件位置"""
        import platform
        import subprocess

        directory = os.path.dirname(path)
        system = platform.system()

        try:
            if system == 'Windows':
                os.startfile(directory)
            elif system == 'Darwin':
                subprocess.run(['open', directory])
            else:
                subprocess.run(['xdg-open', directory])
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开目录:\n{e}")

    def export_book_names(self):
        """导出书籍名称列表到TXT"""
        if not self.all_books:
            QMessageBox.warning(self, "提示", "没有可导出的数据，请先扫描")
            return

        # 显示导出选项对话框
        dialog = BookListExportDialog(self.all_books, self)
        if dialog.exec_() != QDialog.Accepted:
            return

        options = dialog.get_export_options()

        filename, _ = QFileDialog.getSaveFileName(
            self, "保存书籍名称列表",
            f"书籍名称列表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt)"
        )

        if not filename:
            return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("书籍名称列表\n")
                f.write("=" * 80 + "\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"扫描目录: {self.directory}\n")
                f.write(f"书籍总数: {len(self.all_books)}\n\n")

                # 排序
                if options['sort_by'] == 0:  # 按书名
                    sorted_books = sorted(self.all_books.items())
                else:  # 按作者
                    sorted_books = sorted(
                        self.all_books.items(),
                        key=lambda x: x[1][0].get('author', '未知')
                    )

                for idx, (book_name, books) in enumerate(sorted_books, 1):
                    line = f"{idx}. {book_name}"

                    if options['include_author']:
                        author = books[0].get('author', '未知')
                        line += f" - {author}"

                    if options['include_count'] and len(books) > 1:
                        line += f" (共{len(books)}个文件)"

                    f.write(line + "\n")

            QMessageBox.information(self, "成功", f"书籍名称列表已保存到:\n{filename}")
            self.status_bar.showMessage("导出成功", 3000)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败:\n{e}")

    def export_full_report(self):
        """导出完整报告"""
        if not self.all_books:
            QMessageBox.warning(self, "提示", "没有可导出的数据，请先扫描")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "保存分析报告",
            f"mobi_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt)"
        )

        if not filename:
            return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("MOBI电子书分析报告\n")
                f.write("=" * 80 + "\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"扫描目录: {self.directory}\n\n")

                # 统计信息
                total_files = sum(len(books) for books in self.all_books.values())
                f.write("【统计信息】\n")
                f.write(f"总文件数: {total_files}\n")
                f.write(f"唯一书名: {len(self.all_books)}\n")
                f.write(f"重名书籍: {len(self.duplicates)}\n")
                f.write(f"名称不一致: {len(self.mismatched)}\n")
                f.write(f"读取失败: {len(self.failed)}\n\n")

                # 所有书籍列表
                f.write("=" * 80 + "\n")
                f.write("【所有书籍列表】\n")
                f.write("=" * 80 + "\n\n")

                for idx, (book_name, books) in enumerate(sorted(self.all_books.items()), 1):
                    f.write(f"{idx}. {book_name}\n")
                    f.write(f"   作者: {books[0].get('author', '未知')}\n")
                    f.write(f"   出版社: {books[0].get('publisher', '未知')}\n")
                    f.write(f"   文件数: {len(books)}\n")

                    if len(books) > 1:
                        f.write("   文件列表:\n")
                        for book in books:
                            f.write(f"     - {book['filename']} ({book['size_mb']:.2f} MB)\n")
                    else:
                        f.write(f"   文件: {books[0]['filename']} ({books[0]['size_mb']:.2f} MB)\n")
                    f.write("\n")

                # 重名书籍
                if self.duplicates:
                    f.write("=" * 80 + "\n")
                    f.write("【重名书籍详情】\n")
                    f.write("=" * 80 + "\n\n")

                    for idx, (book_name, books) in enumerate(sorted(self.duplicates.items()), 1):
                        f.write(f"{idx}. 书名: {book_name}\n")
                        f.write(f"   重复次数: {len(books)}\n")
                        f.write("-" * 80 + "\n")

                        for i, book in enumerate(books, 1):
                            f.write(f"   副本 {i}:\n")
                            f.write(f"     文件名: {book['filename']}\n")
                            f.write(f"     作者: {book['author']}\n")
                            f.write(f"     出版社: {book['publisher']}\n")
                            f.write(f"     大小: {book['size_mb']:.2f} MB\n")
                            f.write(f"     路径: {book['path']}\n\n")

                # 名称不一致
                if self.mismatched:
                    f.write("=" * 80 + "\n")
                    f.write("【文件名与标题不一致】\n")
                    f.write("=" * 80 + "\n\n")

                    for idx, book in enumerate(self.mismatched, 1):
                        f.write(f"{idx}. 文件名: {book['filename']}\n")
                        f.write(f"   内部标题: {book['title']}\n")
                        f.write(f"   作者: {book['author']}\n")
                        f.write(f"   大小: {book['size_mb']:.2f} MB\n")
                        f.write(f"   路径: {book['path']}\n\n")

                # 失败文件
                if self.failed:
                    f.write("=" * 80 + "\n")
                    f.write("【读取失败的文件】\n")
                    f.write("=" * 80 + "\n\n")

                    for idx, path in enumerate(self.failed, 1):
                        f.write(f"{idx}. {path}\n")

            QMessageBox.information(self, "成功", f"完整报告已保存到:\n{filename}")
            self.status_bar.showMessage("导出成功", 3000)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败:\n{e}")

    def generate_delete_script(self):
        """生成删除脚本"""
        if not self.duplicates:
            QMessageBox.warning(self, "提示", "没有重名书籍")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "保存删除脚本",
            f"delete_duplicates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sh",
            "Shell脚本 (*.sh);;批处理文件 (*.bat)"
        )

        if not filename:
            return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("#!/bin/bash\n")
                f.write("# Mobi重复书籍删除脚本\n")
                f.write("# 自动保留每组中最大的文件，删除其他副本\n")
                f.write("# 使用前请仔细检查！去掉 # 注释后执行\n\n")

                for book_name, books in self.duplicates.items():
                    sorted_books = sorted(books, key=lambda x: x['size_mb'], reverse=True)
                    f.write(f"# 书名: {book_name}\n")
                    f.write(f"# 保留: {sorted_books[0]['filename']} ({sorted_books[0]['size_mb']:.2f} MB)\n")

                    for book in sorted_books[1:]:
                        safe_path = book['path'].replace('"', '\\"')
                        f.write(f'# rm "{safe_path}"  # {book["size_mb"]:.2f} MB\n')

                    f.write("\n")

            QMessageBox.information(
                self, "成功",
                f"删除脚本已生成:\n{filename}\n\n"
                "⚠️ 请检查后手动执行（去掉注释符#）"
            )
            self.status_bar.showMessage("脚本生成成功", 3000)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成脚本失败:\n{e}")

    def generate_rename_script(self):
        """生成重命名脚本"""
        if not self.mismatched:
            QMessageBox.warning(self, "提示", "没有名称不一致的书籍")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "保存重命名脚本",
            f"rename_books_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sh",
            "Shell脚本 (*.sh);;批处理文件 (*.bat)"
        )

        if not filename:
            return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("#!/bin/bash\n")
                f.write("# Mobi书籍重命名脚本\n")
                f.write("# 将文件名修改为与内部标题一致\n")
                f.write("# 使用前请仔细检查！去掉 # 注释后执行\n\n")

                for book in self.mismatched:
                    clean_title = re.sub(r'[<>:"/\\|?*]', '_', book['title'])
                    old_path = book['path']
                    dir_path = os.path.dirname(old_path)
                    new_path = os.path.join(dir_path, clean_title + '.mobi')

                    f.write(f"# 原文件: {book['filename']}\n")
                    f.write(f"# 新文件: {clean_title}.mobi\n")
                    f.write(f'# mv "{old_path}" "{new_path}"\n\n')

            QMessageBox.information(
                self, "成功",
                f"重命名脚本已生成:\n{filename}\n\n"
                "⚠️ 请检查后手动执行（去掉注释符#）"
            )
            self.status_bar.showMessage("脚本生成成功", 3000)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成脚本失败:\n{e}")

    def show_help(self):
        """显示帮助"""
        help_text = """
<h2>📚 Mobi电子书管理器 v2.0 - 使用帮助</h2>

<h3>【主要功能】</h3>
<ul>
<li><b>扫描所有书籍</b> - 列出所有检测到的书籍及其元数据</li>
<li><b>检测重名书籍</b> - 找出标题相同的书籍（不同版本）</li>
<li><b>检测名称不一致</b> - 找出文件名与内部标题不一致的书籍</li>
<li><b>检查损坏文件</b> - 列出无法读取元数据的文件</li>
<li><b>导出书名列表</b> - 将所有书籍名称导出为TXT文件</li>
</ul>

<h3>【使用步骤】</h3>
<ol>
<li>点击"浏览"选择你的Mobi电子书目录</li>
<li>点击"开始扫描"等待扫描完成</li>
<li>在对应标签页查看结果</li>
<li>可导出报告、书名列表或生成脚本批量处理</li>
</ol>

<h3>【功能说明】</h3>
<ul>
<li><b>所有书籍</b>：显示全部扫描到的书籍及其信息</li>
<li><b>重名书籍</b>：同一本书的不同版本，可选择删除</li>
<li><b>名称不一致</b>：文件名杂乱，建议重命名</li>
<li><b>读取失败</b>：文件可能损坏或格式错误</li>
</ul>

<h3>【快捷操作】</h3>
<ul>
<li>右键点击可复制路径或打开文件位置</li>
<li>使用搜索框可快速筛选</li>
<li>生成的脚本默认是注释状态，需手动启用</li>
<li>支持树形展开/折叠查看详情</li>
</ul>

<h3>【新增功能】</h3>
<ul>
<li>✨ 导出所有书籍名称到TXT文件</li>
<li>✨ 更美观的PyQt5界面</li>
<li>✨ 实时搜索过滤功能</li>
<li>✨ 状态栏显示当前操作</li>
<li>✨ 优化的表格和树形视图</li>
</ul>

<h3>【注意事项】</h3>
<p style="color: red;">
⚠️ 删除和重命名操作不可恢复，请谨慎操作！<br>
⚠️ 建议先备份重要文件<br>
⚠️ 脚本执行前请仔细检查
</p>

<p><b>版本:</b> 2.0 (PyQt5)<br>
<b>开发:</b> AI Assistant</p>
        """

        msg = QMessageBox(self)
        msg.setWindowTitle("帮助")
        msg.setTextFormat(Qt.RichText)
        msg.setText(help_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("Mobi电子书管理器")

    # 设置应用图标（如果有）
    # app.setWindowIcon(QIcon('icon.png'))

    window = MobiBookManagerWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()