# -*- coding: utf-8 -*-
"""
Web Content Extractor Pro - 专业网页内容提取工具
基于PyQt5和BeautifulSoup开发，支持多平台内容提取、多格式输出、数学公式处理
Version: 7.0
github网址： https://github.com/lyp0746
QQ邮箱：1610369302@qq.com
作者：LYP

功能特性:
- 支持平台: 菜鸟教程、CSDN博客/专栏、知乎专栏、简书
- 输出格式: Markdown、HTML、PDF (专业书籍风格)
- 数学公式: 完整LaTeX/MathJax 3.0支持
- CSDN增强: 深度内容提取和清理
- GUI优化: 大字体、易操作、专业外观
============================================
"""
import sys
import os
import re
from pathlib import Path
from typing import List, Tuple
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QSettings
from PyQt5.QtGui import QFont, QTextCursor

# PDF生成 - WeasyPrint 59.0+
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASY_AVAILABLE = True
except ImportError:
    WEASY_AVAILABLE = False


# ======================== 数据结构 ========================
class Article:
    """文章数据结构"""
    def __init__(self, title: str, url: str, level: int = 1):
        self.title = title
        self.url = url
        self.level = level
        self.content = ""
        self.html_content = ""
        self.author = ""
        self.date = ""
        self.category = ""


