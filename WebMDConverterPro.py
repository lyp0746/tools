"""
WebMD Converter Pro - 专业网页转Markdown工具
基于PyQt5开发，支持批量转换、智能提取、多种导出选项
Version: 2.0
github网址：https://github.com/lyp0746
QQ邮箱：1610369302@qq.com
作者：LYP
"""

import sys
import os
import re
import json
import base64
import threading
from datetime import datetime
from urllib.parse import urljoin, urlparse
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import html2text

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QProgressBar, QListWidget,
    QSplitter, QGroupBox, QCheckBox, QRadioButton, QButtonGroup,
    QFileDialog, QMessageBox, QLineEdit, QSpinBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QStatusBar, QAction, QMenu, QDialog, QDialogButtonBox,
    QListWidgetItem, QFrame
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QSettings, QTimer, QUrl
)
from PyQt5.QtGui import (
    QIcon, QFont, QTextCursor, QKeySequence, QPalette, QColor,
    QTextCharFormat, QSyntaxHighlighter, QDesktopServices
)


class ConversionWorker(QThread):
    """后台转换工作线程"""
    progress = pyqtSignal(int, str)  # 进度百分比, 状态消息
    finished = pyqtSignal(list)  # 转换结果列表
    error = pyqtSignal(str, str)  # URL, 错误消息

    def __init__(self, urls, options):
        super().__init__()
        self.urls = urls
        self.options = options
        self.results = []
        self._is_running = True

    def run(self):
        """执行转换任务"""
        total = len(self.urls)

        for i, url in enumerate(self.urls):
            if not self._is_running:
                break

            try:
                self.progress.emit(
                    int((i / total) * 100),
                    f"正在处理 ({i+1}/{total}): {url[:60]}..."
                )

                result = self._convert_url(url)
                self.results.append(result)

            except Exception as e:
                error_msg = f"转换失败: {str(e)}"
                self.error.emit(url, error_msg)
                # 添加失败记录
                self.results.append({
                    'url': url,
                    'title': 'Error',
                    'markdown': f"# 转换失败\n\n**URL**: {url}\n\n**错误**: {error_msg}",
                    'success': False,
                    'error': error_msg
                })

        self.progress.emit(100, f"完成！成功转换 {len([r for r in self.results if r.get('success', True)])}/{total} 个页面")
        self.finished.emit(self.results)

    def stop(self):
        """停止转换"""
        self._is_running = False

    def _convert_url(self, url):
        """转换单个URL"""
        # 请求配置
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

        timeout = self.options.get('timeout', 30)

        # 发起请求
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()

        # 自动检测编码
        if response.encoding == 'ISO-8859-1':
            response.encoding = response.apparent_encoding

        html_content = response.text

        # 解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # 提取标题
        title = self._extract_title(soup, url)

        # 提取内容
        if self.options.get('extract_body', True):
            content = self._extract_main_content(soup)
        else:
            content = soup

        # 处理图片
        if self.options.get('download_images', True):
            self._process_images(content, url)

        # 移除不需要的元素
        if self.options.get('remove_scripts', True):
            for tag in content.find_all(['script', 'style']):
                tag.decompose()

        # 转换为Markdown
        markdown = self._html_to_markdown(content, url, title)

        return {
            'url': url,
            'title': title,
            'markdown': markdown,
            'success': True,
            'timestamp': datetime.now().isoformat()
        }

    def _extract_title(self, soup, url):
        """提取页面标题"""
        title = None

        # 优先级1: meta标签
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            title = meta_title['content'].strip()

        # 优先级2: title标签
        if not title and soup.title and soup.title.string:
            title = soup.title.string.strip()
            # 移除常见的网站后缀
            title = re.split(r'[|_\-–—]', title)[0].strip()

        # 优先级3: h1标签
        if not title:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text().strip()

        # 优先级4: URL路径
        if not title:
            path = urlparse(url).path
            title = path.split('/')[-1] or path.split('/')[-2] or 'untitled'
            title = title.replace('.html', '').replace('.htm', '')

        # 清理标题
        title = self._sanitize_filename(title)
        title = title[:150]  # 限制长度

        return title or 'untitled'

    def _sanitize_filename(self, filename):
        """清理文件名，移除非法字符"""
        # 移除Windows非法文件名字符
        illegal_chars = r'[<>:"/\\|?*\x00-\x1f]'
        filename = re.sub(illegal_chars, '_', filename)

        # 移除前后空格和点
        filename = filename.strip(' .')

        # 替换多个连续空格/下划线
        filename = re.sub(r'[\s_]+', '_', filename)

        return filename

    def _extract_main_content(self, soup):
        """智能提取正文内容"""
        # 移除干扰元素
        for tag in soup.find_all(['script', 'style', 'nav', 'footer',
                                  'header', 'aside', 'iframe', 'noscript']):
            tag.decompose()

        # 移除广告、导航等
        for tag in soup.find_all(class_=re.compile(r'ad|advertisement|banner|sidebar|widget|navigation|menu|comment', re.I)):
            tag.decompose()

        for tag in soup.find_all(id=re.compile(r'ad|advertisement|banner|sidebar|widget|navigation|menu|comment', re.I)):
            tag.decompose()

        # 查找主要内容
        main_selectors = [
            ('tag', 'main'),
            ('tag', 'article'),
            ('class', re.compile(r'content|main|article|post-body|entry-content|post-content|article-content|markdown-body', re.I)),
            ('id', re.compile(r'content|main|article|post-body|entry-content', re.I)),
            ('role', 'main'),
        ]

        main_content = None
        for selector_type, selector_value in main_selectors:
            if selector_type == 'tag':
                main_content = soup.find(selector_value)
            elif selector_type == 'class':
                main_content = soup.find(class_=selector_value)
            elif selector_type == 'id':
                main_content = soup.find(id=selector_value)
            elif selector_type == 'role':
                main_content = soup.find(attrs={'role': selector_value})

            if main_content:
                break

        # 如果没找到，尝试找到文本密度最高的div
        if not main_content:
            main_content = self._find_content_by_density(soup)

        return main_content or soup.body or soup

    def _find_content_by_density(self, soup):
        """根据文本密度查找主要内容"""
        candidates = soup.find_all(['div', 'section'])
        max_score = 0
        best_candidate = None

        for candidate in candidates:
            text = candidate.get_text(strip=True)
            text_length = len(text)

            # 计算分数：文本长度 - 链接长度 - 标签数量
            links_length = sum(len(a.get_text(strip=True)) for a in candidate.find_all('a'))
            tags_count = len(candidate.find_all())

            score = text_length - links_length * 0.5 - tags_count * 2

            if score > max_score and text_length > 200:
                max_score = score
                best_candidate = candidate

        return best_candidate

    def _process_images(self, content, base_url):
        """处理图片"""
        images = content.find_all('img')

        for img in images:
            src = img.get('src') or img.get('data-src') or img.get('data-original')
            if not src:
                continue

            # 跳过已经是base64的图片
            if src.startswith('data:image'):
                continue

            try:
                # 转换为绝对URL
                img_url = urljoin(base_url, src)

                # 下载图片
                response = requests.get(img_url, timeout=10)
                if response.status_code == 200:
                    # 获取内容类型
                    content_type = response.headers.get('content-type', 'image/png')
                    if 'image' not in content_type:
                        content_type = 'image/' + img_url.split('.')[-1]

                    # 转换为Base64
                    img_data = base64.b64encode(response.content).decode('utf-8')
                    img['src'] = f"data:{content_type};base64,{img_data}"

                    # 移除懒加载属性
                    for attr in ['data-src', 'data-original']:
                        if img.get(attr):
                            del img[attr]
            except Exception as e:
                # 下载失败，保留原URL或使用绝对URL
                try:
                    img['src'] = urljoin(base_url, src)
                except:
                    pass

    def _html_to_markdown(self, content, url, title):
        """HTML转Markdown"""
        # 配置html2text
        h2t = html2text.HTML2Text()
        h2t.body_width = 0  # 不自动换行
        h2t.ignore_links = False
        h2t.ignore_images = False
        h2t.ignore_emphasis = False
        h2t.skip_internal_links = False
        h2t.inline_links = True
        h2t.protect_links = True
        h2t.wrap_links = False
        h2t.unicode_snob = True
        h2t.escape_snob = True

        # 转换
        markdown_content = h2t.handle(str(content))

        # 添加元信息
        if self.options.get('add_metadata', True):
            metadata = f"# {title}\n\n"
            metadata += f"**原始链接**: {url}\n\n"
            metadata += f"**转换时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            metadata += "---\n\n"
            markdown_content = metadata + markdown_content

        # 清理多余空行
        markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)

        return markdown_content


