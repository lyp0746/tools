# 专业工具集工具箱

<div align="center">

**作者：LYP** | [GitHub](https://github.com/lyp0746) | [邮箱](mailto:1610369302@qq.com)

![Python](https://img.shields.io/badge/python-3.7+-green.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-orange.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

**15个专业级Python工具集 | 提升工作效率的完整解决方案**

[项目概览](#-项目概览) • [快速开始](#-快速开始) • [安装说明](#-安装说明) • [工具详情](#-工具详情) • [贡献指南](#-贡献指南)

</div>

---

## 📋 目录

- [项目概览](#-项目概览)
- [快速开始](#-快速开始)
- [安装说明](#-安装说明)
- [工具详情](#-工具详情)
- [系统要求](#-系统要求)
- [开发工具](#-开发工具)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)
- [联系方式](#-联系方式)

---

## 🎯 项目概览

本工具箱包含15个专业级Python工具，覆盖自动化、数据分析、网络工具、系统监控等多个领域，全部基于PyQt5开发，提供现代化的图形界面。

### 工具列表

| 类别 | 工具名称 | 主要功能 | 核心依赖 |
|------|----------|----------|----------|
| 🔧 **自动化工具** | AutomationToolPro | 定时任务、文件监控、网页自动化等8大功能 | PyQt5 |
| 📊 **数据分析** | DataVizPro | 数据可视化、图表分析 | pandas, matplotlib, plotly |
| 🗄️ **数据库管理** | DatabaseManagerPro | 多数据库管理、SQL执行 | PyQt5, pymysql, psycopg2 |
| 🔍 **代码分析** | CodeAnalyzerPro | 代码质量分析、安全检测 | PyQt5, PyQtChart |
| 🌐 **网络工具** | NetworkToolPro | Ping测试、端口扫描、HTTP测试等9大功能 | PyQt5, requests |
| 📈 **系统监控** | SystemMonitorPro | 系统资源监控、进程管理 | PyQt5, psutil, PyQtChart |
| 📝 **文本处理** | TextProcessorPro | 正则表达式、编码转换、文本对比 | PyQt5 |
| 🔐 **安全工具** | SecurityVaultPro | 密码管理、加密存储 | PyQt5 |
| 💰 **金融计算** | FinancialCalculatorPro | 金融计算、投资分析 | PyQt5 |
| 🖼️ **图像处理** | ImageProcessorPro | 图像编辑、格式转换 | PyQt5, Pillow |
| 📺 **流媒体** | StreamForgeElite | 视频下载、格式转换 | yt-dlp |
| 🎬 **音视频处理** | SubMuxOmniPro | 字幕处理、音视频同步 | 标准库 |
| 📄 **文件转换** | UltimateFileConverter | 多格式文件转换 | Pillow, python-docx, pypdf等 |
| 📖 **文档阅读** | UltimateReader | 多格式文档阅读器 | PyQt5, PyMuPDF, python-docx等 |
| 🕷️ **网络爬虫** | UniversalWebCrawlerPro | 网页爬取、数据采集 | PyQt5, playwright, aiohttp |

---

## 🚀 快速开始

### 1. 环境准备

确保系统已安装：
- **Python 3.7+** (推荐3.9+)
- **pip** 包管理工具

### 2. 一键安装所有依赖

```bash
# 克隆或下载项目
cd D:\0_Code\tools

# 安装所有依赖
pip install -r requirements.txt
```

### 3. 运行工具

```bash
# 运行任意工具（以AutomationToolPro为例）
python AutomationToolPro/AutomationToolPro.py

# 或直接双击对应工具的.py文件
```

### 4. 使用虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境（Windows）
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

---

## 📦 安装说明

### 完整依赖安装

所有工具的依赖已整合到 `requirements.txt` 文件中：

```bash
pip install -r requirements.txt
```

### 按需安装

如果只需要特定工具，可以单独安装其依赖：

```bash
# 自动化工具
pip install PyQt5

# 数据分析工具
pip install pandas numpy matplotlib plotly pyecharts PyQt5

# 数据库管理工具
pip install PyQt5 pymysql psycopg2-binary pandas openpyxl

# 系统监控工具
pip install PyQt5 psutil PyQtChart

# 文件处理工具
pip install Pillow python-docx beautifulsoup4 pypdf reportlab pydub moviepy ebooklib PyYAML toml qrcode cairosvg pandas

# 网络工具
pip install PyQt5 requests

# 文档阅读器
pip install PyQt5 PyMuPDF python-docx odfpy python-pptx Pillow pytesseract markdown2

# 网络爬虫
pip install PyQt5 playwright aiohttp validators beautifulsoup4 Pillow lxml
```

### 系统级依赖

某些工具需要系统级依赖：

- **FFmpeg**: 音频/视频处理工具
- **Calibre**: 电子书转换工具  
- **Tesseract OCR**: 文字识别引擎

---

## 🔧 工具详情

### AutomationToolPro - 自动化工具集
**功能**: 定时任务、文件监控、网页自动化、宏录制、API测试、数据同步、系统监控、日志管理
**特点**: 8大功能模块集成，可视化操作界面

### DataVizPro - 数据可视化工具
**功能**: 数据导入、图表生成、统计分析、交互式可视化
**特点**: 支持多种图表类型，实时数据更新

### DatabaseManagerPro - 数据库管理工具
**功能**: 多数据库连接、SQL执行、数据导出、表结构管理
**特点**: 支持MySQL、PostgreSQL、SQLite等多种数据库

### CodeAnalyzerPro - 代码分析工具
**功能**: 代码质量分析、安全漏洞检测、复杂度评估、依赖关系分析
**特点**: 多维度分析，生成专业报告

### NetworkToolPro - 网络工具集
**功能**: Ping测试、路由跟踪、端口扫描、速度测试、HTTP测试、DNS查询、局域网扫描、Whois查询、子网计算
**特点**: 9大网络工具，多线程并发处理

### SystemMonitorPro - 系统监控工具
**功能**: 系统资源监控、进程管理、日志查看、自动化脚本
**特点**: 实时监控，可视化图表展示

### TextProcessorPro - 文本处理工具
**功能**: 正则表达式测试、编码转换、文本对比、批量替换、统计分析、Markdown编辑
**特点**: 多功能集成，操作简单

### SecurityVaultPro - 安全保险箱
**功能**: 密码管理、加密存储、安全备份
**特点**: AES加密算法，安全可靠

### FinancialCalculatorPro - 金融计算器
**功能**: 贷款计算、投资分析、汇率转换、财务规划
**特点**: 专业金融计算模型

### ImageProcessorPro - 图像处理工具
**功能**: 图像编辑、滤镜应用、格式转换、批量处理
**特点**: 支持多种图像格式

### StreamForgeElite - 流媒体下载工具
**功能**: 视频下载、格式转换、质量选择
**特点**: 支持多个流媒体平台

### SubMuxOmniPro - 音视频处理工具
**功能**: 字幕处理、音视频同步、格式转换
**特点**: 专业级音视频处理

### UltimateFileConverter - 文件格式转换工具
**功能**: 图片、音视频、文档等多格式转换、批量处理
**特点**: 支持50+文件格式

### UltimateReader - 文档阅读器
**功能**: PDF、Word、Excel、PPT、电子书等文档阅读
**特点**: 多格式支持，OCR文字识别

### UniversalWebCrawlerPro - 网络爬虫工具
**功能**: 网页爬取、数据提取、批量下载、反爬虫处理
**特点**: 可视化配置，高性能爬取

---

## 💻 系统要求

### 最低配置
- **操作系统**: Windows 7+ / Linux (Ubuntu 18.04+) / macOS 10.12+
- **Python版本**: 3.7+
- **内存**: 2GB RAM
- **磁盘空间**: 100MB

### 推荐配置
- **操作系统**: Windows 10/11 / Ubuntu 20.04+ / macOS 11+
- **Python版本**: 3.9+
- **内存**: 4GB+ RAM
- **磁盘空间**: 500MB
- **显示器**: 1920x1080分辨率

---

## 🛠️ 开发工具

工具箱包含开发辅助工具：

```bash
# 代码格式化
black .

# 代码检查
flake8 .

# 类型检查
mypy .

# 单元测试
pytest
```

---

## 🤝 贡献指南

我们欢迎任何形式的贡献！

### 代码规范
- 遵循 PEP 8 Python代码规范
- 使用有意义的变量和函数名
- 添加必要的注释和文档字符串
- 编写单元测试

### 提交代码
1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 报告问题
- 使用GitHub Issues报告bug或提出建议
- 提供详细的复现步骤和环境信息

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 📞 联系方式

- **问题反馈**: [GitHub Issues](https://github.com/lyp0746/issues)
- **功能建议**: [GitHub Discussions](https://github.com/lyp0746/discussions)
- **邮件联系**: 1610369302@qq.com

---

## 🙏 致谢

感谢以下开源项目的支持：

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - 强大的GUI框架
- [Python](https://www.python.org/) - 优秀的编程语言
- 所有贡献者和用户的支持与反馈

---

<div align="center">

**如果这个工具箱对你有帮助，请给个⭐Star支持一下！**

</div>
        