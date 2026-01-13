#!/usr/bin/env python3  
# -*- coding: utf-8 -*-  
"""  
TextProcessorPro - 专业文本处理工具 (PyQt5版本)  
功能：正则测试、编码转换、差异对比、批量替换、统计分析、Markdown预览、JSON/XML格式化  
作者：LYP
GitHub：https://github.com/lyp0746
邮箱：1610369302@qq.com
版本：2.0.0
"""  

import sys  
import re  
import json  
import xml.dom.minidom as minidom  
import difflib  
import base64  
import urllib.parse  
import html  
import hashlib  
from collections import Counter  
from datetime import datetime  
from typing import List, Tuple, Optional  

from PyQt5.QtWidgets import (  
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,  
    QTabWidget, QTextEdit, QLineEdit, QPushButton, QLabel,  
    QCheckBox, QComboBox, QGroupBox, QSplitter, QFileDialog,  
    QMessageBox, QTableWidget, QTableWidgetItem, QStatusBar,  
    QToolBar, QAction, QSpinBox, QProgressBar, QDialog,  
    QGridLayout, QListWidget, QMenu, QActionGroup  
)  
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize  
from PyQt5.QtGui import (  
    QFont, QTextCharFormat, QColor, QSyntaxHighlighter,  
    QTextCursor, QIcon, QPalette, QKeySequence  
)  


class MarkdownHighlighter(QSyntaxHighlighter):  
    """Markdown语法高亮"""  
    
    def __init__(self, document):  
        super().__init__(document)  
        self.highlighting_rules = []  
        
        # 标题格式  
        header_format = QTextCharFormat()  
        header_format.setForeground(QColor("#0066CC"))  
        header_format.setFontWeight(QFont.Bold)  
        self.highlighting_rules.append((r'^#{1,6}\s.*$', header_format))  
        
        # 粗体  
        bold_format = QTextCharFormat()  
        bold_format.setFontWeight(QFont.Bold)  
        self.highlighting_rules.append((r'\*\*.*?\*\*', bold_format))  
        self.highlighting_rules.append((r'__.*?__', bold_format))  
        
        # 斜体  
        italic_format = QTextCharFormat()  
        italic_format.setFontItalic(True)  
        self.highlighting_rules.append((r'\*.*?\*', italic_format))  
        self.highlighting_rules.append((r'_.*?_', italic_format))  
        
        # 代码  
        code_format = QTextCharFormat()  
        code_format.setForeground(QColor("#CC0000"))  
        code_format.setBackground(QColor("#F5F5F5"))  
        code_format.setFont(QFont("Consolas", 10))  
        self.highlighting_rules.append((r'`.*?`', code_format))  
        
        # 链接  
        link_format = QTextCharFormat()  
        link_format.setForeground(QColor("#0066CC"))  
        link_format.setFontUnderline(True)  
        self.highlighting_rules.append((r'\[([^\]]+)\]\(([^)]+)\)', link_format))
        
        # 列表  
        list_format = QTextCharFormat()  
        list_format.setForeground(QColor("#666666"))  
        self.highlighting_rules.append((r'^\s*[-*+]\s', list_format))  
        self.highlighting_rules.append((r'^\s*\d+\.\s', list_format))  
        
    def highlightBlock(self, text):  
        for pattern, format in self.highlighting_rules:  
            expression = re.compile(pattern)  
            for match in expression.finditer(text):  
                self.setFormat(match.start(), match.end() - match.start(), format)  


class RegexTesterWidget(QWidget):  
    """正则表达式测试工具"""  
    
    def __init__(self):  
        super().__init__()  
        self.init_ui()  
        
    def init_ui(self):  
        layout = QVBoxLayout()  
        
        # 正则表达式输入区  
        regex_group = QGroupBox("正则表达式")  
        regex_layout = QVBoxLayout()  
        
        # 正则输入  
        pattern_layout = QHBoxLayout()  
        pattern_layout.addWidget(QLabel("模式:"))  
        self.pattern_input = QLineEdit()  
        self.pattern_input.setFont(QFont("Consolas", 10))  
        self.pattern_input.setPlaceholderText("输入正则表达式...")  
        pattern_layout.addWidget(self.pattern_input)  
        regex_layout.addLayout(pattern_layout)  
        
        # 快速模式  
        quick_layout = QHBoxLayout()  
        quick_layout.addWidget(QLabel("快速模式:"))  
        self.quick_pattern = QComboBox()  
        self.quick_pattern.addItems([  
            "自定义",  
            r"邮箱: \b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  
            r"URL: https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+",  
            r"IP地址: \b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",  
            r"手机号: 1[3-9]\d{9}",  
            r"日期: \d{4}-\d{2}-\d{2}",  
            r"时间: \d{2}:\d{2}:\d{2}",  
            r"中文: [\u4e00-\u9fa5]+",  
            r"数字: \d+",  
        ])  
        self.quick_pattern.currentIndexChanged.connect(self.load_quick_pattern)  
        quick_layout.addWidget(self.quick_pattern)  
        quick_layout.addStretch()  
        regex_layout.addLayout(quick_layout)  
        
        # 选项  
        options_layout = QHBoxLayout()  
        self.ignore_case = QCheckBox("忽略大小写 (IGNORECASE)")  
        self.multiline = QCheckBox("多行模式 (MULTILINE)")  
        self.dotall = QCheckBox("点匹配所有 (DOTALL)")  
        self.verbose = QCheckBox("详细模式 (VERBOSE)")  
        
        options_layout.addWidget(self.ignore_case)  
        options_layout.addWidget(self.multiline)  
        options_layout.addWidget(self.dotall)  
        options_layout.addWidget(self.verbose)  
        options_layout.addStretch()  
        regex_layout.addLayout(options_layout)  
        
        regex_group.setLayout(regex_layout)  
        layout.addWidget(regex_group)  
        
        # 测试文本区  
        text_group = QGroupBox("测试文本")  
        text_layout = QVBoxLayout()  
        
        self.test_text = QTextEdit()  
        self.test_text.setFont(QFont("Consolas", 10))  
        self.test_text.setPlaceholderText("输入要测试的文本...")  
        self.test_text.textChanged.connect(self.auto_highlight)  
        text_layout.addWidget(self.test_text)  
        
        text_group.setLayout(text_layout)  
        layout.addWidget(text_group)  
        
        # 操作按钮  
        btn_layout = QHBoxLayout()  
        
        self.find_btn = QPushButton("🔍 查找匹配")  
        self.find_btn.clicked.connect(self.find_matches)  
        
        self.highlight_btn = QPushButton("🎨 高亮显示")  
        self.highlight_btn.clicked.connect(self.highlight_matches)  
        
        self.extract_btn = QPushButton("📦 提取分组")  
        self.extract_btn.clicked.connect(self.extract_groups)  
        
        self.replace_btn = QPushButton("🔄 测试替换")  
        self.replace_btn.clicked.connect(self.test_replace)  
        
        self.clear_btn = QPushButton("🗑️ 清除")  
        self.clear_btn.clicked.connect(self.clear_all)  
        
        self.auto_highlight_check = QCheckBox("自动高亮")  
        self.auto_highlight_check.setChecked(True)  
        
        btn_layout.addWidget(self.find_btn)  
        btn_layout.addWidget(self.highlight_btn)  
        btn_layout.addWidget(self.extract_btn)  
        btn_layout.addWidget(self.replace_btn)  
        btn_layout.addWidget(self.clear_btn)  
        btn_layout.addStretch()  
        btn_layout.addWidget(self.auto_highlight_check)  
        
        layout.addLayout(btn_layout)  
        
        # 结果显示区  
        result_group = QGroupBox("匹配结果")  
        result_layout = QVBoxLayout()  
        
        self.result_text = QTextEdit()  
        self.result_text.setFont(QFont("Consolas", 9))  
        self.result_text.setReadOnly(True)  
        result_layout.addWidget(self.result_text)  
        
        result_group.setLayout(result_layout)  
        layout.addWidget(result_group)  
        
        self.setLayout(layout)  
        
        # 设置比例  
        layout.setStretch(0, 0)  # regex_group  
        layout.setStretch(1, 2)  # text_group  
        layout.setStretch(2, 0)  # btn_layout  
        layout.setStretch(3, 1)  # result_group  
        
    def load_quick_pattern(self, index):  
        """加载快速模式"""  
        if index > 0:  
            pattern = self.quick_pattern.currentText().split(": ", 1)[1]  
            self.pattern_input.setText(pattern)  
    
    def get_regex_flags(self):  
        """获取正则标志"""  
        flags = 0  
        if self.ignore_case.isChecked():  
            flags |= re.IGNORECASE  
        if self.multiline.isChecked():  
            flags |= re.MULTILINE  
        if self.dotall.isChecked():  
            flags |= re.DOTALL  
        if self.verbose.isChecked():  
            flags |= re.VERBOSE  
        return flags  
    
    def find_matches(self):  
        """查找所有匹配"""  
        pattern = self.pattern_input.text()  
        text = self.test_text.toPlainText()  
        
        if not pattern:  
            QMessageBox.warning(self, "警告", "请输入正则表达式")  
            return  
        
        try:  
            flags = self.get_regex_flags()  
            matches = list(re.finditer(pattern, text, flags))  
            
            self.result_text.clear()  
            if matches:  
                result = f"找到 {len(matches)} 个匹配:\n\n"  
                for i, match in enumerate(matches, 1):  
                    result += f"匹配 {i}:\n"  
                    result += f"  位置: {match.start()}-{match.end()}\n"  
                    result += f"  内容: {repr(match.group(0))}\n\n"  
                self.result_text.setText(result)  
            else:  
                self.result_text.setText("未找到匹配项")  
        except re.error as e:  
            QMessageBox.critical(self, "错误", f"正则表达式错误:\n{str(e)}")  
    
    def highlight_matches(self):  
        """高亮显示匹配"""  
        pattern = self.pattern_input.text()  
        text = self.test_text.toPlainText()  
        
        if not pattern:  
            QMessageBox.warning(self, "警告", "请输入正则表达式")  
            return  
        
        try:  
            flags = self.get_regex_flags()  
            matches = list(re.finditer(pattern, text, flags))  
            
            # 清除之前的格式  
            cursor = self.test_text.textCursor()  
            cursor.select(QTextCursor.Document)  
            cursor.setCharFormat(QTextCharFormat())  
            
            # 应用高亮  
            format = QTextCharFormat()  
            format.setBackground(QColor("#FFFF00"))  
            format.setForeground(QColor("#FF0000"))  
            
            for match in matches:  
                cursor = self.test_text.textCursor()  
                cursor.setPosition(match.start())  
                cursor.setPosition(match.end(), QTextCursor.KeepAnchor)  
                cursor.setCharFormat(format)  
            
            self.result_text.setText(f"已高亮显示 {len(matches)} 个匹配项")  
        except re.error as e:  
            QMessageBox.critical(self, "错误", f"正则表达式错误:\n{str(e)}")  
    
    def extract_groups(self):  
        """提取分组"""  
        pattern = self.pattern_input.text()  
        text = self.test_text.toPlainText()  
        
        if not pattern:  
            QMessageBox.warning(self, "警告", "请输入正则表达式")  
            return  
        
        try:  
            flags = self.get_regex_flags()  
            matches = list(re.finditer(pattern, text, flags))  
            
            self.result_text.clear()  
            if matches:  
                result = ""  
                for i, match in enumerate(matches, 1):  
                    result += f"匹配 {i}:\n"  
                    result += f"  完整匹配: {repr(match.group(0))}\n"  
                    
                    if match.groups():  
                        for j, group in enumerate(match.groups(), 1):  
                            result += f"  分组 {j}: {repr(group)}\n"  
                    
                    if match.groupdict():  
                        for name, value in match.groupdict().items():  
                            result += f"  命名分组 '{name}': {repr(value)}\n"  
                    
                    result += "\n"  
                
                self.result_text.setText(result)  
            else:  
                self.result_text.setText("未找到匹配项")  
        except re.error as e:  
            QMessageBox.critical(self, "错误", f"正则表达式错误:\n{str(e)}")  
    
    def test_replace(self):  
        """测试替换"""  
        pattern = self.pattern_input.text()  
        text = self.test_text.toPlainText()  
        
        if not pattern:  
            QMessageBox.warning(self, "警告", "请输入正则表达式")  
            return  
        
        replacement, ok = QMessageBox.getText(self, "替换文本", "输入替换文本:")  
        if not ok:  
            return  
        
        try:  
            flags = self.get_regex_flags()  
            new_text = re.sub(pattern, replacement, text, flags=flags)  
            count = len(re.findall(pattern, text, flags))  
            
            self.result_text.setText(f"替换预览 (共 {count} 处):\n\n{new_text}")  
        except re.error as e:  
            QMessageBox.critical(self, "错误", f"正则表达式错误:\n{str(e)}")  
    
    def auto_highlight(self):  
        """自动高亮"""  
        if self.auto_highlight_check.isChecked() and self.pattern_input.text():  
            self.highlight_matches()  
    
    def clear_all(self):  
        """清除所有"""  
        cursor = self.test_text.textCursor()  
        cursor.select(QTextCursor.Document)  
        cursor.setCharFormat(QTextCharFormat())  
        self.result_text.clear()  


