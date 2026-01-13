#!/usr/bin/env python3  
# -*- coding: utf-8 -*-  
"""  
DatabaseManagerPro - 专业数据库管理工具 (PyQt5版本)  
功能: 多数据库支持、SQL编辑器、数据导入导出、备份恢复、性能监控  
作者：LYP
GitHub：https://github.com/lyp0746
邮箱：1610369302@qq.com
版本: 2.0.0  
"""  

import sys  
import json  
import csv  
import sqlite3  
import re  
import threading  
import time  
from datetime import datetime  
from pathlib import Path  
from typing import Optional, Dict, List, Any  

from PyQt5.QtWidgets import (  
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,  
    QSplitter, QTabWidget, QTreeWidget, QTreeWidgetItem, QTableWidget,  
    QTableWidgetItem, QPushButton, QLabel, QLineEdit, QTextEdit,  
    QComboBox, QSpinBox, QGroupBox, QFileDialog, QMessageBox,  
    QDialog, QDialogButtonBox, QProgressBar, QStatusBar, QMenuBar,  
    QMenu, QAction, QToolBar, QListWidget, QCheckBox, QRadioButton,  
    QButtonGroup, QScrollArea, QFrame, QHeaderView, QPlainTextEdit  
)  
from PyQt5.QtCore import (  
    Qt, QThread, pyqtSignal, QTimer, QSettings, QSize, QRect  
)  
from PyQt5.QtGui import (  
    QFont, QColor, QSyntaxHighlighter, QTextCharFormat, QPalette,  
    QIcon, QPixmap, QPainter, QTextCursor, QKeySequence  
)  

try:  
    import pymysql  
    MYSQL_AVAILABLE = True  
except ImportError:  
    MYSQL_AVAILABLE = False  

try:  
    import psycopg2  
    POSTGRESQL_AVAILABLE = True  
except ImportError:  
    POSTGRESQL_AVAILABLE = False  

try:  
    import pandas as pd  
    PANDAS_AVAILABLE = True  
except ImportError:  
    PANDAS_AVAILABLE = False  


# ==================== 数据库连接管理 ====================  

class DatabaseConnection:  
    """数据库连接管理类"""  
    
    def __init__(self, db_type: str, **kwargs):  
        self.db_type = db_type  
        self.connection = None  
        self.kwargs = kwargs  
        self.connected = False  
        
    def connect(self) -> bool:  
        """建立数据库连接"""  
        try:  
            if self.db_type == 'sqlite':  
                self.connection = sqlite3.connect(  
                    self.kwargs['database'],  
                    check_same_thread=False,  
                    timeout=10  
                )  
                self.connection.row_factory = sqlite3.Row  
                
            elif self.db_type == 'mysql':  
                if not MYSQL_AVAILABLE:  
                    raise Exception("请安装 pymysql: pip install pymysql")  
                self.connection = pymysql.connect(  
                    host=self.kwargs.get('host', 'localhost'),  
                    port=int(self.kwargs.get('port', 3306)),  
                    user=self.kwargs['user'],  
                    password=self.kwargs['password'],  
                    database=self.kwargs['database'],  
                    charset='utf8mb4',  
                    connect_timeout=10  
                )  
                
            elif self.db_type == 'postgresql':  
                if not POSTGRESQL_AVAILABLE:  
                    raise Exception("请安装 psycopg2: pip install psycopg2-binary")  
                self.connection = psycopg2.connect(  
                    host=self.kwargs.get('host', 'localhost'),  
                    port=int(self.kwargs.get('port', 5432)),  
                    user=self.kwargs['user'],  
                    password=self.kwargs['password'],  
                    database=self.kwargs['database'],  
                    connect_timeout=10  
                )  
                
            self.connected = True  
            return True  
            
        except Exception as e:  
            self.connected = False  
            raise Exception(f"连接失败: {str(e)}")  
    
    def execute_query(self, query: str, params: tuple = None) -> Dict[str, Any]:  
        """执行SQL查询"""  
        if not self.connected:  
            raise Exception("数据库未连接")  
        
        cursor = self.connection.cursor()  
        try:  
            if params:  
                cursor.execute(query, params)  
            else:  
                cursor.execute(query)  
            
            # 判断是否是查询语句  
            query_upper = query.strip().upper()  
            is_select = any(query_upper.startswith(kw) for kw in   
                          ['SELECT', 'SHOW', 'DESCRIBE', 'DESC', 'EXPLAIN', 'PRAGMA'])  
            
            if is_select:  
                columns = [desc[0] for desc in cursor.description] if cursor.description else []  
                rows = cursor.fetchall()  
                
                if self.db_type == 'sqlite':  
                    rows = [dict(row) for row in rows]  
                    
                return {  
                    'type': 'select',  
                    'columns': columns,  
                    'rows': rows,  
                    'rowcount': len(rows)  
                }  
            else:  
                self.connection.commit()  
                return {  
                    'type': 'modify',  
                    'affected_rows': cursor.rowcount  
                }  
                
        except Exception as e:  
            self.connection.rollback()  
            raise e  
        finally:  
            cursor.close()  
    
    def get_tables(self) -> List[str]:  
        """获取所有表名"""  
        try:  
            if self.db_type == 'sqlite':  
                query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"  
            elif self.db_type == 'mysql':  
                query = "SHOW TABLES"  
            elif self.db_type == 'postgresql':  
                query = "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"  
            
            result = self.execute_query(query)  
            
            if self.db_type == 'sqlite':  
                return [row['name'] for row in result['rows']]  
            else:  
                return [row[0] for row in result['rows']]  
                
        except Exception as e:  
            print(f"获取表列表失败: {e}")  
            return []  
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:  
        """获取表详细信息"""  
        try:  
            # 获取表结构  
            if self.db_type == 'sqlite':  
                structure = self.execute_query(f"PRAGMA table_info({table_name})")  
            elif self.db_type == 'mysql':  
                structure = self.execute_query(f"DESCRIBE {table_name}")  
            elif self.db_type == 'postgresql':  
                query = f"""  
                    SELECT column_name, data_type, is_nullable, column_default  
                    FROM information_schema.columns  
                    WHERE table_name = '{table_name}'  
                    ORDER BY ordinal_position  
                """  
                structure = self.execute_query(query)  
            
            # 获取行数  
            count_result = self.execute_query(f"SELECT COUNT(*) as cnt FROM {table_name}")  
            row_count = count_result['rows'][0][0] if count_result['rows'] else 0  
            
            return {  
                'name': table_name,  
                'structure': structure,  
                'row_count': row_count  
            }  
            
        except Exception as e:  
            print(f"获取表信息失败: {e}")  
            return None  
    
    def get_database_size(self) -> str:  
        """获取数据库大小"""  
        try:  
            if self.db_type == 'sqlite':  
                file_path = Path(self.kwargs['database'])  
                if file_path.exists():  
                    size_bytes = file_path.stat().st_size  
                    return self._format_size(size_bytes)  
            elif self.db_type == 'mysql':  
                query = f"""  
                    SELECT SUM(data_length + index_length) as size  
                    FROM information_schema.TABLES  
                    WHERE table_schema = '{self.kwargs['database']}'  
                """  
                result = self.execute_query(query)  
                size_bytes = result['rows'][0][0] if result['rows'] else 0  
                return self._format_size(size_bytes)  
            elif self.db_type == 'postgresql':  
                query = f"SELECT pg_database_size('{self.kwargs['database']}') as size"  
                result = self.execute_query(query)  
                size_bytes = result['rows'][0][0] if result['rows'] else 0  
                return self._format_size(size_bytes)  
                
            return "未知"  
            
        except Exception:  
            return "未知"  
    
    def _format_size(self, size_bytes: int) -> str:  
        """格式化文件大小"""  
        for unit in ['B', 'KB', 'MB', 'GB']:  
            if size_bytes < 1024.0:  
                return f"{size_bytes:.2f} {unit}"  
            size_bytes /= 1024.0  
        return f"{size_bytes:.2f} TB"  
    
    def close(self):  
        """关闭连接"""  
        if self.connection:  
            try:  
                self.connection.close()  
            except:  
                pass  
            self.connected = False  


# ==================== SQL语法高亮 ====================  

class SQLHighlighter(QSyntaxHighlighter):  
    """SQL语法高亮器"""  
    
    def __init__(self, parent=None):  
        super().__init__(parent)  
        self.highlighting_rules = []  
        
        # 关键字格式  
        keyword_format = QTextCharFormat()  
        keyword_format.setForeground(QColor("#0000FF"))  
        keyword_format.setFontWeight(QFont.Bold)  
        
        keywords = [  
            'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE',  
            'CREATE', 'DROP', 'ALTER', 'TABLE', 'INDEX', 'VIEW',  
            'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'AS',  
            'AND', 'OR', 'NOT', 'NULL', 'IS', 'IN', 'BETWEEN',  
            'LIKE', 'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT',  
            'OFFSET', 'UNION', 'ALL', 'DISTINCT', 'CASE', 'WHEN',  
            'THEN', 'ELSE', 'END', 'PRIMARY', 'KEY', 'FOREIGN',  
            'UNIQUE', 'DEFAULT', 'CHECK', 'ASC', 'DESC', 'INTO',  
            'VALUES', 'SET', 'DATABASE', 'SCHEMA', 'CONSTRAINT'  
        ]  
        
        for word in keywords:  
            pattern = f'\\b{word}\\b'  
            self.highlighting_rules.append((re.compile(pattern, re.IGNORECASE), keyword_format))  
        
        # 函数格式  
        function_format = QTextCharFormat()  
        function_format.setForeground(QColor("#FF00FF"))  
        
        functions = [  
            'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'UPPER', 'LOWER',  
            'LENGTH', 'SUBSTRING', 'TRIM', 'NOW', 'DATE', 'TIME'  
        ]  
        
        for func in functions:  
            pattern = f'\\b{func}\\b'  
            self.highlighting_rules.append((re.compile(pattern, re.IGNORECASE), function_format))  
        
        # 字符串格式  
        string_format = QTextCharFormat()  
        string_format.setForeground(QColor("#008000"))  
        self.highlighting_rules.append((re.compile(r"'[^']*'"), string_format))  
        self.highlighting_rules.append((re.compile(r'"[^"]*"'), string_format))  
        
        # 数字格式  
        number_format = QTextCharFormat()  
        number_format.setForeground(QColor("#FF6600"))  
        self.highlighting_rules.append((re.compile(r'\b\d+\.?\d*\b'), number_format))  
        
        # 注释格式  
        comment_format = QTextCharFormat()  
        comment_format.setForeground(QColor("#808080"))  
        comment_format.setFontItalic(True)  
        self.highlighting_rules.append((re.compile(r'--[^\n]*'), comment_format))  
    
    def highlightBlock(self, text):  
        """高亮文本块"""  
        for pattern, format in self.highlighting_rules:  
            for match in pattern.finditer(text):  
                start = match.start()  
                length = match.end() - start  
                self.setFormat(start, length, format)  


