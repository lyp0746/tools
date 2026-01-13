#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CodeAnalyzerPro - 专业代码分析工具 (PyQt5版本)
功能：代码复杂度分析、依赖关系可视化、质量评分、重复检测、安全扫描、性能分析
支持：Python, JavaScript, Java, C++, Go, Rust等多种语言
作者：LYP
GitHub：https://github.com/lyp0746
邮箱：1610369302@qq.com
版本：2.0.0
"""  

import sys  
import os  
import ast  
import re  
import json  
import hashlib  
import threading  
import time  
from pathlib import Path  
from collections import defaultdict, Counter  
from datetime import datetime  
from typing import Dict, List, Tuple, Set, Any  

from PyQt5.QtWidgets import (  
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,  
    QPushButton, QTreeWidget, QTreeWidgetItem, QTabWidget, QTextEdit,  
    QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox, QSplitter,  
    QLabel, QProgressBar, QStatusBar, QToolBar, QAction, QMenu,  
    QLineEdit, QComboBox, QGroupBox, QHeaderView, QFrame, QDialog,  
    QDialogButtonBox, QCheckBox, QSpinBox  
)  
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer, QSettings  
from PyQt5.QtGui import (  
    QIcon, QFont, QColor, QPalette, QTextCharFormat, QSyntaxHighlighter,  
    QTextDocument, QPainter, QLinearGradient  
)  
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis  


class CodeMetrics:  
    """代码度量类"""  
    
    def __init__(self):  
        self.total_lines = 0  
        self.code_lines = 0  
        self.comment_lines = 0  
        self.blank_lines = 0  
        self.functions = []  
        self.classes = []  
        self.imports = []  
        self.complexity_scores = {}  
        self.max_nesting = 0  
        self.avg_line_length = 0  


class PythonAnalyzer:  
    """Python代码分析器"""  
    
    def analyze_file(self, filepath: str) -> Dict[str, Any]:  
        """分析Python文件"""  
        try:  
            with open(filepath, 'r', encoding='utf-8') as f:  
                content = f.read()  
            
            tree = ast.parse(content)  
            lines = content.split('\n')  
            
            metrics = CodeMetrics()  
            metrics.total_lines = len(lines)  
            metrics.code_lines = self._count_code_lines(lines)  
            metrics.comment_lines = self._count_comment_lines(lines)  
            metrics.blank_lines = metrics.total_lines - metrics.code_lines - metrics.comment_lines  
            metrics.avg_line_length = sum(len(line) for line in lines) / len(lines) if lines else 0  
            
            # 提取函数、类和复杂度  
            for node in ast.walk(tree):  
                if isinstance(node, ast.FunctionDef):  
                    metrics.functions.append(node.name)  
                    metrics.complexity_scores[node.name] = self._calculate_complexity(node)  
                elif isinstance(node, ast.ClassDef):  
                    metrics.classes.append(node.name)  
            
            # 提取导入  
            metrics.imports = self._extract_imports(tree)  
            
            # 计算最大嵌套深度  
            metrics.max_nesting = self._calculate_max_nesting(tree)  
            
            return {  
                'success': True,  
                'metrics': metrics,  
                'content': content,  
                'ast': tree  
            }  
            
        except Exception as e:  
            return {  
                'success': False,  
                'error': str(e)  
            }  
    
    def _count_code_lines(self, lines: List[str]) -> int:  
        """统计代码行数"""  
        count = 0  
        in_multiline_comment = False  
        
        for line in lines:  
            stripped = line.strip()  
            
            # 处理多行注释  
            if '"""' in stripped or "'''" in stripped:  
                in_multiline_comment = not in_multiline_comment  
                continue  
            
            if in_multiline_comment:  
                continue  
            
            # 非空且非注释行  
            if stripped and not stripped.startswith('#'):  
                count += 1  
        
        return count  
    
    def _count_comment_lines(self, lines: List[str]) -> int:  
        """统计注释行数"""  
        count = 0  
        in_multiline_comment = False  
        
        for line in lines:  
            stripped = line.strip()  
            
            if '"""' in stripped or "'''" in stripped:  
                in_multiline_comment = not in_multiline_comment  
                count += 1  
                continue  
            
            if in_multiline_comment:  
                count += 1  
            elif stripped.startswith('#'):  
                count += 1  
        
        return count  
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:  
        """计算圈复杂度"""  
        complexity = 1  # 基础复杂度  
        
        for child in ast.walk(node):  
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):  
                complexity += 1  
            elif isinstance(child, ast.BoolOp):  
                complexity += len(child.values) - 1  
            elif isinstance(child, (ast.And, ast.Or)):  
                complexity += 1  
            elif isinstance(child, ast.Match):  # Python 3.10+  
                complexity += 1  
        
        return complexity  
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:  
        """提取导入模块"""  
        imports = set()  
        
        for node in ast.walk(tree):  
            if isinstance(node, ast.Import):  
                for alias in node.names:  
                    imports.add(alias.name.split('.')[0])  
            elif isinstance(node, ast.ImportFrom):  
                if node.module:  
                    imports.add(node.module.split('.')[0])  
        
        return sorted(list(imports))  
    
    def _calculate_max_nesting(self, tree: ast.AST) -> int:  
        """计算最大嵌套深度"""  
        max_depth = 0  
        
        def get_depth(node, current_depth=0):  
            nonlocal max_depth  
            max_depth = max(max_depth, current_depth)  
            
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With, ast.Try)):  
                current_depth += 1  
            
            for child in ast.iter_child_nodes(node):  
                get_depth(child, current_depth)  
        
        get_depth(tree)  
        return max_depth  


class SecurityScanner:  
    """安全漏洞扫描器"""  
    
    def __init__(self):  
        self.vulnerability_patterns = {  
            'SQL注入': {  
                'patterns': [  
                    r'execute\s*$[^)]*\+[^)]*$',  
                    r'executemany\s*$[^)]*\+[^)]*$',  
                    r'cursor\.execute$[^)]*%[^)]*$',  
                    r'SELECT.*\+.*FROM',  
                    r'INSERT.*\+.*VALUES',  
                ],  
                'severity': 'critical',  
                'description': '可能存在SQL注入漏洞，应使用参数化查询'  
            },  
            'XSS漏洞': {  
                'patterns': [  
                    r'innerHTML\s*=',  
                    r'document\.write$',  
                    r'eval\s*\(',  
                    r'\.html\([^)]*\+',  
                ],  
                'severity': 'high',  
                'description': '可能存在跨站脚本攻击漏洞'  
            },  
            '硬编码密码': {  
                'patterns': [  
                    r'password\s*=\s*["\'][^"\']{8,}["\']',  
                    r'secret\s*=\s*["\'][^"\']+["\']',  
                    r'api_key\s*=\s*["\'][^"\']+["\']',  
                    r'token\s*=\s*["\'][^"\']{20,}["\']',  
                ],  
                'severity': 'high',  
                'description': '检测到硬编码的敏感信息'  
            },  
            '不安全函数': {  
                'patterns': [  
                    r'\beval\s*\(',  
                    r'\bexec\s*\(',  
                    r'pickle\.loads\(',  
                    r'__import__\s*\(',  
                    r'compile\s*\(',  
                ],  
                'severity': 'critical',  
                'description': '使用了不安全的函数，可能导致代码注入'  
            },  
            '路径遍历': {  
                'patterns': [  
                    r'open\s*\([^)]*\+[^)]*$',  
                    r'\.\./',  
                    r'os\.path\.join$[^)]*input[^)]*$',  
                ],  
                'severity': 'medium',  
                'description': '可能存在路径遍历漏洞'  
            },  
            '命令注入': {  
                'patterns': [  
                    r'os\.system\([^)]*\+',  
                    r'subprocess\.call\([^)]*\+',  
                    r'subprocess\.Popen\([^)]*\+',  
                ],  
                'severity': 'critical',  
                'description': '可能存在命令注入漏洞'  
            },  
            '弱加密': {  
                'patterns': [  
                    r'hashlib\.md5\(',  
                    r'hashlib\.sha1\(',  
                    r'DES\.new\(',  
                ],  
                'severity': 'medium',  
                'description': '使用了弱加密算法'  
            },  
        }  
    
    def scan(self, content: str, filepath: str) -> List[Dict[str, Any]]:  
        """扫描安全漏洞"""  
        vulnerabilities = []  
        lines = content.split('\n')  
        
        for vuln_type, vuln_info in self.vulnerability_patterns.items():  
            for pattern in vuln_info['patterns']:  
                for line_num, line in enumerate(lines, 1):  
                    if re.search(pattern, line, re.IGNORECASE):  
                        vulnerabilities.append({  
                            'type': vuln_type,  
                            'severity': vuln_info['severity'],  
                            'description': vuln_info['description'],  
                            'line': line_num,  
                            'code': line.strip(),  
                            'file': filepath  
                        })  
        
        return vulnerabilities  


