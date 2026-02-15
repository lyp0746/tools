# -*- coding: utf-8 -*-
"""
Web Content Extractor Pro v11.1 - Bug修复版
基于PyQt5和BeautifulSoup开发，支持多平台内容提取、多格式输出、数学公式处理
github网址: https://github.com/lyp0746
QQ邮箱: 1610369302@qq.com
作者: LYP

v11.1 修复:
- [修复] 菜鸟教程: 入口页面"XXX教程"不再丢失，作为第一篇章节插入
- [修复] 聚合文件名: 改为以第一篇文章标题命名
- [增强] PDF样式: 更专业的书籍排版 — 优化封面/目录/正文/代码块/页眉页脚
"""
import sys
import os
import re
import html as html_module
import warnings
import hashlib
import tempfile
import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Set
from urllib.parse import urljoin, urlparse, quote
from dataclasses import dataclass, field
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QTextEdit, QFileDialog, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal, QSettings
from PyQt5.QtGui import QFont, QTextCursor

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message="sipPyTypeDict")

try:
    from weasyprint import HTML as WeasyHTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASY_AVAILABLE = True
except ImportError:
    WEASY_AVAILABLE = False


# ==================== 数据结构 ====================

@dataclass
class Article:
    """文章数据"""
    title: str
    url: str
    level: int = 1              # 层级 (1=章, 2=节, 3=小节)
    content: str = ""           # Markdown 内容
    html_content: str = ""      # HTML 内容
    author: str = ""
    date: str = ""
    category: str = ""
    anchor: str = ""            # 唯一锚点ID (用于目录跳转)
    children: List['Article'] = field(default_factory=list)  # 子页面内容


# ==================== 公式存储 ====================

class MathStore:
    """独立的公式存储，避免公式在HTML/Markdown转换中被破坏"""

    def __init__(self):
        self._formulas: List[Tuple[str, bool]] = []  # (latex, is_display)

    def store(self, latex: str, is_display: bool) -> str:
        """存储一个公式，返回占位符"""
        idx = len(self._formulas)
        self._formulas.append((latex, is_display))
        tag = 'DISPLAY' if is_display else 'INLINE'
        return f'§MATH_{tag}_{idx}§'

    def restore_markdown(self, text: str) -> str:
        """还原为Markdown格式的LaTeX公式"""
        for idx, (latex, is_display) in enumerate(self._formulas):
            if is_display:
                text = text.replace(f'§MATH_DISPLAY_{idx}§', f'\n\n$$\n{latex}\n$$\n\n')
            else:
                text = text.replace(f'§MATH_INLINE_{idx}§', f'${latex}$')
        return text

    def restore_html(self, text: str) -> str:
        """还原为HTML格式，保留原始LaTeX供MathJax渲染"""
        for idx, (latex, is_display) in enumerate(self._formulas):
            escaped = html_module.escape(latex)
            if is_display:
                text = text.replace(
                    f'§MATH_DISPLAY_{idx}§',
                    f'<div class="math-display">$${escaped}$$</div>')
            else:
                text = text.replace(
                    f'§MATH_INLINE_{idx}§',
                    f'<span class="math-inline">${escaped}$</span>')
        return text

    def restore_pdf(self, text: str) -> str:
        """还原为PDF可渲染格式（Unicode近似 + 原始LaTeX注释）"""
        for idx, (latex, is_display) in enumerate(self._formulas):
            readable = _latex_to_readable(latex)
            escaped_readable = html_module.escape(readable)
            escaped_latex = html_module.escape(latex)
            if is_display:
                text = text.replace(
                    f'§MATH_DISPLAY_{idx}§',
                    f'<div class="math-display" title="{escaped_latex}">'
                    f'{escaped_readable}</div>')
            else:
                text = text.replace(
                    f'§MATH_INLINE_{idx}§',
                    f'<span class="math-inline" title="{escaped_latex}">'
                    f'{escaped_readable}</span>')
        return text

    @property
    def empty(self) -> bool:
        return len(self._formulas) == 0


def _latex_to_readable(latex: str) -> str:
    """LaTeX → 可读Unicode文本 (用于PDF降级显示)"""
    text = latex
    _REPLACEMENTS = [
        (r'\\frac\{([^}]*)\}\{([^}]*)\}', r'(\1)/(\2)'),
        (r'\\sqrt\[([^\]]*)\]\{([^}]*)\}', r'(\2)^(1/\1)'),
        (r'\\sqrt\{([^}]*)\}', r'√(\1)'),
        (r'\\overline\{([^}]*)\}', r'\1̄'),
        (r'\\hat\{([^}]*)\}', r'\1̂'),
        (r'\\vec\{([^}]*)\}', r'\1⃗'),
        (r'\\dot\{([^}]*)\}', r'\1̇'),
        (r'\\ddot\{([^}]*)\}', r'\1̈'),
        (r'\\tilde\{([^}]*)\}', r'\1̃'),
        (r'\\bar\{([^}]*)\}', r'\1̄'),
        (r'\^{([^}]*)}', r'^(\1)'),
        (r'_{([^}]*)}', r'_(\1)'),
        (r'\^(\w)', r'^\1'),
        (r'_(\w)', r'_\1'),
        (r'\\alpha', 'α'), (r'\\beta', 'β'), (r'\\gamma', 'γ'),
        (r'\\delta', 'δ'), (r'\\epsilon', 'ε'), (r'\\varepsilon', 'ε'),
        (r'\\zeta', 'ζ'), (r'\\eta', 'η'), (r'\\theta', 'θ'),
        (r'\\vartheta', 'ϑ'), (r'\\iota', 'ι'), (r'\\kappa', 'κ'),
        (r'\\lambda', 'λ'), (r'\\mu', 'μ'), (r'\\nu', 'ν'),
        (r'\\xi', 'ξ'), (r'\\pi', 'π'), (r'\\varpi', 'ϖ'),
        (r'\\rho', 'ρ'), (r'\\varrho', 'ϱ'), (r'\\sigma', 'σ'),
        (r'\\varsigma', 'ς'), (r'\\tau', 'τ'), (r'\\upsilon', 'υ'),
        (r'\\phi', 'φ'), (r'\\varphi', 'ϕ'), (r'\\chi', 'χ'),
        (r'\\psi', 'ψ'), (r'\\omega', 'ω'),
        (r'\\Gamma', 'Γ'), (r'\\Delta', 'Δ'), (r'\\Theta', 'Θ'),
        (r'\\Lambda', 'Λ'), (r'\\Xi', 'Ξ'), (r'\\Pi', 'Π'),
        (r'\\Sigma', 'Σ'), (r'\\Upsilon', 'Υ'), (r'\\Phi', 'Φ'),
        (r'\\Psi', 'Ψ'), (r'\\Omega', 'Ω'),
        (r'\\sum', '∑'), (r'\\prod', '∏'), (r'\\coprod', '∐'),
        (r'\\int', '∫'), (r'\\iint', '∬'), (r'\\iiint', '∭'),
        (r'\\oint', '∮'),
        (r'\\infty', '∞'), (r'\\nabla', '∇'), (r'\\partial', '∂'),
        (r'\\leq', '≤'), (r'\\le', '≤'), (r'\\geq', '≥'), (r'\\ge', '≥'),
        (r'\\neq', '≠'), (r'\\ne', '≠'), (r'\\approx', '≈'),
        (r'\\equiv', '≡'), (r'\\sim', '∼'), (r'\\simeq', '≃'),
        (r'\\cong', '≅'), (r'\\propto', '∝'),
        (r'\\ll', '≪'), (r'\\gg', '≫'),
        (r'\\times', '×'), (r'\\div', '÷'), (r'\\cdot', '·'),
        (r'\\pm', '±'), (r'\\mp', '∓'), (r'\\circ', '∘'),
        (r'\\oplus', '⊕'), (r'\\otimes', '⊗'),
        (r'\\rightarrow', '→'), (r'\\to', '→'),
        (r'\\leftarrow', '←'), (r'\\gets', '←'),
        (r'\\Rightarrow', '⇒'), (r'\\Leftarrow', '⇐'),
        (r'\\leftrightarrow', '↔'), (r'\\Leftrightarrow', '⇔'),
        (r'\\mapsto', '↦'), (r'\\uparrow', '↑'), (r'\\downarrow', '↓'),
        (r'\\forall', '∀'), (r'\\exists', '∃'), (r'\\nexists', '∄'),
        (r'\\neg', '¬'), (r'\\land', '∧'), (r'\\lor', '∨'),
        (r'\\in', '∈'), (r'\\notin', '∉'), (r'\\ni', '∋'),
        (r'\\subset', '⊂'), (r'\\supset', '⊃'),
        (r'\\subseteq', '⊆'), (r'\\supseteq', '⊇'),
        (r'\\cup', '∪'), (r'\\cap', '∩'),
        (r'\\emptyset', '∅'), (r'\\varnothing', '∅'),
        (r'\\ldots', '…'), (r'\\cdots', '⋯'), (r'\\vdots', '⋮'), (r'\\ddots', '⋱'),
        (r'\\quad', '  '), (r'\\qquad', '    '), (r'\\,', ' '), (r'\\;', ' '),
        (r'\\!', ''),
        (r'\\langle', '⟨'), (r'\\rangle', '⟩'),
        (r'\\lfloor', '⌊'), (r'\\rfloor', '⌋'),
        (r'\\lceil', '⌈'), (r'\\rceil', '⌉'),
        (r'\\star', '⋆'), (r'\\bullet', '•'), (r'\\dagger', '†'),
        (r'\\text\{([^}]*)\}', r'\1'),
        (r'\\textbf\{([^}]*)\}', r'\1'),
        (r'\\textit\{([^}]*)\}', r'\1'),
        (r'\\mathrm\{([^}]*)\}', r'\1'),
        (r'\\mathbf\{([^}]*)\}', r'\1'),
        (r'\\mathit\{([^}]*)\}', r'\1'),
        (r'\\mathcal\{([^}]*)\}', r'\1'),
        (r'\\mathbb\{([^}]*)\}', r'\1'),
        (r'\\operatorname\{([^}]*)\}', r'\1'),
        (r'\\(sin|cos|tan|cot|sec|csc|arcsin|arccos|arctan|sinh|cosh|tanh'
         r'|log|ln|exp|lim|sup|inf|max|min|det|dim|ker|gcd|deg|hom|arg)', r'\1'),
        (r'\\left', ''), (r'\\right', ''),
        (r'\\big', ''), (r'\\Big', ''), (r'\\bigg', ''), (r'\\Bigg', ''),
        (r'\\[{}]', ''), (r'\{', '('), (r'\}', ')'),
        (r'\\\\', '\n'), (r'&', ' '),
    ]
    for pattern, repl in _REPLACEMENTS:
        text = re.sub(pattern, repl, text)
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text if text else latex


