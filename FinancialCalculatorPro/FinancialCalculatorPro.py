"""
FinancialCalculatorPro Enterprise Edition - 企业级专业财务管理软件
Version: 2.0.0
对标: 金蝶、用友等专业财务软件
github网址：https://github.com/lyp0746
QQ邮箱：1610369302@qq.com
作者：LYP
"""

import sqlite3
import sys
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtCore import (
    Qt, QDate, QSize
)
from PyQt5.QtGui import (
    QFont, QColor
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QTableWidget,
    QTableWidgetItem, QComboBox, QTextEdit, QGroupBox, QGridLayout,
    QMessageBox, QSpinBox, QDoubleSpinBox, QDateEdit, QHeaderView,
    QFrame, QDialog, QDialogButtonBox, QTreeWidget, QTreeWidgetItem, QFileDialog, QStatusBar,
    QAction, QToolBar, QPushButton
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# 设置matplotlib中文显示
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


# ==================== 数据库管理（增强版）====================
class EnhancedDatabaseManager:
    """增强的数据库管理器"""

    def __init__(self, db_name='financial_enterprise.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_all_tables()
        self.init_basic_data()

    def create_all_tables(self):
        """创建所有数据表"""
        cursor = self.conn.cursor()

        # 会计科目表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS accounts
                       (
                           id                INTEGER PRIMARY KEY AUTOINCREMENT,
                           code              TEXT UNIQUE NOT NULL,
                           name              TEXT        NOT NULL,
                           category          TEXT        NOT NULL,
                           parent_code       TEXT,
                           level             INTEGER,
                           balance_direction TEXT,
                           is_leaf           INTEGER DEFAULT 1,
                           created_date      TEXT
                       )
                       ''')

        # 会计凭证表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS vouchers
                       (
                           id           INTEGER PRIMARY KEY AUTOINCREMENT,
                           voucher_no   TEXT UNIQUE NOT NULL,
                           voucher_date TEXT        NOT NULL,
                           voucher_type TEXT,
                           total_debit  REAL,
                           total_credit REAL,
                           abstract     TEXT,
                           creator      TEXT,
                           auditor      TEXT,
                           status       TEXT DEFAULT 'draft',
                           created_date TEXT
                       )
                       ''')

        # 凭证明细表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS voucher_details
                       (
                           id           INTEGER PRIMARY KEY AUTOINCREMENT,
                           voucher_id   INTEGER,
                           line_no      INTEGER,
                           account_code TEXT,
                           account_name TEXT,
                           abstract     TEXT,
                           debit        REAL DEFAULT 0,
                           credit       REAL DEFAULT 0,
                           FOREIGN KEY (voucher_id) REFERENCES vouchers (id)
                       )
                       ''')

        # 客户信息表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS customers
                       (
                           id             INTEGER PRIMARY KEY AUTOINCREMENT,
                           code           TEXT UNIQUE NOT NULL,
                           name           TEXT        NOT NULL,
                           contact_person TEXT,
                           phone          TEXT,
                           address        TEXT,
                           credit_limit   REAL DEFAULT 0,
                           balance        REAL DEFAULT 0,
                           customer_type  TEXT,
                           created_date   TEXT
                       )
                       ''')

        # 供应商信息表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS suppliers
                       (
                           id             INTEGER PRIMARY KEY AUTOINCREMENT,
                           code           TEXT UNIQUE NOT NULL,
                           name           TEXT        NOT NULL,
                           contact_person TEXT,
                           phone          TEXT,
                           address        TEXT,
                           balance        REAL DEFAULT 0,
                           supplier_type  TEXT,
                           created_date   TEXT
                       )
                       ''')

        # 固定资产表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS fixed_assets
                       (
                           id                       INTEGER PRIMARY KEY AUTOINCREMENT,
                           asset_code               TEXT UNIQUE NOT NULL,
                           asset_name               TEXT        NOT NULL,
                           category                 TEXT,
                           original_value           REAL,
                           accumulated_depreciation REAL DEFAULT 0,
                           net_value                REAL,
                           purchase_date            TEXT,
                           useful_life              INTEGER,
                           depreciation_method      TEXT,
                           department               TEXT,
                           status                   TEXT DEFAULT 'in_use',
                           created_date             TEXT
                       )
                       ''')

        # 应收账款表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS receivables
                       (
                           id              INTEGER PRIMARY KEY AUTOINCREMENT,
                           bill_no         TEXT UNIQUE NOT NULL,
                           customer_code   TEXT,
                           customer_name   TEXT,
                           amount          REAL,
                           received_amount REAL DEFAULT 0,
                           balance         REAL,
                           bill_date       TEXT,
                           due_date        TEXT,
                           status          TEXT DEFAULT 'pending',
                           notes           TEXT,
                           created_date    TEXT
                       )
                       ''')

        # 应付账款表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS payables
                       (
                           id            INTEGER PRIMARY KEY AUTOINCREMENT,
                           bill_no       TEXT UNIQUE NOT NULL,
                           supplier_code TEXT,
                           supplier_name TEXT,
                           amount        REAL,
                           paid_amount   REAL DEFAULT 0,
                           balance       REAL,
                           bill_date     TEXT,
                           due_date      TEXT,
                           status        TEXT DEFAULT 'pending',
                           notes         TEXT,
                           created_date  TEXT
                       )
                       ''')

        # 员工信息表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS employees
                       (
                           id           INTEGER PRIMARY KEY AUTOINCREMENT,
                           emp_code     TEXT UNIQUE NOT NULL,
                           name         TEXT        NOT NULL,
                           department   TEXT,
                           position     TEXT,
                           base_salary  REAL,
                           hire_date    TEXT,
                           id_number    TEXT,
                           phone        TEXT,
                           status       TEXT DEFAULT 'active',
                           created_date TEXT
                       )
                       ''')

        # 工资表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS salaries
                       (
                           id              INTEGER PRIMARY KEY AUTOINCREMENT,
                           emp_code        TEXT,
                           emp_name        TEXT,
                           salary_month    TEXT,
                           base_salary     REAL,
                           allowance       REAL DEFAULT 0,
                           overtime_pay    REAL DEFAULT 0,
                           bonus           REAL DEFAULT 0,
                           social_security REAL DEFAULT 0,
                           housing_fund    REAL DEFAULT 0,
                           income_tax      REAL DEFAULT 0,
                           other_deduction REAL DEFAULT 0,
                           net_salary      REAL,
                           status          TEXT DEFAULT 'unpaid',
                           created_date    TEXT
                       )
                       ''')

        # 成本核算表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS costs
                       (
                           id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                           cost_no            TEXT UNIQUE NOT NULL,
                           product_name       TEXT,
                           cost_period        TEXT,
                           material_cost      REAL DEFAULT 0,
                           labor_cost         REAL DEFAULT 0,
                           manufacturing_cost REAL DEFAULT 0,
                           total_cost         REAL,
                           unit_cost          REAL,
                           quantity           REAL,
                           created_date       TEXT
                       )
                       ''')

        # 预算表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS budgets
                       (
                           id             INTEGER PRIMARY KEY AUTOINCREMENT,
                           budget_year    TEXT,
                           budget_month   TEXT,
                           department     TEXT,
                           category       TEXT,
                           planned_amount REAL,
                           actual_amount  REAL DEFAULT 0,
                           variance       REAL,
                           notes          TEXT,
                           created_date   TEXT
                       )
                       ''')

        # 发票管理表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS invoices
                       (
                           id           INTEGER PRIMARY KEY AUTOINCREMENT,
                           invoice_no   TEXT UNIQUE NOT NULL,
                           invoice_type TEXT,
                           invoice_date TEXT,
                           buyer_name   TEXT,
                           seller_name  TEXT,
                           amount       REAL,
                           tax_rate     REAL,
                           tax_amount   REAL,
                           total_amount REAL,
                           status       TEXT DEFAULT 'valid',
                           created_date TEXT
                       )
                       ''')

        # 系统日志表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS system_logs
                       (
                           id        INTEGER PRIMARY KEY AUTOINCREMENT,
                           log_type  TEXT,
                           module    TEXT,
                           operation TEXT,
                           operator  TEXT,
                           details   TEXT,
                           log_time  TEXT
                       )
                       ''')

        # 系统配置表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS system_config
                       (
                           id           INTEGER PRIMARY KEY AUTOINCREMENT,
                           config_key   TEXT UNIQUE NOT NULL,
                           config_value TEXT,
                           description  TEXT,
                           updated_date TEXT
                       )
                       ''')

        self.conn.commit()

    def init_basic_data(self):
        """初始化基础数据"""
        cursor = self.conn.cursor()

        # 检查是否已初始化
        cursor.execute("SELECT COUNT(*) FROM accounts")
        if cursor.fetchone()[0] > 0:
            return

            # 初始化会计科目（一级科目）
        basic_accounts = [
            ('1001', '库存现金', '资产', None, 1, '借', 1),
            ('1002', '银行存款', '资产', None, 1, '借', 1),
            ('1012', '其他货币资金', '资产', None, 1, '借', 1),
            ('1101', '短期投资', '资产', None, 1, '借', 1),
            ('1121', '应收票据', '资产', None, 1, '借', 1),
            ('1122', '应收账款', '资产', None, 1, '借', 1),
            ('1123', '预付账款', '资产', None, 1, '借', 1),
            ('1221', '其他应收款', '资产', None, 1, '借', 1),
            ('1401', '材料采购', '资产', None, 1, '借', 1),
            ('1402', '在途物资', '资产', None, 1, '借', 1),
            ('1403', '原材料', '资产', None, 1, '借', 1),
            ('1404', '材料成本差异', '资产', None, 1, '借', 1),
            ('1405', '库存商品', '资产', None, 1, '借', 1),
            ('1501', '长期股权投资', '资产', None, 1, '借', 1),
            ('1601', '固定资产', '资产', None, 1, '借', 1),
            ('1602', '累计折旧', '资产', None, 1, '贷', 1),
            ('1701', '无形资产', '资产', None, 1, '借', 1),
            ('2001', '短期借款', '负债', None, 1, '贷', 1),
            ('2201', '应付票据', '负债', None, 1, '贷', 1),
            ('2202', '应付账款', '负债', None, 1, '贷', 1),
            ('2203', '预收账款', '负债', None, 1, '贷', 1),
            ('2211', '应付职工薪酬', '负债', None, 1, '贷', 1),
            ('2221', '应交税费', '负债', None, 1, '贷', 1),
            ('2501', '长期借款', '负债', None, 1, '贷', 1),
            ('4001', '实收资本', '权益', None, 1, '贷', 1),
            ('4002', '资本公积', '权益', None, 1, '贷', 1),
            ('4101', '盈余公积', '权益', None, 1, '贷', 1),
            ('4103', '本年利润', '权益', None, 1, '贷', 1),
            ('4104', '利润分配', '权益', None, 1, '贷', 1),
            ('6001', '主营业务收入', '损益', None, 1, '贷', 1),
            ('6051', '其他业务收入', '损益', None, 1, '贷', 1),
            ('6111', '投资收益', '损益', None, 1, '贷', 1),
            ('6301', '营业外收入', '损益', None, 1, '贷', 1),
            ('6401', '主营业务成本', '损益', None, 1, '借', 1),
            ('6402', '其他业务成本', '损益', None, 1, '借', 1),
            ('6601', '销售费用', '损益', None, 1, '借', 1),
            ('6602', '管理费用', '损益', None, 1, '借', 1),
            ('6603', '财务费用', '损益', None, 1, '借', 1),
            ('6701', '营业外支出', '损益', None, 1, '借', 1),
            ('6801', '所得税费用', '损益', None, 1, '借', 1),
        ]

        for account in basic_accounts:
            try:
                cursor.execute('''
                               INSERT INTO accounts (code, name, category, parent_code,
                                                     level, balance_direction, is_leaf, created_date)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                               ''', (*account, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            except:
                pass

                # 初始化系统配置
        configs = [
            ('company_name', '示例企业有限公司', '公司名称'),
            ('tax_no', '91000000000000000X', '纳税人识别号'),
            ('fiscal_year_start', '01-01', '会计年度开始日期'),
            ('default_currency', 'CNY', '默认货币'),
            ('vat_rate', '13', '增值税率(%)'),
        ]

        for config in configs:
            try:
                cursor.execute('''
                               INSERT INTO system_config (config_key, config_value, description, updated_date)
                               VALUES (?, ?, ?, ?)
                               ''', (*config, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            except:
                pass

        self.conn.commit()

    def add_log(self, log_type, module, operation, operator, details=''):
        """添加系统日志"""
        cursor = self.conn.cursor()
        cursor.execute('''
                       INSERT INTO system_logs (log_type, module, operation, operator, details, log_time)
                       VALUES (?, ?, ?, ?, ?, ?)
                       ''', (log_type, module, operation, operator, details,
                             datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        self.conn.commit()

    def execute_query(self, query, params=()):
        """执行查询"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def execute_update(self, query, params=()):
        """执行更新"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor.lastrowid

    def backup_database(self, backup_path):
        """备份数据库"""
        import shutil
        try:
            shutil.copy2(self.db_name, backup_path)
            return True
        except Exception as e:
            print(f"备份失败: {e}")
            return False

    def restore_database(self, backup_path):
        """恢复数据库"""
        import shutil
        try:
            self.conn.close()
            shutil.copy2(backup_path, self.db_name)
            self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
            return True
        except Exception as e:
            print(f"恢复失败: {e}")
            return False

        # ==================== 财务计算核心（增强版）====================


class EnhancedFinancialCalculator:
    """增强的财务计算器"""

    @staticmethod
    def calculate_vat(amount, rate, is_inclusive=False):
        """增值税计算"""
        if is_inclusive:
            # 价税合计，计算税额
            tax_amount = amount * rate / (1 + rate)
            net_amount = amount - tax_amount
        else:
            # 不含税金额，计算税额
            tax_amount = amount * rate
            net_amount = amount

        return {
            'net_amount': round(net_amount, 2),
            'tax_amount': round(tax_amount, 2),
            'total_amount': round(net_amount + tax_amount, 2)
        }

    @staticmethod
    def calculate_corporate_tax(profit, rate=0.25):
        """企业所得税计算"""
        if profit <= 0:
            return 0

            # 小微企业优惠
        if profit <= 1000000:
            # 100万以下，5%税率
            tax = profit * 0.05
        elif profit <= 3000000:
            # 100-300万，10%税率
            tax = 1000000 * 0.05 + (profit - 1000000) * 0.10
        else:
            # 300万以上，25%税率
            tax = 1000000 * 0.05 + 2000000 * 0.10 + (profit - 3000000) * rate

        return round(tax, 2)

    @staticmethod
    def calculate_depreciation(original_value, salvage_rate, useful_life,
                               method='straight_line', periods_used=0):
        """折旧计算"""
        salvage_value = original_value * salvage_rate
        depreciable_value = original_value - salvage_value

        if method == 'straight_line':
            # 直线法
            monthly_depreciation = depreciable_value / (useful_life * 12)
            accumulated = monthly_depreciation * periods_used

        elif method == 'double_declining':
            # 双倍余额递减法
            rate = 2 / useful_life
            accumulated = 0
            remaining = original_value

            for i in range(periods_used):
                if i < useful_life * 12 - 24:  # 最后两年前
                    monthly_dep = remaining * rate / 12
                else:  # 最后两年改直线法
                    monthly_dep = (remaining - salvage_value) / (useful_life * 12 - i)

                accumulated += monthly_dep
                remaining -= monthly_dep

            monthly_depreciation = monthly_dep

        elif method == 'sum_of_years':
            # 年数总和法
            n = useful_life
            sum_years = n * (n + 1) / 2

            year = periods_used // 12 + 1
            remaining_years = n - year + 1
            annual_rate = remaining_years / sum_years
            monthly_depreciation = depreciable_value * annual_rate / 12

            accumulated = 0
            for i in range(periods_used):
                y = i // 12 + 1
                ry = n - y + 1
                accumulated += depreciable_value * (ry / sum_years) / 12

        else:
            monthly_depreciation = 0
            accumulated = 0

        net_value = original_value - accumulated

        return {
            'monthly_depreciation': round(monthly_depreciation, 2),
            'accumulated_depreciation': round(accumulated, 2),
            'net_value': round(net_value, 2)
        }

    @staticmethod
    def calculate_break_even(fixed_cost, price, variable_cost):
        """盈亏平衡分析"""
        if price <= variable_cost:
            return None

        break_even_quantity = fixed_cost / (price - variable_cost)
        break_even_sales = break_even_quantity * price

        return {
            'quantity': round(break_even_quantity, 2),
            'sales': round(break_even_sales, 2),
            'contribution_margin': round(price - variable_cost, 2),
            'contribution_margin_ratio': round((price - variable_cost) / price * 100, 2)
        }

    @staticmethod
    def aging_analysis(receivables):
        """账龄分析"""
        today = datetime.now()
        aging_groups = {
            '0-30天': 0,
            '31-60天': 0,
            '61-90天': 0,
            '91-180天': 0,
            '180天以上': 0
        }

        for rec in receivables:
            bill_date = datetime.strptime(rec['date'], '%Y-%m-%d')
            days = (today - bill_date).days
            amount = rec['amount']

            if days <= 30:
                aging_groups['0-30天'] += amount
            elif days <= 60:
                aging_groups['31-60天'] += amount
            elif days <= 90:
                aging_groups['61-90天'] += amount
            elif days <= 180:
                aging_groups['91-180天'] += amount
            else:
                aging_groups['180天以上'] += amount

        return aging_groups

    @staticmethod
    def du_pont_analysis(net_profit, sales, assets, equity):
        """杜邦分析"""
        if sales == 0 or assets == 0 or equity == 0:
            return None

        net_profit_margin = net_profit / sales  # 销售净利率
        asset_turnover = sales / assets  # 资产周转率
        equity_multiplier = assets / equity  # 权益乘数
        roe = net_profit_margin * asset_turnover * equity_multiplier  # ROE

        return {
            '销售净利率': round(net_profit_margin * 100, 2),
            '资产周转率': round(asset_turnover, 2),
            '权益乘数': round(equity_multiplier, 2),
            'ROE': round(roe * 100, 2)
        }

    # ==================== 凭证管理对话框 ====================


class VoucherDialog(QDialog):
    """会计凭证录入对话框"""

    def __init__(self, db, parent=None, voucher_id=None):
        super().__init__(parent)
        self.db = db
        self.voucher_id = voucher_id
        self.init_ui()
        if voucher_id:
            self.load_voucher()

    def init_ui(self):
        self.setWindowTitle('会计凭证')
        self.setMinimumSize(900, 600)

        layout = QVBoxLayout(self)

        # 凭证头
        header_group = QGroupBox('凭证信息')
        header_layout = QGridLayout()

        header_layout.addWidget(QLabel('凭证字号:'), 0, 0)
        self.voucher_no = QLineEdit()
        self.voucher_no.setText(f'记-{datetime.now().strftime("%Y%m%d")}-001')
        header_layout.addWidget(self.voucher_no, 0, 1)

        header_layout.addWidget(QLabel('凭证日期:'), 0, 2)
        self.voucher_date = QDateEdit()
        self.voucher_date.setDate(QDate.currentDate())
        self.voucher_date.setCalendarPopup(True)
        header_layout.addWidget(self.voucher_date, 0, 3)

        header_layout.addWidget(QLabel('凭证类型:'), 1, 0)
        self.voucher_type = QComboBox()
        self.voucher_type.addItems(['记账凭证', '收款凭证', '付款凭证', '转账凭证'])
        header_layout.addWidget(self.voucher_type, 1, 1)

        header_layout.addWidget(QLabel('制单人:'), 1, 2)
        self.creator = QLineEdit()
        self.creator.setText('管理员')
        header_layout.addWidget(self.creator, 1, 3)

        header_group.setLayout(header_layout)
        layout.addWidget(header_group)

        # 凭证明细
        detail_group = QGroupBox('凭证分录')
        detail_layout = QVBoxLayout()

        # 工具栏
        toolbar = QHBoxLayout()
        add_line_btn = QPushButton('➕ 添加行')
        add_line_btn.clicked.connect(self.add_line)
        toolbar.addWidget(add_line_btn)

        del_line_btn = QPushButton('➖ 删除行')
        del_line_btn.clicked.connect(self.delete_line)
        toolbar.addWidget(del_line_btn)

        toolbar.addStretch()
        detail_layout.addLayout(toolbar)

        # 明细表格
        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(5)
        self.detail_table.setHorizontalHeaderLabels(['摘要', '会计科目', '科目名称', '借方金额', '贷方金额'])
        self.detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.detail_table.setMinimumHeight(300)
        detail_layout.addWidget(self.detail_table)

        # 合计
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        total_layout.addWidget(QLabel('借方合计:'))
        self.total_debit = QLabel('0.00')
        self.total_debit.setStyleSheet('font-weight: bold; color: #2c3e50;')
        total_layout.addWidget(self.total_debit)

        total_layout.addWidget(QLabel('贷方合计:'))
        self.total_credit = QLabel('0.00')
        self.total_credit.setStyleSheet('font-weight: bold; color: #2c3e50;')
        total_layout.addWidget(self.total_credit)

        total_layout.addWidget(QLabel('平衡差额:'))
        self.balance_diff = QLabel('0.00')
        self.balance_diff.setStyleSheet('font-weight: bold; color: #e74c3c;')
        total_layout.addWidget(self.balance_diff)

        detail_layout.addLayout(total_layout)

        detail_group.setLayout(detail_layout)
        layout.addWidget(detail_group)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton('💾 保存')
        save_btn.clicked.connect(self.save_voucher)
        button_layout.addWidget(save_btn)

        audit_btn = QPushButton('✓ 审核')
        audit_btn.clicked.connect(self.audit_voucher)
        button_layout.addWidget(audit_btn)

        cancel_btn = QPushButton('✗ 取消')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        # 初始化两行
        self.add_line()
        self.add_line()

        # 连接信号
        self.detail_table.cellChanged.connect(self.calculate_totals)

    def add_line(self):
        """添加明细行"""
        row = self.detail_table.rowCount()
        self.detail_table.insertRow(row)

        # 摘要
        abstract_item = QTableWidgetItem('')
        self.detail_table.setItem(row, 0, abstract_item)

        # 科目代码（带下拉）
        account_combo = QComboBox()
        accounts = self.db.execute_query('SELECT code, name FROM accounts ORDER BY code')
        for code, name in accounts:
            account_combo.addItem(f'{code}', code)
        account_combo.currentIndexChanged.connect(lambda: self.on_account_selected(row))
        self.detail_table.setCellWidget(row, 1, account_combo)

        # 科目名称
        name_item = QTableWidgetItem('')
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        self.detail_table.setItem(row, 2, name_item)

        # 借方
        debit_item = QTableWidgetItem('0.00')
        self.detail_table.setItem(row, 3, debit_item)

        # 贷方
        credit_item = QTableWidgetItem('0.00')
        self.detail_table.setItem(row, 4, credit_item)

    def delete_line(self):
        """删除当前行"""
        current_row = self.detail_table.currentRow()
        if current_row >= 0:
            self.detail_table.removeRow(current_row)
            self.calculate_totals()

    def on_account_selected(self, row):
        """科目选择事件"""
        combo = self.detail_table.cellWidget(row, 1)
        if combo:
            code = combo.currentData()
            result = self.db.execute_query('SELECT name FROM accounts WHERE code = ?', (code,))
            if result:
                self.detail_table.item(row, 2).setText(result[0][0])

    def calculate_totals(self):
        """计算借贷合计"""
        total_debit = 0
        total_credit = 0

        for row in range(self.detail_table.rowCount()):
            try:
                debit = float(self.detail_table.item(row, 3).text() or 0)
                credit = float(self.detail_table.item(row, 4).text() or 0)
                total_debit += debit
                total_credit += credit
            except:
                pass

        self.total_debit.setText(f'{total_debit:.2f}')
        self.total_credit.setText(f'{total_credit:.2f}')

        diff = abs(total_debit - total_credit)
        self.balance_diff.setText(f'{diff:.2f}')

        if diff < 0.01:
            self.balance_diff.setStyleSheet('font-weight: bold; color: #27ae60;')
        else:
            self.balance_diff.setStyleSheet('font-weight: bold; color: #e74c3c;')

    def save_voucher(self):
        """保存凭证"""
        # 验证借贷平衡
        if abs(float(self.total_debit.text()) - float(self.total_credit.text())) > 0.01:
            QMessageBox.warning(self, '错误', '借贷不平衡，无法保存！')
            return

        try:
            # 保存凭证头
            voucher_data = (
                self.voucher_no.text(),
                self.voucher_date.date().toString('yyyy-MM-dd'),
                self.voucher_type.currentText(),
                float(self.total_debit.text()),
                float(self.total_credit.text()),
                '',
                self.creator.text(),
                '',
                'draft',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )

            if self.voucher_id:
                # 更新
                query = '''UPDATE vouchers \
                           SET voucher_no=?, \
                               voucher_date=?, \
                               voucher_type=?, \
                               total_debit=?, \
                               total_credit=?, \
                               abstract=?, \
                               creator=?
                           WHERE id = ?'''
                self.db.execute_update(query, voucher_data[:-2] + (self.voucher_id,))
                voucher_id = self.voucher_id

                # 删除旧明细
                self.db.execute_update('DELETE FROM voucher_details WHERE voucher_id=?',
                                       (voucher_id,))
            else:
                # 新增
                query = '''INSERT INTO vouchers (voucher_no, voucher_date, voucher_type,
                                                 total_debit, total_credit, abstract, creator, auditor, status, \
                                                 created_date)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
                voucher_id = self.db.execute_update(query, voucher_data)

                # 保存明细
            for row in range(self.detail_table.rowCount()):
                combo = self.detail_table.cellWidget(row, 1)
                if not combo:
                    continue

                abstract = self.detail_table.item(row, 0).text()
                account_code = combo.currentData()
                account_name = self.detail_table.item(row, 2).text()
                debit = float(self.detail_table.item(row, 3).text() or 0)
                credit = float(self.detail_table.item(row, 4).text() or 0)

                if debit > 0 or credit > 0:
                    detail_query = '''INSERT INTO voucher_details
                                      (voucher_id, line_no, account_code, account_name,
                                       abstract, debit, credit)
                                      VALUES (?, ?, ?, ?, ?, ?, ?)'''
                    self.db.execute_update(detail_query,
                                           (voucher_id, row + 1, account_code, account_name,
                                            abstract, debit, credit))

                    # 记录日志
            self.db.add_log('操作', '凭证管理', '保存凭证', self.creator.text(),
                            f'凭证号: {self.voucher_no.text()}')

            QMessageBox.information(self, '成功', '凭证保存成功！')
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, '错误', f'保存失败: {str(e)}')

    def audit_voucher(self):
        """审核凭证"""
        self.save_voucher()
        if self.voucher_id:
            self.db.execute_update(
                'UPDATE vouchers SET status=?, auditor=? WHERE id=?',
                ('audited', self.creator.text(), self.voucher_id)
            )
            QMessageBox.information(self, '成功', '凭证审核通过！')

    def load_voucher(self):
        """加载凭证"""
        # TODO: 实现凭证加载逻辑
        pass

    # ==================== 主窗口 ====================