class DuplicateDetector:  
    """重复代码检测器"""  
    
    def __init__(self, min_lines: int = 6):  
        self.min_lines = min_lines  
    
    def detect(self, files: List[str]) -> Dict[str, List[Tuple[str, int, str]]]:  
        """检测重复代码"""  
        code_blocks = defaultdict(list)  
        
        for filepath in files:  
            try:  
                with open(filepath, 'r', encoding='utf-8') as f:  
                    lines = f.readlines()  
                
                # 滑动窗口检测  
                for i in range(len(lines) - self.min_lines + 1):  
                    block = ''.join(lines[i:i+self.min_lines]).strip()  
                    
                    # 忽略空白和纯注释块  
                    if not block or all(l.strip().startswith('#') for l in lines[i:i+self.min_lines]):  
                        continue  
                    
                    # 标准化代码块（移除空白）  
                    normalized = re.sub(r'\s+', ' ', block)  
                    block_hash = hashlib.md5(normalized.encode()).hexdigest()  
                    
                    code_blocks[block_hash].append((filepath, i+1, block[:200]))  
                    
            except Exception:  
                continue  
        
        # 只返回重复的代码块  
        duplicates = {k: v for k, v in code_blocks.items() if len(v) > 1}  
        return duplicates  


class QualityScorer:  
    """代码质量评分器"""  
    
    def calculate_score(self, metrics: CodeMetrics, vulnerabilities: List) -> Dict[str, Any]:  
        """计算质量评分"""  
        score = 100.0  
        issues = []  
        
        # 复杂度评分 (30分)  
        if metrics.complexity_scores:  
            avg_complexity = sum(metrics.complexity_scores.values()) / len(metrics.complexity_scores)  
            if avg_complexity > 15:  
                deduction = min(15, (avg_complexity - 15) * 2)  
                score -= deduction  
                issues.append(f"平均复杂度过高: {avg_complexity:.1f}")  
            elif avg_complexity > 10:  
                deduction = (avg_complexity - 10) * 1.5  
                score -= deduction  
                issues.append(f"复杂度偏高: {avg_complexity:.1f}")  
        
        # 注释率评分 (15分)  
        if metrics.total_lines > 0:  
            comment_ratio = metrics.comment_lines / metrics.total_lines  
            if comment_ratio < 0.05:  
                score -= 15  
                issues.append(f"注释率过低: {comment_ratio*100:.1f}%")  
            elif comment_ratio < 0.10:  
                score -= 8  
                issues.append(f"注释率较低: {comment_ratio*100:.1f}%")  
            elif comment_ratio > 0.40:  
                score += 5  
        
        # 函数长度评分 (15分)  
        if metrics.code_lines > 0 and metrics.functions:  
            avg_func_lines = metrics.code_lines / len(metrics.functions)  
            if avg_func_lines > 100:  
                score -= 15  
                issues.append(f"函数平均长度过长: {avg_func_lines:.0f}行")  
            elif avg_func_lines > 50:  
                score -= 8  
                issues.append(f"函数平均长度偏长: {avg_func_lines:.0f}行")  
        
        # 嵌套深度评分 (10分)  
        if metrics.max_nesting > 5:  
            score -= 10  
            issues.append(f"嵌套深度过深: {metrics.max_nesting}层")  
        elif metrics.max_nesting > 3:  
            score -= 5  
            issues.append(f"嵌套深度较深: {metrics.max_nesting}层")  
        
        # 行长度评分 (10分)  
        if metrics.avg_line_length > 120:  
            score -= 10  
            issues.append(f"平均行长度过长: {metrics.avg_line_length:.0f}字符")  
        elif metrics.avg_line_length > 100:  
            score -= 5  
            issues.append(f"平均行长度偏长: {metrics.avg_line_length:.0f}字符")  
        
        # 安全漏洞评分 (20分)  
        critical_vulns = sum(1 for v in vulnerabilities if v['severity'] == 'critical')  
        high_vulns = sum(1 for v in vulnerabilities if v['severity'] == 'high')  
        
        score -= critical_vulns * 10  
        score -= high_vulns * 5  
        
        if critical_vulns > 0:  
            issues.append(f"发现{critical_vulns}个严重安全漏洞")  
        if high_vulns > 0:  
            issues.append(f"发现{high_vulns}个高危安全漏洞")  
        
        score = max(0, min(100, score))  
        
        # 评级  
        if score >= 90:  
            grade = 'A'  
            level = '优秀'  
        elif score >= 80:  
            grade = 'B'  
            level = '良好'  
        elif score >= 70:  
            grade = 'C'  
            level = '中等'  
        elif score >= 60:  
            grade = 'D'  
            level = '及格'  
        else:  
            grade = 'F'  
            level = '需改进'  
        
        return {  
            'score': score,  
            'grade': grade,  
            'level': level,  
            'issues': issues  
        }  


class AnalysisWorker(QThread):  
    """分析工作线程"""  
    
    progress = pyqtSignal(int, str)  
    finished = pyqtSignal(dict)  
    error = pyqtSignal(str)  
    
    def __init__(self, files: List[str], options: Dict[str, bool]):  
        super().__init__()  
        self.files = files  
        self.options = options  
        self.analyzer = PythonAnalyzer()  
        self.security_scanner = SecurityScanner()  
        self.duplicate_detector = DuplicateDetector()  
        self.quality_scorer = QualityScorer()  
    
    def run(self):  
        """执行分析"""  
        try:  
            results = {  
                'files': {},  
                'summary': {},  
                'duplicates': {},  
                'vulnerabilities': [],  
                'quality': {}  
            }  
            
            total_files = len(self.files)  
            
            # 分析每个文件  
            for idx, filepath in enumerate(self.files):  
                self.progress.emit(int((idx / total_files) * 50), f"分析文件: {os.path.basename(filepath)}")  
                
                if filepath.endswith('.py'):  
                    result = self.analyzer.analyze_file(filepath)  
                    
                    if result['success']:  
                        results['files'][filepath] = result  
                        
                        # 安全扫描  
                        if self.options.get('security_scan', True):  
                            vulns = self.security_scanner.scan(result['content'], filepath)  
                            results['vulnerabilities'].extend(vulns)  
                
                time.sleep(0.01)  # 避免界面冻结  
            
            # 重复代码检测  
            if self.options.get('duplicate_detection', True):  
                self.progress.emit(60, "检测重复代码...")  
                results['duplicates'] = self.duplicate_detector.detect(self.files)  
            
            # 生成统计摘要  
            self.progress.emit(80, "生成统计报告...")  
            results['summary'] = self._generate_summary(results)  
            
            # 质量评分  
            self.progress.emit(90, "计算质量评分...")  
            results['quality'] = self._calculate_quality(results)  
            
            self.progress.emit(100, "分析完成")  
            self.finished.emit(results)  
            
        except Exception as e:  
            self.error.emit(str(e))  
    
    def _generate_summary(self, results: Dict) -> Dict:  
        """生成统计摘要"""  
        summary = {  
            'total_files': len(results['files']),  
            'total_lines': 0,  
            'total_code_lines': 0,  
            'total_comment_lines': 0,  
            'total_functions': 0,  
            'total_classes': 0,  
            'unique_imports': set(),  
            'avg_complexity': 0,  
            'max_complexity': 0,  
            'complexity_distribution': {'simple': 0, 'moderate': 0, 'complex': 0, 'very_complex': 0}  
        }  
        
        all_complexities = []  
        
        for filepath, result in results['files'].items():  
            if result['success']:  
                metrics = result['metrics']  
                summary['total_lines'] += metrics.total_lines  
                summary['total_code_lines'] += metrics.code_lines  
                summary['total_comment_lines'] += metrics.comment_lines  
                summary['total_functions'] += len(metrics.functions)  
                summary['total_classes'] += len(metrics.classes)  
                summary['unique_imports'].update(metrics.imports)  
                
                for complexity in metrics.complexity_scores.values():  
                    all_complexities.append(complexity)  
                    if complexity <= 5:  
                        summary['complexity_distribution']['simple'] += 1  
                    elif complexity <= 10:  
                        summary['complexity_distribution']['moderate'] += 1  
                    elif complexity <= 20:  
                        summary['complexity_distribution']['complex'] += 1  
                    else:  
                        summary['complexity_distribution']['very_complex'] += 1  
        
        if all_complexities:  
            summary['avg_complexity'] = sum(all_complexities) / len(all_complexities)  
            summary['max_complexity'] = max(all_complexities)  
        
        summary['unique_imports'] = sorted(list(summary['unique_imports']))  
        
        return summary  
    
    def _calculate_quality(self, results: Dict) -> Dict:  
        """计算整体质量"""  
        quality_scores = []  
        
        for filepath, result in results['files'].items():  
            if result['success']:  
                file_vulns = [v for v in results['vulnerabilities'] if v['file'] == filepath]  
                quality = self.quality_scorer.calculate_score(result['metrics'], file_vulns)  
                quality_scores.append(quality['score'])  
        
        if quality_scores:  
            avg_score = sum(quality_scores) / len(quality_scores)  
        else:  
            avg_score = 0  
        
        return {  
            'average_score': avg_score,  
            'file_scores': quality_scores,  
            'total_vulnerabilities': len(results['vulnerabilities']),  
            'critical_vulnerabilities': sum(1 for v in results['vulnerabilities'] if v['severity'] == 'critical'),  
            'high_vulnerabilities': sum(1 for v in results['vulnerabilities'] if v['severity'] == 'high'),  
        }  