# ==================== 工具函数 ====================

def _make_anchor(title: str, index: int = 0) -> str:
    """生成GitBook风格的锚点ID"""
    anchor = re.sub(r'[^\w\u4e00-\u9fff]+', '-', title).strip('-').lower()
    return f"chapter-{index}-{anchor}" if index else anchor


def _slugify(title: str) -> str:
    """生成安全文件名"""
    s = re.sub(r'[\\/:*?"<>|]+', '_', title).strip()[:100]
    # 如果标题为空或只包含特殊字符，使用"教程"而不是"文档"
    if not s or re.match(r'^[_\s]+$', s):
        return "教程"
    return s


# ==================== 爬虫基类 ====================

class BaseCrawler:
    """爬虫基类 — 图片下载、HTML清理、公式处理、Markdown转换"""

    IMG_ATTRS = ('src', 'data-src', 'data-original-src', 'data-original',
                 'data-actualsrc', 'data-lazy-src', 'data-echo',
                 'data-url', 'data-img')

    def __init__(self):
        self.headers = {
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/125.0.0.0 Safari/537.36'),
            'Accept': ('text/html,application/xhtml+xml,application/xml;'
                       'q=0.9,image/avif,image/webp,*/*;q=0.8'),
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self._img_cache: Dict[str, str] = {}

    def fetch(self, url: str, retries: int = 2, **kwargs) -> requests.Response:
        last_err = None
        for attempt in range(retries + 1):
            try:
                resp = self.session.get(url, headers=self.headers, timeout=20, **kwargs)
                resp.encoding = resp.apparent_encoding or 'utf-8'
                return resp
            except Exception as e:
                last_err = e
                if attempt < retries:
                    time.sleep(1 * (attempt + 1))
        raise last_err

    def fetch_soup(self, url: str) -> BeautifulSoup:
        return BeautifulSoup(self.fetch(url).text, 'html.parser')

    @staticmethod
    def _get_img_src(img: Tag) -> str:
        for attr in BaseCrawler.IMG_ATTRS:
            val = img.get(attr, '')
            if val and not val.startswith('data:'):
                return val.strip()
        srcset = img.get('srcset', '')
        if srcset:
            first = srcset.split(',')[0].strip().split()[0]
            if first and not first.startswith('data:'):
                return first
        return ''

    def download_image(self, url: str, img_dir: str, referer: str = '') -> str:
        if not url or url.startswith('data:'):
            return url
        clean_url = url.split('#')[0]
        if clean_url in self._img_cache:
            return self._img_cache[clean_url]
        for attempt in range(3):
            try:
                headers = self.headers.copy()
                if referer:
                    headers['Referer'] = referer
                resp = self.session.get(clean_url, headers=headers, timeout=20, stream=True)
                if resp.status_code != 200:
                    return url
                ct = resp.headers.get('content-type', '')
                ext = '.png'
                _EXT_MAP = {
                    'jpeg': '.jpg', 'jpg': '.jpg', 'png': '.png',
                    'gif': '.gif', 'webp': '.webp', 'svg+xml': '.svg',
                    'svg': '.svg', 'bmp': '.bmp', 'ico': '.ico',
                }
                for key, val in _EXT_MAP.items():
                    if key in ct:
                        ext = val
                        break
                else:
                    path = urlparse(clean_url).path.lower()
                    for e in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp'):
                        if e in path:
                            ext = e
                            break
                name = f"img_{hashlib.md5(clean_url.encode()).hexdigest()[:12]}{ext}"
                dest = os.path.join(img_dir, name)
                data = b''
                for chunk in resp.iter_content(8192):
                    data += chunk
                if len(data) < 100:
                    return url
                with open(dest, 'wb') as f:
                    f.write(data)
                result = f"images/{name}"
                self._img_cache[clean_url] = result
                return result
            except Exception as e:
                if attempt == 2:
                    print(f"[IMG] 下载失败: {url} → {e}")
                    return url
                time.sleep(0.5)
        return url

    _REMOVE_TAGS = frozenset(['script', 'style', 'iframe', 'noscript', 'link',
                               'meta', 'template', 'svg'])

    _AD_PATTERNS = re.compile(
        r'adsbygoogle|^ads?[-_]|sponsor|promo[-_]|^banner|popup|modal[-_]'
        r'|overlay|recommend[-_]?box|comment[-_]?box|share[-_]?box'
        r'|social[-_]?share|tooltip|mask[-_]|csdn-side-toolbar'
        r'|follow[-_]?box|login[-_]?box|^footer$|cookie[-_]?notice',
        re.I
    )

    def clean_html(self, soup: Tag) -> Tag:
        for tag in soup.find_all(list(self._REMOVE_TAGS)):
            tag.decompose()
        for tag in soup.find_all(class_=self._AD_PATTERNS):
            if len(tag.get_text(strip=True)) < 200:
                tag.decompose()
        for tag in soup.find_all(style=re.compile(r'display\s*:\s*none', re.I)):
            tag.decompose()
        for tag in soup.find_all(['div', 'span']):
            if not tag.get_text(strip=True) and not tag.find('img'):
                tag.decompose()
        return soup

    @staticmethod
    def _extract_latex(elem: Tag) -> Optional[str]:
        if not elem:
            return None
        html_str = str(elem)
        m = re.search(
            r'<annotation[^>]*encoding="application/x-tex"[^>]*>(.*?)</annotation>',
            html_str, re.DOTALL)
        if m:
            return html_module.unescape(m.group(1).strip())
        for attr in ('data-tex', 'data-latex', 'data-formula', 'data-math'):
            v = elem.get(attr)
            if v:
                return v.strip()
        alt = elem.get('alt', '')
        if alt and ('\\' in alt or '$' in alt):
            return alt.strip().strip('$')
        aria = elem.get('aria-label')
        if aria and '\\' in aria:
            return aria.strip()
        mathml = elem.find(class_='katex-mathml')
        if mathml:
            ann = mathml.find('annotation')
            if ann and ann.string:
                return ann.string.strip()
            t = mathml.get_text(strip=True)
            if t:
                return t
        text = elem.get_text(strip=True)
        return text if text else None

    @staticmethod
    def _is_display(elem: Tag) -> bool:
        classes = elem.get('class', [])
        if isinstance(classes, str):
            classes = classes.split()
        class_str = ' '.join(classes)
        if any(kw in class_str for kw in (
                'display', 'block', 'katex-display', 'ql-display',
                'MathJax_Display', 'mjx-chtml')):
            return True
        style = elem.get('style', '')
        if 'display' in style and 'block' in style:
            return True
        if elem.name in ('div', 'p') and elem.find(class_=re.compile(r'katex|mathjax', re.I)):
            children = [c for c in elem.children
                        if isinstance(c, Tag) or (isinstance(c, NavigableString) and c.strip())]
            if len(children) == 1:
                return True
        return False

    def process_math(self, content: Tag) -> Tuple[Tag, MathStore]:
        store = MathStore()
        for script in content.find_all('script', type=re.compile(r'math/tex')):
            formula = (script.string or '').strip()
            if not formula:
                continue
            is_disp = 'mode=display' in (script.get('type') or '')
            ph = store.store(formula, is_disp)
            script.replace_with(NavigableString(ph))
        for elem in content.find_all(class_=re.compile(r'katex-display', re.I)):
            latex = self._extract_latex(elem)
            if latex:
                elem.replace_with(NavigableString(store.store(latex, True)))
        for elem in content.find_all(class_=re.compile(
                r'^katex$|MathJax|math-tex|mathjax', re.I)):
            latex = self._extract_latex(elem)
            if latex:
                elem.replace_with(NavigableString(
                    store.store(latex, self._is_display(elem))))
        for text_node in list(content.find_all(string=True)):
            s = str(text_node)
            if '\\(' not in s and '\\[' not in s:
                continue
            changed = False
            def _repl_disp(m):
                nonlocal changed
                changed = True
                return store.store(m.group(1).strip(), True)
            def _repl_inl(m):
                nonlocal changed
                changed = True
                return store.store(m.group(1).strip(), False)
            s = re.sub(r'\\\[(.*?)\\\]', _repl_disp, s, flags=re.DOTALL)
            s = re.sub(r'\\\((.*?)\\\)', _repl_inl, s)
            if changed:
                text_node.replace_with(NavigableString(s))
        for text_node in list(content.find_all(string=True)):
            s = str(text_node)
            if '$' not in s:
                continue
            changed = False
            def _repl_dd(m):
                nonlocal changed
                inner = m.group(1).strip()
                if '\\' in inner or '_' in inner or '^' in inner:
                    changed = True
                    return store.store(inner, True)
                return m.group(0)
            def _repl_ds(m):
                nonlocal changed
                inner = m.group(1).strip()
                if '\\' in inner or '_' in inner or '^' in inner:
                    changed = True
                    return store.store(inner, False)
                return m.group(0)
            s = re.sub(r'\$\$(.*?)\$\$', _repl_dd, s, flags=re.DOTALL)
            s = re.sub(r'(?<!\$)\$(?!\$)((?:[^$\\]|\\.)+?)\$(?!\$)', _repl_ds, s)
            if changed:
                text_node.replace_with(NavigableString(s))
        return content, store

    def process_content(self, content: Tag, article: Article,
                        download_images: bool, img_dir: str) -> MathStore:
        content = self.clean_html(content)
        self._extra_clean(content, article)
        if download_images:
            for img in content.find_all('img'):
                src = self._get_img_src(img)
                if src:
                    img_url = urljoin(article.url, src)
                    local = self.download_image(img_url, img_dir, article.url)
                    img['src'] = local
                    for attr in self.IMG_ATTRS:
                        if attr != 'src' and img.has_attr(attr):
                            del img[attr]
                    if img.has_attr('srcset'):
                        del img['srcset']
                    if not img.get('alt'):
                        img['alt'] = '图片'
        content, math_store = self.process_math(content)
        article.html_content = math_store.restore_html(str(content))
        article.content = self._html_to_markdown(content, math_store)
        return math_store

    def _extra_clean(self, content: Tag, article: Article):
        pass

    def _html_to_markdown(self, content: Tag, math_store: MathStore) -> str:
        result = self._elem_to_md(content, 0)
        result = math_store.restore_markdown(result)
        result = re.sub(r'\n{3,}', '\n\n', result)
        result = re.sub(r'([^\n])\n([-*] |\d+\. )', r'\1\n\n\2', result)
        return result.strip()

    def _elem_to_md(self, elem, indent: int = 0) -> str:
        if isinstance(elem, NavigableString):
            s = str(elem)
            if '§MATH_' in s:
                return s
            return re.sub(r'[ \t]+', ' ', s)
        if not isinstance(elem, Tag):
            return ''
        tag = elem.name
        if tag in self._REMOVE_TAGS:
            return ''
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            t = elem.get_text(strip=True)
            return f"\n\n{'#' * int(tag[1])} {t}\n\n" if t else ''
        if tag == 'p':
            inner = self._children_md(elem, indent).strip()
            return f"\n\n{inner}\n\n" if inner else ''
        if tag == 'img':
            return self._img_md(elem)
        if tag == 'figure':
            parts = ''
            img = elem.find('img')
            if img:
                parts = self._img_md(img)
            cap = elem.find('figcaption')
            if cap:
                ct = cap.get_text(strip=True)
                if ct:
                    parts += f"\n*{ct}*\n"
            return f"\n{parts}\n" if parts else ''
        if tag == 'picture':
            img = elem.find('img')
            return self._img_md(img) if img else ''
        if tag == 'a':
            img = elem.find('img')
            if img:
                return self._img_md(img)
            href = (elem.get('href') or '').strip()
            text = elem.get_text(strip=True)
            if text and href and href != '#' and not href.startswith('javascript'):
                return f"[{text}]({href})"
            return text or ''
        if tag == 'pre':
            code = elem.find('code')
            text = code.get_text() if code else elem.get_text()
            lang = self._detect_lang(code or elem)
            return f"\n\n```{lang}\n{text.rstrip()}\n```\n\n"
        if tag == 'code' and (not elem.parent or elem.parent.name != 'pre'):
            t = elem.get_text(strip=True)
            if not t:
                return ''
            return f"`` {t} ``" if '`' in t else f"`{t}`"
        if tag == 'blockquote':
            inner = self._children_md(elem, indent).strip()
            if not inner:
                return ''
            quoted = '\n'.join(f"> {line}" for line in inner.split('\n') if line.strip())
            return f"\n\n{quoted}\n\n"
        if tag in ('ul', 'ol'):
            return self._list_md(elem, tag, indent)
        if tag == 'li':
            return self._children_md(elem, indent).strip()
        if tag == 'table':
            return self._table_md(elem)
        if tag in ('strong', 'b'):
            t = self._children_md(elem, indent).strip()
            return f"**{t}**" if t else ''
        if tag in ('em', 'i'):
            t = self._children_md(elem, indent).strip()
            return f"*{t}*" if t else ''
        if tag in ('del', 's', 'strike'):
            t = elem.get_text(strip=True)
            return f"~~{t}~~" if t else ''
        if tag in ('mark',):
            t = self._children_md(elem, indent).strip()
            return f"=={t}==" if t else ''
        if tag in ('sub',):
            t = elem.get_text(strip=True)
            return f"~{t}~" if t else ''
        if tag in ('sup',):
            t = elem.get_text(strip=True)
            return f"^{t}^" if t else ''
        if tag == 'br':
            return '\n'
        if tag == 'hr':
            return '\n\n---\n\n'
        if tag == 'details':
            summary = elem.find('summary')
            s_text = summary.get_text(strip=True) if summary else '详情'
            if summary:
                summary.decompose()
            inner = self._children_md(elem, indent).strip()
            return f"\n\n<details>\n<summary>{s_text}</summary>\n\n{inner}\n\n</details>\n\n"
        if tag == 'summary':
            return ''
        return self._children_md(elem, indent)

    def _children_md(self, elem: Tag, indent: int) -> str:
        return ''.join(self._elem_to_md(c, indent) for c in elem.children)

    def _img_md(self, img: Tag) -> str:
        src = self._get_img_src(img)
        if not src:
            return ''
        alt = (img.get('alt') or '图片')
        alt = alt.replace('[', '').replace(']', '').replace('\n', ' ').strip()[:80]
        return f"\n\n![{alt}]({src})\n\n"

    @staticmethod
    def _detect_lang(elem: Tag) -> str:
        classes = elem.get('class', [])
        if isinstance(classes, str):
            classes = classes.split()
        for cls in classes:
            if cls.startswith('language-') or cls.startswith('lang-'):
                return cls.split('-', 1)[1]
            if cls.startswith('highlight-source-'):
                return cls.replace('highlight-source-', '')
            _KNOWN_LANGS = {
                'python', 'java', 'cpp', 'c', 'javascript', 'js', 'html', 'css',
                'sql', 'bash', 'shell', 'sh', 'go', 'rust', 'ruby', 'php', 'swift',
                'kotlin', 'typescript', 'ts', 'json', 'xml', 'yaml', 'markdown',
                'csharp', 'cs', 'scala', 'r', 'matlab', 'perl', 'lua', 'dart',
                'objectivec', 'objc', 'groovy', 'powershell', 'dockerfile',
            }
            if cls.lower() in _KNOWN_LANGS:
                return cls.lower()
        return elem.get('data-lang', '') or elem.get('data-language', '') or ''

    def _list_md(self, elem: Tag, list_type: str, indent: int) -> str:
        lines = []
        prefix_base = '  ' * indent
        for idx, item in enumerate(elem.find_all('li', recursive=False), 1):
            prefix = f"{prefix_base}{idx}. " if list_type == 'ol' else f"{prefix_base}- "
            parts = []
            for child in item.children:
                if isinstance(child, Tag) and child.name in ('ul', 'ol'):
                    parts.append('\n' + self._list_md(child, child.name, indent + 1))
                else:
                    parts.append(self._elem_to_md(child, indent + 1))
            text = ''.join(parts).strip()
            sub_lines = text.split('\n')
            result = [prefix + sub_lines[0]]
            continuation_indent = '  ' * (indent + 1)
            for sl in sub_lines[1:]:
                result.append((continuation_indent + sl) if sl.strip() else '')
            lines.append('\n'.join(result))
        return '\n\n' + '\n'.join(lines) + '\n\n'

    def _table_md(self, table: Tag) -> str:
        rows = table.find_all('tr')
        if not rows:
            return ''
        all_rows = []
        for row in rows:
            cells = []
            for c in row.find_all(['th', 'td']):
                cell_text = c.get_text(strip=True).replace('|', '\\|').replace('\n', ' ')
                cells.append(cell_text)
            all_rows.append(cells)
        if not all_rows:
            return ''
        max_cols = max(len(r) for r in all_rows)
        for r in all_rows:
            r.extend([''] * (max_cols - len(r)))
        col_widths = [3] * max_cols
        for r in all_rows:
            for i, cell in enumerate(r):
                col_widths[i] = max(col_widths[i], len(cell))
        def fmt_row(cells):
            return '| ' + ' | '.join(c.ljust(col_widths[i]) for i, c in enumerate(cells)) + ' |'
        out = '\n\n' + fmt_row(all_rows[0]) + '\n'
        out += '| ' + ' | '.join('-' * col_widths[i] for i in range(max_cols)) + ' |\n'
        for row in all_rows[1:]:
            out += fmt_row(row) + '\n'
        return out + '\n'


# ==================== 菜鸟教程爬虫 ====================

class RunoobCrawler(BaseCrawler):
    """菜鸟教程爬虫 — 修复入口页丢失问题"""

    _SKIP = frozenset(('/try/', '/quiz/', '/compile/', '/dict/',
                       '/user/', '/login', '/register', '/sitemap',
                       '.zip', '.pdf', '.exe', '.dmg', '.apk',
                       'javascript:', 'mailto:', 'tel:', '/note/', '/download/'))

    def extract_tutorial_info(self, url: str) -> Tuple[str, List[Article]]:
        soup = self.fetch_soup(url)
        title = self._get_title(soup)
        articles: List[Article] = []
        seen: Set[str] = set()
        domain = urlparse(url).netloc

        # ★★★ 修复1: 先将入口页本身作为第一篇文章插入 ★★★
        entry_url = url.rstrip('/')
        seen.add(entry_url)

        # 获取入口页的标题（通常是"XXX 教程"）
        entry_title = title  # 使用页面标题（已经过滤了URL路径）

        # 如果title为空或标题仍然不理想，尝试从h1获取
        if not entry_title or len(entry_title) < 3:
            h1 = soup.find('h1')
            if h1:
                h1_text = h1.get_text(strip=True)
                # 检查h1内容是否是URL路径
                if h1_text and not h1_text.endswith('.html') and not h1_text.endswith('.htm'):
                    entry_title = h1_text

        # 如果h1为空或标题仍然不理想，尝试从content区域获取
        if not entry_title or len(entry_title) < 3:
            content = soup.find('div', id='content') or soup.find('div', class_='article-intro')
            if content:
                content_h1 = content.find('h1')
                if content_h1:
                    h1_text = content_h1.get_text(strip=True)
                    # 检查h1内容是否是URL路径
                    if h1_text and not h1_text.endswith('.html') and not h1_text.endswith('.htm'):
                        entry_title = h1_text
        
        # 清理菜鸟教程后缀
        entry_title = re.sub(r'\s*[-|_–—]?\s*菜鸟教程.*', '', entry_title).strip()
        
        # 如果标题为空，使用URL路径作为标题
        if not entry_title:
            path = urlparse(url).path
            entry_title = path.split('/')[-1] or "教程"
        
        # 确保标题不为空
        if not entry_title:
            entry_title = "教程"
            
        # 入口页作为第1章
        articles.append(Article(entry_title, entry_url, level=1))
        # 侧边栏
        sidebar = (soup.find('div', id='leftcolumn') or
                   soup.find('div', class_='design-left') or
                   soup.find('div', id='sidebar') or
                   soup.find('div', class_=re.compile(r'sidebar|left[-_]?col|menu', re.I)))
        if sidebar:
            self._walk_sidebar(sidebar, articles, seen, url, domain, 1)

        # 内容区域补充
        if len(articles) < 4:  # 改为4，因为第一篇已加入
            content = (soup.find('div', id='content') or
                       soup.find('div', class_='article-intro') or
                       soup.find('div', class_='article-body'))
            if content:
                self._extract_links(content, articles, seen, url, domain)

        # 嵌套页面展开
        articles = self._expand_nested(articles, seen, domain)

        # 兜底
        if len(articles) <= 1:
            for a in soup.find_all('a', href=True):
                self._try_add(a, articles, seen, url, domain)

        return title, articles

    def _expand_nested(self, articles: List[Article],
                       seen: Set[str], domain: str,
                       depth: int = 0) -> List[Article]:
        if depth > 3:
            return articles
        expanded = []
        for art in articles:
            expanded.append(art)
            try:
                soup = self.fetch_soup(art.url)
                content = (soup.find('div', id='content') or
                           soup.find('div', class_='article-intro'))
                if not content:
                    continue
                links = content.find_all('a', href=True)
                valid_links = []
                for link in links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    if (self._is_valid(href, art.url, domain, seen)
                            and text and 1 < len(text) < 100):
                        full = urljoin(art.url, href)
                        if full not in seen:
                            valid_links.append((text, full))
                            seen.add(full)
                if len(valid_links) >= 3:
                    sub_articles = []
                    for text, full in valid_links:
                        sub_articles.append(Article(text, full, level=art.level + 1))
                    sub_articles = self._expand_nested(sub_articles, seen, domain, depth + 1)
                    expanded.extend(sub_articles)
                time.sleep(0.15)
            except Exception:
                pass
        return expanded

    def _walk_sidebar(self, elem: Tag, arts: List[Article],
                      seen: Set[str], base: str, domain: str, level: int):
        if not elem or level > 6:
            return
        for child in elem.children:
            if not isinstance(child, Tag):
                continue
            if child.name == 'a':
                self._try_add(child, arts, seen, base, domain, level)
            elif child.name in ('div', 'ul', 'ol', 'li', 'nav', 'section', 'span', 'dd', 'dl', 'dt'):
                has_title = child.find(['h2', 'h3', 'h4', 'h5', 'strong', 'b'],
                                       recursive=False)
                self._walk_sidebar(child, arts, seen, base, domain,
                                   level + 1 if has_title else level)

    def _extract_links(self, content: Tag, arts: List[Article],
                       seen: Set[str], base: str, domain: str):
        for a in content.find_all('a', href=True):
            self._try_add(a, arts, seen, base, domain)

    def _try_add(self, a: Tag, arts: List[Article], seen: Set[str],
                 base: str, domain: str, level: int = 1):
        href = a.get('href', '')
        if not self._is_valid(href, base, domain, seen):
            return
        full = urljoin(base, href).rstrip('/')
        if full in seen:
            return
        t = a.get_text(strip=True)
        if t and 1 < len(t) < 100:
            arts.append(Article(t, full, level=level))
            seen.add(full)

    def _is_valid(self, href: str, base: str, domain: str, seen: Set[str]) -> bool:
        if not href or href.startswith('#') or href.startswith('javascript'):
            return False
        full = urljoin(base, href).rstrip('/')
        if full in seen:
            return False
        parsed = urlparse(full)
        if parsed.netloc and parsed.netloc != domain:
            return False
        lower = href.lower()
        return not any(p in lower for p in self._SKIP)

    @staticmethod
    def _get_title(soup: BeautifulSoup) -> str:
        # 优先从title标签获取
        title_tag = soup.find('title')
        if title_tag:
            t = title_tag.get_text(strip=True)
            # 清理菜鸟教程后缀
            t = re.sub(r'\s*[-|_–—]?\s*菜鸟教程.*', '', t).strip()
            # 如果标题不是URL路径，直接返回
            if t and not t.endswith('.html') and not t.endswith('.htm'):
                return t

        # 从h1标签获取
        h1_tag = soup.find('h1')
        if h1_tag:
            t = h1_tag.get_text(strip=True)
            # 清理菜鸟教程后缀
            t = re.sub(r'\s*[-|_–—]?\s*菜鸟教程.*', '', t).strip()
            # 如果标题不是URL路径，直接返回
            if t and not t.endswith('.html') and not t.endswith('.htm'):
                return t

        # 尝试从content区域获取
        content = soup.find('div', id='content') or soup.find('div', class_='article-intro')
        if content:
            content_h1 = content.find('h1')
            if content_h1:
                t = content_h1.get_text(strip=True)
                # 清理菜鸟教程后缀
                t = re.sub(r'\s*[-|_–—]?\s*菜鸟教程.*', '', t).strip()
                # 如果标题不是URL路径，直接返回
                if t and not t.endswith('.html') and not t.endswith('.htm'):
                    return t

        # 都没有找到，返回默认值
        return "未知教程"

    def extract_article_content(self, article: Article,
                                download_images: bool, img_dir: str):
        try:
            soup = self.fetch_soup(article.url)
            content = (soup.find('div', id='content') or
                       soup.find('div', class_='article-intro') or
                       soup.find('div', class_='article-body') or
                       soup.find('article') or
                       soup.find('div', class_=re.compile(r'content|article', re.I)))
            if not content:
                article.content = "*内容获取失败*"
                article.html_content = "<p><em>内容获取失败</em></p>"
                return
            self.process_content(content, article, download_images, img_dir)
        except Exception as e:
            article.content = f"*提取失败: {e}*"
            article.html_content = f"<p><em>提取失败: {e}</em></p>"

    def _extra_clean(self, content: Tag, article: Article):
        for tag in content.find_all(class_=re.compile(
                r'example_code_btn|tryit_btn|w3-b|color_h|shareit', re.I)):
            tag.decompose()
        for tag in content.find_all(class_=re.compile(r'breadcrumb|crumb', re.I)):
            tag.decompose()


# ==================== CSDN爬虫 ====================

class CSDNCrawler(BaseCrawler):
    """CSDN爬虫 — 加强反爬、列表页、内容提取"""

    _NOISE_CLASSES = re.compile(
        r'hljs-button|signin|hide-article-box|blog-tags-box|recommend-box'
        r'|recommend-item-box|tool-box|more-toolbox|csdn-side-toolbar'
        r'|article-copyright|first-recommend-box|template-box'
        r'|blog-content-box|operating|toolbar-advert|article-info-box'
        r'|follow-nickName-box|toc-article|side-toolbar|passport-login-tip',
        re.I
    )

    _LIST_PATTERNS = (
        r'/column/', r'/category_', r'/article/list/',
        r'type=blog', r'\?type=', r'/blog$',
    )

    def __init__(self):
        super().__init__()
        self.headers.update({
            'Referer': 'https://blog.csdn.net/',
            'Cookie': 'dc_session_id=10_' + hashlib.md5(
                str(time.time()).encode()).hexdigest(),
        })

    def is_list_page(self, url: str) -> bool:
        if re.match(r'^https?://blog\.csdn\.net/[^/]+/?$', url):
            return True
        if re.match(r'^https?://i-blog\.csdnimg\.cn', url):
            return False
        return any(re.search(p, url, re.I) for p in self._LIST_PATTERNS)

    def extract_column_articles(self, url: str) -> List[Article]:
        articles: List[Article] = []
        seen: Set[str] = set()
        url = url.rstrip('/')
        if '/column/' in url:
            api_arts = self._try_column_api(url, seen)
            if api_arts:
                return api_arts
        for page in range(1, 21):
            try:
                page_url = self._page_url(url, page)
                resp = self.fetch(page_url)
                if resp.status_code != 200:
                    break
                soup = BeautifulSoup(resp.text, 'html.parser')
                batch = self._page_articles(soup, seen)
                if not batch:
                    break
                articles.extend(batch)
                if not self._has_next(soup, page + 1):
                    break
                time.sleep(0.8)
            except Exception:
                break
        return articles

    def _try_column_api(self, url: str, seen: Set[str]) -> List[Article]:
        m = re.search(r'/column/details/(\d+)', url)
        if not m:
            return []
        column_id = m.group(1)
        articles = []
        for page in range(1, 51):
            try:
                api_url = (f'https://blog.csdn.net/community/home-api/v1/'
                           f'get-business-list?page={page}&size=20'
                           f'&businessType=blog&orderby=&no498=false'
                           f'&year=&month=&username=&columnId={column_id}')
                resp = self.fetch(api_url)
                data = resp.json()
                items = data.get('data', {}).get('list', [])
                if not items:
                    break
                for item in items:
                    href = item.get('url', '')
                    title = item.get('title', '')
                    if href and title and href not in seen:
                        articles.append(Article(title, href))
                        seen.add(href)
                time.sleep(0.5)
            except Exception:
                break
        return articles

    def _page_url(self, base: str, page: int) -> str:
        if page == 1:
            return base
        if '/column/' in base:
            return f"{base}/{page}"
        if '/article/list/' in base:
            return re.sub(r'/article/list/\d+', f'/article/list/{page}', base)
        if re.match(r'^https?://blog\.csdn\.net/[^/]+/?$', base):
            return f"{base.rstrip('/')}/article/list/{page}"
        sep = '&' if '?' in base else '?'
        return f"{base}{sep}page={page}"

    @staticmethod
    def _has_next(soup: BeautifulSoup, nxt: int) -> bool:
        pager = soup.find(class_=re.compile(r'pag', re.I))
        if not pager:
            return False
        if pager.find('a', string=re.compile(r'下一页|Next|>', re.I)):
            return True
        return any(str(nxt) == a.get_text(strip=True)
                   for a in pager.find_all('a', href=True))

    def _page_articles(self, soup: BeautifulSoup, seen: Set[str]) -> List[Article]:
        arts: List[Article] = []
        for tag, attrs in [
            ('div', {'class': re.compile(r'column_article|article[-_]?list', re.I)}),
            ('div', {'class': re.compile(r'blog[-_]?item|article[-_]?item', re.I)}),
            ('ul', {'class': re.compile(r'column[-_]?article', re.I)}),
            ('article', {}),
        ]:
            items = soup.find_all(tag, attrs)
            if items:
                for item in items:
                    for link in item.find_all('a', href=re.compile(r'/article/details/')):
                        self._add_link(link, arts, seen)
                if arts:
                    return arts
        for link in soup.find_all('a', href=re.compile(r'/article/details/')):
            self._add_link(link, arts, seen)
        for elem in soup.find_all(attrs={'data-articleid': True}):
            article_id = elem.get('data-articleid')
            if article_id:
                href = f"https://blog.csdn.net/article/details/{article_id}"
                title_elem = elem.find(['h2', 'h3', 'h4', 'a'])
                title = title_elem.get_text(strip=True) if title_elem else f"文章{article_id}"
                if href not in seen and title:
                    arts.append(Article(title, href))
                    seen.add(href)
        return arts

    @staticmethod
    def _add_link(a: Tag, arts: List[Article], seen: Set[str]):
        href = a.get('href', '')
        if not href:
            return
        if not href.startswith('http'):
            href = urljoin('https://blog.csdn.net', href)
        href = href.split('?')[0].split('#')[0]
        if href in seen or '/article/details/' not in href:
            return
        title = re.sub(r'\s+', ' ', a.get_text(strip=True)).strip()
        if title and len(title) > 2:
            arts.append(Article(title, href))
            seen.add(href)

    def extract_article_content(self, article: Article,
                                download_images: bool, img_dir: str):
        try:
            soup = self.fetch_soup(article.url)
            self._fill_meta(soup, article)
            content = None
            for sel in [
                ('div', {'id': 'content_views'}),
                ('div', {'id': 'article_content'}),
                ('div', {'class': 'article_content'}),
                ('div', {'class': re.compile(r'markdown_views', re.I)}),
                ('div', {'class': re.compile(r'htmledit_views', re.I)}),
                ('article', {}),
            ]:
                content = soup.find(sel[0], sel[1])
                if content:
                    break
            if not content:
                article.content = "*内容获取失败*"
                article.html_content = "<p><em>内容获取失败</em></p>"
                return
            self.process_content(content, article, download_images, img_dir)
        except Exception as e:
            article.content = f"*提取失败: {e}*"
            article.html_content = f"<p><em>提取失败: {e}</em></p>"

    def _fill_meta(self, soup: BeautifulSoup, article: Article):
        if not article.title or article.title == "未命名":
            for s in [('h1', {'class': 'title-article'}),
                      ('h1', {'id': 'articleContentId'}),
                      ('span', {'class': 'title-article'}), ('h1', {})]:
                t = soup.find(s[0], s[1])
                if t:
                    article.title = t.get_text(strip=True)
                    break
        if not article.author:
            t = (soup.find('a', class_='follow-nickName') or
                 soup.find('a', class_=re.compile(r'user[-_]?name', re.I)) or
                 soup.find('div', class_='article-info-box'))
            if t:
                a_tag = t.find('a') if t.name == 'div' else t
                if a_tag:
                    article.author = a_tag.get_text(strip=True)
        if not article.date:
            t = (soup.find('span', class_='time') or
                 soup.find('span', class_=re.compile(r'date|time|publish', re.I)))
            if t:
                article.date = t.get_text(strip=True)

    def _extra_clean(self, content: Tag, article: Article):
        for tag in content.find_all(class_=self._NOISE_CLASSES):
            tag.decompose()
        for tag in content.find_all('svg'):
            tag.decompose()
        for tag in content.find_all('button'):
            tag.decompose()
        for noise in ('版权声明', '个人博客导航', '本文为', '禁止转载'):
            for s in content.find_all(string=lambda t: t and noise in t):
                p = s.parent
                if p and p.name in ('div', 'p', 'span') and len(p.get_text(strip=True)) < 150:
                    p.decompose()
        for img in content.find_all('img'):
            src = img.get('src', '')
            if 'csdnimg.cn' in src and '#' in src:
                img['src'] = src.split('#')[0]


# ==================== GitBook爬虫 ====================

class GitBookCrawler(BaseCrawler):
    """GitBook文档爬虫"""

    def extract_gitbook_info(self, url: str) -> Tuple[str, List[Article]]:
        soup = self.fetch_soup(url)
        title_tag = soup.find('h1') or soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else "GitBook文档"
        articles: List[Article] = []
        nav = None
        for tag, attrs in [
            ('nav', {'class': re.compile(r'book-summary|navigation|sidebar', re.I)}),
            ('div', {'class': re.compile(r'toc|summary|navigation|sidebar', re.I)}),
            ('aside', {}),
        ]:
            nav = soup.find(tag, attrs)
            if nav:
                break
        seen: Set[str] = set()
        if nav:
            self._parse_nav(nav, articles, seen, url, 1)
        if not articles:
            summary_url = urljoin(url, 'SUMMARY.md')
            try:
                resp = self.fetch(summary_url)
                if resp.status_code == 200:
                    for m in re.finditer(r'\[([^\]]+)\]\(([^\)]+)\)', resp.text):

                        link_text, link_href = m.group(1), m.group(2)
                        full = urljoin(url, link_href)
                        if full not in seen:
                            articles.append(Article(link_text, full))
                            seen.add(full)
            except Exception:
                pass
        if not articles:
            articles.append(Article(title, url))
        return title, articles

    def _parse_nav(self, nav: Tag, articles: List[Article],
                   seen: Set[str], base_url: str, level: int):
        for child in nav.children:
            if not isinstance(child, Tag):
                continue
            if child.name == 'a':
                href = child.get('href', '')
                if not href or href.startswith('#') or href.startswith('javascript'):
                    continue
                if href.startswith('http') and urlparse(href).netloc != urlparse(base_url).netloc:
                    continue
                full = urljoin(base_url, href)
                t = child.get_text(strip=True)
                if t and len(t) > 1 and full not in seen:
                    articles.append(Article(t, full, level=level))
                    seen.add(full)
            elif child.name in ('ul', 'ol', 'li', 'div', 'nav', 'section'):
                title_tag = child.find(['h2', 'h3', 'h4', 'h5', 'strong', 'b', 'span'],
                                       recursive=False)
                sub_level = level + 1 if title_tag else level
                self._parse_nav(child, articles, seen, base_url, sub_level)

    def extract_article_content(self, article: Article,
                                download_images: bool, img_dir: str):
        try:
            soup = self.fetch_soup(article.url)
            content = None
            for sel in [
                ('div', {'class': re.compile(
                    r'page-wrapper|markdown-section|book-body|page-inner', re.I)}),
                ('main', {}), ('article', {}), ('div', {'class': 'content'}),
                ('div', {'role': 'main'}),
            ]:
                content = soup.find(sel[0], sel[1])
                if content:
                    break
            if not content:
                article.content = "*内容获取失败*"
                article.html_content = "<p><em>内容获取失败</em></p>"
                return
            for tag in content.find_all(class_=re.compile(
                    r'navigation|sidebar|toc-menu|book-header', re.I)):
                tag.decompose()
            self.process_content(content, article, download_images, img_dir)
        except Exception as e:
            article.content = f"*提取失败: {e}*"
            article.html_content = f"<p><em>提取失败: {e}</em></p>"


# ==================== 输出生成器 ====================

class BookGenerator:
    """GitBook风格的专业书籍生成器"""

    def __init__(self, output_dir: str, progress_callback=None):
        self.output_dir = output_dir
        self.progress = progress_callback or (lambda msg: None)

    @staticmethod
    def _assign_anchors(articles: List[Article]):
        used = set()
        for i, art in enumerate(articles, 1):
            base = _make_anchor(art.title, i)
            anchor = base
            counter = 2
            while anchor in used:
                anchor = f"{base}-{counter}"
                counter += 1
            art.anchor = anchor
            used.add(anchor)

    @staticmethod
    def _build_toc_tree(articles: List[Article]) -> List[dict]:
        tree = []
        for art in articles:
            tree.append({
                'article': art,
                'level': art.level,
            })
        return tree

    def gen_markdown(self, path: str, title: str, articles: List[Article], author: str):
        self._assign_anchors(articles)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write(f"> **作者**: {author}  \n")
            f.write(f"> **生成时间**: {now}  \n")
            f.write(f"> **共 {len(articles)} 章节**\n\n")
            f.write("---\n\n")
            if len(articles) > 1:
                f.write("## 📑 目录\n\n")
                # 构建序号映射
                chapter_numbers = {}
                current_chapter = 0
                for i, art in enumerate(articles, 1):
                    if art.level == 1:
                        current_chapter += 1
                        chapter_numbers[i] = str(current_chapter)
                    else:
                        # 子章节使用父章节序号 + .x
                        parent_idx = i - 1
                        while parent_idx > 0 and articles[parent_idx - 1].level >= art.level:
                            parent_idx -= 1
                        if parent_idx > 0:
                            parent_num = chapter_numbers.get(parent_idx, str(parent_idx))
                            sub_num = str(i - parent_idx)
                            chapter_numbers[i] = f"{parent_num}.{sub_num}"
                        else:
                            chapter_numbers[i] = str(i)

                for i, art in enumerate(articles, 1):
                    indent = "  " * (art.level - 1)
                    anchor = art.anchor
                    num = chapter_numbers.get(i, str(i))
                    f.write(f"{indent}{num}. [{art.title}](#{anchor})\n")
                f.write("\n---\n\n")
            for i, art in enumerate(articles, 1):
                level_prefix = '#' * min(art.level + 1, 6)
                heading = f"{level_prefix} {i}. {art.title}" if len(articles) > 1 else f"## {art.title}"
                f.write(f'<a id="{art.anchor}"></a>\n\n')
                f.write(f"{heading}\n\n")
                meta = []
                if art.author:
                    meta.append(f"**作者**: {art.author}")
                if art.date:
                    meta.append(f"**日期**: {art.date}")
                if art.url:
                    meta.append(f"[🔗 原文链接]({art.url})")
                if meta:
                    f.write("> " + " | ".join(meta) + "\n\n")
                f.write(art.content + "\n\n")
                if i < len(articles):
                    f.write("---\n\n")
            f.write(f"\n---\n\n*本文档由 Web Content Extractor Pro v11.1 自动生成 | {now}*\n")
        self.progress(f"✅ Markdown: {os.path.basename(path)}")

    def gen_html(self, path: str, title: str, articles: List[Article], platform: str):
        self._assign_anchors(articles)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if len(articles) > 1:
            # 构建序号映射
            chapter_numbers = {}
            current_chapter = 0
            for i, art in enumerate(articles, 1):
                if art.level == 1:
                    current_chapter += 1
                    chapter_numbers[i] = str(current_chapter)
                else:
                    # 子章节使用父章节序号 + .x
                    parent_idx = i - 1
                    while parent_idx > 0 and articles[parent_idx - 1].level >= art.level:
                        parent_idx -= 1
                    if parent_idx > 0:
                        parent_num = chapter_numbers.get(parent_idx, str(parent_idx))
                        sub_num = str(i - parent_idx)
                        chapter_numbers[i] = f"{parent_num}.{sub_num}"
                    else:
                        chapter_numbers[i] = str(i)

            toc_items = []
            for i, a in enumerate(articles, 1):
                indent_class = f' style="padding-left:{(a.level - 1) * 15}px"' if a.level > 1 else ''
                display_title = a.title[:50] + ('...' if len(a.title) > 50 else '')
                num = chapter_numbers.get(i, str(i))
                toc_items.append(
                    f'<li{indent_class}><a href="#{a.anchor}">'
                    f'<span class="toc-num">{num}.</span> {display_title}</a></li>')
            toc = f'<ul class="sidebar-content">{"".join(toc_items)}</ul>'
        else:
            toc = '<p style="color:#999;font-size:.9em">单篇文章</p>'
        parts = []
        for i, a in enumerate(articles, 1):
            meta = []
            if a.url:
                meta.append(f'<a href="{a.url}" target="_blank">🔗 原文</a>')
            if a.author:
                meta.append(f'✍️ {a.author}')
            if a.date:
                meta.append(f'📅 {a.date}')
            meta_html = (f'<div class="article-meta">{" | ".join(meta)}</div>'
                         if meta else '')
            parts.append(
                f'<div class="article" id="{a.anchor}">'
                f'<h2>{i}. {a.title}</h2>{meta_html}{a.html_content}</div>')
        html = _HTML_TEMPLATE.format(
            title=title, platform=platform, time=now,
            count=len(articles), toc=toc, articles=''.join(parts))
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        self.progress(f"✅ HTML: {os.path.basename(path)}")

    def gen_pdf(self, path: str, title: str, articles: List[Article], platform: str):
        if not WEASY_AVAILABLE:
            self.progress("⚠️ WeasyPrint 未安装，跳过PDF")
            return
        try:
            self._assign_anchors(articles)
            abs_dir = os.path.abspath(self.output_dir)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 构建序号映射
            chapter_numbers = {}
            current_chapter = 0
            for i, art in enumerate(articles, 1):
                if art.level == 1:
                    current_chapter += 1
                    chapter_numbers[i] = str(current_chapter)
                else:
                    # 子章节使用父章节序号 + .x
                    parent_idx = i - 1
                    while parent_idx > 0 and articles[parent_idx - 1].level >= art.level:
                        parent_idx -= 1
                    if parent_idx > 0:
                        parent_num = chapter_numbers.get(parent_idx, str(parent_idx))
                        sub_num = str(i - parent_idx)
                        chapter_numbers[i] = f"{parent_num}.{sub_num}"
                    else:
                        chapter_numbers[i] = str(i)

            toc_entries = []
            for i, a in enumerate(articles, 1):
                indent_style = f' style="padding-left:{(a.level - 1) * 20}px"' if a.level > 1 else ''
                num = chapter_numbers.get(i, str(i))
                toc_entries.append(
                    f'<div class="toc-entry"{indent_style}>'
                    f'<a href="#{a.anchor}">'
                    f'<span class="toc-number">{num}.</span>'
                    f'<span class="toc-title">{a.title[:60]}</span>'
                    f'</a></div>')
            arts_html = []
            for i, a in enumerate(articles, 1):
                meta = []
                if a.author:
                    meta.append(f'作者: {a.author}')
                if a.date:
                    meta.append(f'日期: {a.date}')
                if a.url:
                    meta.append(f'<a href="{a.url}">查看原文</a>')
                meta_html = (f'<div class="article-meta">{" | ".join(meta)}</div>'
                             if meta else '')
                content_html = a.html_content
                content_html = self._fix_img_paths(content_html, abs_dir)
                arts_html.append(
                    f'<div class="article" id="{a.anchor}">'
                    f'<h2>{i}. {a.title}</h2>'
                    f'{meta_html}{content_html}</div>')

            pdf_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{title}</title>
</head>
<body data-date="{now}">
<div class="cover">
  <div class="cover-decoration"></div>
  <h1>{title}</h1>
  <div class="cover-line"></div>
  <div class="meta">
    <p><strong>来源</strong>: {platform}</p>
    <p><strong>生成日期</strong>: {now}</p>
    <p><strong>共 {len(articles)} 章节</strong></p>
  </div>
</div>
<div class="toc">
  <h2>目 录</h2>
  {''.join(toc_entries)}
</div>
{''.join(arts_html)}
<div class="timestamp">Generated by Web Content Extractor Pro v11.1</div>
</body>
</html>"""

            with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False,
                                              encoding='utf-8') as tmp:
                tmp.write(pdf_html)
                tmp_path = tmp.name
            font_config = FontConfiguration()
            WeasyHTML(filename=tmp_path).write_pdf(
                path, stylesheets=[CSS(string=_PDF_CSS)],
                font_config=font_config)
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            self.progress(f"✅ PDF: {os.path.basename(path)}")
        except Exception as e:
            self.progress(f"⚠️ PDF生成失败: {e}")

    @staticmethod
    def _fix_img_paths(html_content: str, abs_dir: str) -> str:
        def _replace(m):
            src = m.group(1)
            if src.startswith(('http://', 'https://', 'file://', 'data:')):
                return m.group(0)
            abs_path = os.path.normpath(os.path.join(abs_dir, src))
            if os.path.exists(abs_path):
                uri = Path(abs_path).as_uri()
                return f'src="{uri}"'
            return m.group(0)
        return re.sub(r'src="([^"]*)"', _replace, html_content)


# ==================== 模板 ====================

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans",sans-serif,"Microsoft YaHei";line-height:1.8;color:#333;background:#fff}}
.wrapper{{display:flex;min-height:100vh}}
.sidebar{{width:280px;background:#fafafa;border-right:1px solid #e8e8e8;padding:30px 15px;position:fixed;left:0;top:0;height:100vh;overflow-y:auto;font-size:.9em;z-index:100}}
.sidebar h3{{margin-bottom:20px;color:#2c3e50;font-size:1.1em;border-bottom:2px solid #4a90d9;padding-bottom:10px;font-weight:600}}
.sidebar-content{{list-style:none;padding:0}}
.sidebar-content li{{margin:4px 0}}
.sidebar-content a{{color:#555;text-decoration:none;display:block;padding:6px 10px;border-radius:4px;transition:all .2s;font-size:.92em;line-height:1.4}}
.sidebar-content a:hover{{background:#e8f0fe;color:#1a73e8;padding-left:15px}}
.sidebar-content .toc-num{{color:#999;margin-right:5px;font-size:.85em}}
.container{{margin-left:280px;flex:1;padding:40px 60px;max-width:960px}}
.header{{background:linear-gradient(135deg,#4a90d9,#7b68ee);color:#fff;padding:60px 40px;margin:-40px -60px 40px;border-radius:0 0 8px 8px}}
.header h1{{font-size:2.5em;margin-bottom:15px;font-weight:700}}
.metadata{{display:flex;gap:30px;margin-top:15px;font-size:.95em;opacity:.9}}
.meta-item{{display:flex;align-items:center;gap:8px}}
h2{{font-size:1.8em;color:#2c3e50;margin:50px 0 20px;padding-left:15px;border-left:4px solid #4a90d9;padding-bottom:8px;font-weight:600}}
h3{{font-size:1.4em;color:#444;margin:35px 0 12px;font-weight:600}}
h4{{font-size:1.2em;color:#555;margin:25px 0 8px;font-weight:600}}
h5,h6{{font-size:1.05em;color:#666;margin:20px 0 8px}}
.article{{margin-bottom:50px;padding-bottom:30px;border-bottom:1px solid #eee}}
.article:last-child{{border-bottom:none}}
.article-meta{{color:#7f8c8d;font-size:.88em;margin-bottom:20px;padding:12px 15px;background:#f8f9fa;border-radius:4px;border-left:3px solid #4a90d9}}
.article-meta a{{color:#4a90d9;text-decoration:none}}
p{{margin:12px 0;text-align:justify;font-size:1.02em;line-height:1.85}}
img{{max-width:100%;height:auto;display:block;margin:20px auto;border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,.1);border:1px solid #e8e8e8}}
pre{{background:#1e1e1e;color:#d4d4d4;padding:18px 20px;border-radius:6px;overflow-x:auto;margin:18px 0;font-family:"Fira Code",Consolas,Monaco,"Courier New",monospace;font-size:.88em;line-height:1.55;border:1px solid #333}}
code{{font-family:"Fira Code",Consolas,monospace;background:#f5f5f5;padding:2px 5px;border-radius:3px;font-size:.9em;color:#e83e8c}}
pre code{{background:none;padding:0;color:inherit;font-size:inherit}}
blockquote{{border-left:4px solid #4a90d9;padding:12px 20px;margin:18px 0;color:#555;background:#f8f9fa;border-radius:0 4px 4px 0}}
.math-inline{{display:inline;margin:0 2px}}
.math-display{{display:block;margin:20px 0;text-align:center;overflow-x:auto;padding:18px;background:#f8f9fa;border-radius:6px;border:1px solid #e8e8e8}}
table{{width:100%;border-collapse:collapse;margin:18px 0;font-size:.95em}}
table th{{background:#4a90d9;color:#fff;padding:10px 12px;text-align:left;font-weight:600}}
table td{{padding:9px 12px;border-bottom:1px solid #e8e8e8}}
table tr:nth-child(even){{background:#f8f9fa}}
table tr:hover{{background:#e8f0fe}}
a{{color:#4a90d9;text-decoration:none}}
a:hover{{color:#2563eb;text-decoration:underline}}
ul,ol{{margin:12px 0;padding-left:28px}}
li{{margin:6px 0;line-height:1.7}}
hr{{border:none;border-top:1px solid #e8e8e8;margin:30px 0}}
.timestamp{{text-align:center;color:#aaa;font-size:.85em;margin-top:40px;padding-top:20px;border-top:1px solid #eee}}
@media(max-width:768px){{
  .wrapper{{flex-direction:column}}
  .sidebar{{position:static;width:100%;height:auto;border-right:none;border-bottom:1px solid #e8e8e8;padding:15px}}
  .container{{margin-left:0;padding:20px}}
  .header{{margin:-20px -20px 20px;padding:30px 20px}}
  h1{{font-size:1.8em}}h2{{font-size:1.4em}}
}}
</style>
<script>
window.MathJax={{
  tex:{{
    inlineMath:[['$','$']],
    displayMath:[['$$','$$']],
    processEscapes:true,
    processEnvironments:true,
    tags:'ams'
  }},
  options:{{
    skipHtmlTags:['script','noscript','style','textarea','pre','code'],
    ignoreHtmlClass:'tex2jax_ignore'
  }},
  svg:{{fontCache:'global'}}
}};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js" async></script>
</head>
<body>
<div class="wrapper">
<div class="sidebar"><h3>📑 目录</h3>{toc}</div>
<div class="container">
<div class="header"><h1>{title}</h1>
<div class="metadata">
<div class="meta-item"><span>📚</span><span><strong>平台</strong>: {platform}</span></div>
<div class="meta-item"><span>⏰</span><span><strong>生成</strong>: {time}</span></div>
<div class="meta-item"><span>📄</span><span><strong>章节</strong>: {count}</span></div>
</div></div>
{articles}
<div class="timestamp">Generated by Web Content Extractor Pro v11.1</div>
</div></div>
</body></html>"""

# ★★★ 修复3: GitBook专业书籍风格PDF样式 ★★★
_PDF_CSS = """
/* ========== 页面基础设置 ========== */
@page {
    size: A4;
    margin: 2.5cm 2cm 2cm 2cm;

    @top-center {
        content: string(chapter-title);
        font-size: 9pt;
        color: #666;
        font-family: "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
        font-weight: 500;
        letter-spacing: 0.5px;
    }

    @bottom-center {
        content: counter(page);
        font-size: 9pt;
        color: #666;
        font-family: "Microsoft YaHei", sans-serif;
    }

    @bottom-left {
        content: "Web Content Extractor Pro";
        font-size: 8pt;
        color: #999;
        font-family: "Microsoft YaHei", sans-serif;
    }

    @bottom-right {
        content: attr(data-date);
        font-size: 8pt;
        color: #999;
        font-family: "Microsoft YaHei", sans-serif;
    }
}

@page:first {
    margin: 0;
    @top-center { content: none; }
    @bottom-center { content: none; }
    @bottom-left { content: none; }
    @bottom-right { content: none; }
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial,
                 "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji",
                 "Segoe UI Symbol", "Noto Color Emoji";
    font-size: 11pt;
    line-height: 1.8;
    color: #34495e;
    text-rendering: optimizeLegibility;
    -webkit-font-smoothing: antialiased;
}

/* ========== GitBook风格封面 ========== */
.cover {
    page-break-after: always;
    text-align: center;
    padding: 0;
    position: relative;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    min-height: 900px;
}

.cover::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></svg>') repeat;
    background-size: 200px;
    opacity: 0.3;
    z-index: 0;
}

.cover-decoration {
    width: 120px;
    height: 4px;
    background: rgba(255,255,255,0.8);
    margin: 150px auto 0;
    border-radius: 2px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    position: relative;
    z-index: 1;
}

.cover h1 {
    font-size: 38pt;
    margin: 50px 60px 40px;
    font-weight: 800;
    letter-spacing: 2px;
    line-height: 1.3;
    text-shadow: 0 4px 12px rgba(0,0,0,0.3);
    position: relative;
    z-index: 1;
}

.cover-line {
    width: 180px;
    height: 3px;
    background: rgba(255,255,255,0.8);
    margin: 30px auto 40px;
    border-radius: 2px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    position: relative;
    z-index: 1;
}

.cover .meta {
    font-size: 12pt;
    margin: 20px 0 150px;
    line-height: 2.4;
    opacity: 0.95;
    position: relative;
    z-index: 1;
}

.cover .meta p {
    margin: 8px 0;
    font-weight: 400;
    letter-spacing: 1px;
    text-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.cover .meta strong {
    font-weight: 600;
    opacity: 0.9;
}

/* ========== GitBook风格目录 ========== */
.toc {
    page-break-after: always;
    padding: 60px 40px;
}

.toc h2 {
    text-align: center;
    font-size: 24pt;
    margin-bottom: 40px;
    color: #2c3e50;
    font-weight: 700;
    letter-spacing: 3px;
    padding-bottom: 20px;
    border-bottom: 2px solid #3498db;
}

.toc-entry {
    margin: 0;
    font-size: 11pt;
    padding: 12px 8px;
    border-bottom: 1px solid #ecf0f1;
    line-height: 1.6;
    transition: all 0.2s;
}

.toc-entry:last-child {
    border-bottom: none;
}

.toc-entry a {
    color: #34495e;
    text-decoration: none;
    display: flex;
    align-items: baseline;
}

.toc-number {
    font-weight: 600;
    color: #3498db;
    min-width: 40px;
    font-size: 11pt;
}

.toc-title {
    flex: 1;
    margin: 0 10px;
}

/* ========== GitBook风格标题层级 ========== */
h1, h2, h3, h4, h5, h6 {
    page-break-after: avoid;
    orphans: 4;
    widows: 3;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial,
                 "Noto Sans", sans-serif;
    line-height: 1.4;
}

h1 {
    font-size: 24pt;
    margin: 40px 0 25px;
    border-bottom: 2px solid #3498db;
    padding-bottom: 15px;
    color: #2c3e50;
    font-weight: 700;
    letter-spacing: 0.5px;
}

h2 {
    font-size: 18pt;
    margin: 35px 0 20px;
    padding-left: 15px;
    border-left: 4px solid #3498db;
    color: #34495e;
    font-weight: 600;
    string-set: chapter-title content();
}

h3 {
    font-size: 15pt;
    margin: 28px 0 15px;
    color: #34495e;
    font-weight: 600;
    border-bottom: 1px solid #ecf0f1;
    padding-bottom: 8px;
}

h4 {
    font-size: 13pt;
    margin: 22px 0 12px;
    color: #5d6d7e;
    font-weight: 600;
}

h5, h6 {
    font-size: 11pt;
    margin: 18px 0 10px;
    color: #5d6d7e;
    font-weight: 600;
}

/* ========== GitBook风格正文排版 ========== */
p {
    margin: 12px 0;
    text-align: justify;
    orphans: 3;
    widows: 3;
    text-indent: 0;
    hyphens: auto;
    line-height: 1.8;
}

img {
    max-width: 95%;
    height: auto;
    display: block;
    margin: 20px auto;
    page-break-inside: avoid;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

/* ========== GitBook风格代码块 ========== */
pre {
    font-size: 9pt;
    page-break-inside: avoid;
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-left: 4px solid #3498db;
    border-radius: 4px;
    padding: 14px 16px;
    margin: 16px 0;
    overflow: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: "Fira Code", "Source Code Pro", "Courier New", "Consolas", monospace;
    line-height: 1.6;
    color: #2c3e50;
}

code {
    font-family: "Fira Code", "Source Code Pro", "Courier New", monospace;
    font-size: 9pt;
    background: #f8f9fa;
    padding: 2px 5px;
    border-radius: 3px;
    color: #e74c3c;
    border: 1px solid #e9ecef;
}

pre code {
    background: none;
    padding: 0;
    border: none;
    color: inherit;
    font-size: inherit;
}

/* ========== GitBook风格引用块 ========== */
blockquote {
    page-break-inside: avoid;
    border-left: 4px solid #3498db;
    margin: 16px 0;
    padding: 12px 20px;
    background: #f8f9fa;
    color: #5d6d7e;
    border-radius: 0 4px 4px 0;
    font-style: italic;
}

blockquote p {
    font-style: italic;
    line-height: 1.7;
}

/* ========== GitBook风格公式 ========== */
.math-inline {
    font-family: "Times New Roman", "STIX Two Math", "Latin Modern Math", serif;
    font-style: italic;
}

.math-display {
    display: block;
    margin: 16px 0;
    text-align: center;
    padding: 14px 18px;
    background: #f8f9fa;
    border-left: 3px solid #3498db;
    page-break-inside: avoid;
    font-family: "Times New Roman", "STIX Two Math", "Latin Modern Math", serif;
    font-style: italic;
    font-size: 12pt;
    border-radius: 0 4px 4px 0;
}

/* ========== GitBook风格表格 ========== */
table {
    page-break-inside: avoid;
    border-collapse: collapse;
    width: 100%;
    margin: 16px 0;
    font-size: 10pt;
    border-radius: 4px;
    overflow: hidden;
}

table th {
    background: #3498db;
    color: #fff;
    padding: 10px 12px;
    text-align: left;
    font-weight: 600;
    font-size: 10pt;
}

table td {
    padding: 9px 12px;
    border-bottom: 1px solid #ecf0f1;
    vertical-align: top;
}

table tr:nth-child(even) {
    background: #f8f9fa;
}

table tr:hover {
    background: #e8f4f8;
}

table tr:last-child td {
    border-bottom: none;
}

/* ========== GitBook风格文章分章 ========== */
.article {
    page-break-before: always;
    orphans: 4;
    widows: 3;
    margin-top: 20px;
}

.article:first-child {
    page-break-before: avoid;
}

.article-meta {
    background: #f8f9fa;
    padding: 10px 16px;
    margin: 16px 0;
    font-size: 9pt;
    border-left: 3px solid #3498db;
    page-break-inside: avoid;
    color: #5d6d7e;
    border-radius: 0 4px 4px 0;
}

/* ========== GitBook风格列表 ========== */
ul, ol {
    margin: 12px 0;
    padding-left: 28px;
}

li {
    margin: 6px 0;
    line-height: 1.8;
}

/* ========== GitBook风格链接与分隔 ========== */
a {
    color: #3498db;
    text-decoration: none;
    border-bottom: 1px dotted #3498db;
}

a:hover {
    color: #2980b9;
    border-bottom-style: solid;
}

hr {
    border: none;
    border-top: 2px solid #ecf0f1;
    margin: 24px 0;
}

/* ========== GitBook风格页脚时间戳 ========== */
.timestamp {
    margin-top: 50px;
    padding-top: 16px;
    border-top: 2px solid #ecf0f1;
    font-size: 9pt;
    color: #95a5a6;
    text-align: center;
    font-style: italic;
}
"""


# ==================== 爬虫线程 ====================

class CrawlerThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self):
        super().__init__()
        self.url = ""
        self.platform = "runoob"
        self.output_dir = "./output"
        self.formats: List[str] = ['markdown', 'html', 'pdf']
        self.download_images = True
        self.aggregate = True
        self.running = True

    def run(self):
        try:
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
            img_dir = os.path.join(self.output_dir, 'images')
            Path(img_dir).mkdir(parents=True, exist_ok=True)
            dispatch = {
                'runoob': self._crawl_runoob,
                'csdn': self._crawl_csdn,
                'gitbook': self._crawl_gitbook,
            }
            dispatch[self.platform]()
            self.finished.emit(True,
                               f"✅ 完成!\n保存位置: {os.path.abspath(self.output_dir)}")
        except Exception as e:
            import traceback
            self.finished.emit(False,
                               f"❌ 错误: {e}\n\n{traceback.format_exc()}")

    def stop(self):
        self.running = False

    def _crawl_runoob(self):
        self.progress.emit("📖 正在分析菜鸟教程...")
        crawler = RunoobCrawler()
        title, articles = crawler.extract_tutorial_info(self.url)
        if not articles:
            raise Exception("未找到任何章节")
        self.progress.emit(f"📚 教程: {title} ({len(articles)}章)")
        # 保存第一篇文章的原始标题，用于文件名
        first_article_title = articles[0].title if articles else title
        self._fetch_all(crawler, articles)
        # 使用保存的标题作为文件名，避免被fetch_all覆盖
        self._output(first_article_title, articles, "菜鸟教程")

    def _crawl_csdn(self):
        self.progress.emit("📖 正在分析CSDN...")
        crawler = CSDNCrawler()
        if crawler.is_list_page(self.url):
            articles = crawler.extract_column_articles(self.url)
            if not articles:
                raise Exception("未找到任何文章")
            title = f"CSDN专栏_{len(articles)}篇"
            self.progress.emit(f"📚 专栏: {len(articles)}篇文章")
        else:
            articles = [Article("未命名", self.url)]
            title = "CSDN文章"
        self._fetch_all(crawler, articles, delay=1.0)
        author = next((a.author for a in articles if a.author), "CSDN")
        self._output(title, articles, author)

    def _crawl_gitbook(self):
        self.progress.emit("📖 正在分析GitBook...")
        crawler = GitBookCrawler()
        title, articles = crawler.extract_gitbook_info(self.url)
        if not articles:
            raise Exception("未找到任何章节")
        self.progress.emit(f"📚 文档: {title} ({len(articles)}章)")
        self._fetch_all(crawler, articles)
        self._output(title, articles, "GitBook")

    def _fetch_all(self, crawler: BaseCrawler, articles: List[Article],
                   delay: float = 0.5):
        img_dir = os.path.join(self.output_dir, 'images')
        total = len(articles)
        for idx, art in enumerate(articles, 1):
            if not self.running:
                return
            self.progress.emit(f"📄 [{idx}/{total}] {art.title[:55]}")
            crawler.extract_article_content(art, self.download_images, img_dir)
            time.sleep(delay)

    def _output(self, title: str, articles: List[Article], author: str):
        gen = BookGenerator(self.output_dir, self.progress.emit)

        if self.aggregate:
            # ★★★ 修复2: 聚合文件名始终使用第一篇文章的标题 ★★★
            first_title = articles[0].title if articles else title
            safe = _slugify(first_title)
            self._gen_formats(gen, safe, title, articles, author)
        else:
            for idx, art in enumerate(articles, 1):
                if not self.running:
                    return
                safe = _slugify(art.title) or f"文章_{idx}"
                self._gen_formats(gen, safe, art.title, [art],
                                  art.author or author)
                self.progress.emit(f"✅ [{idx}/{len(articles)}] {safe}")

    def _gen_formats(self, gen: BookGenerator, filename: str, title: str,
                     articles: List[Article], author: str):
        if 'markdown' in self.formats:
            gen.gen_markdown(os.path.join(self.output_dir, f"{filename}.md"),
                             title, articles, author)
        if 'html' in self.formats:
            gen.gen_html(os.path.join(self.output_dir, f"{filename}.html"),
                         title, articles, author)
        if 'pdf' in self.formats and WEASY_AVAILABLE:
            gen.gen_pdf(os.path.join(self.output_dir, f"{filename}.pdf"),
                        title, articles, author)