class EncodingConverterWidget(QWidget):  
    """编码转换工具"""  
    
    def __init__(self):  
        super().__init__()  
        self.init_ui()  
        
    def init_ui(self):  
        layout = QVBoxLayout()  
        
        # 输入区  
        input_group = QGroupBox("输入文本")  
        input_layout = QVBoxLayout()  
        
        self.input_text = QTextEdit()  
        self.input_text.setFont(QFont("Consolas", 10))  
        self.input_text.setPlaceholderText("输入要转换的文本...")  
        input_layout.addWidget(self.input_text)  
        
        input_group.setLayout(input_layout)  
        layout.addWidget(input_group)  
        
        # 转换选项  
        options_layout = QHBoxLayout()  
        
        options_layout.addWidget(QLabel("转换类型:"))  
        self.convert_type = QComboBox()  
        self.convert_type.addItems([  
            "Base64 编码",  
            "Base64 解码",  
            "URL 编码",  
            "URL 解码",  
            "HTML 转义",  
            "HTML 反转义",  
            "Unicode 转义",  
            "Unicode 反转义",  
            "转大写",  
            "转小写",  
            "首字母大写",  
            "MD5 哈希",  
            "SHA1 哈希",  
            "SHA256 哈希",  
            "十六进制编码",  
            "十六进制解码",  
            "JSON格式化",  
            "JSON压缩",  
            "XML格式化",  
        ])  
        options_layout.addWidget(self.convert_type)  
        
        self.convert_btn = QPushButton("🔄 执行转换")  
        self.convert_btn.clicked.connect(self.perform_conversion)  
        options_layout.addWidget(self.convert_btn)  
        
        self.swap_btn = QPushButton("⇅ 交换输入输出")  
        self.swap_btn.clicked.connect(self.swap_io)  
        options_layout.addWidget(self.swap_btn)  
        
        self.copy_btn = QPushButton("📋 复制结果")  
        self.copy_btn.clicked.connect(self.copy_result)  
        options_layout.addWidget(self.copy_btn)  
        
        self.clear_btn = QPushButton("🗑️ 清空")  
        self.clear_btn.clicked.connect(self.clear_all)  
        options_layout.addWidget(self.clear_btn)  
        
        options_layout.addStretch()  
        layout.addLayout(options_layout)  
        
        # 输出区  
        output_group = QGroupBox("转换结果")  
        output_layout = QVBoxLayout()  
        
        self.output_text = QTextEdit()  
        self.output_text.setFont(QFont("Consolas", 10))  
        self.output_text.setReadOnly(True)  
        output_layout.addWidget(self.output_text)  
        
        output_group.setLayout(output_layout)  
        layout.addWidget(output_group)  
        
        self.setLayout(layout)  
        
        # 设置比例  
        layout.setStretch(0, 1)  # input_group  
        layout.setStretch(1, 0)  # options_layout  
        layout.setStretch(2, 1)  # output_group  
    
    def perform_conversion(self):  
        """执行转换"""  
        text = self.input_text.toPlainText()  
        if not text:  
            QMessageBox.warning(self, "警告", "请输入要转换的文本")  
            return  
        
        conv_type = self.convert_type.currentText()  
        result = ""  
        
        try:  
            if conv_type == "Base64 编码":  
                result = base64.b64encode(text.encode('utf-8')).decode('utf-8')  
            elif conv_type == "Base64 解码":  
                result = base64.b64decode(text.encode('utf-8')).decode('utf-8')  
            elif conv_type == "URL 编码":  
                result = urllib.parse.quote(text)  
            elif conv_type == "URL 解码":  
                result = urllib.parse.unquote(text)  
            elif conv_type == "HTML 转义":  
                result = html.escape(text)  
            elif conv_type == "HTML 反转义":  
                result = html.unescape(text)  
            elif conv_type == "Unicode 转义":  
                result = text.encode('unicode_escape').decode('utf-8')  
            elif conv_type == "Unicode 反转义":  
                result = text.encode('utf-8').decode('unicode_escape')  
            elif conv_type == "转大写":  
                result = text.upper()  
            elif conv_type == "转小写":  
                result = text.lower()  
            elif conv_type == "首字母大写":  
                result = text.title()  
            elif conv_type == "MD5 哈希":  
                result = hashlib.md5(text.encode('utf-8')).hexdigest()  
            elif conv_type == "SHA1 哈希":  
                result = hashlib.sha1(text.encode('utf-8')).hexdigest()  
            elif conv_type == "SHA256 哈希":  
                result = hashlib.sha256(text.encode('utf-8')).hexdigest()  
            elif conv_type == "十六进制编码":  
                result = text.encode('utf-8').hex()  
            elif conv_type == "十六进制解码":  
                result = bytes.fromhex(text).decode('utf-8')  
            elif conv_type == "JSON格式化":  
                obj = json.loads(text)  
                result = json.dumps(obj, indent=4, ensure_ascii=False)  
            elif conv_type == "JSON压缩":  
                obj = json.loads(text)  
                result = json.dumps(obj, ensure_ascii=False, separators=(',', ':'))  
            elif conv_type == "XML格式化":  
                dom = minidom.parseString(text)  
                result = dom.toprettyxml(indent="  ")  
            
            self.output_text.setPlainText(result)  
        except Exception as e:  
            QMessageBox.critical(self, "错误", f"转换失败:\n{str(e)}")  
    
    def swap_io(self):  
        """交换输入输出"""  
        input_text = self.input_text.toPlainText()  
        output_text = self.output_text.toPlainText()  
        self.input_text.setPlainText(output_text)  
        self.output_text.setPlainText(input_text)  
    
    def copy_result(self):  
        """复制结果"""  
        QApplication.clipboard().setText(self.output_text.toPlainText())  
        QMessageBox.information(self, "成功", "结果已复制到剪贴板")  
    
    def clear_all(self):  
        """清空"""  
        self.input_text.clear()  
        self.output_text.clear()  