# ==================== SQL编辑器 ====================  

class LineNumberArea(QWidget):  
    """行号区域"""  
    
    def __init__(self, editor):  
        super().__init__(editor)  
        self.code_editor = editor  
    
    def sizeHint(self):  
        return QSize(self.code_editor.line_number_area_width(), 0)  
    
    def paintEvent(self, event):  
        self.code_editor.line_number_area_paint_event(event)  


class SQLEditor(QPlainTextEdit):  
    """增强的SQL编辑器"""  
    
    executeRequested = pyqtSignal(str)  # 执行SQL信号  
    
    def __init__(self, parent=None):  
        super().__init__(parent)  
        self.setFont(QFont("Consolas", 11))  
        
        # 设置语法高亮  
        self.highlighter = SQLHighlighter(self.document())  
        
        # 设置Tab为4个空格  
        self.setTabStopDistance(40)  
        
        # 行号区域  
        self.line_number_area = LineNumberArea(self)  
        self.blockCountChanged.connect(self.update_line_number_area_width)  
        self.updateRequest.connect(self.update_line_number_area)  
        self.cursorPositionChanged.connect(self.highlight_current_line)  
        
        self.update_line_number_area_width(0)  
        self.highlight_current_line()  
    
    def keyPressEvent(self, event):  
        """处理键盘事件"""  
        # F5 或 Ctrl+Enter 执行SQL  
        if event.key() == Qt.Key_F5 or (event.key() == Qt.Key_Return and   
                                        event.modifiers() == Qt.ControlModifier):  
            self.executeRequested.emit(self.get_sql())  
            return  
        
        # Ctrl+/ 注释/取消注释  
        if event.key() == Qt.Key_Slash and event.modifiers() == Qt.ControlModifier:  
            self.toggle_comment()  
            return  
        
        # 自动缩进  
        if event.key() == Qt.Key_Return:  
            cursor = self.textCursor()  
            block = cursor.block()  
            text = block.text()  
            indent = len(text) - len(text.lstrip())  
            
            super().keyPressEvent(event)  
            
            # 添加相同的缩进  
            self.insertPlainText(' ' * indent)  
            return  
        
        super().keyPressEvent(event)  
    
    def get_sql(self) -> str:  
        """获取SQL文本"""  
        cursor = self.textCursor()  
        if cursor.hasSelection():  
            return cursor.selectedText().replace('\u2029', '\n')  
        return self.toPlainText()  
    
    def set_sql(self, sql: str):  
        """设置SQL文本"""  
        self.setPlainText(sql)  
    
    def toggle_comment(self):  
        """切换注释"""  
        cursor = self.textCursor()  
        start = cursor.selectionStart()  
        end = cursor.selectionEnd()  
        
        cursor.setPosition(start)  
        cursor.movePosition(QTextCursor.StartOfBlock)  
        cursor.setPosition(end, QTextCursor.KeepAnchor)  
        cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)  
        
        text = cursor.selectedText()  
        lines = text.split('\u2029')  
        
        # 判断是否所有行都已注释  
        all_commented = all(line.strip().startswith('--') for line in lines if line.strip())  
        
        new_lines = []  
        for line in lines:  
            if all_commented:  
                # 取消注释  
                new_lines.append(line.replace('--', '', 1).lstrip())  
            else:  
                # 添加注释  
                new_lines.append('-- ' + line)  
        
        cursor.insertText('\n'.join(new_lines))  
    
    def highlight_current_line(self):  
        """高亮当前行"""  
        extra_selections = []  
        
        if not self.isReadOnly():  
            selection = QTextEdit.ExtraSelection()  
            line_color = QColor(Qt.yellow).lighter(160)  
            selection.format.setBackground(line_color)  
            selection.format.setProperty(QTextCharFormat.FullWidthSelection, True)  
            selection.cursor = self.textCursor()  
            selection.cursor.clearSelection()  
            extra_selections.append(selection)  
        
        self.setExtraSelections(extra_selections)  
    
    def line_number_area_width(self):  
        """行号区域宽度"""  
        digits = len(str(max(1, self.blockCount())))  
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits  
        return space  
    
    def update_line_number_area_width(self, _):  
        """更新行号区域宽度"""  
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)  
    
    def update_line_number_area(self, rect, dy):  
        """更新行号区域"""  
        if dy:  
            self.line_number_area.scroll(0, dy)  
        else:  
            self.line_number_area.update(0, rect.y(),   
                                        self.line_number_area.width(),   
                                        rect.height())  
        
        if rect.contains(self.viewport().rect()):  
            self.update_line_number_area_width(0)  
    
    def resizeEvent(self, event):  
        """调整大小事件"""  
        super().resizeEvent(event)  
        
        cr = self.contentsRect()  
        self.line_number_area.setGeometry(  
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())  
        )  
    
    def line_number_area_paint_event(self, event):  
        """绘制行号"""  
        painter = QPainter(self.line_number_area)  
        painter.fillRect(event.rect(), QColor(240, 240, 240))  
        
        block = self.firstVisibleBlock()  
        block_number = block.blockNumber()  
        top = int(self.blockBoundingGeometry(block).translated(  
            self.contentOffset()).top())  
        bottom = top + int(self.blockBoundingRect(block).height())  
        
        while block.isValid() and top <= event.rect().bottom():  
            if block.isVisible() and bottom >= event.rect().top():  
                number = str(block_number + 1)  
                painter.setPen(Qt.black)  
                painter.drawText(0, top, self.line_number_area.width() - 2,  
                               self.fontMetrics().height(),  
                               Qt.AlignRight, number)  
            
            block = block.next()  
            top = bottom  
            bottom = top + int(self.blockBoundingRect(block).height())  
            block_number += 1  


# ==================== 查询执行线程 ====================  

class QueryThread(QThread):  
    """查询执行线程"""  
    
    finished = pyqtSignal(dict)  
    error = pyqtSignal(str)  
    
    def __init__(self, db_connection, sql):  
        super().__init__()  
        self.db_connection = db_connection  
        self.sql = sql  
        self.start_time = None  
    
    def run(self):  
        """执行查询"""  
        try:  
            self.start_time = time.time()  
            result = self.db_connection.execute_query(self.sql)  
            elapsed = time.time() - self.start_time  
            result['elapsed'] = elapsed  
            self.finished.emit(result)  
        except Exception as e:  
            self.error.emit(str(e))  


# ==================== 连接对话框 ====================  

