# AutomationToolPro v2.0 - PyQt5专业自动化工具

<div align="center">

**作者：LYP** | [GitHub](https://github.com/lyp0746) | [邮箱](mailto:1610369302@qq.com)

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

**功能强大的跨平台自动化工具集 | 提升工作效率的利器**

[功能特性](#功能特性) • [安装说明](#安装说明) • [使用指南](#使用指南) • [截图展示](#截图展示) • [常见问题](#常见问题)

</div>

---

## 📋 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [系统要求](#系统要求)
- [安装说明](#安装说明)
- [快速开始](#快速开始)
- [详细使用指南](#详细使用指南)
- [配置文件](#配置文件)
- [常见问题](#常见问题)
- [更新日志](#更新日志)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## 🎯 项目简介

**AutomationToolPro** 是一款基于 PyQt5 开发的专业级自动化工具平台，集成了8大核心功能模块，旨在帮助用户自动化日常重复性任务，提高工作效率。

### 为什么选择 AutomationToolPro？

- ✅ **全功能集成** - 8大模块满足各种自动化需求
- ✅ **界面友好** - 现代化UI设计，操作简单直观
- ✅ **高度可配置** - 灵活的配置选项，适应各种场景
- ✅ **稳定可靠** - 完善的错误处理和日志记录
- ✅ **跨平台支持** - Windows、Linux、macOS全平台兼容
- ✅ **开源免费** - MIT许可证，完全免费使用

---

## 🚀 功能特性

### 1️⃣ 定时任务调度 ⏰

自动执行周期性任务，支持多种动作类型。

**核心功能：**
- ⚙️ 灵活的时间间隔设置（秒级精度）
- 📢 消息提醒功能
- 💻 系统命令执行
- 🌐 自动打开网页
- 🐍 Python脚本执行
- 📊 任务运行统计
- ▶️ 手动立即执行
- ⏸️ 启用/暂停控制

**使用场景：**
- 定时备份数据
- 定期清理临时文件
- 按时发送提醒
- 定时采集数据
- 自动重启服务

---

### 2️⃣ 文件监控系统 📁

实时监控文件变化，自动触发处理动作。

**核心功能：**
- 👁️ 实时文件监控
- 🔍 支持通配符过滤（*.txt, *.pdf等）
- 📂 递归子目录监控
- 🚫 隐藏文件过滤
- 📋 多种处理动作：
  - 复制文件到指定位置
  - 移动文件到目标目录
  - 自动删除匹配文件
  - 执行自定义命令
  - 压缩文件为ZIP
- 📝 详细监控日志
- 📈 触发次数统计

**使用场景：**
- 下载文件自动归档
- 文档自动备份
- 日志文件自动压缩
- 新文件自动处理
- 文件变化触发脚本

---

### 3️⃣ 网页自动化 🌐

无需编程，可视化创建网页自动化脚本。

**核心功能：**
- 🎬 动作序列编辑器
- 🖱️ 支持的动作类型：
  - 点击元素（CSS选择器）
  - 输入文本内容
  - 等待指定时间
  - 页面截图保存
  - 执行JavaScript代码
- ⬆️⬇️ 动作顺序调整
- ⏱️ 超时控制
- 🔄 重试机制
- 📊 执行统计

**使用场景：**
- 自动登录网站
- 表单自动填写
- 数据批量提交
- 网页定时截图
- 网站功能测试

---

### 4️⃣ 宏录制与回放 🎮

录制鼠标键盘操作，自动重复执行。

**核心功能：**
- ⏺️ 一键开始录制
- 🎯 支持的事件：
  - 鼠标左键点击
  - 鼠标右键点击
  - 键盘输入
  - 鼠标移动
  - 延时等待
- 💾 保存录制内容
- ▶️ 精确回放操作
- 📤📥 导入导出宏文件
- 📝 宏描述和备注
- 📊 播放次数统计

**使用场景：**
- 重复性操作自动化
- 游戏辅助工具
- 软件测试录制
- 演示流程录制
- 批量操作执行

---

### 5️⃣ API接口测试 🔌

专业的API测试工具，支持完整的HTTP请求。

**核心功能：**
- 🌐 支持所有HTTP方法（GET/POST/PUT/DELETE/PATCH）
- 📋 自定义请求头（Headers）
- 📦 请求体编辑（JSON格式）
- ✅ 响应状态验证
- ⏱️ 响应时间统计
- 🔄 批量测试执行
- 📊 成功率统计
- 💾 测试结果保存
- 📝 详细响应日志

**使用场景：**
- API接口测试
- 接口性能监控
- 自动化测试
- 接口文档验证
- 服务健康检查

---

### 6️⃣ 数据同步 🔄

智能的文件同步解决方案，支持多种同步模式。

**核心功能：**
- 🔀 三种同步模式：
  - **Mirror** - 镜像同步，完全一致
  - **Sync** - 增量同步，只复制新文件
  - **Backup** - 备份模式，保留所有版本
- 🚫 排除模式支持（.git, *.tmp等）
- 📊 实时进度显示
- 📈 文件统计（新增/更新/删除）
- 📝 详细同步日志
- ⏱️ 同步历史记录

**使用场景：**
- 文件夹自动备份
- 项目文件同步
- 多设备数据同步
- 网站文件部署
- 定期归档备份

---

### 7️⃣ 系统监控 📊

实时监控系统资源使用情况。

**核心功能：**
- 💻 CPU使用率监控
- 🧠 内存使用统计
- 💾 磁盘空间监控
- 🌐 网络流量统计
- 📋 进程列表显示（Top 10）
- 📈 实时数据更新（2秒刷新）
- 📊 可视化卡片展示
- ℹ️ 系统信息汇总

**监控指标：**
- CPU使用百分比
- 内存已用/总量
- 磁盘已用/总量
- 网络发送/接收流量
- 当前进程数量
- 进程CPU/内存占用

---

### 8️⃣ 日志管理 📝

完善的日志系统，记录所有操作。

**核心功能：**
- 📊 多级别日志（信息/警告/错误/成功）
- 🎨 彩色日志显示
- 🔍 日志搜索过滤
- 📁 分类日志展示
- 💾 日志文件自动保存
- 📤 日志导出功能
- 🗑️ 日志清理功能
- 📈 日志统计计数
- 🔄 自动滚动选项

---

## 💻 系统要求

### 最低配置

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 7+ / Linux (Ubuntu 16.04+) / macOS 10.12+ |
| Python版本 | Python 3.7 或更高 |
| 内存 | 2GB RAM |
| 磁盘空间 | 100MB 可用空间 |
| 显示器 | 1280x720 分辨率 |

### 推荐配置

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10/11 / Ubuntu 20.04+ / macOS 11+ |
| Python版本 | Python 3.9+ |
| 内存 | 4GB+ RAM |
| 磁盘空间 | 500MB 可用空间 |
| 显示器 | 1920x1080 分辨率 |

---

## 📦 安装说明

### 方法一：使用 pip 安装依赖

```bash
# 1. 克隆或下载项目
git clone https://github.com/yourusername/AutomationToolPro.git
cd AutomationToolPro

# 2. 安装依赖
pip install PyQt5 psutil

# 3. 运行程序
python automation_tool_pro.py
```

### 方法二：使用虚拟环境（推荐）

```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行程序
python automation_tool_pro.py
```

### requirements.txt

```text
PyQt5>=5.15.0
psutil>=5.8.0
```

---

## 🎬 快速开始

### 第一次使用

1. **启动程序**
   ```bash
   python automation_tool_pro.py
   ```

2. **界面概览**
   - 顶部：工具栏（快速操作按钮）
   - 中间：8个功能标签页
   - 底部：状态栏（显示系统状态）
   - 右下角：系统托盘图标

3. **创建第一个定时任务**
   - 切换到"⏰ 定时任务"标签
   - 点击"➕ 添加任务"
   - 填写任务信息：
     - 名称：每小时提醒
     - 间隔：3600秒
     - 动作：message
     - 参数：休息一下，喝杯水！
   - 点击"确定"保存

4. **任务将自动开始运行**
   - 查看"下次运行"时间
   - 双击任务可暂停/启动
   - 查看"📝 日志"标签的执行记录

---

## 📖 详细使用指南

### 定时任务使用

#### 创建消息提醒任务

```
名称：工作提醒
间隔：1800（30分钟）
动作类型：message
动作参数：该起来活动一下了！
```

#### 创建定时备份任务

```
名称：文档备份
间隔：3600（1小时）
动作类型：command
动作参数：xcopy "C:\Documents" "D:\Backup" /E /Y
```

#### 创建定时打开网页

```
名称：新闻浏览
间隔：7200（2小时）
动作类型：url
动作参数：https://news.example.com
```

#### 创建Python脚本执行

```
名称：数据处理
间隔：600（10分钟）
动作类型：script
动作参数：
import os
print("执行数据处理...")
# 你的Python代码
```

---

### 文件监控使用

#### 下载文件自动归档

```
监控名称：下载归档
监控路径：C:\Users\YourName\Downloads
文件模式：*.pdf
执行动作：copy
目标路径：D:\Documents\PDFs
递归监控：否
忽略隐藏：是
```

#### 日志文件自动压缩

```
监控名称：日志压缩
监控路径：C:\AppLogs
文件模式：*.log
执行动作：compress
目标路径：D:\Backup\Logs
递归监控：是
忽略隐藏：是
```

#### 临时文件自动清理

```
监控名称：临时清理
监控路径：C:\Temp
文件模式：*.tmp
执行动作：delete
目标路径：（留空）
递归监控：是
忽略隐藏：否
```

---

### 网页自动化使用

#### 自动登录示例

```
脚本名称：网站自动登录
起始URL：https://example.com/login
超时时间：30秒

动作序列：
1. [input] #username -> myusername
2. [input] #password -> mypassword
3. [click] #login-button
4. [wait] 等待3秒
5. [screenshot] 保存路径: login_success.png
```

#### 表单自动填写

```
脚本名称：表单填写
起始URL：https://example.com/form
超时时间：30秒

动作序列：
1. [input] #name -> 张三
2. [input] #email -> zhangsan@example.com
3. [input] #phone -> 13800138000
4. [click] .submit-button
5. [wait] 等待2秒
```

---

### API测试使用

#### GET请求测试

```
测试名称：获取用户列表
方法：GET
URL：https://api.example.com/users

Headers：
Authorization: Bearer your_token_here
Content-Type: application/json

Body：（GET请求留空）

期望状态码：200
超时时间：30秒
```

#### POST请求测试

```
测试名称：创建用户
方法：POST
URL：https://api.example.com/users

Headers：
Authorization: Bearer your_token_here
Content-Type: application/json

Body：
{
  "name": "张三",
  "email": "zhangsan@example.com",
  "age": 25
}

期望状态码：201
超时时间：30秒
```

---

### 数据同步使用

#### 镜像同步（完全一致）

```
任务名称：项目同步
源路径：D:\Projects\MyApp
目标路径：E:\Backup\MyApp
同步模式：mirror
排除模式：
node_modules
.git
*.log
__pycache__
```

#### 增量同步（只同步新文件）

```
任务名称：文档增量同步
源路径：C:\Documents
目标路径：D:\Backup\Documents
同步模式：sync
排除模式：
~$*
*.tmp
.DS_Store
```

---

## ⚙️ 配置文件

### 自动保存的配置文件

程序会自动创建以下配置文件：

```
automation_pro_config.json    # 主配置文件
automation_pro.log            # 日志文件
macros.json                   # 宏数据
api_tests.json                # API测试数据
sync_tasks.json               # 同步任务数据
```

### 配置文件格式

**automation_pro_config.json** 示例：

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "id": "abc123",
      "name": "每小时提醒",
      "interval": 3600,
      "action_type": "message",
      "action_param": "休息一下",
      "enabled": true,
      "last_run": 1234567890.0,
      "next_run": 1234571490.0,
      "run_count": 5,
      "status": "就绪"
    }
  ],
  "monitors": [...],
  "api_tests": [...],
  "sync_tasks": [...],
  "macros": [...]
}
```

### 手动编辑配置

1. 退出程序
2. 使用文本编辑器打开 `automation_pro_config.json`
3. 修改配置（注意JSON格式）
4. 保存文件
5. 重新启动程序

---

## 🎨 界面说明

### 工具栏按钮

| 按钮 | 功能 | 说明 |
|------|------|------|
| ▶️ 启动所有 | 启动所有服务 | 开始任务调度和文件监控 |
| ⏸️ 暂停所有 | 暂停所有服务 | 临时停止所有自动化任务 |
| 💾 保存配置 | 保存当前配置 | 手动保存所有设置 |
| 📂 加载配置 | 加载配置文件 | 从文件恢复配置 |
| 📤 导出日志 | 导出日志文件 | 保存日志到文本文件 |
| 🗑️ 清空日志 | 清空所有日志 | 删除当前显示的日志 |
| ℹ️ 关于 | 显示关于信息 | 查看版本和功能说明 |

### 状态栏信息

| 项目 | 说明 |
|------|------|
| 就绪/运行中 | 当前程序状态 |
| 任务: X/Y | 启用任务数/总任务数 |
| 监控: X/Y | 启用监控数/总监控数 |
| CPU: X% | CPU使用率 |
| 内存: X% | 内存使用率 |

### 系统托盘

- **左键双击**：显示/隐藏主窗口
- **右键菜单**：
  - 显示主窗口
  - 退出程序

---

## ❓ 常见问题

### 1. 程序无法启动？

**问题**：双击运行无反应或报错

**解决方案**：
```bash
# 检查Python版本
python --version  # 应该 >= 3.7

# 检查依赖是否安装
pip list | grep PyQt5
pip list | grep psutil

# 重新安装依赖
pip install --upgrade PyQt5 psutil

# 查看详细错误
python automation_tool_pro.py
```

---

### 2. 定时任务不执行？

**问题**：创建的任务不运行

**检查清单**：
- ✅ 任务是否已启用（状态显示"✅ 启用"）
- ✅ 点击"▶️ 启动所有"按钮
- ✅ 检查"下次运行"时间是否正确
- ✅ 查看日志是否有错误信息
- ✅ 任务参数是否正确

**手动测试**：
- 选中任务，点击"▶️ 立即执行"
- 查看日志输出的执行结果

---

### 3. 文件监控不触发？

**问题**：文件变化但没有执行动作

**检查清单**：
- ✅ 监控路径是否存在
- ✅ 文件模式是否匹配（*.txt匹配.txt文件）
- ✅ 监控是否已启用
- ✅ 目标路径是否正确（对于copy/move动作）
- ✅ 是否有足够的文件权限

**调试方法**：
```bash
# 检查路径
import os
print(os.path.exists("你的监控路径"))

# 测试文件模式
from pathlib import Path
files = list(Path("监控路径").glob("*.txt"))
print(files)
```

---

### 4. API测试失败？

**问题**：API请求返回错误

**常见原因**：
- ❌ URL格式错误
- ❌ Headers格式不正确
- ❌ 请求体JSON格式错误
- ❌ 网络连接问题
- ❌ 服务器拒绝请求

**解决方案**：
```
1. 检查URL是否完整（包含http://或https://）
2. Headers格式：
   正确：Content-Type: application/json
   错误：Content-Type = application/json

3. Body检查：
   使用JSON验证工具检查格式
   确保是有效的JSON

4. 测试网络：
   ping api.example.com
   curl https://api.example.com
```

---

### 5. 数据同步卡住？

**问题**：同步进度条不动

**可能原因**：
- 📁 文件数量太多
- 💾 磁盘空间不足
- 🔒 文件被占用
- 🚫 权限不足

**解决方案**：
```bash
# 检查磁盘空间
# Windows: 
dir 目标路径

# Linux/macOS:
df -h

# 检查文件权限
# Windows: 右键→属性→安全
# Linux/macOS: ls -la 路径
```

---

### 6. 宏录制无法保存？

**问题**：停止录制后无法保存

**检查**：
- ✅ 是否点击了"⏹️ 停止录制"
- ✅ 是否输入了宏名称
- ✅ 是否有录制任何事件

**注意**：
- 至少录制一个事件才能保存
- 名称不能为空
- 不能与已有宏同名

---

### 7. 系统监控数据不准确？

**问题**：CPU/内存显示异常

**说明**：
- 数据每2秒刷新一次
- CPU百分比为瞬时值，可能波动较大
- 某些系统可能需要管理员权限

**提升准确性**：
```bash
# Windows: 以管理员身份运行
# Linux: sudo python automation_tool_pro.py
# macOS: sudo python automation_tool_pro.py
```

---

### 8. 配置文件损坏？

**问题**：程序启动报错"配置文件损坏"

**解决方案**：
```bash
# 1. 备份当前配置
cp automation_pro_config.json automation_pro_config.json.bak

# 2. 删除损坏的配置
rm automation_pro_config.json

# 3. 重新启动程序（会创建新配置）
python automation_tool_pro.py

# 4. 如果需要恢复，尝试修复JSON格式
# 使用在线JSON验证工具检查格式
```

---

### 9. 中文显示乱码？

**问题**：界面或日志中文显示为乱码

**解决方案**：
```bash
# Windows:
# 1. 确保系统区域设置为中文
# 2. CMD使用UTF-8编码
chcp 65001

# Linux/macOS:
# 确保locale设置正确
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8
```

---

### 10. 如何完全卸载？

**步骤**：
```bash
# 1. 删除程序目录
rm -rf AutomationToolPro/

# 2. 删除配置文件（如果需要）
rm automation_pro_config.json
rm automation_pro.log
rm macros.json
rm api_tests.json
rm sync_tasks.json

# 3. 卸载Python依赖（可选）
pip uninstall PyQt5 psutil
```

---

## 📝 更新日志

### v2.0.0 (2024-01-XX)

**🎉 重大更新**
- ✨ 完全重构，基于PyQt5开发
- ✨ 全新现代化UI设计
- ✨ 新增8大核心功能模块

**新功能**
- ➕ 定时任务调度系统
- ➕ 文件监控与自动处理
- ➕ 网页自动化脚本
- ➕ 宏录制与回放
- ➕ API接口测试工具
- ➕ 数据同步功能
- ➕ 系统资源监控
- ➕ 完整日志管理系统

**改进**
- 🚀 性能优化，多线程处理
- 🎨 界面美化，用户体验提升
- 📊 增加实时状态显示
- 💾 自动配置保存/加载
- 🔔 系统托盘支持
- 📝 详细操作日志

---

### v1.0.0 (2023-XX-XX)

**首次发布**
- 🎉 基础自动化功能
- 📋 简单任务管理
- 📝 基本日志功能

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献

1. **Fork 项目**
   ```bash
   # 在GitHub上点击Fork按钮
   ```

2. **创建特性分支**
   ```bash
   git checkout -b feature/AmazingFeature
   ```

3. **提交更改**
   ```bash
   git commit -m '添加某个很棒的功能'
   ```

4. **推送到分支**
   ```bash
   git push origin feature/AmazingFeature
   ```

5. **开启Pull Request**

### 贡献类型

- 🐛 **Bug修复**：发现并修复问题
- ✨ **新功能**：添加新的功能特性
- 📝 **文档**：改进文档和示例
- 🎨 **UI改进**：界面优化和美化
- ⚡ **性能**：性能优化
- 🌍 **国际化**：添加语言支持

### 代码规范

- 遵循PEP 8 Python代码规范
- 添加必要的注释和文档字符串
- 保持代码简洁清晰
- 编写单元测试

---

## 📄 许可证

本项目采用 **MIT License** 许可证。

```
MIT License

Copyright (c) 2024 AutomationToolPro

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

- **项目主页**: https://github.com/yourusername/AutomationToolPro
- **问题反馈**: https://github.com/yourusername/AutomationToolPro/issues
- **邮件**: your.email@example.com
- **QQ群**: 123456789

---

## 🌟 支持项目

如果这个项目对你有帮助，请考虑：

- ⭐ 给项目点个Star
- 🐛 报告Bug和建议
- 📖 完善文档
- 💻 贡献代码
- 📢 分享给朋友

---

## 🙏 致谢

感谢以下开源项目：

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - 强大的GUI框架
- [psutil](https://github.com/giampaolo/psutil) - 系统监控库
- [Python](https://www.python.org/) - 优秀的编程语言

---

## 📚 相关资源

### 官方文档
- [PyQt5文档](https://doc.qt.io/qtforpython/)
- [Python官方文档](https://docs.python.org/3/)

### 教程推荐
- [PyQt5入门教程](https://www.tutorialspoint.com/pyqt5/)
- [Python自动化教程](https://automatetheboringstuff.com/)

### 相关工具
- [Qt Designer](https://doc.qt.io/qt-5/qtdesigner-manual.html) - UI设计工具
- [pyinstaller](https://www.pyinstaller.org/) - 打包工具

---

<div align="center">

**Made with ❤️ by AutomationToolPro Team**

[⬆ 回到顶部](#automationtoolpro-v20---pyqt5专业自动化工具)

</div>