class DiffComparerWidget(QWidget):  
    """文本差异对比"""  
    
    def __init__(self):  
        super().__init__()  
        self.init_ui()  
        
    def init_ui(self):  
        layout = QVBoxLayout()  
        
        # 创建分割器  
        splitter = QSplitter(Qt.Vertical)  
        
        # 文本1  
        text1_group = QGroupBox("文本 1 (原始)")  
        text1_layout = QVBoxLayout()  
        
        text1_toolbar = QHBoxLayout()  
        self.load_file1_btn = QPushButton("📂 加载文件")  
        self.load_file1_btn.clicked.connect(lambda: self.load_file(1))  
        text1_toolbar.addWidget(self.load_file1_btn)  
        text1_toolbar.addStretch()  
        text1_layout.addLayout(text1_toolbar)  
        
        self.text1 = QTextEdit()  
        self.text1.setFont(QFont("Consolas", 10))  
        text1_layout.addWidget(self.text1)  
        
        text1_group.setLayout(text1_layout)  
        splitter.addWidget(text1_group)  
        
        # 文本2  
        text2_group = QGroupBox("文本 2 (修改)")  
        text2_layout = QVBoxLayout()  
        
        text2_toolbar = QHBoxLayout()  
        self.load_file2_btn = QPushButton("📂 加载文件")  
        self.load_file2_btn.clicked.connect(lambda: self.load_file(2))  
        text2_toolbar.addWidget(self.load_file2_btn)  
        text2_toolbar.addStretch()  
        text2_layout.addLayout(text2_toolbar)  
        
        self.text2 = QTextEdit()  
        self.text2.setFont(QFont("Consolas", 10))  
        text2_layout.addWidget(self.text2)  
        
        text2_group.setLayout(text2_layout)  
        splitter.addWidget(text2_group)  
        
        # 结果区  
        result_group = QGroupBox("差异结果")  
        result_layout = QVBoxLayout()  
        
        self.result_text = QTextEdit()  
        self.result_text.setFont(QFont("Consolas", 9))  
        self.result_text.setReadOnly(True)  
        result_layout.addWidget(self.result_text)  
        
        result_group.setLayout(result_layout)  
        splitter.addWidget(result_group)  
        
        layout.addWidget(splitter)  
        
        # 操作按钮  
        btn_layout = QHBoxLayout()  
        
        self.compare_btn = QPushButton("📊 对比差异")  
        self.compare_btn.clicked.connect(self.compare_diff)  
        
        self.unified_btn = QPushButton("📋 统一格式")  
        self.unified_btn.clicked.connect(self.unified_diff)  
        
        self.context_btn = QPushButton("📝 上下文格式")  
        self.context_btn.clicked.connect(self.context_diff)  
        
        self.html_btn = QPushButton("🌐 导出HTML")  
        self.html_btn.clicked.connect(self.export_html)  
        
        self.side_by_side_btn = QPushButton("⇄ 并排对比")  
        self.side_by_side_btn.clicked.connect(self.side_by_side_compare)  
        
        self.clear_btn = QPushButton("🗑️ 清空")  
        self.clear_btn.clicked.connect(self.clear_all)  
        
        btn_layout.addWidget(self.compare_btn)  
        btn_layout.addWidget(self.unified_btn)  
        btn_layout.addWidget(self.context_btn)  
        btn_layout.addWidget(self.html_btn)  
        btn_layout.addWidget(self.side_by_side_btn)  
        btn_layout.addWidget(self.clear_btn)  
        btn_layout.addStretch()  
        
        layout.addLayout(btn_layout)  
        
        self.setLayout(layout)  
    
    def load_file(self, num):  
        """加载文件"""  
        file_path, _ = QFileDialog.getOpenFileName(  
            self, "选择文件", "",  
            "Text Files (*.txt);;All Files (*.*)"  
        )  
        
        if file_path:  
            try:  
                with open(file_path, 'r', encoding='utf-8') as f:  
                    content = f.read()  
                    if num == 1:  
                        self.text1.setPlainText(content)  
                    else:  
                        self.text2.setPlainText(content)  
            except Exception as e:  
                QMessageBox.critical(self, "错误", f"读取文件失败:\n{str(e)}")  
    
    def compare_diff(self):  
        """对比差异"""  
        text1_lines = self.text1.toPlainText().splitlines()  
        text2_lines = self.text2.toPlainText().splitlines()  
        
        diff = difflib.ndiff(text1_lines, text2_lines)  
        
        result = []  
        add_count = 0  
        remove_count = 0  
        
        for line in diff:  
            if line.startswith('+ '):  
                add_count += 1  
                result.append(f'<span style="color: green;">{html.escape(line)}</span>')  
            elif line.startswith('- '):  
                remove_count += 1  
                result.append(f'<span style="color: red;">{html.escape(line)}</span>')  
            elif line.startswith('? '):  
                result.append(f'<span style="color: blue;">{html.escape(line)}</span>')  
            else:  
                result.append(html.escape(line))  
        
        header = f"<b>差异统计: +{add_count} 行新增, -{remove_count} 行删除</b><br><br>"  
        self.result_text.setHtml(header + '<br>'.join(result))  
    
    def unified_diff(self):  
        """统一格式差异"""  
        text1_lines = self.text1.toPlainText().splitlines(keepends=True)  
        text2_lines = self.text2.toPlainText().splitlines(keepends=True)  
        
        diff = difflib.unified_diff(  
            text1_lines, text2_lines,  
            fromfile='文本1',  
            tofile='文本2',  
            lineterm=''  
        )  
        
        result = []  
        for line in diff:  
            if line.startswith('+'):  
                result.append(f'<span style="color: green;">{html.escape(line)}</span>')  
            elif line.startswith('-'):  
                result.append(f'<span style="color: red;">{html.escape(line)}</span>')  
            elif line.startswith('@'):  
                result.append(f'<span style="color: blue; font-weight: bold;">{html.escape(line)}</span>')  
            else:  
                result.append(html.escape(line))  
        
        self.result_text.setHtml('<br>'.join(result))  
    
    def context_diff(self):  
        """上下文格式差异"""  
        text1_lines = self.text1.toPlainText().splitlines(keepends=True)  
        text2_lines = self.text2.toPlainText().splitlines(keepends=True)  
        
        diff = difflib.context_diff(  
            text1_lines, text2_lines,  
            fromfile='文本1',  
            tofile='文本2',  
            lineterm=''  
        )  
        
        result = []  
        for line in diff:  
            if line.startswith('+ '):  
                result.append(f'<span style="color: green;">{html.escape(line)}</span>')  
            elif line.startswith('- '):  
                result.append(f'<span style="color: red;">{html.escape(line)}</span>')  
            elif line.startswith('! '):  
                                result.append(f'<span style="color: orange;">{html.escape(line)}</span>')
            elif line.startswith('***'):
                result.append(f'<span style="color: blue; font-weight: bold;">{html.escape(line)}</span>')
            else:
                result.append(html.escape(line))
        
        self.result_text.setHtml('<br>'.join(result))
    
    def export_html(self):
        """导出HTML"""
        text1_lines = self.text1.toPlainText().splitlines()
        text2_lines = self.text2.toPlainText().splitlines()
        
        html_diff = difflib.HtmlDiff()
        result = html_diff.make_file(
            text1_lines, text2_lines,
            '文本1', '文本2',
            context=True,
            numlines=3
        )
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存HTML文件", "",
            "HTML Files (*.html);;All Files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                QMessageBox.information(self, "成功", f"HTML差异报告已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")
    
    def side_by_side_compare(self):
        """并排对比"""
        text1_lines = self.text1.toPlainText().splitlines()
        text2_lines = self.text2.toPlainText().splitlines()
        
        max_lines = max(len(text1_lines), len(text2_lines))
        
        result = ['<table border="1" cellpadding="5" style="border-collapse: collapse;">']
        result.append('<tr><th>行号</th><th>文本1</th><th>文本2</th><th>状态</th></tr>')
        
        for i in range(max_lines):
            line1 = text1_lines[i] if i < len(text1_lines) else ''
            line2 = text2_lines[i] if i < len(text2_lines) else ''
            
            if line1 == line2:
                status = '相同'
                color = '#E8F5E9'
            elif not line1:
                status = '新增'
                color = '#E1F5FE'
            elif not line2:
                status = '删除'
                color = '#FFEBEE'
            else:
                status = '修改'
                color = '#FFF3E0'
            
            result.append(f'<tr style="background-color: {color};">')
            result.append(f'<td>{i+1}</td>')
            result.append(f'<td>{html.escape(line1)}</td>')
            result.append(f'<td>{html.escape(line2)}</td>')
            result.append(f'<td>{status}</td>')
            result.append('</tr>')
        
        result.append('</table>')
        self.result_text.setHtml(''.join(result))
    
    def clear_all(self):
        """清空"""
        self.text1.clear()
        self.text2.clear()
        self.result_text.clear()