class ConnectionDialog(QDialog):  
    """数据库连接对话框"""  
    
    def __init__(self, parent=None, connection_data=None):  
        super().__init__(parent)  
        self.connection_data = connection_data or {}  
        self.result_data = None  
        self.init_ui()  
    
    def init_ui(self):  
        """初始化UI"""  
        self.setWindowTitle("数据库连接")  
        self.setMinimumWidth(500)  
        
        layout = QVBoxLayout(self)  
        
        # 连接名称  
        name_group = QGroupBox("连接信息")  
        name_layout = QVBoxLayout()  
        
        name_hlayout = QHBoxLayout()  
        name_hlayout.addWidget(QLabel("连接名称:"))  
        self.name_edit = QLineEdit()  
        self.name_edit.setText(self.connection_data.get('name', ''))  
        name_hlayout.addWidget(self.name_edit)  
        name_layout.addLayout(name_hlayout)  
        
        # 数据库类型  
        type_hlayout = QHBoxLayout()  
        type_hlayout.addWidget(QLabel("数据库类型:"))  
        self.type_combo = QComboBox()  
        self.type_combo.addItems(['SQLite', 'MySQL', 'PostgreSQL'])  
        self.type_combo.setCurrentText(self.connection_data.get('type', 'SQLite'))  
        self.type_combo.currentTextChanged.connect(self.on_type_changed)  
        type_hlayout.addWidget(self.type_combo)  
        name_layout.addLayout(type_hlayout)  
        
        name_group.setLayout(name_layout)  
        layout.addWidget(name_group)  
        
        # SQLite参数  
        self.sqlite_group = QGroupBox("SQLite 参数")  
        sqlite_layout = QVBoxLayout()  
        
        file_hlayout = QHBoxLayout()  
        file_hlayout.addWidget(QLabel("数据库文件:"))  
        self.sqlite_file_edit = QLineEdit()  
        self.sqlite_file_edit.setText(self.connection_data.get('database', ''))  
        file_hlayout.addWidget(self.sqlite_file_edit)  
        
        browse_btn = QPushButton("浏览...")  
        browse_btn.clicked.connect(self.browse_sqlite_file)  
        file_hlayout.addWidget(browse_btn)  
        
        sqlite_layout.addLayout(file_hlayout)  
        self.sqlite_group.setLayout(sqlite_layout)  
        layout.addWidget(self.sqlite_group)  
        
        # MySQL/PostgreSQL参数  
        self.server_group = QGroupBox("服务器参数")  
        server_layout = QVBoxLayout()  
        
        # 主机和端口  
        host_hlayout = QHBoxLayout()  
        host_hlayout.addWidget(QLabel("主机:"))  
        self.host_edit = QLineEdit()  
        self.host_edit.setText(self.connection_data.get('host', 'localhost'))  
        host_hlayout.addWidget(self.host_edit)  
        
        host_hlayout.addWidget(QLabel("端口:"))  
        self.port_spin = QSpinBox()  
        self.port_spin.setRange(1, 65535)  
        self.port_spin.setValue(self.connection_data.get('port', 3306))  
        host_hlayout.addWidget(self.port_spin)  
        
        server_layout.addLayout(host_hlayout)  
        
        # 用户名  
        user_hlayout = QHBoxLayout()  
        user_hlayout.addWidget(QLabel("用户名:"))  
        self.user_edit = QLineEdit()  
        self.user_edit.setText(self.connection_data.get('user', ''))  
        user_hlayout.addWidget(self.user_edit)  
        server_layout.addLayout(user_hlayout)  
        
        # 密码  
        pass_hlayout = QHBoxLayout()  
        pass_hlayout.addWidget(QLabel("密码:"))  
        self.pass_edit = QLineEdit()  
        self.pass_edit.setEchoMode(QLineEdit.Password)  
        self.pass_edit.setText(self.connection_data.get('password', ''))  
        pass_hlayout.addWidget(self.pass_edit)  
        server_layout.addLayout(pass_hlayout)  
        
        # 数据库名  
        db_hlayout = QHBoxLayout()  
        db_hlayout.addWidget(QLabel("数据库:"))  
        self.database_edit = QLineEdit()  
        self.database_edit.setText(self.connection_data.get('database', ''))  
        db_hlayout.addWidget(self.database_edit)  
        server_layout.addLayout(db_hlayout)  
        
        self.server_group.setLayout(server_layout)  
        layout.addWidget(self.server_group)  
        
        # 按钮  
        button_box = QDialogButtonBox(  
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel  
        )  
        button_box.accepted.connect(self.accept)  
        button_box.rejected.connect(self.reject)  
        layout.addWidget(button_box)  
        
        self.on_type_changed(self.type_combo.currentText())  
    
    def on_type_changed(self, db_type):  
        """数据库类型改变"""  
        if db_type == 'SQLite':  
            self.sqlite_group.show()  
            self.server_group.hide()  
        else:  
            self.sqlite_group.hide()  
            self.server_group.show()  
            
            if db_type == 'MySQL':  
                self.port_spin.setValue(3306)  
            elif db_type == 'PostgreSQL':  
                self.port_spin.setValue(5432)  
    
    def browse_sqlite_file(self):  
        """浏览SQLite文件"""  
        file_path, _ = QFileDialog.getOpenFileName(  
            self,  
            "选择SQLite数据库文件",  
            "",  
            "SQLite数据库 (*.db *.sqlite *.sqlite3);;所有文件 (*.*)"  
        )  
        
        if not file_path:  
            file_path, _ = QFileDialog.getSaveFileName(  
                self,  
                "创建新数据库",  
                "",  
                "SQLite数据库 (*.db)"  
            )  
        
        if file_path:  
            self.sqlite_file_edit.setText(file_path)  
    
    def accept(self):  
        """确认连接"""  
        db_type = self.type_combo.currentText().lower()  
        
        if db_type == 'sqlite':  
            if not self.sqlite_file_edit.text():  
                QMessageBox.warning(self, "警告", "请选择数据库文件")  
                return  
            
            self.result_data = {  
                'name': self.name_edit.text() or 'SQLite连接',  
                'type': db_type,  
                'database': self.sqlite_file_edit.text()  
            }  
        else:  
            if not all([self.host_edit.text(), self.user_edit.text(),   
                       self.database_edit.text()]):  
                QMessageBox.warning(self, "警告", "请填写所有必填项")  
                return  
            
            self.result_data = {  
                'name': self.name_edit.text() or f'{db_type.upper()}连接',  
                'type': db_type,  
                'host': self.host_edit.text(),  
                'port': self.port_spin.value(),  
                'user': self.user_edit.text(),  
                'password': self.pass_edit.text(),  
                'database': self.database_edit.text()  
            }  
        
        super().accept()  


# ==================== 主窗口 ====================  

