# 📊 DataVizPro - 专业数据分析与可视化平台

<div align="center">

**作者：LYP** | [GitHub](https://github.com/lyp0746) | [邮箱](mailto:1610369302@qq.com)

![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

**对标问卷星等专业数据分析软件的开源解决方案**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [使用指南](#-使用指南) • [截图展示](#-截图展示) • [贡献指南](#-贡献指南)

</div>

---

## 🎯 项目简介

**DataVizPro** 是一款基于 PyQt5 开发的现代化数据分析与可视化平台，提供专业级的数据处理、统计分析和图表可视化功能。无需编写代码，通过直观的图形界面即可完成复杂的数据分析任务。

### 🌟 核心优势

- 🚀 **零代码操作** - 纯图形界面，无需编程基础
- 💪 **功能强大** - 16+种图表类型，完整的数据处理流程
- 🎨 **界面精美** - 4种主题，现代化设计
- 📊 **专业级分析** - 对标问卷星、SPSS等专业软件
- 🔄 **实时预览** - 即改即看，快速迭代
- 💾 **多格式支持** - CSV、Excel、JSON、XML等
- 🌐 **交互式图表** - 支持 Plotly 交互式可视化
- 📑 **模板系统** - 内置常用分析模板

---

## ✨ 功能特性

### 📥 数据导入与管理

- ✅ 支持多种文件格式：CSV, Excel (.xlsx/.xls), JSON, XML, TXT
- ✅ 智能编码检测（UTF-8, GBK, GB2312等）
- ✅ 自动数据类型识别（数值、日期、分类）
- ✅ 大数据智能采样（支持百万级数据）
- ✅ 数据预览与实时统计信息

### 🧹 数据清洗工具

#### 缺失值处理
- 删除缺失行
- 均值/中位数/众数填充
- 前向/后向填充
- 插值填充
- 自定义值填充

#### 重复值处理
- 保留第一个/最后一个
- 全部删除

#### 异常值检测
- IQR（四分位距）方法
- Z-Score（标准分数）方法
- 数据截断（Clip）

#### 数据转换
- 类型转换（数值、日期、字符串、类别）
- 数据标准化（MinMax、Z-Score）
- 对数/开方转换

### 📊 16种图表类型

| 图表类型 | 说明 | 适用场景 |
|---------|------|---------|
| 📈 **折线图** | Line Chart | 趋势分析、时间序列 |
| 📊 **柱状图** | Bar Chart | 类别对比、排名 |
| 🥧 **饼图** | Pie Chart | 占比分析、构成 |
| ⚫ **散点图** | Scatter Plot | 相关性分析、分布 |
| 📉 **面积图** | Area Chart | 累积趋势、堆叠对比 |
| 🔥 **热力图** | Heatmap | 相关性矩阵、密度分布 |
| 📦 **箱线图** | Box Plot | 分布特征、异常值检测 |
| 🎻 **小提琴图** | Violin Plot | 分布形态、密度对比 |
| 📊 **直方图** | Histogram | 频数分布、正态性检验 |
| 🌊 **密度图** | Density Plot | 概率密度、分布拟合 |
| 🎯 **雷达图** | Radar Chart | 多维度对比 |
| 🔻 **漏斗图** | Funnel Chart | 转化分析、流程监控 |
| 🌳 **树状图** | Treemap | 层级结构、占比可视化 |
| 💧 **瀑布图** | Waterfall Chart | 累积效应、变化分解 |
| 🔀 **桑基图** | Sankey Diagram | 流量分析、路径可视化 |
| ☁️ **词云图** | Word Cloud | 文本分析、关键词提取 |

### 📈 统计分析

#### 描述性统计
- 均值、中位数、众数
- 标准差、方差
- 分位数（25%, 50%, 75%）
- 偏度、峰度
- 最大值、最小值
- 唯一值计数、缺失值统计

#### 相关性分析
- Pearson 相关系数
- Spearman 秩相关系数
- Kendall τ 相关系数
- 相关性热力图可视化

#### 频数分析
- 分类变量频数统计
- 交叉列联表
- 频率分布可视化

### 🎨 界面与主题

#### 4种精美主题
- 🌞 **浅色主题** - 清新明亮，适合长时间使用
- 🌙 **深色主题** - 护眼模式，降低视觉疲劳
- 💼 **专业蓝** - 商务风格，正式场合
- 🌿 **清新绿** - 自然清爽，舒适体验

#### 响应式设计
- 可调整分割面板
- 自适应窗口大小
- 全屏模式支持

### 🌐 交互式图表（Plotly）

- 🔍 缩放、平移、框选
- 💡 悬停提示详细信息
- 📥 导出高清图片
- 🎯 图例交互筛选
- 📊 数据表格查看

### 📑 分析模板

#### 内置5大模板
1. **基础数据探索** - 快速了解数据分布特征
2. **销售分析报告** - 销售数据全方位分析
3. **用户行为分析** - 用户画像与行为洞察
4. **问卷调查分析** - 问卷数据专业分析
5. **时间序列分析** - 趋势预测与季节性分解

### 💾 导出功能

#### 数据导出
- CSV 文件
- Excel 文件（.xlsx）
- JSON 文件

#### 图表保存
- PNG 图片（高清）
- JPEG 图片
- PDF 矢量图
- SVG 矢量图
- HTML 交互式网页

#### 分析报告
- HTML 网页报告
- Markdown 文档
- 自动生成统计摘要
- 图表嵌入报告

### ⚡ 其他特性

- 🔄 **撤销/重做** - 50步操作历史
- ⌨️ **快捷键支持** - 提高操作效率
- 📋 **数据复制** - 表格数据快速复制
- 🔍 **数据筛选** - Pandas 查询语法
- ⬍ **数据排序** - 多列排序支持
- 💡 **智能提示** - 操作引导与帮助

---

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- 操作系统：Windows / macOS / Linux

### 安装步骤

#### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/DataVizPro.git
cd DataVizPro
```

#### 2. 安装依赖

**基础依赖（必需）：**

```bash
pip install PyQt5 pandas numpy matplotlib seaborn openpyxl
```

**可选依赖（增强功能）：**

```bash
# 交互式图表支持
pip install plotly PyQtWebEngine

# 高级统计分析
pip install scipy scikit-learn

# 词云图支持
pip install wordcloud

# 一键安装所有依赖
pip install -r requirements.txt
```

#### 3. 运行程序

```bash
python DataVizPro.py
```

### Docker 部署（可选）

```bash
docker build -t datavizpro .
docker run -it --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix datavizpro
```

---

## 📖 使用指南

### 基础工作流程

#### 第1步：导入数据

1. 点击工具栏的 **📁 打开** 按钮
2. 或使用菜单：**文件 → 打开文件**
3. 选择支持的文件格式
4. 程序自动检测编码并加载数据

#### 第2步：数据清洗

1. 切换到 **🧹 数据清洗** 标签页
2. 根据需要选择清洗方法：
   - 处理缺失值
   - 删除重复行
   - 检测异常值
   - 转换数据类型
3. 点击对应的执行按钮

#### 第3步：探索分析

1. 切换到 **📈 统计分析** 标签页
2. 选择要分析的列
3. 查看描述性统计
4. 生成相关性矩阵

#### 第4步：可视化

1. 切换到 **📊 图表配置** 标签页
2. 选择图表类型
3. 设置数据映射：
   - X轴：选择横轴数据
   - Y轴：选择纵轴数据（可多选）
   - 分组：选择分组变量
4. 配置图表样式
5. 点击 **🎨 生成图表** 按钮

#### 第5步：导出结果

- **保存数据**：文件 → 保存数据
- **保存图表**：右键图表 → 保存图片
- **导出报告**：文件 → 导出报告

### 高级功能

#### 使用分析模板

1. 点击菜单：**工具 → 分析模板**
2. 选择适合的模板
3. 程序自动生成一系列图表

#### 交互式图表

1. 在图表配置页面设置好参数
2. 点击 **🌐 交互式图表** 按钮
3. 在新标签页中查看可交互的图表
4. 可缩放、悬停查看详情

#### 数据筛选

1. 点击菜单：**数据 → 筛选数据**
2. 输入 Pandas 查询语法，例如：
   ```python
   Age > 30 and City == 'Beijing'
   Price >= 100 and Price <= 500
   Category.isin(['A', 'B', 'C'])
   ```
3. 点击确定应用筛选

#### 撤销与重做

- 撤销：`Ctrl+Z` 或点击工具栏 **↶ 撤销**
- 重做：`Ctrl+Y` 或点击工具栏 **↷ 重做**
- 支持 50 步操作历史

---

## ⌨️ 快捷键列表

| 快捷键 | 功能 | 说明 |
|--------|------|------|
| `Ctrl+O` | 打开文件 | 导入数据文件 |
| `Ctrl+S` | 保存数据 | 导出当前数据 |
| `Ctrl+Z` | 撤销操作 | 回退上一步 |
| `Ctrl+Y` | 重做操作 | 前进下一步 |
| `Ctrl+C` | 复制 | 复制选中的表格数据 |
| `F5` | 刷新数据 | 重新加载数据显示 |
| `F11` | 全屏切换 | 进入/退出全屏模式 |
| `Ctrl+Q` | 退出程序 | 关闭应用 |

---

## 📸 截图展示

### 主界面
```
┌─────────────────────────────────────────────────────────────┐
│  DataVizPro 3.0 - 专业数据分析与可视化平台                    │
├─────────────────────────────────────────────────────────────┤
│  📁 打开  💾 保存  🔄 刷新  🔍 筛选  📈 统计  📊 图表        │
├─────────────────┬───────────────────────────────────────────┤
│                 │  📊 图表配置  🧹 数据清洗  📈 统计分析     │
│  📊 数据信息     │  ┌─────────────────────────────────────┐  │
│  ┌────────────┐ │  │  图表类型: [📈 折线图 ▼]              │  │
│  │ 行数: 1000 │ │  │  X轴: [日期 ▼]                       │  │
│  │ 列数: 15   │ │  │  Y轴: [销售额] [利润]                │  │
│  │ 缺失值: 23 │ │  │  标题: [月度销售趋势]                │  │
│  └────────────┘ │  │  [🎨 生成图表] [🌐 交互式]           │  │
│                 │  └─────────────────────────────────────┘  │
│  🔍 数据预览     │                                           │
│  ┌────────────┐ │  📊 图表显示                              │
│  │ 表格视图   │ │  ┌─────────────────────────────────────┐  │
│  │ 支持排序   │ │  │                                       │  │
│  │ 多列选择   │ │  │        📈 图表区域                    │  │
│  └────────────┘ │  │                                       │  │
│                 │  └─────────────────────────────────────┘  │
└─────────────────┴───────────────────────────────────────────┘
```

### 数据清洗界面
```
┌─────────────────────────────────────────────────┐
│  🧹 数据清洗                                     │
├─────────────────────────────────────────────────┤
│  ┌─ 缺失值处理 ────────────────────────────┐   │
│  │ 处理方法: [均值填充 ▼]                  │   │
│  │ 选择列: [☑ 年龄] [☑ 收入] [☐ 城市]     │   │
│  │ [执行缺失值处理]                         │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
│  ┌─ 重复值处理 ────────────────────────────┐   │
│  │ 保留策略: [保留第一个 ▼]                │   │
│  │ [删除重复行]                             │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
│  ┌─ 异常值处理 ────────────────────────────┐   │
│  │ 选择列: [销售额 ▼]                      │   │
│  │ 方法: [IQR方法 ▼]                       │   │
│  │ 阈值: [1.5]                              │   │
│  │ [处理异常值]                             │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### 图表类型展示
```
📈 折线图        📊 柱状图        🥧 饼图         ⚫ 散点图
📉 面积图        🔥 热力图        📦 箱线图       🎻 小提琴图
📊 直方图        🌊 密度图        🎯 雷达图       🔻 漏斗图
🌳 树状图        💧 瀑布图        🔀 桑基图       ☁️ 词云图
```

---

## 🛠️ 技术栈

### 核心框架
- **PyQt5** - GUI框架
- **Pandas** - 数据处理
- **NumPy** - 数值计算
- **Matplotlib** - 静态图表
- **Seaborn** - 统计图表

### 增强库
- **Plotly** - 交互式图表
- **SciPy** - 科学计算
- **OpenPyXL** - Excel支持
- **WordCloud** - 词云图

### 架构设计
```
DataVizPro/
├── DataImporter      # 数据导入器
├── DataCleaner       # 数据清洗器
├── StatisticalAnalyzer  # 统计分析器
├── ChartRenderer     # 图表渲染器
├── InteractiveChartRenderer  # 交互式图表渲染器
├── PandasTableModel  # 数据表格模型
└── MainWindow        # 主窗口
```

---

## 📊 性能指标

| 指标 | 数值 |
|------|------|
| 支持数据行数 | 1,000,000+ |
| 表格预览行数 | 1,000 |
| 图表绘制行数 | 500,000 |
| 操作历史步数 | 50 |
| 启动时间 | < 2秒 |
| 内存占用 | ~100MB（空载） |

---

## 🔧 配置文件

程序会在用户目录下创建配置文件夹：

```
~/.datavizpro/
├── templates/     # 自定义模板
├── cache/         # 缓存文件
└── logs/          # 日志文件
```

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 贡献方式

1. **提交 Bug 报告**
   - 使用 GitHub Issues
   - 详细描述问题和复现步骤
   - 附上截图或错误日志

2. **功能建议**
   - 在 Issues 中标记为 `enhancement`
   - 说明使用场景和预期效果

3. **代码贡献**
   ```bash
   # Fork 本仓库
   git clone https://github.com/yourusername/DataVizPro.git
   
   # 创建功能分支
   git checkout -b feature/amazing-feature
   
   # 提交更改
   git commit -m 'Add some amazing feature'
   
   # 推送到分支
   git push origin feature/amazing-feature
   
   # 创建 Pull Request
   ```

4. **文档改进**
   - 修正文档错误
   - 添加使用示例
   - 翻译成其他语言

### 开发规范

- 遵循 PEP 8 代码规范
- 添加必要的注释和文档字符串
- 编写单元测试
- 更新 CHANGELOG.md

---

## 📝 更新日志

### Version 3.0.0 (2025-12-12)

#### 🎉 新功能
- ✨ 全面 PyQt5 重构，现代化界面设计
- ✨ 新增 16+ 种图表类型
- ✨ 集成 Plotly 交互式图表
- ✨ 新增 5 大分析模板
- ✨ 支持 4 种主题切换
- ✨ 新增操作历史（撤销/重做）

#### 🔧 改进
- 🚀 优化大数据处理性能
- 🎨 重新设计用户界面
- 📊 增强图表配置选项
- 🧹 完善数据清洗工具
- 📈 扩展统计分析功能

#### 🐛 修复
- 修复文件编码检测问题
- 修复图表保存路径错误
- 修复内存泄漏问题
- 修复主题切换异常

---

## 📄 许可证

本项目采用 **MIT License** 开源许可证。

```
MIT License

Copyright (c) 2025 DataVizPro Team

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

## 📞 联系方式

- **项目主页**: https://github.com/yourusername/DataVizPro
- **问题反馈**: https://github.com/yourusername/DataVizPro/issues
- **电子邮件**: support@datavizpro.com
- **官方网站**: https://datavizpro.com

---

## 🙏 致谢

感谢以下开源项目：

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - 强大的 Python GUI 框架
- [Pandas](https://pandas.pydata.org/) - 数据分析基础库
- [Matplotlib](https://matplotlib.org/) - 数据可视化利器
- [Plotly](https://plotly.com/python/) - 交互式图表库
- [Seaborn](https://seaborn.pydata.org/) - 统计可视化增强

---

## ⭐ Star History

如果这个项目对你有帮助，请给我们一个 Star ⭐️

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/DataVizPro&type=Date)](https://star-history.com/#yourusername/DataVizPro&Date)

---

## 🗺️ 路线图

### 即将推出的功能

#### v3.1.0 (2025 Q1)
- [ ] 机器学习模块（回归、分类、聚类）
- [ ] SQL 数据库连接支持
- [ ] 自动化报告生成
- [ ] 图表动画效果

#### v3.2.0 (2025 Q2)
- [ ] 在线协作功能
- [ ] 云端数据存储
- [ ] 移动端 App
- [ ] 插件系统

#### v4.0.0 (2025 Q3)
- [ ] AI 智能分析助手
- [ ] 自然语言查询
- [ ] 自动图表推荐
- [ ] 实时数据流处理

---

## 💡 常见问题 (FAQ)

### Q1: 程序启动报错怎么办？

**A:** 请检查以下几点：
1. Python 版本是否 >= 3.8
2. 是否安装了所有必需依赖
3. 查看终端错误信息，根据提示安装缺失的库

### Q2: 支持哪些数据格式？

**A:** 支持以下格式：
- CSV (.csv)
- Excel (.xlsx, .xls)
- JSON (.json)
- XML (.xml)
- 文本文件 (.txt)

### Q3: 如何处理大数据文件？

**A:** 程序会自动处理：
- 表格预览限制在 1000 行
- 图表绘制自动采样
- 如果数据超过 50 万行，会随机采样绘图

### Q4: 交互式图表显示不出来？

**A:** 需要安装额外依赖：
```bash
pip install plotly PyQtWebEngine
```

### Q5: 如何自定义分析模板？

**A:** 可以修改代码中的模板方法，或者等待 v3.1.0 版本的插件系统。

### Q6: 支持中文吗？

**A:** 完全支持中文，包括：
- 中文界面
- 中文数据
- 中文图表标题和标签
- 中文文件名

### Q7: 可以商用吗？

**A:** 可以！本项目采用 MIT 许可证，允许商业使用。

---

<div align="center">

**Made with ❤️ by DataVizPro Team**

如果觉得有用，请给个 ⭐️ Star！

[⬆ 回到顶部](#-datavizpro---专业数据分析与可视化平台)

</div>