class SettingsDialog(QDialog):
    """设置对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("转换设置")
        self.setMinimumWidth(500)
        self.settings = QSettings('WebMDConverter', 'Settings')
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        layout = QVBoxLayout()

        # 网络设置
        network_group = QGroupBox("网络设置")
        network_layout = QVBoxLayout()

        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("请求超时 (秒):"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 120)
        self.timeout_spin.setValue(30)
        timeout_layout.addWidget(self.timeout_spin)
        timeout_layout.addStretch()
        network_layout.addLayout(timeout_layout)

        network_group.setLayout(network_layout)
        layout.addWidget(network_group)

        # 内容提取设置
        content_group = QGroupBox("内容提取")
        content_layout = QVBoxLayout()

        self.extract_body_cb = QCheckBox("智能提取正文内容（推荐）")
        self.extract_body_cb.setChecked(True)
        content_layout.addWidget(self.extract_body_cb)

        self.remove_scripts_cb = QCheckBox("移除脚本和样式")
        self.remove_scripts_cb.setChecked(True)
        content_layout.addWidget(self.remove_scripts_cb)

        self.add_metadata_cb = QCheckBox("添加元信息（标题、链接、时间）")
        self.add_metadata_cb.setChecked(True)
        content_layout.addWidget(self.add_metadata_cb)

        content_group.setLayout(content_layout)
        layout.addWidget(content_group)

        # 图片处理设置
        image_group = QGroupBox("图片处理")
        image_layout = QVBoxLayout()

        self.download_images_cb = QCheckBox("下载并转换为Base64内嵌")
        self.download_images_cb.setChecked(True)
        image_layout.addWidget(self.download_images_cb)

        image_group.setLayout(image_layout)
        layout.addWidget(image_group)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _load_settings(self):
        """加载设置"""
        self.timeout_spin.setValue(self.settings.value('timeout', 30, int))
        self.extract_body_cb.setChecked(self.settings.value('extract_body', True, bool))
        self.remove_scripts_cb.setChecked(self.settings.value('remove_scripts', True, bool))
        self.add_metadata_cb.setChecked(self.settings.value('add_metadata', True, bool))
        self.download_images_cb.setChecked(self.settings.value('download_images', True, bool))

    def get_options(self):
        """获取选项"""
        return {
            'timeout': self.timeout_spin.value(),
            'extract_body': self.extract_body_cb.isChecked(),
            'remove_scripts': self.remove_scripts_cb.isChecked(),
            'add_metadata': self.add_metadata_cb.isChecked(),
            'download_images': self.download_images_cb.isChecked(),
        }

    def save_settings(self):
        """保存设置"""
        options = self.get_options()
        for key, value in options.items():
            self.settings.setValue(key, value)


class WebMDConverterPro(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WebMD Converter Pro - 专业网页转Markdown工具")
        self.setGeometry(100, 100, 1400, 900)

        # 数据
        self.conversion_results = []
        self.worker = None
        self.settings = QSettings('WebMDConverter', 'Settings')

        # 初始化UI
        self._init_ui()
        self._create_menu()
        self._create_statusbar()
        self._load_history()

        # 应用样式
        self._apply_style()

    def _init_ui(self):
        """初始化UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # ===== 标题栏 =====
        title_layout = QHBoxLayout()
        title_label = QLabel("🚀 WebMD Converter Pro")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        version_label = QLabel("v2.0")
        version_label.setStyleSheet("color: #888;")
        title_layout.addWidget(version_label)

        main_layout.addLayout(title_layout)

        # ===== URL输入区域 =====
        input_group = QGroupBox("📝 URL输入")
        input_layout = QVBoxLayout()

        # 提示
        tip_label = QLabel("💡 输入一个或多个URL（每行一个），支持批量转换")
        tip_label.setStyleSheet("color: #666; font-size: 12px;")
        input_layout.addWidget(tip_label)

        # URL输入框
        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("请输入URL，例如：\nhttps://example.com/article1\nhttps://example.com/article2")
        self.url_input.setMaximumHeight(120)
        self.url_input.setFont(QFont("Consolas", 10))
        input_layout.addWidget(self.url_input)

        # 快速操作按钮
        quick_actions = QHBoxLayout()

        self.load_urls_btn = QPushButton("📂 从文件加载")
        self.load_urls_btn.clicked.connect(self._load_urls_from_file)
        quick_actions.addWidget(self.load_urls_btn)

        self.validate_btn = QPushButton("✓ 验证URLs")
        self.validate_btn.clicked.connect(self._validate_urls)
        quick_actions.addWidget(self.validate_btn)

        self.clear_urls_btn = QPushButton("🗑 清空")
        self.clear_urls_btn.clicked.connect(self._clear_urls)
        quick_actions.addWidget(self.clear_urls_btn)

        quick_actions.addStretch()

        url_count_label = QLabel("URL数量: ")
        self.url_count_value = QLabel("0")
        self.url_count_value.setStyleSheet("font-weight: bold; color: #2196F3;")
        quick_actions.addWidget(url_count_label)
        quick_actions.addWidget(self.url_count_value)

        input_layout.addLayout(quick_actions)
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # ===== 控制区域 =====
        control_group = QGroupBox("⚙️ 转换控制")
        control_layout = QVBoxLayout()

        # 文件命名选项
        naming_layout = QHBoxLayout()
        naming_layout.addWidget(QLabel("文件命名规则:"))

        self.naming_group = QButtonGroup()
        self.naming_with_index = QRadioButton("数字_标题.md")
        self.naming_title_only = QRadioButton("标题.md")
        self.naming_group.addButton(self.naming_with_index, 1)
        self.naming_group.addButton(self.naming_title_only, 2)
        self.naming_title_only.setChecked(True)  # 默认仅标题

        naming_layout.addWidget(self.naming_with_index)
        naming_layout.addWidget(self.naming_title_only)
        naming_layout.addStretch()
        control_layout.addLayout(naming_layout)

        # 控制按钮
        buttons_layout = QHBoxLayout()

        self.convert_btn = QPushButton("🚀 开始转换")
        self.convert_btn.setMinimumHeight(40)
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.convert_btn.clicked.connect(self._start_conversion)
        buttons_layout.addWidget(self.convert_btn)

        self.stop_btn = QPushButton("⏸ 停止")
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_conversion)
        buttons_layout.addWidget(self.stop_btn)

        self.settings_btn = QPushButton("⚙️ 设置")
        self.settings_btn.setMinimumHeight(40)
        self.settings_btn.clicked.connect(self._open_settings)
        buttons_layout.addWidget(self.settings_btn)

        self.batch_download_btn = QPushButton("💾 批量下载")
        self.batch_download_btn.setMinimumHeight(40)
        self.batch_download_btn.setEnabled(False)
        self.batch_download_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.batch_download_btn.clicked.connect(self._batch_download)
        buttons_layout.addWidget(self.batch_download_btn)

        control_layout.addLayout(buttons_layout)

        # 进度条
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("进度:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)
        control_layout.addLayout(progress_layout)

        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)

        # ===== 结果显示区域 =====
        result_group = QGroupBox("📊 转换结果")
        result_layout = QVBoxLayout()

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：结果列表
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)

        list_header = QHBoxLayout()
        list_title = QLabel("📋 转换列表")
        list_title.setFont(QFont("Arial", 11, QFont.Bold))
        list_header.addWidget(list_title)

        self.result_count_label = QLabel("(0)")
        self.result_count_label.setStyleSheet("color: #666;")
        list_header.addWidget(self.result_count_label)
        list_header.addStretch()

        self.clear_results_btn = QPushButton("清空列表")
        self.clear_results_btn.clicked.connect(self._clear_results)
        list_header.addWidget(self.clear_results_btn)

        left_layout.addLayout(list_header)

        self.result_list = QListWidget()
        self.result_list.itemClicked.connect(self._on_result_selected)
        left_layout.addWidget(self.result_list)

        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)

        # 右侧：预览区域
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)

        preview_header = QHBoxLayout()
        preview_title = QLabel("👁 Markdown预览")
        preview_title.setFont(QFont("Arial", 11, QFont.Bold))
        preview_header.addWidget(preview_title)
        preview_header.addStretch()

        self.copy_btn = QPushButton("📋 复制")
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self._copy_content)
        preview_header.addWidget(self.copy_btn)

        self.save_single_btn = QPushButton("💾 保存")
        self.save_single_btn.setEnabled(False)
        self.save_single_btn.clicked.connect(self._save_single)
        preview_header.addWidget(self.save_single_btn)

        self.open_browser_btn = QPushButton("🌐 源页面")
        self.open_browser_btn.setEnabled(False)
        self.open_browser_btn.clicked.connect(self._open_original_url)
        preview_header.addWidget(self.open_browser_btn)

        right_layout.addLayout(preview_header)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Consolas", 10))
        right_layout.addWidget(self.preview_text)

        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)

        # 设置分割比例
        splitter.setSizes([400, 800])

        result_layout.addWidget(splitter)
        result_group.setLayout(result_layout)
        main_layout.addWidget(result_group)

        central_widget.setLayout(main_layout)

        # 监听URL输入变化
        self.url_input.textChanged.connect(self._update_url_count)

    def _create_menu(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        load_action = QAction("加载URLs", self)
        load_action.setShortcut(QKeySequence.Open)
        load_action.triggered.connect(self._load_urls_from_file)
        file_menu.addAction(load_action)

        save_urls_action = QAction("保存URLs", self)
        save_urls_action.triggered.connect(self._save_urls_to_file)
        file_menu.addAction(save_urls_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")

        settings_action = QAction("设置", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._open_settings)
        edit_menu.addAction(settings_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_statusbar(self):
        """创建状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("就绪")

    def _apply_style(self):
        """应用样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
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
                padding: 5px 15px;
                border-radius: 3px;
                border: 1px solid #ccc;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QTextEdit, QListWidget {
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: white;
            }
        """)

    def _update_url_count(self):
        """更新URL数量"""
        text = self.url_input.toPlainText().strip()
        if text:
            urls = [line.strip() for line in text.split('\n') if line.strip()]
            self.url_count_value.setText(str(len(urls)))
        else:
            self.url_count_value.setText("0")

    def _load_urls_from_file(self):
        """从文件加载URLs"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "加载URLs", "", "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.url_input.setPlainText(content)
                self.statusbar.showMessage(f"已加载: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"加载失败: {str(e)}")

    def _save_urls_to_file(self):
        """保存URLs到文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存URLs", "", "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            try:
                content = self.url_input.toPlainText()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.statusbar.showMessage(f"已保存: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"保存失败: {str(e)}")

    def _validate_urls(self):
        """验证URLs"""
        text = self.url_input.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "提示", "请先输入URLs")
            return

        urls = [line.strip() for line in text.split('\n') if line.strip()]
        valid_urls = []
        invalid_urls = []

        for url in urls:
            if self._is_valid_url(url):
                valid_urls.append(url)
            else:
                invalid_urls.append(url)

        # 去重
        valid_urls = list(dict.fromkeys(valid_urls))

        # 更新输入框
        self.url_input.setPlainText('\n'.join(valid_urls))

        # 显示结果
        msg = f"✓ 有效URLs: {len(valid_urls)}"
        if invalid_urls:
            msg += f"\n✗ 无效URLs: {len(invalid_urls)}\n\n无效列表:\n" + '\n'.join(invalid_urls[:10])
            if len(invalid_urls) > 10:
                msg += f"\n... 还有 {len(invalid_urls) - 10} 个"

        QMessageBox.information(self, "验证结果", msg)

    def _is_valid_url(self, url):
        """验证URL格式"""
        try:
            result = urlparse(url)
            return all([result.scheme in ['http', 'https'], result.netloc])
        except:
            return False

    def _clear_urls(self):
        """清空URLs"""
        self.url_input.clear()
        self.statusbar.showMessage("已清空URLs")

    def _start_conversion(self):
        """开始转换"""
        text = self.url_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "警告", "请输入至少一个URL")
            return

        # 解析URLs
        urls = [line.strip() for line in text.split('\n') if line.strip()]

        # 验证并去重
        valid_urls = []
        for url in urls:
            if self._is_valid_url(url) and url not in valid_urls:
                valid_urls.append(url)

        if not valid_urls:
            QMessageBox.warning(self, "警告", "没有有效的URL")
            return

        # 确认
        reply = QMessageBox.question(
            self, "确认",
            f"准备转换 {len(valid_urls)} 个URL，是否继续？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        # 获取设置
        options = self._get_conversion_options()

        # 清空之前的结果
        self.conversion_results.clear()
        self.result_list.clear()
        self.preview_text.clear()

        # 禁用按钮
        self.convert_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.batch_download_btn.setEnabled(False)

        # 启动工作线程
        self.worker = ConversionWorker(valid_urls, options)
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(self._conversion_finished)
        self.worker.error.connect(self._conversion_error)
        self.worker.start()

        self.statusbar.showMessage("正在转换...")

    def _stop_conversion(self):
        """停止转换"""
        if self.worker:
            self.worker.stop()
            self.stop_btn.setEnabled(False)
            self.statusbar.showMessage("正在停止...")

    def _get_conversion_options(self):
        """获取转换选项"""
        settings_dialog = SettingsDialog(self)
        return settings_dialog.get_options()

    def _update_progress(self, value, message):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.statusbar.showMessage(message)

    def _conversion_finished(self, results):
        """转换完成"""
        self.conversion_results = results

        # 更新列表
        for i, result in enumerate(results):
            if result.get('success', True):
                icon = "✓"
                color = "#4CAF50"
            else:
                icon = "✗"
                color = "#F44336"

            title = result['title']
            item = QListWidgetItem(f"{icon} {title}")
            item.setForeground(QColor(color))
            self.result_list.addItem(item)

        # 更新计数
        self.result_count_label.setText(f"({len(results)})")

        # 重新启用按钮
        self.convert_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        if results:
            self.batch_download_btn.setEnabled(True)
            # 自动选择第一个
            self.result_list.setCurrentRow(0)
            self._on_result_selected(self.result_list.item(0))

        # 保存历史
        self._save_history()

        # 显示完成消息
        success_count = len([r for r in results if r.get('success', True)])
        QMessageBox.information(
            self, "完成",
            f"转换完成！\n\n成功: {success_count}\n失败: {len(results) - success_count}"
        )

    def _conversion_error(self, url, error):
        """转换错误"""
        self.statusbar.showMessage(f"错误: {url} - {error}")

    def _on_result_selected(self, item):
        """选择结果项"""
        if not item:
            return

        index = self.result_list.row(item)
        if index < len(self.conversion_results):
            result = self.conversion_results[index]
            self.preview_text.setPlainText(result['markdown'])

            # 启用按钮
            self.copy_btn.setEnabled(True)
            self.save_single_btn.setEnabled(True)
            self.open_browser_btn.setEnabled(True)

            self.statusbar.showMessage(f"预览: {result['title']}")

    def _copy_content(self):
        """复制内容"""
        content = self.preview_text.toPlainText()
        clipboard = QApplication.clipboard()
        clipboard.setText(content)
        self.statusbar.showMessage("✓ 已复制到剪贴板")

    def _save_single(self):
        """保存单个文件"""
        index = self.result_list.currentRow()
        if index < 0 or index >= len(self.conversion_results):
            return

        result = self.conversion_results[index]
        filename = self._generate_filename(result, index)

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", filename, "Markdown Files (*.md);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(result['markdown'])
                self.statusbar.showMessage(f"✓ 已保存: {file_path}")
                QMessageBox.information(self, "成功", "文件保存成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")

    def _batch_download(self):
        """批量下载"""
        if not self.conversion_results:
            return

        folder = QFileDialog.getExistingDirectory(self, "选择保存文件夹")
        if not folder:
            return

        success_count = 0
        failed_files = []

        for i, result in enumerate(self.conversion_results):
            if not result.get('success', True):
                continue

            try:
                filename = self._generate_filename(result, i)
                file_path = os.path.join(folder, filename)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(result['markdown'])
                success_count += 1
            except Exception as e:
                failed_files.append((filename, str(e)))

        # 显示结果
        msg = f"批量下载完成！\n\n成功: {success_count}/{len(self.conversion_results)}"
        if failed_files:
            msg += f"\n\n失败文件:\n"
            for fname, error in failed_files[:5]:
                msg += f"- {fname}: {error}\n"
            if len(failed_files) > 5:
                msg += f"... 还有 {len(failed_files) - 5} 个"

        QMessageBox.information(self, "完成", msg)
        self.statusbar.showMessage(f"✓ 批量下载完成: {success_count} 个文件")

    def _generate_filename(self, result, index):
        """生成文件名"""
        title = result['title']

        # 清理文件名
        title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', title)
        title = title.strip(' ._')

        # 根据命名规则
        if self.naming_with_index.isChecked():
            return f"{index + 1}_{title}.md"
        else:
            return f"{title}.md"

    def _open_original_url(self):
        """打开原始URL"""
        index = self.result_list.currentRow()
        if index < 0 or index >= len(self.conversion_results):
            return

        result = self.conversion_results[index]
        url = result['url']
        QDesktopServices.openUrl(QUrl(url))

    def _clear_results(self):
        """清空结果"""
        reply = QMessageBox.question(
            self, "确认",
            "确定要清空所有转换结果吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.conversion_results.clear()
            self.result_list.clear()
            self.preview_text.clear()
            self.result_count_label.setText("(0)")
            self.batch_download_btn.setEnabled(False)
            self.copy_btn.setEnabled(False)
            self.save_single_btn.setEnabled(False)
            self.open_browser_btn.setEnabled(False)
            self.statusbar.showMessage("已清空结果")

    def _open_settings(self):
        """打开设置"""
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            dialog.save_settings()
            self.statusbar.showMessage("设置已保存")

    def _show_about(self):
        """显示关于"""
        QMessageBox.about(
            self, "关于 WebMD Converter Pro",
            "<h2>WebMD Converter Pro v2.0</h2>"
            "<p>专业的网页转Markdown工具</p>"
            "<p><b>功能特性：</b></p>"
            "<ul>"
            "<li>智能提取网页正文内容</li>"
            "<li>支持批量转换和下载</li>"
            "<li>图片转Base64内嵌</li>"
            "<li>保留代码块和格式</li>"
            "<li>灵活的文件命名规则</li>"
            "</ul>"
            "<p><b>技术栈：</b> Python, PyQt5, BeautifulSoup, html2text</p>"
            "<p>© 2024 WebMD Converter Pro</p>"
        )

    def _save_history(self):
        """保存历史记录"""
        try:
            history_data = []
            for result in self.conversion_results[-10:]:  # 只保存最近10条
                history_data.append({
                    'url': result['url'],
                    'title': result['title'],
                    'timestamp': result.get('timestamp', ''),
                    'success': result.get('success', True)
                })

            self.settings.setValue('history', json.dumps(history_data))
        except Exception as e:
            print(f"保存历史失败: {e}")

    def _load_history(self):
        """加载历史记录"""
        try:
            history_json = self.settings.value('history', '[]')
            history_data = json.loads(history_json)
            # 可以在这里显示历史记录
        except Exception as e:
            print(f"加载历史失败: {e}")

    def closeEvent(self, event):
        """关闭事件"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "确认",
                "转换任务正在运行，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.No:
                event.ignore()
                return

            self.worker.stop()
            self.worker.wait()

        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("WebMD Converter Pro")
    app.setOrganizationName("WebMDConverter")

    # 设置应用样式
    app.setStyle('Fusion')

    window = WebMDConverterPro()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()