# ==================== GUI ====================

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.thread: Optional[CrawlerThread] = None
        self.settings = QSettings('WebExtractor', 'v11.1')
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        self.setWindowTitle('Web Content Extractor Pro v11.1')
        self.setGeometry(100, 100, 1000, 700)
        self.setFont(QFont('Microsoft YaHei', 10))

        w = QWidget()
        self.setCentralWidget(w)
        layout = QVBoxLayout(w)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl = QLabel('📚 Web Content Extractor Pro v11.1')
        lbl.setFont(QFont('Microsoft YaHei', 18, QFont.Bold))
        lbl.setStyleSheet('color:#2c3e50;padding:10px')
        layout.addWidget(lbl)

        g1 = QGroupBox('📎 URL地址')
        g1.setFont(QFont('Microsoft YaHei', 11, QFont.Bold))
        l1 = QVBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText('请输入网页URL...')
        self.url_input.setMinimumHeight(40)
        l1.addWidget(self.url_input)
        g1.setLayout(l1)
        layout.addWidget(g1)

        g2 = QGroupBox('🌐 选择平台')
        g2.setFont(QFont('Microsoft YaHei', 11, QFont.Bold))
        l2 = QHBoxLayout()
        self.platform_cb = QComboBox()
        self.platform_cb.addItems([
            '菜鸟教程 (runoob.com)',
            'CSDN博客/专栏 (blog.csdn.net)',
            'GitBook文档 (*.gitbook.io)',
        ])
        self.platform_cb.setMinimumHeight(35)
        l2.addWidget(self.platform_cb)
        g2.setLayout(l2)
        layout.addWidget(g2)

        g3 = QGroupBox('⚙️ 输出选项')
        g3.setFont(QFont('Microsoft YaHei', 11, QFont.Bold))
        l3 = QVBoxLayout()
        fl = QHBoxLayout()
        fl.addWidget(QLabel('输出格式:'))
        self.chk_md = QCheckBox('Markdown')
        self.chk_html = QCheckBox('HTML')
        self.chk_pdf = QCheckBox('PDF')
        for c in (self.chk_md, self.chk_html, self.chk_pdf):
            c.setChecked(True)
            fl.addWidget(c)
        fl.addStretch()
        l3.addLayout(fl)
        self.chk_img = QCheckBox('下载图片到本地')
        self.chk_img.setChecked(True)
        l3.addWidget(self.chk_img)
        self.chk_agg = QCheckBox('合并为单个文件（取消则每章独立）')
        self.chk_agg.setChecked(True)
        l3.addWidget(self.chk_agg)
        dl = QHBoxLayout()
        dl.addWidget(QLabel('输出目录:'))
        self.dir_input = QLineEdit('./output')
        dl.addWidget(self.dir_input)
        browse = QPushButton('浏览...')
        browse.clicked.connect(self._browse_dir)
        dl.addWidget(browse)
        l3.addLayout(dl)
        g3.setLayout(l3)
        layout.addWidget(g3)

        bl = QHBoxLayout()
        self.btn_start = QPushButton('🚀 开始提取')
        self.btn_start.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        self.btn_start.setMinimumHeight(45)
        self.btn_start.setStyleSheet("""
            QPushButton{background:#4a90d9;color:#fff;border:none;border-radius:5px;padding:10px}
            QPushButton:hover{background:#357abd}
            QPushButton:pressed{background:#2a5f9e}
            QPushButton:disabled{background:#bdc3c7}""")
        self.btn_start.clicked.connect(self._start)
        bl.addWidget(self.btn_start)

        self.btn_stop = QPushButton('⏹️ 停止')
        self.btn_stop.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        self.btn_stop.setMinimumHeight(45)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("""
            QPushButton{background:#e74c3c;color:#fff;border:none;border-radius:5px;padding:10px}
            QPushButton:hover{background:#c0392b}
            QPushButton:disabled{background:#bdc3c7}""")
        self.btn_stop.clicked.connect(self._stop)
        bl.addWidget(self.btn_stop)
        layout.addLayout(bl)

        g4 = QGroupBox('📋 运行日志')
        g4.setFont(QFont('Microsoft YaHei', 11, QFont.Bold))
        l4 = QVBoxLayout()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont('Consolas', 9))
        self.log.setMinimumHeight(200)
        l4.addWidget(self.log)
        clr = QPushButton('清空日志')
        clr.clicked.connect(self.log.clear)
        l4.addWidget(clr)
        g4.setLayout(l4)
        layout.addWidget(g4)

        self.statusBar().showMessage('就绪')

    def _browse_dir(self):
        d = QFileDialog.getExistingDirectory(self, '选择输出目录')
        if d:
            self.dir_input.setText(d)

    def _log(self, msg: str):
        self.log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        self.log.moveCursor(QTextCursor.End)

    def _start(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, '警告', '请输入URL地址!')
            return
        fmts = []
        if self.chk_md.isChecked():
            fmts.append('markdown')
        if self.chk_html.isChecked():
            fmts.append('html')
        if self.chk_pdf.isChecked():
            fmts.append('pdf')
        if not fmts:
            QMessageBox.warning(self, '警告', '请至少选择一种输出格式!')
            return
        self._save_settings()
        platforms = {0: 'runoob', 1: 'csdn', 2: 'gitbook'}
        self.thread = CrawlerThread()
        self.thread.url = url
        self.thread.platform = platforms.get(self.platform_cb.currentIndex(), 'runoob')
        self.thread.output_dir = self.dir_input.text()
        self.thread.formats = fmts
        self.thread.download_images = self.chk_img.isChecked()
        self.thread.aggregate = self.chk_agg.isChecked()
        self.thread.progress.connect(self._log)
        self.thread.finished.connect(self._on_done)
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.log.clear()
        self.statusBar().showMessage('正在提取...')
        self.thread.start()

    def _stop(self):
        if self.thread and self.thread.isRunning():
            self.thread.stop()
            self._log("⏹️ 用户停止")
            self.statusBar().showMessage('已停止')

    def _on_done(self, ok: bool, msg: str):
        self._log(msg)
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.statusBar().showMessage('完成!' if ok else '失败')
        if ok:
            QMessageBox.information(self, '完成', msg)
        else:
            QMessageBox.critical(self, '错误', msg)

    def _save_settings(self):
        s = self.settings
        s.setValue('url', self.url_input.text())
        s.setValue('platform', self.platform_cb.currentIndex())
        s.setValue('output_dir', self.dir_input.text())
        s.setValue('md', self.chk_md.isChecked())
        s.setValue('html', self.chk_html.isChecked())
        s.setValue('pdf', self.chk_pdf.isChecked())
        s.setValue('img', self.chk_img.isChecked())
        s.setValue('agg', self.chk_agg.isChecked())

    def _load_settings(self):
        s = self.settings
        self.url_input.setText(s.value('url', ''))
        self.platform_cb.setCurrentIndex(int(s.value('platform', 0)))
        self.dir_input.setText(s.value('output_dir', './output'))
        self.chk_md.setChecked(s.value('md', True, type=bool))
        self.chk_html.setChecked(s.value('html', True, type=bool))
        self.chk_pdf.setChecked(s.value('pdf', True, type=bool))
        self.chk_img.setChecked(s.value('img', True, type=bool))
        self.chk_agg.setChecked(s.value('agg', True, type=bool))

    def closeEvent(self, event):
        if self.thread and self.thread.isRunning():
            r = QMessageBox.question(self, '确认', '爬虫正在运行，确定退出？',
                                     QMessageBox.Yes | QMessageBox.No)
            if r == QMessageBox.Yes:
                self.thread.stop()
                self.thread.wait(3000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont('Microsoft YaHei', 10))
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()