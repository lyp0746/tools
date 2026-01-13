#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DataVizPro - 专业数据分析与可视化平台
对标问卷星等专业数据分析软件，基于 PyQt5 的现代化数据分析解决方案
功能：数据导入、可视化、分析、报表生成
作者：LYP
GitHub：https://github.com/lyp0746
邮箱：1610369302@qq.com
版本：3.0.0
依赖: PyQt5, pandas, numpy, matplotlib, seaborn, plotly, openpyxl, scipy
"""

import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Matplotlib 配置
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

# PyQt5 核心
from PyQt5.QtCore import (
    Qt, QAbstractTableModel, QModelIndex, QSize, QTimer
)
from PyQt5.QtGui import (
    QFont, QColor, QKeySequence
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox,
    QVBoxLayout, QHBoxLayout, QWidget, QTableView, QSplitter,
    QTabWidget, QListWidget, QLabel, QPushButton,
    QFormLayout, QComboBox, QLineEdit, QSpinBox, QCheckBox,
    QStatusBar, QAction, QToolBar, QGroupBox, QTextEdit,
    QProgressBar, QScrollArea,
    QDoubleSpinBox, QInputDialog, QFrame, QStyleFactory, QDialog
)

# 可选依赖处理
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView

    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False
    print("警告: PyQtWebEngine 未安装，交互式图表功能将不可用")

try:
    import plotly.express as px
    import plotly.graph_objects as go

    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    print("警告: plotly 未安装，交互式图表功能受限")

try:
    from scipy import stats as scipy_stats

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("警告: scipy 未安装，高级统计功能受限")

import xml.etree.ElementTree as ET

warnings.filterwarnings('ignore')


# ===============================
# 应用配置
# ===============================

class AppConfig:
    """应用配置类"""
    APP_NAME = "DataVizPro"
    APP_VERSION = "3.0.0"
    APP_AUTHOR = "DataVizPro Team"

    # 文件路径
    CONFIG_DIR = Path.cwd() / ".datavizpro"
    TEMPLATE_DIR = CONFIG_DIR / "templates"
    CACHE_DIR = CONFIG_DIR / "cache"
    LOG_DIR = CONFIG_DIR / "logs"

    # 主题配置
    THEMES = {
        "浅色": {
            "primary": "#1976D2",
            "secondary": "#424242",
            "accent": "#FF4081",
            "background": "#FFFFFF",
            "surface": "#F5F5F5",
            "text": "#212121",
            "text_secondary": "#757575"
        },
        "深色": {
            "primary": "#2196F3",
            "secondary": "#616161",
            "accent": "#FF5252",
            "background": "#303030",
            "surface": "#424242",
            "text": "#FFFFFF",
            "text_secondary": "#BDBDBD"
        },
        "专业蓝": {
            "primary": "#0066CC",
            "secondary": "#003D7A",
            "accent": "#FF9900",
            "background": "#F8F9FA",
            "surface": "#FFFFFF",
            "text": "#333333",
            "text_secondary": "#666666"
        },
        "清新绿": {
            "primary": "#00A86B",
            "secondary": "#006644",
            "accent": "#FFA500",
            "background": "#F0F8F0",
            "surface": "#FFFFFF",
            "text": "#2C3E2C",
            "text_secondary": "#5A6B5A"
        }
    }

    # 数据处理配置
    MAX_PREVIEW_ROWS = 1000
    PAGE_SIZE = 100
    MAX_PLOT_ROWS = 500000
    SAMPLE_PLOT_ROWS = 50000

    # 图表配置
    CHART_TYPES = [
        ("折线图", "line", "📈"),
        ("柱状图", "bar", "📊"),
        ("饼图", "pie", "🥧"),
        ("散点图", "scatter", "⚫"),
        ("面积图", "area", "📉"),
        ("热力图", "heatmap", "🔥"),
        ("箱线图", "box", "📦"),
        ("小提琴图", "violin", "🎻"),
        ("直方图", "histogram", "📊"),
        ("密度图", "density", "🌊"),
        ("雷达图", "radar", "🎯"),
        ("漏斗图", "funnel", "🔻"),
        ("树状图", "treemap", "🌳"),
        ("瀑布图", "waterfall", "💧"),
        ("桑基图", "sankey", "🔀"),
        ("词云图", "wordcloud", "☁️")
    ]

    @classmethod
    def init_dirs(cls):
        """初始化目录结构"""
        for dir_path in [cls.CONFIG_DIR, cls.TEMPLATE_DIR, cls.CACHE_DIR, cls.LOG_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)


# ===============================
# 数据导入器
# ===============================

class DataImporter:
    """增强的数据导入器"""

    def __init__(self):
        self.current_df: Optional[pd.DataFrame] = None
        self.filepath: Optional[str] = None
        self.file_encoding: Optional[str] = None

    def detect_encoding(self, filepath: str) -> str:
        """智能检测文件编码"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1', 'iso-8859-1']

        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    f.read(1024)
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue

        return 'utf-8'

    def import_file(self, filepath: str, **kwargs) -> pd.DataFrame:
        """统一文件导入接口"""
        ext = Path(filepath).suffix.lower()

        handlers = {
            '.csv': self._import_csv,
            '.txt': self._import_txt,
            '.xlsx': self._import_excel,
            '.xls': self._import_excel,
            '.json': self._import_json,
            '.xml': self._import_xml,
        }

        handler = handlers.get(ext)
        if not handler:
            raise ValueError(f"不支持的文件类型: {ext}")

        df = handler(filepath, **kwargs)
        self.current_df = self._auto_detect_types(df)
        self.filepath = filepath

        return self.current_df

    def _import_csv(self, filepath: str, **kwargs) -> pd.DataFrame:
        """导入CSV文件"""
        encoding = kwargs.get('encoding')
        if not encoding or encoding == 'auto':
            encoding = self.detect_encoding(filepath)

        self.file_encoding = encoding
        delimiter = kwargs.get('delimiter', ',')

        return pd.read_csv(filepath, encoding=encoding, delimiter=delimiter,
                           low_memory=False)

    def _import_txt(self, filepath: str, **kwargs) -> pd.DataFrame:
        """导入TXT文件"""
        encoding = kwargs.get('encoding')
        if not encoding or encoding == 'auto':
            encoding = self.detect_encoding(filepath)

        delimiter = kwargs.get('delimiter', None)
        if not delimiter:
            with open(filepath, 'r', encoding=encoding) as f:
                first_line = f.readline()
                if '\t' in first_line:
                    delimiter = '\t'
                elif '|' in first_line:
                    delimiter = '|'
                elif ';' in first_line:
                    delimiter = ';'
                else:
                    delimiter = r'\s+'

        return pd.read_csv(filepath, encoding=encoding, sep=delimiter,
                           engine='python', low_memory=False)

    def _import_excel(self, filepath: str, **kwargs) -> pd.DataFrame:
        """导入Excel文件"""
        sheet_name = kwargs.get('sheet_name', 0)
        return pd.read_excel(filepath, sheet_name=sheet_name, engine='openpyxl')

    def _import_json(self, filepath: str, **kwargs) -> pd.DataFrame:
        """导入JSON文件"""
        orient = kwargs.get('orient', 'records')
        return pd.read_json(filepath, orient=orient)

    def _import_xml(self, filepath: str, **kwargs) -> pd.DataFrame:
        """导入XML文件"""
        tree = ET.parse(filepath)
        root = tree.getroot()

        records = []
        for child in root:
            record = {}
            for elem in child:
                record[elem.tag] = elem.text
            if record:
                records.append(record)

        return pd.DataFrame(records) if records else pd.DataFrame()

    def _auto_detect_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """自动检测并转换数据类型"""
        df = df.copy()

        for col in df.columns:
            if df[col].dtype == object:
                # 尝试转换为数值
                try:
                    df[col] = pd.to_numeric(df[col])
                    continue
                except (ValueError, TypeError):
                    pass

                # 尝试转换为日期时间
                try:
                    converted = pd.to_datetime(df[col], errors='coerce')
                    if converted.isna().sum() / len(df) < 0.5:
                        df[col] = converted
                except (ValueError, TypeError):
                    pass

        return df

    def get_basic_stats(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """获取数据基础统计信息"""
        df = df if df is not None else self.current_df
        if df is None or df.empty:
            return {}

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()

        return {
            'rows': len(df),
            'columns': len(df.columns),
            'numeric_columns': len(numeric_cols),
            'categorical_columns': len(categorical_cols),
            'datetime_columns': len(datetime_cols),
            'total_nulls': int(df.isna().sum().sum()),
            'memory_usage': df.memory_usage(deep=True).sum() / 1024 ** 2,
            'column_info': {
                col: {
                    'dtype': str(df[col].dtype),
                    'nulls': int(df[col].isna().sum()),
                    'unique': int(df[col].nunique()),
                    'sample': str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else 'N/A'
                }
                for col in df.columns
            }
        }


# ===============================
# 数据清洗器
# ===============================

class DataCleaner:
    """增强的数据清洗器"""

    @staticmethod
    def handle_missing(df: pd.DataFrame, method: str = 'drop',
                       columns: Optional[List[str]] = None,
                       value: Any = None) -> pd.DataFrame:
        """处理缺失值"""
        df = df.copy()
        cols = columns if columns else df.columns.tolist()

        if method == 'drop':
            df = df.dropna(subset=cols)
        elif method == 'fill_mean':
            for col in cols:
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].mean())
        elif method == 'fill_median':
            for col in cols:
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].median())
        elif method == 'fill_mode':
            for col in cols:
                mode_val = df[col].mode()
                if not mode_val.empty:
                    df[col] = df[col].fillna(mode_val[0])
        elif method == 'fill_forward':
            df[cols] = df[cols].ffill()
        elif method == 'fill_backward':
            df[cols] = df[cols].bfill()
        elif method == 'fill_value' and value is not None:
            df[cols] = df[cols].fillna(value)
        elif method == 'interpolate':
            for col in cols:
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].interpolate()

        return df

    @staticmethod
    def handle_duplicates(df: pd.DataFrame, subset: Optional[List[str]] = None,
                          keep: str = 'first') -> pd.DataFrame:
        """处理重复值"""
        return df.drop_duplicates(subset=subset, keep=keep)

    @staticmethod
    def handle_outliers(df: pd.DataFrame, column: str, method: str = 'iqr',
                        threshold: float = 1.5) -> pd.DataFrame:
        """处理异常值"""
        df = df.copy()

        if not pd.api.types.is_numeric_dtype(df[column]):
            return df

        if method == 'iqr':
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - threshold * IQR
            upper = Q3 + threshold * IQR
            df = df[(df[column] >= lower) & (df[column] <= upper)]

        elif method == 'zscore':
            z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
            df = df[z_scores < threshold]

        elif method == 'clip':
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - threshold * IQR
            upper = Q3 + threshold * IQR
            df[column] = df[column].clip(lower, upper)

        return df

    @staticmethod
    def transform_column(df: pd.DataFrame, column: str, method: str) -> Tuple[pd.DataFrame, List[int]]:
        """转换列类型"""
        df = df.copy()
        failed_indices = []

        if method == 'to_numeric':
            new_series = pd.to_numeric(df[column], errors='coerce')
        elif method == 'to_datetime':
            new_series = pd.to_datetime(df[column], errors='coerce')
        elif method == 'to_string':
            new_series = df[column].astype(str)
        elif method == 'to_category':
            new_series = df[column].astype('category')
        else:
            return df, []

        mask_failed = df[column].notna() & new_series.isna()
        failed_indices = df[mask_failed].index.tolist()

        df[column] = new_series
        return df, failed_indices

    @staticmethod
    def normalize_column(df: pd.DataFrame, column: str, method: str = 'minmax') -> pd.DataFrame:
        """标准化/归一化列"""
        df = df.copy()

        if not pd.api.types.is_numeric_dtype(df[column]):
            return df

        if method == 'minmax':
            min_val = df[column].min()
            max_val = df[column].max()
            if max_val != min_val:
                df[column] = (df[column] - min_val) / (max_val - min_val)

        elif method == 'zscore':
            mean_val = df[column].mean()
            std_val = df[column].std()
            if std_val != 0:
                df[column] = (df[column] - mean_val) / std_val

        elif method == 'log':
            df[column] = np.log1p(df[column].clip(lower=0))

        elif method == 'sqrt':
            df[column] = np.sqrt(df[column].clip(lower=0))

        return df


