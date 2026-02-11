# -*- coding: utf-8 -*-
"""
Web Content Extractor Pro - 专业网页内容提取工具
基于PyQt5和BeautifulSoup开发，支持多平台内容提取、多格式输出、数学公式处理
Version: 8.1 - CSDN数学公式深度优化版
github网址： https://github.com/lyp0746
QQ邮箱：1610369302@qq.com
作者：LYP

优化重点:
- CSDN数学公式深度清理(移除XML标签)
- Markdown数学公式正确渲染
- PDF专业书籍风格优化
- 智能文件命名(使用文章标题)
- 支持菜鸟教程、CSDN、GitBook三大平台

功能特性:
- 支持平台: 菜鸟教程、CSDN博客/专栏、GitBook文档
- 输出格式: Markdown、HTML、PDF (专业书籍风格)
- 数学公式: 完整LaTeX/MathJax 3.0支持
- CSDN增强: 深度内容提取和清理
- GUI优化: 大字体、易操作、专业外观
============================================
"""
import sys
import os
import re
import warnings
from pathlib import Path
from typing import List, Tuple
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup, NavigableString
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QSettings
from PyQt5.QtGui import QFont, QTextCursor

# 抑制警告
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message="sipPyTypeDict")

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
    
    def clean_math_formula(self, text: str) -> str:
        """
        深度清理数学公式 - 移除CSDN的XML标签
        将复杂的MathML标签转换为纯LaTeX
        """
        if not text:
            return text
        
        # 移除所有MathML XML标签,保留纯文本公式
        # 处理: <semantics><mrow>...</mrow><annotation encoding="application/x-tex">LATEX_HERE</annotation></semantics>
        
        # 提取annotation标签中的LaTeX
        annotation_pattern = r'<annotation[^>]*encoding="application/x-tex"[^>]*>(.*?)</annotation>'
        annotations = re.findall(annotation_pattern, text, re.DOTALL)
        
        if annotations:
            # 如果找到annotation,直接使用其中的LaTeX
            return annotations[0].strip()
        
        # 移除所有XML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 清理多余空格
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def process_math_formulas(self, content):
        """
        增强数学公式处理 - CSDN深度优化
        支持格式:
        - LaTeX行内: \\( ... \\) 或 $ ... $
        - LaTeX块级: \\[ ... \\] 或 $$ ... $$
        - MathJax script标签
        - CSDN的katex/mathjax span标签
        """
        soup = BeautifulSoup(str(content), 'html.parser')
        
        # 处理MathJax script标签
        for script in soup.find_all('script', type='math/tex'):
            formula = script.string
            if formula:
                formula_clean = self.clean_math_formula(formula)
                span = soup.new_tag('span', attrs={'class': 'math-inline'})
                span.string = f'${formula_clean}$'
                script.replace_with(span)
        
        for script in soup.find_all('script', type='math/tex; mode=display'):
            formula = script.string
            if formula:
                formula_clean = self.clean_math_formula(formula)
                div = soup.new_tag('div', attrs={'class': 'math-display'})
                div.string = f'$${formula_clean}$$'
                script.replace_with(div)
        
        # 处理CSDN的katex/mathjax span标签 - 深度清理
        for span in soup.find_all('span', class_=re.compile('katex|mathjax|MathJax')):
            # 获取原始HTML内容
            formula_html = str(span)
            formula_text = span.get_text()
            
            # 尝试提取annotation中的LaTeX
            formula_clean = self.clean_math_formula(formula_html)
            
            # 如果清理后为空,使用文本内容
            if not formula_clean or formula_clean == formula_text:
                formula_clean = formula_text
            
            # 判断是行内还是块级
            if 'display' in span.get('class', []) or 'block' in str(span.get('style', '')):
                new_div = soup.new_tag('div', attrs={'class': 'math-display'})
                new_div.string = f'$${formula_clean}$$'
                span.replace_with(new_div)
            else:
                new_span = soup.new_tag('span', attrs={'class': 'math-inline'})
                new_span.string = f'${formula_clean}$'
                span.replace_with(new_span)
        
        # LaTeX行内公式: \( ... \)
        content_str = str(soup)
        content_str = re.sub(
            r'\\\((.*?)\\\)', 
            r'<span class="math-inline">$\1$</span>', 
            content_str
        )
        
        # LaTeX块级公式: \[ ... \]
        content_str = re.sub(
            r'\\\[(.*?)\\\]', 
            r'<div class="math-display">$$\1$$</div>', 
            content_str, 
            flags=re.DOTALL
        )
        
        return BeautifulSoup(content_str, 'html.parser')
    
    def html_to_markdown(self, content) -> str:
        """
        增强的HTML转Markdown - 正确处理数学公式
        """
        lines = []
        
        for element in content.descendants:
            # 跳过NavigableString
            if isinstance(element, NavigableString):
                continue
            
            tag = element.name
            
            # 数学公式 - 直接转换为Markdown语法
            if tag == 'span' and 'math-inline' in element.get('class', []):
                formula = element.get_text().strip()
                if formula.startswith('$') and formula.endswith('$'):
                    lines.append(formula)
                else:
                    lines.append(f'${formula}$')
                continue
            
            if tag == 'div' and 'math-display' in element.get('class', []):
                formula = element.get_text().strip()
                if formula.startswith('$$') and formula.endswith('$$'):
                    lines.append(f'\n{formula}\n')
                else:
                    lines.append(f'\n$${formula}$$\n')
                continue
            
            # 标题
            if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(tag[1])
                text = element.get_text().strip()
                if text:
                    lines.append(f"\n{'#' * level} {text}\n")
                continue
            
            # 段落
            if tag == 'p':
                text = element.get_text().strip()
                if text:
                    lines.append(f"\n{text}\n")
                continue
            
            # 代码块
            if tag == 'pre':
                code_tag = element.find('code')
                lang = ''
                if code_tag:
                    lang_classes = code_tag.get('class', [])
                    for cls in lang_classes:
                        if cls.startswith('language-'):
                            lang = cls.replace('language-', '')
                            break
                code_text = element.get_text()
                lines.append(f"\n```{lang}\n{code_text}\n```\n")
                continue
            
            # 引用
            if tag == 'blockquote':
                text = element.get_text().strip()
                if text:
                    lines.append(f"\n> {text}\n")
                continue
        
        return ''.join(lines)


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