class DatabaseManagerPro(QMainWindow):  
    """数据库管理主窗口"""  
    
    def __init__(self):  
        super().__init__()  
        self.db_connection = None  
        self.query_history = []  
        self.current_table = None  
        self.current_result = None  
        self.settings = QSettings('DatabaseManagerPro', 'Settings')  
        
        self.init_ui()  
        self.load_settings()  
        self.apply_style()  
    
    def init_ui(self):  
        """初始化UI"""  
        self.setWindowTitle("DatabaseManagerPro - 专业数据库管理工具")  
        self.setGeometry(100, 100, 1400, 900)  
        
        # 创建菜单栏  
        self.create_menu_bar()  
        
        # 创建工具栏  
        self.create_tool_bar()  
        
        # 创建中心部件  
        central_widget = QWidget()  
        self.setCentralWidget(central_widget)  
        
        main_layout = QHBoxLayout(central_widget)  
        main_layout.setContentsMargins(0, 0, 0, 0)  
        
        # 主分割器  
        main_splitter = QSplitter(Qt.Horizontal)  
        
        # 左侧面板  
        left_panel = self.create_left_panel()  
        main_splitter.addWidget(left_panel)  
        
        # 右侧面板  
        right_panel = self.create_right_panel()  
        main_splitter.addWidget(right_panel)  
        
        main_splitter.setStretchFactor(0, 1)  
        main_splitter.setStretchFactor(1, 4)  
        
        main_layout.addWidget(main_splitter)  
        
        # 创建状态栏  
        self.create_status_bar()  
    
    def create_menu_bar(self):  
        """创建菜单栏"""  
        menubar = self.menuBar()  
        
        # 文件菜单  
        file_menu = menubar.addMenu("文件(&F)")  
        
        new_conn_action = QAction("新建连接(&N)", self)  
        new_conn_action.setShortcut(QKeySequence.New)  
        new_conn_action.triggered.connect(self.show_connection_dialog)  
        file_menu.addAction(new_conn_action)  
        
        file_menu.addSeparator()  
        
        import_action = QAction("导入数据(&I)", self)  
        import_action.triggered.connect(self.import_data)  
        file_menu.addAction(import_action)  
        
        export_action = QAction("导出数据(&E)", self)  
        export_action.triggered.connect(self.export_data)  
        file_menu.addAction(export_action)  
        
        file_menu.addSeparator()  
        
        exit_action = QAction("退出(&X)", self)  
        exit_action.setShortcut(QKeySequence.Quit)  
        exit_action.triggered.connect(self.close)  
        file_menu.addAction(exit_action)  
        
        # 编辑菜单  
        edit_menu = menubar.addMenu("编辑(&E)")  
        
        format_sql_action = QAction("格式化SQL(&F)", self)  
        format_sql_action.setShortcut("Ctrl+Shift+F")  
        format_sql_action.triggered.connect(self.format_sql)  
        edit_menu.addAction(format_sql_action)  
        
        clear_action = QAction("清空编辑器(&C)", self)  
        clear_action.triggered.connect(self.clear_editor)  
        edit_menu.addAction(clear_action)  
        
        # 查询菜单  
        query_menu = menubar.addMenu("查询(&Q)")  
        
        execute_action = QAction("执行查询(&E)", self)  
        execute_action.setShortcut("F5")  
        execute_action.triggered.connect(self.execute_query)  
        query_menu.addAction(execute_action)  
        
        explain_action = QAction("查询分析(&A)", self)  
        explain_action.triggered.connect(self.explain_query)  
        query_menu.addAction(explain_action)  
        
        # 工具菜单  
        tools_menu = menubar.addMenu("工具(&T)")  
        
        backup_action = QAction("数据库备份(&B)", self)  
        backup_action.triggered.connect(self.backup_database)  
        tools_menu.addAction(backup_action)  
        
        restore_action = QAction("数据库恢复(&R)", self)  
        restore_action.triggered.connect(self.restore_database)  
        tools_menu.addAction(restore_action)  
        
        tools_menu.addSeparator()  
        
        optimize_action = QAction("性能优化(&O)", self)  
        optimize_action.triggered.connect(self.optimize_database)  
        tools_menu.addAction(optimize_action)  
        
        monitor_action = QAction("性能监控(&M)", self)  
        monitor_action.triggered.connect(self.show_performance_monitor)  
        tools_menu.addAction(monitor_action)  
        
        # 帮助菜单  
        help_menu = menubar.addMenu("帮助(&H)")  
        
        help_action = QAction("使用帮助(&H)", self)  
        help_action.setShortcut("F1")  
        help_action.triggered.connect(self.show_help)  
        help_menu.addAction(help_action)  
        
        about_action = QAction("关于(&A)", self)  
        about_action.triggered.connect(self.show_about)  
        help_menu.addAction(about_action)  
    
    def create_tool_bar(self):  
        """创建工具栏"""  
        toolbar = QToolBar("主工具栏")  
        toolbar.setMovable(False)  
        self.addToolBar(toolbar)  
        
        # 连接按钮  
        connect_btn = QPushButton("🔌 连接")  
        connect_btn.setToolTip("连接数据库")  
        connect_btn.clicked.connect(self.show_connection_dialog)  
        toolbar.addWidget(connect_btn)  
        
        toolbar.addSeparator()  
        
        # 执行按钮  
        execute_btn = QPushButton("▶ 执行 (F5)")  
        execute_btn.setToolTip("执行SQL查询")  
        execute_btn.clicked.connect(self.execute_query)  
        toolbar.addWidget(execute_btn)  
        
        # 格式化按钮  
        format_btn = QPushButton("📋 格式化")  
        format_btn.setToolTip("格式化SQL语句")  
        format_btn.clicked.connect(self.format_sql)  
        toolbar.addWidget(format_btn)  
        
        # 清空按钮  
        clear_btn = QPushButton("🗑 清空")  
        clear_btn.setToolTip("清空编辑器")  
        clear_btn.clicked.connect(self.clear_editor)  
        toolbar.addWidget(clear_btn)  
        
        toolbar.addSeparator()  
        
        # 刷新按钮  
        refresh_btn = QPushButton("🔄 刷新")  
        refresh_btn.setToolTip("刷新表列表")  
        refresh_btn.clicked.connect(self.refresh_tables)  
        toolbar.addWidget(refresh_btn)  
    
    def create_left_panel(self):  
        """创建左侧面板"""  
        left_widget = QWidget()  
        left_layout = QVBoxLayout(left_widget)  
        left_layout.setContentsMargins(5, 5, 5, 5)  
        
        # 连接信息  
        conn_group = QGroupBox("数据库连接")  
        conn_layout = QVBoxLayout()  
        
        self.conn_info_label = QLabel("未连接")  
        self.conn_info_label.setStyleSheet("color: red; font-weight: bold;")  
        conn_layout.addWidget(self.conn_info_label)  
        
        self.db_info_label = QLabel("")  
        self.db_info_label.setWordWrap(True)  
        conn_layout.addWidget(self.db_info_label)  
        
        conn_group.setLayout(conn_layout)  
        left_layout.addWidget(conn_group)  
        
        # 表搜索  
        search_layout = QHBoxLayout()  
        self.table_search = QLineEdit()  
        self.table_search.setPlaceholderText("搜索表...")  
        self.table_search.textChanged.connect(self.filter_tables)  
        search_layout.addWidget(self.table_search)  
        
        search_btn = QPushButton("🔍")  
        search_btn.setMaximumWidth(40)  
        search_layout.addWidget(search_btn)  
        
        left_layout.addLayout(search_layout)  
        
        # 表列表  
        self.tables_tree = QTreeWidget()  
        self.tables_tree.setHeaderLabels(["表", "行数"])  
        self.tables_tree.setColumnWidth(0, 200)  
        self.tables_tree.itemDoubleClicked.connect(self.on_table_double_clicked)  
        self.tables_tree.setContextMenuPolicy(Qt.CustomContextMenu)  
        self.tables_tree.customContextMenuRequested.connect(self.show_table_context_menu)  
        left_layout.addWidget(self.tables_tree)  
        
        return left_widget  
    
    def create_right_panel(self):  
        """创建右侧面板"""  
        right_widget = QWidget()  
        right_layout = QVBoxLayout(right_widget)  
        right_layout.setContentsMargins(0, 0, 0, 0)  
        
        # 创建标签页  
        self.tab_widget = QTabWidget()  
        self.tab_widget.setTabsClosable(True)  
        self.tab_widget.tabCloseRequested.connect(self.close_tab)  
        
        # SQL编辑器标签  
        self.create_query_tab()  
        
        # 查询历史标签  
        self.create_history_tab()  
        
        right_layout.addWidget(self.tab_widget)  
        
        return right_widget  
    
    def create_query_tab(self):  
        """创建查询标签"""  
        query_widget = QWidget()  
        query_layout = QVBoxLayout(query_widget)  
        query_layout.setContentsMargins(5, 5, 5, 5)  
        
        # SQL编辑器工具栏  
        editor_toolbar = QHBoxLayout()  
        
        open_btn = QPushButton("📂 打开")  
        open_btn.clicked.connect(self.open_sql_file)  
        editor_toolbar.addWidget(open_btn)  
        
        save_btn = QPushButton("💾 保存")  
        save_btn.clicked.connect(self.save_sql_file)  
        editor_toolbar.addWidget(save_btn)  
        
        editor_toolbar.addStretch()  
        
        self.auto_commit_check = QCheckBox("自动提交")  
        self.auto_commit_check.setChecked(True)  
        editor_toolbar.addWidget(self.auto_commit_check)  
        
        query_layout.addLayout(editor_toolbar)  
        
        # 分割器  
        splitter = QSplitter(Qt.Vertical)  
        
        # SQL编辑器  
        self.sql_editor = SQLEditor()  
        self.sql_editor.executeRequested.connect(self.execute_query)  
        splitter.addWidget(self.sql_editor)  
        
        # 结果区域  
        result_widget = QWidget()  
        result_layout = QVBoxLayout(result_widget)  
        result_layout.setContentsMargins(0, 0, 0, 0)  
        
        # 结果工具栏  
        result_toolbar = QHBoxLayout()  
        
        export_csv_btn = QPushButton("📊 导出CSV")  
        export_csv_btn.clicked.connect(lambda: self.export_results('csv'))  
        result_toolbar.addWidget(export_csv_btn)  
        
        export_json_btn = QPushButton("📄 导出JSON")  
        export_json_btn.clicked.connect(lambda: self.export_results('json'))  
        result_toolbar.addWidget(export_json_btn)  
        
        if PANDAS_AVAILABLE:  
            export_excel_btn = QPushButton("📗 导出Excel")  
            export_excel_btn.clicked.connect(lambda: self.export_results('excel'))  
            result_toolbar.addWidget(export_excel_btn)  
        
        result_toolbar.addStretch()  
        
        self.result_info_label = QLabel("就绪")  
        result_toolbar.addWidget(self.result_info_label)  
        
        result_layout.addLayout(result_toolbar)  
        
        # 结果表格  
        self.result_table = QTableWidget()  
        self.result_table.setAlternatingRowColors(True)  
        self.result_table.horizontalHeader().setStretchLastSection(True)  
        self.result_table.setContextMenuPolicy(Qt.CustomContextMenu)  
        self.result_table.customContextMenuRequested.connect(self.show_result_context_menu)  
        result_layout.addWidget(self.result_table)  
        
        result_widget.setLayout(result_layout)  
        splitter.addWidget(result_widget)  
        
        splitter.setStretchFactor(0, 1)  
        splitter.setStretchFactor(1, 2)  
        
        query_layout.addWidget(splitter)  
        
        self.tab_widget.addTab(query_widget, "SQL编辑器")  
    
    def create_history_tab(self):  
        """创建历史标签"""  
        history_widget = QWidget()  
        history_layout = QVBoxLayout(history_widget)  
        
        # 工具栏  
        toolbar = QHBoxLayout()  
        
        clear_btn = QPushButton("清空历史")  
        clear_btn.clicked.connect(self.clear_history)  
        toolbar.addWidget(clear_btn)  
        
        toolbar.addStretch()  
        
        self.history_search = QLineEdit()  
        self.history_search.setPlaceholderText("搜索历史...")  
        self.history_search.textChanged.connect(self.filter_history)  
        toolbar.addWidget(self.history_search)  
        
        history_layout.addLayout(toolbar)  
        
        # 历史列表  
        self.history_list = QListWidget()  
        self.history_list.itemDoubleClicked.connect(self.load_history_item)  
        history_layout.addWidget(self.history_list)  
        
        self.tab_widget.addTab(history_widget, "查询历史")  
    
    def create_status_bar(self):  
        """创建状态栏"""  
        self.status_bar = QStatusBar()  
        self.setStatusBar(self.status_bar)  
        
        self.status_label = QLabel("就绪")  
        self.status_bar.addWidget(self.status_label)  
        
        self.status_bar.addPermanentWidget(QLabel("  |  "))  
        
        self.time_label = QLabel("")  
        self.status_bar.addPermanentWidget(self.time_label)  
        
        # 更新时间  
        self.timer = QTimer()  
        self.timer.timeout.connect(self.update_time)  
        self.timer.start(1000)  
        self.update_time()  
    
    def update_time(self):  
        """更新时间显示"""  
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
        self.time_label.setText(current_time)  
    
    def show_connection_dialog(self):  
        """显示连接对话框"""  
        dialog = ConnectionDialog(self)  
        if dialog.exec_() == QDialog.Accepted:  
            self.connect_database(dialog.result_data)  
    
    def connect_database(self, conn_data):  
        """连接数据库"""  
        try:  
            # 关闭旧连接  
            if self.db_connection:  
                self.db_connection.close()  
            
            # 创建新连接  
            db_type = conn_data['type']  
            kwargs = {k: v for k, v in conn_data.items() if k not in ['name', 'type']}  
            
            self.db_connection = DatabaseConnection(db_type, **kwargs)  
            self.db_connection.connect()  
            
            # 更新UI  
            conn_info = f"{conn_data['name']}"  
            self.conn_info_label.setText(conn_info)  
            self.conn_info_label.setStyleSheet("color: green; font-weight: bold;")  
            
            # 更新数据库信息  
            db_size = self.db_connection.get_database_size()  
            db_info = f"类型: {db_type.upper()}\n"  
            db_info += f"大小: {db_size}"  
            self.db_info_label.setText(db_info)  
            
            self.status_label.setText(f"已连接到 {conn_info}")  
            
            # 刷新表列表  
            self.refresh_tables()  
            
            # 保存连接配置  
            self.save_connection(conn_data)  
            
            QMessageBox.information(self, "成功", "数据库连接成功！")  
            
        except Exception as e:  
            QMessageBox.critical(self, "连接失败", str(e))  
    
    def refresh_tables(self):  
        """刷新表列表"""  
        if not self.db_connection:  
            QMessageBox.warning(self, "警告", "请先连接数据库")  
            return  
        
        try:  
            self.tables_tree.clear()  
            tables = self.db_connection.get_tables()  
            
            for table in tables:  
                # 获取表信息  
                table_info = self.db_connection.get_table_info(table)  
                if table_info:  
                    item = QTreeWidgetItem([table, str(table_info['row_count'])])  
                    self.tables_tree.addTopLevelItem(item)  
            
            self.status_label.setText(f"共 {len(tables)} 个表")  
            
        except Exception as e:  
            QMessageBox.critical(self, "错误", f"刷新表列表失败: {str(e)}")  
    
    def filter_tables(self):  
        """过滤表列表"""  
        search_text = self.table_search.text().lower()  
        
        for i in range(self.tables_tree.topLevelItemCount()):  
            item = self.tables_tree.topLevelItem(i)  
            table_name = item.text(0).lower()  
            item.setHidden(search_text not in table_name)  
    
    def on_table_double_clicked(self, item, column):  
        """表双击事件"""  
        table_name = item.text(0)  
        self.show_table_data(table_name)  
    
    def show_table_data(self, table_name):  
        """显示表数据"""  
        sql = f"SELECT * FROM {table_name} LIMIT 1000"  
        self.sql_editor.set_sql(sql)  
        self.execute_query()  
    
    def show_table_context_menu(self, position):  
        """显示表右键菜单"""  
        item = self.tables_tree.itemAt(position)  
        if not item:  
            return  
        
        table_name = item.text(0)  
        
        menu = QMenu()  
        
        view_data_action = QAction("查看数据", self)  
        view_data_action.triggered.connect(lambda: self.show_table_data(table_name))  
        menu.addAction(view_data_action)  
        
        view_structure_action = QAction("查看结构", self)  
        view_structure_action.triggered.connect(lambda: self.show_table_structure(table_name))  
        menu.addAction(view_structure_action)  
        
        menu.addSeparator()  
        
        export_action = QAction("导出表", self)  
        export_action.triggered.connect(lambda: self.export_table(table_name))  
        menu.addAction(export_action)  
        
        menu.addSeparator()  
        
        truncate_action = QAction("清空表", self)  
        truncate_action.triggered.connect(lambda: self.truncate_table(table_name))  
        menu.addAction(truncate_action)  
        
        drop_action = QAction("删除表", self)  
        drop_action.triggered.connect(lambda: self.drop_table(table_name))  
        menu.addAction(drop_action)  
        
        menu.exec_(self.tables_tree.viewport().mapToGlobal(position))  
    
    def show_table_structure(self, table_name):  
        """显示表结构"""  
        try:  
            table_info = self.db_connection.get_table_info(table_name)  
            if table_info:  
                result = table_info['structure']  
                self.display_results(result)  
                self.result_info_label.setText(f"表 {table_name} 的结构")  
        except Exception as e:  
            QMessageBox.critical(self, "错误", f"获取表结构失败: {str(e)}")  
    
    def execute_query(self):  
        """执行SQL查询"""  
        if not self.db_connection:  
            QMessageBox.warning(self, "警告", "请先连接数据库")  
            return  
        
        sql = self.sql_editor.get_sql()  
        if not sql:  
            return  
        
        # 添加到历史  
        self.add_to_history(sql)  
        
        # 在线程中执行  
        self.query_thread = QueryThread(self.db_connection, sql)  
        self.query_thread.finished.connect(self.on_query_finished)  
        self.query_thread.error.connect(self.on_query_error)  
        self.query_thread.start()  
        
        self.status_label.setText("正在执行查询...")  
        self.result_info_label.setText("执行中...")  
    
    def on_query_finished(self, result):  
        """查询完成"""  
        elapsed = result.get('elapsed', 0)  
        
        if result['type'] == 'select':  
            self.display_results(result)  
            self.result_info_label.setText(  
                f"查询完成，共 {result['rowcount']} 行，耗时: {elapsed:.3f}秒"  
            )  
        else:  
            affected = result.get('affected_rows', 0)  
            self.result_info_label.setText(  
                f"执行完成，影响 {affected} 行，耗时: {elapsed:.3f}秒"  
            )  
            # 刷新表列表  
            self.refresh_tables()  
        
        self.status_label.setText("查询完成")  
    
    def on_query_error(self, error):  
        """查询错误"""  
        QMessageBox.critical(self, "查询错误", error)  
        self.status_label.setText("查询失败")  
        self.result_info_label.setText("查询失败")  
    
    def display_results(self, result):  
        """显示查询结果"""  
        if 'columns' not in result:  
            return  
        
        columns = result['columns']  
        rows = result['rows']  
        
        # 设置表格  
        self.result_table.clear()  
        self.result_table.setRowCount(len(rows))  
        self.result_table.setColumnCount(len(columns))  
        self.result_table.setHorizontalHeaderLabels(columns)  
        
        # 填充数据  
        for row_idx, row in enumerate(rows):  
            if isinstance(row, dict):  
                values = [str(row.get(col, '')) for col in columns]  
            else:  
                values = [str(val) if val is not None else '' for val in row]  
            
            for col_idx, value in enumerate(values):  
                item = QTableWidgetItem(value)  
                self.result_table.setItem(row_idx, col_idx, item)  
        
        # 调整列宽  
        self.result_table.resizeColumnsToContents()  
        
        # 保存当前结果  
        self.current_result = result  
    
    def show_result_context_menu(self, position):  
        """显示结果右键菜单"""  
        menu = QMenu()  
        
        copy_action = QAction("复制", self)  
        copy_action.triggered.connect(self.copy_selected_cells)  
        menu.addAction(copy_action)  
        
        copy_row_action = QAction("复制行", self)  
        copy_row_action.triggered.connect(self.copy_selected_row)  
        menu.addAction(copy_row_action)  
        
        menu.exec_(self.result_table.viewport().mapToGlobal(position))  
    
    def copy_selected_cells(self):  
        """复制选中单元格"""  
        selected = self.result_table.selectedItems()  
        if selected:  
            text = '\n'.join([item.text() for item in selected])  
            QApplication.clipboard().setText(text)  
    
    def copy_selected_row(self):  
        """复制选中行"""  
        selected_rows = set([item.row() for item in self.result_table.selectedItems()])  
        
        text = []  
        for row in sorted(selected_rows):  
            row_data = []  
            for col in range(self.result_table.columnCount()):  
                item = self.result_table.item(row, col)  
                row_data.append(item.text() if item else '')  
            text.append('\t'.join(row_data))  
        
        QApplication.clipboard().setText('\n'.join(text))  
    
    def export_results(self, format_type):  
        """导出查询结果"""  
        if not hasattr(self, 'current_result') or not self.current_result:  
            QMessageBox.warning(self, "警告", "没有可导出的数据")  
            return  
        
        if format_type == 'csv':  
            file_path, _ = QFileDialog.getSaveFileName(  
                self, "导出CSV", "", "CSV文件 (*.csv)"  
            )  
            if file_path:  
                self.export_to_csv(file_path)  
        
        elif format_type == 'json':  
            file_path, _ = QFileDialog.getSaveFileName(  
                self, "导出JSON", "", "JSON文件 (*.json)"  
            )  
            if file_path:  
                self.export_to_json(file_path)  
        
        elif format_type == 'excel':  
            if not PANDAS_AVAILABLE:  
                QMessageBox.warning(self, "警告", "请安装 pandas 和 openpyxl")  
                return  
            
            file_path, _ = QFileDialog.getSaveFileName(  
                self, "导出Excel", "", "Excel文件 (*.xlsx)"  
            )  
            if file_path:  
                self.export_to_excel(file_path)  
    
    def export_to_csv(self, file_path):  
        """导出为CSV"""  
        try:  
            result = self.current_result  
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:  
                writer = csv.writer(f)  
                writer.writerow(result['columns'])  
                
                for row in result['rows']:  
                    if isinstance(row, dict):  
                        values = [row.get(col, '') for col in result['columns']]  
                    else:  
                        values = list(row)  
                    writer.writerow(values)  
            
            QMessageBox.information(self, "成功", f"数据已导出到: {file_path}")  
        except Exception as e:  
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")  
    
    def export_to_json(self, file_path):  
        """导出为JSON"""  
        try:  
            result = self.current_result  
            data = []  
            
            for row in result['rows']:  
                if isinstance(row, dict):  
                    data.append(row)  
                else:  
                    row_dict = {}  
                    for i, col in enumerate(result['columns']):  
                        row_dict[col] = row[i]  
                    data.append(row_dict)  
            
            with open(file_path, 'w', encoding='utf-8') as f:  
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)  
            
            QMessageBox.information(self, "成功", f"数据已导出到: {file_path}")  
        except Exception as e:  
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")  
    
    def export_to_excel(self, file_path):  
        """导出为Excel"""  
        try:  
            result = self.current_result  
            data = []  
            
            for row in result['rows']:  
                if isinstance(row, dict):  
                    data.append(row)  
                else:  
                    row_dict = {}  
                    for i, col in enumerate(result['columns']):  
                        row_dict[col] = row[i]  
                    data.append(row_dict)  
            
            df = pd.DataFrame(data)  
            df.to_excel(file_path, index=False)  
            
            QMessageBox.information(self, "成功", f"数据已导出到: {file_path}")  
        except Exception as e:  
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")  
    
    def format_sql(self):  
        """格式化SQL"""  
        sql = self.sql_editor.get_sql()  
        if not sql:  
            return  
        
        # 简单的SQL格式化  
        formatted = sql  
        keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT JOIN', 'RIGHT JOIN',  
                   'INNER JOIN', 'ORDER BY', 'GROUP BY', 'HAVING', 'LIMIT']  
        
        for keyword in keywords:  
            formatted = re.sub(f'\\b{keyword}\\b', f'\n{keyword}', formatted, flags=re.IGNORECASE)  
        
        formatted = re.sub(r',', ',\n  ', formatted)  
        formatted = formatted.strip()  
        
        self.sql_editor.set_sql(formatted)  
    
    def clear_editor(self):  
        """清空编辑器"""  
        reply = QMessageBox.question(  
            self, "确认", "确定要清空编辑器吗？",  
            QMessageBox.Yes | QMessageBox.No  
        )  
        if reply == QMessageBox.Yes:  
            self.sql_editor.clear()  
    
    def explain_query(self):  
        """查询分析"""  
        if not self.db_connection:  
            QMessageBox.warning(self, "警告", "请先连接数据库")  
            return  
        
        sql = self.sql_editor.get_sql()  
        if not sql:  
            return  
        
        try:  
            explain_sql = f"EXPLAIN {sql}"  
            result = self.db_connection.execute_query(explain_sql)  
            self.display_results(result)  
            self.result_info_label.setText("查询分析结果")  
        except Exception as e:  
            QMessageBox.critical(self, "错误", f"查询分析失败: {str(e)}")  
    
    def open_sql_file(self):  
        """打开SQL文件"""  
        file_path, _ = QFileDialog.getOpenFileName(  
            self, "打开SQL文件", "", "SQL文件 (*.sql);;所有文件 (*.*)"  
        )  
        if file_path:  
            try:  
                with open(file_path, 'r', encoding='utf-8') as f:  
                    sql = f.read()  
                    self.sql_editor.set_sql(sql)  
            except Exception as e:  
                QMessageBox.critical(self, "错误", f"打开文件失败: {str(e)}")  
    
    def save_sql_file(self):  
        """保存SQL文件"""  
        file_path, _ = QFileDialog.getSaveFileName(  
            self, "保存SQL文件", "", "SQL文件 (*.sql)"  
        )  
        if file_path:
            try:  
                sql = self.sql_editor.get_sql()  
                with open(file_path, 'w', encoding='utf-8') as f:  
                    f.write(sql)  
                QMessageBox.information(self, "成功", "文件已保存")  
            except Exception as e:  
                QMessageBox.critical(self, "错误", f"保存文件失败: {str(e)}")  
    
    def import_data(self):  
        """导入数据"""  
        if not self.db_connection:  
            QMessageBox.warning(self, "警告", "请先连接数据库")  
            return  
        
        file_path, _ = QFileDialog.getOpenFileName(  
            self, "选择数据文件", "",  
            "CSV文件 (*.csv);;JSON文件 (*.json);;所有文件 (*.*)"  
        )  
        
        if not file_path:  
            return  
        
        # 创建导入对话框  
        dialog = ImportDialog(self, file_path, self.db_connection)  
        dialog.exec_()  
    
    def export_data(self):  
        """导出数据"""  
        if not self.db_connection:  
            QMessageBox.warning(self, "警告", "请先连接数据库")  
            return  
        
        # 创建导出对话框  
        dialog = ExportDialog(self, self.db_connection)  
        dialog.exec_()  
    
    def export_table(self, table_name):  
        """导出表"""  
        sql = f"SELECT * FROM {table_name}"  
        self.sql_editor.set_sql(sql)  
        self.execute_query()  
    
    def truncate_table(self, table_name):  
        """清空表"""  
        reply = QMessageBox.question(  
            self, "确认", f"确定要清空表 {table_name} 吗？",  
            QMessageBox.Yes | QMessageBox.No  
        )  
        
        if reply == QMessageBox.Yes:  
            try:  
                sql = f"DELETE FROM {table_name}"  
                self.db_connection.execute_query(sql)  
                self.refresh_tables()  
                QMessageBox.information(self, "成功", f"表 {table_name} 已清空")  
            except Exception as e:  
                QMessageBox.critical(self, "错误", f"清空失败: {str(e)}")  
    
    def drop_table(self, table_name):  
        """删除表"""  
        reply = QMessageBox.question(  
            self, "确认", f"确定要删除表 {table_name} 吗？此操作不可恢复！",  
            QMessageBox.Yes | QMessageBox.No  
        )  
        
        if reply == QMessageBox.Yes:  
            try:  
                sql = f"DROP TABLE {table_name}"  
                self.db_connection.execute_query(sql)  
                self.refresh_tables()  
                QMessageBox.information(self, "成功", f"表 {table_name} 已删除")  
            except Exception as e:  
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")  
    
    def backup_database(self):  
        """数据库备份"""  
        if not self.db_connection:  
            QMessageBox.warning(self, "警告", "请先连接数据库")  
            return  
        
        if self.db_connection.db_type != 'sqlite':  
            QMessageBox.information(self, "提示", "当前仅支持SQLite数据库备份")  
            return  
        
        backup_file, _ = QFileDialog.getSaveFileName(  
            self, "保存备份", "", "SQLite数据库 (*.db)"  
        )  
        
        if backup_file:  
            try:  
                import shutil  
                source = self.db_connection.kwargs['database']  
                shutil.copy2(source, backup_file)  
                QMessageBox.information(self, "成功", f"数据库已备份到: {backup_file}")  
            except Exception as e:  
                QMessageBox.critical(self, "错误", f"备份失败: {str(e)}")  
    
    def restore_database(self):  
        """数据库恢复"""  
        QMessageBox.information(  
            self, "提示",  
            "请使用'连接数据库'功能选择备份文件进行恢复"  
        )  
    
    def optimize_database(self):  
        """性能优化"""  
        if not self.db_connection:  
            QMessageBox.warning(self, "警告", "请先连接数据库")  
            return  
        
        dialog = OptimizeDialog(self, self.db_connection)  
        dialog.exec_()  
    
    def show_performance_monitor(self):  
        """性能监控"""  
        if not self.db_connection:  
            QMessageBox.warning(self, "警告", "请先连接数据库")  
            return  
        
        dialog = PerformanceMonitorDialog(self, self.db_connection)  
        dialog.exec_()  
    
    def add_to_history(self, sql):  
        """添加到历史"""  
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
        history_item = f"[{timestamp}]\n{sql}"  
        
        self.history_list.insertItem(0, history_item)  
        self.query_history.insert(0, {'time': timestamp, 'sql': sql})  
        
        # 只保留最近100条  
        if self.history_list.count() > 100:  
            self.history_list.takeItem(100)  
            self.query_history = self.query_history[:100]  
        
        # 保存历史  
        self.save_history()  
    
    def filter_history(self):  
        """过滤历史"""  
        search_text = self.history_search.text().lower()  
        
        for i in range(self.history_list.count()):  
            item = self.history_list.item(i)  
            item.setHidden(search_text not in item.text().lower())  
    
    def load_history_item(self, item):  
        """加载历史项"""  
        text = item.text()  
        # 提取SQL部分  
        lines = text.split('\n')  
        sql = '\n'.join(lines[1:])  
        self.sql_editor.set_sql(sql)  
        self.tab_widget.setCurrentIndex(0)  
    
    def clear_history(self):  
        """清空历史"""  
        reply = QMessageBox.question(  
            self, "确认", "确定要清空所有历史记录吗？",  
            QMessageBox.Yes | QMessageBox.No  
        )  
        
        if reply == QMessageBox.Yes:  
            self.history_list.clear()  
            self.query_history.clear()  
            self.save_history()  
    
    def close_tab(self, index):  
        """关闭标签页"""  
        if index > 1:  # 不允许关闭前两个固定标签  
            self.tab_widget.removeTab(index)  
    
    def show_help(self):  
        """显示帮助"""  
        help_text = """  
<h2>DatabaseManagerPro 使用帮助</h2>  

<h3>1. 连接数据库</h3>  
<ul>  
<li>支持 SQLite, MySQL, PostgreSQL</li>  
<li>点击工具栏的"连接"按钮或使用菜单"文件->新建连接"</li>  
<li>填写相应的连接参数</li>  
</ul>  

<h3>2. SQL查询</h3>  
<ul>  
<li>在SQL编辑器中输入查询语句</li>  
<li>按F5或Ctrl+Enter执行</li>  
<li>支持语法高亮和行号显示</li>  
<li>可以选中部分SQL执行</li>  
</ul>  

<h3>3. 数据导入导出</h3>  
<ul>  
<li>支持CSV, JSON, Excel格式</li>  
<li>使用文件菜单中的导入/导出功能</li>  
<li>可以导出查询结果或整个表</li>  
</ul>  

<h3>4. 表管理</h3>  
<ul>  
<li>双击表名查看数据</li>  
<li>右键菜单提供更多操作</li>  
<li>支持查看表结构和统计信息</li>  
</ul>  

<h3>5. 快捷键</h3>  
<ul>  
<li>F5: 执行查询</li>  
<li>Ctrl+Enter: 执行查询</li>  
<li>Ctrl+/: 注释/取消注释</li>  
<li>Ctrl+Shift+F: 格式化SQL</li>  
<li>Ctrl+N: 新建连接</li>  
<li>Ctrl+O: 打开SQL文件</li>  
<li>Ctrl+S: 保存SQL文件</li>  
</ul>  

<h3>6. 性能优化</h3>  
<ul>  
<li>使用"工具->性能优化"检查数据库</li>  
<li>查看优化建议</li>  
<li>使用EXPLAIN分析查询</li>  
</ul>  
        """  
        
        msg_box = QMessageBox(self)  
        msg_box.setWindowTitle("使用帮助")  
        msg_box.setTextFormat(Qt.RichText)  
        msg_box.setText(help_text)  
        msg_box.exec_()  
    
    def show_about(self):  
        """显示关于"""  
        about_text = """  
<h2>DatabaseManagerPro</h2>  
<p><b>版本:</b> 2.0.0</p>  
<p><b>开发:</b> Python + PyQt5</p>  

<h3>功能特性:</h3>  
<ul>  
<li>✓ 多数据库支持 (SQLite, MySQL, PostgreSQL)</li>  
<li>✓ 可视化SQL编辑器</li>  
<li>✓ 语法高亮和智能提示</li>  
<li>✓ 数据导入导出 (CSV, JSON, Excel)</li>  
<li>✓ 数据库备份恢复</li>  
<li>✓ 性能监控和优化建议</li>  
<li>✓ 查询历史管理</li>  
</ul>  

<p>专业的数据库管理工具，让数据库管理更简单！</p>  
        """  
        
        msg_box = QMessageBox(self)  
        msg_box.setWindowTitle("关于")  
        msg_box.setTextFormat(Qt.RichText)  
        msg_box.setText(about_text)  
        msg_box.exec_()  
    
    def save_connection(self, conn_data):  
        """保存连接配置"""  
        connections = self.settings.value('connections', [])  
        if not isinstance(connections, list):  
            connections = []  
        
        # 不保存密码  
        conn_copy = conn_data.copy()  
        if 'password' in conn_copy:  
            conn_copy['password'] = ''  
        
        # 检查是否已存在  
        existing = False  
        for i, conn in enumerate(connections):  
            if conn.get('name') == conn_copy.get('name'):  
                connections[i] = conn_copy  
                existing = True  
                break  
        
        if not existing:  
            connections.append(conn_copy)  
        
        # 只保留最近10个  
        connections = connections[-10:]  
        
        self.settings.setValue('connections', connections)  
    
    def save_history(self):  
        """保存历史"""  
        self.settings.setValue('query_history', self.query_history[:100])  
    
    def load_settings(self):  
        """加载设置"""  
        # 加载窗口位置和大小  
        geometry = self.settings.value('geometry')  
        if geometry:  
            self.restoreGeometry(geometry)  
        
        # 加载历史  
        history = self.settings.value('query_history', [])  
        if isinstance(history, list):  
            self.query_history = history  
            for item in history:  
                history_text = f"[{item['time']}]\n{item['sql']}"  
                self.history_list.addItem(history_text)  
    
    def apply_style(self):  
        """应用样式"""  
        style = """  
        QMainWindow {  
            background-color: #f5f5f5;  
        }  
        
        QGroupBox {  
            font-weight: bold;  
            border: 1px solid #cccccc;  
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
            background-color: #ffffff;  
            border: 1px solid #cccccc;  
            border-radius: 3px;  
            padding: 5px 15px;  
            min-height: 25px;  
        }  
        
        QPushButton:hover {  
            background-color: #e6f2ff;  
            border-color: #0078d7;  
        }  
        
        QPushButton:pressed {  
            background-color: #cce4f7;  
        }  
        
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {  
            border: 1px solid #cccccc;  
            border-radius: 3px;  
            padding: 5px;  
            background-color: white;  
        }  
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {  
            border-color: #0078d7;  
        }  
        
        QTableWidget {  
            gridline-color: #d0d0d0;  
            background-color: white;  
            alternate-background-color: #f9f9f9;  
        }  
        
        QTableWidget::item:selected {  
            background-color: #0078d7;  
            color: white;  
        }  
        
        QHeaderView::section {  
            background-color: #e0e0e0;  
            padding: 5px;  
            border: 1px solid #c0c0c0;  
            font-weight: bold;  
        }  
        
        QTreeWidget {  
            background-color: white;  
            border: 1px solid #cccccc;  
            border-radius: 3px;  
        }  
        
        QTreeWidget::item:selected {  
            background-color: #0078d7;  
        }  
        
        QTabWidget::pane {  
            border: 1px solid #cccccc;  
            background-color: white;  
        }  
        
        QTabBar::tab {  
            background-color: #e0e0e0;  
            border: 1px solid #cccccc;  
            padding: 8px 20px;  
            margin-right: 2px;  
        }  
        
        QTabBar::tab:selected {  
            background-color: white;  
            border-bottom-color: white;  
        }  
        
        QStatusBar {  
            background-color: #f0f0f0;  
            border-top: 1px solid #cccccc;  
        }  
        """  
        self.setStyleSheet(style)  
    
    def closeEvent(self, event):  
        """关闭事件"""  
        # 保存窗口状态  
        self.settings.setValue('geometry', self.saveGeometry())  
        
        # 关闭数据库连接  
        if self.db_connection:  
            self.db_connection.close()  
        
        event.accept()  