class BatchReplaceWidget(QWidget):
    """批量文本替换"""
    
    def __init__(self):
        super().__init__()
        self.history = []
        self.current_index = -1
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 文本编辑区
        text_group = QGroupBox("编辑文本")
        text_layout = QVBoxLayout()
        
        # 工具栏
        toolbar = QHBoxLayout()
        self.load_btn = QPushButton("📂 打开文件")
        self.load_btn.clicked.connect(self.load_file)
        self.save_btn = QPushButton("💾 保存文件")
        self.save_btn.clicked.connect(self.save_file)
        self.undo_btn = QPushButton("↶ 撤销")
        self.undo_btn.clicked.connect(self.undo)
        self.redo_btn = QPushButton("↷ 重做")
        self.redo_btn.clicked.connect(self.redo)
        
        toolbar.addWidget(self.load_btn)
        toolbar.addWidget(self.save_btn)
        toolbar.addWidget(self.undo_btn)
        toolbar.addWidget(self.redo_btn)
        toolbar.addStretch()
        
        text_layout.addLayout(toolbar)
        
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Consolas", 10))
        text_layout.addWidget(self.text_edit)
        
        text_group.setLayout(text_layout)
        layout.addWidget(text_group)
        
        # 替换规则区
        rule_group = QGroupBox("替换规则")
        rule_layout = QVBoxLayout()
        
        # 单个替换
        single_layout = QGridLayout()
        single_layout.addWidget(QLabel("查找:"), 0, 0)
        self.find_input = QLineEdit()
        self.find_input.setFont(QFont("Consolas", 10))
        single_layout.addWidget(self.find_input, 0, 1)
        
        single_layout.addWidget(QLabel("替换为:"), 1, 0)
        self.replace_input = QLineEdit()
        self.replace_input.setFont(QFont("Consolas", 10))
        single_layout.addWidget(self.replace_input, 1, 1)
        
        rule_layout.addLayout(single_layout)
        
        # 选项
        options_layout = QHBoxLayout()
        self.regex_check = QCheckBox("正则表达式")
        self.case_check = QCheckBox("区分大小写")
        self.whole_word_check = QCheckBox("全字匹配")
        
        options_layout.addWidget(self.regex_check)
        options_layout.addWidget(self.case_check)
        options_layout.addWidget(self.whole_word_check)
        options_layout.addStretch()
        
        rule_layout.addLayout(options_layout)
        
        # 批量规则
        rule_layout.addWidget(QLabel("批量规则 (每行格式: 查找->替换):"))
        self.batch_rules = QTextEdit()
        self.batch_rules.setFont(QFont("Consolas", 9))
        self.batch_rules.setMaximumHeight(100)
        self.batch_rules.setPlaceholderText("示例:\nold->new\nfoo->bar")
        rule_layout.addWidget(self.batch_rules)
        
        rule_group.setLayout(rule_layout)
        layout.addWidget(rule_group)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        self.find_btn = QPushButton("🔍 查找")
        self.find_btn.clicked.connect(self.find_text)
        
        self.replace_btn = QPushButton("🔄 替换当前")
        self.replace_btn.clicked.connect(self.replace_current)
        
        self.replace_all_btn = QPushButton("🔄 替换全部")
        self.replace_all_btn.clicked.connect(self.replace_all)
        
        self.batch_replace_btn = QPushButton("📦 批量替换")
        self.batch_replace_btn.clicked.connect(self.batch_replace)
        
        self.preview_btn = QPushButton("👁️ 预览")
        self.preview_btn.clicked.connect(self.preview_replace)
        
        self.clear_btn = QPushButton("🗑️ 清空")
        self.clear_btn.clicked.connect(self.clear_all)
        
        btn_layout.addWidget(self.find_btn)
        btn_layout.addWidget(self.replace_btn)
        btn_layout.addWidget(self.replace_all_btn)
        btn_layout.addWidget(self.batch_replace_btn)
        btn_layout.addWidget(self.preview_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #E8F5E9; }")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # 设置比例
        layout.setStretch(0, 3)  # text_group
        layout.setStretch(1, 1)  # rule_group
    
    def save_history(self):
        """保存历史记录"""
        content = self.text_edit.toPlainText()
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        self.history.append(content)
        self.current_index += 1
        
        # 限制历史记录数量
        if len(self.history) > 50:
            self.history.pop(0)
            self.current_index -= 1
    
    def load_file(self):
        """加载文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "",
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.text_edit.setPlainText(content)
                    self.save_history()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"读取文件失败:\n{str(e)}")
    
    def save_file(self):
        """保存文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "",
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.text_edit.toPlainText())
                QMessageBox.information(self, "成功", "文件已保存")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")
    
    def undo(self):
        """撤销"""
        if self.current_index > 0:
            self.current_index -= 1
            self.text_edit.setPlainText(self.history[self.current_index])
            self.status_label.setText("已撤销")
    
    def redo(self):
        """重做"""
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            self.text_edit.setPlainText(self.history[self.current_index])
            self.status_label.setText("已重做")
    
    def find_text(self):
        """查找文本"""
        find_str = self.find_input.text()
        if not find_str:
            QMessageBox.warning(self, "警告", "请输入查找内容")
            return
        
        cursor = self.text_edit.textCursor()
        flags = QTextDocument.FindFlags()
        
        if self.case_check.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        if self.whole_word_check.isChecked():
            flags |= QTextDocument.FindWholeWords
        
        if self.regex_check.isChecked():
            import re
            pattern = re.compile(find_str)
            cursor = self.text_edit.document().find(pattern, cursor, flags)
        else:
            cursor = self.text_edit.document().find(find_str, cursor, flags)
        
        if not cursor.isNull():
            self.text_edit.setTextCursor(cursor)
            self.status_label.setText("找到匹配项")
        else:
            self.status_label.setText("未找到匹配项")
    
    def replace_current(self):
        """替换当前"""
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            self.save_history()
            cursor.insertText(self.replace_input.text())
            self.status_label.setText("已替换当前项")
        else:
            QMessageBox.information(self, "提示", "请先选择要替换的文本")
    
    def replace_all(self):
        """替换全部"""
        find_str = self.find_input.text()
        replace_str = self.replace_input.text()
        
        if not find_str:
            QMessageBox.warning(self, "警告", "请输入查找内容")
            return
        
        self.save_history()
        content = self.text_edit.toPlainText()
        
        if self.regex_check.isChecked():
            flags = 0 if self.case_check.isChecked() else re.IGNORECASE
            try:
                new_content = re.sub(find_str, replace_str, content, flags=flags)
                count = len(re.findall(find_str, content, flags=flags))
            except re.error as e:
                QMessageBox.critical(self, "错误", f"正则表达式错误:\n{str(e)}")
                return
        else:
            if self.whole_word_check.isChecked():
                pattern = r'\b' + re.escape(find_str) + r'\b'
                flags = 0 if self.case_check.isChecked() else re.IGNORECASE
                new_content = re.sub(pattern, replace_str, content, flags=flags)
                count = len(re.findall(pattern, content, flags=flags))
            else:
                if self.case_check.isChecked():
                    count = content.count(find_str)
                    new_content = content.replace(find_str, replace_str)
                else:
                    count = content.lower().count(find_str.lower())
                    new_content = re.sub(
                        re.escape(find_str), replace_str,
                        content, flags=re.IGNORECASE
                    )
        
        self.text_edit.setPlainText(new_content)
        self.status_label.setText(f"已替换 {count} 处")
    
    def batch_replace(self):
        """批量替换"""
        rules_text = self.batch_rules.toPlainText().strip()
        if not rules_text:
            QMessageBox.warning(self, "警告", "请输入批量替换规则")
            return
        
        self.save_history()
        content = self.text_edit.toPlainText()
        total_count = 0
        
        for line in rules_text.split('\n'):
            line = line.strip()
            if '->' not in line:
                continue
            
            find_str, replace_str = line.split('->', 1)
            find_str = find_str.strip()
            replace_str = replace_str.strip()
            
            if find_str:
                count = content.count(find_str)
                content = content.replace(find_str, replace_str)
                total_count += count
        
        self.text_edit.setPlainText(content)
        self.status_label.setText(f"批量替换完成，共替换 {total_count} 处")
    
    def preview_replace(self):
        """预览替换"""
        find_str = self.find_input.text()
        if not find_str:
            QMessageBox.warning(self, "警告", "请输入查找内容")
            return
        
        # 高亮显示
        cursor = QTextCursor(self.text_edit.document())
        format = QTextCharFormat()
        format.setBackground(QColor("#FFFF00"))
        
        while True:
            cursor = self.text_edit.document().find(find_str, cursor)
            if cursor.isNull():
                break
            cursor.mergeCharFormat(format)
        
        content = self.text_edit.toPlainText()
        flags = 0 if self.case_check.isChecked() else re.IGNORECASE
        
        if self.regex_check.isChecked():
            try:
                count = len(re.findall(find_str, content, flags))
            except:
                count = 0
        else:
            count = content.count(find_str) if self.case_check.isChecked() else content.lower().count(find_str.lower())
        
        self.status_label.setText(f"预览：找到 {count} 处匹配")
    
    def clear_all(self):
        """清空"""
        reply = QMessageBox.question(
            self, "确认", "确定要清空所有内容吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.save_history()
            self.text_edit.clear()
            self.status_label.setText("已清空")


class TextStatsWidget(QWidget):
    """文本统计分析"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 文本输入区
        input_group = QGroupBox("待分析文本")
        input_layout = QVBoxLayout()
        
        input_toolbar = QHBoxLayout()
        self.load_btn = QPushButton("📂 加载文件")
        self.load_btn.clicked.connect(self.load_file)
        self.paste_btn = QPushButton("📋 粘贴")
        self.paste_btn.clicked.connect(self.paste_text)
        input_toolbar.addWidget(self.load_btn)
        input_toolbar.addWidget(self.paste_btn)
        input_toolbar.addStretch()
        input_layout.addLayout(input_toolbar)
        
        self.input_text = QTextEdit()
        self.input_text.setFont(QFont("Consolas", 10))
        self.input_text.setPlaceholderText("输入或粘贴要分析的文本...")
        input_layout.addWidget(self.input_text)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        self.basic_btn = QPushButton("📊 基础统计")
        self.basic_btn.clicked.connect(self.basic_stats)
        
        self.word_freq_btn = QPushButton("📈 词频分析")
        self.word_freq_btn.clicked.connect(self.word_frequency)
        
        self.char_dist_btn = QPushButton("📉 字符分布")
        self.char_dist_btn.clicked.connect(self.char_distribution)
        
        self.line_stats_btn = QPushButton("📏 行统计")
        self.line_stats_btn.clicked.connect(self.line_stats)
        
        self.export_btn = QPushButton("💾 导出报告")
        self.export_btn.clicked.connect(self.export_report)
        
        self.clear_btn = QPushButton("🗑️ 清空")
        self.clear_btn.clicked.connect(self.clear_all)
        
        btn_layout.addWidget(self.basic_btn)
        btn_layout.addWidget(self.word_freq_btn)
        btn_layout.addWidget(self.char_dist_btn)
        btn_layout.addWidget(self.line_stats_btn)
        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # 结果显示区
        result_group = QGroupBox("统计结果")
        result_layout = QVBoxLayout()
        
        self.result_text = QTextEdit()
        self.result_text.setFont(QFont("Consolas", 9))
        self.result_text.setReadOnly(True)
        result_layout.addWidget(self.result_text)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        self.setLayout(layout)
        
        # 设置比例
        layout.setStretch(0, 2)  # input_group
        layout.setStretch(1, 0)  # btn_layout
        layout.setStretch(2, 2)  # result_group
    
    def load_file(self):
        """加载文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "",
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.input_text.setPlainText(content)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"读取文件失败:\n{str(e)}")
    
    def paste_text(self):
        """粘贴文本"""
        clipboard = QApplication.clipboard()
        self.input_text.setPlainText(clipboard.text())
    
    def basic_stats(self):
        """基础统计"""
        text = self.input_text.toPlainText()
        
        if not text:
            QMessageBox.warning(self, "警告", "请输入要分析的文本")
            return
        
        # 统计各项指标
        total_chars = len(text)
        total_chars_no_space = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
        lines = text.split('\n')
        total_lines = len(lines)
        non_empty_lines = len([line for line in lines if line.strip()])
        words = text.split()
        total_words = len(words)
        
        # 字符类型统计
        letters = sum(c.isalpha() for c in text)
        digits = sum(c.isdigit() for c in text)
        spaces = sum(c.isspace() for c in text)
        punctuation = sum(not c.isalnum() and not c.isspace() for c in text)
        
        # 中英文统计
        chinese = sum('\u4e00' <= c <= '\u9fff' for c in text)
        english = sum(c.isalpha() and ord(c) < 128 for c in text)
        
        # 平均值
        avg_word_length = sum(len(w) for w in words) / total_words if total_words > 0 else 0
        avg_line_length = sum(len(line) for line in lines) / total_lines if total_lines > 0 else 0
        
        result = f"""
╔════════════════════════════════════════════════╗
║                  基础文本统计                   ║
╠════════════════════════════════════════════════╣
║ 总字符数:              {total_chars:>20,}
║ 有效字符数(不含空白):  {total_chars_no_space:>20,}
║ 总行数:                {total_lines:>20,}
║ 非空行数:              {non_empty_lines:>20,}
║ 总单词数:              {total_words:>20,}
╠════════════════════════════════════════════════╣
║ 字母:                  {letters:>20,}
║ 数字:                  {digits:>20,}
║ 空白字符:              {spaces:>20,}
║ 标点符号:              {punctuation:>20,}
╠════════════════════════════════════════════════╣
║ 中文字符:              {chinese:>20,}
║ 英文字符:              {english:>20,}
╠════════════════════════════════════════════════╣
║ 平均单词长度:          {avg_word_length:>20.2f}
║ 平均行长度:            {avg_line_length:>20.2f}
╚════════════════════════════════════════════════╝
        """
        
        self.result_text.setPlainText(result.strip())
    
    def word_frequency(self):
        """词频分析"""
        text = self.input_text.toPlainText()
        
        if not text:
            QMessageBox.warning(self, "警告", "请输入要分析的文本")
            return
        
        # 分词
        words = re.findall(r'\b\w+\b', text.lower())
        
        if not words:
            self.result_text.setPlainText("未找到有效单词")
            return
        
        word_count = Counter(words)
        total_words = len(words)
        unique_words = len(word_count)
        
        result = f"词频分析结果\n{'='*70}\n\n"
        result += f"总单词数: {total_words:,}\n"
        result += f"唯一单词数: {unique_words:,}\n"
        result += f"词汇丰富度: {(unique_words/total_words)*100:.2f}%\n\n"
        result += f"Top 30 高频词:\n{'-'*70}\n"
        result += f"{'排名':<6}{'单词':<20}{'次数':<10}{'占比':<10}{'图示'}\n"
        result += f"{'-'*70}\n"
        
        for i, (word, count) in enumerate(word_count.most_common(30), 1):
            percentage = (count / total_words) * 100
            bar = '█' * int(percentage * 3)
            result += f"{i:<6}{word:<20}{count:<10}{percentage:>6.2f}%    {bar}\n"
        
        self.result_text.setPlainText(result)
    
    def char_distribution(self):
        """字符分布"""
        text = self.input_text.toPlainText()
        
        if not text:
            QMessageBox.warning(self, "警告", "请输入要分析的文本")
            return
        
        char_count = Counter(text)
        
        # 移除空白字符
        for char in [' ', '\n', '\t', '\r']:
            char_count.pop(char, None)
        
        if not char_count:
            self.result_text.setPlainText("未找到有效字符")
            return
        
        total_chars = sum(char_count.values())
        
        result = f"字符分布分析\n{'='*80}\n\n"
        result += f"有效字符总数: {total_chars:,}\n"
        result += f"唯一字符数: {len(char_count):,}\n\n"
        result += f"Top 50 高频字符:\n{'-'*80}\n"
        result += f"{'排名':<6}{'字符':<10}{'次数':<10}{'占比':<10}{'图示'}\n"
        result += f"{'-'*80}\n"
        
        for i, (char, count) in enumerate(char_count.most_common(50), 1):
            percentage = (count / total_chars) * 100
            bar = '▓' * int(percentage * 4)
            char_repr = repr(char)[1:-1] if not char.isprintable() else char
            result += f"{i:<6}{char_repr:<10}{count:<10}{percentage:>6.2f}%    {bar}\n"
        
        self.result_text.setPlainText(result)
    
    def line_stats(self):
        """行统计"""
        text = self.input_text.toPlainText()
        
        if not text:
            QMessageBox.warning(self, "警告", "请输入要分析的文本")
            return
        
        lines = text.split('\n')
        line_lengths = [len(line) for line in lines]
        non_empty_lines = [line for line in lines if line.strip()]
        
        total_lines = len(lines)
        empty_lines = total_lines - len(non_empty_lines)
        max_length = max(line_lengths) if line_lengths else 0
        min_length = min(line_lengths) if line_lengths else 0
        avg_length = sum(line_lengths) / total_lines if total_lines > 0 else 0
        
        # 长度分布
        length_dist = Counter(line_lengths)
        
        result = f"行统计分析\n{'='*70}\n\n"
        result += f"总行数: {total_lines:,}\n"
        result += f"非空行数: {len(non_empty_lines):,}\n"
        result += f"空行数: {empty_lines:,}\n"
        result += f"最长行: {max_length:,} 字符\n"
        result += f"最短行: {min_length:,} 字符\n"
        result += f"平均行长: {avg_length:.2f} 字符\n\n"
        
        result += f"行长度分布 (Top 20):\n{'-'*70}\n"
        result += f"{'长度':<10}{'行数':<10}{'占比'}\n"
        result += f"{'-'*70}\n"
        
        for length, count in sorted(length_dist.most_common(20)):
            percentage = (count / total_lines) * 100
            bar = '█' * int(percentage * 2)
            result += f"{length:<10}{count:<10}{percentage:>6.2f}%  {bar}\n"
        
        self.result_text.setPlainText(result)
    
    def export_report(self):
        """导出报告"""
        if not self.result_text.toPlainText():
            QMessageBox.warning(self, "警告", "没有可导出的统计结果")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存报告", "",
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"TextProcessorPro 统计报告\n")
                    f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"{'='*70}\n\n")
                    f.write(self.result_text.toPlainText())
                QMessageBox.information(self, "成功", f"报告已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")
    
    def clear_all(self):
        """清空"""
        self.input_text.clear()
        self.result_text.clear()