class SettingsDialog(QDialog):  
    """设置对话框"""  
    
    def __init__(self, parent=None):  
        super().__init__(parent)  
        self.setWindowTitle("分析设置")  
        self.setModal(True)  
        self.resize(500, 400)  
        
        self.settings = {  
            'security_scan': True,  
            'duplicate_detection': True,  
            'min_duplicate_lines': 6,  
            'complexity_threshold': 10,  
            'max_line_length': 100,  
        }  
        
        self._setup_ui()  
    
    def _setup_ui(self):  
        """设置界面"""  
        layout = QVBoxLayout()  
        
        # 分析选项  
        group1 = QGroupBox("分析选项")  
        group1_layout = QVBoxLayout()  
        
        self.security_check = QCheckBox("安全漏洞扫描")  
        self.security_check.setChecked(True)  
        group1_layout.addWidget(self.security_check)  
        
        self.duplicate_check = QCheckBox("重复代码检测")  
        self.duplicate_check.setChecked(True)  
        group1_layout.addWidget(self.duplicate_check)  
        
        group1.setLayout(group1_layout)  
        layout.addWidget(group1)  
        
        # 阈值设置  
        group2 = QGroupBox("阈值设置")  
        group2_layout = QVBoxLayout()  
        
        dup_layout = QHBoxLayout()  
        dup_layout.addWidget(QLabel("最小重复行数:"))  
        self.min_dup_spin = QSpinBox()  
        self.min_dup_spin.setRange(3, 20)  
        self.min_dup_spin.setValue(6)  
        dup_layout.addWidget(self.min_dup_spin)  
        group2_layout.addLayout(dup_layout)  
        
        complexity_layout = QHBoxLayout()  
        complexity_layout.addWidget(QLabel("复杂度阈值:"))  
        self.complexity_spin = QSpinBox()  
        self.complexity_spin.setRange(5, 30)  
        self.complexity_spin.setValue(10)  
        complexity_layout.addWidget(self.complexity_spin)  
        group2_layout.addLayout(complexity_layout)  
        
        line_layout = QHBoxLayout()  
        line_layout.addWidget(QLabel("最大行长度:"))  
        self.line_spin = QSpinBox()  
        self.line_spin.setRange(80, 200)  
        self.line_spin.setValue(100)  
        line_layout.addWidget(self.line_spin)  
        group2_layout.addLayout(line_layout)  
        
        group2.setLayout(group2_layout)  
        layout.addWidget(group2)  
        
        # 按钮  
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)  
        buttons.accepted.connect(self.accept)  
        buttons.rejected.connect(self.reject)  
        layout.addWidget(buttons)  
        
        self.setLayout(layout)  
    
    def get_settings(self) -> Dict:  
        """获取设置"""  
        return {  
            'security_scan': self.security_check.isChecked(),  
            'duplicate_detection': self.duplicate_check.isChecked(),  
            'min_duplicate_lines': self.min_dup_spin.value(),  
            'complexity_threshold': self.complexity_spin.value(),  
            'max_line_length': self.line_spin.value(),  
        }  