# ==================== 导入对话框 ====================  

class ImportDialog(QDialog):  
    """数据导入对话框"""  
    
    def __init__(self, parent, file_path, db_connection):  
        super().__init__(parent)  
        self.file_path = file_path  
        self.db_connection = db_connection  
        self.init_ui()  
    
    def init_ui(self):  
        """初始化UI"""  
        self.setWindowTitle("导入数据")  
        self.setMinimumWidth(500)  
        
        layout = QVBoxLayout(self)  
        
        # 文件信息  
        file_group = QGroupBox("文件信息")  
        file_layout = QVBoxLayout()  
        
        file_label = QLabel(f"文件: {Path(self.file_path).name}")  
        file_layout.addWidget(file_label)  
        
        file_group.setLayout(file_layout)  
        layout.addWidget(file_group)  
        
        # 目标表  
        table_group = QGroupBox("目标表")  
        table_layout = QVBoxLayout()  
        
        table_hlayout = QHBoxLayout()  
        table_hlayout.addWidget(QLabel("表名:"))  
        self.table_edit = QLineEdit()  
        table_hlayout.addWidget(self.table_edit)  
        table_layout.addLayout(table_hlayout)  
        
        self.create_table_check = QCheckBox("如果表不存在则创建")  
        self.create_table_check.setChecked(True)  
        table_layout.addWidget(self.create_table_check)  
        
        self.truncate_check = QCheckBox("导入前清空表")  
        table_layout.addWidget(self.truncate_check)  
        
        table_group.setLayout(table_layout)  
        layout.addWidget(table_group)  
        
        # 进度条  
        self.progress_bar = QProgressBar()  
        self.progress_bar.setVisible(False)  
        layout.addWidget(self.progress_bar)  
        
        # 按钮  
        button_layout = QHBoxLayout()  
        
        import_btn = QPushButton("开始导入")  
        import_btn.clicked.connect(self.start_import)  
        button_layout.addWidget(import_btn)  
        
        cancel_btn = QPushButton("取消")  
        cancel_btn.clicked.connect(self.reject)  
        button_layout.addWidget(cancel_btn)  
        
        layout.addLayout(button_layout)  
    
    def start_import(self):  
        """开始导入"""  
        table_name = self.table_edit.text()  
        if not table_name:  
            QMessageBox.warning(self, "警告", "请输入表名")  
            return  
        
        try:  
            self.progress_bar.setVisible(True)  
            self.progress_bar.setValue(0)  
            
            # 读取文件  
            if self.file_path.endswith('.csv'):  
                with open(self.file_path, 'r', encoding='utf-8') as f:  
                    reader = csv.DictReader(f)  
                    data = list(reader)  
            elif self.file_path.endswith('.json'):  
                with open(self.file_path, 'r', encoding='utf-8') as f:  
                    data = json.load(f)  
            else:  
                QMessageBox.critical(self, "错误", "不支持的文件格式")  
                return  
            
            if not data:  
                QMessageBox.warning(self, "警告", "文件中没有数据")  
                return  
            
            # 清空表  
            if self.truncate_check.isChecked():  
                try:  
                    self.db_connection.execute_query(f"DELETE FROM {table_name}")  
                except:  
                    pass  
            
            # 创建表  
            if self.create_table_check.isChecked():  
                columns = list(data[0].keys())  
                create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ("  
                create_sql += ", ".join([f"{col} TEXT" for col in columns])  
                create_sql += ")"  
                self.db_connection.execute_query(create_sql)  
            
            # 插入数据  
            columns = list(data[0].keys())  
            placeholders = ", ".join(  
                ["?" if self.db_connection.db_type == 'sqlite' else "%s"] * len(columns)  
            )  
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"  
            
            cursor = self.db_connection.connection.cursor()  
            total = len(data)  
            
            for i, row in enumerate(data):  
                values = [row[col] for col in columns]  
                cursor.execute(insert_sql, values)  
                
                # 更新进度  
                progress = int((i + 1) / total * 100)  
                self.progress_bar.setValue(progress)  
                QApplication.processEvents()  
            
            self.db_connection.connection.commit()  
            cursor.close()  
            
            self.progress_bar.setValue(100)  
            QMessageBox.information(self, "成功", f"成功导入 {total} 行数据")  
            self.accept()  
            
        except Exception as e:  
            QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")  


# ==================== 导出对话框 ====================  

class ExportDialog(QDialog):  
    """数据导出对话框"""  
    
    def __init__(self, parent, db_connection):  
        super().__init__(parent)  
        self.db_connection = db_connection  
        self.init_ui()  
    
    def init_ui(self):  
        """初始化UI"""  
        self.setWindowTitle("导出数据")  
        self.setMinimumWidth(500)  
        
        layout = QVBoxLayout(self)  
        
        # 导出选项  
        option_group = QGroupBox("导出选项")  
        option_layout = QVBoxLayout()  
        
        self.export_type_group = QButtonGroup()  
        
        self.export_all_radio = QRadioButton("导出所有表")  
        self.export_all_radio.setChecked(True)  
        self.export_type_group.addButton(self.export_all_radio)  
        option_layout.addWidget(self.export_all_radio)  
        
        self.export_selected_radio = QRadioButton("导出选中的表")  
        self.export_type_group.addButton(self.export_selected_radio)  
        option_layout.addWidget(self.export_selected_radio)  
        
        # 表列表  
        self.table_list = QListWidget()  
        self.table_list.setSelectionMode(QListWidget.MultiSelection)  
        
        try:  
            tables = self.db_connection.get_tables()  
            for table in tables:  
                self.table_list.addItem(table)  
        except:  
            pass  
        
        option_layout.addWidget(self.table_list)  
        
        option_group.setLayout(option_layout)  
        layout.addWidget(option_group)  
        
        # 导出格式  
        format_group = QGroupBox("导出格式")  
        format_layout = QVBoxLayout()  
        
        self.format_combo = QComboBox()  
        self.format_combo.addItems(['SQL', 'CSV', 'JSON'])  
        format_layout.addWidget(self.format_combo)  
        
        format_group.setLayout(format_layout)  
        layout.addWidget(format_group)  
        
        # 按钮  
        button_layout = QHBoxLayout()  
        
        export_btn = QPushButton("开始导出")  
        export_btn.clicked.connect(self.start_export)  
        button_layout.addWidget(export_btn)  
        
        cancel_btn = QPushButton("取消")  
        cancel_btn.clicked.connect(self.reject)  
        button_layout.addWidget(cancel_btn)  
        
        layout.addLayout(button_layout)  
    
    def start_export(self):  
        """开始导出"""  
        # 获取要导出的表  
        if self.export_all_radio.isChecked():  
            tables = self.db_connection.get_tables()  
        else:  
            selected_items = self.table_list.selectedItems()  
            if not selected_items:  
                QMessageBox.warning(self, "警告", "请选择要导出的表")  
                return  
            tables = [item.text() for item in selected_items]  
        
        # 选择保存位置  
        format_type = self.format_combo.currentText()  
        
        if format_type == 'SQL':  
            file_path, _ = QFileDialog.getSaveFileName(  
                self, "导出SQL", "", "SQL文件 (*.sql)"  
            )  
        elif format_type == 'CSV':  
            file_path = QFileDialog.getExistingDirectory(self, "选择导出目录")  
        elif format_type == 'JSON':  
            file_path, _ = QFileDialog.getSaveFileName(  
                self, "导出JSON", "", "JSON文件 (*.json)"  
            )  
        
        if not file_path:  
            return  
        
        try:  
            if format_type == 'SQL':  
                self.export_to_sql(tables, file_path)  
            elif format_type == 'CSV':  
                self.export_to_csv_files(tables, file_path)  
            elif format_type == 'JSON':  
                self.export_to_json(tables, file_path)  
            
            QMessageBox.information(self, "成功", "导出完成")  
            self.accept()  
            
        except Exception as e:  
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")  
    
    def export_to_sql(self, tables, file_path):  
        """导出为SQL"""  
        with open(file_path, 'w', encoding='utf-8') as f:  
            f.write(f"-- Database Export\n")  
            f.write(f"-- Date: {datetime.now()}\n\n")  
            
            for table in tables:  
                # 导出表结构  
                if self.db_connection.db_type == 'sqlite':  
                    result = self.db_connection.execute_query(  
                        f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'"  
                    )  
                    if result['rows']:  
                        create_sql = result['rows'][0]['sql']  
                        f.write(f"\n-- Table: {table}\n")  
                        f.write(f"{create_sql};\n\n")  
                
                # 导出数据  
                result = self.db_connection.execute_query(f"SELECT * FROM {table}")  
                if result['rows']:  
                    columns = result['columns']  
                    for row in result['rows']:  
                        if isinstance(row, dict):  
                            values = [self.escape_sql_value(row[col]) for col in columns]  
                        else:  
                            values = [self.escape_sql_value(v) for v in row]  
                        
                        values_str = ", ".join(values)  
                        insert_sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({values_str});"  
                        f.write(f"{insert_sql}\n")  
                    f.write("\n")  
    
    def export_to_csv_files(self, tables, directory):  
        """导出为CSV文件"""  
        for table in tables:  
            file_path = Path(directory) / f"{table}.csv"  
            result = self.db_connection.execute_query(f"SELECT * FROM {table}")  
            
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:  
                writer = csv.writer(f)  
                writer.writerow(result['columns'])  
                
                for row in result['rows']:  
                    if isinstance(row, dict):  
                        values = [row[col] for col in result['columns']]  
                    else:  
                        values = list(row)  
                    writer.writerow(values)  
    
    def export_to_json(self, tables, file_path):  
        """导出为JSON"""  
        export_data = {}  
        
        for table in tables:  
            result = self.db_connection.execute_query(f"SELECT * FROM {table}")  
            table_data = []  
            
            for row in result['rows']:  
                if isinstance(row, dict):  
                    table_data.append(row)  
                else:  
                    row_dict = {}  
                    for i, col in enumerate(result['columns']):  
                        row_dict[col] = row[i]  
                    table_data.append(row_dict)  
            
            export_data[table] = table_data  
        
        with open(file_path, 'w', encoding='utf-8') as f:  
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)  
    
    def escape_sql_value(self, value):  
        """转义SQL值"""  
        if value is None:  
            return 'NULL'  
        elif isinstance(value, str):  
            escaped = value.replace("'", "''")  
            return "'" + escaped + "'"  
        else:  
            return str(value)  


