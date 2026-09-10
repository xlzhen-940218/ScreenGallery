# Software Requirements Specification (SRS) / Agent Execution Spec

## 1. 项目概述 (Project Overview)
- **项目名称**：Cross-Platform Smart Digital Photo Frame (跨平台智能电子相框)
- **技术栈**：Python 3.10+, PyQt6 / PySide6, QSS (Qt Style Sheets)
- **目标平台**：Windows, Linux, macOS (跨平台支持)
- **受众对象**：Autonomous AI Agent / 开发工程师。请根据本规范逐步设计、编写并交付完整工程。

---

## 2. 核心系统特性 (System & Environment Requirements)

### 2.1 全屏与防休眠 / 防锁屏 (Fullscreen & Keep-Awake)
- **全屏覆盖**：
  - 启动默认无边框全屏模式 (`showFullScreen()`)，隐藏标题栏与任务栏。
  - 提供退出机制（如快捷键 `Esc` 或双击特定隐蔽区域弹出退出/设置面板）。
- **跨平台防锁屏/防休眠机制**：
  - **Windows**：调用 Win32 API `ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_DISPLAY_REQUIRED | ES_SYSTEM_REQUIRED)`。
  - **Linux (X11 / Wayland)**：通过 `dbus` 调用 FreeDesktop ScreenSaver 接口抑制锁屏（`org.freedesktop.ScreenSaver.Inhibit`），或使用 `xdotool` / `systemd-inhibit`。
  - **macOS**：利用 `caffeinate` 进程或调用 IOKit `IOPMAssertionCreateWithName` 防止屏幕休眠。
  - 需在程序退出时优雅注销/恢复电源状态。

### 2.2 现代化视觉与高DPI缩放 (UI Polish & High-DPI Support)
- **High-DPI 适配**：
  - 显式配置 Qt 高分屏环境变量：
    ```python
    import os
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    ```
  - 使用相对单位或动态缩放基准，确保在 100%、125%、150%、200% 等缩放下布局不挤压、字体不发糊。
- **界面美学与视觉风格**：
  - 采用现代磨砂玻璃/暗黑质感设计风格（Dark Mode + 半透明卡片背景 + 细微边框发光/阴影效果）。
  - 卡片圆角统一（建议 `border-radius: 16px`），布局层次分明。
  - 动效平滑：图片轮播淡入淡出、圆环进度条平滑缓动动画、任务完成划线过渡。

---

## 3. 架构与布局规划 (Modular Architecture & Layout)

### 3.1 模块化网格布局 (Grid / Dashboard Layout)
建议采用 16:9 响应式仪表盘网格划分：
- **主展示区（占屏幕 60%~65% 面积）**：
  - 模块 1：电子相册（轮播展示，沉浸式视觉焦点）。
- **侧边控制台/挂件区（占屏幕 35%~40% 面积）**：
  - 顶部/右上：系统资源占用监控（CPU & 内存双环仪表盘）。
  - 中部：今日备忘录列表（Today's Priority Tasks）。
  - 底部/右下：月历视图（Month Calendar）与日期交互。

---

## 4. 详细模块规格 (Module Specifications)

### 模块 1：电子相册轮播 (Photo Gallery Carousel)
1. **文件夹配置**：
   - 默认读取配置中的图片目录（支持 `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`）。
   - 若目录为空或不存在，展示精美的默认背景图或占位提示。
2. **轮播机制**：
   - 支持自动定时切换（默认可配置，如每隔 10~30 秒）。
   - 切换动画采用平滑渐变（`QGraphicsOpacityEffect` + `QPropertyAnimation` 实现 cross-fade 交叉淡入淡出）。
   - 图片按比例缩放适配容器（`Qt.AspectRatioMode.KeepAspectRatioByExpanding` 或 `KeepAspectRatio`），边缘居中裁剪或磨砂模糊背景填充。

### 模块 2：月历与备忘录管理 (Month Calendar & Memo Modal)
1. **按月展示视图**：
   - 自定义或美化 `QCalendarWidget`，与整体暗黑/透明毛玻璃主题融为一体。
   - 高亮当天日期；若某天存在未完成备忘录，日期下方显示微小的状态指示点（Dot Indicator）。
2. **交互行为**：
   - 单击具体日期：弹出对话框（`MemoDialog`），展示该选定日期的任务详情，并支持新建任务。
