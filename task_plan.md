# 任务计划 — Anime Outfit Analyzer

**项目:** 动漫化穿搭分析桌面App
**创建日期:** 2026-07-07
**状态:** 规划中

---

## 阶段概览

| # | 阶段 | 状态 | 依赖 |
|---|------|------|------|
| 1 | 项目脚手架 + 基础UI | ⬜ 待开始 | - |
| 2 | 本地穿搭分析模块 | ⬜ 待开始 | 1 |
| 3 | 云端动漫化模块 | ⬜ 待开始 | 1 |
| 4 | 联网搜索 + 建议生成 | ⬜ 待开始 | 2 |
| 5 | 集成 + 完整流程 | ⬜ 待开始 | 2,3,4 |
| 6 | 测试 + 打包 | ⬜ 待开始 | 5 |

---

## 详细任务

### 阶段 1: 项目脚手架 + 基础UI
可并行: 1a, 1b (不同文件)

- [ ] **1a** — 项目初始化
  - 文件: `requirements.txt`, `settings.py`, `main.py`
  - 内容: 依赖声明(PyQt6, ultralytics, open-clip-torch, replicate, requests), 配置管理, 窗口入口
  - 验证: `python main.py` 弹出空白窗口

- [ ] **1b** — UI 面板搭建
  - 文件: `ui/main_window.py`, `ui/image_panel.py`, `ui/anime_panel.py`, `ui/outfit_panel.py`
  - 内容: 主窗口布局(左右分栏+底部分析区), 图片拖拽区, 动漫结果区, 穿搭分析区(空状态)
  - 验证: 窗口显示完整布局，图片可拖入并预览

### 阶段 2: 本地穿搭分析模块
顺序执行: 2a → 2b → 2c

- [ ] **2a** — 数据模型
  - 文件: `data/schema.py`
  - 内容: ClothingItem, OutfitAnalysis dataclass
  - 验证: 导入无报错，dataclass 可实例化

- [ ] **2b** — YOLO + CLIP 推理封装
  - 文件: `models/outfit_model.py`
  - 内容: 服装分割(YOLOv8-seg), 属性分类(CLIP), 模型下载管理
  - 验证: 给一张测试图，打印检测到的服装列表

- [ ] **2c** — OutfitWorker
  - 文件: `workers/outfit_worker.py`
  - 内容: QThread, 调用 outfit_model, 发信号更新 UI
  - 验证: UI 中加载图片 → 分析面板显示单品卡片

### 阶段 3: 云端动漫化模块
顺序执行: 3a → 3b

- [ ] **3a** — Replicate API 封装
  - 文件: `models/anime_client.py`
  - 内容: API 调用, 4种风格 LoRA 映射, 超时处理, 重试逻辑
  - 验证: 独立脚本调 API，返回动漫化图片 URL

- [ ] **3b** — AnimeWorker
  - 文件: `workers/anime_worker.py`
  - 内容: QThread, 调用 anime_client, 下载结果图, 发信号
  - 验证: UI 中选择风格 → 动漫化结果显示在右侧面板

### 阶段 4: 联网搜索 + 建议生成
顺序执行: 4a → 4b → 4c

- [ ] **4a** — 搜索 API 封装
  - 文件: `models/search_client.py`
  - 内容: SerpAPI/Bing API, 查询构造, 结果解析
  - 验证: 独立脚本搜 "黑色T恤 蓝色牛仔裤 搭配建议"，打印结果

- [ ] **4b** — 规则引擎打分
  - 文件: `models/scoring.py`
  - 内容: 4维度评分(配色/比例/层次/风格), 建议生成
  - 验证: 给定测试数据，打印评分 + 建议

- [ ] **4c** — SearchWorker
  - 文件: `workers/search_worker.py`
  - 内容: QThread, 调用搜索 + 评分, 发信号
  - 验证: 分析完成后底部面板显示评分 + 建议 + 参考链接

### 阶段 5: 集成
顺序执行: 5a → 5b

- [ ] **5a** — 完整流程串联
  - 文件: `ui/main_window.py` (更新)
  - 内容: 三个 Worker 并行调度, 结果汇总, 导出按钮逻辑
  - 验证: 加载图片 → 一键分析 → 三个区域均有结果

- [ ] **5b** — 设置页面
  - 文件: `ui/settings_dialog.py`
  - 内容: API Key 配置, 默认风格, 缓存路径, 导出格式
  - 验证: 设置保存重启后生效

### 阶段 6: 测试 + 打包
可并行: 6a, 6b

- [ ] **6a** — 功能测试
  - 测试: 常规穿搭图 / 多人图 / 无人物图 / 模糊图 / API断网模拟
  - 验证: 所有错误场景有友好提示

- [ ] **6b** — Windows 打包
  - 工具: PyInstaller
  - 输出: 单个 .exe
  - 验证: 另一台机器运行 .exe 正常工作

---

## 决策记录

| # | 决策 | 理由 | 日期 |
|---|------|------|------|
| 1 | Python + PyQt6 | 用户熟悉，AI集成方便 | 2026-07-07 |
| 2 | 穿搭本地、动漫云端 | 本地快省成本，SD需GPU | 2026-07-07 |
| 3 | 规则引擎打分 | 比LLM简单，无额外API成本 | 2026-07-07 |
| 4 | 单体架构 | 单人工具，无需微服务 | 2026-07-07 |