# ===============================
# 统计分析器
# ===============================

class StatisticalAnalyzer:
    """统计分析器"""

    @staticmethod
    def descriptive_stats(df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """描述性统计"""
        if column not in df.columns:
            return {}

        series = df[column].dropna()

        if pd.api.types.is_numeric_dtype(series):
            stats = {
                '计数': len(series),
                '均值': float(series.mean()),
                '中位数': float(series.median()),
                '众数': float(series.mode()[0]) if not series.mode().empty else None,
                '标准差': float(series.std()),
                '方差': float(series.var()),
                '最小值': float(series.min()),
                '最大值': float(series.max()),
                '25分位': float(series.quantile(0.25)),
                '75分位': float(series.quantile(0.75)),
                '偏度': float(series.skew()),
                '峰度': float(series.kurtosis())
            }
        else:
            value_counts = series.value_counts()
            stats = {
                '计数': len(series),
                '唯一值': series.nunique(),
                '最频繁': str(value_counts.index[0]) if not value_counts.empty else None,
                '频数': int(value_counts.iloc[0]) if not value_counts.empty else 0,
                '频数分布': value_counts.head(10).to_dict()
            }

        return stats

    @staticmethod
    def correlation_analysis(df: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame:
        """相关性分析"""
        numeric_df = df.select_dtypes(include=[np.number])

        if numeric_df.empty:
            return pd.DataFrame()

        return numeric_df.corr(method=method)


# ===============================
# 图表渲染器
# ===============================

class ChartRenderer:
    """增强的图表渲染器"""

    def __init__(self):
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['figure.autolayout'] = True

        self.figure_size = (10, 6)
        self.dpi = 100
        self.color_palette = 'Set2'

    def create_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Figure:
        """统一图表创建接口"""
        chart_type = config.get('chart_type', 'line')

        chart_methods = {
            'line': self._line_chart,
            'bar': self._bar_chart,
            'pie': self._pie_chart,
            'scatter': self._scatter_chart,
            'area': self._area_chart,
            'heatmap': self._heatmap_chart,
            'box': self._box_chart,
            'violin': self._violin_chart,
            'histogram': self._histogram_chart,
            'density': self._density_chart,
        }

        method = chart_methods.get(chart_type, self._line_chart)
        return method(df, config)

    def _prepare_figure(self, config: Dict[str, Any]) -> Tuple[Figure, Any]:
        """准备画布"""
        figsize = config.get('figsize', self.figure_size)
        dpi = config.get('dpi', self.dpi)

        fig = Figure(figsize=figsize, dpi=dpi)
        ax = fig.add_subplot(111)

        return fig, ax

    def _apply_styling(self, ax: Any, config: Dict[str, Any]):
        """应用样式配置"""
        if config.get('title'):
            ax.set_title(config['title'], fontsize=config.get('title_size', 14),
                         fontweight='bold', pad=20)

        if config.get('xlabel'):
            ax.set_xlabel(config['xlabel'], fontsize=config.get('label_size', 11))

        if config.get('ylabel'):
            ax.set_ylabel(config['ylabel'], fontsize=config.get('label_size', 11))

        if config.get('grid', True):
            ax.grid(True, alpha=0.3, linestyle='--')

        if config.get('legend', True) and ax.get_legend_handles_labels()[0]:
            ax.legend(fontsize=config.get('legend_size', 10))

    def _line_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Figure:
        """折线图"""
        fig, ax = self._prepare_figure(config)

        x = config.get('x')
        y = config.get('y', [])
        if isinstance(y, str):
            y = [y]

        hue = config.get('hue')

        if hue and hue in df.columns:
            for group_name in df[hue].unique():
                group_data = df[df[hue] == group_name]
                if y and y[0] in group_data.columns:
                    ax.plot(group_data[x], group_data[y[0]],
                            marker='o', label=str(group_name), linewidth=2)
        else:
            for col in y:
                if col in df.columns:
                    ax.plot(df[x], df[col], marker='o',
                            label=col, linewidth=2, markersize=4)

        self._apply_styling(ax, config)
        fig.tight_layout()

        return fig

    def _bar_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Figure:
        """柱状图"""
        fig, ax = self._prepare_figure(config)

        x = config.get('x')
        y = config.get('y')
        if isinstance(y, list):
            y = y[0] if y else None

        hue = config.get('hue')
        orientation = config.get('orientation', 'vertical')

        if hue and hue in df.columns:
            grouped = df.groupby([x, hue])[y].mean().unstack()
            if orientation == 'horizontal':
                grouped.plot(kind='barh', ax=ax, width=0.8, legend=True)
            else:
                grouped.plot(kind='bar', ax=ax, width=0.8, legend=True)
        else:
            if orientation == 'horizontal':
                ax.barh(df[x], df[y], height=0.8)
            else:
                ax.bar(df[x], df[y], width=0.8, color=plt.cm.get_cmap(self.color_palette)(0))

        if orientation == 'vertical':
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

        self._apply_styling(ax, config)
        fig.tight_layout()

        return fig

    def _pie_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Figure:
        """饼图"""
        fig, ax = self._prepare_figure(config)

        labels_col = config.get('x')
        values_col = config.get('y')
        if isinstance(values_col, list):
            values_col = values_col[0]

        labels = df[labels_col].astype(str)
        values = df[values_col]

        mask = values > 0
        labels = labels[mask]
        values = values[mask]

        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%',
                                          colors=colors, startangle=90,
                                          textprops={'fontsize': 10})

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        ax.axis('equal')

        if config.get('title'):
            ax.set_title(config['title'], fontsize=config.get('title_size', 14),
                         fontweight='bold', pad=20)

        fig.tight_layout()

        return fig

    def _scatter_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Figure:
        """散点图"""
        fig, ax = self._prepare_figure(config)

        x = config.get('x')
        y = config.get('y')
        if isinstance(y, list):
            y = y[0]

        hue = config.get('hue')
        size = config.get('size')

        if hue and hue in df.columns:
            for group_name in df[hue].unique():
                group_data = df[df[hue] == group_name]
                sizes = group_data[size] * 50 if size and size in df.columns else 50
                ax.scatter(group_data[x], group_data[y],
                           s=sizes, label=str(group_name), alpha=0.6)
        else:
            sizes = df[size] * 50 if size and size in df.columns else 50
            ax.scatter(df[x], df[y], s=sizes, alpha=0.6,
                       color=plt.cm.get_cmap(self.color_palette)(0))

        self._apply_styling(ax, config)
        fig.tight_layout()

        return fig

    def _area_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Figure:
        """面积图"""
        fig, ax = self._prepare_figure(config)

        x = config.get('x')
        y = config.get('y', [])
        if isinstance(y, str):
            y = [y]

        for col in y:
            if col in df.columns:
                ax.fill_between(df[x], df[col], alpha=0.5, label=col)

        self._apply_styling(ax, config)
        fig.tight_layout()

        return fig

    def _heatmap_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Figure:
        """热力图"""
        fig, ax = self._prepare_figure(config)

        if config.get('correlation', True):
            numeric_df = df.select_dtypes(include=[np.number])
            if not numeric_df.empty:
                corr = numeric_df.corr()
                sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm',
                            center=0, ax=ax, cbar_kws={'label': '相关系数'})

        self._apply_styling(ax, config)
        fig.tight_layout()

        return fig

    def _box_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Figure:
        """箱线图"""
        fig, ax = self._prepare_figure(config)

        x = config.get('x')
        y = config.get('y')
        if isinstance(y, list):
            y = y[0]

        hue = config.get('hue')

        sns.boxplot(data=df, x=x, y=y, hue=hue, ax=ax, palette=self.color_palette)

        self._apply_styling(ax, config)
        fig.tight_layout()

        return fig

    def _violin_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Figure:
        """小提琴图"""
        fig, ax = self._prepare_figure(config)

        x = config.get('x')
        y = config.get('y')
        if isinstance(y, list):
            y = y[0]

        hue = config.get('hue')

        sns.violinplot(data=df, x=x, y=y, hue=hue, ax=ax, palette=self.color_palette)

        self._apply_styling(ax, config)
        fig.tight_layout()

        return fig

    def _histogram_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Figure:
        """直方图"""
        fig, ax = self._prepare_figure(config)

        column = config.get('y')
        if isinstance(column, list):
            column = column[0]

        bins = config.get('bins', 30)

        ax.hist(df[column].dropna(), bins=bins, alpha=0.7,
                color='steelblue', edgecolor='black')

        self._apply_styling(ax, config)
        fig.tight_layout()

        return fig

    def _density_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Figure:
        """密度图"""
        fig, ax = self._prepare_figure(config)

        y = config.get('y', [])
        if isinstance(y, str):
            y = [y]

        for col in y:
            if col in df.columns:
                df[col].dropna().plot.density(ax=ax, label=col, linewidth=2)

        self._apply_styling(ax, config)
        fig.tight_layout()

        return fig


# ===============================
# 交互式图表渲染器
# ===============================