# ==================== 性能优化对话框 ====================  

class OptimizeDialog(QDialog):  
    """性能优化对话框"""  
    
    def __init__(self, parent, db_connection):  
        super().__init__(parent)  
        self.db_connection = db_connection  
        self.init_ui()  
        self.analyze_database()  
    
    def init_ui(self):  
        """初始化UI"""  
        self.setWindowTitle("性能优化")  
        self.setMinimumSize(700, 500)  
        
        layout = QVBoxLayout(self)  
        
        # 优化建议  
        self.suggestions_text = QTextEdit()  
        self.suggestions_text.setReadOnly(True)  
        layout.addWidget(self.suggestions_text)  
        
        # 按钮  
        button_layout = QHBoxLayout()  
        
        optimize_btn = QPushButton("执行优化")  
        optimize_btn.clicked.connect(self.execute_optimize)  
        button_layout.addWidget(optimize_btn)  
        
        close_btn = QPushButton("关闭")  
        close_btn.clicked.connect(self.accept)  
        button_layout.addWidget(close_btn)  
        
        layout.addLayout(button_layout)  
    
    def analyze_database(self):  
        """分析数据库"""  
        suggestions = []  
        
        try:  
            if self.db_connection.db_type == 'sqlite':  
                # 检查索引  
                tables = self.db_connection.get_tables()  
                for table in tables:  
                    result = self.db_connection.execute_query(  
                        f"PRAGMA index_list({table})"  
                    )  
                    if not result['rows']:  
                        suggestions.append(f"表 {table} 没有索引，建议添加索引提高查询性能")  
            
            # 添加更多优化建议  
            suggestions.append("定期执行 VACUUM 清理数据库")  
            suggestions.append("为常用查询字段创建索引")  
            suggestions.append("避免使用 SELECT *")  
            suggestions.append("使用 EXPLAIN 分析慢查询")  
            
            text = "=== 性能优化建议 ===\n\n"  
            for i, suggestion in enumerate(suggestions, 1):  
                text += f"{i}. {suggestion}\n\n"  
            
            self.suggestions_text.setText(text)
            
        except Exception as e:
            self.suggestions_text.setText(f"分析失败: {str(e)}")
    
    def execute_optimize(self):
        """执行优化"""
        try:
            if self.db_connection.db_type == 'sqlite':
                self.db_connection.execute_query("VACUUM")
                self.db_connection.execute_query("ANALYZE")
                QMessageBox.information(self, "成功", "优化完成")
            else:
                QMessageBox.information(self, "提示", "请使用数据库专用工具进行优化")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"优化失败: {str(e)}")