# ======================== 爬虫基类 ========================
class BaseCrawler:
    """爬虫基类 - 提供通用功能"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        self.session = requests.Session()
        self.img_cache = {}
        
    def download_image(self, url: str, img_dir: str, referer: str = None) -> str:
        """下载图片到本地"""
        try:
            if url in self.img_cache:
                return self.img_cache[url]
            
            headers = self.headers.copy()
            if referer:
                headers['Referer'] = referer
            
            response = self.session.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                # 获取扩展名
                content_type = response.headers.get('content-type', '')
                ext_map = {
                    'image/png': '.png',
                    'image/jpeg': '.jpg',
                    'image/jpg': '.jpg',
                    'image/gif': '.gif',
                    'image/webp': '.webp',
                    'image/svg+xml': '.svg'
                }
                ext = '.png'
                for mime, extension in ext_map.items():
                    if mime in content_type:
                        ext = extension
                        break
                
                img_name = f"img_{abs(hash(url))}{ext}"
                img_path = os.path.join(img_dir, img_name)
                
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                
                result = f"images/{img_name}"
                self.img_cache[url] = result
                return result
                
        except Exception as e:
            print(f"图片下载失败: {url}, {e}")
        
        return url
    
    def clean_html(self, soup):
        """清理HTML - 移除无关元素"""
        # 移除脚本和样式
        for tag in soup.find_all(['script', 'style', 'iframe', 'noscript']):
            tag.decompose()
        
        # 移除广告元素
        ad_patterns = [
            'ad', 'advertisement', 'adsbygoogle', 'sponsor', 
            'promo', 'banner', 'popup', 'modal'
        ]
        for pattern in ad_patterns:
            for tag in soup.find_all(class_=re.compile(pattern, re.I)):
                tag.decompose()
        
        return soup
    
    def process_math_formulas(self, content):
        """
        增强数学公式处理
        支持格式:
        - LaTeX行内: \( ... \) 或 $ ... $
        - LaTeX块级: \[ ... \] 或 $$ ... $$
        - MathJax script标签
        """
        content_str = str(content)
        
        # LaTeX行内公式: \( ... \)
        content_str = re.sub(
            r'\\\\?\((.*?)\\\\?\)', 
            r'<span class="math-inline">$\1$</span>', 
            content_str
        )
        
        # LaTeX块级公式: \[ ... \]
        content_str = re.sub(
            r'\\\\?\[(.*?)\\\\?\]', 
            r'<div class="math-display">$$\1$$</div>', 
            content_str, 
            flags=re.DOTALL
        )
        
        # 处理MathJax script标签
        soup = BeautifulSoup(content_str, 'html.parser')
        
        # 行内公式
        for script in soup.find_all('script', type='math/tex'):
            formula = script.string
            if formula:
                span = soup.new_tag('span', attrs={'class': 'math-inline'})
                span.string = f'${formula}$'
                script.replace_with(span)
        
        # 块级公式
        for script in soup.find_all('script', type='math/tex; mode=display'):
            formula = script.string
            if formula:
                div = soup.new_tag('div', attrs={'class': 'math-display'})
                div.string = f'$${formula}$$'
                script.replace_with(div)
        
        # 处理CSDN的公式标记
        for span in soup.find_all('span', class_=re.compile('katex|mathjax')):
            formula_text = span.get_text()
            if formula_text:
                new_span = soup.new_tag('span', attrs={'class': 'math-inline'})
                new_span.string = f'${formula_text}$'
                span.replace_with(new_span)
        
        return soup


# ======================== 菜鸟教程爬虫 ========================
class RunoobCrawler(BaseCrawler):
    """菜鸟教程爬虫"""
    
    def extract_tutorial_info(self, url: str) -> Tuple[str, List[Article]]:
        response = self.session.get(url, headers=self.headers, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取标题
        title_tag = soup.find('h1') or soup.find('title')
        title = title_tag.get_text().strip() if title_tag else "未知教程"
        title = re.sub(r'\s*[-|]?\s*菜鸟教程.*', '', title)
        
        # 提取章节
        articles = []
        sidebar = soup.find('div', {'id': 'leftcolumn'})
        
        if sidebar:
            links = sidebar.find_all('a')
            for link in links:
                href = link.get('href')
                if href and not href.startswith('#') and not href.startswith('javascript'):
                    full_url = urljoin(url, href)
                    link_title = link.get_text().strip()
                    if link_title and len(link_title) > 1:
                        articles.append(Article(link_title, full_url))
        
        # 去重
        seen = set()
        unique = []
        for art in articles:
            if art.url not in seen:
                seen.add(art.url)
                unique.append(art)
        
        return title, unique
    
    def extract_article_content(self, article: Article, download_images: bool, img_dir: str):
        try:
            response = self.session.get(article.url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            content = soup.find('div', {'id': 'content'}) or soup.find('article') or soup.find('div', class_='article-intro')
            
            if not content:
                article.content = "_内容获取失败_"
                article.html_content = "<p><em>内容获取失败</em></p>"
                return
            
            content = self.clean_html(content)
            content = self.process_math_formulas(content)
            
            # 处理图片
            if download_images:
                for img in content.find_all('img'):
                    src = img.get('src') or img.get('data-src')
                    if src:
                        img_url = urljoin(article.url, src)
                        local_path = self.download_image(img_url, img_dir)
                        img['src'] = local_path
                        if not img.get('alt'):
                            img['alt'] = 'image'
            
            # 处理代码块
            for pre in content.find_all('pre'):
                pre['class'] = 'code-block'
            
            article.html_content = str(content)
            article.content = self.html_to_markdown(content)
            
        except Exception as e:
            article.content = f"_提取失败: {str(e)}_"
            article.html_content = f"<p><em>提取失败: {str(e)}</em></p>"
    
    def html_to_markdown(self, content) -> str:
        lines = []
        for element in content.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'pre', 'ul', 'ol', 'blockquote']):
            tag = element.name
            text = element.get_text().strip()
            
            if tag == 'h1' and text:
                lines.append(f"\n# {text}\n")
            elif tag == 'h2' and text:
                lines.append(f"\n## {text}\n")
            elif tag == 'h3' and text:
                lines.append(f"\n### {text}\n")
            elif tag == 'h4' and text:
                lines.append(f"\n#### {text}\n")
            elif tag == 'p' and text:
                lines.append(f"\n{text}\n")
            elif tag == 'pre':
                lines.append(f"\n```\n{element.get_text()}\n```\n")
            elif tag == 'blockquote' and text:
                lines.append(f"\n> {text}\n")
        
        return ''.join(lines)


# ======================== CSDN爬虫 - 增强版 ========================
class CSDNCrawler(BaseCrawler):
    """CSDN博客爬虫 - 增强内容提取"""
    
    def __init__(self):
        super().__init__()
        self.headers.update({
            'Referer': 'https://blog.csdn.net/',
            'Cookie': 'uuid_tt_dd=10_12345678-1234567890123-0123456789012-0123456789012'
        })
    
    def extract_column_articles(self, url: str) -> List[Article]:
        """提取专栏文章列表"""
        articles = []
        
        try:
            response = self.session.get(url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 多种方式查找文章列表
            selectors = [
                ('div', {'class': 'column_article_list'}),
                ('div', {'class': re.compile('article.*item')}),
                ('div', {'class': re.compile('blog.*item')}),
                ('article', {}),
            ]
            
            article_items = []
            for tag, attrs in selectors:
                items = soup.find_all(tag, attrs)
                if items:
                    article_items.extend(items)
                    break
            
            # 提取文章链接
            for item in article_items:
                link = item.find('a', href=re.compile('/article/details/'))
                if link:
                    title = link.get_text().strip()
                    href = link.get('href')
                    if not href.startswith('http'):
                        href = urljoin('https://blog.csdn.net', href)
                    articles.append(Article(title, href))
            
            # 如果上述方法都失败，直接查找所有文章链接
            if not articles:
                links = soup.find_all('a', href=re.compile('/article/details/'))
                for link in links:
                    title = link.get_text().strip()
                    if title and len(title) > 5:
                        href = link.get('href')
                        if not href.startswith('http'):
                            href = urljoin('https://blog.csdn.net', href)
                        articles.append(Article(title, href))
            
        except Exception as e:
            print(f"提取专栏文章失败: {e}")
        
        # 去重
        seen = set()
        unique = []
        for art in articles:
            if art.url not in seen and '/article/details/' in art.url:
                seen.add(art.url)
                unique.append(art)
        
        return unique
    
    def extract_article_info(self, article: Article):
        """提取文章元信息"""
        try:
            response = self.session.get(article.url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取标题
            if not article.title or article.title == "未命名":
                title_selectors = [
                    ('h1', {'class': 'title-article'}),
                    ('h1', {'id': 'articleContentId'}),
                    ('h1', {}),
                ]
                for tag, attrs in title_selectors:
                    title_tag = soup.find(tag, attrs)
                    if title_tag:
                        article.title = title_tag.get_text().strip()
                        break
            
            # 提取作者
            author_selectors = [
                ('a', {'class': 'follow-nickName'}),
                ('a', {'class': re.compile('user.*name')}),
                ('div', {'class': 'user-info'}),
            ]
            for tag, attrs in author_selectors:
                author_tag = soup.find(tag, attrs)
                if author_tag:
                    article.author = author_tag.get_text().strip()
                    break
            
            # 提取日期
            date_selectors = [
                ('span', {'class': 'time'}),
                ('span', {'class': re.compile('date|time')}),
            ]
            for tag, attrs in date_selectors:
                date_tag = soup.find(tag, attrs)
                if date_tag:
                    article.date = date_tag.get_text().strip()
                    break
            
            # 提取分类
            category_tag = soup.find('a', {'class': 'tag-link'})
            if category_tag:
                article.category = category_tag.get_text().strip()
            
        except Exception as e:
            print(f"提取文章信息失败: {e}")
    
    def extract_article_content(self, article: Article, download_images: bool, img_dir: str):
        """增强的内容提取"""
        try:
            self.extract_article_info(article)
            
            response = self.session.get(article.url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 多种方式查找内容区域
            content_selectors = [
                ('div', {'id': 'content_views'}),
                ('div', {'class': 'article_content'}),
                ('div', {'class': re.compile('article.*content')}),
                ('article', {}),
            ]
            
            content = None
            for tag, attrs in content_selectors:
                content = soup.find(tag, attrs)
                if content:
                    break
            
            if not content:
                article.content = "_内容获取失败_"
                article.html_content = "<p><em>内容获取失败</em></p>"
                return
            
            # 清理HTML
            content = self.clean_html(content)
            
            # 移除CSDN特有的干扰元素
            csdn_noise_patterns = [
                'hljs-button', 'csdn-tracking', 'hide-article',
                'blog-content-box', 'recommend-box', 'comment-box',
                'tool-box', 'more-toolbox', 'opt-box'
            ]
            for pattern in csdn_noise_patterns:
                for tag in content.find_all(class_=re.compile(pattern, re.I)):
                    tag.decompose()
            
            # 移除"已收录"等提示
            for tag in content.find_all(text=re.compile('已收录|版权声明|©️|查看原文')):
                parent = tag.parent
                if parent:
                    parent.decompose()
            
            # 处理图片 - CSDN需要特殊处理
            if download_images:
                for img in content.find_all('img'):
                    # CSDN图片可能在多个属性中
                    src = img.get('src') or img.get('data-src') or img.get('data-original-src')
                    if src:
                        img_url = urljoin(article.url, src)
                        local_path = self.download_image(img_url, img_dir, article.url)
                        img['src'] = local_path
                        if not img.get('alt'):
                            img['alt'] = 'image'
            
            # 处理数学公式 - 增强支持
            content = self.process_math_formulas(content)
            
            # 处理代码块
            for pre in content.find_all('pre'):
                # 保留代码块的语言标识
                code_tag = pre.find('code')
                if code_tag:
                    lang = code_tag.get('class', [''])[0]
                    if lang.startswith('language-'):
                        lang = lang.replace('language-', '')
                        pre['data-lang'] = lang
                pre['class'] = 'code-block'
            
            article.html_content = str(content)
            article.content = self.html_to_markdown(content)
            
        except Exception as e:
            article.content = f"_提取失败: {str(e)}_"
            article.html_content = f"<p><em>提取失败: {str(e)}</em></p>"
    
    def html_to_markdown(self, content) -> str:
        lines = []
        for element in content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'pre', 'blockquote']):
            tag = element.name
            text = element.get_text().strip()
            
            if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'] and text:
                level = int(tag[1])
                lines.append(f"\n{'#' * level} {text}\n")
            elif tag == 'p' and text:
                lines.append(f"\n{text}\n")
            elif tag == 'pre':
                # 尝试获取语言标识
                lang = element.get('data-lang', '')
                lines.append(f"\n```{lang}\n{element.get_text()}\n```\n")
            elif tag == 'blockquote' and text:
                lines.append(f"\n> {text}\n")
        
        return ''.join(lines)


# ======================== 知乎爬虫 ========================
class ZhihuCrawler(BaseCrawler):
    """知乎专栏爬虫"""
    
    def __init__(self):
        super().__init__()
        self.headers.update({
            'Referer': 'https://www.zhihu.com/',
        })
    
    def extract_article_content(self, article: Article, download_images: bool, img_dir: str):
        try:
            response = self.session.get(article.url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取标题
            if not article.title or article.title == "未命名":
                title_tag = soup.find('h1', class_='Post-Title') or soup.find('h1')
                article.title = title_tag.get_text().strip() if title_tag else "未知文章"
            
            # 提取作者
            author_tag = soup.find('meta', attrs={'name': 'author'})
            article.author = author_tag.get('content') if author_tag else "未知作者"
            
            # 提取内容
            content = soup.find('div', class_='Post-RichText') or soup.find('div', class_='RichText')
            
            if not content:
                article.content = "_内容获取失败_"
                article.html_content = "<p><em>内容获取失败</em></p>"
                return
            
            content = self.clean_html(content)
            content = self.process_math_formulas(content)
            
            # 处理图片
            if download_images:
                for img in content.find_all('img'):
                    src = img.get('src') or img.get('data-original') or img.get('data-actualsrc')
                    if src:
                        img_url = urljoin(article.url, src)
                        local_path = self.download_image(img_url, img_dir, article.url)
                        img['src'] = local_path
            
            article.html_content = str(content)
            article.content = self.html_to_markdown(content)
            
        except Exception as e:
            article.content = f"_提取失败: {str(e)}_"
            article.html_content = f"<p><em>提取失败: {str(e)}</em></p>"
    
    def html_to_markdown(self, content) -> str:
        lines = []
        for element in content.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'pre', 'blockquote']):
            tag = element.name
            text = element.get_text().strip()
            
            if tag in ['h1', 'h2', 'h3', 'h4'] and text:
                level = int(tag[1])
                lines.append(f"\n{'#' * level} {text}\n")
            elif tag == 'p' and text:
                lines.append(f"\n{text}\n")
            elif tag == 'pre':
                lines.append(f"\n```\n{element.get_text()}\n```\n")
            elif tag == 'blockquote' and text:
                lines.append(f"\n> {text}\n")
        
        return ''.join(lines)


# ======================== 简书爬虫 ========================
class JianshuCrawler(BaseCrawler):
    """简书爬虫"""
    
    def __init__(self):
        super().__init__()
        self.headers.update({
            'Referer': 'https://www.jianshu.com/',
        })
    
    def extract_article_content(self, article: Article, download_images: bool, img_dir: str):
        try:
            response = self.session.get(article.url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取标题
            if not article.title or article.title == "未命名":
                title_tag = soup.find('h1', class_='title') or soup.find('h1')
                article.title = title_tag.get_text().strip() if title_tag else "未知文章"
            
            # 提取作者
            author_tag = soup.find('a', class_='author')
            article.author = author_tag.get_text().strip() if author_tag else "未知作者"
            
            # 提取内容
            content = soup.find('article') or soup.find('div', class_='show-content')
            
            if not content:
                article.content = "_内容获取失败_"
                article.html_content = "<p><em>内容获取失败</em></p>"
                return
            
            content = self.clean_html(content)
            content = self.process_math_formulas(content)
            
            # 处理图片
            if download_images:
                for img in content.find_all('img'):
                    src = img.get('src') or img.get('data-original-src')
                    if src:
                        img_url = urljoin(article.url, src)
                        local_path = self.download_image(img_url, img_dir, article.url)
                        img['src'] = local_path
            
            article.html_content = str(content)
            article.content = self.html_to_markdown(content)
            
        except Exception as e:
            article.content = f"_提取失败: {str(e)}_"
            article.html_content = f"<p><em>提取失败: {str(e)}</em></p>"
    
    def html_to_markdown(self, content) -> str:
        lines = []
        for element in content.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'pre', 'blockquote']):
            tag = element.name
            text = element.get_text().strip()
            
            if tag in ['h1', 'h2', 'h3', 'h4'] and text:
                level = int(tag[1])
                lines.append(f"\n{'#' * level} {text}\n")
            elif tag == 'p' and text:
                lines.append(f"\n{text}\n")
            elif tag == 'pre':
                lines.append(f"\n```\n{element.get_text()}\n```\n")
            elif tag == 'blockquote' and text:
                lines.append(f"\n> {text}\n")
        
        return ''.join(lines)


# ======================== 爬虫线程 ========================
class CrawlerThread(QThread):
    """爬虫线程 - 增强版"""
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self):
        super().__init__()
        self.url = ""
        self.platform = "runoob"
        self.output_dir = "./output"
        self.output_formats = ['markdown', 'html', 'pdf']
        self.download_images = True
        self.aggregate_mode = True  # True=合并成一个文件，False=每篇独立文件
        self.is_running = True
        
    def run(self):
        try:
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
            img_dir = os.path.join(self.output_dir, 'images')
            Path(img_dir).mkdir(parents=True, exist_ok=True)
            
            if self.platform == 'runoob':
                self.crawl_runoob()
            elif self.platform == 'csdn':
                self.crawl_csdn()
            elif self.platform == 'zhihu':
                self.crawl_zhihu()
            elif self.platform == 'jianshu':
                self.crawl_jianshu()
            
            self.finished_signal.emit(True, f"✅ 完成!\n保存位置: {os.path.abspath(self.output_dir)}")
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.finished_signal.emit(False, f"❌ 错误: {str(e)}\n\n{error_detail}")
    
    def stop(self):
        self.is_running = False
    
    def crawl_runoob(self):
        self.progress_signal.emit("📖 正在分析菜鸟教程...")
        
        crawler = RunoobCrawler()
        title, articles = crawler.extract_tutorial_info(self.url)
        
        if not articles:
            raise Exception("未找到任何章节")
        
        self.progress_signal.emit(f"📚 教程: {title}")
        self.progress_signal.emit(f"📑 共 {len(articles)} 个章节")
        
        img_dir = os.path.join(self.output_dir, 'images')
        
        for idx, article in enumerate(articles, 1):
            if not self.is_running:
                return
            
            self.progress_signal.emit(f"📄 [{idx}/{len(articles)}] {article.title}")
            crawler.extract_article_content(article, self.download_images, img_dir)
            time.sleep(0.5)
        
        # 根据模式生成文件
        if self.aggregate_mode:
            self.generate_files(title, articles, "菜鸟教程")
        else:
            self.generate_separate_files(articles, "菜鸟教程")
    
    def crawl_csdn(self):
        self.progress_signal.emit("📖 正在分析CSDN...")
        
        crawler = CSDNCrawler()
        
        if '/category_' in self.url or '/column/' in self.url:
            self.progress_signal.emit("📚 检测到专栏，正在提取文章列表...")
            articles = crawler.extract_column_articles(self.url)
            
            if not articles:
                raise Exception("未找到任何文章")
            
            self.progress_signal.emit(f"📑 共 {len(articles)} 篇文章")
            
            img_dir = os.path.join(self.output_dir, 'images')
            
            for idx, article in enumerate(articles, 1):
                if not self.is_running:
                    return
                
                self.progress_signal.emit(f"📄 [{idx}/{len(articles)}] {article.title}")
                crawler.extract_article_content(article, self.download_images, img_dir)
                time.sleep(1)
            
            title = articles[0].author + "的CSDN专栏" if articles else "CSDN专栏"
            
            if self.aggregate_mode:
                self.generate_files(title, articles, articles[0].author if articles else "未知作者")
            else:
                self.generate_separate_files(articles, articles[0].author if articles else "未知作者")
            
        else:
            article = Article("未命名", self.url)
            
            img_dir = os.path.join(self.output_dir, 'images')
            self.progress_signal.emit("📄 正在提取文章内容...")
            crawler.extract_article_content(article, self.download_images, img_dir)
            
            self.generate_files(article.title, [article], article.author)
    
    def crawl_zhihu(self):
        """爬取知乎专栏"""
        self.progress_signal.emit("📖 正在分析知乎...")
        
        crawler = ZhihuCrawler()
        article = Article("未命名", self.url)
        
        img_dir = os.path.join(self.output_dir, 'images')
        self.progress_signal.emit("📄 正在提取文章内容...")
        crawler.extract_article_content(article, self.download_images, img_dir)
        
        self.generate_files(article.title, [article], article.author)
    
    def crawl_jianshu(self):
        """爬取简书"""
        self.progress_signal.emit("📖 正在分析简书...")
        
        crawler = JianshuCrawler()
        article = Article("未命名", self.url)
        
        img_dir = os.path.join(self.output_dir, 'images')
        self.progress_signal.emit("📄 正在提取文章内容...")
        crawler.extract_article_content(article, self.download_images, img_dir)
        
        self.generate_files(article.title, [article], article.author)
    
    def generate_separate_files(self, articles: List[Article], author: str):
        """非聚合模式 - 每篇文章单独保存"""
        self.progress_signal.emit("📝 非聚合模式：每篇文章单独保存...")
        
        for idx, article in enumerate(articles, 1):
            if not self.is_running:
                return
            
            # 使用文章标题作为文件名
            safe_title = re.sub(r'[\\/:"*?<>|]+', '_', article.title)
            safe_title = safe_title.strip()[:100]
            
            if not safe_title:
                safe_title = f"文章_{idx}"
            
            # Markdown
            if 'markdown' in self.output_formats:
                md_path = os.path.join(self.output_dir, f"{safe_title}.md")
                self.generate_markdown(md_path, article.title, [article], author)
            
            # HTML
            html_path = None
            if 'html' in self.output_formats or 'pdf' in self.output_formats:
                html_path = os.path.join(self.output_dir, f"{safe_title}.html")
                self.generate_html(html_path, article.title, [article], author)
            
            # PDF
            if 'pdf' in self.output_formats and WEASY_AVAILABLE and html_path:
                pdf_path = os.path.join(self.output_dir, f"{safe_title}.pdf")
                self.generate_pdf_professional(html_path, pdf_path)
            
            self.progress_signal.emit(f"✅ [{idx}/{len(articles)}] {safe_title}")
    
    def generate_files(self, title: str, articles: List[Article], author: str):
        """聚合模式 - 所有文章合并成一个文件"""
        # 修复文件名
        safe_title = re.sub(r'[\\/:"*?<>|]+', '_', title)
        safe_title = safe_title.strip()[:100]
        
        if not safe_title:
            safe_title = "未命名文档"
        
        # Markdown
        if 'markdown' in self.output_formats:
            self.progress_signal.emit("📝 生成Markdown...")
            md_path = os.path.join(self.output_dir, f"{safe_title}.md")
            self.generate_markdown(md_path, title, articles, author)
        
        # HTML
        html_path = None
        if 'html' in self.output_formats or 'pdf' in self.output_formats:
            self.progress_signal.emit("🌐 生成HTML...")
            html_path = os.path.join(self.output_dir, f"{safe_title}.html")
            self.generate_html(html_path, title, articles, author)
        
        # PDF - 专业书籍风格
        if 'pdf' in self.output_formats and WEASY_AVAILABLE and html_path:
            self.progress_signal.emit("📄 生成专业PDF (这可能需要一些时间)...")
            pdf_path = os.path.join(self.output_dir, f"{safe_title}.pdf")
            self.generate_pdf_professional(html_path, pdf_path)
    
    def generate_markdown(self, path: str, title: str, articles: List[Article], author: str):
        """生成Markdown文件"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write(f"> **作者**: {author}\n")
            f.write(f"> **生成时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            # 目录（仅在多篇文章时显示）
            if len(articles) > 1:
                f.write("## 📑 目录\n\n")
                for idx, art in enumerate(articles, 1):
                    f.write(f"{idx}. [{art.title}](#{idx})\n")
                f.write("\n---\n\n")
            
            # 内容
            for idx, art in enumerate(articles, 1):
                if len(articles) > 1:
                    f.write(f'<div id="{idx}"></div>\n\n')
                    f.write(f"## {idx}. {art.title}\n\n")
                else:
                    f.write(f"## {art.title}\n\n")
                
                if art.author:
                    f.write(f"**作者**: {art.author}  \n")
                if art.date:
                    f.write(f"**日期**: {art.date}  \n")
                if art.category:
                    f.write(f"**分类**: {art.category}  \n")
                
                f.write("\n")
                f.write(art.content)
                f.write("\n\n---\n\n")
            
            f.write("\n\n**本文档由网页内容提取器生成，仅供学习使用**\n")
        
        self.progress_signal.emit(f"✅ Markdown: {os.path.basename(path)}")
    
    def generate_html(self, path: str, title: str, articles: List[Article], author: str):
        """生成HTML文件 - GitBook专业风格 + 数学公式增强"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="author" content="{author}">
    <title>{title}</title>
    
    <!-- 数学公式支持 - MathJax 3.0 -->
    <script>
        window.MathJax = {{
            tex: {{
                inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
                processEscapes: true,
                processEnvironments: true,
                tags: 'ams',
                autoload: {{
                    color: [],
                    colorV2: ['color']
                }},
                packages: {{'[+]': ['noerrors']}}
            }},
            options: {{
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre'],
                ignoreHtmlClass: 'tex2jax_ignore',
                processHtmlClass: 'tex2jax_process'
            }},
            loader: {{
                load: ['[tex]/noerrors']
            }}
        }};
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" async></script>
    
    <style>
        /* ==================== 专业书籍风格 - GitBook优化版 ==================== */
        
        /* 页面设置 */
        @page {{
            size: A4;
            margin: 25mm 20mm;
            
            @top-center {{
                content: "{title}";
                font-size: 9pt;
                color: #999;
            }}
            
            @bottom-center {{
                content: "第 " counter(page) " 页";
                font-size: 9pt;
                color: #999;
            }}
        }}
        
        /* 基础样式 */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        html {{
            font-size: 16px;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', 
                         'Hiragino Sans GB', 'Noto Sans CJK SC', 'Source Han Sans CN', sans-serif;
            font-size: 1rem;
            line-height: 1.8;
            color: #2c3e50;
            background: #ffffff;
            text-rendering: optimizeLegibility;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        
        /* 容器 */
        .book-container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 30px;
        }}
        
        /* 封面页 */
        .book-cover {{
            text-align: center;
            padding: 100px 40px;
            page-break-after: always;
            border-bottom: 3px solid #3498db;
        }}
        
        .book-cover h1 {{
            font-size: 3rem;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 30px;
            line-height: 1.3;
            letter-spacing: 2px;
        }}
        
        .book-meta {{
            font-size: 1.1rem;
            color: #7f8c8d;
            margin: 20px 0;
            line-height: 2;
        }}
        
        .book-meta strong {{
            color: #34495e;
            font-weight: 600;
        }}
        
        /* 目录 */
        .toc {{
            page-break-after: always;
            padding: 40px 0;
        }}
        
        .toc-title {{
            font-size: 2.2rem;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 40px;
            padding-bottom: 15px;
            border-bottom: 3px solid #3498db;
        }}
        
        .toc ul {{
            list-style: none;
            padding: 0;
        }}
        
        .toc li {{
            margin: 15px 0;
            padding-left: 30px;
            position: relative;
            font-size: 1.05rem;
            line-height: 1.8;
        }}
        
        .toc li::before {{
            content: "▪";
            position: absolute;
            left: 10px;
            color: #3498db;
            font-size: 1.2rem;
        }}
        
        .toc a {{
            color: #34495e;
            text-decoration: none;
            transition: color 0.2s;
            border-bottom: 1px solid transparent;
        }}
        
        .toc a:hover {{
            color: #3498db;
            border-bottom-color: #3498db;
        }}
        
        /* 章节 */
        .chapter {{
            page-break-before: always;
            padding: 30px 0;
            margin-bottom: 50px;
        }}
        
        .chapter-title {{
            font-size: 2.4rem;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid #3498db;
            line-height: 1.3;
        }}
        
        .chapter-meta {{
            font-size: 0.95rem;
            color: #7f8c8d;
            margin-bottom: 30px;
            padding: 12px 20px;
            background: #f8f9fa;
            border-left: 4px solid #3498db;
            border-radius: 4px;
        }}
        
        /* 标题层级 */
        .chapter h1, .chapter h2, .chapter h3, .chapter h4, .chapter h5, .chapter h6 {{
            font-weight: 600;
            line-height: 1.4;
            margin-top: 35px;
            margin-bottom: 18px;
            color: #2c3e50;
        }}
        
        .chapter h1 {{ font-size: 2.2rem; border-bottom: 2px solid #ecf0f1; padding-bottom: 12px; }}
        .chapter h2 {{ font-size: 1.9rem; }}
        .chapter h3 {{ font-size: 1.6rem; color: #34495e; }}
        .chapter h4 {{ font-size: 1.3rem; color: #34495e; }}
        .chapter h5 {{ font-size: 1.1rem; color: #34495e; }}
        .chapter h6 {{ font-size: 1rem; color: #34495e; }}
        
        /* 段落 */
        .chapter p {{
            margin: 18px 0;
            font-size: 1.05rem;
            line-height: 1.9;
            text-align: justify;
            text-justify: inter-ideograph;
            color: #34495e;
        }}
        
        .chapter p:first-of-type {{
            margin-top: 0;
        }}
        
        /* 代码块 */
        .code-block, pre {{
            background: #282c34;
            color: #abb2bf;
            padding: 20px 25px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 25px 0;
            font-family: 'Consolas', 'Monaco', 'Courier New', 'Source Code Pro', monospace;
            font-size: 0.92rem;
            line-height: 1.6;
            border: 1px solid #21252b;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        pre code {{
            background: transparent;
            padding: 0;
            border: none;
            color: inherit;
            font-size: inherit;
        }}
        
        /* 行内代码 */
        code {{
            background: #f8f9fa;
            color: #e74c3c;
            padding: 3px 8px;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.92em;
            border: 1px solid #ecf0f1;
        }}
        
        /* 数学公式样式 - 增强版 */
        .math-inline {{
            font-family: 'Latin Modern Math', 'STIX Two Math', 'Cambria Math', 'Times New Roman', serif;
            color: #c0392b;
            font-size: 1.05em;
            padding: 0 2px;
        }}
        
        .math-display {{
            font-family: 'Latin Modern Math', 'STIX Two Math', 'Cambria Math', 'Times New Roman', serif;
            text-align: center;
            margin: 25px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 6px;
            border: 1px solid #ecf0f1;
            overflow-x: auto;
        }}
        
        /* MathJax全局设置 */
        mjx-container {{
            font-size: 1.05em !important;
        }}
        
        mjx-container[display="true"] {{
            margin: 25px 0 !important;
        }}
        
        /* 表格 */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 30px 0;
            font-size: 0.98rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-radius: 6px;
            overflow: hidden;
        }}
        
        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        th {{
            padding: 15px 18px;
            text-align: left;
            font-weight: 600;
            font-size: 1rem;
        }}
        
        td {{
            padding: 13px 18px;
            border-bottom: 1px solid #ecf0f1;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        tr:last-child td {{
            border-bottom: none;
        }}
        
        /* 图片 */
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 30px auto;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }}
        
        /* 列表 */
        ul, ol {{
            margin: 20px 0;
            padding-left: 35px;
        }}
        
        li {{
            margin: 12px 0;
            line-height: 1.8;
            font-size: 1.02rem;
        }}
        
        ul li {{
            list-style-type: disc;
        }}
        
        ul ul li {{
            list-style-type: circle;
        }}
        
        ol li {{
            list-style-type: decimal;
        }}
        
        /* 引用块 */
        blockquote {{
            border-left: 4px solid #3498db;
            padding: 15px 25px;
            margin: 25px 0;
            background: #f8f9fa;
            color: #555;
            font-style: italic;
            border-radius: 0 6px 6px 0;
        }}
        
        blockquote p {{
            margin: 8px 0;
        }}
        
        /* 分隔线 */
        hr {{
            border: none;
            border-top: 2px solid #ecf0f1;
            margin: 40px 0;
        }}
        
        /* 链接 */
        a {{
            color: #3498db;
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: all 0.2s;
        }}
        
        a:hover {{
            color: #2980b9;
            border-bottom-color: #2980b9;
        }}
        
        /* 注释/提示框 */
        .note, .tip, .warning {{
            padding: 18px 25px;
            margin: 25px 0;
            border-radius: 6px;
            border-left: 4px solid;
        }}
        
        .note {{
            background: #e3f2fd;
            border-color: #2196f3;
            color: #1565c0;
        }}
        
        .tip {{
            background: #e8f5e9;
            border-color: #4caf50;
            color: #2e7d32;
        }}
        
        .warning {{
            background: #fff3e0;
            border-color: #ff9800;
            color: #e65100;
        }}
        
        /* 页脚 */
        .book-footer {{
            text-align: center;
            padding: 50px 20px;
            margin-top: 80px;
            border-top: 2px solid #ecf0f1;
            color: #95a5a6;
            font-size: 0.95rem;
            page-break-before: always;
        }}
        
        /* 打印优化 */
        @media print {{
            body {{
                background: white;
            }}
            
            .book-container {{
                max-width: 100%;
                padding: 0;
            }}
            
            a {{
                color: #2c3e50;
                border-bottom: none;
            }}
            
            .chapter {{
                page-break-inside: avoid;
            }}
            
            h1, h2, h3, h4, h5, h6 {{
                page-break-after: avoid;
            }}
            
            img {{
                page-break-inside: avoid;
            }}
            
            pre, blockquote {{
                page-break-inside: avoid;
            }}
        }}
        
        /* 响应式 */
        @media screen and (max-width: 768px) {{
            html {{
                font-size: 14px;
            }}
            
            .book-container {{
                padding: 20px 15px;
            }}
            
            .book-cover {{
                padding: 60px 20px;
            }}
            
            .book-cover h1 {{
                font-size: 2rem;
            }}
            
            .chapter-title {{
                font-size: 1.8rem;
            }}
            
            .chapter h1 {{ font-size: 1.7rem; }}
            .chapter h2 {{ font-size: 1.5rem; }}
            .chapter h3 {{ font-size: 1.3rem; }}
        }}
    </style>
</head>
<body>
    <div class="book-container">
        <!-- 封面 -->
        <div class="book-cover">
            <h1>{title}</h1>
            <div class="book-meta">
                <p><strong>作者</strong> {author}</p>
                <p><strong>生成时间</strong> {datetime.now().strftime('%Y年%m月%d日')}</p>
            </div>
        </div>
"""
        
        # 目录（仅在多篇文章时显示）
        if len(articles) > 1:
            html += """
        <!-- 目录 -->
        <div class="toc">
            <h2 class="toc-title">📑 目录</h2>
            <ul>
"""
            for idx, art in enumerate(articles, 1):
                html += f'                <li><a href="#chapter-{idx}">{idx}. {art.title}</a></li>\n'
            
            html += """            </ul>
        </div>
"""
        
        # 章节内容
        for idx, art in enumerate(articles, 1):
            meta_parts = []
            if art.author:
                meta_parts.append(f"<strong>作者</strong> {art.author}")
            if art.date:
                meta_parts.append(f"<strong>日期</strong> {art.date}")
            if art.category:
                meta_parts.append(f"<strong>分类</strong> {art.category}")
            
            meta_html = f'<div class="chapter-meta">{" | ".join(meta_parts)}</div>' if meta_parts else ''
            
            chapter_title = f"{idx}. {art.title}" if len(articles) > 1 else art.title
            
            html += f"""
        <!-- 章节 {idx} -->
        <div id="chapter-{idx}" class="chapter">
            <h1 class="chapter-title">{chapter_title}</h1>
            {meta_html}
            <div class="chapter-content">
                {art.html_content}
            </div>
        </div>
"""
        
        # 页脚
        html += f"""
        <!-- 页脚 -->
        <div class="book-footer">
            <p>本文档由网页内容提取器 v7.0 生成</p>
            <p>仅供个人学习使用，请勿用于商业用途</p>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.progress_signal.emit(f"✅ HTML: {os.path.basename(path)}")
    
    def generate_pdf_professional(self, html_path: str, pdf_path: str):
        """生成专业书籍风格的PDF - WeasyPrint 59.0+"""
        try:
            # 读取HTML内容
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 创建字体配置
            font_config = FontConfiguration()
            
            # PDF专用CSS - 增强打印效果
            pdf_css = """
                @page {
                    size: A4;
                    margin: 25mm 20mm;
                }
                
                body {
                    font-family: 'Microsoft YaHei', 'SimSun', 'SimHei', 'PingFang SC', sans-serif;
                    font-size: 11pt;
                    line-height: 1.7;
                }
                
                .chapter {
                    page-break-before: always;
                }
                
                .toc {
                    page-break-after: always;
                }
                
                h1, h2, h3, h4 {
                    page-break-after: avoid;
                }
                
                pre, blockquote, table, img {
                    page-break-inside: avoid;
                }
                
                .math-inline, .math-display {
                    font-family: 'Times New Roman', 'STIX Two Math', serif;
                }
                
                code {
                    background: #f4f4f4;
                    border: 1px solid #ddd;
                    padding: 2px 6px;
                    border-radius: 3px;
                }
                
                pre {
                    background: #2d2d2d;
                    color: #f8f8f2;
                    padding: 15px;
                    border-radius: 5px;
                    font-size: 9pt;
                }
            """
            
            # 生成PDF
            html_doc = HTML(string=html_content, base_url=os.path.dirname(html_path))
            css_doc = CSS(string=pdf_css, font_config=font_config)
            
            html_doc.write_pdf(
                target=pdf_path,
                stylesheets=[css_doc],
                font_config=font_config
            )
            
            self.progress_signal.emit(f"✅ PDF: {os.path.basename(pdf_path)}")
            
        except Exception as e:
            import traceback
            error_msg = f"⚠️ PDF生成失败: {str(e)}\n{traceback.format_exc()}"
            self.progress_signal.emit(error_msg)
            print(error_msg)


# ======================== 主窗口 - GUI增强版 ========================
class MainWindow(QMainWindow):
    """主窗口 - 大字体、易操作"""
    
    def __init__(self):
        super().__init__()
        self.spider = None
        self.settings = QSettings('WebContentExtractor', 'v7')
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        self.setWindowTitle('🌐 网页内容提取器 v7.0 - 专业增强版')
        self.setGeometry(100, 100, 1200, 900)
        self.setMinimumSize(1000, 800)
        
        # 优化样式 - 大字体、专业外观
        self.setStyleSheet("""
            QMainWindow {
                background: #f5f7fa;
            }
            QWidget {
                font-size: 16px;
            }
            QGroupBox {
                border: 2px solid #dfe6e9;
                border-radius: 10px;
                margin-top: 20px;
                padding: 25px 18px 18px 18px;
                font-weight: 600;
                font-size: 17px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                background: white;
                font-size: 18px;
                color: #2c3e50;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 16px 28px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                min-width: 130px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5568d3, stop:1 #6a3f8f);
            }
            QPushButton:pressed {
                background: #5568d3;
            }
            QPushButton:disabled {
                background: #bdc3c7;
            }
            QLineEdit {
                padding: 14px;
                border: 2px solid #dfe6e9;
                border-radius: 8px;
                background: white;
                font-size: 16px;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
            }
            QTextEdit {
                border: 2px solid #dfe6e9;
                border-radius: 8px;
                background: white;
                padding: 14px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 15px;
                line-height: 1.6;
            }
            QRadioButton, QCheckBox {
                spacing: 10px;
                font-size: 16px;
            }
            QRadioButton::indicator, QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QProgressBar {
                border: 2px solid #dfe6e9;
                border-radius: 8px;
                text-align: center;
                background: white;
                height: 35px;
                font-size: 15px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 6px;
            }
            QLabel {
                color: #2c3e50;
                font-size: 16px;
            }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # 标题
        title_widget = QWidget()
        title_widget.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #667eea, stop:1 #764ba2);
            border-radius: 12px;
        """)
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(25, 25, 25, 25)
        
        title_label = QLabel("🌐 网页内容提取器 v7.0")
        title_label.setFont(QFont('Microsoft YaHei', 24, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel("专业版 | PDF书籍风格 | 数学公式增强 | CSDN深度提取 | 大字体GUI")
        subtitle.setStyleSheet("color: rgba(255,255,255,0.95); font-size: 15px;")
        subtitle.setAlignment(Qt.AlignCenter)
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle)
        layout.addWidget(title_widget)
        
        # URL输入
        url_group = QGroupBox("🔗 输入网址")
        url_layout = QVBoxLayout()
        url_layout.setSpacing(14)
        
        # 平台选择
        platform_layout = QHBoxLayout()
        platform_layout.setSpacing(16)
        platform_layout.addWidget(QLabel("平台:"))
        
        self.runoob_radio = QRadioButton("📘 菜鸟教程")
        self.csdn_radio = QRadioButton("📙 CSDN博客")
        self.zhihu_radio = QRadioButton("📗 知乎专栏")
        self.jianshu_radio = QRadioButton("📕 简书")
        self.runoob_radio.setChecked(True)
        
        platform_layout.addWidget(self.runoob_radio)
        platform_layout.addWidget(self.csdn_radio)
        platform_layout.addWidget(self.zhihu_radio)
        platform_layout.addWidget(self.jianshu_radio)
        platform_layout.addStretch()
        url_layout.addLayout(platform_layout)
        
        # URL输入
        url_input_layout = QHBoxLayout()
        url_input_layout.setSpacing(10)
        url_label = QLabel("网址:")
        url_label.setMinimumWidth(50)
        url_input_layout.addWidget(url_label)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("粘贴完整URL (支持教程首页、单篇文章、专栏)...")
        url_input_layout.addWidget(self.url_input, 1)
        url_layout.addLayout(url_input_layout)
        
        # 示例
        example = QLabel(
            "💡 支持的URL格式:\n"
            "• 菜鸟教程: https://www.runoob.com/python3/python3-tutorial.html\n"
            "• CSDN文章: https://blog.csdn.net/xxx/article/details/123456\n"
            "• 知乎专栏: https://zhuanlan.zhihu.com/p/123456789\n"
            "• 简书文章: https://www.jianshu.com/p/123456789abc"
        )
        example.setStyleSheet("color: #7f8c8d; font-size: 14px; padding: 12px; background: #f8f9fa; border-radius: 6px;")
        url_layout.addWidget(example)
        
        url_group.setLayout(url_layout)
        layout.addWidget(url_group)
        
        # 输出设置
        output_group = QGroupBox("⚙️ 输出设置")
        output_layout = QVBoxLayout()
        output_layout.setSpacing(14)
        
        # 输出目录
        dir_layout = QHBoxLayout()
        dir_layout.setSpacing(10)
        dir_label = QLabel("目录:")
        dir_label.setMinimumWidth(50)
        dir_layout.addWidget(dir_label)
        self.output_path = QLineEdit('./output')
        dir_layout.addWidget(self.output_path, 1)
        browse_btn = QPushButton("📁 浏览")
        browse_btn.setMaximumWidth(120)
        browse_btn.clicked.connect(self.browse_output_dir)
        dir_layout.addWidget(browse_btn)
        output_layout.addLayout(dir_layout)
        
        # 格式选择
        format_layout = QHBoxLayout()
        format_layout.setSpacing(16)
        format_label = QLabel("格式:")
        format_label.setMinimumWidth(50)
        format_layout.addWidget(format_label)
        
        self.md_check = QCheckBox("📝 Markdown")
        self.html_check = QCheckBox("🌐 HTML")
        self.pdf_check = QCheckBox("📄 PDF (专业书籍)")
        
        self.md_check.setChecked(True)
        self.html_check.setChecked(True)
        if WEASY_AVAILABLE:
            self.pdf_check.setChecked(True)
        else:
            self.pdf_check.setEnabled(False)
            self.pdf_check.setToolTip("需要安装 weasyprint")
        
        format_layout.addWidget(self.md_check)
        format_layout.addWidget(self.html_check)
        format_layout.addWidget(self.pdf_check)
        
        self.download_img_check = QCheckBox("🖼️ 下载图片")
        self.download_img_check.setChecked(True)
        format_layout.addWidget(self.download_img_check)
        
        # 非聚合模式
        self.separate_mode_check = QCheckBox("📑 非聚合模式（每篇独立）")
        self.separate_mode_check.setChecked(False)
        self.separate_mode_check.setToolTip("勾选后，多篇文章将分别保存为独立文件")
        format_layout.addWidget(self.separate_mode_check)
        
        format_layout.addStretch()
        output_layout.addLayout(format_layout)
        
        if not WEASY_AVAILABLE:
            pdf_hint = QLabel("💡 安装 weasyprint 以启用PDF功能\n   命令: pip install weasyprint")
            pdf_hint.setStyleSheet("color: #f39c12; font-size: 14px; padding: 10px;")
            output_layout.addWidget(pdf_hint)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        control_layout.setSpacing(16)
        
        self.start_btn = QPushButton("🚀 开始提取")
        self.start_btn.clicked.connect(self.start_crawling)
        self.start_btn.setMinimumHeight(55)
        
        self.stop_btn = QPushButton("⏹️ 停止")
        self.stop_btn.clicked.connect(self.stop_crawling)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(55)
        
        open_btn = QPushButton("📂 打开文件夹")
        open_btn.clicked.connect(self.open_output_folder)
        open_btn.setMinimumHeight(55)
        
        control_layout.addWidget(self.start_btn, 2)
        control_layout.addWidget(self.stop_btn, 1)
        control_layout.addWidget(open_btn, 1)
        layout.addLayout(control_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0)
        layout.addWidget(self.progress_bar)
        
        # 日志
        log_label = QLabel("📋 运行日志")
        log_label.setFont(QFont('Microsoft YaHei', 14, QFont.Bold))
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(220)
        layout.addWidget(self.log_text)
        
    def browse_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_path.setText(directory)
            
    def open_output_folder(self):
        path = os.path.abspath(self.output_path.text())
        if os.path.exists(path):
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        else:
            QMessageBox.warning(self, "提示", "输出目录不存在")
            
    def start_crawling(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "提示", "请输入URL!")
            return
        
        if not url.startswith('http'):
            QMessageBox.warning(self, "提示", "请输入完整的URL (以http开头)")
            return
        
        # 检查格式
        formats = []
        if self.md_check.isChecked():
            formats.append('markdown')
        if self.html_check.isChecked():
            formats.append('html')
        if self.pdf_check.isChecked():
            formats.append('pdf')
        
        if not formats:
            QMessageBox.warning(self, "提示", "请至少选择一种输出格式!")
            return
        
        # 判断平台
        if self.runoob_radio.isChecked():
            platform = 'runoob'
        elif self.csdn_radio.isChecked():
            platform = 'csdn'
        elif self.zhihu_radio.isChecked():
            platform = 'zhihu'
        else:
            platform = 'jianshu'
        
        # 创建爬虫线程
        self.spider = CrawlerThread()
        self.spider.url = url
        self.spider.platform = platform
        self.spider.output_dir = self.output_path.text()
        self.spider.output_formats = formats
        self.spider.download_images = self.download_img_check.isChecked()
        self.spider.aggregate_mode = not self.separate_mode_check.isChecked()
        
        self.spider.progress_signal.connect(self.update_progress)
        self.spider.finished_signal.connect(self.crawl_finished)
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setRange(0, 0)
        self.log_text.clear()
        
        self.spider.start()
        mode_text = "聚合模式（合并成一个文件）" if self.spider.aggregate_mode else "非聚合模式（每篇独立文件）"
        self.log("=" * 80)
        self.log(f"🚀 开始提取")
        self.log(f"📍 URL: {url}")
        self.log(f"📦 平台: {platform}")
        self.log(f"📁 格式: {', '.join(formats)}")
        self.log(f"📄 模式: {mode_text}")
        self.log("=" * 80)
        
    def stop_crawling(self):
        if self.spider:
            self.spider.stop()
            self.log("⏹️ 正在停止...")
            
    def update_progress(self, message: str):
        self.log(message)
        
    def crawl_finished(self, success: bool, message: str):
        self.log("=" * 80)
        self.log(message)
        self.log("=" * 80)
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100 if success else 0)
        
        if success:
            QMessageBox.information(self, "✅ 完成", message)
        else:
            QMessageBox.critical(self, "❌ 错误", message)
            
    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.moveCursor(QTextCursor.End)
        
    def load_settings(self):
        output = self.settings.value('output_dir', './output')
        self.output_path.setText(output)
        
    def closeEvent(self, event):
        self.settings.setValue('output_dir', self.output_path.text())
        if self.spider and self.spider.isRunning():
            reply = QMessageBox.question(
                self, 
                '确认', 
                '任务正在进行，确定退出吗?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.spider.stop()
                self.spider.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


# ======================== 主程序入口 ========================
def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 显示启动信息
    splash = QMessageBox()
    splash.setWindowTitle("网页内容提取器 v7.0")
    splash.setIcon(QMessageBox.Information)
    
    status_text = "✅ 功能状态:\n\n"
    status_text += "• Markdown输出: ✅ 可用\n"
    status_text += "• HTML输出: ✅ GitBook风格\n"
    status_text += "• 数学公式: ✅ MathJax 3.0 完整支持\n"
    status_text += "• 图片下载: ✅ 可用\n"
    status_text += "• 非聚合模式: ✅ 支持独立文件\n"
    status_text += "• CSDN增强: ✅ 深度内容提取\n"
    status_text += "• GUI优化: ✅ 大字体易操作\n"
    
    if WEASY_AVAILABLE:
        status_text += "• PDF输出: ✅ 专业书籍风格\n"
    else:
        status_text += "• PDF输出: ❌ 未安装\n"
        status_text += "\n💡 安装PDF支持:\n"
        status_text += "pip install weasyprint\n"
    
    status_text += "\n🌐 支持平台:\n"
    status_text += "• 菜鸟教程、CSDN、知乎、简书"
    
    splash.setText(status_text)
    splash.setStandardButtons(QMessageBox.Ok)
    splash.exec_()
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()