# ======================== CSDN爬虫 - 数学公式深度优化版 ========================

class CSDNCrawler(BaseCrawler):
    """CSDN博客爬虫 - 数学公式深度优化"""
    
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
                    if title and len(title) > 3:
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
        """增强的内容提取 - 数学公式深度优化"""
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
            
            # 修复: 使用 string 参数替代 text 参数
            for tag in content.find_all(string=re.compile('已收录|版权声明|©️|查看原文')):
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
            
            # 处理数学公式 - 深度优化
            content = self.process_math_formulas(content)
            
            # 处理代码块
            for pre in content.find_all('pre'):
                # 保留代码块的语言标识
                code_tag = pre.find('code')
                if code_tag:
                    lang_classes = code_tag.get('class', [])
                    for cls in lang_classes:
                        if cls.startswith('language-'):
                            lang = cls.replace('language-', '')
                            pre['data-lang'] = lang
                            break
                pre['class'] = 'code-block'
            
            article.html_content = str(content)
            article.content = self.html_to_markdown(content)
            
        except Exception as e:
            article.content = f"_提取失败: {str(e)}_"
            article.html_content = f"<p><em>提取失败: {str(e)}</em></p>"


# ======================== GitBook爬虫 ========================

class GitBookCrawler(BaseCrawler):
    """GitBook文档爬虫"""
    
    def extract_gitbook_info(self, url: str) -> Tuple[str, List[Article]]:
        """提取GitBook的文档结构"""
        response = self.session.get(url, headers=self.headers, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取标题
        title_tag = soup.find('h1') or soup.find('title')
        title = title_tag.get_text().strip() if title_tag else "GitBook文档"
        
        # 提取目录/章节
        articles = []
        
        # GitBook通常有导航栏或目录
        nav_selectors = [
            ('nav', {'class': re.compile('book-summary|navigation|sidebar')}),
            ('div', {'class': re.compile('toc|summary|navigation')}),
            ('aside', {}),
        ]
        
        nav = None
        for tag, attrs in nav_selectors:
            nav = soup.find(tag, attrs)
            if nav:
                break
        
        if nav:
            # 提取所有链接
            links = nav.find_all('a', href=True)
            for link in links:
                href = link.get('href')
                if href and not href.startswith('#') and not href.startswith('javascript'):
                    # 跳过外部链接
                    if href.startswith('http') and urlparse(href).netloc != urlparse(url).netloc:
                        continue
                    
                    full_url = urljoin(url, href)
                    link_title = link.get_text().strip()
                    if link_title and len(link_title) > 1:
                        articles.append(Article(link_title, full_url))
        
        # 如果没找到导航，至少添加当前页
        if not articles:
            articles.append(Article(title, url))
        
        # 去重
        seen = set()
        unique = []
        for art in articles:
            if art.url not in seen:
                seen.add(art.url)
                unique.append(art)
        
        return title, unique
    
    def extract_article_content(self, article: Article, download_images: bool, img_dir: str):
        """提取GitBook文章内容"""
        try:
            response = self.session.get(article.url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # GitBook内容区域选择器
            content_selectors = [
                ('div', {'class': re.compile('page-wrapper|markdown-section|book-body')}),
                ('article', {}),
                ('main', {}),
                ('div', {'class': 'content'}),
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
            
            # 移除导航元素
            for tag in content.find_all(class_=re.compile('navigation|sidebar|toc-menu')):
                tag.decompose()
            
            # 处理数学公式
            content = self.process_math_formulas(content)
            
            # 处理图片
            if download_images:
                for img in content.find_all('img'):
                    src = img.get('src') or img.get('data-src')
                    if src:
                        img_url = urljoin(article.url, src)
                        local_path = self.download_image(img_url, img_dir, article.url)
                        img['src'] = local_path
                        if not img.get('alt'):
                            img['alt'] = 'image'
            
            # 处理代码块
            for pre in content.find_all('pre'):
                code_tag = pre.find('code')
                if code_tag:
                    lang_classes = code_tag.get('class', [])
                    for cls in lang_classes:
                        if cls.startswith('language-'):
                            lang = cls.replace('language-', '')
                            pre['data-lang'] = lang
                            break
                pre['class'] = 'code-block'
            
            article.html_content = str(content)
            article.content = self.html_to_markdown(content)
            
        except Exception as e:
            article.content = f"_提取失败: {str(e)}_"
            article.html_content = f"<p><em>提取失败: {str(e)}</em></p>"


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
            elif self.platform == 'gitbook':
                self.crawl_gitbook()
            
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
            self.generate_separate_files(articles)
    
    def crawl_csdn(self):
        self.progress_signal.emit("📖 正在分析CSDN...")
        
        crawler = CSDNCrawler()
        
        # 判断是专栏还是单篇文章
        if '/column/info/' in self.url or '/category_' in self.url:
            # 专栏模式
            articles = crawler.extract_column_articles(self.url)
            if not articles:
                raise Exception("未找到任何文章")
            
            title = f"CSDN专栏_{len(articles)}篇"
            self.progress_signal.emit(f"📚 专栏: {len(articles)}篇文章")
        else:
            # 单篇文章模式
            articles = [Article("未命名", self.url)]
            title = "CSDN文章"
            self.progress_signal.emit(f"📄 单篇文章")
        
        img_dir = os.path.join(self.output_dir, 'images')
        
        for idx, article in enumerate(articles, 1):
            if not self.is_running:
                return
            
            self.progress_signal.emit(f"📄 [{idx}/{len(articles)}] 提取中...")
            crawler.extract_article_content(article, self.download_images, img_dir)
            time.sleep(1)  # CSDN需要更长延迟
        
        # 根据模式生成文件
        if self.aggregate_mode and len(articles) > 1:
            self.generate_files(title, articles, articles[0].author if articles else "")
        else:
            self.generate_separate_files(articles)
    
    def crawl_gitbook(self):
        self.progress_signal.emit("📖 正在分析GitBook...")
        
        crawler = GitBookCrawler()
        title, articles = crawler.extract_gitbook_info(self.url)
        
        if not articles:
            raise Exception("未找到任何章节")
        
        self.progress_signal.emit(f"📚 文档: {title}")
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
            self.generate_files(title, articles, "GitBook")
        else:
            self.generate_separate_files(articles)
    
    def generate_separate_files(self, articles: List[Article]):
        """每篇文章独立文件 - 使用文章标题命名"""
        for idx, article in enumerate(articles, 1):
            if not self.is_running:
                return
            
            # 使用文章标题作为文件名
            safe_title = re.sub(r'[\\/:"*?<>|]+', '_', article.title)
            safe_title = safe_title.strip()[:100]  # 限制长度
            
            if not safe_title or safe_title == "未命名":
                safe_title = f"文章_{idx}"
            
            if 'markdown' in self.output_formats:
                md_path = os.path.join(self.output_dir, f"{safe_title}.md")
                self.generate_markdown(md_path, article.title, [article], article.author)
            
            if 'html' in self.output_formats:
                html_path = os.path.join(self.output_dir, f"{safe_title}.html")
                self.generate_html(html_path, article.title, [article], article.author)
            
            if 'pdf' in self.output_formats and WEASY_AVAILABLE:
                pdf_path = os.path.join(self.output_dir, f"{safe_title}.pdf")
                self.generate_pdf(pdf_path, article.title, [article], article.author)
            
            self.progress_signal.emit(f"✅ [{idx}/{len(articles)}] {safe_title}")
    
    def generate_files(self, title: str, articles: List[Article], author: str):
        """聚合模式 - 使用标题命名"""
        # 智能文件名
        if articles and articles[0].title and articles[0].title != "未命名":
            safe_title = re.sub(r'[\\/:"*?<>|]+', '_', articles[0].title)
        else:
            safe_title = re.sub(r'[\\/:"*?<>|]+', '_', title)
        
        safe_title = safe_title.strip()[:100]
        if not safe_title:
            safe_title = "文档"
        
        if 'markdown' in self.output_formats:
            md_path = os.path.join(self.output_dir, f"{safe_title}.md")
            self.generate_markdown(md_path, title, articles, author)
        
        if 'html' in self.output_formats:
            html_path = os.path.join(self.output_dir, f"{safe_title}.html")
            self.generate_html(html_path, title, articles, author)
        
        if 'pdf' in self.output_formats and WEASY_AVAILABLE:
            pdf_path = os.path.join(self.output_dir, f"{safe_title}.pdf")
            self.generate_pdf(pdf_path, title, articles, author)
    
    def generate_markdown(self, filepath: str, title: str, articles: List[Article], author: str):
        """生成Markdown文件 - 优化数学公式"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write(f"> **作者**: {author}\n")
            f.write(f"> **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            for idx, art in enumerate(articles, 1):
                if len(articles) > 1:
                    f.write(f"## {idx}. {art.title}\n\n")
                else:
                    f.write(f"## {art.title}\n\n")
                
                if art.author:
                    f.write(f"**作者**: {art.author}  \n")
                if art.date:
                    f.write(f"**日期**: {art.date}  \n")
                if art.url:
                    f.write(f"**原文**: {art.url}  \n")
                
                f.write("\n")
                f.write(art.content)
                f.write("\n\n---\n\n")
        
        self.progress_signal.emit(f"✅ Markdown: {os.path.basename(filepath)}")
    
    def generate_html(self, filepath: str, title: str, articles: List[Article], platform: str):
        """生成HTML文件 - 增强数学公式支持"""
        html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Microsoft YaHei";
            line-height: 1.8;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}
        h1 {{
            font-size: 2.5em;
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }}
        h2 {{
            font-size: 2em;
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
            padding-left: 15px;
            border-left: 5px solid #3498db;
        }}
        h3 {{
            font-size: 1.5em;
            color: #555;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        .meta {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
            font-size: 0.95em;
        }}
        .meta strong {{
            color: #2980b9;
        }}
        .article {{
            margin-bottom: 50px;
            padding-bottom: 30px;
            border-bottom: 2px dashed #ddd;
        }}
        .article:last-child {{
            border-bottom: none;
        }}
        .article-meta {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-bottom: 15px;
        }}
        p {{
            margin: 15px 0;
            text-align: justify;
        }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
            border-radius: 5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .code-block, pre {{
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 20px 0;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.5;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            padding-left: 20px;
            margin: 20px 0;
            color: #555;
            background: #f9f9f9;
            padding: 15px 20px;
            border-radius: 0 5px 5px 0;
        }}
        /* 数学公式样式 */
        .math-inline {{
            display: inline;
            margin: 0 2px;
        }}
        .math-display {{
            display: block;
            margin: 20px 0;
            text-align: center;
            overflow-x: auto;
            padding: 15px;
            background: #f9f9f9;
            border-radius: 5px;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .timestamp {{
            text-align: center;
            color: #95a5a6;
            font-size: 0.85em;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
        }}
    </style>
    <!-- MathJax 3.x 配置 - 支持所有LaTeX公式 -->
    <script>
        window.MathJax = {{
            tex: {{
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']],
                processEscapes: true,
                processEnvironments: true,
                tags: 'ams',
                packages: {{'[+]': ['ams', 'newcommand', 'configmacros']}}
            }},
            options: {{
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
                ignoreHtmlClass: 'tex2jax_ignore',
                processHtmlClass: 'tex2jax_process'
            }},
            startup: {{
                pageReady: () => {{
                    return MathJax.startup.defaultPageReady().then(() => {{
                        console.log('MathJax 已加载完成');
                    }});
                }}
            }},
            svg: {{
                fontCache: 'global'
            }}
        }};
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js" async></script>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="meta">
            <p><strong>平台</strong>: {platform}</p>
            <p><strong>生成时间</strong>: {generation_time}</p>
            <p><strong>章节数</strong>: {article_count}</p>
        </div>
        {articles_html}
        <div class="timestamp">
            Generated by Web Content Extractor Pro v8.1
        </div>
    </div>
</body>
</html>"""
        
        articles_html = []
        for idx, article in enumerate(articles, 1):
            article_html = f'<div class="article">'
            article_html += f'<h2>{idx}. {article.title}</h2>'
            
            meta_parts = []
            if article.url:
                meta_parts.append(f'<a href="{article.url}" target="_blank">查看原文</a>')
            if article.author:
                meta_parts.append(f'作者: {article.author}')
            if article.date:
                meta_parts.append(f'日期: {article.date}')
            
            if meta_parts:
                article_html += f'<div class="article-meta">{" | ".join(meta_parts)}</div>'
            
            article_html += article.html_content
            article_html += '</div>'
            articles_html.append(article_html)
        
        html_content = html_template.format(
            title=title,
            platform=platform,
            generation_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            article_count=len(articles),
            articles_html=''.join(articles_html)
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.progress_signal.emit(f"✅ HTML: {os.path.basename(filepath)}")
    
    def generate_pdf(self, filepath: str, title: str, articles: List[Article], platform: str):
        """生成PDF文件 - 优化字体配置"""
        if not WEASY_AVAILABLE:
            self.progress_signal.emit("⚠️ WeasyPrint未安装，跳过PDF生成")
            return
        
        try:
            # 先生成临时HTML
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as tmp:
                tmp_path = tmp.name
                self.generate_html(tmp_path, title, articles, platform)
            
            # 创建字体配置 - 抑制警告
            font_config = FontConfiguration()
            
            # 生成PDF
            HTML(filename=tmp_path).write_pdf(
                filepath,
                stylesheets=[CSS(string=self.get_pdf_css())],
                font_config=font_config
            )
            
            # 清理临时文件
            try:
                os.remove(tmp_path)
            except:
                pass
            
            self.progress_signal.emit(f"✅ PDF: {os.path.basename(filepath)}")
            
        except Exception as e:
            self.progress_signal.emit(f"⚠️ PDF生成失败: {str(e)}")
    
    def get_pdf_css(self) -> str:
        """PDF专用CSS - 优化打印效果"""
        return """
        @page {
            size: A4;
            margin: 2.5cm 2cm;
        }
        body {
            font-family: "Microsoft YaHei", "SimSun", sans-serif;
            font-size: 11pt;
            line-height: 1.7;
        }
        .chapter {
            page-break-before: always;
        }
        h1, h2, h3 {
            page-break-after: avoid;
        }
        h1 { font-size: 24pt; }
        h2 { font-size: 18pt; margin-top: 20pt; }
        h3 { font-size: 14pt; }
        .article {
            page-break-after: always;
        }
        .code-block, pre {
            font-size: 9pt;
            page-break-inside: avoid;
            background: #f5f5f5;
            border: 1px solid #ddd;
        }
        img {
            max-width: 100%;
            page-break-inside: avoid;
        }
        .math-inline {
            font-family: "Times New Roman", "STIX Two Math", serif;
        }
        .math-display {
            text-align: center;
            margin: 20px 0;
            font-family: "Times New Roman", serif;
        }
        """


# ======================== GUI主窗口 ========================

class MainWindow(QMainWindow):
    """主窗口 - 现代化UI设计"""
    
    def __init__(self):
        super().__init__()
        self.crawler_thread = None
        self.settings = QSettings('WebExtractor', 'v8.1')
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        self.setWindowTitle('Web Content Extractor Pro v8.1 - 数学公式优化版')
        self.setGeometry(100, 100, 1000, 700)
        
        # 设置应用字体
        app_font = QFont('Microsoft YaHei', 10)
        self.setFont(app_font)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # ===== 标题区域 =====
        title_label = QLabel('📚 Web Content Extractor Pro')
        title_font = QFont('Microsoft YaHei', 18, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet('color: #2c3e50; padding: 10px;')
        main_layout.addWidget(title_label)
        
        # ===== URL输入区域 =====
        url_group = QGroupBox('📎 URL地址')
        url_group.setFont(QFont('Microsoft YaHei', 11, QFont.Bold))
        url_layout = QVBoxLayout()
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText('请输入网页URL...')
        self.url_input.setFont(QFont('Microsoft YaHei', 10))
        self.url_input.setMinimumHeight(40)
        url_layout.addWidget(self.url_input)
        
        url_group.setLayout(url_layout)
        main_layout.addWidget(url_group)
        
        # ===== 平台选择 =====
        platform_group = QGroupBox('🌐 选择平台')
        platform_group.setFont(QFont('Microsoft YaHei', 11, QFont.Bold))
        platform_layout = QHBoxLayout()
        
        self.platform_combo = QComboBox()
        self.platform_combo.addItems([
            '菜鸟教程 (runoob.com)',
            'CSDN博客/专栏 (blog.csdn.net)',
            'GitBook文档 (*.gitbook.io)'
        ])
        self.platform_combo.setFont(QFont('Microsoft YaHei', 10))
        self.platform_combo.setMinimumHeight(35)
        platform_layout.addWidget(self.platform_combo)
        
        platform_group.setLayout(platform_layout)
        main_layout.addWidget(platform_group)
        
        # ===== 输出选项 =====
        options_group = QGroupBox('⚙️ 输出选项')
        options_group.setFont(QFont('Microsoft YaHei', 11, QFont.Bold))
        options_layout = QVBoxLayout()
        
        # 输出格式
        format_layout = QHBoxLayout()
        format_label = QLabel('输出格式:')
        format_label.setFont(QFont('Microsoft YaHei', 10))
        format_layout.addWidget(format_label)
        
        self.markdown_check = QCheckBox('Markdown')
        self.html_check = QCheckBox('HTML')
        self.pdf_check = QCheckBox('PDF')
        for cb in [self.markdown_check, self.html_check, self.pdf_check]:
            cb.setFont(QFont('Microsoft YaHei', 10))
            cb.setChecked(True)
            format_layout.addWidget(cb)
        
        format_layout.addStretch()
        options_layout.addLayout(format_layout)
        
        # 其他选项
        self.download_img_check = QCheckBox('下载图片到本地')
        self.download_img_check.setChecked(True)
        self.download_img_check.setFont(QFont('Microsoft YaHei', 10))
        options_layout.addWidget(self.download_img_check)
        
        self.aggregate_check = QCheckBox('合并为单个文件（取消则每章独立）')
        self.aggregate_check.setChecked(True)
        self.aggregate_check.setFont(QFont('Microsoft YaHei', 10))
        options_layout.addWidget(self.aggregate_check)
        
        # 输出目录
        dir_layout = QHBoxLayout()
        dir_label = QLabel('输出目录:')
        dir_label.setFont(QFont('Microsoft YaHei', 10))
        dir_layout.addWidget(dir_label)
        
        self.output_dir_input = QLineEdit('./output')
        self.output_dir_input.setFont(QFont('Microsoft YaHei', 10))
        dir_layout.addWidget(self.output_dir_input)
        
        dir_btn = QPushButton('浏览...')
        dir_btn.setFont(QFont('Microsoft YaHei', 10))
        dir_btn.clicked.connect(self.select_output_dir)
        dir_layout.addWidget(dir_btn)
        
        options_layout.addLayout(dir_layout)
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)
        
        # ===== 控制按钮 =====
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton('🚀 开始提取')
        self.start_btn.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        self.start_btn.setMinimumHeight(45)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.start_btn.clicked.connect(self.start_crawl)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton('⏹️ 停止')
        self.stop_btn.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        self.stop_btn.setMinimumHeight(45)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_crawl)
        button_layout.addWidget(self.stop_btn)
        
        main_layout.addLayout(button_layout)
        
        # ===== 日志区域 =====
        log_group = QGroupBox('📋 运行日志')
        log_group.setFont(QFont('Microsoft YaHei', 11, QFont.Bold))
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont('Consolas', 9))
        self.log_text.setMinimumHeight(200)
        log_layout.addWidget(self.log_text)
        
        clear_btn = QPushButton('清空日志')
        clear_btn.setFont(QFont('Microsoft YaHei', 9))
        clear_btn.clicked.connect(self.log_text.clear)
        log_layout.addWidget(clear_btn)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # 状态栏
        self.statusBar().showMessage('就绪')
        self.statusBar().setFont(QFont('Microsoft YaHei', 9))
    
    def select_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, '选择输出目录')
        if dir_path:
            self.output_dir_input.setText(dir_path)
    
    def log_message(self, message: str):
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        self.log_text.moveCursor(QTextCursor.End)
    
    def start_crawl(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, '警告', '请输入URL地址!')
            return
        
        # 检查输出格式
        output_formats = []
        if self.markdown_check.isChecked():
            output_formats.append('markdown')
        if self.html_check.isChecked():
            output_formats.append('html')
        if self.pdf_check.isChecked():
            output_formats.append('pdf')
        
        if not output_formats:
            QMessageBox.warning(self, '警告', '请至少选择一种输出格式!')
            return
        
        # 确定平台
        platform_map = {
            0: 'runoob',
            1: 'csdn',
            2: 'gitbook'
        }
        platform = platform_map.get(self.platform_combo.currentIndex(), 'runoob')
        
        # 保存设置
        self.save_settings()
        
        # 创建爬虫线程
        self.crawler_thread = CrawlerThread()
        self.crawler_thread.url = url
        self.crawler_thread.platform = platform
        self.crawler_thread.output_dir = self.output_dir_input.text()
        self.crawler_thread.output_formats = output_formats
        self.crawler_thread.download_images = self.download_img_check.isChecked()
        self.crawler_thread.aggregate_mode = self.aggregate_check.isChecked()
        
        # 连接信号
        self.crawler_thread.progress_signal.connect(self.log_message)
        self.crawler_thread.finished_signal.connect(self.on_crawl_finished)
        
        # 更新UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log_text.clear()
        self.statusBar().showMessage('正在提取...')
        
        # 启动线程
        self.crawler_thread.start()
    
    def stop_crawl(self):
        if self.crawler_thread and self.crawler_thread.isRunning():
            self.crawler_thread.stop()
            self.log_message("⏹️ 用户停止操作")
            self.statusBar().showMessage('已停止')
    
    def on_crawl_finished(self, success: bool, message: str):
        self.log_message(message)
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        if success:
            self.statusBar().showMessage('完成!')
            QMessageBox.information(self, '完成', message)
        else:
            self.statusBar().showMessage('失败')
            QMessageBox.critical(self, '错误', message)
    
    def save_settings(self):
        self.settings.setValue('url', self.url_input.text())
        self.settings.setValue('platform', self.platform_combo.currentIndex())
        self.settings.setValue('output_dir', self.output_dir_input.text())
        self.settings.setValue('markdown', self.markdown_check.isChecked())
        self.settings.setValue('html', self.html_check.isChecked())
        self.settings.setValue('pdf', self.pdf_check.isChecked())
        self.settings.setValue('download_images', self.download_img_check.isChecked())
        self.settings.setValue('aggregate', self.aggregate_check.isChecked())
    
    def load_settings(self):
        self.url_input.setText(self.settings.value('url', ''))
        self.platform_combo.setCurrentIndex(int(self.settings.value('platform', 0)))
        self.output_dir_input.setText(self.settings.value('output_dir', './output'))
        self.markdown_check.setChecked(self.settings.value('markdown', True, type=bool))
        self.html_check.setChecked(self.settings.value('html', True, type=bool))
        self.pdf_check.setChecked(self.settings.value('pdf', True, type=bool))
        self.download_img_check.setChecked(self.settings.value('download_images', True, type=bool))
        self.aggregate_check.setChecked(self.settings.value('aggregate', True, type=bool))
    
    def closeEvent(self, event):
        if self.crawler_thread and self.crawler_thread.isRunning():
            reply = QMessageBox.question(
                self, '确认退出',
                '爬虫正在运行，确定要退出吗？',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.crawler_thread.stop()
                self.crawler_thread.wait(3000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


# ======================== 主程序入口 ========================

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion样式
    
    # 设置全局字体
    font = QFont('Microsoft YaHei', 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()