class MarkdownEditorWidget(QWidget):
    """Markdown编辑器"""
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        # 文件操作
        self.new_btn = QPushButton("📄 新建")
        self.new_btn.clicked.connect(self.new_file)
        self.open_btn = QPushButton("📂 打开")
        self.open_btn.clicked.connect(self.open_file)
        self.save_btn = QPushButton("💾 保存")
        self.save_btn.clicked.connect(self.save_file)
        self.save_as_btn = QPushButton("💾 另存为")
        self.save_as_btn.clicked.connect(self.save_as_file)
        
        toolbar.addWidget(self.new_btn)
        toolbar.addWidget(self.open_btn)
        toolbar.addWidget(self.save_btn)
        toolbar.addWidget(self.save_as_btn)
        
        # 分隔符
        toolbar.addWidget(QLabel("|"))
        
        # Markdown快捷按钮
        md_buttons = [
            ("H1", "# "),
            ("H2", "## "),
            ("H3", "### "),
            ("粗体", "**", "**"),
            ("斜体", "*", "*"),
            ("代码", "`", "`"),
            ("链接", "[](url)", ""),
            ("图片", "![](url)", ""),
            ("列表", "- ", ""),
            ("引用", "> ", ""),
            ("分割线", "\n---\n", ""),
        ]
        
        for text, prefix, *suffix in md_buttons:
            btn = QPushButton(text)
            suffix_text = suffix[0] if suffix else ""
            btn.clicked.connect(lambda checked, p=prefix, s=suffix_text: self.insert_markdown(p, s))
            toolbar.addWidget(btn)
        
        toolbar.addStretch()
        
        # 导出按钮
        self.export_html_btn = QPushButton("🌐 导出HTML")
        self.export_html_btn.clicked.connect(self.export_html)
        self.export_pdf_btn = QPushButton("📄 导出PDF")
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        
        toolbar.addWidget(self.export_html_btn)
        toolbar.addWidget(self.export_pdf_btn)
        
        layout.addLayout(toolbar)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 编辑区
        editor_group = QGroupBox("Markdown 编辑器")
        editor_layout = QVBoxLayout()
        
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Consolas", 11))
        self.editor.textChanged.connect(self.update_preview)
        
        # 应用语法高亮
        self.highlighter = MarkdownHighlighter(self.editor.document())
        
        editor_layout.addWidget(self.editor)
        editor_group.setLayout(editor_layout)
        splitter.addWidget(editor_group)
        
        # 预览区
        preview_group = QGroupBox("实时预览")
        preview_layout = QVBoxLayout()
        
        self.preview = QTextEdit()
        self.preview.setFont(QFont("Microsoft YaHei", 10))
        self.preview.setReadOnly(True)
        preview_layout.addWidget(self.preview)
        
        preview_group.setLayout(preview_layout)
        splitter.addWidget(preview_group)
        
        layout.addWidget(splitter)
        
        # 状态栏
        status_layout = QHBoxLayout()
        self.status_label = QLabel("就绪")
        self.word_count_label = QLabel("字数: 0")
        self.char_count_label = QLabel("字符: 0")
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.word_count_label)
        status_layout.addWidget(self.char_count_label)
        
        layout.addLayout(status_layout)
        
        self.setLayout(layout)
        
        # 自动保存定时器
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(60000)  # 每分钟自动保存
    
    def insert_markdown(self, prefix, suffix=""):
        """插入Markdown语法"""
        cursor = self.editor.textCursor()
        
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            cursor.insertText(f"{prefix}{selected_text}{suffix}")
        else:
            cursor.insertText(f"{prefix}{suffix}")
            # 移动光标到中间
            if suffix:
                for _ in range(len(suffix)):
                    cursor.movePosition(QTextCursor.Left)
                self.editor.setTextCursor(cursor)
    
    def update_preview(self):
        """更新预览"""
        md_text = self.editor.toPlainText()
        
        # 简单的Markdown转HTML
        html_content = self.markdown_to_html(md_text)
        self.preview.setHtml(html_content)
        
        # 更新统计
        words = len(md_text.split())
        chars = len(md_text)
        self.word_count_label.setText(f"字数: {words}")
        self.char_count_label.setText(f"字符: {chars}")
    
    def markdown_to_html(self, md_text):
        """简单的Markdown转HTML"""
        lines = md_text.split('\n')
        html_lines = []
        in_code_block = False
        in_list = False
        
        for line in lines:
            # 代码块
            if line.startswith('```'):  
                if in_code_block:  
                    html_lines.append('</code></pre>')  
                    in_code_block = False  
                else:  
                    html_lines.append('<pre><code>')  
                    in_code_block = True  
                continue  
            
            if in_code_block:  
                html_lines.append(html.escape(line))  
                continue  
            
            # 标题  
            if line.startswith('# '):  
                html_lines.append(f'<h1>{html.escape(line[2:])}</h1>')  
            elif line.startswith('## '):  
                html_lines.append(f'<h2>{html.escape(line[3:])}</h2>')  
            elif line.startswith('### '):  
                html_lines.append(f'<h3>{html.escape(line[4:])}</h3>')  
            elif line.startswith('#### '):  
                html_lines.append(f'<h4>{html.escape(line[5:])}</h4>')  
            # 列表  
            elif line.startswith('- ') or line.startswith('* '):  
                if not in_list:  
                    html_lines.append('<ul>')  
                    in_list = True  
                html_lines.append(f'<li>{html.escape(line[2:])}</li>')  
            elif line.startswith('> '):  
                html_lines.append(f'<blockquote>{html.escape(line[2:])}</blockquote>')  
            elif line.strip() == '---':  
                html_lines.append('<hr>')  
            else:  
                if in_list and line.strip():  
                    html_lines.append('</ul>')  
                    in_list = False  
                
                # 行内样式  
                line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)  
                line = re.sub(r'\*(.*?)\*', r'<em>\1</em>', line)  
                line = re.sub(r'`(.*?)`', r'<code>\1</code>', line)  
                line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', line)
                line = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', line)
                
                if line.strip():  
                    html_lines.append(f'<p>{line}</p>')  
                else:  
                    html_lines.append('<br>')  
        
        if in_list:  
            html_lines.append('</ul>')  
        
        css = """  
        <style>  
            body { font-family: 'Microsoft YaHei', Arial, sans-serif; line-height: 1.6; padding: 20px; }  
            h1, h2, h3, h4 { color: #333; margin-top: 24px; margin-bottom: 16px; }  
            h1 { border-bottom: 2px solid #eee; padding-bottom: 8px; }  
            h2 { border-bottom: 1px solid #eee; padding-bottom: 6px; }  
            code { background-color: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-family: Consolas, monospace; }  
            pre { background-color: #f5f5f5; padding: 16px; border-radius: 6px; overflow-x: auto; }  
            pre code { padding: 0; }  
            blockquote { border-left: 4px solid #ddd; padding-left: 16px; color: #666; margin: 16px 0; }  
            a { color: #0066cc; text-decoration: none; }  
            a:hover { text-decoration: underline; }  
            ul { padding-left: 24px; }  
            li { margin: 8px 0; }  
            hr { border: none; border-top: 2px solid #eee; margin: 24px 0; }  
        </style>  
        """  
        
        return css + ''.join(html_lines)  
    
    def new_file(self):  
        """新建文件"""  
        if self.editor.toPlainText():  
            reply = QMessageBox.question(  
                self, "确认", "当前文档未保存，是否继续？",  
                QMessageBox.Yes | QMessageBox.No  
            )  
            if reply == QMessageBox.No:  
                return  
        
        self.editor.clear()  
        self.current_file = None  
        self.status_label.setText("新建文档")  
    
    def open_file(self):  
        """打开文件"""  
        file_path, _ = QFileDialog.getOpenFileName(  
            self, "打开文件", "",  
            "Markdown Files (*.md *.markdown);;Text Files (*.txt);;All Files (*.*)"  
        )  
        
        if file_path:  
            try:  
                with open(file_path, 'r', encoding='utf-8') as f:  
                    content = f.read()  
                    self.editor.setPlainText(content)  
                    self.current_file = file_path  
                    self.status_label.setText(f"已打开: {file_path}")  
            except Exception as e:  
                QMessageBox.critical(self, "错误", f"打开文件失败:\n{str(e)}")  
    
    def save_file(self):  
        """保存文件"""  
        if self.current_file:  
            try:  
                with open(self.current_file, 'w', encoding='utf-8') as f:  
                    f.write(self.editor.toPlainText())  
                self.status_label.setText(f"已保存: {self.current_file}")  
            except Exception as e:  
                QMessageBox.critical(self, "错误", f"保存文件失败:\n{str(e)}")  
        else:  
            self.save_as_file()  
    
    def save_as_file(self):  
        """另存为"""  
        file_path, _ = QFileDialog.getSaveFileName(  
            self, "另存为", "",  
            "Markdown Files (*.md);;Text Files (*.txt);;All Files (*.*)"  
        )  
        
        if file_path:  
            try:  
                with open(file_path, 'w', encoding='utf-8') as f:  
                    f.write(self.editor.toPlainText())  
                self.current_file = file_path  
                self.status_label.setText(f"已保存: {file_path}")  
            except Exception as e:  
                QMessageBox.critical(self, "错误", f"保存文件失败:\n{str(e)}")  
    
    def auto_save(self):  
        """自动保存"""  
        if self.current_file and self.editor.toPlainText():  
            try:  
                with open(self.current_file, 'w', encoding='utf-8') as f:  
                    f.write(self.editor.toPlainText())  
            except:  
                pass  
    
    def export_html(self):  
        """导出HTML"""  
        file_path, _ = QFileDialog.getSaveFileName(  
            self, "导出HTML", "",  
            "HTML Files (*.html);;All Files (*.*)"  
        )  
        
        if file_path:  
            try:  
                html_content = f"""  
<!DOCTYPE html>  
<html>  
<head>  
    <meta charset="UTF-8">  
    <title>Markdown Export</title>  
    {self.markdown_to_html("")}  
</head>  
<body>  
    {self.preview.toHtml()}  
</body>  
</html>  
                """  
                with open(file_path, 'w', encoding='utf-8') as f:  
                    f.write(html_content)  
                QMessageBox.information(self, "成功", f"HTML已导出到:\n{file_path}")  
            except Exception as e:  
                QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")  
    
    def export_pdf(self):  
        """导出PDF"""  
        QMessageBox.information(self, "提示", "PDF导出功能需要安装额外的库\n建议先导出为HTML，然后使用浏览器打印为PDF")  


