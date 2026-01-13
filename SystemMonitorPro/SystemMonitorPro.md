# SystemMonitorPro v2.0

<div align="center">

**作者：LYP** | [GitHub](https://github.com/lyp0746) | [邮箱](mailto:1610369302@qq.com)

![Version](https://img.shields.io/badge/version-2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-green.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-orange.svg)
![License](https://img.shields.io/badge/license-MIT-purple.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

**专业级跨平台系统监控与运维工具**

[功能特性](#-功能特性) • [安装指南](#-安装指南) • [使用说明](#-使用说明) • [截图预览](#-截图预览) • [技术架构](#-技术架构)

</div>

---

## 📋 目录

- [项目简介](#-项目简介)
- [功能特性](#-功能特性)
- [系统要求](#-系统要求)
- [安装指南](#-安装指南)
- [快速开始](#-快速开始)
- [使用说明](#-使用说明)
- [配置说明](#-配置说明)
- [技术架构](#-技术架构)
- [常见问题](#-常见问题)
- [更新日志](#-更新日志)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)
- [联系方式](#-联系方式)

---

## 🚀 项目简介

**SystemMonitorPro** 是一款基于 Python 和 PyQt5 开发的**专业级系统监控工具**，为系统管理员、开发者和高级用户提供全方位的系统监控、进程管理、日志分析和自动化运维功能。

### ✨ 核心优势

- 🎯 **实时监控** - 毫秒级数据刷新，精准掌握系统状态
- 📊 **可视化图表** - 动态曲线图表，直观展示历史趋势
- 🛠️ **进程管理** - 强大的进程控制与详情查看功能
- 🌐 **网络监控** - 实时流量统计和连接状态跟踪
- 📄 **日志分析** - 智能日志查看与过滤工具
- 🔧 **自动化运维** - 内置脚本模板，快速执行运维任务
- 🎨 **现代化UI** - 支持深色/浅色主题切换
- 📦 **跨平台** - 完美支持 Windows、Linux 和 macOS

---

## 🎯 功能特性

### 1️⃣ 实时系统监控仪表盘

#### CPU监控
- ✅ 实时CPU使用率（总体 + 单核心）
- ✅ CPU频率监控（当前/最小/最大）
- ✅ 核心数统计（物理核心 + 逻辑核心）
- ✅ 60秒历史趋势图表
- ✅ 自定义警报阈值

#### 内存监控
- ✅ 物理内存使用情况
- ✅ 虚拟内存（Swap）监控
- ✅ 详细内存占用分布
- ✅ 实时使用率曲线
- ✅ 内存泄漏检测

#### 磁盘监控
- ✅ 多磁盘分区监控
- ✅ 磁盘IO速度（读/写）
- ✅ 使用率和剩余空间
- ✅ 文件系统类型识别
- ✅ 磁盘健康预警

#### 网络监控
- ✅ 实时上传/下载速度
- ✅ 总流量统计
- ✅ 网络连接数统计
- ✅ 双曲线速度图表
- ✅ 网络接口详情

#### 硬件监控
- ✅ CPU温度传感器
- ✅ GPU温度（支持的设备）
- ✅ 电池状态与剩余时间
- ✅ 电源管理状态

---

### 2️⃣ 高级进程管理器

#### 进程列表
- ✅ 实时进程列表（PID、名称、状态）
- ✅ CPU和内存占用排序
- ✅ 线程数统计
- ✅ 用户身份识别
- ✅ 智能搜索和过滤

#### 进程操作
- ✅ 结束进程（Terminate/Kill）
- ✅ 挂起/恢复进程
- ✅ 进程详情对话框
- ✅ 批量进程管理
- ✅ 右键快捷菜单

#### 进程详情
- ✅ 完整进程信息查看
- ✅ 命令行参数
- ✅ 工作目录
- ✅ 可执行文件路径
- ✅ 创建时间与运行时长

---

### 3️⃣ 网络连接监控

#### 连接列表
- ✅ 实时TCP/UDP连接
- ✅ 本地/远程地址端口
- ✅ 连接状态（ESTABLISHED、LISTEN等）
- ✅ 进程关联显示
- ✅ 连接状态过滤

#### 网络接口
- ✅ 网卡列表与IP地址
- ✅ MAC地址识别
- ✅ 接口类型（IPv4/IPv6）
- ✅ 接口启用状态

---

### 4️⃣ 日志查看与分析

#### 日志查看
- ✅ 支持多种日志格式
- ✅ 实时日志监控（自动刷新）
- ✅ 大文件快速加载
- ✅ 语法高亮显示
- ✅ 行号统计

#### 日志分析
- ✅ 全文搜索功能
- ✅ 日志级别过滤（ERROR、WARN、INFO、DEBUG）
- ✅ 时间范围筛选
- ✅ 正则表达式搜索
- ✅ 导出筛选结果

---

### 5️⃣ 自动化脚本运行器

#### 脚本模板
- ✅ 内置常用运维脚本
  - 系统清理（临时文件、缓存清理）
  - 磁盘检查与修复
  - 网络诊断（ping、traceroute、netstat）
  - 系统信息采集
  - 进程管理脚本
- ✅ Windows和Linux双平台支持

#### 脚本编辑器
- ✅ 代码高亮编辑器
- ✅ 语法提示
- ✅ 注释支持
- ✅ 脚本保存与加载
- ✅ 导入外部脚本

#### 脚本执行
- ✅ 异步执行机制
- ✅ 实时输出捕获
- ✅ 错误信息高亮
- ✅ 执行超时控制
- ✅ 执行日志记录

---

### 6️⃣ 警报与通知系统

#### 性能警报
- ✅ CPU使用率警报
- ✅ 内存使用率警报
- ✅ 磁盘空间警报
- ✅ 自定义阈值设置
- ✅ 警报历史记录

#### 通知方式
- ✅ 系统托盘通知
- ✅ 声音提醒（可选）
- ✅ 桌面弹窗
- ✅ 警报日志保存

---

### 7️⃣ 数据导出与报告

#### 导出格式
- ✅ **CSV格式** - Excel友好的表格数据
- ✅ **JSON格式** - 结构化API数据
- ✅ **TXT格式** - 人类可读的文本报告
- ✅ **PDF报告**（规划中）

#### 导出内容
- ✅ 系统快照（CPU、内存、磁盘）
- ✅ 进程列表
- ✅ 网络连接状态
- ✅ 日志文件
- ✅ 自定义时间范围

---

### 8️⃣ 个性化设置

#### 外观设置
- ✅ 深色主题
- ✅ 浅色主题
- ✅ 自定义颜色方案
- ✅ 字体大小调整

#### 性能设置
- ✅ 监控刷新间隔（500ms - 10s）
- ✅ 进程刷新频率
- ✅ 历史数据长度（30-300秒）
- ✅ 内存占用优化

#### 警报设置
- ✅ 启用/禁用警报
- ✅ 阈值自定义
- ✅ 通知方式选择

---

## 💻 系统要求

### 最低要求
- **操作系统**: Windows 7+ / Linux (Kernel 3.0+) / macOS 10.12+
- **Python版本**: Python 3.7+
- **内存**: 512 MB RAM
- **磁盘空间**: 100 MB 可用空间

### 推荐配置
- **操作系统**: Windows 10/11 / Ubuntu 20.04+ / macOS 12+
- **Python版本**: Python 3.9+
- **内存**: 2 GB RAM
- **磁盘空间**: 500 MB 可用空间
- **显示器**: 1920x1080 分辨率

---

## 📦 安装指南

### 方法一：使用 pip 安装（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/SystemMonitorPro.git
cd SystemMonitorPro

# 2. 创建虚拟环境（可选但推荐）
python -m venv venv

# Windows 激活虚拟环境
venv\Scripts\activate

# Linux/macOS 激活虚拟环境
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行程序
python SystemMonitorPro.py
```

### 方法二：手动安装依赖

```bash
# 安装核心依赖
pip install PyQt5==5.15.9
pip install psutil==5.9.5
pip install PyQtChart==5.15.6
```

### 方法三：使用 conda 安装

```bash
# 创建 conda 环境
conda create -n sysmonitor python=3.9
conda activate sysmonitor

# 安装依赖
conda install pyqt psutil
pip install PyQtChart

# 运行程序
python SystemMonitorPro.py
```

### Linux 额外配置

某些功能需要管理员权限（如网络连接监控）：

```bash
# 临时授权
sudo python SystemMonitorPro.py

# 或添加 capabilities（推荐）
sudo setcap cap_net_raw+ep $(which python3)
```

---

## 🎬 快速开始

### 基础使用

```bash
# 1. 启动程序
python SystemMonitorPro.py

# 2. 查看系统监控仪表盘
点击 "📊 仪表盘" 标签页

# 3. 管理进程
点击 "⚙️ 进程管理" 标签页
搜索进程 → 选择进程 → 右键菜单操作

# 4. 查看日志
点击 "📄 日志查看" 标签页
输入日志路径 → 点击"加载"

# 5. 运行自动化脚本
点击 "🔧 自动化脚本" 标签页
选择模板 → 编辑脚本 → 点击"运行"
```

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `F5` | 刷新所有数据 |
| `Ctrl + Q` | 退出程序 |
| `Ctrl + S` | 保存当前脚本 |
| `Ctrl + E` | 导出报告 |
| `Ctrl + ,` | 打开设置 |

---

## 📖 使用说明

### 1. 仪表盘使用

#### 查看实时数据
- **统计卡片**: 顶部显示CPU、内存、磁盘、网络的实时使用率
- **历史图表**: 中间区域显示最近60秒的历史趋势
- **详细信息**: 底部显示系统信息、实时数据和温度/电池状态

#### 自定义显示
1. 点击 `⚙️ 设置`
2. 调整监控刷新间隔（默认1秒）
3. 修改历史数据长度（默认60秒）

### 2. 进程管理

#### 查找进程
```
1. 在搜索框输入进程名或PID
2. 表格自动过滤显示匹配结果
3. 点击列标题可按该列排序
```

#### 结束进程
```
1. 选中目标进程
2. 点击"❌ 结束"按钮
3. 确认操作
```

#### 查看进程详情
```
1. 双击进程行
2. 或右键 → "📋 查看详情"
3. 查看完整进程信息
```

### 3. 网络监控

#### 查看网络连接
```
1. 切换到 "🌐 网络监控" 标签页
2. 查看所有TCP/UDP连接
3. 使用过滤器筛选连接状态
```

#### 查看网络接口
```
顶部"网络接口"区域显示：
- 接口名称
- IP地址（IPv4/IPv6）
- MAC地址
```

### 4. 日志分析

#### 加载日志文件
```bash
# Windows 示例
C:\Windows\System32\winevt\Logs\System.evtx

# Linux 示例
/var/log/syslog
/var/log/auth.log
/var/log/nginx/access.log
```

#### 搜索日志
```
1. 在搜索框输入关键词
2. 按回车或点击"搜索"
3. 匹配内容会高亮显示
```

#### 过滤日志级别
```
使用级别过滤下拉框：
- ERROR: 仅显示错误
- WARN: 显示警告
- INFO: 显示信息
- DEBUG: 显示调试信息
```

### 5. 脚本自动化

#### 使用内置模板
```
1. 从"脚本模板"下拉框选择
2. 编辑器自动加载模板
3. 根据需要修改参数
4. 点击"▶️ 运行"
```

#### 创建自定义脚本
```bash
# 示例：备份重要文件
#!/bin/bash
# 备份脚本

# 设置备份目录
BACKUP_DIR="/backup/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 备份文件
cp -r /etc/nginx $BACKUP_DIR/
cp -r /var/www $BACKUP_DIR/

# 压缩备份
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR

echo "备份完成: $BACKUP_DIR.tar.gz"
```

#### 保存和加载脚本
```
保存: 点击"💾 保存" → 选择位置 → 保存
加载: 点击"📂 加载" → 选择文件 → 加载
```

### 6. 导出报告

#### 导出系统报告
```
1. 点击工具栏 "📊" 或菜单 "文件 → 导出报告"
2. 选择导出格式（CSV/JSON/TXT）
3. 选择保存位置
4. 点击"保存"
```

#### CSV格式示例
```csv
类别,项目,值
系统,操作系统,Windows 11
系统,主机名,DESKTOP-ABC123
CPU,使用率,45.2%
CPU,核心数,8
内存,使用率,62.5%
内存,总容量,16.00 GB
```

#### JSON格式示例
```json
{
  "timestamp": "2025-12-12T15:30:00",
  "system": {
    "platform": "Windows",
    "hostname": "DESKTOP-ABC123"
  },
  "cpu": {
    "percent": 45.2,
    "count": 8
  },
  "memory": {
    "total": 17179869184,
    "percent": 62.5
  }
}
```

---

## ⚙️ 配置说明

### 配置文件位置

配置文件使用 `QSettings` 自动管理：

```
Windows: HKEY_CURRENT_USER\Software\SystemMonitorPro\Settings
Linux: ~/.config/SystemMonitorPro/Settings.conf
macOS: ~/Library/Preferences/com.SystemMonitorPro.Settings.plist
```

### 配置选项

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `monitor_interval` | int | 1000 | 监控刷新间隔（毫秒） |
| `process_refresh` | int | 5000 | 进程列表刷新间隔（毫秒） |
| `history_length` | int | 60 | 历史数据长度（秒） |
| `theme` | str | light | 主题（light/dark） |
| `cpu_threshold` | float | 80.0 | CPU警报阈值（%） |
| `memory_threshold` | float | 80.0 | 内存警报阈值（%） |
| `disk_threshold` | float | 90.0 | 磁盘警报阈值（%） |
| `enable_alerts` | bool | true | 是否启用警报 |

### 手动编辑配置

**Linux 示例**：
```ini
# ~/.config/SystemMonitorPro/Settings.conf

[General]
monitor_interval=1000
process_refresh=5000
history_length=60
theme=dark
cpu_threshold=80.0
memory_threshold=80.0
disk_threshold=90.0
enable_alerts=true
```

---

## 🏗️ 技术架构

### 核心技术栈

```
┌─────────────────────────────────────┐
│         用户界面层 (PyQt5)          │
│  ┌──────────┬──────────┬──────────┐ │
│  │ 仪表盘   │ 进程管理 │ 日志查看 │ │
│  └──────────┴──────────┴──────────┘ │
└─────────────────────────────────────┘
              ↓ ↑
┌─────────────────────────────────────┐
│        业务逻辑层 (Python)          │
│  ┌──────────┬──────────┬──────────┐ │
│  │ 数据采集 │ 进程控制 │ 脚本执行 │ │
│  └──────────┴──────────┴──────────┘ │
└─────────────────────────────────────┘
              ↓ ↑
┌─────────────────────────────────────┐
│      系统接口层 (psutil)            │
│  ┌──────────┬──────────┬──────────┐ │
│  │ CPU/内存 │ 进程API  │ 网络IO   │ │
│  └──────────┴──────────┴──────────┘ │
└─────────────────────────────────────┘
              ↓ ↑
┌─────────────────────────────────────┐
│         操作系统 (OS Kernel)        │
└─────────────────────────────────────┘
```

### 依赖库

| 库名 | 版本 | 用途 |
|------|------|------|
| PyQt5 | 5.15+ | GUI框架 |
| psutil | 5.9+ | 系统信息采集 |
| PyQtChart | 5.15+ | 图表绘制 |

### 项目结构

```
SystemMonitorPro/
├── SystemMonitorPro.py       # 主程序文件
├── README.md                  # 本文档
├── requirements.txt           # 依赖列表
├── LICENSE                    # 许可证
├── .gitignore                # Git忽略文件
├── docs/                     # 文档目录
│   ├── screenshots/          # 截图
│   ├── manual.md            # 用户手册
│   └── api.md               # API文档
├── scripts/                  # 示例脚本
│   ├── system_cleanup.sh
│   ├── disk_check.bat
│   └── network_diag.sh
└── tests/                    # 测试文件
    ├── test_monitor.py
    └── test_process.py
```

### 多线程架构

```python
主线程 (GUI)
  ├── MonitorThread        # 系统监控线程
  ├── ProcessRefreshTimer  # 进程刷新定时器
  └── ScriptExecutor       # 脚本执行线程（异步）
```

---

## ❓ 常见问题

### Q1: 为什么某些功能需要管理员权限？

**A**: 某些系统信息（如网络连接、进程详情）需要较高权限才能访问。建议：

- **Windows**: 右键 → "以管理员身份运行"
- **Linux**: 使用 `sudo python SystemMonitorPro.py`
- **macOS**: 使用 `sudo` 或在"系统偏好设置"中授权

### Q2: 温度传感器显示不可用怎么办？

**A**: 温度监控依赖硬件和驱动支持：

- **Windows**: 安装 Open Hardware Monitor 或 HWiNFO
- **Linux**: 安装 `lm-sensors` 并运行 `sensors-detect`
- **macOS**: 部分Mac不支持温度读取

### Q3: 如何减少CPU占用？

**A**: 在设置中调整：

```
监控刷新间隔: 1000ms → 2000ms
进程刷新间隔: 5000ms → 10000ms
历史数据长度: 60秒 → 30秒
```

### Q4: 脚本执行超时怎么办？

**A**: 目前超时设置为30秒，可修改源码：

```python
# 在 ScriptRunnerWidget.run_script() 中
result = subprocess.run(
    line,
    shell=True,
    capture_output=True,
    text=True,
    timeout=60  # 修改为60秒
)
```

### Q5: 如何自定义主题颜色？

**A**: 在 `MainWindow.apply_theme()` 方法中修改样式表：

```python
# 自定义颜色方案
self.setStyleSheet("""
    QPushButton {
        background-color: #your_color;
    }
""")
```

### Q6: 支持远程监控吗？

**A**: 当前版本仅支持本地监控。远程监控功能计划在 v3.0 中实现。

### Q7: 如何导出历史数据？

**A**: 历史数据存储在内存中，可通过以下方式导出：

1. 点击"导出报告"按钮
2. 选择JSON格式
3. 历史数据会包含在导出文件中

---

## 📝 更新日志

### v2.0 (2025-12-12) - 完全重构版

#### 新增功能
- ✨ 全新的现代化UI设计
- ✨ 深色/浅色主题切换
- ✨ 网络连接监控标签页
- ✨ 进程挂起/恢复功能
- ✨ 进程详情对话框
- ✨ 警报系统与系统托盘通知
- ✨ 配置管理系统
- ✨ 数据导出功能（CSV/JSON/TXT）
- ✨ 日志自动刷新
- ✨ 脚本模板库
- ✨ 电池信息监控

#### 优化改进
- 🚀 性能优化：使用deque提高历史数据效率
- 🚀 线程安全改进
- 🚀 异常处理完善
- 🚀 内存占用优化
- 🎨 UI布局优化
- 🎨 图表动画优化

#### Bug修复
- 🐛 修复网络速度计算错误
- 🐛 修复进程列表刷新延迟
- 🐛 修复日志文件大文件卡顿
- 🐛 修复跨平台兼容性问题
- 🐛 修复内存泄漏

### v1.0 (2025-12-10) - 初始版本

- 🎉 基础系统监控功能
- 🎉 进程管理
- 🎉 日志查看
- 🎉 脚本执行

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献

1. **Fork 项目**
2. **创建特性分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'Add some AmazingFeature'`)
4. **推送到分支** (`git push origin feature/AmazingFeature`)
5. **提交 Pull Request**

### 贡献类型

- 🐛 报告Bug
- 💡 提出新功能建议
- 📝 改进文档
- 🔧 修复问题
- ✨ 添加新功能
- 🌐 翻译支持

### 代码规范

- 遵循 PEP 8 Python代码规范
- 使用有意义的变量和函数名
- 添加必要的注释和文档字符串
- 编写单元测试

### 问题反馈

在 [GitHub Issues](https://github.com/yourusername/SystemMonitorPro/issues) 中提交：

- 详细的问题描述
- 复现步骤
- 系统环境信息
- 相关截图或日志

---

## 📄 许可证

本项目采用 **MIT License** 许可证 - 详见 [LICENSE](LICENSE) 文件。

```
MIT License

Copyright (c) 2025 SystemMonitorPro

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## 📧 联系方式

- **项目主页**: https://github.com/yourusername/SystemMonitorPro
- **问题反馈**: https://github.com/yourusername/SystemMonitorPro/issues
- **电子邮件**: your.email@example.com
- **官方文档**: https://systemmonitorpro.readthedocs.io

---

## 🙏 致谢

感谢以下开源项目：

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - 强大的Python GUI框架
- [psutil](https://github.com/giampaolo/psutil) - 跨平台系统监控库
- [Python](https://www.python.org/) - 优雅的编程语言

---

## 🌟 Star History

如果这个项目对你有帮助，请给我们一个 ⭐️！

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/SystemMonitorPro&type=Date)](https://star-history.com/#yourusername/SystemMonitorPro&Date)

---

<div align="center">

**[⬆ 回到顶部](#systemmonitorpro-v20)**

Made with ❤️ by [Your Name]

© 2025 SystemMonitorPro. All rights reserved.

</div>