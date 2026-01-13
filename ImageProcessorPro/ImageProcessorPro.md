# ImageProcessorPro Ultimate - 专业图像处理工具

<div align="center">

**作者：LYP** | [GitHub](https://github.com/lyp0746) | [邮箱](mailto:1610369302@qq.com)

**🎨 对标 WPS 图片的全功能专业图像处理软件**

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Version](https://img.shields.io/badge/Version-2.0-red.svg)

[功能特性](#-功能特性) • [安装说明](#-安装说明) • [使用指南](#-使用指南) • [快捷键](#-快捷键列表) • [依赖说明](#-依赖说明)

</div>

---

## 📋 目录

- [项目简介](#-项目简介)
- [功能特性](#-功能特性)
- [系统要求](#-系统要求)
- [安装说明](#-安装说明)
- [使用指南](#-使用指南)
- [快捷键列表](#-快捷键列表)
- [依赖说明](#-依赖说明)
- [常见问题](#-常见问题)
- [更新日志](#-更新日志)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)

---

## 🎯 项目简介

**ImageProcessorPro Ultimate** 是一款功能强大的专业图像处理软件，采用 Python + PyQt5 开发，提供与 WPS 图片相媲美的全方位图像编辑功能。软件拥有现代化的深色主题界面，支持批量处理、AI 智能抠图、多种滤镜特效等高级功能。

### ✨ 亮点

- 🎨 **20+ 专业滤镜** - 复古、HDR、卡通、素描等多种艺术效果
- 🤖 **AI 智能功能** - 一键智能抠图、背景移除
- 📦 **批量处理** - 多线程异步处理，支持批量格式转换
- 🖼️ **图片拼接** - 横向/纵向/网格三种拼接模式
- 📝 **OCR 识别** - 支持中英文文字识别
- 🎭 **历史记录** - 无限撤销/重做（最多50步）
- ⚡ **实时预览** - 所有调整效果实时可见
- 🌙 **深色主题** - 现代化护眼界面设计

---

## 🚀 功能特性

### 📐 基础编辑功能

| 功能 | 描述 | 快捷键 |
|------|------|--------|
| **旋转** | 左转90°、右转90°、旋转180° | `Ctrl+R` / `Ctrl+Shift+R` |
| **翻转** | 水平翻转、垂直翻转 | `Ctrl+H` / `Ctrl+V` |
| **裁剪** | 框选裁剪、固定尺寸裁剪、居中裁剪 | - |
| **缩放** | 自由缩放、保持宽高比缩放 | - |

### 🎨 高级调节功能

- **亮度调节** (0.5-1.5倍)
- **对比度调节** (0.5-1.5倍)
- **饱和度调节** (0-2倍)
- **锐度调节** (0-2倍)
- **色温调节** (-100 到 +100)
- **色相调节** (-180° 到 +180°)

### 🌈 滤镜特效库

#### 基础滤镜
- 黑白、怀旧、反色
- 模糊、高斯模糊、锐化
- 边缘增强、浮雕、轮廓

#### 艺术滤镜
- **复古** - 经典怀旧色调
- **冷色调** - 增强蓝色调
- **暖色调** - 增强红黄色调
- **鲜艳** - 提高色彩饱和度
- **柔和** - 降低对比度和锐度
- **戏剧** - 高对比度效果
- **HDR** - 高动态范围模拟
- **卡通** - 卡通化效果
- **素描** - 铅笔素描效果

### 🤖 AI 智能功能

- **智能抠图** - 基于 AI 的自动背景移除
- **一键美化** - 智能色彩增强

### 📝 标注工具

| 工具 | 功能描述 |
|------|----------|
| **文字标注** | 可调大小、颜色、位置的文字标记 |
| **马赛克** | 框选区域添加马赛克保护隐私 |
| **水印** | 添加文字/图片水印，可调透明度 |

### 🖼️ 图片拼接

- **横向拼接** - 将图片从左到右排列
- **纵向拼接** - 将图片从上到下排列
- **网格拼接** - 自动计算行列数的网格布局

### 📦 批量处理

- ✅ 批量格式转换（JPEG/PNG/BMP/WEBP）
- ✅ 批量缩放调整
- ✅ 批量应用滤镜
- ✅ 批量添加水印
- ✅ 自定义命名规则（前缀/后缀）
- ✅ 多线程异步处理
- ✅ 实时进度显示

### 🔧 实用工具

- **OCR 文字识别** - 支持中英文识别（需要 Tesseract）
- **EXIF 信息查看** - 查看图片元数据
- **RGB 直方图** - 分析图片色彩分布
- **打印预览** - 图片打印功能

### 💾 文件支持

**支持格式：**
```
.jpg, .jpeg, .png, .bmp, .gif, .tiff, .tif, .webp, .ico, .ppm, .pgm, .pbm
```

---

## 💻 系统要求

### 最低要求
- **操作系统**: Windows 7+, macOS 10.12+, Linux (Ubuntu 16.04+)
- **Python**: 3.7 或更高版本
- **内存**: 2GB RAM
- **硬盘**: 100MB 可用空间

### 推荐配置
- **操作系统**: Windows 10+, macOS 11+, Linux (Ubuntu 20.04+)
- **Python**: 3.9 或更高版本
- **内存**: 4GB+ RAM
- **硬盘**: 500MB 可用空间

---

## 📥 安装说明

### 方法一：使用 pip 安装（推荐）

#### 1. 安装核心依赖

```bash
# 安装必需的库
pip install PyQt5 Pillow numpy opencv-python
```

#### 2. 安装可选依赖

```bash
# OCR 文字识别功能
pip install pytesseract

# AI 智能抠图功能
pip install rembg

# 直方图显示功能
pip install matplotlib
```

#### 3. 安装 Tesseract OCR（用于 OCR 功能）

**Windows:**
1. 下载安装程序：https://github.com/UB-Mannheim/tesseract/wiki
2. 安装到默认路径
3. 下载中文语言包（chi_sim.traineddata）放到 `tessdata` 目录

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang  # 中文支持
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-chi-sim  # 中文支持
```

### 方法二：使用 requirements.txt

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装所有依赖
pip install -r requirements.txt
```

**requirements.txt 内容：**
```txt
PyQt5>=5.15.0
Pillow>=9.0.0
numpy>=1.21.0
opencv-python>=4.5.0
pytesseract>=0.3.8
rembg>=2.0.0
matplotlib>=3.5.0
```

### 方法三：从源码安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/ImageProcessorPro.git
cd ImageProcessorPro

# 安装依赖
pip install -r requirements.txt

# 运行程序
python ImageProcessorPro.py
```

---

## 📖 使用指南

### 🎬 快速开始

#### 1. 启动程序

```bash
python ImageProcessorPro.py
```

#### 2. 添加图片

- **方法一**: 点击左侧 `添加` 按钮选择图片
- **方法二**: 直接拖拽图片文件到左侧列表区域
- **方法三**: 使用菜单 `文件 → 打开图片` (Ctrl+O)

#### 3. 基础编辑流程

```
选择图片 → 使用工具面板编辑 → 实时预览效果 → 应用更改 → 保存图片
```

### 🎨 详细操作说明

#### 基础编辑

1. **旋转图片**
   - 点击 `基础编辑` 标签页
   - 选择 `左转90°`、`右转90°` 或 `旋转180°`
   - 效果立即应用

2. **裁剪图片**
   - 方法一：点击 `框选裁剪`，在图片上拖拽选择区域
   - 方法二：输入固定尺寸，点击 `居中裁剪`

3. **缩放图片**
   - 输入目标宽度和高度
   - 勾选 `保持宽高比` 可等比缩放
   - 点击 `应用缩放`

#### 调节参数

1. 切换到 `调节` 标签页
2. 拖动滑块调整各项参数：
   - 亮度、对比度、饱和度
   - 锐度、色温、色相
3. 效果实时预览
4. 满意后点击 `应用更改`

#### 应用滤镜

1. 切换到 `滤镜特效` 标签页
2. 从列表中选择滤镜
3. 实时预览效果
4. 点击 `应用更改` 确认

#### 添加文字标注

1. 切换到 `标注` 标签页
2. 在 `文字标注` 区域输入文字
3. 设置字体大小和颜色
4. 选择位置（左上/右上/左下/右下/居中）
5. 点击 `添加文字`

#### 添加马赛克

1. 切换到 `标注` 标签页
2. 在 `马赛克` 区域设置块大小
3. 点击 `框选添加马赛克`
4. 在图片上拖拽选择要打码的区域

#### 添加水印

1. 切换到 `水印` 标签页
2. 输入水印文字
3. 设置位置、大小、透明度
4. 点击 `添加水印`

#### 批量处理

1. 添加多张图片到列表
2. 切换到 `批处理` 标签页
3. 配置输出设置：
   - 格式：选择输出格式
   - 质量：调整压缩质量（1-100）
   - 命名：设置前缀和后缀
4. 配置处理选项（如缩放、滤镜等）
5. 点击 `开始批处理`
6. 选择输出目录
7. 等待处理完成

#### 图片拼接

1. 按住 Ctrl 选中多张图片（至少2张）
2. 切换到 `工具` 标签页
3. 在 `图片拼接` 区域选择拼接模式
4. 设置图片间距
5. 点击 `拼接选中的图片`

#### AI 智能抠图

1. 选择要抠图的图片
2. 切换到 `工具` 标签页
3. 点击 `智能抠图/背景移除`
4. 等待 AI 处理（可能需要几秒钟）
5. 完成后背景变为透明

#### OCR 文字识别

1. 选择包含文字的图片
2. 切换到 `工具` 标签页
3. 选择识别语言（中英文/仅中文/仅英文）
4. 点击 `识别文字`
5. 在弹出窗口查看识别结果
6. 可点击 `复制` 按钮复制文本

#### 查看图片信息

- **EXIF 信息**: `工具` → `查看EXIF信息`
- **RGB 直方图**: `工具` → `查看直方图`

### 💾 保存图片

#### 保存方式

1. **覆盖保存** (Ctrl+S)
   - 直接覆盖原文件
   - 会提示确认

2. **另存为** (Ctrl+Shift+S)
   - 保存到新文件
   - 可选择格式和路径

### ⏮️ 撤销与重做

- **撤销**: Ctrl+Z 或点击工具栏撤销按钮
- **重做**: Ctrl+Shift+Z 或点击工具栏重做按钮
- 支持最多 50 步历史记录

---

## ⌨️ 快捷键列表

### 文件操作

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+O` | 打开图片 |
| `Ctrl+S` | 保存 |
| `Ctrl+Shift+S` | 另存为 |
| `Ctrl+Q` | 退出程序 |

### 编辑操作

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Z` | 撤销 |
| `Ctrl+Shift+Z` | 重做 |
| `Ctrl+R` | 右转90° |
| `Ctrl+Shift+R` | 左转90° |
| `Ctrl+H` | 水平翻转 |
| `Ctrl+V` | 垂直翻转 |

### 视图控制

| 快捷键 | 功能 |
|--------|------|
| `Ctrl++` | 放大 |
| `Ctrl+-` | 缩小 |
| `Ctrl+0` | 实际大小 |

### 导航

| 快捷键 | 功能 |
|--------|------|
| `←` | 上一张图片 |
| `→` | 下一张图片 |

---

## 📦 依赖说明

### 核心依赖（必需）

| 库名 | 版本 | 用途 |
|------|------|------|
| **PyQt5** | ≥5.15.0 | GUI 框架 |
| **Pillow** | ≥9.0.0 | 图像处理核心 |
| **NumPy** | ≥1.21.0 | 数值计算 |
| **OpenCV-Python** | ≥4.5.0 | 高级图像处理 |

### 可选依赖

| 库名 | 版本 | 用途 | 安装命令 |
|------|------|------|----------|
| **pytesseract** | ≥0.3.8 | OCR 文字识别 | `pip install pytesseract` |
| **rembg** | ≥2.0.0 | AI 智能抠图 | `pip install rembg` |
| **matplotlib** | ≥3.5.0 | 直方图显示 | `pip install matplotlib` |

### 可选依赖说明

- **pytesseract**: 需要额外安装 Tesseract OCR 引擎
- **rembg**: 首次使用会自动下载 AI 模型（约 176MB）
- **matplotlib**: 仅用于显示 RGB 直方图

---

## ❓ 常见问题

### Q1: 程序启动报错 "No module named 'PyQt5'"

**A:** 请确保已正确安装 PyQt5：
```bash
pip install PyQt5
```

### Q2: OCR 功能不可用

**A:** 需要完成以下步骤：
1. 安装 pytesseract: `pip install pytesseract`
2. 安装 Tesseract OCR 引擎（见[安装说明](#3-安装-tesseract-ocr用于-ocr-功能)）
3. 确保 Tesseract 在系统 PATH 中

### Q3: AI 抠图功能很慢或失败

**A:** 
- 首次使用会下载 AI 模型，需要良好的网络连接
- 处理大图需要较长时间，请耐心等待
- 确保已安装: `pip install rembg`

### Q4: 批处理时程序假死

**A:** 
- 这是正常现象，程序在后台处理
- 查看进度条了解处理进度
- 不要在处理过程中关闭程序

### Q5: 某些滤镜效果不明显

**A:** 
- 不同图片效果不同
- 可尝试先调节亮度、对比度等参数
- 可叠加多个滤镜使用

### Q6: 保存后图片质量下降

**A:** 
- JPEG 格式会有压缩损失
- 批处理时可提高质量参数（90-100）
- 需要无损保存可选择 PNG 格式

### Q7: 如何完全卸载

**A:** 
```bash
# 卸载 Python 包
pip uninstall PyQt5 Pillow numpy opencv-python pytesseract rembg matplotlib

# 删除程序文件
# 手动删除 ImageProcessorPro.py 及相关文件
```

---

## 📝 更新日志

### Version 2.0 (2025-12-12)

#### 🎉 重大更新
- ✨ 完全重构代码架构
- 🎨 新增 20+ 专业滤镜特效
- 🤖 集成 AI 智能抠图功能
- 🖼️ 新增图片拼接功能（横向/纵向/网格）
- 📝 新增 OCR 文字识别功能

#### 🔧 功能增强
- ⚡ 批处理性能优化（多线程异步）
- 🎭 新增历史记录系统（撤销/重做）
- 📊 新增 RGB 直方图显示
- 💾 新增 EXIF 信息查看
- 🎨 新增色温和色相调节

#### 🖥️ UI/UX 改进
- 🌙 全新深色主题界面
- 🖼️ 优化图片预览效果
- 📱 改进响应式布局
- ⌨️ 完善快捷键支持
- 🎯 优化拖拽操作体验

#### 🐛 Bug 修复
- 修复大图加载内存溢出
- 修复 EXIF 方向信息处理
- 修复透明图片保存问题
- 修复批处理中断问题
- 修复多处界面显示 bug

### Version 1.0 (Initial Release)
- 基础图像编辑功能
- 简单滤镜效果
- 水印添加
- 批量转换

---

## 🤝 贡献指南

我们欢迎任何形式的贡献！

### 如何贡献

1. **Fork 本仓库**
2. **创建特性分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'Add some AmazingFeature'`)
4. **推送到分支** (`git push origin feature/AmazingFeature`)
5. **提交 Pull Request**

### 报告 Bug

请在 [Issues](https://github.com/yourusername/ImageProcessorPro/issues) 页面提交 Bug 报告，包含：
- 详细的问题描述
- 复现步骤
- 预期行为
- 实际行为
- 系统环境信息
- 错误截图（如有）

### 功能建议

欢迎在 [Issues](https://github.com/yourusername/ImageProcessorPro/issues) 提出新功能建议！

---

## 📄 许可证

本项目采用 **MIT License** 开源协议。

```
MIT License

Copyright (c) 2025 ImageProcessorPro

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

- **项目主页**: https://github.com/yourusername/ImageProcessorPro
- **问题反馈**: https://github.com/yourusername/ImageProcessorPro/issues
- **邮箱**: your.email@example.com

---

## 🌟 致谢

感谢以下开源项目：

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI 框架
- [Pillow](https://python-pillow.org/) - Python 图像库
- [OpenCV](https://opencv.org/) - 计算机视觉库
- [rembg](https://github.com/danielgatis/rembg) - AI 背景移除
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - 文字识别引擎

---

## 📸 截图预览

### 主界面
```
┌─────────────────────────────────────────────────────────────┐
│  [文件] [编辑] [视图] [帮助]                    [🔧 工具栏] │
├──────────┬──────────────────────────────┬───────────────────┤
│          │                              │  ┌─基础编辑─┐    │
│  图片    │                              │  │  旋转     │    │
│  列表    │      图片预览区              │  │  翻转     │    │
│          │                              │  │  裁剪     │    │
│  [缩略图]│                              │  │  缩放     │    │
│          │                              │  └──────────┘    │
│          │                              │  ┌─调节─────┐    │
│          │                              │  │  亮度     │    │
│  [+添加] │      [适应窗口] [━━100%━━]  │  │  对比度   │    │
│  [-删除] │                              │  │  饱和度   │    │
│  [×清空] │                              │  └──────────┘    │
├──────────┴──────────────────────────────┴───────────────────┤
│  就绪                                     [进度条]          │
└─────────────────────────────────────────────────────────────┘
```

---

<div align="center">

**⭐ 如果觉得这个项目有用，请给一个 Star！⭐**

Made with ❤️ by ImageProcessorPro Team

</div>