class InteractiveChartRenderer:
    """交互式图表渲染器（基于Plotly）"""

    @staticmethod
    def create_interactive_chart(df: pd.DataFrame, config: Dict[str, Any]) -> Optional[str]:
        """创建交互式图表并返回HTML"""
        if not HAS_PLOTLY:
            return None

        chart_type = config.get('chart_type', 'line')

        chart_methods = {
            'line': InteractiveChartRenderer._plotly_line,
            'bar': InteractiveChartRenderer._plotly_bar,
            'pie': InteractiveChartRenderer._plotly_pie,
            'scatter': InteractiveChartRenderer._plotly_scatter,
            'area': InteractiveChartRenderer._plotly_area,
            'box': InteractiveChartRenderer._plotly_box,
            'violin': InteractiveChartRenderer._plotly_violin,
            'histogram': InteractiveChartRenderer._plotly_histogram,
            'heatmap': InteractiveChartRenderer._plotly_heatmap,
            'funnel': InteractiveChartRenderer._plotly_funnel,
            'treemap': InteractiveChartRenderer._plotly_treemap,
            'waterfall': InteractiveChartRenderer._plotly_waterfall,
        }

        method = chart_methods.get(chart_type)
        if not method:
            return None

        try:
            fig = method(df, config)
            return fig.to_html(include_plotlyjs='cdn', full_html=True)
        except Exception as e:
            print(f"创建交互式图表失败: {str(e)}")
            return None

    @staticmethod
    def _plotly_line(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Plotly折线图"""
        x = config.get('x')
        y = config.get('y', [])
        if isinstance(y, str):
            y = [y]
        hue = config.get('hue')

        fig = px.line(df, x=x, y=y, color=hue,
                      title=config.get('title', ''),
                      labels={x: config.get('xlabel', x),
                              y[0] if y else '': config.get('ylabel', '')})

        fig.update_traces(mode='lines+markers', marker_size=6, line_width=2)
        fig.update_layout(hovermode='x unified')

        return fig

    @staticmethod
    def _plotly_bar(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Plotly柱状图"""
        x = config.get('x')
        y = config.get('y')
        if isinstance(y, list):
            y = y[0]
        hue = config.get('hue')
        orientation = config.get('orientation', 'v')

        if orientation == 'horizontal':
            fig = px.bar(df, y=x, x=y, color=hue,
                         title=config.get('title', ''),
                         orientation='h')
        else:
            fig = px.bar(df, x=x, y=y, color=hue,
                         title=config.get('title', ''))

        fig.update_layout(hovermode='closest')

        return fig

    @staticmethod
    def _plotly_pie(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Plotly饼图"""
        labels_col = config.get('x')
        values_col = config.get('y')
        if isinstance(values_col, list):
            values_col = values_col[0]

        fig = px.pie(df, names=labels_col, values=values_col,
                     title=config.get('title', ''))

        fig.update_traces(textposition='inside', textinfo='percent+label')

        return fig

    @staticmethod
    def _plotly_scatter(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Plotly散点图"""
        x = config.get('x')
        y = config.get('y')
        if isinstance(y, list):
            y = y[0]
        hue = config.get('hue')
        size = config.get('size')

        fig = px.scatter(df, x=x, y=y, color=hue, size=size,
                         title=config.get('title', ''),
                         labels={x: config.get('xlabel', x),
                                 y: config.get('ylabel', y)})

        fig.update_traces(marker=dict(line=dict(width=0.5, color='white')))

        return fig

    @staticmethod
    def _plotly_area(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Plotly面积图"""
        x = config.get('x')
        y = config.get('y', [])
        if isinstance(y, str):
            y = [y]

        fig = px.area(df, x=x, y=y, title=config.get('title', ''))

        return fig

    @staticmethod
    def _plotly_box(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Plotly箱线图"""
        x = config.get('x')
        y = config.get('y')
        if isinstance(y, list):
            y = y[0]
        hue = config.get('hue')

        fig = px.box(df, x=x, y=y, color=hue, title=config.get('title', ''))

        return fig

    @staticmethod
    def _plotly_violin(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Plotly小提琴图"""
        x = config.get('x')
        y = config.get('y')
        if isinstance(y, list):
            y = y[0]
        hue = config.get('hue')

        fig = px.violin(df, x=x, y=y, color=hue, title=config.get('title', ''))

        return fig

    @staticmethod
    def _plotly_histogram(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Plotly直方图"""
        column = config.get('y')
        if isinstance(column, list):
            column = column[0]
        bins = config.get('bins', 30)

        fig = px.histogram(df, x=column, nbins=bins, title=config.get('title', ''))

        return fig

    @staticmethod
    def _plotly_heatmap(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Plotly热力图"""
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return go.Figure()

        corr = numeric_df.corr()

        fig = px.imshow(corr, text_auto='.2f', aspect='auto',
                        color_continuous_scale='RdBu_r',
                        title=config.get('title', '相关性热力图'))

        return fig

    @staticmethod
    def _plotly_funnel(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Plotly漏斗图"""
        x = config.get('x')
        y = config.get('y')
        if isinstance(y, list):
            y = y[0]

        fig = go.Figure(go.Funnel(
            y=df[x],
            x=df[y],
            textinfo="value+percent initial"
        ))

        fig.update_layout(title=config.get('title', ''))

        return fig

    @staticmethod
    def _plotly_treemap(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Plotly树状图"""
        path = config.get('path', [config.get('x')])
        values = config.get('y')
        if isinstance(values, list):
            values = values[0]

        fig = px.treemap(df, path=path, values=values,
                         title=config.get('title', ''))

        return fig

    @staticmethod
    def _plotly_waterfall(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Plotly瀑布图"""
        x = config.get('x')
        y = config.get('y')
        if isinstance(y, list):
            y = y[0]

        fig = go.Figure(go.Waterfall(
            x=df[x],
            y=df[y],
            textposition="outside"
        ))

        fig.update_layout(title=config.get('title', ''))

        return fig


# ===============================
# 数据模型
# ===============================

class PandasTableModel(QAbstractTableModel):
    """Pandas DataFrame 的 Qt 表格模型"""

    def __init__(self, df: pd.DataFrame = None, parent=None):
        super().__init__(parent)
        self._df = df if df is not None else pd.DataFrame()
        self._original_df = self._df.copy() if df is not None else pd.DataFrame()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._df) if not parent.isValid() else 0

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._df.columns) if not parent.isValid() else 0

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        value = self._df.iloc[index.row(), index.column()]

        if role == Qt.DisplayRole:
            if pd.isna(value):
                return 'NaN'
            elif isinstance(value, (float, np.floating)):
                return f'{value:.4f}'
            else:
                return str(value)

        elif role == Qt.TextAlignmentRole:
            if pd.api.types.is_numeric_dtype(self._df.iloc[:, index.column()]):
                return Qt.AlignRight | Qt.AlignVCenter
            else:
                return Qt.AlignLeft | Qt.AlignVCenter

        elif role == Qt.BackgroundRole:
            if pd.isna(value):
                return QColor(255, 240, 240)

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                col_name = str(self._df.columns[section])
                dtype = str(self._df.dtypes[section])
                return f"{col_name}\n({dtype})"
            else:
                return str(section + 1)

        elif role == Qt.FontRole:
            font = QFont()
            font.setBold(True)
            return font

        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

        return None

    def get_dataframe(self) -> pd.DataFrame:
        return self._df.copy()

    def update_dataframe(self, df: pd.DataFrame):
        self.beginResetModel()
        self._df = df.copy()
        self.endResetModel()


# ===============================
# 主窗口
# ===============================

class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()

        # 初始化组件
        self.importer = DataImporter()
        self.cleaner = DataCleaner()
        self.analyzer = StatisticalAnalyzer()
        self.chart_renderer = ChartRenderer()
        self.interactive_renderer = InteractiveChartRenderer()

        # 数据
        self.current_df: Optional[pd.DataFrame] = None
        self.table_model = PandasTableModel()
        self.operation_history: List[pd.DataFrame] = []
        self.history_index = -1

        # 配置
        self.current_theme = "浅色"
        self.chart_configs: Dict[str, Dict] = {}

        # 初始化UI
        self.init_ui()
        self.init_menus()
        self.init_toolbar()
        self.init_statusbar()

        # 应用主题
        self.apply_theme(self.current_theme)

        # 显示欢迎信息
        self.show_welcome_message()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle(f"{AppConfig.APP_NAME} {AppConfig.APP_VERSION}")
        self.setGeometry(100, 100, 1400, 900)

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 左侧面板（数据预览和信息）
        left_panel = self.create_left_panel()
        left_panel.setMinimumWidth(400)

        # 右侧面板（图表和控制）
        right_panel = self.create_right_panel()

        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)

    def create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(5)

        # 数据信息组
        info_group = QGroupBox("📊 数据信息")
        info_layout = QVBoxLayout(info_group)

        self.data_info_label = QLabel("未加载数据")
        self.data_info_label.setWordWrap(True)
        self.data_info_label.setStyleSheet("padding: 10px; background: #f5f5f5;")
        info_layout.addWidget(self.data_info_label)

        layout.addWidget(info_group)

        # 数据预览表格
        preview_group = QGroupBox("🔍 数据预览")
        preview_layout = QVBoxLayout(preview_group)

        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        preview_layout.addWidget(self.table_view)

        layout.addWidget(preview_group, 1)

        # 快速操作按钮
        quick_actions_group = QGroupBox("⚡ 快速操作")
        quick_actions_layout = QVBoxLayout(quick_actions_group)

        btn_layout1 = QHBoxLayout()
        self.btn_refresh = QPushButton("🔄 刷新")
        self.btn_refresh.clicked.connect(self.refresh_data)
        self.btn_filter = QPushButton("🔍 筛选")
        self.btn_filter.clicked.connect(self.show_filter_dialog)
        btn_layout1.addWidget(self.btn_refresh)
        btn_layout1.addWidget(self.btn_filter)

        btn_layout2 = QHBoxLayout()
        self.btn_stats = QPushButton("📈 统计分析")
        self.btn_stats.clicked.connect(self.show_stats_dialog)
        self.btn_export = QPushButton("💾 导出数据")
        self.btn_export.clicked.connect(self.export_data)
        btn_layout2.addWidget(self.btn_stats)
        btn_layout2.addWidget(self.btn_export)

        quick_actions_layout.addLayout(btn_layout1)
        quick_actions_layout.addLayout(btn_layout2)

        layout.addWidget(quick_actions_group)

        return panel

    def create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(5)

        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)

        # 图表配置标签
        self.chart_config_tab = self.create_chart_config_tab()
        self.tab_widget.addTab(self.chart_config_tab, "📊 图表配置")

        # 数据清洗标签
        self.data_cleaning_tab = self.create_data_cleaning_tab()
        self.tab_widget.addTab(self.data_cleaning_tab, "🧹 数据清洗")

        # 统计分析标签
        self.stats_tab = self.create_stats_tab()
        self.tab_widget.addTab(self.stats_tab, "📈 统计分析")

        layout.addWidget(self.tab_widget)

        # 图表显示区域
        chart_group = QGroupBox("📊 图表显示")
        chart_layout = QVBoxLayout(chart_group)

        # 图表工具栏
        chart_toolbar = QHBoxLayout()
        self.btn_generate_chart = QPushButton("🎨 生成图表")
        self.btn_generate_chart.clicked.connect(self.generate_chart)
        self.btn_generate_chart.setStyleSheet("""  
            QPushButton {  
                background-color: #1976D2;  
                color: white;  
                font-weight: bold;  
                padding: 8px 16px;  
                border-radius: 4px;  
            }  
            QPushButton:hover {  
                background-color: #1565C0;  
            }  
        """)

        self.btn_interactive_chart = QPushButton("🌐 交互式图表")
        self.btn_interactive_chart.clicked.connect(self.generate_interactive_chart)
        self.btn_interactive_chart.setEnabled(HAS_PLOTLY and HAS_WEBENGINE)

        self.btn_save_chart = QPushButton("💾 保存图表")
        self.btn_save_chart.clicked.connect(self.save_chart)

        chart_toolbar.addWidget(self.btn_generate_chart)
        chart_toolbar.addWidget(self.btn_interactive_chart)
        chart_toolbar.addWidget(self.btn_save_chart)
        chart_toolbar.addStretch()

        chart_layout.addLayout(chart_toolbar)

        # 图表显示标签页
        self.chart_tab_widget = QTabWidget()
        self.chart_tab_widget.setTabsClosable(True)
        self.chart_tab_widget.tabCloseRequested.connect(self.close_chart_tab)

        chart_layout.addWidget(self.chart_tab_widget, 1)

        layout.addWidget(chart_group, 1)

        return panel

    def create_chart_config_tab(self) -> QWidget:
        """创建图表配置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # 图表类型选择
        type_group = QGroupBox("图表类型")
        type_layout = QVBoxLayout(type_group)

        self.chart_type_combo = QComboBox()
        for name, code, icon in AppConfig.CHART_TYPES:
            self.chart_type_combo.addItem(f"{icon} {name}", code)
        self.chart_type_combo.currentIndexChanged.connect(self.on_chart_type_changed)

        type_layout.addWidget(self.chart_type_combo)
        scroll_layout.addWidget(type_group)

        # 数据映射
        mapping_group = QGroupBox("数据映射")
        mapping_layout = QFormLayout(mapping_group)

        self.x_combo = QComboBox()
        self.y_list = QListWidget()
        self.y_list.setSelectionMode(QListWidget.MultiSelection)
        self.y_list.setMaximumHeight(120)

        self.hue_combo = QComboBox()
        self.size_combo = QComboBox()

        mapping_layout.addRow("X 轴:", self.x_combo)
        mapping_layout.addRow("Y 轴:", self.y_list)
        mapping_layout.addRow("分组 (Hue):", self.hue_combo)
        mapping_layout.addRow("大小 (Size):", self.size_combo)

        scroll_layout.addWidget(mapping_group)

        # 样式配置
        style_group = QGroupBox("样式配置")
        style_layout = QFormLayout(style_group)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("输入图表标题")

        self.xlabel_input = QLineEdit()
        self.xlabel_input.setPlaceholderText("X轴标签")

        self.ylabel_input = QLineEdit()
        self.ylabel_input.setPlaceholderText("Y轴标签")

        self.grid_check = QCheckBox("显示网格")
        self.grid_check.setChecked(True)

        self.legend_check = QCheckBox("显示图例")
        self.legend_check.setChecked(True)

        style_layout.addRow("标题:", self.title_input)
        style_layout.addRow("X轴标签:", self.xlabel_input)
        style_layout.addRow("Y轴标签:", self.ylabel_input)
        style_layout.addRow("", self.grid_check)
        style_layout.addRow("", self.legend_check)

        scroll_layout.addWidget(style_group)

        # 高级选项
        advanced_group = QGroupBox("高级选项")
        advanced_layout = QFormLayout(advanced_group)

        self.figsize_width = QSpinBox()
        self.figsize_width.setRange(5, 20)
        self.figsize_width.setValue(10)

        self.figsize_height = QSpinBox()
        self.figsize_height.setRange(4, 15)
        self.figsize_height.setValue(6)

        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(50, 300)
        self.dpi_spin.setValue(100)
        self.dpi_spin.setSuffix(" dpi")

        figsize_layout = QHBoxLayout()
        figsize_layout.addWidget(self.figsize_width)
        figsize_layout.addWidget(QLabel("×"))
        figsize_layout.addWidget(self.figsize_height)

        advanced_layout.addRow("图表大小:", figsize_layout)
        advanced_layout.addRow("分辨率:", self.dpi_spin)

        scroll_layout.addWidget(advanced_group)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return widget

    def create_data_cleaning_tab(self) -> QWidget:
        """创建数据清洗标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # 缺失值处理
        missing_group = QGroupBox("缺失值处理")
        missing_layout = QVBoxLayout(missing_group)

        self.missing_method_combo = QComboBox()
        self.missing_method_combo.addItems([
            "删除缺失行", "均值填充", "中位数填充", "众数填充",
            "向前填充", "向后填充", "插值填充", "自定义值填充"
        ])

        self.missing_value_input = QLineEdit()
        self.missing_value_input.setPlaceholderText("自定义填充值")

        self.missing_columns_list = QListWidget()
        self.missing_columns_list.setSelectionMode(QListWidget.MultiSelection)
        self.missing_columns_list.setMaximumHeight(100)

        btn_handle_missing = QPushButton("执行缺失值处理")
        btn_handle_missing.clicked.connect(self.handle_missing_values)

        missing_layout.addWidget(QLabel("处理方法:"))
        missing_layout.addWidget(self.missing_method_combo)
        missing_layout.addWidget(QLabel("自定义值:"))
        missing_layout.addWidget(self.missing_value_input)
        missing_layout.addWidget(QLabel("选择列:"))
        missing_layout.addWidget(self.missing_columns_list)
        missing_layout.addWidget(btn_handle_missing)

        scroll_layout.addWidget(missing_group)

        # 重复值处理
        duplicate_group = QGroupBox("重复值处理")
        duplicate_layout = QVBoxLayout(duplicate_group)

        self.duplicate_keep_combo = QComboBox()
        self.duplicate_keep_combo.addItems(["保留第一个", "保留最后一个", "全部删除"])

        btn_handle_duplicates = QPushButton("删除重复行")
        btn_handle_duplicates.clicked.connect(self.handle_duplicates)

        duplicate_layout.addWidget(QLabel("保留策略:"))
        duplicate_layout.addWidget(self.duplicate_keep_combo)
        duplicate_layout.addWidget(btn_handle_duplicates)

        scroll_layout.addWidget(duplicate_group)

        # 异常值处理
        outlier_group = QGroupBox("异常值处理")
        outlier_layout = QVBoxLayout(outlier_group)

        self.outlier_column_combo = QComboBox()

        self.outlier_method_combo = QComboBox()
        self.outlier_method_combo.addItems(["IQR方法", "Z-Score方法", "截断(Clip)"])

        self.outlier_threshold_spin = QDoubleSpinBox()
        self.outlier_threshold_spin.setRange(0.1, 10.0)
        self.outlier_threshold_spin.setValue(1.5)
        self.outlier_threshold_spin.setSingleStep(0.1)

        btn_handle_outliers = QPushButton("处理异常值")
        btn_handle_outliers.clicked.connect(self.handle_outliers)

        outlier_layout.addWidget(QLabel("选择列:"))
        outlier_layout.addWidget(self.outlier_column_combo)
        outlier_layout.addWidget(QLabel("方法:"))
        outlier_layout.addWidget(self.outlier_method_combo)
        outlier_layout.addWidget(QLabel("阈值:"))
        outlier_layout.addWidget(self.outlier_threshold_spin)
        outlier_layout.addWidget(btn_handle_outliers)

        scroll_layout.addWidget(outlier_group)

        # 数据转换
        transform_group = QGroupBox("数据类型转换")
        transform_layout = QVBoxLayout(transform_group)

        self.transform_column_combo = QComboBox()

        self.transform_method_combo = QComboBox()
        self.transform_method_combo.addItems([
            "转换为数值", "转换为日期时间", "转换为字符串", "转换为类别"
        ])

        btn_transform = QPushButton("执行转换")
        btn_transform.clicked.connect(self.transform_column_type)

        transform_layout.addWidget(QLabel("选择列:"))
        transform_layout.addWidget(self.transform_column_combo)
        transform_layout.addWidget(QLabel("转换类型:"))
        transform_layout.addWidget(self.transform_method_combo)
        transform_layout.addWidget(btn_transform)

        scroll_layout.addWidget(transform_group)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return widget

    def create_stats_tab(self) -> QWidget:
        """创建统计分析标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 描述性统计
        desc_group = QGroupBox("描述性统计")
        desc_layout = QVBoxLayout(desc_group)

        self.stats_column_combo = QComboBox()

        btn_desc_stats = QPushButton("查看描述统计")
        btn_desc_stats.clicked.connect(self.show_descriptive_stats)

        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(200)

        desc_layout.addWidget(QLabel("选择列:"))
        desc_layout.addWidget(self.stats_column_combo)
        desc_layout.addWidget(btn_desc_stats)
        desc_layout.addWidget(self.stats_text)

        layout.addWidget(desc_group)

        # 相关性分析
        corr_group = QGroupBox("相关性分析")
        corr_layout = QVBoxLayout(corr_group)

        self.corr_method_combo = QComboBox()
        self.corr_method_combo.addItems(["Pearson", "Spearman", "Kendall"])

        btn_corr_analysis = QPushButton("生成相关性矩阵")
        btn_corr_analysis.clicked.connect(self.show_correlation_analysis)

        corr_layout.addWidget(QLabel("相关系数方法:"))
        corr_layout.addWidget(self.corr_method_combo)
        corr_layout.addWidget(btn_corr_analysis)

        layout.addWidget(corr_group)

        layout.addStretch()

        return widget

    def init_menus(self):
        """初始化菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        action_open = QAction("📁 打开文件", self)
        action_open.setShortcut(QKeySequence.Open)
        action_open.triggered.connect(self.open_file)
        file_menu.addAction(action_open)

        action_save = QAction("💾 保存数据", self)
        action_save.setShortcut(QKeySequence.Save)
        action_save.triggered.connect(self.export_data)
        file_menu.addAction(action_save)

        file_menu.addSeparator()

        action_export_report = QAction("📄 导出报告", self)
        action_export_report.triggered.connect(self.export_report)
        file_menu.addAction(action_export_report)

        file_menu.addSeparator()

        action_exit = QAction("❌ 退出", self)
        action_exit.setShortcut(QKeySequence.Quit)
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")

        action_undo = QAction("↶ 撤销", self)
        action_undo.setShortcut(QKeySequence.Undo)
        action_undo.triggered.connect(self.undo_operation)
        edit_menu.addAction(action_undo)

        action_redo = QAction("↷ 重做", self)
        action_redo.setShortcut(QKeySequence.Redo)
        action_redo.triggered.connect(self.redo_operation)
        edit_menu.addAction(action_redo)

        edit_menu.addSeparator()

        action_copy = QAction("📋 复制", self)
        action_copy.setShortcut(QKeySequence.Copy)
        action_copy.triggered.connect(self.copy_selection)
        edit_menu.addAction(action_copy)

        # 数据菜单
        data_menu = menubar.addMenu("数据")

        action_refresh = QAction("🔄 刷新数据", self)
        action_refresh.setShortcut("F5")
        action_refresh.triggered.connect(self.refresh_data)
        data_menu.addAction(action_refresh)

        action_filter = QAction("🔍 筛选数据", self)
        action_filter.triggered.connect(self.show_filter_dialog)
        data_menu.addAction(action_filter)

        data_menu.addSeparator()

        action_sort = QAction("⬍ 排序", self)
        action_sort.triggered.connect(self.show_sort_dialog)
        data_menu.addAction(action_sort)

        # 视图菜单
        view_menu = menubar.addMenu("视图")

        theme_submenu = view_menu.addMenu("🎨 主题")
        for theme_name in AppConfig.THEMES.keys():
            action_theme = QAction(theme_name, self)
            action_theme.triggered.connect(lambda checked, t=theme_name: self.apply_theme(t))
            theme_submenu.addAction(action_theme)

        view_menu.addSeparator()

        action_fullscreen = QAction("⛶ 全屏", self)
        action_fullscreen.setShortcut("F11")
        action_fullscreen.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(action_fullscreen)

        # 工具菜单
        tools_menu = menubar.addMenu("工具")

        action_templates = QAction("📑 分析模板", self)
        action_templates.triggered.connect(self.show_templates_dialog)
        tools_menu.addAction(action_templates)

        action_batch = QAction("⚡ 批量处理", self)
        action_batch.triggered.connect(self.show_batch_dialog)
        tools_menu.addAction(action_batch)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        action_docs = QAction("📖 文档", self)
        action_docs.triggered.connect(self.show_documentation)
        help_menu.addAction(action_docs)

        action_about = QAction("ℹ️ 关于", self)
        action_about.triggered.connect(self.show_about_dialog)
        help_menu.addAction(action_about)

    def init_toolbar(self):
        """初始化工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)

        # 打开文件
        action_open = QAction("📁\n打开", self)
        action_open.triggered.connect(self.open_file)
        toolbar.addAction(action_open)

        # 保存
        action_save = QAction("💾\n保存", self)
        action_save.triggered.connect(self.export_data)
        toolbar.addAction(action_save)

        toolbar.addSeparator()

        # 刷新
        action_refresh = QAction("🔄\n刷新", self)
        action_refresh.triggered.connect(self.refresh_data)
        toolbar.addAction(action_refresh)

        # 筛选
        action_filter = QAction("🔍\n筛选", self)
        action_filter.triggered.connect(self.show_filter_dialog)
        toolbar.addAction(action_filter)

        toolbar.addSeparator()

        # 统计
        action_stats = QAction("📈\n统计", self)
        action_stats.triggered.connect(self.show_stats_dialog)
        toolbar.addAction(action_stats)

        # 图表
        action_chart = QAction("📊\n图表", self)
        action_chart.triggered.connect(self.generate_chart)
        toolbar.addAction(action_chart)

        toolbar.addSeparator()

        # 撤销/重做
        action_undo = QAction("↶\n撤销", self)
        action_undo.triggered.connect(self.undo_operation)
        toolbar.addAction(action_undo)

        action_redo = QAction("↷\n重做", self)
        action_redo.triggered.connect(self.redo_operation)
        toolbar.addAction(action_redo)

    def init_statusbar(self):
        """初始化状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.status_label = QLabel("就绪")
        self.statusbar.addWidget(self.status_label)

        self.statusbar.addPermanentWidget(QLabel(""))

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.statusbar.addPermanentWidget(self.progress_bar)

    def show_welcome_message(self):
        """显示欢迎信息"""
        welcome_html = f"""  
                <div style='text-align: center; padding: 20px;'>  
                    <h2>欢迎使用 {AppConfig.APP_NAME} {AppConfig.APP_VERSION}</h2>  
                    <p>专业的数据分析与可视化平台</p>  
                    <hr>  
                    <p style='color: #666;'>  
                        点击 <b>文件 → 打开文件</b> 开始分析<br>  
                        或使用工具栏中的 📁 按钮  
                    </p>  
                    <p style='margin-top: 20px; font-size: 12px; color: #999;'>  
                        支持格式: CSV, Excel, JSON, XML, TXT  
                    </p>  
                </div>  
                """
        self.data_info_label.setText(welcome_html)
        self.data_info_label.setTextFormat(Qt.RichText)

        # ===============================
        # 文件操作
        # ===============================

    def open_file(self):
        """打开文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开数据文件",
            "",
            "所有支持的文件 (*.csv *.xlsx *.xls *.json *.xml *.txt);;"
            "CSV文件 (*.csv);;"
            "Excel文件 (*.xlsx *.xls);;"
            "JSON文件 (*.json);;"
            "XML文件 (*.xml);;"
            "文本文件 (*.txt);;"
            "所有文件 (*.*)"
        )

        if not file_path:
            return

        self.load_file(file_path)

    def load_file(self, filepath: str):
        """加载文件"""
        try:
            self.set_status("正在加载文件...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(30)

            # 导入数据
            df = self.importer.import_file(filepath)

            self.progress_bar.setValue(60)

            # 数据采样（如果数据量过大）
            if len(df) > AppConfig.MAX_PREVIEW_ROWS:
                preview_df = df.head(AppConfig.MAX_PREVIEW_ROWS)
                QMessageBox.information(
                    self,
                    "数据采样",
                    f"数据量较大({len(df)}行)，表格预览显示前{AppConfig.MAX_PREVIEW_ROWS}行"
                )
            else:
                preview_df = df

            self.current_df = df
            self.table_model.update_dataframe(preview_df)

            # 初始化历史记录
            self.operation_history = [df.copy()]
            self.history_index = 0

            self.progress_bar.setValue(80)

            # 更新UI
            self.update_data_info()
            self.update_column_selectors()

            self.progress_bar.setValue(100)
            self.set_status(f"成功加载文件: {Path(filepath).name}")

            QTimer.singleShot(2000, lambda: self.progress_bar.setVisible(False))

        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "加载失败", f"无法加载文件:\n{str(e)}")
            self.set_status("加载失败")

    def export_data(self):
        """导出数据"""
        if self.current_df is None or self.current_df.empty:
            QMessageBox.warning(self, "警告", "没有可导出的数据")
            return

        file_path, file_filter = QFileDialog.getSaveFileName(
            self,
            "导出数据",
            "",
            "CSV文件 (*.csv);;"
            "Excel文件 (*.xlsx);;"
            "JSON文件 (*.json)"
        )

        if not file_path:
            return

        try:
            self.set_status("正在导出数据...")

            if "csv" in file_filter.lower():
                self.current_df.to_csv(file_path, index=False, encoding='utf-8-sig')
            elif "xlsx" in file_filter.lower():
                self.current_df.to_excel(file_path, index=False, engine='openpyxl')
            elif "json" in file_filter.lower():
                self.current_df.to_json(file_path, orient='records', force_ascii=False, indent=2)

            self.set_status(f"数据已导出: {Path(file_path).name}")
            QMessageBox.information(self, "成功", "数据导出成功！")

        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"无法导出数据:\n{str(e)}")
            self.set_status("导出失败")

    def export_report(self):
        """导出分析报告"""
        if self.current_df is None or self.current_df.empty:
            QMessageBox.warning(self, "警告", "没有数据可以生成报告")
            return

        file_path, file_filter = QFileDialog.getSaveFileName(
            self,
            "导出报告",
            "",
            "HTML报告 (*.html);;"
            "Markdown报告 (*.md)"
        )

        if not file_path:
            return

        try:
            self.set_status("正在生成报告...")

            report_content = self.generate_report_content()

            if "html" in file_filter.lower():
                html_content = self.convert_to_html_report(report_content)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)

            self.set_status(f"报告已生成: {Path(file_path).name}")
            QMessageBox.information(self, "成功", "报告生成成功！")

        except Exception as e:
            QMessageBox.critical(self, "生成失败", f"无法生成报告:\n{str(e)}")
            self.set_status("生成失败")

    def generate_report_content(self) -> str:
        """生成报告内容"""
        stats = self.importer.get_basic_stats(self.current_df)

        report = f"""# {AppConfig.APP_NAME} 数据分析报告  

        生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  

        ---  

        ## 数据概览  

        - **总行数**: {stats.get('rows', 0):,}  
        - **总列数**: {stats.get('columns', 0)}  
        - **数值列**: {stats.get('numeric_columns', 0)}  
        - **分类列**: {stats.get('categorical_columns', 0)}  
        - **日期时间列**: {stats.get('datetime_columns', 0)}  
        - **缺失值总数**: {stats.get('total_nulls', 0):,}  
        - **内存占用**: {stats.get('memory_usage', 0):.2f} MB  

        ---  

        ## 列详细信息  

        | 列名 | 数据类型 | 缺失值 | 唯一值 | 示例 |  
        |------|----------|--------|--------|------|  
        """

        for col, info in stats.get('column_info', {}).items():
            report += f"| {col} | {info['dtype']} | {info['nulls']} | {info['unique']} | {info['sample']} |\n"

        report += "\n---\n\n## 数值列统计摘要\n\n"

        numeric_cols = self.current_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            desc = self.current_df[numeric_cols].describe()
            report += desc.to_markdown()

        report += f"\n\n---\n\n*报告由 {AppConfig.APP_NAME} {AppConfig.APP_VERSION} 生成*"

        return report

    def convert_to_html_report(self, markdown_content: str) -> str:
        """将Markdown转换为HTML报告"""
        html_template = f"""<!DOCTYPE html>  
        <html lang="zh-CN">  
        <head>  
            <meta charset="UTF-8">  
            <meta name="viewport" content="width=device-width, initial-scale=1.0">  
            <title>{AppConfig.APP_NAME} 分析报告</title>  
            <style>  
                body {{  
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;  
                    max-width: 1200px;  
                    margin: 0 auto;  
                    padding: 40px 20px;  
                    background: #f5f5f5;  
                    line-height: 1.6;  
                }}  
                .container {{  
                    background: white;  
                    padding: 40px;  
                    border-radius: 8px;  
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);  
                }}  
                h1 {{  
                    color: #1976D2;  
                    border-bottom: 3px solid #1976D2;  
                    padding-bottom: 10px;  
                }}  
                h2 {{  
                    color: #424242;  
                    margin-top: 30px;  
                    border-left: 4px solid #1976D2;  
                    padding-left: 10px;  
                }}  
                table {{  
                    width: 100%;  
                    border-collapse: collapse;  
                    margin: 20px 0;  
                    font-size: 14px;  
                }}  
                th, td {{  
                    padding: 12px;  
                    text-align: left;  
                    border-bottom: 1px solid #ddd;  
                }}  
                th {{  
                    background-color: #1976D2;  
                    color: white;  
                    font-weight: bold;  
                }}  
                tr:hover {{  
                    background-color: #f5f5f5;  
                }}  
                ul {{  
                    list-style-type: none;  
                    padding-left: 0;  
                }}  
                ul li {{  
                    padding: 8px 0;  
                    border-bottom: 1px solid #eee;  
                }}  
                ul li strong {{  
                    color: #1976D2;  
                    display: inline-block;  
                    min-width: 150px;  
                }}  
                hr {{  
                    border: none;  
                    border-top: 2px solid #e0e0e0;  
                    margin: 30px 0;  
                }}  
                .footer {{  
                    margin-top: 40px;  
                    text-align: center;  
                    color: #999;  
                    font-size: 12px;  
                }}  
            </style>  
        </head>  
        <body>  
            <div class="container">  
                <pre style="white-space: pre-wrap;">{markdown_content}</pre>  
            </div>  
        </body>  
        </html>"""
        return html_template

        # ===============================
        # 数据操作
        # ===============================

    def refresh_data(self):
        """刷新数据显示"""
        if self.current_df is not None:
            self.table_model.update_dataframe(
                self.current_df.head(AppConfig.MAX_PREVIEW_ROWS)
            )
            self.update_data_info()
            self.set_status("数据已刷新")

    def update_data_info(self):
        """更新数据信息显示"""
        if self.current_df is None:
            return

        stats = self.importer.get_basic_stats(self.current_df)

        info_html = f"""  
                <div style='padding: 10px;'>  
                    <h3 style='color: #1976D2; margin-top: 0;'>📊 数据集信息</h3>  
                    <table style='width: 100%; font-size: 12px;'>  
                        <tr><td><b>行数:</b></td><td>{stats['rows']:,}</td></tr>  
                        <tr><td><b>列数:</b></td><td>{stats['columns']}</td></tr>  
                        <tr><td><b>数值列:</b></td><td>{stats['numeric_columns']}</td></tr>  
                        <tr><td><b>分类列:</b></td><td>{stats['categorical_columns']}</td></tr>  
                        <tr><td><b>缺失值:</b></td><td>{stats['total_nulls']:,}</td></tr>  
                        <tr><td><b>内存:</b></td><td>{stats['memory_usage']:.2f} MB</td></tr>  
                    </table>  
                </div>  
                """

        self.data_info_label.setText(info_html)
        self.data_info_label.setTextFormat(Qt.RichText)

    def update_column_selectors(self):
        """更新所有列选择器"""
        if self.current_df is None:
            return

        columns = ['(无)'] + list(self.current_df.columns)

        # 更新图表配置选择器
        self.x_combo.clear()
        self.x_combo.addItems(columns)

        self.y_list.clear()
        self.y_list.addItems(self.current_df.columns.tolist())

        self.hue_combo.clear()
        self.hue_combo.addItems(columns)

        self.size_combo.clear()
        self.size_combo.addItems(columns)

        # 更新数据清洗选择器
        self.missing_columns_list.clear()
        self.missing_columns_list.addItems(self.current_df.columns.tolist())

        self.outlier_column_combo.clear()
        self.outlier_column_combo.addItems(self.current_df.columns.tolist())

        self.transform_column_combo.clear()
        self.transform_column_combo.addItems(self.current_df.columns.tolist())

        # 更新统计分析选择器
        self.stats_column_combo.clear()
        self.stats_column_combo.addItems(self.current_df.columns.tolist())

    def add_to_history(self, df: pd.DataFrame):
        """添加到操作历史"""
        self.history_index += 1
        self.operation_history = self.operation_history[:self.history_index]
        self.operation_history.append(df.copy())

        # 限制历史记录数量
        if len(self.operation_history) > 50:
            self.operation_history.pop(0)
            self.history_index -= 1

    def undo_operation(self):
        """撤销操作"""
        if self.history_index > 0:
            self.history_index -= 1
            self.current_df = self.operation_history[self.history_index].copy()
            self.table_model.update_dataframe(
                self.current_df.head(AppConfig.MAX_PREVIEW_ROWS)
            )
            self.update_data_info()
            self.set_status("已撤销操作")
        else:
            QMessageBox.information(self, "提示", "没有可撤销的操作")

    def redo_operation(self):
        """重做操作"""
        if self.history_index < len(self.operation_history) - 1:
            self.history_index += 1
            self.current_df = self.operation_history[self.history_index].copy()
            self.table_model.update_dataframe(
                self.current_df.head(AppConfig.MAX_PREVIEW_ROWS)
            )
            self.update_data_info()
            self.set_status("已重做操作")
        else:
            QMessageBox.information(self, "提示", "没有可重做的操作")

    def copy_selection(self):
        """复制选中的单元格"""
        selection = self.table_view.selectedIndexes()
        if not selection:
            return

        rows = sorted(set(index.row() for index in selection))
        columns = sorted(set(index.column() for index in selection))

        text = ""
        for row in rows:
            row_data = []
            for col in columns:
                index = self.table_model.index(row, col)
                row_data.append(str(self.table_model.data(index)))
            text += "\t".join(row_data) + "\n"

        QApplication.clipboard().setText(text)
        self.set_status(f"已复制 {len(rows)} 行 × {len(columns)} 列")

        # ===============================
        # 数据清洗
        # ===============================

    def handle_missing_values(self):
        """处理缺失值"""
        if self.current_df is None:
            QMessageBox.warning(self, "警告", "请先加载数据")
            return

        method_map = {
            "删除缺失行": "drop",
            "均值填充": "fill_mean",
            "中位数填充": "fill_median",
            "众数填充": "fill_mode",
            "向前填充": "fill_forward",
            "向后填充": "fill_backward",
            "插值填充": "interpolate",
            "自定义值填充": "fill_value"
        }

        method = method_map[self.missing_method_combo.currentText()]
        selected_items = self.missing_columns_list.selectedItems()
        columns = [item.text() for item in selected_items] if selected_items else None

        value = None
        if method == "fill_value":
            value_text = self.missing_value_input.text().strip()
            if not value_text:
                QMessageBox.warning(self, "警告", "请输入填充值")
                return
            value = value_text

        try:
            df_cleaned = self.cleaner.handle_missing(
                self.current_df, method=method, columns=columns, value=value
            )

            self.current_df = df_cleaned
            self.add_to_history(df_cleaned)
            self.table_model.update_dataframe(
                df_cleaned.head(AppConfig.MAX_PREVIEW_ROWS)
            )
            self.update_data_info()

            self.set_status("缺失值处理完成")
            QMessageBox.information(self, "成功", "缺失值处理完成！")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理失败:\n{str(e)}")

    def handle_duplicates(self):
        """处理重复值"""
        if self.current_df is None:
            QMessageBox.warning(self, "警告", "请先加载数据")
            return

        keep_map = {
            "保留第一个": "first",
            "保留最后一个": "last",
            "全部删除": False
        }

        keep = keep_map[self.duplicate_keep_combo.currentText()]

        try:
            original_rows = len(self.current_df)
            df_cleaned = self.cleaner.handle_duplicates(self.current_df, keep=keep)
            removed_rows = original_rows - len(df_cleaned)

            self.current_df = df_cleaned
            self.add_to_history(df_cleaned)
            self.table_model.update_dataframe(
                df_cleaned.head(AppConfig.MAX_PREVIEW_ROWS)
            )
            self.update_data_info()

            self.set_status(f"已删除 {removed_rows} 个重复行")
            QMessageBox.information(self, "成功", f"已删除 {removed_rows} 个重复行！")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理失败:\n{str(e)}")

    def handle_outliers(self):
        """处理异常值"""
        if self.current_df is None:
            QMessageBox.warning(self, "警告", "请先加载数据")
            return

        column = self.outlier_column_combo.currentText()
        if not column:
            QMessageBox.warning(self, "警告", "请选择列")
            return

        method_map = {
            "IQR方法": "iqr",
            "Z-Score方法": "zscore",
            "截断(Clip)": "clip"
        }

        method = method_map[self.outlier_method_combo.currentText()]
        threshold = self.outlier_threshold_spin.value()

        try:
            original_rows = len(self.current_df)
            df_cleaned = self.cleaner.handle_outliers(
                self.current_df, column=column, method=method, threshold=threshold
            )
            removed_rows = original_rows - len(df_cleaned)

            self.current_df = df_cleaned
            self.add_to_history(df_cleaned)
            self.table_model.update_dataframe(
                df_cleaned.head(AppConfig.MAX_PREVIEW_ROWS)
            )
            self.update_data_info()

            if method == "clip":
                self.set_status(f"列 '{column}' 的异常值已截断")
                QMessageBox.information(self, "成功", f"列 '{column}' 的异常值已截断！")
            else:
                self.set_status(f"已删除 {removed_rows} 个异常值")
                QMessageBox.information(self, "成功", f"已删除 {removed_rows} 个异常值！")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理失败:\n{str(e)}")

    def transform_column_type(self):
        """转换列类型"""
        if self.current_df is None:
            QMessageBox.warning(self, "警告", "请先加载数据")
            return

        column = self.transform_column_combo.currentText()
        if not column:
            QMessageBox.warning(self, "警告", "请选择列")
            return

        method_map = {
            "转换为数值": "to_numeric",
            "转换为日期时间": "to_datetime",
            "转换为字符串": "to_string",
            "转换为类别": "to_category"
        }

        method = method_map[self.transform_method_combo.currentText()]

        try:
            df_transformed, failed_indices = self.cleaner.transform_column(
                self.current_df, column=column, method=method
            )

            if failed_indices:
                QMessageBox.warning(
                    self,
                    "转换警告",
                    f"有 {len(failed_indices)} 个值转换失败，已设置为NaN"
                )

            self.current_df = df_transformed
            self.add_to_history(df_transformed)
            self.table_model.update_dataframe(
                df_transformed.head(AppConfig.MAX_PREVIEW_ROWS)
            )
            self.update_data_info()
            self.update_column_selectors()

            self.set_status(f"列 '{column}' 已转换")
            QMessageBox.information(self, "成功", f"列 '{column}' 类型转换完成！")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"转换失败:\n{str(e)}")

            # ===============================
        # 统计分析
        # ===============================

    def show_descriptive_stats(self):
        """显示描述性统计"""
        if self.current_df is None:
            QMessageBox.warning(self, "警告", "请先加载数据")
            return

        column = self.stats_column_combo.currentText()
        if not column:
            QMessageBox.warning(self, "警告", "请选择列")
            return

        try:
            stats = self.analyzer.descriptive_stats(self.current_df, column)

            if not stats:
                QMessageBox.information(self, "提示", "无法计算统计信息")
                return

            stats_text = f"列 '{column}' 的描述性统计:\n\n"
            for key, value in stats.items():
                if key != '频数分布':
                    stats_text += f"{key}: {value}\n"
                else:
                    stats_text += f"\n{key}:\n"
                    for k, v in value.items():
                        stats_text += f"  {k}: {v}\n"

            self.stats_text.setText(stats_text)
            self.set_status(f"已计算列 '{column}' 的统计信息")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"统计分析失败:\n{str(e)}")

    def show_correlation_analysis(self):
        """显示相关性分析"""
        if self.current_df is None:
            QMessageBox.warning(self, "警告", "请先加载数据")
            return

        numeric_df = self.current_df.select_dtypes(include=[np.number])
        if numeric_df.empty or len(numeric_df.columns) < 2:
            QMessageBox.warning(self, "警告", "需要至少两个数值列进行相关性分析")
            return

        method_map = {
            "Pearson": "pearson",
            "Spearman": "spearman",
            "Kendall": "kendall"
        }

        method = method_map[self.corr_method_combo.currentText()]

        try:
            corr_matrix = self.analyzer.correlation_analysis(self.current_df, method=method)

            # 创建热力图
            config = {
                'chart_type': 'heatmap',
                'title': f'相关性矩阵 ({method.capitalize()})',
                'correlation': True,
                'figsize': (10, 8)
            }

            fig = self.chart_renderer.create_chart(self.current_df, config)
            self.add_chart_to_tab(fig, f"相关性分析-{method}")

            self.set_status("相关性分析完成")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"相关性分析失败:\n{str(e)}")

    def show_stats_dialog(self):
        """显示统计分析对话框"""
        if self.current_df is None:
            QMessageBox.warning(self, "警告", "请先加载数据")
            return

        self.tab_widget.setCurrentIndex(2)  # 切换到统计分析标签

        # ===============================
        # 图表生成
        # ===============================

    def on_chart_type_changed(self):
        """图表类型改变时的处理"""
        chart_type = self.chart_type_combo.currentData()

        # 根据图表类型调整控件可见性
        if chart_type in ['pie', 'funnel', 'treemap']:
            self.y_list.setSelectionMode(QListWidget.SingleSelection)
        else:
            self.y_list.setSelectionMode(QListWidget.MultiSelection)

    def get_chart_config(self) -> Dict[str, Any]:
        """获取当前图表配置"""
        config = {
            'chart_type': self.chart_type_combo.currentData(),
            'x': self.x_combo.currentText() if self.x_combo.currentText() != '(无)' else None,
            'y': [item.text() for item in self.y_list.selectedItems()],
            'hue': self.hue_combo.currentText() if self.hue_combo.currentText() != '(无)' else None,
            'size': self.size_combo.currentText() if self.size_combo.currentText() != '(无)' else None,
            'title': self.title_input.text() or None,
            'xlabel': self.xlabel_input.text() or None,
            'ylabel': self.ylabel_input.text() or None,
            'grid': self.grid_check.isChecked(),
            'legend': self.legend_check.isChecked(),
            'figsize': (self.figsize_width.value(), self.figsize_height.value()),
            'dpi': self.dpi_spin.value()
        }

        return config

    def generate_chart(self):
        """生成图表"""
        if self.current_df is None or self.current_df.empty:
            QMessageBox.warning(self, "警告", "请先加载数据")
            return

        config = self.get_chart_config()

        # 验证配置
        if not config['x'] and config['chart_type'] not in ['heatmap']:
            QMessageBox.warning(self, "警告", "请选择X轴数据")
            return

        if not config['y'] and config['chart_type'] not in ['heatmap']:
            QMessageBox.warning(self, "警告", "请选择Y轴数据")
            return

        try:
            self.set_status("正在生成图表...")

            # 数据采样（如果数据量过大）
            plot_df = self.current_df
            if len(plot_df) > AppConfig.MAX_PLOT_ROWS:
                if len(plot_df) > AppConfig.SAMPLE_PLOT_ROWS:
                    plot_df = plot_df.sample(AppConfig.SAMPLE_PLOT_ROWS)
                    QMessageBox.information(
                        self,
                        "数据采样",
                        f"数据量较大，已随机采样 {AppConfig.SAMPLE_PLOT_ROWS} 行进行绘图"
                    )

            # 创建图表
            fig = self.chart_renderer.create_chart(plot_df, config)

            # 添加到标签页
            chart_name = f"{self.chart_type_combo.currentText()}-{datetime.now().strftime('%H:%M:%S')}"
            self.add_chart_to_tab(fig, chart_name)

            self.set_status("图表生成完成")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"图表生成失败:\n{str(e)}")
            self.set_status("图表生成失败")

    def generate_interactive_chart(self):
        """生成交互式图表"""
        if not HAS_PLOTLY or not HAS_WEBENGINE:
            QMessageBox.warning(
                self,
                "功能不可用",
                "交互式图表需要安装 plotly 和 PyQtWebEngine\n\n"
                "请运行: pip install plotly PyQtWebEngine"
            )
            return

        if self.current_df is None or self.current_df.empty:
            QMessageBox.warning(self, "警告", "请先加载数据")
            return

        config = self.get_chart_config()

        # 验证配置
        if not config['x'] and config['chart_type'] not in ['heatmap']:
            QMessageBox.warning(self, "警告", "请选择X轴数据")
            return

        if not config['y'] and config['chart_type'] not in ['heatmap']:
            QMessageBox.warning(self, "警告", "请选择Y轴数据")
            return

        try:
            self.set_status("正在生成交互式图表...")

            # 数据采样
            plot_df = self.current_df
            if len(plot_df) > AppConfig.SAMPLE_PLOT_ROWS:
                plot_df = plot_df.sample(AppConfig.SAMPLE_PLOT_ROWS)

            # 创建交互式图表
            html_content = self.interactive_renderer.create_interactive_chart(plot_df, config)

            if html_content:
                # 添加到标签页
                chart_name = f"交互-{self.chart_type_combo.currentText()}-{datetime.now().strftime('%H:%M:%S')}"
                self.add_interactive_chart_to_tab(html_content, chart_name)
                self.set_status("交互式图表生成完成")
            else:
                QMessageBox.warning(self, "警告", "该图表类型暂不支持交互式渲染")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"交互式图表生成失败:\n{str(e)}")
            self.set_status("图表生成失败")

    def add_chart_to_tab(self, fig: Figure, name: str):
        """添加图表到标签页"""
        chart_widget = QWidget()
        layout = QVBoxLayout(chart_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建画布
        canvas = FigureCanvas(fig)
        toolbar = NavigationToolbar(canvas, chart_widget)

        layout.addWidget(toolbar)
        layout.addWidget(canvas)

        # 添加标签页
        index = self.chart_tab_widget.addTab(chart_widget, name)
        self.chart_tab_widget.setCurrentIndex(index)

    def add_interactive_chart_to_tab(self, html_content: str, name: str):
        """添加交互式图表到标签页"""
        if not HAS_WEBENGINE:
            return

        chart_widget = QWidget()
        layout = QVBoxLayout(chart_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建Web视图
        web_view = QWebEngineView()
        web_view.setHtml(html_content)

        layout.addWidget(web_view)

        # 添加标签页
        index = self.chart_tab_widget.addTab(chart_widget, name)
        self.chart_tab_widget.setCurrentIndex(index)

    def close_chart_tab(self, index: int):
        """关闭图表标签页"""
        self.chart_tab_widget.removeTab(index)

    def save_chart(self):
        """保存当前图表"""
        current_widget = self.chart_tab_widget.currentWidget()
        if not current_widget:
            QMessageBox.warning(self, "警告", "没有可保存的图表")
            return

        file_path, file_filter = QFileDialog.getSaveFileName(
            self,
            "保存图表",
            "",
            "PNG图片 (*.png);;"
            "JPEG图片 (*.jpg);;"
            "PDF文件 (*.pdf);;"
            "SVG文件 (*.svg);;"
            "HTML文件 (*.html)"
        )

        if not file_path:
            return

        try:
            # 查找FigureCanvas
            canvas = None
            web_view = None

            for child in current_widget.findChildren(FigureCanvas):
                canvas = child
                break

            if not canvas:
                for child in current_widget.findChildren(QWebEngineView):
                    web_view = child
                    break

            if canvas:
                # 保存matplotlib图表
                canvas.figure.savefig(file_path, dpi=300, bbox_inches='tight')
                self.set_status(f"图表已保存: {Path(file_path).name}")
                QMessageBox.information(self, "成功", "图表保存成功！")

            elif web_view and "html" in file_filter.lower():
                # 保存HTML
                html_content = web_view.page().toHtml(lambda html: self._save_html(html, file_path))

            else:
                QMessageBox.warning(self, "警告", "无法保存此类型的图表")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")

    def _save_html(self, html: str, filepath: str):
        """保存HTML内容"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
            self.set_status(f"图表已保存: {Path(filepath).name}")
            QMessageBox.information(self, "成功", "图表保存成功！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")

        # ===============================
        # 对话框
        # ===============================

    def show_filter_dialog(self):
        """显示数据筛选对话框"""
        if self.current_df is None:
            QMessageBox.warning(self, "警告", "请先加载数据")
            return

        dialog = QInputDialog(self)
        dialog.setWindowTitle("数据筛选")
        dialog.setLabelText("输入筛选条件 (Pandas查询语法):\n例: Age > 30 and City == 'Beijing'")
        dialog.setTextValue("")
        dialog.resize(500, 200)

        if dialog.exec_() == QInputDialog.Accepted:
            query = dialog.textValue().strip()
            if query:
                try:
                    df_filtered = self.current_df.query(query)
                    self.current_df = df_filtered
                    self.add_to_history(df_filtered)
                    self.table_model.update_dataframe(
                        df_filtered.head(AppConfig.MAX_PREVIEW_ROWS)
                    )
                    self.update_data_info()
                    self.set_status(f"筛选后保留 {len(df_filtered)} 行")
                    QMessageBox.information(self, "成功", f"筛选完成！保留 {len(df_filtered)} 行")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"筛选失败:\n{str(e)}")

    def show_sort_dialog(self):
        """显示排序对话框"""
        if self.current_df is None:
            QMessageBox.warning(self, "警告", "请先加载数据")
            return

        column, ok = QInputDialog.getItem(
            self,
            "数据排序",
            "选择排序列:",
            self.current_df.columns.tolist(),
            0,
            False
        )

        if ok and column:
            ascending, ok = QInputDialog.getItem(
                self,
                "排序方式",
                "选择排序方式:",
                ["升序", "降序"],
                0,
                False
            )

            if ok:
                try:
                    df_sorted = self.current_df.sort_values(
                        by=column,
                        ascending=(ascending == "升序")
                    )
                    self.current_df = df_sorted
                    self.add_to_history(df_sorted)
                    self.table_model.update_dataframe(
                        df_sorted.head(AppConfig.MAX_PREVIEW_ROWS)
                    )
                    self.set_status(f"已按 '{column}' 列{ascending}排序")
                    QMessageBox.information(self, "成功", "排序完成！")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"排序失败:\n{str(e)}")

    def show_templates_dialog(self):
        """显示分析模板对话框"""
        if self.current_df is None:
            QMessageBox.warning(self, "警告", "请先加载数据")
            return

        templates = [
            "基础数据探索",
            "销售分析报告",
            "用户行为分析",
            "问卷调查分析",
            "时间序列分析"
        ]

        template, ok = QInputDialog.getItem(
            self,
            "分析模板",
            "选择分析模板:",
            templates,
            0,
            False
        )

        if ok and template:
            self.apply_template(template)

    def apply_template(self, template_name: str):
        """应用分析模板"""
        try:
            if template_name == "基础数据探索":
                self._apply_basic_exploration_template()
            elif template_name == "销售分析报告":
                self._apply_sales_analysis_template()
            elif template_name == "用户行为分析":
                self._apply_user_behavior_template()
            elif template_name == "问卷调查分析":
                self._apply_survey_analysis_template()
            elif template_name == "时间序列分析":
                self._apply_timeseries_template()

            self.set_status(f"已应用模板: {template_name}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"应用模板失败:\n{str(e)}")

    def _apply_basic_exploration_template(self):
        """应用基础数据探索模板"""
        numeric_cols = self.current_df.select_dtypes(include=[np.number]).columns.tolist()

        if len(numeric_cols) >= 1:
            # 生成直方图
            for col in numeric_cols[:3]:  # 最多3列
                config = {
                    'chart_type': 'histogram',
                    'y': [col],
                    'title': f'{col} 分布图',
                    'bins': 30
                }
                fig = self.chart_renderer.create_chart(self.current_df, config)
                self.add_chart_to_tab(fig, f"{col}-分布")

        if len(numeric_cols) >= 2:
            # 生成相关性热力图
            config = {
                'chart_type': 'heatmap',
                'title': '相关性矩阵',
                'correlation': True
            }
            fig = self.chart_renderer.create_chart(self.current_df, config)
            self.add_chart_to_tab(fig, "相关性分析")

        QMessageBox.information(self, "完成", "基础数据探索图表已生成！")

    def _apply_sales_analysis_template(self):
        """应用销售分析模板"""
        QMessageBox.information(self, "提示", "请根据您的数据结构自定义此模板")

    def _apply_user_behavior_template(self):
        """应用用户行为分析模板"""
        QMessageBox.information(self, "提示", "请根据您的数据结构自定义此模板")

    def _apply_survey_analysis_template(self):
        """应用问卷调查分析模板"""
        categorical_cols = self.current_df.select_dtypes(
            include=['object', 'category']
        ).columns.tolist()

        if len(categorical_cols) >= 1:
            for col in categorical_cols[:3]:
                value_counts = self.current_df[col].value_counts()
                if len(value_counts) <= 10:  # 只对类别较少的列生成饼图
                    df_pie = pd.DataFrame({
                        'category': value_counts.index,
                        'count': value_counts.values
                    })

                    config = {
                        'chart_type': 'pie',
                        'x': 'category',
                        'y': ['count'],
                        'title': f'{col} 分布'
                    }
                    fig = self.chart_renderer.create_chart(df_pie, config)
                    self.add_chart_to_tab(fig, f"{col}-分布")

        QMessageBox.information(self, "完成", "问卷分析图表已生成！")

    def _apply_timeseries_template(self):
        """应用时间序列分析模板"""
        datetime_cols = self.current_df.select_dtypes(include=['datetime64']).columns.tolist()

        if not datetime_cols:
            QMessageBox.warning(self, "警告", "数据中没有日期时间列")
            return

        numeric_cols = self.current_df.select_dtypes(include=[np.number]).columns.tolist()

        if datetime_cols and numeric_cols:
            config = {
                'chart_type': 'line',
                'x': datetime_cols[0],
                'y': numeric_cols[:2],
                'title': '时间序列趋势图'
            }
            fig = self.chart_renderer.create_chart(self.current_df, config)
            self.add_chart_to_tab(fig, "时间序列")

        QMessageBox.information(self, "完成", "时间序列分析图表已生成！")

    def show_batch_dialog(self):
        """显示批量处理对话框"""
        QMessageBox.information(
            self,
            "批量处理",
            "批量处理功能开发中...\n\n"
            "将支持:\n"
            "• 批量导入文件\n"
            "• 批量应用清洗规则\n"
            "• 批量生成图表\n"
            "• 批量导出报告"
        )

    def show_documentation(self):
        """显示文档"""
        doc_text = f"""
            # {AppConfig.APP_NAME} 使用文档

            ## 快速开始

            ### 1. 导入数据
            - 点击 **文件 → 打开文件** 或工具栏的 📁 按钮
            - 支持格式: CSV, Excel, JSON, XML, TXT

            ### 2. 数据清洗
            - 切换到 **数据清洗** 标签页
            - 处理缺失值、重复值、异常值
            - 转换数据类型

            ### 3. 统计分析
            - 切换到 **统计分析** 标签页
            - 查看描述性统计
            - 生成相关性矩阵

            ### 4. 图表可视化
            - 切换到 **图表配置** 标签页
            - 选择图表类型和数据映射
            - 点击 **生成图表** 按钮

            ### 5. 导出结果
            - **文件 → 保存数据**: 导出清洗后的数据
            - **文件 → 导出报告**: 生成分析报告
            - 右键图表可保存图片

            ## 支持的图表类型

            - 📈 折线图
            - 📊 柱状图
            - 🥧 饼图
            - ⚫ 散点图
            - 📉 面积图
            - 🔥 热力图
            - 📦 箱线图
            - 🎻 小提琴图
            - 📊 直方图
            - 🌊 密度图
            - 🎯 雷达图
            - 🔻 漏斗图
            - 🌳 树状图
            - 💧 瀑布图

            ## 快捷键

            - **Ctrl+O**: 打开文件
            - **Ctrl+S**: 保存数据
            - **Ctrl+Z**: 撤销操作
            - **Ctrl+Y**: 重做操作
            - **Ctrl+C**: 复制选中单元格
            - **F5**: 刷新数据
            - **F11**: 全屏切换

            ## 技术支持

            如有问题，请联系: support@datavizpro.com

            版本: {AppConfig.APP_VERSION}
                    """

        dialog = QDialog(self)
        dialog.setWindowTitle("使用文档")
        dialog.resize(700, 600)

        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(doc_text)
        text_edit.setStyleSheet("font-family: monospace;")

        layout.addWidget(text_edit)

        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(dialog.close)
        layout.addWidget(btn_close)

        dialog.exec_()

    def show_about_dialog(self):
        """显示关于对话框"""
        about_text = f"""
            <div style='text-align: center;'>
                <h1>{AppConfig.APP_NAME}</h1>
                <h3>版本 {AppConfig.APP_VERSION}</h3>
                <p>专业的数据分析与可视化平台</p>
                <hr>
                <p>
                    <b>作者:</b> {AppConfig.APP_AUTHOR}<br>
                    <b>技术栈:</b> Python, PyQt5, Pandas, Matplotlib, Plotly<br>
                    <b>许可证:</b> MIT License
                </p>
                <hr>
                <p style='color: #666; font-size: 12px;'>
                    © 2025 DataVizPro Team. All rights reserved.
                </p>
            </div>
                    """

        QMessageBox.about(self, "关于", about_text)

        # ===============================
        # 主题和样式
        # ===============================

    def apply_theme(self, theme_name: str):
        """应用主题"""
        if theme_name not in AppConfig.THEMES:
            return

        self.current_theme = theme_name
        theme = AppConfig.THEMES[theme_name]

        # 生成样式表
        stylesheet = f"""
                    QMainWindow {{
                        background-color: {theme['background']};
                    }}

                    QWidget {{
                        background-color: {theme['background']};
                        color: {theme['text']};
                    }}

                    QGroupBox {{
                        font-weight: bold;
                        border: 2px solid {theme['primary']};
                        border-radius: 5px;
                        margin-top: 10px;
                        padding-top: 10px;
                    }}

                    QGroupBox::title {{
                        color: {theme['primary']};
                        subcontrol-origin: margin;
                        left: 10px;
                        padding: 0 5px;
                    }}

                    QPushButton {{
                        background-color: {theme['primary']};
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        font-weight: bold;
                    }}

                    QPushButton:hover {{
                        background-color: {theme['secondary']};
                    }}

                    QPushButton:pressed {{
                        background-color: {theme['accent']};
                    }}

                    QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox {{
                        padding: 5px;
                        border: 1px solid {theme['secondary']};
                        border-radius: 3px;
                        background-color: {theme['surface']};
                    }}

                    QTableView {{
                        gridline-color: {theme['secondary']};
                        selection-background-color: {theme['primary']};
                        alternate-background-color: {theme['surface']};
                    }}

                    QHeaderView::section {{
                        background-color: {theme['primary']};
                        color: white;
                        padding: 5px;
                        border: none;
                        font-weight: bold;
                    }}

                    QTabWidget::pane {{
                        border: 1px solid {theme['secondary']};
                        border-radius: 3px;
                    }}

                    QTabBar::tab {{
                        background-color: {theme['surface']};
                        padding: 8px 16px;
                        border: 1px solid {theme['secondary']};
                        border-bottom: none;
                        border-top-left-radius: 4px;
                        border-top-right-radius: 4px;
                    }}

                    QTabBar::tab:selected {{
                        background-color: {theme['primary']};
                        color: white;
                    }}

                    QListWidget {{
                        border: 1px solid {theme['secondary']};
                        border-radius: 3px;
                    }}

                    QTextEdit {{
                        border: 1px solid {theme['secondary']};
                        border-radius: 3px;
                        background-color: {theme['surface']};
                    }}

                    QStatusBar {{
                        background-color: {theme['surface']};
                        color: {theme['text_secondary']};
                    }}

                    QToolBar {{
                        background-color: {theme['surface']};
                        border-bottom: 1px solid {theme['secondary']};
                        spacing: 10px;
                        padding: 5px;
                    }}

                    QMenuBar {{
                        background-color: {theme['surface']};
                    }}

                    QMenuBar::item:selected {{
                        background-color: {theme['primary']};
                        color: white;
                    }}

                    QMenu {{
                        background-color: {theme['surface']};
                        border: 1px solid {theme['secondary']};
                    }}

                    QMenu::item:selected {{
                        background-color: {theme['primary']};
                        color: white;
                    }}
                    """

        self.setStyleSheet(stylesheet)
        self.set_status(f"已切换到 '{theme_name}' 主题")

        # ===============================
        # 辅助方法
        # ===============================

    def set_status(self, message: str):
        """设置状态栏消息"""
        self.status_label.setText(message)
        QApplication.processEvents()

    def toggle_fullscreen(self):
        """切换全屏模式"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def closeEvent(self, event):
        """窗口关闭事件"""
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出程序吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    # ===============================
    # 应用入口
    # ===============================


def main():
    """主函数"""
    # 初始化应用配置
    AppConfig.init_dirs()

    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName(AppConfig.APP_NAME)
    app.setApplicationVersion(AppConfig.APP_VERSION)
    app.setOrganizationName(AppConfig.APP_AUTHOR)

    # 设置应用样式
    app.setStyle(QStyleFactory.create("Fusion"))

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 运行应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