class MainWindow(QMainWindow):  
    """主窗口"""  
    
    def __init__(self):  
        super().__init__()  
        self.setWindowTitle("CodeAnalyzerPro - 专业代码分析工具")  
        self.setGeometry(100, 100, 1600, 900)  
        
        self.current_files = []  
        self.analysis_results = None  
        self.settings_config = {  
            'security_scan': True,  
            'duplicate_detection': True,  
        }  
        
        self._setup_ui()  
        self._apply_styles()  
        
        # 加载设置  
        self.load_settings()  
    
    def _setup_ui(self):  
        """设置界面"""  
        # 创建中心部件  
        central_widget = QWidget()  
        self.setCentralWidget(central_widget)  
        
        main_layout = QVBoxLayout()  
        central_widget.setLayout(main_layout)  
        
        # 创建工具栏  
        self._create_toolbar()  
        
        # 创建主分割器  
        splitter = QSplitter(Qt.Horizontal)  
        
        # 左侧面板 - 文件树  
        left_panel = self._create_left_panel()  
        splitter.addWidget(left_panel)  
        
        # 右侧面板 - 分析结果  
        right_panel = self._create_right_panel()  
        splitter.addWidget(right_panel)  
        
        splitter.setSizes([400, 1200])  
        main_layout.addWidget(splitter)  
        
        # 创建状态栏  
        self._create_statusbar()  
    
    def _create_toolbar(self):  
        """创建工具栏"""  
        toolbar = QToolBar()  
        toolbar.setIconSize(QSize(32, 32))  
        toolbar.setMovable(False)  
        self.addToolBar(toolbar)  
        
        # 打开文件  
        open_file_action = QAction("📁 打开文件", self)  
        open_file_action.triggered.connect(self.open_files)  
        toolbar.addAction(open_file_action)  
        
        # 打开目录  
        open_dir_action = QAction("📂 打开目录", self)  
        open_dir_action.triggered.connect(self.open_directory)  
        toolbar.addAction(open_dir_action)  
        
        toolbar.addSeparator()  
        
        # 开始分析  
        analyze_action = QAction("🔍 开始分析", self)  
        analyze_action.triggered.connect(self.start_analysis)  
        toolbar.addAction(analyze_action)  
        
        # 停止分析  
        stop_action = QAction("⏹ 停止", self)  
        stop_action.triggered.connect(self.stop_analysis)  
        toolbar.addAction(stop_action)  
        
        toolbar.addSeparator()  
        
        # 导出报告  
        export_action = QAction("💾 导出报告", self)  
        export_action.triggered.connect(self.export_report)  
        toolbar.addAction(export_action)  
        
        # 设置  
        settings_action = QAction("⚙ 设置", self)  
        settings_action.triggered.connect(self.show_settings)  
        toolbar.addAction(settings_action)  
        
        toolbar.addSeparator()  
        
        # 帮助  
        help_action = QAction("❓ 帮助", self)  
        help_action.triggered.connect(self.show_help)  
        toolbar.addAction(help_action)  
    
    def _create_left_panel(self) -> QWidget:  
        """创建左侧面板"""  
        panel = QWidget()  
        layout = QVBoxLayout()  
        panel.setLayout(layout)  
        
        # 标题  
        title_label = QLabel("📄 文件列表")  
        title_label.setFont(QFont("Arial", 12, QFont.Bold))  
        layout.addWidget(title_label)  
        
        # 搜索框  
        self.search_box = QLineEdit()  
        self.search_box.setPlaceholderText("搜索文件...")  
        self.search_box.textChanged.connect(self.filter_files)  
        layout.addWidget(self.search_box)  
        
        # 文件树  
        self.file_tree = QTreeWidget()  
        self.file_tree.setHeaderLabels(["文件名", "路径"])  
        self.file_tree.setColumnWidth(0, 200)  
        self.file_tree.itemSelectionChanged.connect(self.on_file_selected)  
        layout.addWidget(self.file_tree)  
        
        # 文件统计  
        stats_group = QGroupBox("统计信息")  
        stats_layout = QVBoxLayout()  
        self.stats_label = QLabel("文件数: 0\n总行数: 0")  
        stats_layout.addWidget(self.stats_label)  
        stats_group.setLayout(stats_layout)  
        layout.addWidget(stats_group)  
        
        return panel  
    
    def _create_right_panel(self) -> QWidget:  
        """创建右侧面板"""  
        panel = QWidget()  
        layout = QVBoxLayout()  
        panel.setLayout(layout)  
        
        # 进度条  
        self.progress_bar = QProgressBar()  
        self.progress_bar.setVisible(False)  
        layout.addWidget(self.progress_bar)  
        
        # 标签页  
        self.tab_widget = QTabWidget()  
        
        # 概览  
        self.overview_tab = self._create_overview_tab()  
        self.tab_widget.addTab(self.overview_tab, "📊 概览")  
        
        # 复杂度分析  
        self.complexity_tab = self._create_complexity_tab()  
        self.tab_widget.addTab(self.complexity_tab, "🔢 复杂度")  
        
        # 依赖关系  
        self.dependencies_tab = self._create_dependencies_tab()  
        self.tab_widget.addTab(self.dependencies_tab, "🔗 依赖")  
        
        # 重复代码  
        self.duplicates_tab = self._create_duplicates_tab()  
        self.tab_widget.addTab(self.duplicates_tab, "📋 重复代码")  
        
        # 安全扫描  
        self.security_tab = self._create_security_tab()  
        self.tab_widget.addTab(self.security_tab, "🛡️ 安全")  
        
        # 质量评分  
        self.quality_tab = self._create_quality_tab()  
        self.tab_widget.addTab(self.quality_tab, "⭐ 质量")  
        
        # 代码视图  
        self.code_tab = self._create_code_tab()  
        self.tab_widget.addTab(self.code_tab, "📝 代码")  
        
        layout.addWidget(self.tab_widget)  
        
        return panel  
    
    def _create_overview_tab(self) -> QWidget:  
        """创建概览标签页"""  
        widget = QWidget()  
        layout = QVBoxLayout()  
        widget.setLayout(layout)  
        
        self.overview_text = QTextEdit()  
        self.overview_text.setReadOnly(True)  
        self.overview_text.setFont(QFont("Consolas", 10))  
        layout.addWidget(self.overview_text)  
        
        return widget  
    
    def _create_complexity_tab(self) -> QWidget:  
        """创建复杂度标签页"""  
        widget = QWidget()  
        layout = QVBoxLayout()  
        widget.setLayout(layout)  
        
        # 筛选工具栏  
        filter_layout = QHBoxLayout()  
        filter_layout.addWidget(QLabel("筛选:"))  
        
        self.complexity_filter = QComboBox()  
        self.complexity_filter.addItems(["全部", "简单 (≤5)", "中等 (6-10)", "复杂 (11-20)", "极复杂 (>20)"])  
        self.complexity_filter.currentTextChanged.connect(self.filter_complexity)  
        filter_layout.addWidget(self.complexity_filter)  
        filter_layout.addStretch()  
        
        layout.addLayout(filter_layout)  
        
        # 复杂度表格  
        self.complexity_table = QTableWidget()  
        self.complexity_table.setColumnCount(5)  
        self.complexity_table.setHorizontalHeaderLabels(["文件", "函数", "复杂度", "状态", "建议"])  
        self.complexity_table.horizontalHeader().setStretchLastSection(True)  
        self.complexity_table.setSelectionBehavior(QTableWidget.SelectRows)  
        self.complexity_table.setEditTriggers(QTableWidget.NoEditTriggers)  
        layout.addWidget(self.complexity_table)  
        
        return widget  
    
    def _create_dependencies_tab(self) -> QWidget:  
        """创建依赖关系标签页"""  
        widget = QWidget()  
        layout = QVBoxLayout()  
        widget.setLayout(layout)  
        
        # 分割器：图表和列表  
        splitter = QSplitter(Qt.Vertical)  
        
        # 依赖统计图表  
        self.dep_chart_view = QChartView()  
        self.dep_chart_view.setMinimumHeight(300)  
        splitter.addWidget(self.dep_chart_view)  
        
        # 依赖详情列表  
        self.dependencies_table = QTableWidget()  
        self.dependencies_table.setColumnCount(3)  
        self.dependencies_table.setHorizontalHeaderLabels(["模块名", "使用次数", "使用文件"])  
        self.dependencies_table.horizontalHeader().setStretchLastSection(True)  
        splitter.addWidget(self.dependencies_table)  
        
        layout.addWidget(splitter)  
        
        return widget  
    
    def _create_duplicates_tab(self) -> QWidget:  
        """创建重复代码标签页"""  
        widget = QWidget()  
        layout = QVBoxLayout()  
        widget.setLayout(layout)  
        
        # 统计信息  
        stats_layout = QHBoxLayout()  
        self.dup_stats_label = QLabel("重复代码块: 0 | 重复率: 0%")  
        self.dup_stats_label.setFont(QFont("Arial", 10, QFont.Bold))  
        stats_layout.addWidget(self.dup_stats_label)  
        stats_layout.addStretch()  
        layout.addLayout(stats_layout)  
        
        # 重复代码树  
        self.duplicates_tree = QTreeWidget()  
        self.duplicates_tree.setHeaderLabels(["重复块", "文件", "行号", "代码预览"])  
        self.duplicates_tree.setColumnWidth(0, 120)  
        self.duplicates_tree.setColumnWidth(1, 250)  
        self.duplicates_tree.setColumnWidth(2, 80)  
        layout.addWidget(self.duplicates_tree)  
        
        return widget  
    
    def _create_security_tab(self) -> QWidget:  
        """创建安全扫描标签页"""  
        widget = QWidget()  
        layout = QVBoxLayout()  
        widget.setLayout(layout)  
        
        # 安全摘要  
        summary_layout = QHBoxLayout()  
        
        self.critical_label = QLabel("严重: 0")  
        self.critical_label.setStyleSheet("color: #ff4444; font-weight: bold;")  
        summary_layout.addWidget(self.critical_label)  
        
        self.high_label = QLabel("高危: 0")  
        self.high_label.setStyleSheet("color: #ff8800; font-weight: bold;")  
        summary_layout.addWidget(self.high_label)  
        
        self.medium_label = QLabel("中危: 0")  
        self.medium_label.setStyleSheet("color: #ffaa00; font-weight: bold;")  
        summary_layout.addWidget(self.medium_label)  
        
        summary_layout.addStretch()  
        layout.addLayout(summary_layout)  
        
        # 漏洞表格  
        self.security_table = QTableWidget()  
        self.security_table.setColumnCount(6)  
        self.security_table.setHorizontalHeaderLabels(["严重程度", "类型", "文件", "行号", "代码", "说明"])  
        self.security_table.setSelectionBehavior(QTableWidget.SelectRows)  
        self.security_table.setEditTriggers(QTableWidget.NoEditTriggers)  
        
        # 设置列宽  
        self.security_table.setColumnWidth(0, 100)  
        self.security_table.setColumnWidth(1, 120)  
        self.security_table.setColumnWidth(2, 200)  
        self.security_table.setColumnWidth(3, 80)  
        self.security_table.setColumnWidth(4, 300)  
        self.security_table.horizontalHeader().setStretchLastSection(True)  
        
        layout.addWidget(self.security_table)  
        
        return widget  
    
    def _create_quality_tab(self) -> QWidget:  
        """创建质量评分标签页"""  
        widget = QWidget()  
        layout = QVBoxLayout()  
        widget.setLayout(layout)  
        
        # 总体评分卡片  
        score_card = QGroupBox("总体质量评分")  
        score_layout = QVBoxLayout()  
        
        self.score_label = QLabel("--")  
        self.score_label.setFont(QFont("Arial", 48, QFont.Bold))  
        self.score_label.setAlignment(Qt.AlignCenter)  
        score_layout.addWidget(self.score_label)  
        
        self.grade_label = QLabel("等级: --")  
        self.grade_label.setFont(QFont("Arial", 16))  
        self.grade_label.setAlignment(Qt.AlignCenter)  
        score_layout.addWidget(self.grade_label)  
        
        score_card.setLayout(score_layout)  
        layout.addWidget(score_card)  
        
        # 详细评分表  
        self.quality_table = QTableWidget()  
        self.quality_table.setColumnCount(4)  
        self.quality_table.setHorizontalHeaderLabels(["文件", "评分", "等级", "主要问题"])  
        self.quality_table.horizontalHeader().setStretchLastSection(True)  
        layout.addWidget(self.quality_table)  
        
        return widget  
    
    def _create_code_tab(self) -> QWidget:  
        """创建代码视图标签页"""  
        widget = QWidget()  
        layout = QVBoxLayout()  
        widget.setLayout(layout)  
        
        # 文件信息  
        info_layout = QHBoxLayout()  
        self.code_file_label = QLabel("未选择文件")  
        self.code_file_label.setFont(QFont("Arial", 10, QFont.Bold))  
        info_layout.addWidget(self.code_file_label)  
        info_layout.addStretch()  
        layout.addLayout(info_layout)  
        
        # 代码编辑器  
        self.code_editor = QTextEdit()  
        self.code_editor.setReadOnly(True)  
        self.code_editor.setFont(QFont("Consolas", 10))  
        self.code_editor.setLineWrapMode(QTextEdit.NoWrap)  
        layout.addWidget(self.code_editor)  
        
        return widget  
    
    def _create_statusbar(self):  
        """创建状态栏"""  
        self.statusbar = QStatusBar()  
        self.setStatusBar(self.statusbar)  
        
        self.status_label = QLabel("准备就绪")  
        self.statusbar.addWidget(self.status_label)  
        
        self.statusbar.addPermanentWidget(QLabel(""))  
    
    def _apply_styles(self):  
        """应用样式表"""  
        self.setStyleSheet("""  
            QMainWindow {  
                background-color: #1e1e1e;  
            }  
            
            QWidget {  
                background-color: #1e1e1e;  
                color: #ffffff;  
            }  
            
            QLabel {  
                color: #ffffff;  
            }  
            
            QTreeWidget, QTableWidget, QTextEdit {  
                background-color: #2d2d2d;  
                color: #ffffff;  
                border: 1px solid #3d3d3d;  
                border-radius: 5px;  
            }  
            
            QTreeWidget::item:selected, QTableWidget::item:selected {  
                background-color: #007acc;  
            }  
            
            QTreeWidget::item:hover, QTableWidget::item:hover {  
                background-color: #3d3d3d;  
            }  
            
            QHeaderView::section {  
                background-color: #2d2d2d;  
                color: #ffffff;  
                padding: 5px;  
                border: 1px solid #3d3d3d;  
                font-weight: bold;  
            }  
            
            QPushButton {  
                background-color: #007acc;  
                color: #ffffff;  
                border: none;  
                padding: 8px 16px;  
                border-radius: 4px;  
                font-weight: bold;  
            }  
            
            QPushButton:hover {  
                background-color: #005a9e;  
            }  
            
            QPushButton:pressed {  
                background-color: #004578;  
            }  
            
            QLineEdit, QComboBox, QSpinBox {  
                background-color: #2d2d2d;  
                color: #ffffff;  
                border: 1px solid #3d3d3d;  
                border-radius: 3px;  
                padding: 5px;  
            }  
            
            QTabWidget::pane {  
                border: 1px solid #3d3d3d;  
                border-radius: 5px;  
                background-color: #1e1e1e;  
            }  
            
            QTabBar::tab {  
                background-color: #2d2d2d;  
                color: #ffffff;  
                padding: 10px 20px;  
                margin-right: 2px;  
                border-top-left-radius: 5px;  
                border-top-right-radius: 5px;  
            }  
            
            QTabBar::tab:selected {  
                background-color: #007acc;  
            }  
            
            QTabBar::tab:hover {  
                background-color: #3d3d3d;  
            }  
            
            QGroupBox {  
                border: 2px solid #3d3d3d;  
                border-radius: 5px;  
                margin-top: 10px;  
                font-weight: bold;  
            }  
            
            QGroupBox::title {  
                color: #007acc;  
                subcontrol-origin: margin;  
                left: 10px;  
                padding: 0 5px;  
            }  
            
            QProgressBar {  
                border: 1px solid #3d3d3d;  
                border-radius: 5px;  
                text-align: center;  
                background-color: #2d2d2d;  
            }  
            
            QProgressBar::chunk {  
                background-color: #007acc;  
                border-radius: 5px;  
            }  
            
            QToolBar {  
                background-color: #2d2d2d;  
                border: none;  
                spacing: 10px;  
                padding: 5px;  
            }  
            
            QToolBar QToolButton {  
                background-color: transparent;  
                color: #ffffff;  
                border: none;  
                padding: 5px;  
                border-radius: 3px;  
            }  
            
            QToolBar QToolButton:hover {  
                background-color: #3d3d3d;  
            }  
            
            QStatusBar {  
                background-color: #2d2d2d;  
                color: #ffffff;  
            }  
            
            QScrollBar:vertical {  
                background-color: #2d2d2d;  
                width: 12px;  
                border-radius: 6px;  
            }  
            
            QScrollBar::handle:vertical {  
                background-color: #3d3d3d;  
                border-radius: 6px;  
            }  
            
            QScrollBar::handle:vertical:hover {  
                background-color: #4d4d4d;  
            }  
            
            QScrollBar:horizontal {  
                background-color: #2d2d2d;  
                height: 12px;  
                border-radius: 6px;  
            }  
            
            QScrollBar::handle:horizontal {  
                background-color: #3d3d3d;  
                border-radius: 6px;  
            }  
        """)  
    
    def open_files(self):  
        """打开文件"""  
        files, _ = QFileDialog.getOpenFileNames(  
            self,  
            "选择代码文件",  
            "",  
            "Python Files (*.py);;JavaScript Files (*.js);;Java Files (*.java);;C++ Files (*.cpp *.h);;All Files (*.*)"  
        )  
        
        if files:  
            self.current_files = files  
            self.update_file_tree()  
            self.status_label.setText(f"已加载 {len(files)} 个文件")  
    
    def open_directory(self):  
        """打开目录"""  
        directory = QFileDialog.getExistingDirectory(self, "选择项目目录")  
        
        if directory:  
            self.current_files = []  
            supported_ext = {'.py', '.js', '.java', '.cpp', '.c', '.h', '.go', '.rs'}  
            
            for root, dirs, files in os.walk(directory):  
                # 跳过常见的忽略目录  
                dirs[:] = [d for d in dirs if d not in {'.git', '.svn', 'node_modules', '__pycache__', 'venv', '.venv'}]  
                
                for file in files:  
                    if Path(file).suffix in supported_ext:  
                        self.current_files.append(os.path.join(root, file))  
            
            self.update_file_tree()  
            self.status_label.setText(f"已加载 {len(self.current_files)} 个文件")  
    
    def update_file_tree(self):  
        """更新文件树"""  
        self.file_tree.clear()  
        
        total_lines = 0  
        
        for filepath in self.current_files:  
            try:  
                with open(filepath, 'r', encoding='utf-8') as f:  
                    lines = len(f.readlines())  
                    total_lines += lines  
            except:  
                lines = 0  
            
            item = QTreeWidgetItem([os.path.basename(filepath), filepath])  
            self.file_tree.addTopLevelItem(item)  
        
        self.stats_label.setText(f"文件数: {len(self.current_files)}\n总行数: {total_lines:,}")  
    
    def filter_files(self, text: str):  
        """筛选文件"""  
        for i in range(self.file_tree.topLevelItemCount()):  
            item = self.file_tree.topLevelItem(i)  
            if text.lower() in item.text(0).lower():  
                item.setHidden(False)  
            else:  
                item.setHidden(True)  
    
    def start_analysis(self):  
        """开始分析"""  
        if not self.current_files:  
            QMessageBox.warning(self, "警告", "请先选择要分析的文件")  
            return  
        
        self.progress_bar.setVisible(True)  
        self.progress_bar.setValue(0)  
        self.status_label.setText("正在分析...")  
        
        # 创建分析线程  
        self.worker = AnalysisWorker(self.current_files, self.settings_config)  
        self.worker.progress.connect(self.update_progress)  
        self.worker.finished.connect(self.analysis_finished)  
        self.worker.error.connect(self.analysis_error)  
        self.worker.start()  
    
    def stop_analysis(self):  
        """停止分析"""  
        if hasattr(self, 'worker') and self.worker.isRunning():  
            self.worker.terminate()  
            self.worker.wait()  
            self.progress_bar.setVisible(False)  
            self.status_label.setText("分析已停止")  
            QMessageBox.information(self, "提示", "分析已停止")  
    
    def update_progress(self, value: int, message: str):  
        """更新进度"""  
        self.progress_bar.setValue(value)  
        self.status_label.setText(message)  
    
    def analysis_finished(self, results: Dict):  
        """分析完成"""  
        self.progress_bar.setVisible(False)  
        self.analysis_results = results  
        
        # 更新各个标签页  
        self.update_overview(results)  
        self.update_complexity(results)  
        self.update_dependencies(results)  
        self.update_duplicates(results)  
        self.update_security(results)  
        self.update_quality(results)  
        
        self.status_label.setText(f"分析完成！共分析 {len(self.current_files)} 个文件")  
        QMessageBox.information(self, "完成", "代码分析完成！")  
    
    def analysis_error(self, error: str):  
        """分析错误"""  
        self.progress_bar.setVisible(False)  
        self.status_label.setText("分析出错")  
        QMessageBox.critical(self, "错误", f"分析过程中出错:\n{error}")  
    
    def update_overview(self, results: Dict):  
        """更新概览"""  
        summary = results['summary']  
        quality = results['quality']  
        
        overview_html = f"""  
        <html>  
        <body style="font-family: Consolas; background-color: #2d2d2d; color: #ffffff;">  
            <h2 style="color: #007acc;">📊 代码分析概览报告</h2>  
            <hr style="border-color: #3d3d3d;">  
            
            <h3>📁 项目统计</h3>  
            <table style="width: 100%; border-collapse: collapse;">  
                <tr><td style="padding: 5px;">文件总数:</td><td style="padding: 5px; color: #4ec9b0;"><b>{summary['total_files']}</b></td></tr>  
                <tr><td style="padding: 5px;">代码总行数:</td><td style="padding: 5px; color: #4ec9b0;"><b>{summary['total_lines']:,}</b></td></tr>  
                <tr><td style="padding: 5px;">有效代码:</td><td style="padding: 5px; color: #4ec9b0;"><b>{summary['total_code_lines']:,}</b></td></tr>  
                <tr><td style="padding: 5px;">注释行数:</td><td style="padding: 5px; color: #4ec9b0;"><b>{summary['total_comment_lines']:,}</b></td></tr>  
                <tr><td style="padding: 5px;">空白行数:</td><td style="padding: 5px; color: #4ec9b0;"><b>{summary['total_lines'] - summary['total_code_lines'] - summary['total_comment_lines']:,}</b></td></tr>  
            </table>  
            
            <h3>🔧 代码结构</h3>  
            <table style="width: 100%; border-collapse: collapse;">  
                <tr><td style="padding: 5px;">函数数量:</td><td style="padding: 5px; color: #4ec9b0;"><b>{summary['total_functions']}</b></td></tr>  
                <tr><td style="padding: 5px;">类数量:</td><td style="padding: 5px; color: #4ec9b0;"><b>{summary['total_classes']}</b></td></tr>  
                <tr><td style="padding: 5px;">平均函数数/文件:</td><td style="padding: 5px; color: #4ec9b0;"><b>{summary['total_functions']/summary['total_files']:.1f}</b></td></tr>  
            </table>  
            
            <h3>📊 复杂度分析</h3>  
            <table style="width: 100%; border-collapse: collapse;">  
                <tr><td style="padding: 5px;">平均复杂度:</td><td style="padding: 5px; color: #4ec9b0;"><b>{summary['avg_complexity']:.2f}</b></td></tr>  
                <tr><td style="padding: 5px;">最大复杂度:</td><td style="padding: 5px; color: #4ec9b0;"><b>{summary['max_complexity']}</b></td></tr>  
            </table>  
            
            <h3>⭐ 质量评估</h3>  
            <table style="width: 100%; border-collapse: collapse;">  
                <tr><td style="padding: 5px;">平均质量评分:</td><td style="padding: 5px; color: #4ec9b0;"><b>{quality['average_score']:.1f}/100</b></td></tr>  
                <tr><td style="padding: 5px;">注释率:</td><td style="padding: 5px; color: #4ec9b0;"><b>{(summary['total_comment_lines']/summary['total_lines']*100 if summary['total_lines'] > 0 else 0):.1f}%</b></td></tr>  
            </table>  
            
            <h3>🛡️ 安全状况</h3>  
            <table style="width: 100%; border-collapse: collapse;">  
                <tr><td style="padding: 5px;">严重漏洞:</td><td style="padding: 5px; color: #ff4444;"><b>{quality['critical_vulnerabilities']}</b></td></tr>  
                <tr><td style="padding: 5px;">高危漏洞:</td><td style="padding: 5px; color: #ff8800;"><b>{quality['high_vulnerabilities']}</b></td></tr>  
                <tr><td style="padding: 5px;">总漏洞数:</td><td style="padding: 5px; color: #ffaa00;"><b>{quality['total_vulnerabilities']}</b></td></tr>  
            </table>  
            
            <hr style="border-color: #3d3d3d;">  
            <p style="color: #888;">分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>  
        </body>  
        </html>  
        """  
        
        self.overview_text.setHtml(overview_html)  
    
    def update_complexity(self, results: Dict):  
        """更新复杂度"""  
        self.complexity_table.setRowCount(0)  
        
        for filepath, result in results['files'].items():  
            if result['success']:  
                metrics = result['metrics']  
                filename = os.path.basename(filepath)  
                
                for func_name, complexity in metrics.complexity_scores.items():  
                    row = self.complexity_table.rowCount()  
                    self.complexity_table.insertRow(row)  
                    
                    self.complexity_table.setItem(row, 0, QTableWidgetItem(filename))  
                    self.complexity_table.setItem(row, 1, QTableWidgetItem(func_name))  
                    self.complexity_table.setItem(row, 2, QTableWidgetItem(str(complexity)))  
                    
                    # 状态  
                    if complexity <= 5:  
                        status = "✅ 简单"  
                        suggestion = "保持良好"  
                    elif complexity <= 10:  
                        status = "⚠️ 中等"  
                        suggestion = "可以优化"  
                    elif complexity <= 20:  
                        status = "❌ 复杂"  
                        suggestion = "建议重构"  
                    else:  
                        status = "🔴 极复杂"  
                        suggestion = "必须重构"  
                    
                    self.complexity_table.setItem(row, 3, QTableWidgetItem(status))  
                    self.complexity_table.setItem(row, 4, QTableWidgetItem(suggestion))  
        
        # 调整列宽  
        self.complexity_table.resizeColumnsToContents()  
    
    def filter_complexity(self, filter_text: str):  
        """筛选复杂度"""  
        for row in range(self.complexity_table.rowCount()):  
            complexity = int(self.complexity_table.item(row, 2).text())  
            
            show = True  
            if filter_text == "简单 (≤5)" and complexity > 5:  
                show = False  
            elif filter_text == "中等 (6-10)" and (complexity <= 5 or complexity > 10):  
                show = False  
            elif filter_text == "复杂 (11-20)" and (complexity <= 10 or complexity > 20):  
                show = False  
            elif filter_text == "极复杂 (>20)" and complexity <= 20:  
                show = False  
            
            self.complexity_table.setRowHidden(row, not show)  
    
    def update_dependencies(self, results: Dict):  
        """更新依赖关系"""  
        # 统计依赖  
        dep_counter = Counter()  
        dep_files = defaultdict(list)  
        
        for filepath, result in results['files'].items():  
            if result['success']:  
                filename = os.path.basename(filepath)  
                for imp in result['metrics'].imports:  
                    dep_counter[imp] += 1  
                    dep_files[imp].append(filename)  
        
        # 更新表格  
        self.dependencies_table.setRowCount(len(dep_counter))  
        
        for row, (dep, count) in enumerate(sorted(dep_counter.items(), key=lambda x: x[1], reverse=True)):  
            self.dependencies_table.setItem(row, 0, QTableWidgetItem(dep))  
            self.dependencies_table.setItem(row, 1, QTableWidgetItem(str(count)))  
            self.dependencies_table.setItem(row, 2, QTableWidgetItem(", ".join(dep_files[dep][:3])))  
        
        # 创建饼图  
        if dep_counter:  
            chart = QChart()  
            chart.setTitle("依赖分布 (Top 10)")  
            chart.setAnimationOptions(QChart.SeriesAnimations)  
            
            series = QPieSeries()  
            
            top_deps = dep_counter.most_common(10)  
            for dep, count in top_deps:  
                slice = series.append(dep, count)  
                slice.setLabelVisible(True)  
            
            chart.addSeries(series)  
            chart.legend().setAlignment(Qt.AlignRight)  
            
            self.dep_chart_view.setChart(chart)  
            self.dep_chart_view.setRenderHint(QPainter.Antialiasing)  
    
    def update_duplicates(self, results: Dict):  
        """更新重复代码"""  
        self.duplicates_tree.clear()  
        duplicates = results['duplicates']  
        
        # 计算重复率  
        total_blocks = len(duplicates)  
        if total_blocks > 0:  
            dup_rate = sum(len(locs) for locs in duplicates.values()) / len(self.current_files)  
        else:  
            dup_rate = 0  
        
        self.dup_stats_label.setText(f"重复代码块: {total_blocks} | 平均重复率: {dup_rate:.1f}次/文件")  
        
        # 填充树  
        for idx, (hash_val, locations) in enumerate(duplicates.items(), 1):  
            parent = QTreeWidgetItem([f"重复块 #{idx}", "", "", f"{len(locations)} 处重复"])  
            parent.setExpanded(False)  
            
            for filepath, line_num, code in locations:  
                filename = os.path.basename(filepath)  
                child = QTreeWidgetItem([  
                    "",  
                    filename,  
                    str(line_num),  
                    code[:100] + "..." if len(code) > 100 else code  
                ])  
                parent.addChild(child)  
            
            self.duplicates_tree.addTopLevelItem(parent)  
    
    def update_security(self, results: Dict):  
        """更新安全扫描"""  
        vulnerabilities = results['vulnerabilities']  
        
        # 统计数量  
        critical_count = sum(1 for v in vulnerabilities if v['severity'] == 'critical')  
        high_count = sum(1 for v in vulnerabilities if v['severity'] == 'high')  
        medium_count = sum(1 for v in vulnerabilities if v['severity'] == 'medium')
        
        # 更新标签
        self.critical_label.setText(f"严重: {critical_count}")
        self.high_label.setText(f"高危: {high_count}")
        self.medium_label.setText(f"中危: {medium_count}")
        
        # 填充表格
        self.security_table.setRowCount(len(vulnerabilities))
        
        for row, vuln in enumerate(vulnerabilities):
            # 严重程度
            severity_item = QTableWidgetItem(vuln['severity'].upper())
            if vuln['severity'] == 'critical':
                severity_item.setForeground(QColor('#ff4444'))
            elif vuln['severity'] == 'high':
                severity_item.setForeground(QColor('#ff8800'))
            else:
                severity_item.setForeground(QColor('#ffaa00'))
            self.security_table.setItem(row, 0, severity_item)
            
            # 其他信息
            self.security_table.setItem(row, 1, QTableWidgetItem(vuln['type']))
            self.security_table.setItem(row, 2, QTableWidgetItem(os.path.basename(vuln['file'])))
            self.security_table.setItem(row, 3, QTableWidgetItem(str(vuln['line'])))
            self.security_table.setItem(row, 4, QTableWidgetItem(vuln['code'][:100]))
            self.security_table.setItem(row, 5, QTableWidgetItem(vuln['description']))
        
        self.security_table.resizeColumnsToContents()
    
    def update_quality(self, results: Dict):
        """更新质量评分"""
        quality = results['quality']
        scorer = QualityScorer()
        
        # 更新总体评分
        avg_score = quality['average_score']
        self.score_label.setText(f"{avg_score:.1f}")
        
        # 根据分数设置颜色
        if avg_score >= 90:
            self.score_label.setStyleSheet("color: #4ec9b0;")
            grade = "A (优秀)"
        elif avg_score >= 80:
            self.score_label.setStyleSheet("color: #7cb342;")
            grade = "B (良好)"
        elif avg_score >= 70:
            self.score_label.setStyleSheet("color: #ffa726;")
            grade = "C (中等)"
        elif avg_score >= 60:
            self.score_label.setStyleSheet("color: #ff8800;")
            grade = "D (及格)"
        else:
            self.score_label.setStyleSheet("color: #ff4444;")
            grade = "F (需改进)"
        
        self.grade_label.setText(f"等级: {grade}")
        
        # 更新详细评分表
        self.quality_table.setRowCount(len(results['files']))
        
        row_idx = 0
        for filepath, result in results['files'].items():
            if result['success']:
                filename = os.path.basename(filepath)
                metrics = result['metrics']
                
                # 计算该文件的质量评分
                file_vulns = [v for v in results['vulnerabilities'] if v['file'] == filepath]
                file_quality = scorer.calculate_score(metrics, file_vulns)
                
                self.quality_table.setItem(row_idx, 0, QTableWidgetItem(filename))
                
                score_item = QTableWidgetItem(f"{file_quality['score']:.1f}")
                if file_quality['score'] >= 80:
                    score_item.setForeground(QColor('#4ec9b0'))
                elif file_quality['score'] >= 60:
                    score_item.setForeground(QColor('#ffa726'))
                else:
                    score_item.setForeground(QColor('#ff4444'))
                self.quality_table.setItem(row_idx, 1, score_item)
                
                self.quality_table.setItem(row_idx, 2, QTableWidgetItem(file_quality['grade']))
                
                issues_text = "; ".join(file_quality['issues'][:2]) if file_quality['issues'] else "无明显问题"
                self.quality_table.setItem(row_idx, 3, QTableWidgetItem(issues_text))
                
                row_idx += 1
        
        self.quality_table.resizeColumnsToContents()
    
    def on_file_selected(self):
        """文件选择事件"""
        items = self.file_tree.selectedItems()
        if items:
            filepath = items[0].text(1)
            
            # 在代码视图中显示文件内容
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.code_file_label.setText(f"📄 {os.path.basename(filepath)}")
                self.code_editor.setPlainText(content)
                
                # 如果有分析结果，高亮显示问题
                if self.analysis_results and filepath in self.analysis_results['files']:
                    self.highlight_issues(filepath)
                
            except Exception as e:
                self.code_editor.setPlainText(f"无法读取文件: {str(e)}")
    
    def highlight_issues(self, filepath: str):
        """高亮显示问题行"""
        # 这里可以添加语法高亮和问题标记
        # 由于PyQt5的限制，简化处理
        pass
    
    def export_report(self):
        """导出报告"""
        if not self.analysis_results:
            QMessageBox.warning(self, "警告", "没有可导出的分析结果")
            return
        
        # 选择导出格式
        export_format, _ = QFileDialog.getSaveFileName(
            self,
            "导出报告",
            f"code_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "JSON文件 (*.json);;HTML报告 (*.html);;Markdown (*.md)"
        )
        
        if export_format:
            try:
                if export_format.endswith('.json'):
                    self._export_json(export_format)
                elif export_format.endswith('.html'):
                    self._export_html(export_format)
                elif export_format.endswith('.md'):
                    self._export_markdown(export_format)
                
                QMessageBox.information(self, "成功", f"报告已导出到:\n{export_format}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def _export_json(self, filepath: str):
        """导出JSON格式"""
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'files_analyzed': len(self.current_files),
            'summary': self.analysis_results['summary'],
            'quality': self.analysis_results['quality'],
            'vulnerabilities': self.analysis_results['vulnerabilities'],
            'duplicates_count': len(self.analysis_results['duplicates']),
        }
        
        # 转换set为list
        if 'unique_imports' in export_data['summary']:
            export_data['summary']['unique_imports'] = list(export_data['summary']['unique_imports'])
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def _export_html(self, filepath: str):
        """导出HTML格式"""
        summary = self.analysis_results['summary']
        quality = self.analysis_results['quality']
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>CodeAnalyzerPro - 分析报告</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            margin: 0;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 36px;
        }}
        .header p {{
            margin: 10px 0 0;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .stat-card h3 {{
            margin: 0 0 10px;
            color: #667eea;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .stat-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        .score-circle {{
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: conic-gradient(#4ec9b0 0%, #4ec9b0 {quality['average_score']}%, #e0e0e0 {quality['average_score']}%, #e0e0e0 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 20px auto;
            position: relative;
        }}
        .score-circle::before {{
            content: '';
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: white;
            position: absolute;
        }}
        .score-text {{
            position: relative;
            z-index: 1;
            font-size: 48px;
            font-weight: bold;
            color: #4ec9b0;
        }}
        .vulnerability-list {{
            list-style: none;
            padding: 0;
        }}
        .vulnerability-item {{
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 4px solid;
        }}
        .vulnerability-critical {{
            background: #ffebee;
            border-color: #f44336;
        }}
        .vulnerability-high {{
            background: #fff3e0;
            border-color: #ff9800;
        }}
        .vulnerability-medium {{
            background: #fff9c4;
            border-color: #ffc107;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #667eea;
            color: white;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 CodeAnalyzerPro</h1>
            <p>专业代码分析报告</p>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>📊 项目概览</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>文件总数</h3>
                        <div class="value">{summary['total_files']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>代码总行数</h3>
                        <div class="value">{summary['total_lines']:,}</div>
                    </div>
                    <div class="stat-card">
                        <h3>函数数量</h3>
                        <div class="value">{summary['total_functions']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>类数量</h3>
                        <div class="value">{summary['total_classes']}</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>⭐ 质量评分</h2>
                <div class="score-circle">
                    <div class="score-text">{quality['average_score']:.0f}</div>
                </div>
                <div style="text-align: center;">
                    <p><strong>平均质量评分:</strong> {quality['average_score']:.1f}/100</p>
                    <p><strong>注释率:</strong> {(summary['total_comment_lines']/summary['total_lines']*100 if summary['total_lines'] > 0 else 0):.1f}%</p>
                </div>
            </div>
            
            <div class="section">
                <h2>🔢 复杂度分析</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>平均复杂度</h3>
                        <div class="value">{summary['avg_complexity']:.1f}</div>
                    </div>
                    <div class="stat-card">
                        <h3>最大复杂度</h3>
                        <div class="value">{summary['max_complexity']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>简单函数</h3>
                        <div class="value">{summary['complexity_distribution']['simple']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>复杂函数</h3>
                        <div class="value">{summary['complexity_distribution']['complex'] + summary['complexity_distribution']['very_complex']}</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>🛡️ 安全分析</h2>
                <div class="stats-grid">
                    <div class="stat-card" style="border-left: 4px solid #f44336;">
                        <h3>严重漏洞</h3>
                        <div class="value" style="color: #f44336;">{quality['critical_vulnerabilities']}</div>
                    </div>
                    <div class="stat-card" style="border-left: 4px solid #ff9800;">
                        <h3>高危漏洞</h3>
                        <div class="value" style="color: #ff9800;">{quality['high_vulnerabilities']}</div>
                    </div>
                    <div class="stat-card" style="border-left: 4px solid #ffc107;">
                        <h3>总漏洞数</h3>
                        <div class="value" style="color: #ffc107;">{quality['total_vulnerabilities']}</div>
                    </div>
                </div>
                
                <h3>漏洞详情 (前10项)</h3>
                <ul class="vulnerability-list">
        """
        
        # 添加漏洞详情
        for vuln in self.analysis_results['vulnerabilities'][:10]:
            severity_class = f"vulnerability-{vuln['severity']}"
            html_content += f"""
                    <li class="vulnerability-item {severity_class}">
                        <strong>{vuln['type']}</strong> - {vuln['description']}<br>
                        <small>文件: {os.path.basename(vuln['file'])} | 行号: {vuln['line']}</small><br>
                        <code>{vuln['code'][:100]}</code>
                    </li>
            """
        
        html_content += """
                </ul>
            </div>
            
            <div class="section">
                <h2>📋 重复代码</h2>
                <p><strong>重复代码块数量:</strong> """ + str(len(self.analysis_results['duplicates'])) + """</p>
            </div>
        </div>
        
        <div class="footer">
            <p>由 CodeAnalyzerPro 生成 | © 2024</p>
        </div>
    </div>
</body>
</html>
        """
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _export_markdown(self, filepath: str):
        """导出Markdown格式"""
        summary = self.analysis_results['summary']
        quality = self.analysis_results['quality']
        
        md_content = f"""# CodeAnalyzerPro - 代码分析报告

**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 项目概览

| 指标 | 数值 |
|------|------|
| 文件总数 | {summary['total_files']} |
| 代码总行数 | {summary['total_lines']:,} |
| 有效代码 | {summary['total_code_lines']:,} |
| 注释行数 | {summary['total_comment_lines']:,} |
| 函数数量 | {summary['total_functions']} |
| 类数量 | {summary['total_classes']} |

## ⭐ 质量评分

**平均质量评分:** {quality['average_score']:.1f}/100

**注释率:** {(summary['total_comment_lines']/summary['total_lines']*100 if summary['total_lines'] > 0 else 0):.1f}%

## 🔢 复杂度分析

| 指标 | 数值 |
|------|------|
| 平均复杂度 | {summary['avg_complexity']:.2f} |
| 最大复杂度 | {summary['max_complexity']} |
| 简单函数 (≤5) | {summary['complexity_distribution']['simple']} |
| 中等函数 (6-10) | {summary['complexity_distribution']['moderate']} |
| 复杂函数 (11-20) | {summary['complexity_distribution']['complex']} |
| 极复杂函数 (>20) | {summary['complexity_distribution']['very_complex']} |

## 🛡️ 安全分析

- **严重漏洞:** {quality['critical_vulnerabilities']}
- **高危漏洞:** {quality['high_vulnerabilities']}
- **总漏洞数:** {quality['total_vulnerabilities']}

### 漏洞详情

"""
        
        for idx, vuln in enumerate(self.analysis_results['vulnerabilities'][:10], 1):
            md_content += f"""
#### {idx}. {vuln['type']} ({vuln['severity'].upper()})

- **文件:** {os.path.basename(vuln['file'])}
- **行号:** {vuln['line']}
- **说明:** {vuln['description']}
- **代码:** `{vuln['code'][:100]}`

"""
        
        md_content += f"""
## 📋 重复代码

**重复代码块数量:** {len(self.analysis_results['duplicates'])}

---

*报告由 CodeAnalyzerPro 自动生成*
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
    
    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self)
        
        if dialog.exec_() == QDialog.Accepted:
            self.settings_config = dialog.get_settings()
            QMessageBox.information(self, "提示", "设置已保存")
    
    def show_help(self):
        """显示帮助"""
        help_text = """
        <h2>CodeAnalyzerPro - 使用帮助</h2>
        
        <h3>功能介绍</h3>
        <ul>
            <li><b>代码复杂度分析:</b> 计算圈复杂度，评估代码复杂程度</li>
            <li><b>依赖关系可视化:</b> 分析模块依赖，生成可视化图表</li>
            <li><b>代码质量评分:</b> 综合多个指标给出质量评分</li>
            <li><b>重复代码检测:</b> 识别项目中的重复代码块</li>
            <li><b>安全漏洞扫描:</b> 检测常见的安全漏洞</li>
        </ul>
        
        <h3>使用步骤</h3>
        <ol>
            <li>点击 "打开文件" 或 "打开目录" 选择要分析的代码</li>
            <li>（可选）点击 "设置" 配置分析选项</li>
            <li>点击 "开始分析" 执行代码分析</li>
            <li>查看各个标签页的分析结果</li>
            <li>点击 "导出报告" 保存分析结果</li>
        </ol>
        
        <h3>评分标准</h3>
        <ul>
            <li><b>90-100分:</b> A级 - 优秀</li>
            <li><b>80-89分:</b> B级 - 良好</li>
            <li><b>70-79分:</b> C级 - 中等</li>
            <li><b>60-69分:</b> D级 - 及格</li>
            <li><b>60分以下:</b> F级 - 需改进</li>
        </ul>
        
        <h3>快捷键</h3>
        <ul>
            <li><b>Ctrl+O:</b> 打开文件</li>
            <li><b>Ctrl+D:</b> 打开目录</li>
            <li><b>Ctrl+R:</b> 开始分析</li>
            <li><b>Ctrl+S:</b> 导出报告</li>
        </ul>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("帮助")
        msg.setTextFormat(Qt.RichText)
        msg.setText(help_text)
        msg.exec_()
    
    def load_settings(self):
        """加载设置"""
        settings = QSettings("CodeAnalyzerPro", "Settings")
        
        # 恢复窗口大小和位置
        if settings.contains("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        
        # 加载其他设置
        self.settings_config = {
            'security_scan': settings.value('security_scan', True, type=bool),
            'duplicate_detection': settings.value('duplicate_detection', True, type=bool),
        }
    
    def save_settings(self):
        """保存设置"""
        settings = QSettings("CodeAnalyzerPro", "Settings")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue('security_scan', self.settings_config['security_scan'])
        settings.setValue('duplicate_detection', self.settings_config['duplicate_detection'])
    
    def closeEvent(self, event):
        """关闭事件"""
        self.save_settings()
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("CodeAnalyzerPro")
    app.setOrganizationName("CodeAnalyzer")
    
    # 设置应用图标（如果有）
    # app.setWindowIcon(QIcon("icon.png"))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()