# ==================== 性能监控对话框 ====================

class PerformanceMonitorDialog(QDialog):
    """性能监控对话框"""
    
    def __init__(self, parent, db_connection):
        super().__init__(parent)
        self.db_connection = db_connection
        self.init_ui()
        self.update_info()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("性能监控")
        self.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(self)
        
        # 信息显示
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.info_text)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.update_info)
        button_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def update_info(self):
        """更新信息"""
        try:
            info = "=== 数据库信息 ===\n\n"
            info += f"数据库类型: {self.db_connection.db_type.upper()}\n"
            info += f"数据库大小: {self.db_connection.get_database_size()}\n\n"
            
            info += "=== 表统计 ===\n\n"
            tables = self.db_connection.get_tables()
            info += f"总表数: {len(tables)}\n\n"
            
            for table in tables:
                table_info = self.db_connection.get_table_info(table)
                if table_info:
                    info += f"{table}: {table_info['row_count']} 行\n"
            
            self.info_text.setText(info)
            
        except Exception as e:
            self.info_text.setText(f"获取信息失败: {str(e)}")


# ==================== 主函数 ====================

def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("DatabaseManagerPro")
    app.setOrganizationName("DatabaseManagerPro")
    
    # 设置应用图标（如果有的话）
    # app.setWindowIcon(QIcon('icon.png'))
    
    window = DatabaseManagerPro()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()