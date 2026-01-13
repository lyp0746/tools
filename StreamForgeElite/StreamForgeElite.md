# StreamForge Elite v10.0 🎬

<div align="center">

**作者：LYP** | [GitHub](https://github.com/lyp0746) | [邮箱](mailto:1610369302@qq.com)

![Version](https://img.shields.io/badge/version-10.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-orange.svg)
![License](https://img.shields.io/badge/license-MIT-purple.svg)

**全能流媒体终端 - 多站点解析与批量下载**

基于 `yt-dlp` 与 `FFmpeg` | PyQt5 终极重构版

[功能特性](#-功能特性) • [安装指南](#-安装指南) • [使用教程](#-使用教程) • [常见问题](#-常见问题)

</div>

---

## 📖 简介

StreamForge Elite 是一款功能强大的跨平台流媒体下载工具，支持 YouTube、Bilibili、Twitter、TikTok 等数百个视频平台。采用现代化的 PyQt5 界面，提供直观的操作体验和丰富的高级功能。

### 🆕 v10.0 重大更新

- ✨ **全新 PyQt5 界面** - 更现代化的设计语言
- ✨ **批量 URL 解析** - 支持多个链接同时解析
- ✨ **拖放导入支持** - 直接拖放 URL 到输入框
- ✨ **下载限速功能** - 精准控制网络带宽
- ✨ **格式预设管理** - 保存常用配置，一键切换
- ✨ **快捷键支持** - 提升操作效率
- ✨ **优化的布局** - 更宽松的间距，避免元素拥挤
- ✨ **深色/浅色主题** - 自由切换视觉风格
- ✨ **系统托盘支持** - 最小化到托盘运行
- ✨ **任务队列持久化** - 自动保存和恢复任务

---

## 🚀 功能特性

### 核心功能

#### 📥 多站点支持
- 支持 **1000+ 视频网站**
  - 🎥 YouTube / YouTube Music
  - 📺 Bilibili (哔哩哔哩)
  - 🐦 Twitter / X
  - 🎵 TikTok / 抖音
  - 📷 Instagram
  - 🎬 Vimeo
  - 🎮 Twitch
  - 📺 Facebook
  - 更多...

#### 🎯 智能解析
- **单视频解析** - 自动提取最佳画质
- **播放列表解析** - 批量下载整个播放列表
- **频道解析** - 下载 UP 主全部视频
- **批量 URL 导入** - 支持多个链接同时解析
- **实时进度反馈** - 显示解析状态和进度

#### 🎬 视频下载
- **多分辨率选择**
  - Best (最佳画质)
  - 4K (2160p)
  - 2K (1440p)
  - 1080p / 720p / 480p / 360p
  
- **格式转换**
  - 视频: MP4, MKV, WebM, AVI
  - 音频: MP3, M4A, FLAC, Opus, WAV

- **多线程下载** (1-32 线程可调)
- **断点续传** (自动重试)
- **下载限速** (防止占满带宽)

#### 🎵 音频提取
- **高音质提取**
  - 320 kbps / 256 kbps / 192 kbps / 128 kbps / 96 kbps
  
- **多格式支持**
  - MP3 (通用兼容)
  - FLAC (无损音质)
  - M4A (Apple 生态)
  - Opus (高效编码)
  - WAV (原始音频)

#### 📝 字幕管理
- **自动下载字幕**
  - 所有可用语言
  - 简体中文 / 繁体中文
  - 英语 / 日语 / 韩语
  - 法语 / 西班牙语 / 德语
  
- **字幕内嵌** (自动合并到视频)
- **自动字幕** (AI 生成字幕)

#### 🍪 身份验证
- **浏览器 Cookie 获取**
  - Chrome / Chromium
  - Firefox
  - Edge
  - Opera / Brave
  - Safari
  
- **解锁会员内容**
- **绕过地区限制**
- **解决年龄验证**

#### ✂️ 视频截取
- **精准时间切片**
  - 支持格式: `HH:MM:SS` 或 `MM:SS`
  - 示例: `00:05:30` 到 `00:10:45`
  
- **无损切割** (基于关键帧)

#### 🚀 网络加速
- **多线程并发下载**
- **代理服务器支持**
  - HTTP / HTTPS 代理
  - SOCKS5 代理
  
- **智能限速** (避免 ISP 限流)
- **断线重连** (自动恢复)

#### 📦 任务管理
- **任务队列系统**
  - 添加 / 删除 / 暂停
  - 重新排队失败任务
  - 清空已完成任务
  
- **队列持久化** (自动保存和恢复)
- **导入 / 导出队列** (JSON 格式)
- **右键菜单** (复制标题、链接等)

#### 🎨 界面特性
- **现代化 UI 设计**
- **深色 / 浅色主题** 切换
- **拖放 URL 导入**
- **系统托盘支持**
- **实时进度显示**
- **多 Tab 布局**
  - 资源选择
  - 任务队列
  - 系统日志
  
- **快捷键支持**
- **响应式布局**

#### 🧩 高级功能
- **格式预设管理** (保存常用配置)
- **剪贴板监听** (自动检测视频链接)
- **完成后动作**
  - 无操作
  - 关闭程序
  - 关机
  - 休眠
  
- **元数据嵌入** (标题、艺术家、封面等)
- **缩略图嵌入**
- **文件名清理** (移除特殊字符)
- **描述文本保存**

#### 🛠️ 开发者工具
- **环境自检** (检测依赖和配置)
- **一键自测** (验证解析功能)
- **日志导出** (便于排查问题)
- **配置导入/导出**

---

## 💻 安装指南

### 系统要求

- **操作系统**: Windows 10/11, macOS 10.14+, Linux (Ubuntu 20.04+)
- **Python**: 3.8 或更高版本
- **内存**: 至少 2GB RAM
- **磁盘**: 100MB 安装空间 + 下载文件空间

### 方法一：使用 pip 安装（推荐）

#### 1. 安装 Python

**Windows:**
- 从 [python.org](https://www.python.org/downloads/) 下载安装包
- 安装时勾选 "Add Python to PATH"

**macOS:**
```bash
brew install python3
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

#### 2. 安装依赖

```bash
# 安装核心依赖
pip install PyQt5 yt-dlp

# 或使用国内镜像（速度更快）
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple PyQt5 yt-dlp
```

#### 3. 安装 FFmpeg（必需）

**Windows:**
- 从 [FFmpeg 官网](https://ffmpeg.org/download.html) 下载
- 或使用 Chocolatey: `choco install ffmpeg`
- 或使用 Scoop: `scoop install ffmpeg`

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install ffmpeg
```

#### 4. 运行程序

```bash
python StreamForgeElite.py
```

### 方法二：克隆仓库

```bash
# 克隆项目
git clone https://github.com/yourusername/StreamForgeElite.git
cd StreamForgeElite

# 安装依赖
pip install -r requirements.txt

# 运行程序
python StreamForgeElite.py
```

### 验证安装

运行程序后，点击菜单栏 **"工具" → "环境自检"** 验证所有依赖是否正确安装。

---

## 📚 使用教程

### 快速开始

#### 1️⃣ 解析视频

**方法 A: 手动输入**
1. 在顶部输入框粘贴视频链接
2. 支持多行输入（每行一个链接）
3. 点击 **"🔍 智能解析"** 按钮

**方法 B: 拖放导入**
1. 直接拖动链接到输入框
2. 自动填充

**方法 C: 剪贴板监听**
1. 勾选 **"剪贴板监听"**
2. 复制视频链接后自动填充

#### 2️⃣ 配置参数

**视频模式:**
- 选择分辨率 (Best / 4K / 2K / 1080p / 720p / 480p / 360p)
- 选择格式 (MP4 / MKV / WebM / AVI)

**音频模式:**
- 选择格式 (MP3 / M4A / FLAC / Opus / WAV)
- 选择码率 (320 / 256 / 192 / 128 / 96 kbps)

**高级选项:**
- 身份验证: 选择浏览器 Cookie
- 字幕设置: 选择语言和内嵌选项
- 时间切片: 输入起始和结束时间
- 网络设置: 配置代理、线程数、限速

#### 3️⃣ 添加到队列

1. 解析完成后，在 **"资源选择"** Tab 中查看结果
2. 选择要下载的视频（支持多选）
3. 点击 **"⬇ 添加到下载队列"** 按钮

或者勾选 **"解析后自动添加"** 自动加入队列。

#### 4️⃣ 开始下载

1. 切换到 **"任务队列"** Tab
2. 设置保存路径
3. 点击 **"▶ 开始所有任务"** 按钮
4. 实时查看进度和速度

#### 5️⃣ 查看日志

切换到 **"系统日志"** Tab 查看详细运行信息。

---

### 高级用法

#### 🎯 使用格式预设

**保存预设:**
1. 配置好视频/音频参数
2. 点击顶部 **"💾"** 按钮
3. 输入预设名称

**应用预设:**
1. 在 **"快捷预设"** 下拉框中选择
2. 自动应用配置

**管理预设:**
- 菜单栏 → 工具 → 管理格式预设

#### 🍪 使用 Cookie 下载会员内容

1. 在浏览器中登录视频网站
2. 在 **"身份验证"** 区域选择对应浏览器
3. 程序会自动读取 Cookie
4. 现在可以下载会员专属内容

**支持的场景:**
- Bilibili 大会员视频
- YouTube Premium 内容
- 地区限制视频
- 年龄验证视频

#### ✂️ 视频时间切片

**示例 1: 截取 5 分钟到 10 分钟的片段**
```
起始: 00:05:00
结束: 00:10:00
```

**示例 2: 截取前 30 秒**
```
起始: 00:00:00
结束: 00:00:30
```

**示例 3: 使用分钟格式**
```
起始: 5:30
结束: 10:45
```

#### 🚀 使用代理加速

**HTTP 代理:**
```
http://127.0.0.1:7890
```

**SOCKS5 代理:**
```
socks5://127.0.0.1:1080
```

**带认证的代理:**
```
http://username:password@proxy.example.com:8080
```

#### 📦 批量下载播放列表

1. 粘贴播放列表 URL
   ```
   https://www.youtube.com/playlist?list=PLxxxxxx
   ```
2. 解析后会显示所有视频
3. 全选后添加到队列
4. 批量下载

#### 📤 导出和导入队列

**导出队列:**
- 文件 → 导出任务队列
- 选择保存位置
- 生成 JSON 文件

**导入队列:**
- 文件 → 导入任务队列
- 选择之前导出的 JSON 文件
- 自动恢复任务

#### ⌨️ 快捷键列表

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Enter` | 开始下载 |
| `Ctrl+Shift+A` | 解析 URL |
| `Ctrl+L` | 清空输入 |
| `Ctrl+V` | 粘贴到输入框 |
| `Ctrl+O` | 打开保存目录 |
| `Ctrl+E` | 导出队列 |
| `Ctrl+I` | 导入队列 |
| `Ctrl+Q` | 退出程序 |
| `Delete` | 删除选中任务 |
| `F1` | 显示快捷键帮助 |

---

## 🎨 界面预览

### 主界面布局

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚡ StreamForge Elite v10.0        [预设▾] [主题] [托盘]        │
├─────────────────────────────────────────────────────────────────┤
│  📎 视频链接输入 (支持拖放)                                      │
│  ┌───────────────────────────────────────────────────┬────────┐ │
│  │ https://www.youtube.com/watch?v=...               │ [清空] │ │
│  │                                                    │ [粘贴] │ │
│  └───────────────────────────────────────────────────┴────────┘ │
│  [🔍 智能解析] [⏹ 停止] ☑ 剪贴板监听  ☑ 解析后自动添加          │
├──────────────────┬──────────────────────────────────────────────┤
│ ⚙️ 格式与画质     │  1️⃣ 资源选择  2️⃣ 任务队列  3️⃣ 系统日志    │
│ ☑ 视频 1080p MP4 │ ┌──────────────────────────────────────────┐ │
│ ☐ 音频 MP3 320   │ │ 📹 视频列表                              │ │
│                  │ │ ├─ YouTube Video 1    [10:23]  1M views  │ │
│ 🍪 身份验证       │ │ ├─ Bilibili Video 2   [05:45]  500K      │ │
│ [选择浏览器▾]    │ │ └─ Twitter Video 3    [00:30]  100K      │ │
│                  │ │                                          │ │
│ 📝 字幕设置       │ │ [全选] [取消] [反选]  已解析: 3 项       │ │
│ ☑ 下载并内嵌     │ │           [⬇ 添加到下载队列]            │ │
│ [语言: 全部▾]    │ └──────────────────────────────────────────┘ │
│                  │                                              │
│ ✂️ 视频截取       │                                              │
│ 起始: [00:00:00] │                                              │
│ 结束: [00:10:00] │                                              │
│                  │                                              │
│ 🚀 网络与加速     │                                              │
│ 线程: [8▾]       │                                              │
│ 限速: [0 MB/s▾]  │                                              │
│ 代理: [______]   │                                              │
│                  │                                              │
│ 🧩 文件与元数据   │                                              │
│ ☑ 清理文件名     │                                              │
│ ☑ 嵌入缩略图     │                                              │
│ ☐ 保存描述       │                                              │
└──────────────────┴──────────────────────────────────────────────┘
│ 💾 保存路径: [C:\Users\Downloads]    [📂 浏览] [打开文件夹]     │
│ 完成后: [无操作▾]       ⚡ 5.2 MB/s    [⏹ 停止] [▶ 开始所有]   │
└─────────────────────────────────────────────────────────────────┘
```

---

## ❓ 常见问题

### Q1: 安装后无法运行？

**A:** 检查以下几点：
1. Python 版本是否 ≥ 3.8
2. 依赖是否完整安装：`pip list | grep -E "PyQt5|yt-dlp"`
3. 运行环境自检：菜单 → 工具 → 环境自检

### Q2: 下载速度很慢？

**A:** 尝试以下方法：
1. 增加线程数（推荐 8-16）
2. 使用代理服务器
3. 检查网络连接
4. 关闭限速功能

### Q3: 无法下载某些视频？

**A:** 可能的原因：
- **地区限制**: 使用代理或 VPN
- **会员专属**: 配置浏览器 Cookie
- **年龄验证**: 使用已登录的浏览器 Cookie
- **平台更新**: 更新 yt-dlp：`pip install -U yt-dlp`

### Q4: 字幕没有内嵌到视频？

**A:** 确保：
1. FFmpeg 已正确安装
2. 勾选了 "下载字幕并自动内嵌"
3. 视频格式支持字幕（推荐 MP4 或 MKV）

### Q5: Cookie 验证失败？

**A:** 检查：
1. 浏览器是否已登录视频网站
2. 浏览器版本是否过旧
3. 尝试切换其他浏览器
4. Windows 用户可能需要管理员权限

### Q6: 如何下载整个频道的视频？

**A:** 
1. 粘贴频道 URL（如 `https://www.youtube.com/@username`）
2. 解析后会列出所有视频
3. 全选后批量下载

### Q7: 下载中途中断了怎么办？

**A:**
1. 查看系统日志确定原因
2. 在任务队列中右键选择 "重新排队"
3. 程序支持断点续传

### Q8: 如何更新到最新版本？

**A:**
```bash
# 更新 yt-dlp
pip install -U yt-dlp

# 更新 PyQt5（如需要）
pip install -U PyQt5

# 下载最新版程序文件
```

### Q9: 程序崩溃或卡死？

**A:**
1. 查看日志文件
2. 导出日志并提交 Issue
3. 尝试清空缓存：工具 → 清空缓存数据
4. 重启程序

### Q10: 支持哪些视频网站？

**A:** 支持 1000+ 网站，完整列表查看：
```bash
yt-dlp --list-extractors
```

常见网站包括：
- 视频: YouTube, Bilibili, Vimeo, Dailymotion
- 社交: Twitter/X, TikTok, Instagram, Facebook
- 直播: Twitch, YouTube Live
- 教育: Coursera, Udemy
- 其他: Reddit, SoundCloud, Spotify

---

## 🛠️ 故障排查

### 错误：`ModuleNotFoundError: No module named 'PyQt5'`

```bash
pip install PyQt5
```

### 错误：`ModuleNotFoundError: No module named 'yt_dlp'`

```bash
pip install yt-dlp
```

### 错误：`ffmpeg not found`

**Windows:**
1. 下载 FFmpeg
2. 解压到 `C:\ffmpeg`
3. 添加到环境变量 PATH: `C:\ffmpeg\bin`

**macOS/Linux:**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

### 错误：`SSL: CERTIFICATE_VERIFY_FAILED`

```bash
# macOS
/Applications/Python\ 3.x/Install\ Certificates.command

# Windows/Linux: 更新 certifi
pip install --upgrade certifi
```

### 解析失败：`ERROR: Unable to extract`

1. 更新 yt-dlp：`pip install -U yt-dlp`
2. 检查 URL 是否有效
3. 尝试使用代理或 Cookie

---

## 🔧 高级配置

### 配置文件位置

程序会在运行目录创建以下文件：

- `.streamforge_v10_config.json` - 主配置
- `.streamforge_v10_queue.json` - 任务队列
- `.streamforge_v10_presets.json` - 格式预设

### 手动编辑配置

**config.json 示例:**
```json
{
  "save_dir": "C:\\Users\\YourName\\Downloads",
  "proxy": "http://127.0.0.1:7890",
  "threads": 16,
  "rate_limit": 10.0,
  "clean_name": true,
  "embed_sub": true,
  "embed_thumb": true,
  "dark_mode": false
}
```

### 命令行使用 yt-dlp

如果需要更高级的功能，可以直接使用 yt-dlp：

```bash
# 下载最佳画质
yt-dlp -f "bv*+ba/b" URL

# 下载指定分辨率
yt-dlp -f "bv*[height<=1080]+ba/b" URL

# 仅下载音频
yt-dlp -x --audio-format mp3 --audio-quality 320K URL

# 使用代理
yt-dlp --proxy http://127.0.0.1:7890 URL

# 使用浏览器 Cookie
yt-dlp --cookies-from-browser chrome URL

# 下载字幕
yt-dlp --write-subs --sub-langs "en,zh-Hans" URL
```

---

## 📝 更新日志

### v10.0 (2024-12-12) 🎉

**重大更新:**
- ✨ 完全重构为 PyQt5 版本
- ✨ 全新的现代化界面设计
- ✨ 批量 URL 解析功能
- ✨ 拖放 URL 导入支持

**新增功能:**
- ➕ 下载限速设置
- ➕ 格式预设管理
- ➕ 快捷键支持
- ➕ 系统托盘集成
- ➕ 深色/浅色主题切换
- ➕ 任务右键菜单
- ➕ 队列导入/导出
- ➕ 实时进度条
- ➕ 剪贴板监听

**界面优化:**
- 🎨 更宽松的布局间距
- 🎨 优化的视觉分组
- 🎨 改进的配色方案
- 🎨 响应式设计
- 🎨 可滚动设置面板

**Bug 修复:**
- 🐛 修复线程安全问题
- 🐛 修复资源泄漏
- 🐛 改进错误处理
- 🐛 优化内存使用
- 🐛 修复 UI 卡顿

**性能提升:**
- ⚡ 更高效的 UI 更新
- ⚡ 优化的解析速度
- ⚡ 改进的下载逻辑

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 报告 Bug

请包含以下信息：
1. 操作系统和版本
2. Python 版本
3. 完整的错误信息
4. 重现步骤
5. 相关的日志输出

### 提交 Pull Request

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'Add some AmazingFeature'`
4. 推送到分支：`git push origin feature/AmazingFeature`
5. 提交 Pull Request

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/StreamForgeElite.git
cd StreamForgeElite

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行程序
python StreamForgeElite.py
```

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

本项目基于以下优秀开源项目：

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 强大的视频下载工具
- [FFmpeg](https://ffmpeg.org/) - 音视频处理框架
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - Python GUI 框架

感谢所有贡献者和用户的支持！

---

## 📧 联系方式

- **问题反馈**: [GitHub Issues](https://github.com/yourusername/StreamForgeElite/issues)
- **功能建议**: [GitHub Discussions](https://github.com/yourusername/StreamForgeElite/discussions)
- **邮件**: your.email@example.com

---

## ⭐ Star History

如果这个项目对你有帮助，请给一个 Star ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/StreamForgeElite&type=Date)](https://star-history.com/#yourusername/StreamForgeElite&Date)

---

<div align="center">

**[⬆ 返回顶部](#streamforge-elite-v100-)**

Made with ❤️ by StreamForge Team

</div>
