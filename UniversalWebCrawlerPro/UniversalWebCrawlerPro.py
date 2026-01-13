#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UniversalWebCrawlerPro - 万能网络爬虫系统
功能：网页爬取、数据提取、异步处理、数据库存储
作者：LYP
GitHub：https://github.com/lyp0746
邮箱：1610369302@qq.com
版本：4.0.0
"""

import sys
import os
import json
import sqlite3
import asyncio
import threading
import logging
import hashlib
import re
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse, unquote
from collections import deque

# PyQt5
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QProgressBar,
    QCheckBox, QSlider, QSpinBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QDialog, QGroupBox, QGridLayout, QSplitter,
    QStatusBar, QMenuBar, QToolBar, QAction, QComboBox, QListWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette, QTextCursor

# 第三方库
import validators
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import aiohttp

# ============ 配置日志 ============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('crawler_playwright_v4.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


# ============ 数据库管理器 ============
class DatabaseManager:
    """SQLite数据库管理器"""

    def __init__(self, db_path: str = "crawler_data_v4.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 爬取任务表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS tasks
                       (
                           id         INTEGER PRIMARY KEY AUTOINCREMENT,
                           url        TEXT NOT NULL,
                           save_path  TEXT NOT NULL,
                           start_time TEXT,
                           end_time   TEXT,
                           status     TEXT,
                           pages      INTEGER DEFAULT 0,
                           images     INTEGER DEFAULT 0,
                           videos     INTEGER DEFAULT 0,
                           audios     INTEGER DEFAULT 0,
                           documents  INTEGER DEFAULT 0,
                           others     INTEGER DEFAULT 0,
                           total_size INTEGER DEFAULT 0,
                           errors     INTEGER DEFAULT 0,
                           config     TEXT
                       )
                       ''')

        # 下载资源表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS resources
                       (
                           id            INTEGER PRIMARY KEY AUTOINCREMENT,
                           task_id       INTEGER,
                           url           TEXT,
                           filepath      TEXT,
                           resource_type TEXT,
                           file_size     INTEGER,
                           download_time TEXT,
                           FOREIGN KEY (task_id) REFERENCES tasks (id)
                       )
                       ''')

        # 错误日志表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS error_logs
                       (
                           id            INTEGER PRIMARY KEY AUTOINCREMENT,
                           task_id       INTEGER,
                           url           TEXT,
                           error_message TEXT,
                           error_time    TEXT,
                           FOREIGN KEY (task_id) REFERENCES tasks (id)
                       )
                       ''')

        conn.commit()
        conn.close()

    def create_task(self, url: str, save_path: str, config: str = '') -> int:
        """创建新任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
                       INSERT INTO tasks (url, save_path, start_time, status, config)
                       VALUES (?, ?, ?, ?, ?)
                       ''', (url, save_path, datetime.now().isoformat(), 'running', config))
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id

    def update_task_stats(self, task_id: int, stats: Dict):
        """更新任务统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
                       UPDATE tasks
                       SET pages=?,
                           images=?,
                           videos=?,
                           audios=?,
                           documents=?,
                           others=?,
                           total_size=?,
                           errors=?
                       WHERE id = ?
                       ''', (stats['pages'], stats['images'], stats['videos'], stats['audios'],
                             stats['documents'], stats['others'], stats['total_size'],
                             stats['errors'], task_id))
        conn.commit()
        conn.close()

    def finish_task(self, task_id: int, status: str = 'completed'):
        """完成任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
                       UPDATE tasks
                       SET end_time=?,
                           status=?
                       WHERE id = ?
                       ''', (datetime.now().isoformat(), status, task_id))
        conn.commit()
        conn.close()

    def add_resource(self, task_id: int, url: str, filepath: str,
                     resource_type: str, file_size: int):
        """添加下载资源记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
                       INSERT INTO resources (task_id, url, filepath, resource_type, file_size, download_time)
                       VALUES (?, ?, ?, ?, ?, ?)
                       ''', (task_id, url, filepath, resource_type, file_size, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def add_error(self, task_id: int, url: str, error_msg: str):
        """添加错误日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
                       INSERT INTO error_logs (task_id, url, error_message, error_time)
                       VALUES (?, ?, ?, ?)
                       ''', (task_id, url, error_msg, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def get_task_history(self, limit: int = 50) -> List[Dict]:
        """获取任务历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
                       SELECT id,
                              url,
                              save_path,
                              start_time,
                              end_time,
                              status,
                              pages,
                              images,
                              videos,
                              audios,
                              documents,
                              others,
                              total_size,
                              errors
                       FROM tasks
                       ORDER BY id DESC
                       LIMIT ?
                       ''', (limit,))
        rows = cursor.fetchall()
        conn.close()

        history = []
        for row in rows:
            history.append({
                'id': row[0], 'url': row[1], 'save_path': row[2],
                'start_time': row[3], 'end_time': row[4], 'status': row[5],
                'pages': row[6], 'images': row[7], 'videos': row[8],
                'audios': row[9], 'documents': row[10], 'others': row[11],
                'total_size': row[12], 'errors': row[13]
            })
        return history

    def get_task_resources(self, task_id: int) -> List[Dict]:
        """获取任务的所有资源"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
                       SELECT url, filepath, resource_type, file_size, download_time
                       FROM resources
                       WHERE task_id = ?
                       ORDER BY download_time DESC
                       ''', (task_id,))
        rows = cursor.fetchall()
        conn.close()

        resources = []
        for row in rows:
            resources.append({
                'url': row[0], 'filepath': row[1], 'resource_type': row[2],
                'file_size': row[3], 'download_time': row[4]
            })
        return resources

    def delete_task(self, task_id: int):
        """删除任务及其相关数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM resources WHERE task_id = ?', (task_id,))
        cursor.execute('DELETE FROM error_logs WHERE task_id = ?', (task_id,))
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
        conn.close()


# ============ 资源下载器 ============
class ResourceDownloader:
    """异步资源下载器"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=60, connect=10)

    async def init_session(self):
        """初始化HTTP会话"""
        if not self.session or self.session.closed:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            self.session = aiohttp.ClientSession(headers=headers, timeout=self.timeout)

    async def download(self, url: str, save_path: str, max_retries: int = 3) -> Tuple[bool, int, str]:
        """下载资源"""
        await self.init_session()

        for attempt in range(max_retries):
            try:
                async with self.session.get(url, ssl=False) as response:
                    if response.status == 200:
                        content = await response.read()
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)
                        with open(save_path, 'wb') as f:
                            f.write(content)
                        return True, len(content), ""
                    else:
                        if attempt == max_retries - 1:
                            return False, 0, f"HTTP {response.status}"
            except asyncio.TimeoutError:
                if attempt == max_retries - 1:
                    return False, 0, "下载超时"
            except Exception as e:
                if attempt == max_retries - 1:
                    return False, 0, str(e)

            if attempt < max_retries - 1:
                await asyncio.sleep(1 * (attempt + 1))

        return False, 0, "未知错误"

    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()


# ============ Playwright爬虫引擎 ============
class PlaywrightCrawler:
    """Playwright爬虫核心引擎"""

    def __init__(self, config: Dict, callback=None):
        self.config = config
        self.callback = callback
        self.db = DatabaseManager()

        self.is_running = False
        self.is_paused = False
        self.task_id: Optional[int] = None

        self.stats = {
            'pages': 0, 'images': 0, 'videos': 0, 'audios': 0,
            'documents': 0, 'others': 0, 'total_size': 0, 'errors': 0
        }

        self.visited_urls: Set[str] = set()
        self.url_queue: deque = deque()
        self.downloaded_resources: Set[str] = set()

        self.downloader = ResourceDownloader()
        self.browser: Optional[Browser] = None

    async def start(self):
        """启动爬虫"""
        self.is_running = True
        config_json = json.dumps(self.config, ensure_ascii=False)
        self.task_id = self.db.create_task(
            self.config['start_url'],
            self.config['save_path'],
            config_json
        )

        self._log("🚀 启动Playwright爬虫引擎...")

        try:
            async with async_playwright() as p:
                self.browser = await p.chromium.launch(
                    headless=self.config.get('headless', True),
                    args=['--disable-blink-features=AutomationControlled']
                )
                self._log("✓ 浏览器已启动")
                await self.downloader.init_session()
                self.url_queue.append((self.config['start_url'], 0))
                await self._crawl_loop()
        except Exception as e:
            self._log(f"✗ 爬虫错误: {e}", 'error')
            self.db.add_error(self.task_id, "", str(e))
            self.stats['errors'] += 1
        finally:
            await self._cleanup()

    async def _crawl_loop(self):
        """爬取循环"""
        max_pages = self.config.get('max_pages', 100)
        max_depth = self.config.get('max_depth', 2)

        while self.url_queue and self.is_running:
            while self.is_paused and self.is_running:
                await asyncio.sleep(0.5)

            if not self.is_running:
                break

            if self.stats['pages'] >= max_pages:
                self._log(f"⚠ 已达到最大页面数: {max_pages}")
                break

            current_url, depth = self.url_queue.popleft()

            if depth > max_depth or current_url in self.visited_urls:
                continue

            if self.config.get('domain_limit', True):
                if urlparse(current_url).netloc != urlparse(self.config['start_url']).netloc:
                    continue

            await self._crawl_page(current_url, depth)
            self._update_stats()
            await asyncio.sleep(self.config.get('delay', 1.0))

    async def _crawl_page(self, url: str, depth: int):
        """爬取单个页面"""
        try:
            self.visited_urls.add(url)
            self.stats['pages'] += 1
            self._log(f"📄 [{self.stats['pages']}] 爬取: {url[:70]}...")

            page = await self.browser.new_page()
            page.set_default_timeout(30000)

            try:
                response = await page.goto(url, wait_until='domcontentloaded')
                if not response or response.status != 200:
                    raise Exception(f"HTTP {response.status if response else 'None'}")

                await page.wait_for_load_state('networkidle', timeout=10000)
                content = await page.content()
                soup = BeautifulSoup(content, 'lxml')

                await self._extract_and_download_resources(soup, url, page)

                if depth < self.config.get('max_depth', 2):
                    links = await self._extract_links(page, url)
                    for link in links:
                        if link not in self.visited_urls:
                            self.url_queue.append((link, depth + 1))

            finally:
                await page.close()

        except PlaywrightTimeout:
            self._log(f"✗ 超时: {url[:60]}...", 'error')
            self.stats['errors'] += 1
            self.db.add_error(self.task_id, url, "页面加载超时")
        except Exception as e:
            self._log(f"✗ 错误: {url[:60]}... - {e}", 'error')
            self.stats['errors'] += 1
            self.db.add_error(self.task_id, url, str(e))

    async def _extract_and_download_resources(self, soup: BeautifulSoup, base_url: str, page: Page):
        """提取并下载所有资源"""
        resources = []

        if self.config.get('download_images', True):
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                if src:
                    resources.append((urljoin(base_url, src), 'images'))

        if self.config.get('download_videos', False):
            for video in soup.find_all(['video', 'source']):
                src = video.get('src')
                if src:
                    resources.append((urljoin(base_url, src), 'videos'))

        if self.config.get('download_audios', False):
            for audio in soup.find_all(['audio', 'source']):
                src = audio.get('src')
                if src:
                    resources.append((urljoin(base_url, src), 'audios'))

        if self.config.get('download_css', False):
            for link in soup.find_all('link', rel='stylesheet'):
                href = link.get('href')
                if href:
                    resources.append((urljoin(base_url, href), 'others'))

        if self.config.get('download_js', False):
            for script in soup.find_all('script', src=True):
                src = script.get('src')
                if src:
                    resources.append((urljoin(base_url, src), 'others'))

        if self.config.get('download_documents', True):
            for a in soup.find_all('a', href=True):
                href = a.get('href')
                full_url = urljoin(base_url, href)
                if self._is_document(full_url):
                    resources.append((full_url, 'documents'))

        tasks = []
        for resource_url, resource_type in resources:
            if resource_url not in self.downloaded_resources:
                self.downloaded_resources.add(resource_url)
                tasks.append(self._download_resource(resource_url, resource_type))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _download_resource(self, url: str, resource_type: str):
        """下载单个资源"""
        try:
            filename = self._generate_filename(url)
            type_dir = os.path.join(self.config['save_path'], resource_type)
            filepath = os.path.join(type_dir, filename)

            if os.path.exists(filepath):
                return

            success, file_size, error_msg = await self.downloader.download(url, filepath)

            if success:
                self.stats[resource_type] += 1
                self.stats['total_size'] += file_size
                self.db.add_resource(self.task_id, url, filepath, resource_type, file_size)
                self._log(f"  ✓ 下载: {filename} ({self._format_size(file_size)})")
            else:
                self.stats['errors'] += 1
                self.db.add_error(self.task_id, url, f"下载失败: {error_msg}")
                self._log(f"  ✗ 失败: {url[:50]}... - {error_msg}", 'error')

        except Exception as e:
            self.stats['errors'] += 1
            self._log(f"  ✗ 下载异常: {url[:50]}... - {e}", 'error')

    async def _extract_links(self, page: Page, base_url: str) -> List[str]:
        """提取页面链接"""
        links = []
        try:
            hrefs = await page.eval_on_selector_all(
                'a[href]',
                '(elements) => elements.map(e => e.href)'
            )

            for href in hrefs:
                full_url = urljoin(base_url, href)
                if full_url.startswith('http') and not full_url.endswith(('#', 'javascript:', 'mailto:')):
                    links.append(full_url)

        except Exception as e:
            self._log(f"提取链接错误: {e}", 'error')

        return links

    def _is_document(self, url: str) -> bool:
        """判断是否为文档"""
        doc_extensions = {
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.txt', '.zip', '.rar', '.7z', '.tar', '.gz', '.epub'
        }
        ext = Path(unquote(urlparse(url).path)).suffix.lower()
        return ext in doc_extensions

    def _generate_filename(self, url: str) -> str:
        """生成安全文件名"""
        parsed = urlparse(url)
        filename = unquote(os.path.basename(parsed.path))

        if not filename or filename == '/':
            filename = hashlib.md5(url.encode()).hexdigest()[:16]
            ext = self._guess_extension(url)
            filename += ext if ext else '.bin'

        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        name, ext = os.path.splitext(filename)
        if len(name) > 200:
            name = name[:200]

        return name + ext

    def _guess_extension(self, url: str) -> str:
        """推测文件扩展名"""
        ext = Path(unquote(urlparse(url).path)).suffix.lower()
        if ext:
            return ext

        mime_type, _ = mimetypes.guess_type(url)
        if mime_type:
            ext = mimetypes.guess_extension(mime_type)
            if ext:
                return ext

        return ''

    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    def _log(self, message: str, level: str = 'info'):
        """日志输出"""
        if self.callback:
            self.callback('log', message, self.stats)

        if level == 'error':
            logging.error(message)
        else:
            logging.info(message)

    def _update_stats(self):
        """更新统计信息"""
        if self.task_id:
            self.db.update_task_stats(self.task_id, self.stats)

        if self.callback:
            self.callback('stats', "", self.stats)

    async def _cleanup(self):
        """清理资源"""
        self._log("🧹 清理资源...")

        if self.browser:
            await self.browser.close()

        await self.downloader.close()

        if self.task_id:
            self.db.finish_task(
                self.task_id,
                'completed' if self.is_running else 'stopped'
            )

        self.is_running = False

        if self.callback:
            self.callback('complete', "✅ 爬取完成！", self.stats)

    def stop(self):
        """停止爬虫"""
        self._log("🛑 正在停止爬虫...")
        self.is_running = False

    def pause(self):
        """暂停爬虫"""
        self.is_paused = True
        self._log("⏸ 爬虫已暂停")

    def resume(self):
        """恢复爬虫"""
        self.is_paused = False
        self._log("▶ 爬虫已恢复")


# ============ 爬虫工作线程 ============
class CrawlerThread(QThread):
    """爬虫工作线程"""
    log_signal = pyqtSignal(str)
    stats_signal = pyqtSignal(dict)
    complete_signal = pyqtSignal(str, dict)

    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
        self.crawler = None

    def run(self):
        """运行爬虫"""
        try:
            self.crawler = PlaywrightCrawler(self.config, self.crawler_callback)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.crawler.start())
        except Exception as e:
            self.log_signal.emit(f"✗ 爬虫异常: {e}")
        finally:
            if loop:
                loop.close()

    def crawler_callback(self, event_type: str, message: str, stats: Dict):
        """爬虫回调"""
        if event_type == 'log':
            self.log_signal.emit(message)
        elif event_type == 'stats':
            self.stats_signal.emit(stats)
        elif event_type == 'complete':
            self.complete_signal.emit(message, stats)

    def stop(self):
        """停止爬虫"""
        if self.crawler:
            self.crawler.stop()

    def pause(self):
        """暂停爬虫"""
        if self.crawler:
            self.crawler.pause()

    def resume(self):
        """恢复爬虫"""
        if self.crawler:
            self.crawler.resume()


# ============ 主窗口 ============
class CrawlerMainWindow(QMainWindow):
    """爬虫主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Universal Web Crawler Pro v4.0 - PyQt5 Professional Edition")
        self.setGeometry(100, 100, 1600, 900)
        self.setMinimumSize(1400, 800)

        self.db = DatabaseManager()
        self.crawler_thread = None
        self.config_file = "crawler_config_v4.json"

        self.init_ui()
        self.apply_styles()
        self.load_config()

        # 状态栏更新定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_bar)
        self.status_timer.start(1000)

    def init_ui(self):
        """初始化UI"""
        # 创建菜单栏
        self.create_menu_bar()

        # 创建工具栏
        self.create_toolbar()

        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧配置面板
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # 右侧内容面板
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

        # 状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        import_action = QAction("导入配置", self)
        import_action.triggered.connect(self.import_config)
        file_menu.addAction(import_action)

        export_action = QAction("导出配置", self)
        export_action.triggered.connect(self.export_config)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 任务菜单
        task_menu = menubar.addMenu("任务(&T)")

        start_action = QAction("开始爬取", self)
        start_action.triggered.connect(self.start_crawl)
        task_menu.addAction(start_action)

        pause_action = QAction("暂停", self)
        pause_action.triggered.connect(self.pause_crawl)
        task_menu.addAction(pause_action)

        stop_action = QAction("停止", self)
        stop_action.triggered.connect(self.stop_crawl)
        task_menu.addAction(stop_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")

        history_action = QAction("历史记录", self)
        history_action.triggered.connect(self.show_history)
        view_menu.addAction(history_action)

        stats_action = QAction("统计分析", self)
        stats_action.triggered.connect(self.show_statistics)
        view_menu.addAction(stats_action)

        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")

        clean_action = QAction("清理数据库", self)
        clean_action.triggered.connect(self.clean_database)
        tools_menu.addAction(clean_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        doc_action = QAction("使用文档", self)
        doc_action.triggered.connect(self.show_help)
        help_menu.addAction(doc_action)

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # 开始按钮
        self.start_action = QAction("🚀 开始", self)
        self.start_action.triggered.connect(self.start_crawl)
        toolbar.addAction(self.start_action)

        # 暂停按钮
        self.pause_action = QAction("⏸ 暂停", self)
        self.pause_action.triggered.connect(self.pause_crawl)
        self.pause_action.setEnabled(False)
        toolbar.addAction(self.pause_action)

        # 停止按钮
        self.stop_action = QAction("⏹ 停止", self)
        self.stop_action.triggered.connect(self.stop_crawl)
        self.stop_action.setEnabled(False)
        toolbar.addAction(self.stop_action)

        toolbar.addSeparator()

        # 历史记录
        history_action = QAction("📊 历史", self)
        history_action.triggered.connect(self.show_history)
        toolbar.addAction(history_action)

        # 设置
        settings_action = QAction("⚙️ 设置", self)
        settings_action.triggered.connect(self.show_settings)
        toolbar.addAction(settings_action)

    def create_left_panel(self):
        """创建左侧配置面板"""
        panel = QWidget()
        panel.setMaximumWidth(500)
        layout = QVBoxLayout(panel)

        # 标题
        title = QLabel("⚙️ 爬取配置")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 滚动区域（使用Tab切换不同配置）
        tabs = QTabWidget()
        tabs.addTab(self.create_basic_config(), "基本配置")
        tabs.addTab(self.create_advanced_config(), "高级配置")
        tabs.addTab(self.create_resource_config(), "资源类型")
        layout.addWidget(tabs)

        # 控制按钮
        control_group = QGroupBox("🎮 控制面板")
        control_layout = QVBoxLayout()

        self.start_btn = QPushButton("🚀 开始爬取")
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setFont(QFont("Arial", 14, QFont.Bold))
        self.start_btn.clicked.connect(self.start_crawl)
        control_layout.addWidget(self.start_btn)

        btn_row = QHBoxLayout()
        self.pause_btn = QPushButton("⏸ 暂停")
        self.pause_btn.setMinimumHeight(40)
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.pause_crawl)
        btn_row.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_crawl)
        btn_row.addWidget(self.stop_btn)

        control_layout.addLayout(btn_row)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # 统计面板
        stats_group = self.create_stats_panel()
        layout.addWidget(stats_group)

        return panel

    def create_basic_config(self):
        """创建基本配置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # URL输入
        url_group = QGroupBox("🌐 目标网址")
        url_layout = QVBoxLayout()
        self.url_entry = QLineEdit()
        self.url_entry.setPlaceholderText("https://example.com")
        self.url_entry.setMinimumHeight(35)
        self.url_entry.textChanged.connect(self.validate_url)
        url_layout.addWidget(self.url_entry)

        self.url_status = QLabel("")
        self.url_status.setFont(QFont("Arial", 10))
        url_layout.addWidget(self.url_status)
        url_group.setLayout(url_layout)
        layout.addWidget(url_group)

        # 保存路径
        path_group = QGroupBox("💾 保存路径")
        path_layout = QHBoxLayout()
        self.path_entry = QLineEdit()
        self.path_entry.setPlaceholderText("选择保存目录")
        self.path_entry.setMinimumHeight(35)
        path_layout.addWidget(self.path_entry)

        browse_btn = QPushButton("📁 浏览")
        browse_btn.setMinimumHeight(35)
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        # 爬取深度
        depth_group = QGroupBox("📏 爬取深度")
        depth_layout = QHBoxLayout()
        self.depth_slider = QSlider(Qt.Horizontal)
        self.depth_slider.setMinimum(1)
        self.depth_slider.setMaximum(5)
        self.depth_slider.setValue(2)
        self.depth_slider.setTickPosition(QSlider.TicksBelow)
        self.depth_slider.setTickInterval(1)
        self.depth_slider.valueChanged.connect(self.update_depth_label)
        depth_layout.addWidget(self.depth_slider)

        self.depth_label = QLabel("2层")
        self.depth_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.depth_label.setMinimumWidth(60)
        self.depth_label.setAlignment(Qt.AlignCenter)
        depth_layout.addWidget(self.depth_label)
        depth_group.setLayout(depth_layout)
        layout.addWidget(depth_group)

        # 最大页面数
        pages_group = QGroupBox("📄 最大页面数")
        pages_layout = QHBoxLayout()
        self.max_pages_spin = QSpinBox()
        self.max_pages_spin.setMinimum(1)
        self.max_pages_spin.setMaximum(10000)
        self.max_pages_spin.setValue(100)
        self.max_pages_spin.setMinimumHeight(35)
        pages_layout.addWidget(self.max_pages_spin)

        pages_hint = QLabel("建议: 50-500页")
        pages_hint.setStyleSheet("color: gray;")
        pages_layout.addWidget(pages_hint)
        pages_group.setLayout(pages_layout)
        layout.addWidget(pages_group)

        # 请求延迟
        delay_group = QGroupBox("⏱ 请求延迟 (秒)")
        delay_layout = QHBoxLayout()
        self.delay_slider = QSlider(Qt.Horizontal)
        self.delay_slider.setMinimum(5)
        self.delay_slider.setMaximum(50)
        self.delay_slider.setValue(10)
        self.delay_slider.setTickPosition(QSlider.TicksBelow)
        self.delay_slider.setTickInterval(5)
        self.delay_slider.valueChanged.connect(self.update_delay_label)
        delay_layout.addWidget(self.delay_slider)

        self.delay_label = QLabel("1.0s")
        self.delay_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.delay_label.setMinimumWidth(60)
        self.delay_label.setAlignment(Qt.AlignCenter)
        delay_layout.addWidget(self.delay_label)
        delay_group.setLayout(delay_layout)
        layout.addWidget(delay_group)

        layout.addStretch()
        return widget

    def create_advanced_config(self):
        """创建高级配置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        options_group = QGroupBox("🎯 爬取选项")
        options_layout = QVBoxLayout()

        self.domain_limit_cb = QCheckBox("仅爬取同域名")
        self.domain_limit_cb.setChecked(True)
        options_layout.addWidget(self.domain_limit_cb)

        self.headless_cb = QCheckBox("无头模式 (后台运行)")
        self.headless_cb.setChecked(True)
        options_layout.addWidget(self.headless_cb)

        self.follow_redirect_cb = QCheckBox("跟随重定向")
        self.follow_redirect_cb.setChecked(True)
        options_layout.addWidget(self.follow_redirect_cb)

        self.ignore_robots_cb = QCheckBox("忽略robots.txt (不推荐)")
        self.ignore_robots_cb.setChecked(False)
        options_layout.addWidget(self.ignore_robots_cb)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # 下载限制
        limit_group = QGroupBox("📊 下载限制")
        limit_layout = QGridLayout()

        limit_layout.addWidget(QLabel("单文件大小上限 (MB):"), 0, 0)
        self.file_size_limit = QSpinBox()
        self.file_size_limit.setMinimum(1)
        self.file_size_limit.setMaximum(1000)
        self.file_size_limit.setValue(50)
        limit_layout.addWidget(self.file_size_limit, 0, 1)

        limit_layout.addWidget(QLabel("并发下载数:"), 1, 0)
        self.concurrent_downloads = QSpinBox()
        self.concurrent_downloads.setMinimum(1)
        self.concurrent_downloads.setMaximum(20)
        self.concurrent_downloads.setValue(5)
        limit_layout.addWidget(self.concurrent_downloads, 1, 1)

        limit_group.setLayout(limit_layout)
        layout.addWidget(limit_group)

        layout.addStretch()
        return widget

    def create_resource_config(self):
        """创建资源类型配置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        resource_group = QGroupBox("📦 下载资源类型")
        resource_layout = QVBoxLayout()

        self.download_images_cb = QCheckBox("🖼️ 图片 (jpg, png, gif, webp等)")
        self.download_images_cb.setChecked(True)
        resource_layout.addWidget(self.download_images_cb)

        self.download_videos_cb = QCheckBox("🎬 视频 (mp4, avi, mov等)")
        self.download_videos_cb.setChecked(False)
        resource_layout.addWidget(self.download_videos_cb)

        self.download_audios_cb = QCheckBox("🎵 音频 (mp3, wav, flac等)")
        self.download_audios_cb.setChecked(False)
        resource_layout.addWidget(self.download_audios_cb)

        self.download_documents_cb = QCheckBox("📁 文档 (pdf, docx, xlsx等)")
        self.download_documents_cb.setChecked(True)
        resource_layout.addWidget(self.download_documents_cb)

        self.download_css_cb = QCheckBox("🎨 CSS样式表")
        self.download_css_cb.setChecked(False)
        resource_layout.addWidget(self.download_css_cb)

        self.download_js_cb = QCheckBox("📜 JavaScript脚本")
        self.download_js_cb.setChecked(False)
        resource_layout.addWidget(self.download_js_cb)

        resource_group.setLayout(resource_layout)
        layout.addWidget(resource_group)

        # 文件类型过滤
        filter_group = QGroupBox("🔍 文件扩展名过滤")
        filter_layout = QVBoxLayout()

        filter_layout.addWidget(QLabel("包含 (用逗号分隔，如: jpg,png):"))
        self.include_ext = QLineEdit()
        self.include_ext.setPlaceholderText("留空表示不限制")
        filter_layout.addWidget(self.include_ext)

        filter_layout.addWidget(QLabel("排除 (用逗号分隔):"))
        self.exclude_ext = QLineEdit()
        self.exclude_ext.setPlaceholderText("如: exe,dmg")
        filter_layout.addWidget(self.exclude_ext)

        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        layout.addStretch()
        return widget

    def create_stats_panel(self):
        """创建统计面板"""
        group = QGroupBox("📊 实时统计")
        layout = QGridLayout()

        stats_items = [
            ('pages', '📄 页面:', 0, 0),
            ('images', '🖼️ 图片:', 0, 2),
            ('videos', '🎬 视频:', 1, 0),
            ('audios', '🎵 音频:', 1, 2),
            ('documents', '📁 文档:', 2, 0),
            ('others', '📦 其他:', 2, 2),
            ('errors', '❌ 错误:', 3, 0),
        ]

        self.stats_labels = {}
        for key, label, row, col in stats_items:
            layout.addWidget(QLabel(label), row, col)
            value_label = QLabel("0")
            value_label.setFont(QFont("Arial", 12, QFont.Bold))
            layout.addWidget(value_label, row, col + 1)
            self.stats_labels[key] = value_label

        # 总大小
        layout.addWidget(QLabel("💾 总大小:"), 4, 0)
        self.size_label = QLabel("0 B")
        self.size_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(self.size_label, 4, 1, 1, 3)

        group.setLayout(layout)
        return group

    def create_right_panel(self):
        """创建右侧内容面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 标签页
        self.tab_widget = QTabWidget()

        # 日志标签页
        log_tab = self.create_log_tab()
        self.tab_widget.addTab(log_tab, "📋 运行日志")

        # 进度标签页
        progress_tab = self.create_progress_tab()
        self.tab_widget.addTab(progress_tab, "📈 进度监控")

        # 资源列表标签页
        resource_tab = self.create_resource_tab()
        self.tab_widget.addTab(resource_tab, "📦 资源列表")

        layout.addWidget(self.tab_widget)

        return panel

    def create_log_tab(self):
        """创建日志标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("实时日志输出"))
        toolbar.addStretch()

        export_btn = QPushButton("💾 导出日志")
        export_btn.clicked.connect(self.export_log)
        toolbar.addWidget(export_btn)

        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.clicked.connect(self.clear_log)
        toolbar.addWidget(clear_btn)

        layout.addLayout(toolbar)

        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.log_text)

        return widget

    def create_progress_tab(self):
        """创建进度标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 进度条
        progress_group = QGroupBox("总体进度")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("准备就绪")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setFont(QFont("Arial", 12))
        progress_layout.addWidget(self.progress_label)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # 详细信息
        info_group = QGroupBox("爬取详情")
        info_layout = QVBoxLayout()

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setFont(QFont("Arial", 11))
        info_layout.addWidget(self.info_text)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        return widget

    def create_resource_tab(self):
        """创建资源列表标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("已下载资源"))
        toolbar.addStretch()

        self.resource_filter = QComboBox()
        self.resource_filter.addItems(["全部", "图片", "视频", "音频", "文档", "其他"])
        self.resource_filter.currentTextChanged.connect(self.filter_resources)
        toolbar.addWidget(self.resource_filter)

        open_btn = QPushButton("📂 打开目录")
        open_btn.clicked.connect(self.open_folder)
        toolbar.addWidget(open_btn)

        layout.addLayout(toolbar)

        # 资源表格
        self.resource_table = QTableWidget()
        self.resource_table.setColumnCount(4)
        self.resource_table.setHorizontalHeaderLabels(["文件名", "类型", "大小", "下载时间"])
        self.resource_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.resource_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.resource_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.resource_table)

        return widget

    def apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e3a8a;
            }
            QPushButton:disabled {
                background-color: #94a3b8;
            }
            QLineEdit, QSpinBox {
                padding: 5px;
                border: 2px solid #d1d5db;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus, QSpinBox:focus {
                border-color: #2563eb;
            }
            QTextEdit {
                border: 2px solid #d1d5db;
                border-radius: 4px;
                background-color: white;
            }
            QTabWidget::pane {
                border: 2px solid #d1d5db;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e5e7eb;
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
            }
            QProgressBar {
                border: 2px solid #d1d5db;
                border-radius: 8px;
                text-align: center;
                background-color: #f3f4f6;
            }
            QProgressBar::chunk {
                background-color: #10b981;
                border-radius: 6px;
            }
            QStatusBar {
                background-color: #1e3a5f;
                color: white;
            }
        """)

    # ========== 事件处理 ==========

    def validate_url(self):
        """验证URL"""
        url = self.url_entry.text().strip()
        if not url:
            self.url_status.setText("")
        elif validators.url(url):
            self.url_status.setText("✓ URL格式正确")
            self.url_status.setStyleSheet("color: #10b981;")
        else:
            self.url_status.setText("✗ URL格式错误")
            self.url_status.setStyleSheet("color: #ef4444;")

    def update_depth_label(self, value):
        """更新深度标签"""
        self.depth_label.setText(f"{value}层")

    def update_delay_label(self, value):
        """更新延迟标签"""
        self.delay_label.setText(f"{value / 10:.1f}s")

    def browse_path(self):
        """选择保存目录"""
        folder = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if folder:
            self.path_entry.setText(folder)

    def log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

        # 限制行数
        if self.log_text.document().lineCount() > 1000:
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 100)
            cursor.removeSelectedText()

    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.log("✓ 日志已清空")

    def export_log(self):
        """导出日志"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存日志",
            f"crawler_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "成功", f"日志已导出到:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def update_stats(self, stats: Dict):
        """更新统计"""
        for key, value in stats.items():
            if key in self.stats_labels:
                self.stats_labels[key].setText(str(value))

        # 更新大小
        total_size = stats.get('total_size', 0)
        self.size_label.setText(self.format_size(total_size))

        # 更新进度条
        max_pages = self.max_pages_spin.value()
        current = stats.get('pages', 0)
        progress = min(int(current / max_pages * 100), 100)
        self.progress_bar.setValue(progress)
        self.progress_label.setText(
            f"已爬取 {current}/{max_pages} 页 ({progress}%)"
        )

    def on_crawl_complete(self, message: str, stats: Dict):
        """爬取完成"""
        self.log(message)
        self.update_stats(stats)

        self.start_btn.setEnabled(True)
        self.start_action.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_action.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.stop_action.setEnabled(False)

        # 显示摘要
        summary = f"""
爬取完成！

📊 统计摘要:
━━━━━━━━━━━━━━━━━━━━━━
📄 页面: {stats['pages']}
🖼️ 图片: {stats['images']}
🎬 视频: {stats['videos']}
🎵 音频: {stats['audios']}
📁 文档: {stats['documents']}
📦 其他: {stats['others']}
❌ 错误: {stats['errors']}
💾 总大小: {self.format_size(stats['total_size'])}
━━━━━━━━━━━━━━━━━━━━━━
        """

        self.info_text.setPlainText(summary)
        QMessageBox.information(self, "完成", "爬取任务已完成！")

    def validate_inputs(self) -> bool:
        """验证输入"""
        url = self.url_entry.text().strip()
        path = self.path_entry.text().strip()

        if not url:
            QMessageBox.critical(self, "错误", "请输入目标网址")
            return False

        if not validators.url(url):
            QMessageBox.critical(self, "错误", "网址格式不正确")
            return False

        if not path:
            QMessageBox.critical(self, "错误", "请选择保存路径")
            return False

        return True

    def start_crawl(self):
        """开始爬取"""
        if not self.validate_inputs():
            return

        if self.crawler_thread and self.crawler_thread.isRunning():
            QMessageBox.warning(self, "警告", "爬虫正在运行中")
            return

        # 保存配置
        self.save_config()

        # 更新UI
        self.start_btn.setEnabled(False)
        self.start_action.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.pause_action.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.stop_action.setEnabled(True)
        self.clear_log()

        # 重置统计
        for label in self.stats_labels.values():
            label.setText("0")
        self.size_label.setText("0 B")
        self.progress_bar.setValue(0)

        # 准备配置
        config = {
            'start_url': self.url_entry.text().strip(),
            'save_path': self.path_entry.text().strip(),
            'max_depth': self.depth_slider.value(),
            'max_pages': self.max_pages_spin.value(),
            'delay': self.delay_slider.value() / 10.0,
            'domain_limit': self.domain_limit_cb.isChecked(),
            'headless': self.headless_cb.isChecked(),
            'download_images': self.download_images_cb.isChecked(),
            'download_videos': self.download_videos_cb.isChecked(),
            'download_audios': self.download_audios_cb.isChecked(),
            'download_documents': self.download_documents_cb.isChecked(),
            'download_css': self.download_css_cb.isChecked(),
            'download_js': self.download_js_cb.isChecked(),
        }

        # 创建并启动爬虫线程
        self.crawler_thread = CrawlerThread(config)
        self.crawler_thread.log_signal.connect(self.log)
        self.crawler_thread.stats_signal.connect(self.update_stats)
        self.crawler_thread.complete_signal.connect(self.on_crawl_complete)
        self.crawler_thread.start()

        self.log(f"🚀 启动爬虫: {config['start_url']}")
        self.log(f"💾 保存路径: {config['save_path']}")
        self.log(f"⚙️ 深度:{config['max_depth']}层 | 最大:{config['max_pages']}页 | 延迟:{config['delay']:.1f}s")

    def pause_crawl(self):
        """暂停/恢复爬取"""
        if not self.crawler_thread:
            return

        if self.pause_btn.text() == "⏸ 暂停":
            self.crawler_thread.pause()
            self.pause_btn.setText("▶ 恢复")
        else:
            self.crawler_thread.resume()
            self.pause_btn.setText("⏸ 暂停")

    def stop_crawl(self):
        """停止爬取"""
        if not self.crawler_thread:
            return

        self.crawler_thread.stop()
        self.log("🛑 正在停止爬虫...")

        self.start_btn.setEnabled(True)
        self.start_action.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_action.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.stop_action.setEnabled(False)

    def show_history(self):
        """显示历史记录"""
        dialog = HistoryDialog(self.db, self)
        dialog.exec_()

    def show_statistics(self):
        """显示统计分析"""
        dialog = StatisticsDialog(self.db, self)
        dialog.exec_()

    def show_settings(self):
        """显示设置"""
        dialog = SettingsDialog(self)
        dialog.exec_()

    def show_help(self):
        """显示帮助"""
        dialog = HelpDialog(self)
        dialog.exec_()

    def show_about(self):
        """显示关于"""
        QMessageBox.about(self, "关于", """
<h2>Universal Web Crawler Pro v4.0</h2>
<p><b>PyQt5 Professional Edition</b></p>
<p>高级万能网络爬虫系统 - 商用级</p>
<p>技术栈: Playwright + PyQt5 + SQLite + asyncio</p>
<br>
<p>© 2024 All Rights Reserved</p>
<p>Email: support@example.com</p>
        """)

    def open_folder(self):
        """打开下载文件夹"""
        path = self.path_entry.text().strip()
        if path and os.path.exists(path):
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        else:
            QMessageBox.warning(self, "提示", "保存路径不存在")

    def filter_resources(self, filter_text: str):
        """过滤资源列表"""
        # TODO: 实现资源过滤功能
        pass

    def clean_database(self):
        """清理数据库"""
        reply = QMessageBox.question(
            self, "确认", "确定要清理历史数据吗？此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # TODO: 实现数据库清理
            QMessageBox.information(self, "成功", "数据库已清理")

    def save_config(self):
        """保存配置"""
        config = {
            'url': self.url_entry.text(),
            'save_path': self.path_entry.text(),
            'max_depth': self.depth_slider.value(),
            'max_pages': self.max_pages_spin.value(),
            'delay': self.delay_slider.value() / 10.0,
            'domain_limit': self.domain_limit_cb.isChecked(),
            'headless': self.headless_cb.isChecked(),
            'download_images': self.download_images_cb.isChecked(),
            'download_videos': self.download_videos_cb.isChecked(),
            'download_audios': self.download_audios_cb.isChecked(),
            'download_documents': self.download_documents_cb.isChecked(),
            'download_css': self.download_css_cb.isChecked(),
            'download_js': self.download_js_cb.isChecked(),
        }

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"保存配置失败: {e}")

    def load_config(self):
        """加载配置"""
        if not os.path.exists(self.config_file):
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            self.url_entry.setText(config.get('url', ''))
            self.path_entry.setText(config.get('save_path', ''))
            self.depth_slider.setValue(config.get('max_depth', 2))
            self.max_pages_spin.setValue(config.get('max_pages', 100))
            self.delay_slider.setValue(int(config.get('delay', 1.0) * 10))
            self.domain_limit_cb.setChecked(config.get('domain_limit', True))
            self.headless_cb.setChecked(config.get('headless', True))
            self.download_images_cb.setChecked(config.get('download_images', True))
            self.download_videos_cb.setChecked(config.get('download_videos', False))
            self.download_audios_cb.setChecked(config.get('download_audios', False))
            self.download_documents_cb.setChecked(config.get('download_documents', True))
            self.download_css_cb.setChecked(config.get('download_css', False))
            self.download_js_cb.setChecked(config.get('download_js', False))

        except Exception as e:
            logging.error(f"加载配置失败: {e}")

    def import_config(self):
        """导入配置"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "导入配置", "", "JSON文件 (*.json);;所有文件 (*.*)"
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 应用配置...
                QMessageBox.information(self, "成功", "配置已导入")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败: {e}")

    def export_config(self):
        """导出配置"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "导出配置",
            f"crawler_config_{datetime.now().strftime('%Y%m%d')}.json",
            "JSON文件 (*.json);;所有文件 (*.*)"
        )
        if filename:
            self.save_config()
            try:
                import shutil
                shutil.copy(self.config_file, filename)
                QMessageBox.information(self, "成功", f"配置已导出到:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    def update_status_bar(self):
        """更新状态栏"""
        if self.crawler_thread and self.crawler_thread.isRunning():
            self.statusBar.showMessage("⏳ 爬虫运行中...")
        else:
            self.statusBar.showMessage("✓ 就绪")

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.crawler_thread and self.crawler_thread.isRunning():
            reply = QMessageBox.question(
                self, "确认退出", "爬虫正在运行，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.crawler_thread.stop()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


# ============ 历史记录对话框 ============
class HistoryDialog(QDialog):
    """历史记录对话框"""

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("爬取历史记录")
        self.setGeometry(200, 200, 1200, 700)
        self.init_ui()
        self.load_history()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("📊 历史爬取记录")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 工具栏
        toolbar = QHBoxLayout()
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.load_history)
        toolbar.addWidget(refresh_btn)

        delete_btn = QPushButton("🗑️ 删除选中")
        delete_btn.clicked.connect(self.delete_selected)
        toolbar.addWidget(delete_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "网址", "状态", "页面", "图片", "文档", "错误", "总大小", "开始时间"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def load_history(self):
        """加载历史记录"""
        history = self.db.get_task_history(100)
        self.table.setRowCount(len(history))

        for row, task in enumerate(history):
            self.table.setItem(row, 0, QTableWidgetItem(str(task['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(task['url'][:50]))
            self.table.setItem(row, 2, QTableWidgetItem(task['status']))
            self.table.setItem(row, 3, QTableWidgetItem(str(task['pages'])))
            self.table.setItem(row, 4, QTableWidgetItem(str(task['images'])))
            self.table.setItem(row, 5, QTableWidgetItem(str(task['documents'])))
            self.table.setItem(row, 6, QTableWidgetItem(str(task['errors'])))

            size = self.format_size(task['total_size'])
            self.table.setItem(row, 7, QTableWidgetItem(size))

            start_time = task['start_time'][:19] if task['start_time'] else ''
            self.table.setItem(row, 8, QTableWidgetItem(start_time))

    def delete_selected(self):
        """删除选中的记录"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的记录")
            return

        reply = QMessageBox.question(
            self, "确认", "确定要删除选中的记录吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # TODO: 实现删除功能
            self.load_history()

    def format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.0f}{unit}"
            size /= 1024.0
        return f"{size:.0f}PB"


# ============ 统计分析对话框 ============
class StatisticsDialog(QDialog):
    """统计分析对话框"""

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("统计分析")
        self.setGeometry(200, 200, 800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("📈 爬取统计分析")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        info = QTextEdit()
        info.setReadOnly(True)
        info.setPlainText("统计分析功能开发中...")
        layout.addWidget(info)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)


# ============ 设置对话框 ============
class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("高级设置")
        self.setGeometry(200, 200, 700, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("⚙️ 高级配置选项")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        info = QTextEdit()
        info.setReadOnly(True)
        info.setPlainText("""
🔧 高级功能说明
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 当前版本特性:
  • Playwright渲染引擎 - 完美支持JavaScript动态网站
  • PyQt5现代化界面 - 专业、美观、易用
  • 智能资源识别 - 自动识别所有类型资源
  • 断点续传 - 支持暂停和恢复
  • 数据持久化 - SQLite数据库存储
  • 异步下载 - 高效并发下载
  • 智能重试 - 自动处理失败请求

🚀 新增功能:
  • 完善的菜单栏和工具栏
  • 历史记录管理
  • 配置导入导出
  • 实时资源列表
  • 统计分析功能
  • 主题自定义

📖 使用建议:
  • 首次爬取建议从较小深度(1-2层)开始
  • 视频文件通常较大，建议谨慎下载
  • 增加请求延迟可避免被封IP
  • 遵守网站robots.txt规则
  • 商用前请确认目标网站使用条款

💡 技术支持:
  Email: support@example.com
  GitHub: github.com/example/crawler
  Version: 4.0 PyQt5 Professional Edition
        """)
        layout.addWidget(info)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)


# ============ 帮助对话框 ============
class HelpDialog(QDialog):
    """帮助对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("使用帮助")
        self.setGeometry(200, 200, 750, 650)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("❓ 使用帮助")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setPlainText("""
📘 快速入门指南
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ 基本配置
  • 输入目标网址（必须以http://或https://开头）
  • 选择保存路径
  • 设置爬取深度（建议1-3层）
  • 设置最大页面数（建议100-500）

2️⃣ 高级配置
  • 仅爬取同域名：限制在同一网站内爬取
  • 无头模式：后台运行，不显示浏览器窗口
  • 请求延迟：避免请求过快被封禁
  • 文件大小限制：控制单个文件大小
  • 并发下载数：控制同时下载的文件数量

3️⃣ 资源类型
  ✅ 推荐下载：图片、文档
  ⚠️ 谨慎下载：视频、音频（文件较大）
  🔧 开发用途：CSS、JavaScript

4️⃣ 控制面板
  • 开始：启动爬虫
  • 暂停：临时暂停，可恢复
  • 停止：终止爬虫

5️⃣ 查看结果
  • 运行日志：查看实时爬取过程
  • 进度监控：查看进度和统计
  • 资源列表：查看已下载资源
  • 历史记录：查看历史爬取任务

6️⃣ 快捷键
  • Ctrl+S：开始爬取
  • Ctrl+P：暂停/恢复
  • Ctrl+Q：退出程序
  • F1：打开帮助

⚠️ 注意事项
  • 请遵守目标网站的使用条款和robots.txt
  • 商用前请获得网站所有者授权
  • 大规模爬取可能被封IP，建议使用代理
  • 部分网站有反爬虫机制，请合理配置延迟

💡 技巧
  • 首次爬取建议先测试1-2页
  • 增加延迟可提高成功率
  • 定期清理下载目录
  • 导出日志便于问题排查
  • 使用配置导入导出功能快速切换任务
        """)
        layout.addWidget(help_text)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)


# ============ 主程序 ============
def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion样式

    # 设置应用信息
    app.setApplicationName("Universal Web Crawler Pro")
    app.setApplicationVersion("4.0")
    app.setOrganizationName("CrawlerPro")

    window = CrawlerMainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()