class MainWindow(QMainWindow):  
    """主窗口"""  
    
    def __init__(self):  
        super().__init__()  
        self.init_ui()  
        
    def init_ui(self):  
        self.setWindowTitle("TextProcessorPro - 专业文本处理工具")  
        self.setGeometry(100, 100, 1400, 900)  
        
        # 设置应用图标和样式  
        self.setup_style()  
        
        # 创建中心widget  
        central_widget = QWidget()  
        self.setCentralWidget(central_widget)  
        
        # 主布局  
        main_layout = QVBoxLayout(central_widget)  
        
        # 创建标签页  
        self.tab_widget = QTabWidget()  
        self.tab_widget.setTabPosition(QTabWidget.North)  
        self.tab_widget.setMovable(True)  
        
        # 添加各功能标签页  
        self.tab_widget.addTab(RegexTesterWidget(), "🔍 正则测试")  
        self.tab_widget.addTab(EncodingConverterWidget(), "🔄 编码转换")  
        self.tab_widget.addTab(DiffComparerWidget(), "📊 差异对比")  
        self.tab_widget.addTab(BatchReplaceWidget(), "🔧 批量替换")  
        self.tab_widget.addTab(TextStatsWidget(), "📈 统计分析")  
        self.tab_widget.addTab(MarkdownEditorWidget(), "📝 Markdown")  
        
        main_layout.addWidget(self.tab_widget)  
        
        # 创建状态栏  
        self.status_bar = QStatusBar()  
        self.setStatusBar(self.status_bar)  
        self.status_bar.showMessage("就绪")  
        
        # 创建菜单栏  
        self.create_menu_bar()  
        
        # 创建工具栏  
        self.create_toolbar()  
    
    def setup_style(self):  
        """设置样式"""  
        # 使用Fusion风格  
        QApplication.setStyle('Fusion')  
        
        # 设置调色板  
        palette = QPalette()  
        palette.setColor(QPalette.Window, QColor(240, 240, 240))  
        palette.setColor(QPalette.WindowText, QColor(0, 0, 0))  
        palette.setColor(QPalette.Base, QColor(255, 255, 255))  
        palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))  
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))  
        palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))  
        palette.setColor(QPalette.Text, QColor(0, 0, 0))  
        palette.setColor(QPalette.Button, QColor(240, 240, 240))  
        palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))  
        palette.setColor(QPalette.Link, QColor(0, 102, 204))  
        palette.setColor(QPalette.Highlight, QColor(0, 120, 215))  
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))  
        
        QApplication.setPalette(palette)  
        
        # 自定义样式表  
        self.setStyleSheet("""  
            QTabWidget::pane {  
                border: 1px solid #cccccc;  
                background-color: white;  
            }  
            QTabBar::tab {  
                background-color: #e0e0e0;  
                padding: 8px 16px;  
                margin-right: 2px;  
                border-top-left-radius: 4px;  
                border-top-right-radius: 4px;  
            }  
            QTabBar::tab:selected {  
                background-color: white;  
                border-bottom: 2px solid #0078d4;  
            }  
            QTabBar::tab:hover {  
                background-color: #f0f0f0;  
            }  
            QPushButton {  
                background-color: #0078d4;  
                color: white;  
                border: none;  
                padding: 6px 12px;  
                border-radius: 4px;  
                font-size: 13px;  
            }  
            QPushButton:hover {  
                background-color: #0063b1;  
            }  
            QPushButton:pressed {  
                background-color: #005a9e;  
            }  
            QGroupBox {  
                font-weight: bold;  
                border: 2px solid #cccccc;  
                border-radius: 6px;  
                margin-top: 12px;  
                padding-top: 12px;  
            }  
            QGroupBox::title {  
                subcontrol-origin: margin;  
                subcontrol-position: top left;  
                padding: 0 8px;  
                color: #0078d4;  
            }  
            QLineEdit, QTextEdit {  
                border: 1px solid #cccccc;  
                border-radius: 4px;  
                padding: 4px;  
            }  
            QLineEdit:focus, QTextEdit:focus {  
                border: 2px solid #0078d4;  
            }  
        """)  
    
    def create_menu_bar(self):  
        """创建菜单栏"""  
        menubar = self.menuBar()  
        
        # 文件菜单  
        file_menu = menubar.addMenu("文件(&F)")  
        
        new_action = QAction("新建", self)  
        new_action.setShortcut(QKeySequence.New)  
        file_menu.addAction(new_action)  
        
        open_action = QAction("打开", self)  
        open_action.setShortcut(QKeySequence.Open)  
        file_menu.addAction(open_action)  
        
        save_action = QAction("保存", self)  
        save_action.setShortcut(QKeySequence.Save)  
        file_menu.addAction(save_action)  
        
        file_menu.addSeparator()  
        
        exit_action = QAction("退出", self)  
        exit_action.setShortcut(QKeySequence.Quit)  
        exit_action.triggered.connect(self.close)  
        file_menu.addAction(exit_action)  
        
        # 编辑菜单  
        edit_menu = menubar.addMenu("编辑(&E)")  
        
        undo_action = QAction("撤销", self)  
        undo_action.setShortcut(QKeySequence.Undo)  
        edit_menu.addAction(undo_action)  
        
        redo_action = QAction("重做", self)  
        redo_action.setShortcut(QKeySequence.Redo)  
        edit_menu.addAction(redo_action)  
        
        edit_menu.addSeparator()  
        
        cut_action = QAction("剪切", self)  
        cut_action.setShortcut(QKeySequence.Cut)  
        edit_menu.addAction(cut_action)  
        
        copy_action = QAction("复制", self)  
        copy_action.setShortcut(QKeySequence.Copy)  
        edit_menu.addAction(copy_action)  
        
        paste_action = QAction("粘贴", self)  
        paste_action.setShortcut(QKeySequence.Paste)  
        edit_menu.addAction(paste_action)  
        
        # 视图菜单  
        view_menu = menubar.addMenu("视图(&V)")  
        
        theme_menu = view_menu.addMenu("主题")  
        theme_group = QActionGroup(self)  
        
        light_theme = QAction("浅色主题", self, checkable=True)  
        light_theme.setChecked(True)  
        light_theme.triggered.connect(lambda: self.change_theme("light"))  
        theme_group.addAction(light_theme)  
        theme_menu.addAction(light_theme)  
        
        dark_theme = QAction("深色主题", self, checkable=True)  
        dark_theme.triggered.connect(lambda: self.change_theme("dark"))  
        theme_group.addAction(dark_theme)  
        theme_menu.addAction(dark_theme)  
        
        # 工具菜单  
        tools_menu = menubar.addMenu("工具(&T)")  
        
        settings_action = QAction("设置", self)  
        settings_action.triggered.connect(self.show_settings)  
        tools_menu.addAction(settings_action)  
        
        # 帮助菜单  
        help_menu = menubar.addMenu("帮助(&H)")  
        
        about_action = QAction("关于", self)  
        about_action.triggered.connect(self.show_about)  
        help_menu.addAction(about_action)  
        
        help_action = QAction("使用帮助", self)  
        help_action.setShortcut(QKeySequence.HelpContents)  
        help_action.triggered.connect(self.show_help)  
        help_menu.addAction(help_action)  
    
    def create_toolbar(self):  
        """创建工具栏"""  
        toolbar = QToolBar()  
        toolbar.setMovable(False)  
        toolbar.setIconSize(QSize(24, 24))  
        self.addToolBar(toolbar)  
        
        # 添加快捷按钮  
        regex_action = QAction("🔍 正则", self)  
        regex_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))  
        toolbar.addAction(regex_action)  
        
        encode_action = QAction("🔄 编码", self)  
        encode_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))  
        toolbar.addAction(encode_action)  
        
        diff_action = QAction("📊 对比", self)  
        diff_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))  
        toolbar.addAction(diff_action)  
        
        replace_action = QAction("🔧 替换", self)  
        replace_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(3))  
        toolbar.addAction(replace_action)  
        
        stats_action = QAction("📈 统计", self)  
        stats_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(4))  
        toolbar.addAction(stats_action)  
        
        md_action = QAction("📝 Markdown", self)  
        md_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(5))  
        toolbar.addAction(md_action)  
        
        toolbar.addSeparator()  
        
        # 搜索框  
        search_label = QLabel("搜索:")  
        toolbar.addWidget(search_label)  
        
        self.search_box = QLineEdit()  
        self.search_box.setPlaceholderText("搜索功能...")  
        self.search_box.setMaximumWidth(200)  
        toolbar.addWidget(self.search_box)  
    
    def change_theme(self, theme):  
        """更改主题"""  
        if theme == "dark":
            self.apply_vscode_dark()
        else:
            self.setup_style()

    def apply_vscode_dark(self):
        """应用 VS Code 风格深色主题（全局）"""
        palette = QPalette()
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
        QApplication.setPalette(palette)

        global_style = (
            "QWidget { background-color: #1e1e1e; color: #d4d4d4; }"
            "QMainWindow { background-color: #1e1e1e; }"
            "QGroupBox { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #2a2a2a; margin-top: 6px; }"
            "QScrollArea { background-color: #1e1e1e; }"
            "QScrollArea QWidget { background-color: #1e1e1e; }"
            "QTabWidget::pane { background: #1e1e1e; }"
            "QTabBar::tab { background: #252526; color: #d4d4d4; padding: 6px; }"
            "QTabBar::tab:selected { background: #1e1e1e; }"
            "QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #3c3c3c; }"
            "QTableWidget, QListWidget { background-color: #1e1e1e; color: #d4d4d4; gridline-color: #2a2a2a; }"
            "QHeaderView::section { background-color: #2d2d30; color: #d4d4d4; }"
            "QPushButton { background-color: #0e639c; color: #ffffff; border: 0px solid #3c3c3c; padding: 4px 8px; border-radius: 3px; }"
            "QPushButton:hover { background-color: #1177bb; }"
            "QProgressBar { background: #252526; color: #d4d4d4; border: 1px solid #3c3c3c; }"
            "QStatusBar { background: #1e1e1e; color: #d4d4d4; }"
            "QToolTip { background-color: #f5f5f5; color: #111; }"
        )
        self.setStyleSheet(global_style)
    
    def show_settings(self):  
        """显示设置对话框"""  
        QMessageBox.information(self, "设置", "设置功能开发中...")  
    
    def show_about(self):  
        """显示关于对话框"""  
        about_text = """  
        <h2>TextProcessorPro</h2>  
        <p><b>版本:</b> 2.0</p>  
        <p><b>作者:</b> AI Assistant</p>  
        <p><b>描述:</b> 专业的文本处理工具集</p>  
        <br>  
        <p><b>功能模块:</b></p>  
        <ul>  
            <li>🔍 正则表达式测试</li>  
            <li>🔄 文本编码转换</li>  
            <li>📊 文本差异对比</li>  
            <li>🔧 批量文本替换</li>  
            <li>📈 文本统计分析</li>  
            <li>📝 Markdown编辑器</li>  
        </ul>  
        <br>  
        <p>© 2024 TextProcessorPro. All rights reserved.</p>  
        """  
        QMessageBox.about(self, "关于 TextProcessorPro", about_text)  
    
    def show_help(self):  
        """显示帮助"""  
        help_text = """  
        <h2>使用帮助</h2>  
        
        <h3>🔍 正则表达式测试</h3>  
        <p>支持实时测试正则表达式，高亮显示匹配结果，提取分组信息。</p>  
        
        <h3>🔄 编码转换</h3>  
        <p>支持多种编码格式转换，包括Base64、URL、HTML、Unicode等。</p>  
        
        <h3>📊 差异对比</h3>  
        <p>对比两个文本的差异，支持多种对比格式和HTML导出。</p>
        
        <h3>🔧 批量替换</h3>
        <p>支持正则表达式替换、批量规则替换，提供预览和撤销功能。</p>
        
        <h3>📈 统计分析</h3>
        <p>全面的文本统计功能，包括词频分析、字符分布等。</p>
        
        <h3>📝 Markdown编辑器</h3>
        <p>实时预览的Markdown编辑器，支持语法高亮和HTML导出。</p>
        
        <br>
        <p><b>快捷键:</b></p>
        <ul>
            <li>Ctrl+N: 新建</li>
            <li>Ctrl+O: 打开</li>
            <li>Ctrl+S: 保存</li>
            <li>Ctrl+Z: 撤销</li>
            <li>Ctrl+Y: 重做</li>
            <li>F1: 帮助</li>
        </ul>
        """
        
        help_dialog = QMessageBox(self)
        help_dialog.setWindowTitle("使用帮助")
        help_dialog.setTextFormat(Qt.RichText)
        help_dialog.setText(help_text)
        help_dialog.exec_()


