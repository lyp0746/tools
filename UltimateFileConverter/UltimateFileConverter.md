# 🚀 终极文件格式转换器 v4.0 Pro (PyQt5)

<div align="center">

**作者：LYP** | [GitHub](https://github.com/lyp0746) | [邮箱](mailto:1610369302@qq.com)

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

**一款功能强大、界面现代化的多格式文件转换工具**

支持 50+ 种文件格式 | 批量处理 | 拖拽操作 | 主题切换 | 实时预览

[快速开始](#快速开始) • [功能特性](#功能特性) • [支持格式](#支持格式) • [安装指南](#安装指南) • [使用说明](#使用说明)

</div>

---

## 📋 目录

- [功能特性](#功能特性)
- [支持格式](#支持格式)
- [系统要求](#系统要求)
- [安装指南](#安装指南)
- [使用说明](#使用说明)
- [快捷键](#快捷键)
- [依赖库](#依赖库)
- [常见问题](#常见问题)
- [更新日志](#更新日志)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## ✨ 功能特性

### 🎨 现代化界面
- ✅ **PyQt5 界面** - 告别传统 Tkinter，拥抱现代设计
- ✅ **主题切换** - 亮色/暗色模式随心切换
- ✅ **响应式布局** - 自适应窗口大小
- ✅ **Material Design** - 符合现代审美的UI风格

### 🚀 强大功能
- ✅ **拖拽支持** - 直接拖拽文件到窗口即可添加
- ✅ **批量转换** - 一次处理多个文件
- ✅ **实时预览** - 图片、文本文件即时预览
- ✅ **进度显示** - 实时转换进度和详细日志
- ✅ **质量控制** - 可调节输出质量（1-100）
- ✅ **历史记录** - 记录每次转换的详细信息

### 🔧 用户体验
- ✅ **多线程处理** - 转换时界面不卡顿
- ✅ **配置保存** - 自动保存用户偏好设置
- ✅ **错误提示** - 详细的错误信息和解决建议
- ✅ **文件信息** - 显示文件大小、MD5等详细信息
- ✅ **快捷键** - 支持常用快捷键操作

---

## 📦 支持格式

### 🖼️ 图片格式 (10种)
```
PNG ⟷ JPG ⟷ BMP ⟷ GIF ⟷ WEBP ⟷ ICO ⟷ TIFF ⟷ SVG ⟷ PDF
```
**特性：**
- 支持透明通道处理
- EXIF方向自动校正
- SVG矢量图转换（需cairosvg）
- 批量生成缩略图

### 📄 文档格式 (7种)
```
TXT ⟷ MD ⟷ HTML ⟷ DOCX ⟷ PDF ⟷ RTF ⟷ ODT
```
**特性：**
- 保留文本格式
- 支持中文字体
- HTML样式优化
- PDF多页处理

### 📊 数据格式 (7种)
```
CSV ⟷ XLSX ⟷ JSON ⟷ XML ⟷ YAML ⟷ PARQUET ⟷ TSV
```
**特性：**
- 自动识别编码
- 保留数据结构
- 支持大文件处理
- Excel多sheet支持

### 🎵 音频格式 (6种)
```
MP3 ⟷ WAV ⟷ OGG ⟷ FLAC ⟷ M4A ⟷ AAC
```
**特性：**
- 比特率可调
- 无损/有损转换
- 批量处理
- 质量优化

### 🎬 视频格式 (9种)
```
MP4 ⟷ AVI ⟷ MKV ⟷ MOV ⟷ FLV ⟷ WMV ⟷ WEBM ⟷ M4V ⟷ GIF
```
**特性：**
- 视频转GIF
- 编码器自动选择
- 比特率优化
- 音频流保留

### 📦 压缩格式 (4种)
```
ZIP ⟷ TAR ⟷ TAR.GZ ⟷ TAR.BZ2
```
**特性：**
- 压缩等级可调
- 保留目录结构
- 批量压缩/解压

### 📚 电子书格式 (6种)
```
EPUB ⟷ MOBI ⟷ AZW3 ⟷ TXT ⟷ HTML ⟷ PDF
```
**特性：**
- 元数据保留
- 目录结构保持
- Calibre增强支持

### 🔐 编码转换 (4种)
```
Base64 | Hex | MD5 | SHA256
```
**特性：**
- 文件哈希计算
- 编码/解码
- 批量处理

### 🎨 特殊功能 (3种)
```
二维码生成 | 缩略图生成 | 水印添加
```
**特性：**
- 文本转二维码
- 批量缩略图
- 自定义水印

---

## 💻 系统要求

### 最低要求
- **操作系统**: Windows 7+ / macOS 10.12+ / Linux
- **Python**: 3.7 或更高版本
- **内存**: 2GB RAM
- **硬盘**: 500MB 可用空间

### 推荐配置
- **操作系统**: Windows 10/11 / macOS 12+ / Ubuntu 20.04+
- **Python**: 3.9 或更高版本
- **内存**: 4GB+ RAM
- **硬盘**: 1GB+ 可用空间

---

## 🔧 安装指南

### 方法一：快速安装（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/UltimateFileConverter.git
cd UltimateFileConverter

# 2. 安装核心依赖
pip install PyQt5 Pillow

# 3. 运行程序
python UltimateFileConverter.py
```

### 方法二：完整安装（全功能）

```bash
# 安装所有依赖
pip install PyQt5 Pillow pandas openpyxl python-docx beautifulsoup4 \
    pypdf reportlab pydub moviepy ebooklib pyyaml qrcode cairosvg toml

# 安装 FFmpeg（音视频转换必需）
# Windows (使用 Chocolatey):
choco install ffmpeg

# macOS (使用 Homebrew):
brew install ffmpeg

# Linux (Ubuntu/Debian):
sudo apt update && sudo apt install ffmpeg

# 安装 Calibre（电子书增强）
# 访问: https://calibre-ebook.com/download
```

### 方法三：使用虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行程序
python UltimateFileConverter.py
```

### 创建 requirements.txt
```text
PyQt5>=5.15.0
Pillow>=9.0.0
pandas>=1.3.0
openpyxl>=3.0.0
python-docx>=0.8.11
beautifulsoup4>=4.10.0
pypdf>=3.0.0
reportlab>=3.6.0
pydub>=0.25.1
moviepy>=1.0.3
ebooklib>=0.18
PyYAML>=6.0
qrcode>=7.3
cairosvg>=2.5.0
toml>=0.10.2
```

---

## 📖 使用说明

### 基本操作流程

#### 1️⃣ 添加文件
- **方法一**: 点击 `📁 添加文件` 按钮
- **方法二**: 点击 `批量添加` 选择多个文件
- **方法三**: 直接拖拽文件到窗口

#### 2️⃣ 选择转换类别
在左侧面板选择文件类别：
- 🖼️ 图片格式
- 📄 文档格式
- 📊 数据格式
- 🎵 音频格式
- 🎬 视频格式
- 📦 压缩格式
- 📚 电子书
- 🔐 编码转换
- 🎨 特殊功能

#### 3️⃣ 选择输出格式
从下拉菜单中选择目标格式

#### 4️⃣ 调整质量（可选）
拖动质量滑块（1-100），默认85

#### 5️⃣ 选择输出位置（可选）
- 默认：与源文件相同位置
- 自定义：点击 `选择输出文件夹`

#### 6️⃣ 开始转换
点击 `🚀 开始转换` 按钮

### 高级功能

#### 📊 文件信息查看
选中文件后，在右侧 `ℹ️ 文件信息` 标签页查看：
- 文件名、路径、大小
- 创建/修改时间
- MD5 哈希值

#### 👁️ 文件预览
支持预览：
- 图片文件（PNG、JPG等）
- 文本文件（TXT、MD等）

#### 📜 历史记录
查看所有转换记录：
- 转换时间
- 文件数量
- 成功/失败统计
- 转换用时

#### 🎨 主题切换
- 菜单栏：`视图 → 切换主题`
- 快捷键：`Ctrl+T`

---

## ⌨️ 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+O` | 打开文件 |
| `Ctrl+Shift+O` | 批量打开文件 |
| `Ctrl+T` | 切换主题 |
| `Ctrl+Q` | 退出程序 |
| `F1` | 打开帮助 |
| `拖拽文件` | 添加文件到列表 |

---

## 📚 依赖库

### 核心依赖（必需）
```python
PyQt5       # GUI框架
Pillow      # 图片处理
```

### 功能依赖（可选）

| 库名 | 功能 | 安装命令 |
|------|------|----------|
| `pandas` | 数据格式转换 | `pip install pandas openpyxl` |
| `python-docx` | Word文档处理 | `pip install python-docx` |
| `beautifulsoup4` | HTML解析 | `pip install beautifulsoup4` |
| `pypdf` | PDF读取 | `pip install pypdf` |
| `reportlab` | PDF生成 | `pip install reportlab` |
| `pydub` | 音频处理 | `pip install pydub` |
| `moviepy` | 视频处理 | `pip install moviepy` |
| `ebooklib` | 电子书处理 | `pip install ebooklib` |
| `PyYAML` | YAML处理 | `pip install pyyaml` |
| `qrcode` | 二维码生成 | `pip install qrcode` |
| `cairosvg` | SVG转换 | `pip install cairosvg` |

### 外部工具

| 工具 | 用途 | 下载链接 |
|------|------|----------|
| `FFmpeg` | 音视频转换 | [下载](https://ffmpeg.org/download.html) |
| `Calibre` | 电子书增强 | [下载](https://calibre-ebook.com/download) |

---

## 🔍 常见问题

### Q1: 安装后无法运行？
**A:** 检查 Python 版本：
```bash
python --version  # 应为 3.7+
```

### Q2: 转换失败提示缺少依赖？
**A:** 使用依赖检查功能：
- 菜单栏 → `帮助 → 依赖检查`
- 根据提示安装缺失的库

### Q3: 音频/视频转换不工作？
**A:** 确保已安装 FFmpeg：
```bash
# 测试 FFmpeg
ffmpeg -version

# 如未安装，参考安装指南
```

### Q4: PDF中文显示乱码？
**A:** 确保系统已安装中文字体：
- Windows: 自动使用宋体
- macOS: 自动使用PingFang
- Linux: 安装 `fonts-wqy-microhei`

### Q5: SVG转换失败？
**A:** 安装 cairosvg：
```bash
pip install cairosvg
# Linux 需额外安装:
sudo apt install libcairo2-dev
```

### Q6: 如何处理大文件？
**A:** 
- 建议单个文件 < 500MB
- 大文件可能需要较长时间
- 转换时避免操作其他程序

### Q7: 转换质量如何控制？
**A:** 
- 图片：质量越高文件越大（推荐 80-90）
- 音频：影响比特率（推荐 70-85）
- 视频：影响比特率（推荐 75-90）

### Q8: 支持批量转换吗？
**A:** 是的！
- 使用 `批量添加` 或拖拽多个文件
- 程序会依次处理所有文件

---

## 📝 更新日志

### v4.0 Pro (2024-01-XX) - 重大更新
- 🎉 **全新界面**: 从 Tkinter 迁移到 PyQt5
- ✨ **拖拽支持**: 直接拖拽文件到窗口
- 🎨 **主题切换**: 支持亮色/暗色模式
- 👁️ **文件预览**: 实时预览图片和文本
- 📊 **历史记录**: 表格化显示转换历史
- 🔧 **多线程**: 转换时界面不卡顿
- 💾 **配置保存**: 自动保存用户设置
- 🐛 **Bug修复**: 修复多个已知问题

### v3.0 (2023-XX-XX)
- 新增视频格式支持
- 优化转换速度
- 改进错误处理

### v2.0 (2023-XX-XX)
- 新增电子书转换
- 支持批量处理
- 添加质量控制

### v1.0 (2023-XX-XX)
- 首次发布
- 支持基本图片转换
- 支持文档转换

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献

1. **Fork 本仓库**
2. **创建特性分支**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **提交更改**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **推送到分支**
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **提交 Pull Request**

### 贡献类型

- 🐛 报告 Bug
- 💡 提出新功能建议
- 📝 改进文档
- 🔧 提交代码修复
- 🌍 翻译文档

### 代码规范

- 遵循 PEP 8 Python 代码风格
- 添加适当的注释和文档字符串
- 编写单元测试
- 确保代码通过所有测试

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

```
MIT License

Copyright (c) 2024 Ultimate Converter Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📧 联系方式

- **项目主页**: [GitHub](https://github.com/yourusername/UltimateFileConverter)
- **问题反馈**: [Issues](https://github.com/yourusername/UltimateFileConverter/issues)
- **邮箱**: your.email@example.com

---

## 🌟 致谢

感谢以下开源项目：

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - 强大的GUI框架
- [Pillow](https://python-pillow.org/) - Python图像处理库
- [pandas](https://pandas.pydata.org/) - 数据分析库
- [FFmpeg](https://ffmpeg.org/) - 多媒体处理工具
- [Calibre](https://calibre-ebook.com/) - 电子书管理工具

---

## ⭐ Star History

如果这个项目对您有帮助，请给我们一个 Star ⭐️

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/UltimateFileConverter&type=Date)](https://star-history.com/#yourusername/UltimateFileConverter&Date)

---

<div align="center">

**[⬆ 回到顶部](#-终极文件格式转换器-v40-pro-pyqt5)**

Made with ❤️ by Ultimate Converter Team

</div>