3. **备忘录属性定义**：
   - 任务ID (`id`)
   - 日期 (`date`: YYYY-MM-DD)
   - 标题/内容 (`text`: str)
   - 优先级 (`priority`: `HIGH` (重点任务) | `NORMAL` (普通任务))
   - 完成状态 (`is_completed`: bool)
   - 创建时间 (`created_at`: timestamp)
4. **数据持久化**：
   - 采用轻量本地 SQLite 数据库或 JSON 文件（`data/memos.json`）存储，确保关闭后不丢失。

### 模块 3：今日备忘录列表 (Today's Tasks Dashboard)
1. **数据源**：实时过滤当天日期（`date == today`）的备忘录。
2. **排序规则**：
   - **第一优先级**：未完成任务排在已完成任务前面。
   - **第二优先级**：未完成任务中，重点任务（Priority High）排在普通任务（Priority Normal）前面。
   - **第三优先级**：同等优先级下按创建时间先后排列。
3. **视觉与交互**：
   - 重点任务：带有高亮徽标（如红色/橙色标签或星标）、卡片边框高光。
   - 普通任务：常规中性色彩展示。
   - 事项右侧设置完成复选框/按钮（Check Icon）。
   - **点击完成操作**：
     - 文字中间添加删除线（Strike-through: `text-decoration: line-through` 或 `font.setStrikeOut(True)`）。
     - 字体颜色降噪变灰。
     - 触发重新排序动画，平滑滑动重排至列表底部。

### 模块 4：CPU 与内存占用监控 (System Resource Donut Meters)
1. **数据采集**：
   - 使用 `psutil` 库周期性采集（建议刷新周期 1.5s ~ 2.0s，避免过度占用 CPU）。
   - 后台采用 `QThread` 或 `QTimer` 异步刷新，避免阻塞 UI 线程。
2. **环形进度条组件 (Custom Donut/Circular Gauge)**：
   - 继承自 `QWidget`，重写 `paintEvent`，使用 `QPainter` 与 `QPainterPath` 绘制。
   - 渲染双环结构（CPU 使用率环、RAM 内存使用率环），或两个并列的独立环形图。
   - **视觉设计**：
     - 底环：低饱和度半透明圆环轨道。
     - 进度环：平滑渐变色弧线（如 CPU 蓝紫渐变，内存青绿渐变；当占用率 > 85% 时动态变红警示）。
     - 中心文字：居中绘制百分比数值（大字体）及指标名称标签（小字体）。
     - 启用抗锯齿：`painter.setRenderHint(QPainter.RenderHint.Antialiasing)`。

---

## 5. Agent 任务分解与执行路线 (Task Breakdown for Agent)

- [ ] **Task 1: 环境与依赖初始化**
  - 创建虚拟环境配置 `requirements.txt`：`PyQt6>=6.5.0`, `psutil>=5.9.0`, `qtawesome`（可选图标库）。
- [ ] **Task 2: 电源管理与屏幕常亮工具实现 (`utils/power.py`)**
  - 封装针对 Windows/Linux/macOS 的防熄屏/防锁屏与恢复上下文管理器。
- [ ] **Task 3: 数据持久层与备忘录模型 (`models/memo_manager.py`)**
  - 实现 SQLite 或 JSON 本地 CRUD 操作，提供排序与过滤接口。
- [ ] **Task 4: 自定义圆环进度条控件 (`widgets/circular_gauge.py`)**
  - 实现 `CircularProgressBar`，支持平滑插值动画、渐变色渲染与参数配置。
- [ ] **Task 5: 核心业务组件开发**
  - `PhotoWidget`：相册扫描、自适应展示、平滑渐变轮播。
  - `CalendarWidget`：带任务小红点的月历、日期点击事件绑定。
  - `MemoListWidget`：今日待办、高亮权重排序、一键完成划线置底动效。
- [ ] **Task 6: 弹窗与交互设计 (`dialogs/memo_dialog.py`)**
  - 创建备忘录编辑对话框，支持设置重点/普通等级与删除管理。
- [ ] **Task 7: 主窗口与仪表盘装配 (`main_window.py`)**
  - 组合所有模块，引入 QSS 美化，绑定 DPI 自适应与全屏热键。
- [ ] **Task 8: 测试与跨平台验证**
  - 验证多分辨率下的缩放布局、无图片时的 Fallback 处理、长时间运行内存泄漏情况。