class JSONFormatterWidget(QWidget):
    """JSON格式化工具（额外功能）"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 输入区
        input_group = QGroupBox("JSON输入")
        input_layout = QVBoxLayout()
        
        self.input_text = QTextEdit()
        self.input_text.setFont(QFont("Consolas", 10))
        self.input_text.setPlaceholderText("输入JSON文本...")
        input_layout.addWidget(self.input_text)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        self.format_btn = QPushButton("✨ 格式化")
        self.format_btn.clicked.connect(self.format_json)
        
        self.compress_btn = QPushButton("📦 压缩")
        self.compress_btn.clicked.connect(self.compress_json)
        
        self.validate_btn = QPushButton("✓ 验证")
        self.validate_btn.clicked.connect(self.validate_json)
        
        self.sort_btn = QPushButton("🔤 排序键")
        self.sort_btn.clicked.connect(self.sort_keys)
        
        self.escape_btn = QPushButton("🔐 转义")
        self.escape_btn.clicked.connect(self.escape_json)
        
        self.unescape_btn = QPushButton("🔓 反转义")
        self.unescape_btn.clicked.connect(self.unescape_json)
        
        self.clear_btn = QPushButton("🗑️ 清空")
        self.clear_btn.clicked.connect(self.clear_all)
        
        btn_layout.addWidget(self.format_btn)
        btn_layout.addWidget(self.compress_btn)
        btn_layout.addWidget(self.validate_btn)
        btn_layout.addWidget(self.sort_btn)
        btn_layout.addWidget(self.escape_btn)
        btn_layout.addWidget(self.unescape_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        
        # 缩进设置
        btn_layout.addWidget(QLabel("缩进:"))
        self.indent_spin = QSpinBox()
        self.indent_spin.setRange(2, 8)
        self.indent_spin.setValue(4)
        btn_layout.addWidget(self.indent_spin)
        
        layout.addLayout(btn_layout)
        
        # 输出区
        output_group = QGroupBox("JSON输出")
        output_layout = QVBoxLayout()
        
        self.output_text = QTextEdit()
        self.output_text.setFont(QFont("Consolas", 10))
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_text)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # 状态信息
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #E8F5E9; }")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        layout.setStretch(0, 1)
        layout.setStretch(1, 0)
        layout.setStretch(2, 1)
    
    def format_json(self):
        """格式化JSON"""
        try:
            text = self.input_text.toPlainText()
            obj = json.loads(text)
            formatted = json.dumps(obj, indent=self.indent_spin.value(), ensure_ascii=False)
            self.output_text.setPlainText(formatted)
            self.status_label.setText("✓ JSON格式化成功")
            self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #E8F5E9; }")
        except json.JSONDecodeError as e:
            self.status_label.setText(f"✗ JSON解析错误: {str(e)}")
            self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #FFEBEE; }")
            QMessageBox.critical(self, "错误", f"JSON格式错误:\n{str(e)}")
    
    def compress_json(self):
        """压缩JSON"""
        try:
            text = self.input_text.toPlainText()
            obj = json.loads(text)
            compressed = json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
            self.output_text.setPlainText(compressed)
            
            original_size = len(text)
            compressed_size = len(compressed)
            ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
            
            self.status_label.setText(f"✓ 压缩完成 - 原始: {original_size} 字节, 压缩后: {compressed_size} 字节, 压缩率: {ratio:.1f}%")
            self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #E8F5E9; }")
        except json.JSONDecodeError as e:
            self.status_label.setText(f"✗ JSON解析错误: {str(e)}")
            self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #FFEBEE; }")
    
    def validate_json(self):
        """验证JSON"""
        try:
            text = self.input_text.toPlainText()
            obj = json.loads(text)
            
            # 分析JSON结构
            def analyze(obj, depth=0):
                if isinstance(obj, dict):
                    return f"对象 ({len(obj)} 个键)"
                elif isinstance(obj, list):
                    return f"数组 ({len(obj)} 个元素)"
                elif isinstance(obj, str):
                    return f"字符串 (长度: {len(obj)})"
                elif isinstance(obj, (int, float)):
                    return f"数字 ({obj})"
                elif isinstance(obj, bool):
                    return f"布尔值 ({obj})"
                elif obj is None:
                    return "null"
                return "未知类型"
            
            info = f"✓ JSON格式正确\n\n根节点类型: {analyze(obj)}"
            self.output_text.setPlainText(info)
            self.status_label.setText("✓ JSON验证通过")
            self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #E8F5E9; }")
        except json.JSONDecodeError as e:
            error_msg = f"✗ JSON格式错误:\n\n行 {e.lineno}, 列 {e.colno}\n{e.msg}"
            self.output_text.setPlainText(error_msg)
            self.status_label.setText("✗ JSON验证失败")
            self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #FFEBEE; }")
    
    def sort_keys(self):
        """排序键"""
        try:
            text = self.input_text.toPlainText()
            obj = json.loads(text)
            sorted_json = json.dumps(obj, indent=self.indent_spin.value(), ensure_ascii=False, sort_keys=True)
            self.output_text.setPlainText(sorted_json)
            self.status_label.setText("✓ 键已按字母顺序排序")
            self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #E8F5E9; }")
        except json.JSONDecodeError as e:
            self.status_label.setText(f"✗ JSON解析错误: {str(e)}")
            self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #FFEBEE; }")
    
    def escape_json(self):
        """转义JSON"""
        text = self.input_text.toPlainText()
        escaped = json.dumps(text)
        self.output_text.setPlainText(escaped)
        self.status_label.setText("✓ JSON已转义")
    
    def unescape_json(self):
        """反转义JSON"""
        try:
            text = self.input_text.toPlainText()
            unescaped = json.loads(text)
            self.output_text.setPlainText(unescaped)
            self.status_label.setText("✓ JSON已反转义")
        except:
            self.status_label.setText("✗ 反转义失败")
            self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #FFEBEE; }")
    
    def clear_all(self):
        """清空"""
        self.input_text.clear()
        self.output_text.clear()
        self.status_label.setText("就绪")
        self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #E8F5E9; }")


class XMLFormatterWidget(QWidget):
    """XML格式化工具（额外功能）"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 输入区
        input_group = QGroupBox("XML输入")
        input_layout = QVBoxLayout()
        
        self.input_text = QTextEdit()
        self.input_text.setFont(QFont("Consolas", 10))
        self.input_text.setPlaceholderText("输入XML文本...")
        input_layout.addWidget(self.input_text)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        self.format_btn = QPushButton("✨ 格式化")
        self.format_btn.clicked.connect(self.format_xml)
        
        self.compress_btn = QPushButton("📦 压缩")
        self.compress_btn.clicked.connect(self.compress_xml)
        
        self.validate_btn = QPushButton("✓ 验证")
        self.validate_btn.clicked.connect(self.validate_xml)
        
        self.to_json_btn = QPushButton("→ JSON")
        self.to_json_btn.clicked.connect(self.xml_to_json)
        
        self.clear_btn = QPushButton("🗑️ 清空")
        self.clear_btn.clicked.connect(self.clear_all)
        
        btn_layout.addWidget(self.format_btn)
        btn_layout.addWidget(self.compress_btn)
        btn_layout.addWidget(self.validate_btn)
        btn_layout.addWidget(self.to_json_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # 输出区
        output_group = QGroupBox("XML输出")
        output_layout = QVBoxLayout()
        
        self.output_text = QTextEdit()
        self.output_text.setFont(QFont("Consolas", 10))
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_text)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # 状态信息
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #E8F5E9; }")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        layout.setStretch(0, 1)
        layout.setStretch(1, 0)
        layout.setStretch(2, 1)
    
    def format_xml(self):
        """格式化XML"""
        try:
            text = self.input_text.toPlainText()
            dom = minidom.parseString(text)
            formatted = dom.toprettyxml(indent="  ")
            # 移除多余的空行
            formatted = '\n'.join([line for line in formatted.split('\n') if line.strip()])
            self.output_text.setPlainText(formatted)
            self.status_label.setText("✓ XML格式化成功")
            self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #E8F5E9; }")
        except Exception as e:
            self.status_label.setText(f"✗ XML解析错误: {str(e)}")
            self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #FFEBEE; }")
            QMessageBox.critical(self, "错误", f"XML格式错误:\n{str(e)}")
    
    def compress_xml(self):
        """压缩XML"""
        try:
            text = self.input_text.toPlainText()
            dom = minidom.parseString(text)
            compressed = dom.toxml()
            self.output_text.setPlainText(compressed)
            
            original_size = len(text)
            compressed_size = len(compressed)
            ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
            
            self.status_label.setText(f"✓ 压缩完成 - 原始: {original_size} 字节, 压缩后: {compressed_size} 字节")
            self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #E8F5E9; }")
        except Exception as e:
            self.status_label.setText(f"✗ XML解析错误: {str(e)}")
            self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #FFEBEE; }")
    
    def validate_xml(self):
        """验证XML"""
        try:
            text = self.input_text.toPlainText()
            dom = minidom.parseString(text)
            
            root = dom.documentElement
            info = f"✓ XML格式正确\n\n"
            info += f"根节点: {root.nodeName}\n"
            info += f"属性数: {len(root.attributes.items()) if root.attributes else 0}\n"
            info += f"子节点数: {len([n for n in root.childNodes if n.nodeType == n.ELEMENT_NODE])}\n"
            
            self.output_text.setPlainText(info)
            self.status_label.setText("✓ XML验证通过")
            self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #E8F5E9; }")
        except Exception as e:
            error_msg = f"✗ XML格式错误:\n\n{str(e)}"
            self.output_text.setPlainText(error_msg)
            self.status_label.setText("✗ XML验证失败")
            self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #FFEBEE; }")
    
    def xml_to_json(self):
        """XML转JSON"""
        try:
            import xml.etree.ElementTree as ET
            
            text = self.input_text.toPlainText()
            root = ET.fromstring(text)
            
            def elem_to_dict(elem):
                result = {}
                if elem.attrib:
                    result['@attributes'] = elem.attrib
                
                children = list(elem)
                if children:
                    child_dict = {}
                    for child in children:
                        child_data = elem_to_dict(child)
                        if child.tag in child_dict:
                            if not isinstance(child_dict[child.tag], list):
                                child_dict[child.tag] = [child_dict[child.tag]]
                            child_dict[child.tag].append(child_data)
                        else:
                            child_dict[child.tag] = child_data
                    result.update(child_dict)
                
                if elem.text and elem.text.strip():
                    if len(result) == 0:
                        return elem.text.strip()
                    else:
                        result['#text'] = elem.text.strip()
                
                return result
            
            json_data = {root.tag: elem_to_dict(root)}
            json_str = json.dumps(json_data, indent=4, ensure_ascii=False)
            
            self.output_text.setPlainText(json_str)
            self.status_label.setText("✓ XML转JSON成功")
            self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #E8F5E9; }")
        except Exception as e:
            self.status_label.setText(f"✗ 转换失败: {str(e)}")
            self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #FFEBEE; }")
            QMessageBox.critical(self, "错误", f"转换失败:\n{str(e)}")
    
    def clear_all(self):
        """清空"""
        self.input_text.clear()
        self.output_text.clear()
        self.status_label.setText("就绪")
        self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #E8F5E9; }")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("TextProcessorPro")
    app.setOrganizationName("TextProcessorPro")
    app.setApplicationVersion("2.0")
    
    # 创建并显示主窗口
    window = MainWindow()
    
    # 可选：添加JSON和XML格式化工具
    window.tab_widget.addTab(JSONFormatterWidget(), "📋 JSON")
    window.tab_widget.addTab(XMLFormatterWidget(), "📰 XML")
    
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()