class FinancialEnterpriseSystem(QMainWindow):
    """企业级财务管理系统主窗口"""

    def __init__(self):
        super().__init__()
        self.db = EnhancedDatabaseManager()
        self.calc = EnhancedFinancialCalculator()
        self.current_user = '管理员'
        self.init_ui()
        self.apply_modern_style()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle('FinancialCalculatorPro Enterprise - 企业级财务管理系统 v2.0')
        self.setGeometry(50, 50, 1600, 1000)

        # 创建菜单栏
        self.create_menus()

        # 创建工具栏
        self.create_toolbars()

        # 创建状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage('就绪')

        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 左侧导航栏
        self.create_sidebar()
        main_layout.addWidget(self.sidebar)

        # 右侧内容区
        self.content_stack = QTabWidget()
        self.content_stack.setTabsClosable(True)
        self.content_stack.setMovable(True)
        self.content_stack.tabCloseRequested.connect(self.close_tab)
        main_layout.addWidget(self.content_stack, 1)

        # 添加欢迎页
        self.add_welcome_page()

    def create_menus(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu('📁 文件')

        new_action = QAction('新建账套', self)
        new_action.setShortcut('Ctrl+N')
        file_menu.addAction(new_action)

        open_action = QAction('打开账套', self)
        open_action.setShortcut('Ctrl+O')
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        backup_action = QAction('备份数据', self)
        backup_action.triggered.connect(self.backup_data)
        file_menu.addAction(backup_action)

        restore_action = QAction('恢复数据', self)
        restore_action.triggered.connect(self.restore_data)
        file_menu.addAction(restore_action)

        file_menu.addSeparator()

        import_action = QAction('导入数据', self)
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)

        export_action = QAction('导出数据', self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 编辑菜单
        edit_menu = menubar.addMenu('✏️ 编辑')

        # 凭证菜单
        voucher_menu = menubar.addMenu('📝 凭证')

        new_voucher = QAction('新建凭证', self)
        new_voucher.setShortcut('Ctrl+V')
        new_voucher.triggered.connect(self.new_voucher)
        voucher_menu.addAction(new_voucher)

        # 账簿菜单
        book_menu = menubar.addMenu('📚 账簿')

        general_ledger = QAction('总账', self)
        book_menu.addAction(general_ledger)

        detail_ledger = QAction('明细账', self)
        book_menu.addAction(detail_ledger)

        # 报表菜单
        report_menu = menubar.addMenu('📊 报表')

        balance_sheet = QAction('资产负债表', self)
        report_menu.addAction(balance_sheet)

        income_statement = QAction('利润表', self)
        report_menu.addAction(income_statement)

        cash_flow = QAction('现金流量表', self)
        report_menu.addAction(cash_flow)

        # 工具菜单
        tool_menu = menubar.addMenu('🔧 工具')

        calculator = QAction('财务计算器', self)
        tool_menu.addAction(calculator)

        # 帮助菜单
        help_menu = menubar.addMenu('❓ 帮助')

        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbars(self):
        """创建工具栏"""
        toolbar = QToolBar('主工具栏')
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # 凭证
        voucher_btn = QAction('📝\n凭证', self)
        voucher_btn.triggered.connect(self.new_voucher)
        toolbar.addAction(voucher_btn)

        toolbar.addSeparator()

        # 报表
        report_btn = QAction('📊\n报表', self)
        toolbar.addAction(report_btn)

        toolbar.addSeparator()

        # 查询
        query_btn = QAction('🔍\n查询', self)
        toolbar.addAction(query_btn)

        toolbar.addSeparator()

        # 打印
        print_btn = QAction('🖨️\n打印', self)
        toolbar.addAction(print_btn)

    def create_sidebar(self):
        """创建侧边栏"""
        self.sidebar = QFrame()
        self.sidebar.setFrameStyle(QFrame.StyledPanel)
        self.sidebar.setMaximumWidth(220)
        self.sidebar.setMinimumWidth(220)

        layout = QVBoxLayout(self.sidebar)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 10, 5, 10)

        # Logo
        logo_label = QLabel('💰 财务系统')
        logo_font = QFont()
        logo_font.setPointSize(16)
        logo_font.setBold(True)
        logo_label.setFont(logo_font)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet('color: #2c3e50; padding: 10px;')
        layout.addWidget(logo_label)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # 导航按钮
        nav_items = [
            ('🏠 工作台', self.show_dashboard),
            ('📝 凭证管理', self.show_voucher_management),
            ('📚 账簿查询', self.show_ledger_query),
            ('📊 财务报表', self.show_financial_reports),
            ('💰 资金管理', self.show_cash_management),
            ('🏢 固定资产', self.show_fixed_assets),
            ('👥 往来管理', self.show_ar_ap_management),
            ('💵 工资管理', self.show_payroll),
            ('📦 成本核算', self.show_cost_accounting),
            ('📋 预算管理', self.show_budget_management),
            ('🧾 发票管理', self.show_invoice_management),
            ('💹 财务分析', self.show_financial_analysis),
            ('🔧 系统设置', self.show_system_settings),
        ]

        for text, handler in nav_items:
            btn = QPushButton(text)
            btn.setStyleSheet('''  
                QPushButton {  
                    text-align: left;  
                    padding: 12px 15px;  
                    border: none;  
                    background-color: transparent;  
                    border-radius: 5px;  
                    font-size: 13px;  
                }  
                QPushButton:hover {  
                    background-color: #ecf0f1;  
                }  
                QPushButton:pressed {  
                    background-color: #bdc3c7;  
                }  
            ''')
            btn.clicked.connect(handler)
            layout.addWidget(btn)

        layout.addStretch()

        # 用户信息
        user_frame = QFrame()
        user_frame.setFrameStyle(QFrame.Box)
        user_layout = QVBoxLayout(user_frame)
        user_label = QLabel(f'👤 {self.current_user}')
        user_label.setAlignment(Qt.AlignCenter)
        user_layout.addWidget(user_label)
        layout.addWidget(user_frame)

    def apply_modern_style(self):
        """应用现代化样式"""
        self.setStyleSheet('''  
            QMainWindow {  
                background-color: #f5f6fa;  
            }  
            QFrame#sidebar {  
                background-color: #ffffff;  
                border-right: 1px solid #dcdde1;  
            }  
            QTabWidget::pane {  
                border: 1px solid #dcdde1;  
                background-color: #ffffff;  
                border-radius: 5px;  
            }  
            QTabBar::tab {  
                background-color: #ecf0f1;  
                padding: 10px 20px;  
                margin-right: 2px;  
                border-top-left-radius: 5px;  
                border-top-right-radius: 5px;  
                color: #2c3e50;  
            }  
            QTabBar::tab:selected {  
                background-color: #ffffff;  
                border-bottom: 3px solid #3498db;  
                font-weight: bold;  
            }  
            QTabBar::tab:hover {  
                background-color: #d5dbdb;  
            }  
            QGroupBox {  
                font-weight: bold;  
                border: 2px solid #bdc3c7;  
                border-radius: 8px;  
                margin-top: 15px;  
                padding-top: 15px;  
                background-color: #ffffff;  
            }  
            QGroupBox::title {  
                color: #2c3e50;  
                subcontrol-origin: margin;  
                left: 10px;  
                padding: 0 5px;  
            }  
            QPushButton {  
                background-color: #3498db;  
                color: white;  
                border: none;  
                padding: 10px 20px;  
                border-radius: 5px;  
                font-weight: bold;  
                min-width: 80px;  
            }  
            QPushButton:hover {  
                background-color: #2980b9;  
            }  
            QPushButton:pressed {  
                background-color: #21618c;  
            }  
            QPushButton:disabled {  
                background-color: #95a5a6;  
            }  
            QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox, QDateEdit {  
                padding: 8px;  
                border: 2px solid #bdc3c7;  
                border-radius: 5px;  
                background-color: #ffffff;  
            }  
            QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {  
                border: 2px solid #3498db;  
            }  
            QTableWidget {  
                gridline-color: #ecf0f1;  
                background-color: #ffffff;  
                border: 1px solid #bdc3c7;  
                border-radius: 5px;  
            }  
            QTableWidget::item {  
                padding: 5px;  
            }  
            QTableWidget::item:selected {  
                background-color: #3498db;  
                color: white;  
            }  
            QHeaderView::section {  
                background-color: #34495e;  
                color: white;  
                padding: 8px;  
                border: none;  
                font-weight: bold;  
            }  
            QTextEdit {  
                border: 2px solid #bdc3c7;  
                border-radius: 5px;  
                background-color: #ffffff;  
                padding: 5px;  
            }  
            QMenuBar {  
                background-color: #34495e;  
                color: white;  
                padding: 5px;  
            }  
            QMenuBar::item {  
                padding: 5px 10px;  
                background-color: transparent;  
            }  
            QMenuBar::item:selected {  
                background-color: #2c3e50;  
            }  
            QMenu {  
                background-color: #ffffff;  
                border: 1px solid #bdc3c7;  
            }  
            QMenu::item {  
                padding: 8px 30px;  
            }  
            QMenu::item:selected {  
                background-color: #3498db;  
                color: white;  
            }  
            QToolBar {  
                background-color: #ecf0f1;  
                border-bottom: 1px solid #bdc3c7;  
                spacing: 10px;  
                padding: 5px;  
            }  
            QStatusBar {  
                background-color: #34495e;  
                color: white;  
            }  
        ''')

    def add_welcome_page(self):
        """添加欢迎页"""
        welcome_widget = QWidget()
        layout = QVBoxLayout(welcome_widget)
        layout.setAlignment(Qt.AlignCenter)

        # 标题
        title = QLabel('🏢 欢迎使用企业级财务管理系统')
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 副标题
        subtitle = QLabel('FinancialCalculatorPro Enterprise Edition v2.0')
        subtitle_font = QFont()
        subtitle_font.setPointSize(14)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet('color: #7f8c8d; margin: 10px;')
        layout.addWidget(subtitle)

        # 功能卡片网格
        cards_widget = QWidget()
        cards_layout = QGridLayout(cards_widget)
        cards_layout.setSpacing(20)

        features = [
            ('📝', '凭证管理', '快速录入会计凭证'),
            ('📊', '财务报表', '自动生成三大报表'),
            ('💰', '资金管理', '实时监控资金流向'),
            ('🏢', '固定资产', '资产全生命周期管理'),
            ('👥', '往来管理', '应收应付智能分析'),
            ('💵', '工资管理', '一键计算员工薪资'),
            ('📦', '成本核算', '精准成本分析'),
            ('💹', '财务分析', '多维度数据分析'),
        ]

        for i, (icon, title, desc) in enumerate(features):
            card = self.create_feature_card(icon, title, desc)
            cards_layout.addWidget(card, i // 4, i % 4)

        layout.addWidget(cards_widget)

        # 快速开始按钮
        quick_start_layout = QHBoxLayout()
        quick_start_layout.setAlignment(Qt.AlignCenter)

        new_voucher_btn = QPushButton('📝 新建凭证')
        new_voucher_btn.setMinimumSize(150, 50)
        new_voucher_btn.clicked.connect(self.new_voucher)
        quick_start_layout.addWidget(new_voucher_btn)

        view_report_btn = QPushButton('📊 查看报表')
        view_report_btn.setMinimumSize(150, 50)
        view_report_btn.clicked.connect(self.show_financial_reports)
        quick_start_layout.addWidget(view_report_btn)

        layout.addLayout(quick_start_layout)

        self.content_stack.addTab(welcome_widget, '🏠 工作台')

    def create_feature_card(self, icon, title, description):
        """创建功能卡片"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet('''  
            QFrame {  
                background-color: #ffffff;  
                border: 2px solid #ecf0f1;  
                border-radius: 10px;  
                padding: 15px;  
            }  
            QFrame:hover {  
                border: 2px solid #3498db;  
            }  
        ''')
        card.setMinimumSize(200, 120)

        layout = QVBoxLayout(card)

        icon_label = QLabel(icon)
        icon_font = QFont()
        icon_font.setPointSize(32)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet('color: #7f8c8d; font-size: 10px;')
        layout.addWidget(desc_label)

        return card

    def close_tab(self, index):
        """关闭标签页"""
        if index > 0:  # 不关闭工作台
            self.content_stack.removeTab(index)

    def new_voucher(self):
        """新建凭证"""
        dialog = VoucherDialog(self.db, self)
        if dialog.exec_() == QDialog.Accepted:
            self.statusBar.showMessage('凭证保存成功', 3000)

    def show_dashboard(self):
        """显示工作台"""
        self.content_stack.setCurrentIndex(0)

    def show_voucher_management(self):
        """显示凭证管理"""
        widget = self.create_voucher_list_widget()
        self.add_or_switch_tab(widget, '📝 凭证管理')

    def create_voucher_list_widget(self):
        """创建凭证列表控件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 工具栏
        toolbar = QHBoxLayout()

        new_btn = QPushButton('➕ 新建')
        new_btn.clicked.connect(self.new_voucher)
        toolbar.addWidget(new_btn)

        edit_btn = QPushButton('✏️ 修改')
        toolbar.addWidget(edit_btn)

        delete_btn = QPushButton('🗑️ 删除')
        toolbar.addWidget(delete_btn)

        audit_btn = QPushButton('✓ 审核')
        toolbar.addWidget(audit_btn)

        toolbar.addStretch()

        # 搜索
        search_box = QLineEdit()
        search_box.setPlaceholderText('搜索凭证...')
        search_box.setMaximumWidth(200)
        toolbar.addWidget(search_box)

        search_btn = QPushButton('🔍 搜索')
        toolbar.addWidget(search_btn)

        layout.addLayout(toolbar)

        # 凭证列表
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            '凭证号', '日期', '类型', '借方合计', '贷方合计',
            '制单人', '审核人', '状态'
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 加载数据
        vouchers = self.db.execute_query('''
                                         SELECT voucher_no,
                                                voucher_date,
                                                voucher_type,
                                                total_debit,
                                                total_credit,
                                                creator,
                                                auditor,
                                                status
                                         FROM vouchers
                                         ORDER BY created_date DESC
                                         LIMIT 100
                                         ''')

        table.setRowCount(len(vouchers))
        for row, voucher in enumerate(vouchers):
            for col, value in enumerate(voucher):
                if col in [3, 4]:  # 金额列
                    item = QTableWidgetItem(f'{float(value):,.2f}')
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif col == 7:  # 状态列
                    status_text = '草稿' if value == 'draft' else '已审核'
                    item = QTableWidgetItem(status_text)
                    if value == 'audited':
                        item.setForeground(QColor('#27ae60'))
                else:
                    item = QTableWidgetItem(str(value) if value else '')
                table.setItem(row, col, item)

        layout.addWidget(table)

        return widget

    def show_ledger_query(self):
        """显示账簿查询"""
        widget = self.create_ledger_query_widget()
        self.add_or_switch_tab(widget, '📚 账簿查询')

    def create_ledger_query_widget(self):
        """创建账簿查询控件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 查询条件
        query_group = QGroupBox('查询条件')
        query_layout = QGridLayout()

        query_layout.addWidget(QLabel('账簿类型:'), 0, 0)
        ledger_type = QComboBox()
        ledger_type.addItems(['总账', '明细账', '日记账', '多栏账'])
        query_layout.addWidget(ledger_type, 0, 1)

        query_layout.addWidget(QLabel('会计科目:'), 0, 2)
        account_combo = QComboBox()
        accounts = self.db.execute_query('SELECT code, name FROM accounts ORDER BY code')
        for code, name in accounts:
            account_combo.addItem(f'{code} {name}')
        query_layout.addWidget(account_combo, 0, 3)

        query_layout.addWidget(QLabel('开始日期:'), 1, 0)
        start_date = QDateEdit()
        start_date.setDate(QDate.currentDate().addMonths(-1))
        start_date.setCalendarPopup(True)
        query_layout.addWidget(start_date, 1, 1)

        query_layout.addWidget(QLabel('结束日期:'), 1, 2)
        end_date = QDateEdit()
        end_date.setDate(QDate.currentDate())
        end_date.setCalendarPopup(True)
        query_layout.addWidget(end_date, 1, 3)

        query_btn = QPushButton('🔍 查询')
        query_layout.addWidget(query_btn, 2, 0, 1, 2)

        export_btn = QPushButton('📤 导出')
        export_btn.clicked.connect(lambda: self.export_ledger(table))
        query_layout.addWidget(export_btn, 2, 2, 1, 2)

        query_group.setLayout(query_layout)
        layout.addWidget(query_group)

        # 账簿数据
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            '日期', '凭证号', '摘要', '借方金额', '贷方金额',
            '方向', '余额', '对方科目'
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)

        # 合计行
        summary_layout = QHBoxLayout()
        summary_layout.addStretch()
        summary_layout.addWidget(QLabel('借方合计:'))
        total_debit_label = QLabel('0.00')
        total_debit_label.setStyleSheet('font-weight: bold; color: #2c3e50;')
        summary_layout.addWidget(total_debit_label)

        summary_layout.addWidget(QLabel('贷方合计:'))
        total_credit_label = QLabel('0.00')
        total_credit_label.setStyleSheet('font-weight: bold; color: #2c3e50;')
        summary_layout.addWidget(total_credit_label)

        summary_layout.addWidget(QLabel('期末余额:'))
        balance_label = QLabel('0.00')
        balance_label.setStyleSheet('font-weight: bold; color: #27ae60;')
        summary_layout.addWidget(balance_label)

        layout.addLayout(summary_layout)

        return widget

    def show_financial_reports(self):
        """显示财务报表"""
        widget = self.create_financial_reports_widget()
        self.add_or_switch_tab(widget, '📊 财务报表')

    def create_financial_reports_widget(self):
        """创建财务报表控件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 报表类型选择
        toolbar = QHBoxLayout()

        report_type = QComboBox()
        report_type.addItems(['资产负债表', '利润表', '现金流量表'])
        report_type.currentIndexChanged.connect(lambda: self.load_report(report_type.currentText(), report_table))
        toolbar.addWidget(report_type)

        period_label = QLabel('会计期间:')
        toolbar.addWidget(period_label)

        period_combo = QComboBox()
        current_year = datetime.now().year
        for year in range(current_year - 5, current_year + 1):
            for month in range(1, 13):
                period_combo.addItem(f'{year}-{month:02d}')
        period_combo.setCurrentIndex(period_combo.count() - 1)
        toolbar.addWidget(period_combo)

        toolbar.addStretch()

        refresh_btn = QPushButton('🔄 刷新')
        refresh_btn.clicked.connect(lambda: self.load_report(report_type.currentText(), report_table))
        toolbar.addWidget(refresh_btn)

        print_btn = QPushButton('🖨️ 打印')
        toolbar.addWidget(print_btn)

        export_btn = QPushButton('📤 导出')
        export_btn.clicked.connect(lambda: self.export_report(report_table))
        toolbar.addWidget(export_btn)

        layout.addLayout(toolbar)

        # 报表表格
        report_table = QTableWidget()
        layout.addWidget(report_table)

        # 加载默认报表
        self.load_report('资产负债表', report_table)

        return widget

    def load_report(self, report_type, table):
        """加载报表"""
        if report_type == '资产负债表':
            self.load_balance_sheet(table)
        elif report_type == '利润表':
            self.load_income_statement(table)
        elif report_type == '现金流量表':
            self.load_cash_flow_statement(table)

    def load_balance_sheet(self, table):
        """加载资产负债表"""
        table.clear()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(['资产', '金额', '负债和所有者权益', '金额'])

        # 模拟数据
        assets = [
            ('流动资产:', ''),
            ('  货币资金', '1,000,000.00'),
            ('  应收账款', '500,000.00'),
            ('  存货', '800,000.00'),
            ('流动资产合计', '2,300,000.00'),
            ('', ''),
            ('非流动资产:', ''),
            ('  固定资产', '5,000,000.00'),
            ('  无形资产', '500,000.00'),
            ('非流动资产合计', '5,500,000.00'),
            ('', ''),
            ('资产总计', '7,800,000.00'),
        ]

        liabilities = [
            ('流动负债:', ''),
            ('  短期借款', '500,000.00'),
            ('  应付账款', '300,000.00'),
            ('流动负债合计', '800,000.00'),
            ('', ''),
            ('非流动负债:', ''),
            ('  长期借款', '2,000,000.00'),
            ('非流动负债合计', '2,000,000.00'),
            ('负债合计', '2,800,000.00'),
            ('', ''),
            ('所有者权益:', ''),
            ('  实收资本', '3,000,000.00'),
            ('  未分配利润', '2,000,000.00'),
            ('所有者权益合计', '5,000,000.00'),
            ('', ''),
            ('负债和所有者权益总计', '7,800,000.00'),
        ]

        max_rows = max(len(assets), len(liabilities))
        table.setRowCount(max_rows)

        for row in range(max_rows):
            if row < len(assets):
                item1 = QTableWidgetItem(assets[row][0])
                item2 = QTableWidgetItem(assets[row][1])
                if assets[row][0].endswith('合计') or assets[row][0].endswith('总计'):
                    font = item1.font()
                    font.setBold(True)
                    item1.setFont(font)
                    item2.setFont(font)
                table.setItem(row, 0, item1)
                table.setItem(row, 1, item2)

            if row < len(liabilities):
                item3 = QTableWidgetItem(liabilities[row][0])
                item4 = QTableWidgetItem(liabilities[row][1])
                if liabilities[row][0].endswith('合计') or liabilities[row][0].endswith('总计'):
                    font = item3.font()
                    font.setBold(True)
                    item3.setFont(font)
                    item4.setFont(font)
                table.setItem(row, 2, item3)
                table.setItem(row, 3, item4)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def load_income_statement(self, table):
        """加载利润表"""
        table.clear()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(['项目', '本月金额', '本年累计'])

        data = [
            ('一、营业收入', '5,000,000.00', '50,000,000.00'),
            ('减：营业成本', '3,000,000.00', '30,000,000.00'),
            ('    税金及附加', '100,000.00', '1,000,000.00'),
            ('    销售费用', '500,000.00', '5,000,000.00'),
            ('    管理费用', '400,000.00', '4,000,000.00'),
            ('    财务费用', '100,000.00', '1,000,000.00'),
            ('加：投资收益', '50,000.00', '500,000.00'),
            ('二、营业利润', '950,000.00', '9,500,000.00'),
            ('加：营业外收入', '20,000.00', '200,000.00'),
            ('减：营业外支出', '10,000.00', '100,000.00'),
            ('三、利润总额', '960,000.00', '9,600,000.00'),
            ('减：所得税费用', '240,000.00', '2,400,000.00'),
            ('四、净利润', '720,000.00', '7,200,000.00'),
        ]

        table.setRowCount(len(data))
        for row, (item, current, ytd) in enumerate(data):
            item_widget = QTableWidgetItem(item)
            current_widget = QTableWidgetItem(current)
            ytd_widget = QTableWidgetItem(ytd)

            if item.startswith(('一、', '二、', '三、', '四、')):
                font = item_widget.font()
                font.setBold(True)
                item_widget.setFont(font)
                current_widget.setFont(font)
                ytd_widget.setFont(font)

            current_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            ytd_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            table.setItem(row, 0, item_widget)
            table.setItem(row, 1, current_widget)
            table.setItem(row, 2, ytd_widget)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def load_cash_flow_statement(self, table):
        """加载现金流量表"""
        table.clear()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(['项目', '金额'])

        data = [
            ('一、经营活动产生的现金流量:', ''),
            ('  销售商品、提供劳务收到的现金', '5,200,000.00'),
            ('  收到的税费返还', '50,000.00'),
            ('  经营活动现金流入小计', '5,250,000.00'),
            ('  购买商品、接受劳务支付的现金', '3,200,000.00'),
            ('  支付给职工以及为职工支付的现金', '800,000.00'),
            ('  支付的各项税费', '600,000.00'),
            ('  经营活动现金流出小计', '4,600,000.00'),
            ('经营活动产生的现金流量净额', '650,000.00'),
            ('', ''),
            ('二、投资活动产生的现金流量:', ''),
            ('  购建固定资产支付的现金', '500,000.00'),
            ('投资活动产生的现金流量净额', '-500,000.00'),
            ('', ''),
            ('三、筹资活动产生的现金流量:', ''),
            ('  取得借款收到的现金', '1,000,000.00'),
            ('  偿还债务支付的现金', '500,000.00'),
            ('筹资活动产生的现金流量净额', '500,000.00'),
            ('', ''),
            ('四、现金及现金等价物净增加额', '650,000.00'),
            ('  期初现金及现金等价物余额', '350,000.00'),
            ('  期末现金及现金等价物余额', '1,000,000.00'),
        ]

        table.setRowCount(len(data))
        for row, (item, amount) in enumerate(data):
            item_widget = QTableWidgetItem(item)
            amount_widget = QTableWidgetItem(amount)

            if item.endswith('净额') or item.endswith('净增加额') or '合计' in item or '小计' in item:
                font = item_widget.font()
                font.setBold(True)
                item_widget.setFont(font)
                amount_widget.setFont(font)

            amount_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            table.setItem(row, 0, item_widget)
            table.setItem(row, 1, amount_widget)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def show_cash_management(self):
        """显示资金管理"""
        widget = self.create_cash_management_widget()
        self.add_or_switch_tab(widget, '💰 资金管理')

    def create_cash_management_widget(self):
        """创建资金管理控件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 资金概览
        overview_group = QGroupBox('资金概览')
        overview_layout = QGridLayout()

        cards_layout = QHBoxLayout()

        # 银行存款
        bank_card = self.create_info_card('🏦', '银行存款', '1,000,000.00', '#3498db')
        cards_layout.addWidget(bank_card)

        # 库存现金
        cash_card = self.create_info_card('💵', '库存现金', '50,000.00', '#27ae60')
        cards_layout.addWidget(cash_card)

        # 其他货币资金
        other_card = self.create_info_card('💳', '其他货币资金', '100,000.00', '#9b59b6')
        cards_layout.addWidget(other_card)

        # 资金总额
        total_card = self.create_info_card('💰', '资金总额', '1,150,000.00', '#e67e22')
        cards_layout.addWidget(total_card)

        overview_layout.addLayout(cards_layout, 0, 0)
        overview_group.setLayout(overview_layout)
        layout.addWidget(overview_group)

        # 银行账户列表
        account_group = QGroupBox('银行账户')
        account_layout = QVBoxLayout()

        account_table = QTableWidget()
        account_table.setColumnCount(6)
        account_table.setHorizontalHeaderLabels([
            '账户名称', '开户银行', '账号', '币种', '余额', '状态'
        ])
        account_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 示例数据
        accounts_data = [
            ('基本户', '中国工商银行', '6222 **** **** 1234', 'CNY', '800,000.00', '正常'),
            ('一般户', '中国建设银行', '6227 **** **** 5678', 'CNY', '200,000.00', '正常'),
        ]

        account_table.setRowCount(len(accounts_data))
        for row, data in enumerate(accounts_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(value)
                if col == 4:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                account_table.setItem(row, col, item)

        account_layout.addWidget(account_table)
        account_group.setLayout(account_layout)
        layout.addWidget(account_group)

        # 资金流水
        flow_group = QGroupBox('资金流水')
        flow_layout = QVBoxLayout()

        flow_table = QTableWidget()
        flow_table.setColumnCount(6)
        flow_table.setHorizontalHeaderLabels([
            '日期', '摘要', '收入', '支出', '余额', '凭证号'
        ])
        flow_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        flow_layout.addWidget(flow_table)

        flow_group.setLayout(flow_layout)
        layout.addWidget(flow_group)

        return widget

    def show_fixed_assets(self):
        """显示固定资产"""
        widget = self.create_fixed_assets_widget()
        self.add_or_switch_tab(widget, '🏢 固定资产')

    def create_fixed_assets_widget(self):
        """创建固定资产控件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 工具栏
        toolbar = QHBoxLayout()

        add_btn = QPushButton('➕ 新增资产')
        add_btn.clicked.connect(self.add_fixed_asset)
        toolbar.addWidget(add_btn)

        depreciation_btn = QPushButton('📊 计提折旧')
        depreciation_btn.clicked.connect(self.calculate_depreciation_dialog)
        toolbar.addWidget(depreciation_btn)

        disposal_btn = QPushButton('🗑️ 资产处置')
        toolbar.addWidget(disposal_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # 资产列表
        table = QTableWidget()
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels([
            '资产编号', '资产名称', '类别', '原值', '累计折旧',
            '净值', '购置日期', '使用年限', '状态'
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 加载数据
        assets = self.db.execute_query('''
                                       SELECT asset_code,
                                              asset_name,
                                              category,
                                              original_value,
                                              accumulated_depreciation,
                                              net_value,
                                              purchase_date,
                                              useful_life,
                                              status
                                       FROM fixed_assets
                                       ORDER BY asset_code
                                       ''')

        table.setRowCount(len(assets))
        for row, asset in enumerate(assets):
            for col, value in enumerate(asset):
                if col in [3, 4, 5]:  # 金额列
                    item = QTableWidgetItem(f'{float(value):,.2f}')
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif col == 8:  # 状态列
                    status_map = {'in_use': '使用中', 'idle': '闲置', 'disposed': '已处置'}
                    item = QTableWidgetItem(status_map.get(value, value))
                else:
                    item = QTableWidgetItem(str(value) if value else '')
                table.setItem(row, col, item)

        layout.addWidget(table)

        return widget

    def show_ar_ap_management(self):
        """显示往来管理"""
        widget = self.create_ar_ap_widget()
        self.add_or_switch_tab(widget, '👥 往来管理')

    def create_ar_ap_widget(self):
        """创建往来管理控件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 标签页
        tabs = QTabWidget()

        # 应收账款
        ar_widget = QWidget()
        ar_layout = QVBoxLayout(ar_widget)

        ar_toolbar = QHBoxLayout()
        ar_add_btn = QPushButton('➕ 新增应收')
        ar_add_btn.clicked.connect(self.add_receivable)
        ar_toolbar.addWidget(ar_add_btn)

        ar_receive_btn = QPushButton('💰 收款')
        ar_toolbar.addWidget(ar_receive_btn)

        ar_aging_btn = QPushButton('📊 账龄分析')
        ar_aging_btn.clicked.connect(self.show_aging_analysis)
        ar_toolbar.addWidget(ar_aging_btn)

        ar_toolbar.addStretch()
        ar_layout.addLayout(ar_toolbar)

        ar_table = QTableWidget()
        ar_table.setColumnCount(8)
        ar_table.setHorizontalHeaderLabels([
            '单据号', '客户', '应收金额', '已收金额', '未收金额',
            '账单日期', '到期日期', '状态'
        ])
        ar_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 加载应收数据
        receivables = self.db.execute_query('''
                                            SELECT bill_no,
                                                   customer_name,
                                                   amount,
                                                   received_amount,
                                                   balance,
                                                   bill_date,
                                                   due_date,
                                                   status
                                            FROM receivables
                                            ORDER BY bill_date DESC
                                            LIMIT 50
                                            ''')

        ar_table.setRowCount(len(receivables))
        for row, rec in enumerate(receivables):
            for col, value in enumerate(rec):
                if col in [2, 3, 4]:
                    item = QTableWidgetItem(f'{float(value):,.2f}')
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif col == 7:
                    status_map = {'pending': '未收款', 'partial': '部分收款', 'paid': '已收款'}
                    item = QTableWidgetItem(status_map.get(value, value))
                else:
                    item = QTableWidgetItem(str(value) if value else '')
                ar_table.setItem(row, col, item)

        ar_layout.addWidget(ar_table)
        tabs.addTab(ar_widget, '应收账款')

        # 应付账款
        ap_widget = QWidget()
        ap_layout = QVBoxLayout(ap_widget)

        ap_toolbar = QHBoxLayout()
        ap_add_btn = QPushButton('➕ 新增应付')
        ap_add_btn.clicked.connect(self.add_payable)
        ap_toolbar.addWidget(ap_add_btn)

        ap_pay_btn = QPushButton('💸 付款')
        ap_toolbar.addWidget(ap_pay_btn)

        ap_toolbar.addStretch()
        ap_layout.addLayout(ap_toolbar)

        ap_table = QTableWidget()
        ap_table.setColumnCount(8)
        ap_table.setHorizontalHeaderLabels([
            '单据号', '供应商', '应付金额', '已付金额', '未付金额',
            '账单日期', '到期日期', '状态'
        ])
        ap_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 加载应付数据
        payables = self.db.execute_query('''
                                         SELECT bill_no,
                                                supplier_name,
                                                amount,
                                                paid_amount,
                                                balance,
                                                bill_date,
                                                due_date,
                                                status
                                         FROM payables
                                         ORDER BY bill_date DESC
                                         LIMIT 50
                                         ''')

        ap_table.setRowCount(len(payables))
        for row, pay in enumerate(payables):
            for col, value in enumerate(pay):
                if col in [2, 3, 4]:
                    item = QTableWidgetItem(f'{float(value):,.2f}')
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif col == 7:
                    status_map = {'pending': '未付款', 'partial': '部分付款', 'paid': '已付款'}
                    item = QTableWidgetItem(status_map.get(value, value))
                else:
                    item = QTableWidgetItem(str(value) if value else '')
                ap_table.setItem(row, col, item)

        ap_layout.addWidget(ap_table)
        tabs.addTab(ap_widget, '应付账款')

        layout.addWidget(tabs)

        return widget

    def show_payroll(self):
        """显示工资管理"""
        widget = self.create_payroll_widget()
        self.add_or_switch_tab(widget, '💵 工资管理')

    def create_payroll_widget(self):
        """创建工资管理控件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 工具栏
        toolbar = QHBoxLayout()

        month_label = QLabel('工资月份:')
        toolbar.addWidget(month_label)

        month_edit = QLineEdit()
        month_edit.setText(datetime.now().strftime('%Y-%m'))
        month_edit.setMaximumWidth(100)
        toolbar.addWidget(month_edit)

        calculate_btn = QPushButton('🧮 批量计算')
        calculate_btn.clicked.connect(lambda: self.calculate_salaries(month_edit.text()))
        toolbar.addWidget(calculate_btn)

        import_btn = QPushButton('📥 导入工资')
        toolbar.addWidget(import_btn)

        pay_btn = QPushButton('💰 发放工资')
        toolbar.addWidget(pay_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # 工资表
        table = QTableWidget()
        table.setColumnCount(11)
        table.setHorizontalHeaderLabels([
            '员工编号', '姓名', '基本工资', '岗位津贴', '加班费',
            '奖金', '社保', '公积金', '个税', '实发工资', '状态'
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 加载工资数据
        salaries = self.db.execute_query('''
                                         SELECT emp_code,
                                                emp_name,
                                                base_salary,
                                                allowance,
                                                overtime_pay,
                                                bonus,
                                                social_security,
                                                housing_fund,
                                                income_tax,
                                                net_salary,
                                                status
                                         FROM salaries
                                         WHERE salary_month = ?
                                         ORDER BY emp_code
                                         ''', (datetime.now().strftime('%Y-%m'),))

        table.setRowCount(len(salaries))
        for row, salary in enumerate(salaries):
            for col, value in enumerate(salary):
                if col in range(2, 10):  # 金额列
                    item = QTableWidgetItem(f'{float(value):,.2f}')
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif col == 10:
                    status_map = {'unpaid': '未发放', 'paid': '已发放'}
                    item = QTableWidgetItem(status_map.get(value, value))
                else:
                    item = QTableWidgetItem(str(value) if value else '')
                table.setItem(row, col, item)

        layout.addWidget(table)

        return widget

    def show_cost_accounting(self):
        """显示成本核算"""
        widget = self.create_cost_accounting_widget()
        self.add_or_switch_tab(widget, '📦 成本核算')

    def create_cost_accounting_widget(self):
        """创建成本核算控件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 标签页
        tabs = QTabWidget()

        # 成本录入
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)

        input_form = QGroupBox('成本信息')
        form_layout = QGridLayout()

        form_layout.addWidget(QLabel('成本单号:'), 0, 0)
        cost_no = QLineEdit()
        cost_no.setText(f'CB{datetime.now().strftime("%Y%m%d")}001')
        form_layout.addWidget(cost_no, 0, 1)

        form_layout.addWidget(QLabel('产品名称:'), 0, 2)
        product_name = QLineEdit()
        form_layout.addWidget(product_name, 0, 3)

        form_layout.addWidget(QLabel('核算期间:'), 1, 0)
        period = QLineEdit()
        period.setText(datetime.now().strftime('%Y-%m'))
        form_layout.addWidget(period, 1, 1)

        form_layout.addWidget(QLabel('数量:'), 1, 2)
        quantity = QDoubleSpinBox()
        quantity.setRange(0, 1000000)
        quantity.setValue(100)
        form_layout.addWidget(quantity, 1, 3)

        form_layout.addWidget(QLabel('直接材料:'), 2, 0)
        material_cost = QDoubleSpinBox()
        material_cost.setRange(0, 10000000)
        material_cost.setDecimals(2)
        form_layout.addWidget(material_cost, 2, 1)

        form_layout.addWidget(QLabel('直接人工:'), 2, 2)
        labor_cost = QDoubleSpinBox()
        labor_cost.setRange(0, 10000000)
        labor_cost.setDecimals(2)
        form_layout.addWidget(labor_cost, 2, 3)

        form_layout.addWidget(QLabel('制造费用:'), 3, 0)
        manufacturing_cost = QDoubleSpinBox()
        manufacturing_cost.setRange(0, 10000000)
        manufacturing_cost.setDecimals(2)
        form_layout.addWidget(manufacturing_cost, 3, 1)

        form_layout.addWidget(QLabel('总成本:'), 3, 2)
        total_cost_label = QLabel('0.00')
        total_cost_label.setStyleSheet('font-weight: bold;')
        form_layout.addWidget(total_cost_label, 3, 3)

        form_layout.addWidget(QLabel('单位成本:'), 4, 0)
        unit_cost_label = QLabel('0.00')
        unit_cost_label.setStyleSheet('font-weight: bold;')
        form_layout.addWidget(unit_cost_label, 4, 1)

        def calculate_cost():
            mat = material_cost.value()
            lab = labor_cost.value()
            man = manufacturing_cost.value()
            total = mat + lab + man
            unit = total / quantity.value() if quantity.value() > 0 else 0
            total_cost_label.setText(f'{total:,.2f}')
            unit_cost_label.setText(f'{unit:,.2f}')

        material_cost.valueChanged.connect(calculate_cost)
        labor_cost.valueChanged.connect(calculate_cost)
        manufacturing_cost.valueChanged.connect(calculate_cost)
        quantity.valueChanged.connect(calculate_cost)

        save_cost_btn = QPushButton('💾 保存')
        save_cost_btn.clicked.connect(lambda: self.save_cost(
            cost_no.text(), product_name.text(), period.text(),
            material_cost.value(), labor_cost.value(), manufacturing_cost.value(),
            float(total_cost_label.text().replace(',', '')),
            float(unit_cost_label.text().replace(',', '')),
            quantity.value()
        ))
        form_layout.addWidget(save_cost_btn, 5, 0, 1, 4)

        input_form.setLayout(form_layout)
        input_layout.addWidget(input_form)
        input_layout.addStretch()

        tabs.addTab(input_widget, '成本录入')

        # 成本查询
        query_widget = QWidget()
        query_layout = QVBoxLayout(query_widget)

        cost_table = QTableWidget()
        cost_table.setColumnCount(8)
        cost_table.setHorizontalHeaderLabels([
            '成本单号', '产品名称', '直接材料', '直接人工',
            '制造费用', '总成本', '单位成本', '数量'
        ])
        cost_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 加载成本数据
        costs = self.db.execute_query('''
                                      SELECT cost_no,
                                             product_name,
                                             material_cost,
                                             labor_cost,
                                             manufacturing_cost,
                                             total_cost,
                                             unit_cost,
                                             quantity
                                      FROM costs
                                      ORDER BY created_date DESC
                                      LIMIT 50
                                      ''')

        cost_table.setRowCount(len(costs))
        for row, cost in enumerate(costs):
            for col, value in enumerate(cost):
                if col in range(2, 8):
                    item = QTableWidgetItem(f'{float(value):,.2f}')
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    item = QTableWidgetItem(str(value) if value else '')
                cost_table.setItem(row, col, item)

        query_layout.addWidget(cost_table)
        tabs.addTab(query_widget, '成本查询')

        layout.addWidget(tabs)

        return widget

    def show_budget_management(self):
        """显示预算管理"""
        widget = self.create_budget_widget()
        self.add_or_switch_tab(widget, '📋 预算管理')

    def create_budget_widget(self):
        """创建预算管理控件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 预算录入
        input_group = QGroupBox('预算录入')
        input_layout = QGridLayout()

        input_layout.addWidget(QLabel('预算年度:'), 0, 0)
        budget_year = QComboBox()
        current_year = datetime.now().year
        budget_year.addItems([str(y) for y in range(current_year - 1, current_year + 3)])
        budget_year.setCurrentText(str(current_year))
        input_layout.addWidget(budget_year, 0, 1)

        input_layout.addWidget(QLabel('预算月份:'), 0, 2)
        budget_month = QComboBox()
        budget_month.addItems(['全年'] + [f'{m}月' for m in range(1, 13)])
        input_layout.addWidget(budget_month, 0, 3)

        input_layout.addWidget(QLabel('部门:'), 1, 0)
        department = QComboBox()
        department.addItems(['销售部', '生产部', '行政部', '财务部', '研发部'])
        department.setEditable(True)
        input_layout.addWidget(department, 1, 1)

        input_layout.addWidget(QLabel('预算类别:'), 1, 2)
        category = QComboBox()
        category.addItems(['收入预算', '成本预算', '费用预算', '投资预算'])
        input_layout.addWidget(category, 1, 3)

        input_layout.addWidget(QLabel('计划金额:'), 2, 0)
        planned = QDoubleSpinBox()
        planned.setRange(0, 100000000)
        planned.setDecimals(2)
        input_layout.addWidget(planned, 2, 1)

        input_layout.addWidget(QLabel('备注:'), 2, 2)
        notes = QLineEdit()
        input_layout.addWidget(notes, 2, 3)

        add_budget_btn = QPushButton('➕ 添加预算')
        add_budget_btn.clicked.connect(lambda: self.add_budget(
            budget_year.currentText(), budget_month.currentText(),
            department.currentText(), category.currentText(),
            planned.value(), notes.text()
        ))
        input_layout.addWidget(add_budget_btn, 3, 0, 1, 4)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # 预算执行
        exec_group = QGroupBox('预算执行情况')
        exec_layout = QVBoxLayout()

        budget_table = QTableWidget()
        budget_table.setColumnCount(7)
        budget_table.setHorizontalHeaderLabels([
            '部门', '类别', '计划金额', '实际金额', '差异', '执行率', '备注'
        ])
        budget_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 加载预算数据
        budgets = self.db.execute_query('''
                                        SELECT department,
                                               category,
                                               planned_amount,
                                               actual_amount,
                                               variance,
                                               notes
                                        FROM budgets
                                        WHERE budget_year = ?
                                          AND budget_month = ?
                                        ORDER BY department, category
                                        ''', (str(current_year), datetime.now().strftime('%m')))

        budget_table.setRowCount(len(budgets))
        for row, budget in enumerate(budgets):
            dept, cat, planned, actual, variance, note = budget

            budget_table.setItem(row, 0, QTableWidgetItem(dept))
            budget_table.setItem(row, 1, QTableWidgetItem(cat))

            planned_item = QTableWidgetItem(f'{float(planned):,.2f}')
            planned_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            budget_table.setItem(row, 2, planned_item)

            actual_item = QTableWidgetItem(f'{float(actual):,.2f}')
            actual_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            budget_table.setItem(row, 3, actual_item)

            var = actual - planned
            variance_item = QTableWidgetItem(f'{var:,.2f}')
            variance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if var > 0:
                variance_item.setForeground(QColor('#e74c3c'))
            else:
                variance_item.setForeground(QColor('#27ae60'))
            budget_table.setItem(row, 4, variance_item)

            exec_rate = (actual / planned * 100) if planned > 0 else 0
            rate_item = QTableWidgetItem(f'{exec_rate:.1f}%')
            rate_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            budget_table.setItem(row, 5, rate_item)

            budget_table.setItem(row, 6, QTableWidgetItem(note or ''))

        exec_layout.addWidget(budget_table)
        exec_group.setLayout(exec_layout)
        layout.addWidget(exec_group)

        return widget

    def show_invoice_management(self):
        """显示发票管理"""
        widget = self.create_invoice_widget()
        self.add_or_switch_tab(widget, '🧾 发票管理')

    def create_invoice_widget(self):
        """创建发票管理控件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 工具栏
        toolbar = QHBoxLayout()

        add_btn = QPushButton('➕ 新增发票')
        add_btn.clicked.connect(self.add_invoice)
        toolbar.addWidget(add_btn)

        verify_btn = QPushButton('✓ 发票验真')
        toolbar.addWidget(verify_btn)

        stat_btn = QPushButton('📊 发票统计')
        toolbar.addWidget(stat_btn)

        toolbar.addStretch()

        invoice_type = QComboBox()
        invoice_type.addItems(['全部', '增值税专用发票', '增值税普通发票', '电子发票'])
        toolbar.addWidget(invoice_type)

        layout.addLayout(toolbar)

        # 发票列表
        table = QTableWidget()
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels([
            '发票号码', '发票类型', '开票日期', '购方名称',
            '销方名称', '金额', '税率', '税额', '价税合计'
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 加载发票数据
        invoices = self.db.execute_query('''
                                         SELECT invoice_no,
                                                invoice_type,
                                                invoice_date,
                                                buyer_name,
                                                seller_name,
                                                amount,
                                                tax_rate,
                                                tax_amount,
                                                total_amount
                                         FROM invoices
                                         ORDER BY invoice_date DESC
                                         LIMIT 100
                                         ''')

        table.setRowCount(len(invoices))
        for row, invoice in enumerate(invoices):
            for col, value in enumerate(invoice):
                if col in [5, 7, 8]:  # 金额列
                    item = QTableWidgetItem(f'{float(value):,.2f}')
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif col == 6:  # 税率
                    item = QTableWidgetItem(f'{float(value)}%')
                else:
                    item = QTableWidgetItem(str(value) if value else '')
                table.setItem(row, col, item)

        layout.addWidget(table)

        return widget

    def show_financial_analysis(self):
        """显示财务分析"""
        widget = self.create_financial_analysis_widget()
        self.add_or_switch_tab(widget, '💹 财务分析')

    def create_financial_analysis_widget(self):
        """创建财务分析控件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 标签页
        tabs = QTabWidget()

        # 比率分析
        ratio_widget = self.create_ratio_analysis_widget()
        tabs.addTab(ratio_widget, '比率分析')

        # 趋势分析
        trend_widget = self.create_trend_analysis_widget()
        tabs.addTab(trend_widget, '趋势分析')

        # 杜邦分析
        dupont_widget = self.create_dupont_analysis_widget()
        tabs.addTab(dupont_widget, '杜邦分析')

        layout.addWidget(tabs)

        return widget

    def create_ratio_analysis_widget(self):
        """创建比率分析控件"""
        widget = QWidget()
        layout = QGridLayout(widget)

        # 输入区
        input_group = QGroupBox('财务数据输入')
        input_layout = QGridLayout()

        input_layout.addWidget(QLabel('营业收入:'), 0, 0)
        revenue = QDoubleSpinBox()
        revenue.setRange(0, 10000000000)
        revenue.setValue(10000000)
        revenue.setDecimals(2)
        input_layout.addWidget(revenue, 0, 1)

        input_layout.addWidget(QLabel('营业成本:'), 0, 2)
        cost = QDoubleSpinBox()
        cost.setRange(0, 10000000000)
        cost.setValue(6000000)
        cost.setDecimals(2)
        input_layout.addWidget(cost, 0, 3)

        input_layout.addWidget(QLabel('总资产:'), 1, 0)
        assets = QDoubleSpinBox()
        assets.setRange(0, 10000000000)
        assets.setValue(50000000)
        assets.setDecimals(2)
        input_layout.addWidget(assets, 1, 1)

        input_layout.addWidget(QLabel('总负债:'), 1, 2)
        liabilities = QDoubleSpinBox()
        liabilities.setRange(0, 10000000000)
        liabilities.setValue(30000000)
        liabilities.setDecimals(2)
        input_layout.addWidget(liabilities, 1, 3)

        input_layout.addWidget(QLabel('所有者权益:'), 2, 0)
        equity = QDoubleSpinBox()
        equity.setRange(0, 10000000000)
        equity.setValue(20000000)
        equity.setDecimals(2)
        input_layout.addWidget(equity, 2, 1)

        input_layout.addWidget(QLabel('净利润:'), 2, 2)
        net_income = QDoubleSpinBox()
        net_income.setRange(-10000000000, 10000000000)
        net_income.setValue(2000000)
        net_income.setDecimals(2)
        input_layout.addWidget(net_income, 2, 3)

        analyze_btn = QPushButton('📊 分析')
        analyze_btn.clicked.connect(lambda: self.analyze_ratios(
            revenue.value(), cost.value(), assets.value(),
            liabilities.value(), equity.value(), net_income.value(),
            result_text
        ))
        input_layout.addWidget(analyze_btn, 3, 0, 1, 4)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group, 0, 0, 1, 2)

        # 结果显示
        result_group = QGroupBox('分析结果')
        result_layout = QVBoxLayout()

        result_text = QTextEdit()
        result_text.setReadOnly(True)
        result_layout.addWidget(result_text)

        result_group.setLayout(result_layout)
        layout.addWidget(result_group, 1, 0, 1, 2)

        return widget

    def create_trend_analysis_widget(self):
        """创建趋势分析控件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 图表
        chart_widget = ChartWidget()
        layout.addWidget(chart_widget)

        # 生成示例趋势数据
        months = [f'{i}月' for i in range(1, 13)]
        revenue = [800 + i * 50 + np.random.randint(-50, 50) for i in range(12)]
        profit = [100 + i * 10 + np.random.randint(-10, 10) for i in range(12)]

        chart_widget.plot_trend(months, revenue, profit)

        return widget

    def create_dupont_analysis_widget(self):
        """创建杜邦分析控件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 输入
        input_group = QGroupBox('输入数据')
        input_layout = QGridLayout()

        input_layout.addWidget(QLabel('净利润:'), 0, 0)
        net_profit = QDoubleSpinBox()
        net_profit.setRange(0, 10000000000)
        net_profit.setValue(2000000)
        net_profit.setDecimals(2)
        input_layout.addWidget(net_profit, 0, 1)

        input_layout.addWidget(QLabel('营业收入:'), 0, 2)
        sales = QDoubleSpinBox()
        sales.setRange(0, 10000000000)
        sales.setValue(10000000)
        sales.setDecimals(2)
        input_layout.addWidget(sales, 0, 3)

        input_layout.addWidget(QLabel('总资产:'), 1, 0)
        assets = QDoubleSpinBox()
        assets.setRange(0, 10000000000)
        assets.setValue(50000000)
        assets.setDecimals(2)
        input_layout.addWidget(assets, 1, 1)

        input_layout.addWidget(QLabel('所有者权益:'), 1, 2)
        equity = QDoubleSpinBox()
        equity.setRange(0, 10000000000)
        equity.setValue(20000000)
        equity.setDecimals(2)
        input_layout.addWidget(equity, 1, 3)

        analyze_dupont_btn = QPushButton('🔍 杜邦分析')
        analyze_dupont_btn.clicked.connect(lambda: self.perform_dupont_analysis(
            net_profit.value(), sales.value(), assets.value(), equity.value(), result_text
        ))
        input_layout.addWidget(analyze_dupont_btn, 2, 0, 1, 4)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # 结果
        result_group = QGroupBox('杜邦分析结果')
        result_layout = QVBoxLayout()

        result_text = QTextEdit()
        result_text.setReadOnly(True)
        result_layout.addWidget(result_text)

        result_group.setLayout(result_layout)
        layout.addWidget(result_group)

        return widget

    def show_system_settings(self):
        """显示系统设置"""
        widget = self.create_system_settings_widget()
        self.add_or_switch_tab(widget, '🔧 系统设置')

    def create_system_settings_widget(self):
        """创建系统设置控件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        tabs = QTabWidget()

        # 基本设置
        basic_widget = QWidget()
        basic_layout = QVBoxLayout(basic_widget)

        basic_group = QGroupBox('公司信息')
        basic_form = QGridLayout()

        basic_form.addWidget(QLabel('公司名称:'), 0, 0)
        company_name = QLineEdit()
        company_name.setText('示例企业有限公司')
        basic_form.addWidget(company_name, 0, 1)

        basic_form.addWidget(QLabel('纳税人识别号:'), 1, 0)
        tax_no = QLineEdit()
        tax_no.setText('91000000000000000X')
        basic_form.addWidget(tax_no, 1, 1)

        basic_form.addWidget(QLabel('会计年度开始:'), 2, 0)
        fiscal_year = QComboBox()
        fiscal_year.addItems([f'{m}月1日' for m in range(1, 13)])
        basic_form.addWidget(fiscal_year, 2, 1)

        basic_form.addWidget(QLabel('默认币种:'), 3, 0)
        currency = QComboBox()
        currency.addItems(['人民币(CNY)', '美元(USD)', '欧元(EUR)'])
        basic_form.addWidget(currency, 3, 1)

        save_basic_btn = QPushButton('💾 保存设置')
        basic_form.addWidget(save_basic_btn, 4, 0, 1, 2)

        basic_group.setLayout(basic_form)
        basic_layout.addWidget(basic_group)
        basic_layout.addStretch()

        tabs.addTab(basic_widget, '基本设置')

        # 科目设置
        account_widget = QWidget()
        account_layout = QVBoxLayout(account_widget)

        account_toolbar = QHBoxLayout()
        add_account_btn = QPushButton('➕ 新增科目')
        add_account_btn.clicked.connect(self.add_account)
        account_toolbar.addWidget(add_account_btn)

        edit_account_btn = QPushButton('✏️ 修改科目')
        account_toolbar.addWidget(edit_account_btn)

        delete_account_btn = QPushButton('🗑️ 删除科目')
        account_toolbar.addWidget(delete_account_btn)

        account_toolbar.addStretch()
        account_layout.addLayout(account_toolbar)

        account_tree = QTreeWidget()
        account_tree.setHeaderLabels(['科目代码', '科目名称', '类别', '余额方向'])

        # 加载科目树
        self.load_account_tree(account_tree)

        account_layout.addWidget(account_tree)
        tabs.addTab(account_widget, '科目设置')

        # 用户管理
        user_widget = QWidget()
        user_layout = QVBoxLayout(user_widget)

        user_table = QTableWidget()
        user_table.setColumnCount(5)
        user_table.setHorizontalHeaderLabels(['用户名', '姓名', '角色', '状态', '最后登录'])
        user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        user_layout.addWidget(user_table)

        tabs.addTab(user_widget, '用户管理')

        layout.addWidget(tabs)

        return widget

    def load_account_tree(self, tree):
        """加载科目树"""
        tree.clear()

        # 按类别分组
        categories = {}
        accounts = self.db.execute_query('''
                                         SELECT code, name, category, balance_direction
                                         FROM accounts
                                         ORDER BY code
                                         ''')

        for code, name, category, direction in accounts:
            if category not in categories:
                categories[category] = []
            categories[category].append((code, name, direction))

            # 创建树
        for category, items in categories.items():
            parent = QTreeWidgetItem(tree)
            parent.setText(0, '')
            parent.setText(1, category)
            parent.setText(2, category)
            parent.setText(3, '')

            for code, name, direction in items:
                child = QTreeWidgetItem(parent)
                child.setText(0, code)
                child.setText(1, name)
                child.setText(2, category)
                child.setText(3, direction)

        tree.expandAll()

        # ==================== 辅助方法 ====================

    def add_or_switch_tab(self, widget, title):
        """添加或切换到已存在的标签页"""
        for i in range(self.content_stack.count()):
            if self.content_stack.tabText(i) == title:
                self.content_stack.setCurrentIndex(i)
                return

        self.content_stack.addTab(widget, title)
        self.content_stack.setCurrentWidget(widget)

    def create_info_card(self, icon, title, value, color):
        """创建信息卡片"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet(f'''  
            QFrame {{  
                background-color: {color};  
                border-radius: 10px;  
                padding: 15px;  
            }}  
        ''')
        card.setMinimumSize(150, 100)

        layout = QVBoxLayout(card)

        icon_label = QLabel(icon)
        icon_font = QFont()
        icon_font.setPointSize(24)
        icon_label.setFont(icon_font)
        icon_label.setStyleSheet('color: white;')
        layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet('color: white; font-size: 12px;')
        layout.addWidget(title_label)

        value_label = QLabel(f'¥{value}')
        value_font = QFont()
        value_font.setPointSize(16)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet('color: white;')
        layout.addWidget(value_label)

        return card

    def analyze_ratios(self, revenue, cost, assets, liabilities, equity, net_income, result_widget):
        """分析财务比率"""
        ratios = self.calc.financial_ratios(revenue, cost, assets, liabilities, equity, net_income)

        result = "=" * 60 + "\n"
        result += "财务比率分析报告\n"
        result += "=" * 60 + "\n\n"

        result += "【盈利能力指标】\n"
        result += "-" * 60 + "\n"
        for key in ['毛利率', '净利率', '资产收益率(ROA)', '净资产收益率(ROE)']:
            if key in ratios:
                result += f"{key:20s}: {ratios[key]:>10.2f}%"
                if key == '净资产收益率(ROE)':
                    if ratios[key] > 15:
                        result += "  ✓ 优秀"
                    elif ratios[key] > 10:
                        result += "  ○ 良好"
                    else:
                        result += "  △ 一般"
                result += "\n"

        result += "\n【偿债能力指标】\n"
        result += "-" * 60 + "\n"
        for key in ['资产负债率', '流动比率', '速动比率']:
            if key in ratios:
                result += f"{key:20s}: {ratios[key]:>10.2f}%"
                if key == '资产负债率':
                    if ratios[key] < 50:
                        result += "  ✓ 低风险"
                    elif ratios[key] < 70:
                        result += "  ○ 中等风险"
                    else:
                        result += "  △ 高风险"
                result += "\n"

        result += "\n【运营能力指标】\n"
        result += "-" * 60 + "\n"
        for key in ['总资产周转率']:
            if key in ratios:
                result += f"{key:20s}: {ratios[key]:>10.2f}次/年\n"

        result += "\n" + "=" * 60 + "\n"

        result_widget.setText(result)

    def financial_ratios(self, revenue, cost, assets, liabilities, equity, net_income):
        """计算财务比率"""
        ratios = {}

        # 盈利能力
        ratios['毛利率'] = ((revenue - cost) / revenue * 100) if revenue > 0 else 0
        ratios['净利率'] = (net_income / revenue * 100) if revenue > 0 else 0
        ratios['资产收益率(ROA)'] = (net_income / assets * 100) if assets > 0 else 0
        ratios['净资产收益率(ROE)'] = (net_income / equity * 100) if equity > 0 else 0

        # 偿债能力
        ratios['资产负债率'] = (liabilities / assets * 100) if assets > 0 else 0
        ratios['流动比率'] = 200  # 示例值
        ratios['速动比率'] = 150  # 示例值

        # 运营能力
        ratios['总资产周转率'] = (revenue / assets) if assets > 0 else 0

        return ratios

    def perform_dupont_analysis(self, net_profit, sales, assets, equity, result_widget):
        """执行杜邦分析"""
        result = self.calc.du_pont_analysis(net_profit, sales, assets, equity)

        if result:
            text = "=" * 60 + "\n"
            text += "杜邦分析报告\n"
            text += "=" * 60 + "\n\n"

            text += "【核心指标】\n"
            text += "-" * 60 + "\n"
            text += f"净资产收益率(ROE):     {result['ROE']:>10.2f}%\n\n"

            text += "【三大驱动因素】\n"
            text += "-" * 60 + "\n"
            text += f"销售净利率:             {result['销售净利率']:>10.2f}%\n"
            text += f"总资产周转率:           {result['资产周转率']:>10.2f}次/年\n"
            text += f"权益乘数:               {result['权益乘数']:>10.2f}倍\n\n"

            text += "【分析结论】\n"
            text += "-" * 60 + "\n"

            if result['ROE'] > 15:
                text += "✓ ROE表现优秀，企业盈利能力强\n"
            elif result['ROE'] > 10:
                text += "○ ROE表现良好，企业盈利能力较好\n"
            else:
                text += "△ ROE偏低，需要提升盈利能力\n"

            text += "\n改进建议：\n"
            if result['销售净利率'] < 10:
                text += "• 提高销售净利率：控制成本费用，提高产品附加值\n"
            if result['资产周转率'] < 1:
                text += "• 提高资产周转率：加快资金周转，提高资产使用效率\n"
            if result['权益乘数'] < 2:
                text += "• 优化资本结构：适当增加财务杠杆，提高资金使用效率\n"

            text += "\n" + "=" * 60 + "\n"

            result_widget.setText(text)
        else:
            result_widget.setText("数据不完整，无法进行杜邦分析")

    def add_fixed_asset(self):
        """添加固定资产"""
        dialog = QDialog(self)
        dialog.setWindowTitle('新增固定资产')
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout(dialog)

        form = QGroupBox('资产信息')
        form_layout = QGridLayout()

        form_layout.addWidget(QLabel('资产编号:'), 0, 0)
        asset_code = QLineEdit()
        asset_code.setText(f'FA{datetime.now().strftime("%Y%m%d")}001')
        form_layout.addWidget(asset_code, 0, 1)

        form_layout.addWidget(QLabel('资产名称:'), 1, 0)
        asset_name = QLineEdit()
        form_layout.addWidget(asset_name, 1, 1)

        form_layout.addWidget(QLabel('资产类别:'), 2, 0)
        category = QComboBox()
        category.addItems(['房屋建筑物', '机器设备', '运输工具', '电子设备', '其他'])
        form_layout.addWidget(category, 2, 1)

        form_layout.addWidget(QLabel('原值:'), 3, 0)
        original_value = QDoubleSpinBox()
        original_value.setRange(0, 100000000)
        original_value.setDecimals(2)
        form_layout.addWidget(original_value, 3, 1)

        form_layout.addWidget(QLabel('购置日期:'), 4, 0)
        purchase_date = QDateEdit()
        purchase_date.setDate(QDate.currentDate())
        purchase_date.setCalendarPopup(True)
        form_layout.addWidget(purchase_date, 4, 1)

        form_layout.addWidget(QLabel('使用年限:'), 5, 0)
        useful_life = QSpinBox()
        useful_life.setRange(1, 50)
        useful_life.setValue(10)
        form_layout.addWidget(useful_life, 5, 1)

        form_layout.addWidget(QLabel('折旧方法:'), 6, 0)
        depreciation_method = QComboBox()
        depreciation_method.addItems(['直线法', '双倍余额递减法', '年数总和法'])
        form_layout.addWidget(depreciation_method, 6, 1)

        form_layout.addWidget(QLabel('使用部门:'), 7, 0)
        department = QComboBox()
        department.addItems(['销售部', '生产部', '行政部', '财务部', '研发部'])
        department.setEditable(True)
        form_layout.addWidget(department, 7, 1)

        form.setLayout(form_layout)
        layout.addWidget(form)

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_fixed_asset(
            asset_code.text(), asset_name.text(), category.currentText(),
            original_value.value(), purchase_date.date().toString('yyyy-MM-dd'),
            useful_life.value(), depreciation_method.currentText(),
            department.currentText(), dialog
        ))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec_()

    def save_fixed_asset(self, code, name, category, original_value, purchase_date,
                         useful_life, method, department, dialog):
        """保存固定资产"""
        try:
            method_map = {
                '直线法': 'straight_line',
                '双倍余额递减法': 'double_declining',
                '年数总和法': 'sum_of_years'
            }

            self.db.execute_update('''
                                   INSERT INTO fixed_assets
                                   (asset_code, asset_name, category, original_value, accumulated_depreciation,
                                    net_value, purchase_date, useful_life, depreciation_method, department,
                                    status, created_date)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                   ''', (code, name, category, original_value, 0, original_value,
                                         purchase_date, useful_life, method_map.get(method, 'straight_line'),
                                         department, 'in_use', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

            self.db.add_log('操作', '固定资产', '新增资产', self.current_user, f'资产编号: {code}')

            QMessageBox.information(self, '成功', '固定资产添加成功！')
            dialog.accept()

        except Exception as e:
            QMessageBox.critical(self, '错误', f'保存失败: {str(e)}')

    def calculate_depreciation_dialog(self):
        """计提折旧对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle('计提折旧')
        dialog.setMinimumWidth(600)

        layout = QVBoxLayout(dialog)

        # 计提月份
        month_layout = QHBoxLayout()
        month_layout.addWidget(QLabel('计提月份:'))
        month_edit = QLineEdit()
        month_edit.setText(datetime.now().strftime('%Y-%m'))
        month_layout.addWidget(month_edit)
        month_layout.addStretch()
        layout.addLayout(month_layout)

        # 计算按钮
        calc_btn = QPushButton('🧮 计算折旧')
        calc_btn.clicked.connect(lambda: self.calculate_all_depreciation(month_edit.text(), result_table))
        layout.addWidget(calc_btn)

        # 结果表格
        result_table = QTableWidget()
        result_table.setColumnCount(6)
        result_table.setHorizontalHeaderLabels([
            '资产名称', '原值', '本月折旧', '累计折旧', '净值', '备注'
        ])
        result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(result_table)

        # 关闭按钮
        close_btn = QPushButton('关闭')
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec_()

    def calculate_all_depreciation(self, month, table):
        """计算所有资产折旧"""
        assets = self.db.execute_query('''
                                       SELECT asset_name,
                                              original_value,
                                              accumulated_depreciation,
                                              useful_life,
                                              depreciation_method,
                                              purchase_date
                                       FROM fixed_assets
                                       WHERE status = 'in_use'
                                       ''')

        table.setRowCount(len(assets))

        for row, asset in enumerate(assets):
            name, original, accumulated, life, method, purchase_date = asset

            # 计算使用月数
            purchase = datetime.strptime(purchase_date, '%Y-%m-%d')
            months_used = (datetime.now().year - purchase.year) * 12 + (datetime.now().month - purchase.month)

            # 计算折旧
            dep_result = self.calc.calculate_depreciation(
                original, 0.05, life, method, months_used
            )

            table.setItem(row, 0, QTableWidgetItem(name))
            table.setItem(row, 1, QTableWidgetItem(f'{original:,.2f}'))
            table.setItem(row, 2, QTableWidgetItem(f'{dep_result["monthly_depreciation"]:,.2f}'))
            table.setItem(row, 3, QTableWidgetItem(f'{dep_result["accumulated_depreciation"]:,.2f}'))
            table.setItem(row, 4, QTableWidgetItem(f'{dep_result["net_value"]:,.2f}'))
            table.setItem(row, 5, QTableWidgetItem(''))

    def add_receivable(self):
        """添加应收账款"""
        dialog = QDialog(self)
        dialog.setWindowTitle('新增应收账款')
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout(dialog)

        form = QGroupBox('应收信息')
        form_layout = QGridLayout()

        form_layout.addWidget(QLabel('单据号:'), 0, 0)
        bill_no = QLineEdit()
        bill_no.setText(f'AR{datetime.now().strftime("%Y%m%d")}001')
        form_layout.addWidget(bill_no, 0, 1)

        form_layout.addWidget(QLabel('客户:'), 1, 0)
        customer = QComboBox()
        customers = self.db.execute_query('SELECT name FROM customers')
        customer.addItems([c[0] for c in customers])
        customer.setEditable(True)
        form_layout.addWidget(customer, 1, 1)

        form_layout.addWidget(QLabel('应收金额:'), 2, 0)
        amount = QDoubleSpinBox()
        amount.setRange(0, 100000000)
        amount.setDecimals(2)
        form_layout.addWidget(amount, 2, 1)

        form_layout.addWidget(QLabel('账单日期:'), 3, 0)
        bill_date = QDateEdit()
        bill_date.setDate(QDate.currentDate())
        bill_date.setCalendarPopup(True)
        form_layout.addWidget(bill_date, 3, 1)

        form_layout.addWidget(QLabel('到期日期:'), 4, 0)
        due_date = QDateEdit()
        due_date.setDate(QDate.currentDate().addDays(30))
        due_date.setCalendarPopup(True)
        form_layout.addWidget(due_date, 4, 1)

        form_layout.addWidget(QLabel('备注:'), 5, 0)
        notes = QLineEdit()
        form_layout.addWidget(notes, 5, 1)

        form.setLayout(form_layout)
        layout.addWidget(form)

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_receivable(
            bill_no.text(), customer.currentText(), amount.value(),
            bill_date.date().toString('yyyy-MM-dd'),
            due_date.date().toString('yyyy-MM-dd'),
            notes.text(), dialog
        ))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec_()

    def save_receivable(self, bill_no, customer, amount, bill_date, due_date, notes, dialog):
        """保存应收账款"""
        try:
            self.db.execute_update('''
                                   INSERT INTO receivables
                                   (bill_no, customer_name, amount, received_amount, balance,
                                    bill_date, due_date, status, notes, created_date)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                   ''', (bill_no, customer, amount, 0, amount, bill_date, due_date,
                                         'pending', notes, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

            QMessageBox.information(self, '成功', '应收账款添加成功！')
            dialog.accept()

        except Exception as e:
            QMessageBox.critical(self, '错误', f'保存失败: {str(e)}')

    def add_payable(self):
        """添加应付账款"""
        dialog = QDialog(self)
        dialog.setWindowTitle('新增应付账款')
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout(dialog)

        form = QGroupBox('应付信息')
        form_layout = QGridLayout()

        form_layout.addWidget(QLabel('单据号:'), 0, 0)
        bill_no = QLineEdit()
        bill_no.setText(f'AP{datetime.now().strftime("%Y%m%d")}001')
        form_layout.addWidget(bill_no, 0, 1)

        form_layout.addWidget(QLabel('供应商:'), 1, 0)
        supplier = QComboBox()
        suppliers = self.db.execute_query('SELECT name FROM suppliers')
        supplier.addItems([s[0] for s in suppliers])
        supplier.setEditable(True)
        form_layout.addWidget(supplier, 1, 1)

        form_layout.addWidget(QLabel('应付金额:'), 2, 0)
        amount = QDoubleSpinBox()
        amount.setRange(0, 100000000)
        amount.setDecimals(2)
        form_layout.addWidget(amount, 2, 1)

        form_layout.addWidget(QLabel('账单日期:'), 3, 0)
        bill_date = QDateEdit()
        bill_date.setDate(QDate.currentDate())
        bill_date.setCalendarPopup(True)
        form_layout.addWidget(bill_date, 3, 1)

        form_layout.addWidget(QLabel('到期日期:'), 4, 0)
        due_date = QDateEdit()
        due_date.setDate(QDate.currentDate().addDays(30))
        due_date.setCalendarPopup(True)
        form_layout.addWidget(due_date, 4, 1)

        form_layout.addWidget(QLabel('备注:'), 5, 0)
        notes = QLineEdit()
        form_layout.addWidget(notes, 5, 1)

        form.setLayout(form_layout)
        layout.addWidget(form)

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_payable(
            bill_no.text(), supplier.currentText(), amount.value(),
            bill_date.date().toString('yyyy-MM-dd'),
            due_date.date().toString('yyyy-MM-dd'),
            notes.text(), dialog
        ))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec_()

    def save_payable(self, bill_no, supplier, amount, bill_date, due_date, notes, dialog):
        """保存应付账款"""
        try:
            self.db.execute_update('''
                                   INSERT INTO payables
                                   (bill_no, supplier_name, amount, paid_amount, balance,
                                    bill_date, due_date, status, notes, created_date)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                   ''', (bill_no, supplier, amount, 0, amount, bill_date, due_date,
                                         'pending', notes, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

            QMessageBox.information(self, '成功', '应付账款添加成功！')
            dialog.accept()

        except Exception as e:
            QMessageBox.critical(self, '错误', f'保存失败: {str(e)}')

    def show_aging_analysis(self):
        """显示账龄分析"""
        dialog = QDialog(self)
        dialog.setWindowTitle('应收账款账龄分析')
        dialog.setMinimumSize(800, 600)

        layout = QVBoxLayout(dialog)

        # 获取应收数据
        receivables_data = self.db.execute_query('''
                                                 SELECT bill_date, balance
                                                 FROM receivables
                                                 WHERE status != 'paid'
                                                 ''')

        receivables = [{'date': r[0], 'amount': r[1]} for r in receivables_data]

        # 账龄分析
        aging = self.calc.aging_analysis(receivables)

        # 表格显示
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(['账龄', '金额', '占比'])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        total = sum(aging.values())

        table.setRowCount(len(aging))
        for row, (age_group, amount) in enumerate(aging.items()):
            table.setItem(row, 0, QTableWidgetItem(age_group))

            amount_item = QTableWidgetItem(f'{amount:,.2f}')
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(row, 1, amount_item)

            ratio = (amount / total * 100) if total > 0 else 0
            ratio_item = QTableWidgetItem(f'{ratio:.2f}%')
            ratio_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(row, 2, ratio_item)

        layout.addWidget(table)

        # 图表
        chart_widget = ChartWidget()
        chart_widget.plot_pie(list(aging.keys()), list(aging.values()), '应收账款账龄分布')
        layout.addWidget(chart_widget)

        # 关闭按钮
        close_btn = QPushButton('关闭')
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec_()

    def calculate_salaries(self, month):
        """批量计算工资"""
        try:
            # 获取员工信息
            employees = self.db.execute_query('''
                                              SELECT emp_code, name, base_salary
                                              FROM employees
                                              WHERE status = 'active'
                                              ''')

            for emp_code, name, base_salary in employees:
                # 简单计算示例
                allowance = base_salary * 0.1  # 10%津贴
                overtime_pay = 500  # 固定加班费
                bonus = 0

                # 社保公积金（简化计算）
                social_security = base_salary * 0.105  # 10.5%
                housing_fund = base_salary * 0.12  # 12%

                # 应发工资
                gross_salary = base_salary + allowance + overtime_pay + bonus

                # 扣除项
                deductions = social_security + housing_fund

                # 个税（简化计算，5000起征点）
                taxable = gross_salary - deductions - 5000
                if taxable <= 0:
                    income_tax = 0
                elif taxable <= 3000:
                    income_tax = taxable * 0.03
                elif taxable <= 12000:
                    income_tax = taxable * 0.1 - 210
                else:
                    income_tax = taxable * 0.2 - 1410

                # 实发工资
                net_salary = gross_salary - deductions - income_tax

                # 保存或更新工资记录
                self.db.execute_update('''
                        INSERT OR REPLACE INTO salaries 
                        (emp_code, emp_name, salary_month, base_salary, allowance,
                         overtime_pay, bonus, social_security, housing_fund, income_tax,
                         other_deduction, net_salary, status, created_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (emp_code, name, month, base_salary, allowance, overtime_pay,
                          bonus, social_security, housing_fund, income_tax, 0, net_salary,
                          'unpaid', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

            QMessageBox.information(self, '成功', f'{month}工资计算完成！')

        except Exception as e:
            QMessageBox.critical(self, '错误', f'计算失败: {str(e)}')

    def save_cost(self, cost_no, product_name, period, material, labor,
                  manufacturing, total, unit, quantity):
        """保存成本"""
        try:
            self.db.execute_update('''
                                   INSERT INTO costs
                                   (cost_no, product_name, cost_period, material_cost, labor_cost,
                                    manufacturing_cost, total_cost, unit_cost, quantity, created_date)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                   ''', (cost_no, product_name, period, material, labor, manufacturing,
                                         total, unit, quantity, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

            QMessageBox.information(self, '成功', '成本保存成功！')

        except Exception as e:
            QMessageBox.critical(self, '错误', f'保存失败: {str(e)}')

    def add_budget(self, year, month, department, category, planned, notes):
        """添加预算"""
        try:
            self.db.execute_update('''
                                   INSERT INTO budgets
                                   (budget_year, budget_month, department, category, planned_amount,
                                    actual_amount, variance, notes, created_date)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                   ''', (year, month, department, category, planned, 0, -planned, notes,
                                         datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

            QMessageBox.information(self, '成功', '预算添加成功！')

        except Exception as e:
            QMessageBox.critical(self, '错误', f'保存失败: {str(e)}')

    def add_invoice(self):
        """添加发票"""
        dialog = QDialog(self)
        dialog.setWindowTitle('新增发票')
        dialog.setMinimumWidth(600)

        layout = QVBoxLayout(dialog)

        form = QGroupBox('发票信息')
        form_layout = QGridLayout()

        form_layout.addWidget(QLabel('发票号码:'), 0, 0)
        invoice_no = QLineEdit()
        form_layout.addWidget(invoice_no, 0, 1)

        form_layout.addWidget(QLabel('发票类型:'), 0, 2)
        invoice_type = QComboBox()
        invoice_type.addItems(['增值税专用发票', '增值税普通发票', '电子发票'])
        form_layout.addWidget(invoice_type, 0, 3)

        form_layout.addWidget(QLabel('开票日期:'), 1, 0)
        invoice_date = QDateEdit()
        invoice_date.setDate(QDate.currentDate())
        invoice_date.setCalendarPopup(True)
        form_layout.addWidget(invoice_date, 1, 1)

        form_layout.addWidget(QLabel('购方名称:'), 2, 0)
        buyer_name = QLineEdit()
        form_layout.addWidget(buyer_name, 2, 1, 1, 3)

        form_layout.addWidget(QLabel('销方名称:'), 3, 0)
        seller_name = QLineEdit()
        form_layout.addWidget(seller_name, 3, 1, 1, 3)

        form_layout.addWidget(QLabel('金额:'), 4, 0)
        amount = QDoubleSpinBox()
        amount.setRange(0, 100000000)
        amount.setDecimals(2)
        amount.valueChanged.connect(lambda: self.calculate_invoice_tax(
            amount, tax_rate, tax_amount, total_amount
        ))
        form_layout.addWidget(amount, 4, 1)

        form_layout.addWidget(QLabel('税率(%):'), 4, 2)
        tax_rate = QDoubleSpinBox()
        tax_rate.setRange(0, 100)
        tax_rate.setValue(13)
        tax_rate.setDecimals(2)
        tax_rate.valueChanged.connect(lambda: self.calculate_invoice_tax(
            amount, tax_rate, tax_amount, total_amount
        ))
        form_layout.addWidget(tax_rate, 4, 3)

        form_layout.addWidget(QLabel('税额:'), 5, 0)
        tax_amount = QLineEdit()
        tax_amount.setReadOnly(True)
        tax_amount.setText('0.00')
        form_layout.addWidget(tax_amount, 5, 1)

        form_layout.addWidget(QLabel('价税合计:'), 5, 2)
        total_amount = QLineEdit()
        total_amount.setReadOnly(True)
        total_amount.setText('0.00')
        form_layout.addWidget(total_amount, 5, 3)

        form.setLayout(form_layout)
        layout.addWidget(form)

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_invoice(
            invoice_no.text(), invoice_type.currentText(),
            invoice_date.date().toString('yyyy-MM-dd'),
            buyer_name.text(), seller_name.text(),
            amount.value(), tax_rate.value(),
            float(tax_amount.text()), float(total_amount.text()), dialog
        ))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec_()

    def calculate_invoice_tax(self, amount_widget, rate_widget, tax_widget, total_widget):
        """计算发票税额"""
        amount = amount_widget.value()
        rate = rate_widget.value() / 100

        tax = amount * rate
        total = amount + tax

        tax_widget.setText(f'{tax:.2f}')
        total_widget.setText(f'{total:.2f}')

    def save_invoice(self, invoice_no, invoice_type, invoice_date, buyer, seller,
                     amount, tax_rate, tax_amount, total_amount, dialog):
        """保存发票"""
        try:
            self.db.execute_update('''
                                   INSERT INTO invoices
                                   (invoice_no, invoice_type, invoice_date, buyer_name, seller_name,
                                    amount, tax_rate, tax_amount, total_amount, status, created_date)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                   ''', (invoice_no, invoice_type, invoice_date, buyer, seller,
                                         amount, tax_rate, tax_amount, total_amount, 'valid',
                                         datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

            QMessageBox.information(self, '成功', '发票添加成功！')
            dialog.accept()

        except Exception as e:
            QMessageBox.critical(self, '错误', f'保存失败: {str(e)}')

    def add_account(self):
        """添加会计科目"""
        dialog = QDialog(self)
        dialog.setWindowTitle('新增会计科目')
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        form = QGroupBox('科目信息')
        form_layout = QGridLayout()

        form_layout.addWidget(QLabel('科目代码:'), 0, 0)
        code = QLineEdit()
        form_layout.addWidget(code, 0, 1)

        form_layout.addWidget(QLabel('科目名称:'), 1, 0)
        name = QLineEdit()
        form_layout.addWidget(name, 1, 1)

        form_layout.addWidget(QLabel('科目类别:'), 2, 0)
        category = QComboBox()
        category.addItems(['资产', '负债', '权益', '损益'])
        form_layout.addWidget(category, 2, 1)

        form_layout.addWidget(QLabel('余额方向:'), 3, 0)
        direction = QComboBox()
        direction.addItems(['借', '贷'])
        form_layout.addWidget(direction, 3, 1)

        form.setLayout(form_layout)
        layout.addWidget(form)

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_account(
            code.text(), name.text(), category.currentText(), direction.currentText(), dialog
        ))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec_()

    def save_account(self, code, name, category, direction, dialog):
        """保存会计科目"""
        try:
            self.db.execute_update('''
                                   INSERT INTO accounts
                                   (code, name, category, parent_code, level, balance_direction, is_leaf,
                                    created_date)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                   ''', (code, name, category, None, 1, direction, 1,
                                         datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

            QMessageBox.information(self, '成功', '科目添加成功！')
            dialog.accept()

        except Exception as e:
            QMessageBox.critical(self, '错误', f'保存失败: {str(e)}')

    def backup_data(self):
        """备份数据"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, '备份数据库', f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db',
            'Database Files (*.db)'
        )

        if file_path:
            if self.db.backup_database(file_path):
                QMessageBox.information(self, '成功', '数据备份成功！')
            else:
                QMessageBox.critical(self, '错误', '数据备份失败！')

    def restore_data(self):
        """恢复数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择备份文件', '', 'Database Files (*.db)'
        )

        if file_path:
            reply = QMessageBox.question(
                self, '确认', '恢复数据将覆盖当前数据，是否继续？',
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                if self.db.restore_database(file_path):
                    QMessageBox.information(self, '成功', '数据恢复成功！请重启软件。')
                else:
                    QMessageBox.critical(self, '错误', '数据恢复失败！')

    def import_data(self):
        """导入数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '导入数据', '', 'Excel Files (*.xlsx *.xls);;CSV Files (*.csv)'
        )

        if file_path:
            QMessageBox.information(self, '提示', '数据导入功能开发中...')

    def export_data(self):
        """导出数据"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, '导出数据', f'export_{datetime.now().strftime("%Y%m%d")}.xlsx',
            'Excel Files (*.xlsx)'
        )

        if file_path:
            QMessageBox.information(self, '提示', '数据导出功能开发中...')

    def export_ledger(self, table):
        """导出账簿"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, '导出账簿', f'ledger_{datetime.now().strftime("%Y%m%d")}.xlsx',
            'Excel Files (*.xlsx)'
        )

        if file_path:
            QMessageBox.information(self, '提示', '账簿导出功能开发中...')

    def export_report(self, table):
        """导出报表"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, '导出报表', f'report_{datetime.now().strftime("%Y%m%d")}.xlsx',
            'Excel Files (*.xlsx)'
        )

        if file_path:
            QMessageBox.information(self, '提示', '报表导出功能开发中...')

    def show_about(self):
        """显示关于对话框"""
        about_text = """
            <h2>FinancialCalculatorPro Enterprise Edition</h2>
            <p><b>版本:</b> 2.0.0</p>
            <p><b>企业级财务管理系统</b></p>
            <hr>
            <p><b>主要功能:</b></p>
            <ul>
                <li>📝 凭证管理 - 会计凭证录入、审核</li>
                <li>📚 账簿查询 - 总账、明细账、日记账</li>
                <li>📊 财务报表 - 资产负债表、利润表、现金流量表</li>
                <li>💰 资金管理 - 银行账户、资金流水</li>
                <li>🏢 固定资产 - 资产管理、折旧计算</li>
                <li>👥 往来管理 - 应收应付、账龄分析</li>
                <li>💵 工资管理 - 工资计算、个税计算</li>
                <li>📦 成本核算 - 成本计算、成本分析</li>
                <li>📋 预算管理 - 预算编制、预算执行</li>
                <li>🧾 发票管理 - 发票录入、发票查询</li>
                <li>💹 财务分析 - 比率分析、趋势分析、杜邦分析</li>
                <li>🔧 系统设置 - 科目设置、用户管理</li>
            </ul>
            <hr>
            <p><b>技术支持:</b> AI Assistant</p>
            <p><b>版权所有</b> © 2024</p>
            """

        QMessageBox.about(self, '关于', about_text)


# ==================== 图表控件 ====================
class ChartWidget(QWidget):
    """图表控件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

    def plot_trend(self, labels, data1, data2):
        """绘制趋势图"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        x = np.arange(len(labels))
        width = 0.35

        ax.bar(x - width / 2, data1, width, label='营业收入', color='#3498db')
        ax.bar(x + width / 2, data2, width, label='净利润', color='#27ae60')

        ax.set_xlabel('月份')
        ax.set_ylabel('金额(万元)')
        ax.set_title('财务趋势分析')
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        ax.grid(True, alpha=0.3)

        self.figure.tight_layout()
        self.canvas.draw()

    def plot_pie(self, labels, sizes, title):
        """绘制饼图"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        colors = ['#3498db', '#27ae60', '#f39c12', '#e74c3c', '#9b59b6']
        explode = [0.05] * len(labels)

        ax.pie(sizes, explode=explode, labels=labels, colors=colors,
               autopct='%1.1f%%', shadow=True, startangle=90)
        ax.set_title(title)
        ax.axis('equal')

        self.figure.tight_layout()
        self.canvas.draw()


# ==================== 主程序 ====================
def main():
    """主程序入口"""
    app = QApplication(sys.argv)

    # 设置应用图标和信息
    app.setApplicationName('FinancialCalculatorPro Enterprise')
    app.setApplicationVersion('2.0.0')
    app.setOrganizationName('FinancialSoft')

    # 创建主窗口
    window = FinancialEnterpriseSystem()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
