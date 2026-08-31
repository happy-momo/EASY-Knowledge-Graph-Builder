# KG AI Builder 🧠 → 🕸️

<p align="center">
  <strong>从文本到知识图谱的智能转换 — AI 驱动的知识图谱构建工具</strong>
</p>

<p align="center">
  <a href="https://github.com/happy-momo/EASY-Knowledge-Graph-Builder/stargazers">
    <img src="https://img.shields.io/github/stars/happy-momo/EASY-Knowledge-Graph-Builder?style=flat-square&logo=github" alt="GitHub stars">
  </a>
  <a href="https://github.com/happy-momo/EASY-Knowledge-Graph-Builder/network">
    <img src="https://img.shields.io/github/forks/happy-momo/EASY-Knowledge-Graph-Builder?style=flat-square&logo=github" alt="GitHub forks">
  </a>
  <a href="https://github.com/happy-momo/EASY-Knowledge-Graph-Builder/issues">
    <img src="https://img.shields.io/github/issues/happy-momo/EASY-Knowledge-Graph-Builder?style=flat-square&logo=github" alt="GitHub issues">
  </a>
  <a href="https://hub.docker.com/r/neo4j">
    <img src="https://img.shields.io/badge/Neo4j-5.13-4581C3?style=flat-square&logo=neo4j" alt="Neo4j">
  </a>
  <a href="https://streamlit.io">
    <img src="https://img.shields.io/badge/Streamlit-1.32-FF4B4B?style=flat-square&logo=streamlit" alt="Streamlit">
  </a>
  <a href="https://www.python.org">
    <img src="https://img.shields.io/badge/Python-3.10-3776AB?style=flat-square&logo=python" alt="Python">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License">
  </a>
  <a href="README.md">
    <img src="https://img.shields.io/badge/Language-English-blue?style=flat-square" alt="English">
  </a>
</p>

---

## 📋 目录

- [项目简介](#-项目简介)
- [功能特点](#-功能特点)
- [架构概览](#-架构概览)
- [快速开始](#-快速开始)
- [配置指南](#-配置指南)
- [使用指南](#-使用指南)
- [项目结构](#-项目结构)
- [开发指南](#-开发指南)
- [常见问题](#-常见问题)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)

---

## 📖 项目简介

**KG AI Builder** 是一个强大的 AI 驱动知识图谱构建工具，能够将非结构化文本（如 PDF、Word、Excel、TXT 文档）自动转换为结构化的知识图谱。通过结合大语言模型（LLM）的文本理解能力和 Neo4j 图数据库的存储优势，实现从原始文本到语义网络的自动化转换。

无论是科研文献分析、企业文档管理，还是知识库构建，KG AI Builder 都能帮助您快速、高效地从海量文本中提取有价值的结构化知识。

---

## ✨ 功能特点

| 功能 | 说明 |
|------|------|
| 🎯 **多模型支持** | 兼容智谱AI GLM、OpenAI GPT、Anthropic Claude、Google Gemini、阿里云通义千问、DeepSeek 等主流 LLM |
| 🚀 **一键部署** | 提供 Docker Compose 配置，一条命令即可启动完整服务（含 Neo4j 数据库） |
| 📊 **可视化界面** | 基于 Streamlit 构建的直观 Web 界面，步骤式引导，操作简单 |
| 📚 **多格式文档** | 支持 PDF、DOCX、XLSX、TXT 格式，单文件或文件夹批量导入 |
| 🔗 **智能抽取** | 自动从文本中提取实体、关系和属性，构建 RDF 三元组 |
| 📝 **Schema 定义** | 支持预设模板、YAML 上传、手动输入三种方式定义本体 Schema |
| 🗄️ **Neo4j 集成** | 与 Neo4j 图数据库无缝集成，支持图结构可视化浏览 |
| ⚡ **实时进度** | 处理进度实时显示，支持断点续传 |
| 🎨 **结构图预览** | 在抽取前即可预览 Schema 结构图，直观了解实体关系 |
| ✅ **审核机制** | 支持自动和人工两种审核模式，确保数据质量 |
| 🐳 **跨平台** | 支持 Docker 部署，Windows / macOS / Linux 均可运行 |

---

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    KG AI Builder                            │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Streamlit Web UI (app.py)                              ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  ││
│  │  │ Schema   │ │  File    │ │  Config  │ │  Review  │  ││
│  │  │  Config  │ │  Import  │ │  LLM+DB  │ │  Panel   │  ││
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  ││
│  └─────────────────────────────────────────────────────────┘│
│                           │                                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Core Engine (utils/)                                   ││
│  │  ┌────────────┐ ┌────────────┐ ┌──────────────────┐    ││
│  │  │  Extractor │ │  Cypher    │ │  Neo4j Manager   │    ││
│  │  │  (LLM)     │ │  Generator │ │  (DB Operations) │    ││
│  │  └────────────┘ └────────────┘ └──────────────────┘    ││
│  │  ┌────────────┐ ┌────────────┐ ┌──────────────────┐    ││
│  │  │  Doc       │ │  File     │ │  Progress        │    ││
│  │  │  Loader    │ │  Manager  │ │  Tracker         │    ││
│  │  └────────────┘ └────────────┘ └──────────────────┘    ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
         │                                        │
         ▼                                        ▼
┌──────────────┐                     ┌──────────────────┐
│   LLM API    │                     │  Neo4j Database  │
│ (OpenAI/     │                     │  (Graph Storage)  │
│  Zhipu/      │                     │  Port 7474/7687  │
│  Claude/...) │                     └──────────────────┘
└──────────────┘
```

---

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

这是最快捷的启动方式，一条命令即可启动完整服务（包括 Neo4j 数据库）。

**前置要求：**

- [Docker](https://docs.docker.com/get-docker/) (24.0+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.0+)

**步骤：**

```bash
# 1. 克隆项目
git clone https://github.com/happy-momo/EASY-Knowledge-Graph-Builder.git
cd EASY-Knowledge-Graph-Builder

# 2. 配置环境变量（复制并编辑 .env 文件）
cp .env.example .env
# 编辑 .env 文件，填入您的 LLM API Key（至少一个）

# 3. 启动服务（首次启动需要下载镜像，约 2-5 分钟）
docker compose up -d

# 4. 查看服务状态
docker compose ps

# 5. 访问应用
# KG Builder:    http://localhost:8501
# Neo4j Browser: http://localhost:7474  (用户名: neo4j, 密码: password123)
```

**一键启动脚本（可选）：**

```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

**常用命令：**

```bash
# 查看日志
docker compose logs -f

# 停止服务
docker compose down

# 停止并删除数据卷（谨慎！会清除所有数据）
docker compose down -v

# 重启服务
docker compose restart

# 更新到最新版本
git pull
docker compose up -d --build
```

### 方式二：本地运行

**前置要求：**

- Python 3.10+
- Neo4j 5.0+（运行中）
- 对应的 LLM API Key

**步骤：**

```bash
# 1. 克隆项目
git clone https://github.com/happy-momo/EASY-Knowledge-Graph-Builder.git
cd EASY-Knowledge-Graph-Builder

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 API Key 和 Neo4j 连接信息

# 5. 启动应用
streamlit run app.py

# 访问 http://localhost:8501
```

---

## 🔧 配置指南

### LLM 模型配置

KG AI Builder 支持双路由架构，自动适配不同 LLM 提供商的 API 格式。

#### 支持的模型

| 提供商 | 环境变量 | 推荐模型 | 注册地址 |
|--------|---------|---------|---------|
| 智谱AI | `ZHIPU_API_KEY` | `glm-4-plus` | [open.bigmodel.cn](https://open.bigmodel.cn/) |
| OpenAI | `OPENAI_API_KEY` | `gpt-4o-mini` | [platform.openai.com](https://platform.openai.com/) |
| Anthropic | `ANTHROPIC_API_KEY` | `claude-sonnet-4-20250514` | [console.anthropic.com](https://console.anthropic.com/) |
| Google | `GOOGLE_API_KEY` | `gemini-2.0-flash` | [makersuite.google.com](https://makersuite.google.com/) |
| 阿里云 | `DASHSCOPE_API_KEY` | `qwen-plus` | [help.aliyun.com](https://help.aliyun.com/document_detail/2712195.html) |
| DeepSeek | `DEEPSEEK_API_KEY` | `deepseek-chat` | [platform.deepseek.com](https://platform.deepseek.com/) |

**配置方式：**

1. **环境变量方式（推荐 Docker 部署）**：在 `.env` 文件中设置 `XXX_API_KEY=your_key`
2. **应用内输入**：启动后在 Web 界面的"配置连接"步骤中手动输入 API Key

### Neo4j 数据库配置

#### Docker Compose 环境（默认配置）

```
URI:      bolt://neo4j:7687
用户名:   neo4j
密码:     password123
```

#### 本地环境

```
URI:      bolt://localhost:7687
用户名:   neo4j
密码:     <您的密码>
```

> **注意**：首次使用 Neo4j 时，需要在 Neo4j Browser (http://localhost:7474) 中修改默认密码。

### 应用参数配置

| 参数 | 环境变量 | 默认值 | 说明 |
|------|---------|-------|------|
| 分块大小 | `CHUNK_SIZE` | 2000 | 文本分块的最大字符数 |
| 最小分块 | `CHUNK_MIN_SIZE` | 500 | 文本分块的最小字符数 |
| LLM 温度 | `LLM_TEMPERATURE` | 0.1 | 生成温度（0.0-1.0），越低越确定 |

---

## 📖 使用指南

### 工作流程

KG AI Builder 采用步骤式引导设计，共分为 6 个步骤：

```
Schema 配置 → 文档导入 → 配置连接 → 抽取处理 → 审核入库 → 完成
```

### 步骤 1：Schema 配置

定义知识图谱的本体结构，包括实体类型和关系类型。

**三种配置方式：**

1. **预设模板** — 选择内置模板（如"人物-组织"、"概念-关系"等），一键生成
2. **上传 YAML 文件** — 上传自定义的 YAML Schema 文件
3. **手动输入** — 在文本框中直接输入 YAML 格式的 Schema 定义

**Schema 示例：**

```yaml
entities:
  - name: "Person"
    properties:
      - "name"
      - "age"
      - "occupation"
  - name: "Organization"
    properties:
      - "name"
      - "industry"
      - "foundedYear"
  - name: "Location"
    properties:
      - "name"
      - "country"

relationships:
  - head: "Person"
    relation: "worksAt"
    tail: "Organization"
  - head: "Person"
    relation: "livesIn"
    tail: "Location"
  - head: "Organization"
    relation: "locatedIn"
    tail: "Location"
```

> 💡 **提示**：配置完成后可以在"结构图"标签页中预览实体-关系图。

### 步骤 2：文档导入

上传需要处理的文档。

**支持格式：**
- 📄 **PDF** (.pdf) — 自动提取文本内容
- 📝 **Word** (.docx) — 保留段落结构
- 📊 **Excel** (.xlsx) — 读取所有工作表
- 📃 **纯文本** (.txt) — 直接读取

**两种导入方式：**
- **单文件上传** — 点击上传按钮选择文件
- **文件夹导入** — 输入文件夹路径批量处理

### 步骤 3：配置连接

配置 LLM 模型和 Neo4j 数据库连接。

1. **选择 LLM 服务商** — 从下拉列表中选择
2. **输入 API Key** — 粘贴您的 API Key（或使用 .env 文件中配置的）
3. **指定模型名称** — 输入具体模型名称
4. **测试连接** — 点击"测试连接"按钮验证配置
5. **配置 Neo4j** — 输入 URI、用户名和密码
6. **测试数据库连接** — 验证 Neo4j 是否可访问

### 步骤 4：抽取处理

系统自动将文档分块，并使用 LLM 逐块抽取三元组。

- **实时进度条** — 显示当前处理进度和预估剩余时间
- **处理日志** — 每块的处理状态实时更新
- **断点续传** — 如果中断，已处理的结果不会丢失

### 步骤 5：审核入库

**两种审核模式：**

1. **自动审核** — 系统自动将所有抽取的三元组入库（适合信任 LLM 结果的场景）
2. **人工审核** — 逐个查看三元组，确认/编辑/删除后入库（适合对数据质量要求高的场景）

审核完成点击"确认入库"。

### 步骤 6：完成

查看抽取统计信息：
- 处理的文档数和分块数
- 抽取的实体数、关系数、属性数
- 处理耗时

> 🗄️ 在 Neo4j Browser (http://localhost:7474) 中查看知识图谱：
> ```cypher
> MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100
> ```

---

## 📁 项目结构

```
EASY-Knowledge-Graph-Builder/
├── app.py                          # 主应用入口（Streamlit）
├── Dockerfile                      # Docker 构建文件
├── docker-compose.yml              # Docker Compose 配置（含 Neo4j）
├── .env.example                    # 环境变量示例
├── requirements.txt                # Python 依赖列表
│
├── components/                     # UI 组件
│   ├── __init__.py
│   ├── config_page.py              # 配置页面组件
│   ├── file_import.py              # 文件导入组件
│   ├── icons.py                    # SVG 图标库（跨浏览器兼容）
│   ├── process_display.py          # 处理进度显示组件
│   ├── review_panel.py             # 审核面板组件
│   ├── schema_templates.py         # Schema 模板选择组件
│   ├── step_navigation.py          # 步骤导航组件
│   └── welcome_page.py             # 欢迎引导页组件
│
├── config/                         # 配置
│   └── app_config.py               # 应用配置（Schema模板、默认值）
│
├── utils/                          # 核心工具
│   ├── cypher_generator.py         # Cypher 查询生成器
│   ├── doc_loader.py               # 文档加载与分块
│   ├── env_checker.py              # 环境变量检测
│   ├── extractor.py                # LLM 三元组抽取引擎
│   ├── file_manager.py             # 文件管理
│   ├── folder_loader.py            # 文件夹加载
│   ├── llm_config.py               # LLM 配置与双路由
│   ├── neo4j_manager.py            # Neo4j 数据库操作
│   ├── progress_tracker.py         # 进度追踪
│   ├── schema_visualizer.py        # Schema 结构图可视化
│   └── state_manager.py            # 状态管理
│
├── styles/                         # 样式
│   └── main.css                    # 全局样式
│
├── scripts/                        # 脚本
│   └── start.sh                    # 一键启动脚本
│
├── tests/                          # 测试
│   ├── conftest.py                 # pytest 夹具
│   ├── test_core.py                # 核心功能测试
│   └── test_new_features.py        # 新功能测试
│
└── .data/                          # 数据持久化（gitignore）
    ├── session/                    # 会话状态
    └── uploads/                    # 上传文件
```

---

## 💻 开发指南

### 环境搭建

```bash
# 克隆项目
git clone https://github.com/happy-momo/EASY-Knowledge-Graph-Builder.git
cd EASY-Knowledge-Graph-Builder

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS

# 安装开发依赖
pip install -r requirements.txt
pip install pytest pytest-cov  # 测试依赖

# 启动开发服务器
streamlit run app.py
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 带覆盖率报告
pytest tests/ --cov=utils --cov=components --cov-report=term-missing -v

# 运行特定测试
pytest tests/test_core.py -v -k "test_sanitize"
```

### 代码风格

- Python: 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 规范
- 导入顺序: 标准库 → 第三方库 → 本地模块
- 类型注解: 对函数参数和返回值使用类型注解
- 文档字符串: 使用 Google 风格 docstring

### 构建 Docker 镜像

```bash
# 构建镜像
docker build -t kg-builder .

# 使用 Docker Compose 构建并启动
docker compose up -d --build
```

---

## ❓ 常见问题

### Docker 相关

**Q: 启动时提示"端口已被占用"？**
> 修改 `docker-compose.yml` 中的端口映射，如 `"8502:8501"`。

**Q: 如何查看 Neo4j 日志？**
> ```bash
> docker compose logs neo4j
> ```

**Q: 数据存在哪里？**
> - Neo4j 数据存储在 Docker 卷 `kg-neo4j-data` 中
> - 应用数据存储在 `.data/` 目录或卷 `kg-builder-data` 中

### LLM 相关

**Q: 需要配置多个 API Key 吗？**
> 不需要，只需要配置至少一个 LLM 提供商的 API Key 即可使用。

**Q: 抽取结果不准确怎么办？**
> - 尝试使用更强大的模型（如 `gpt-4o` 替代 `gpt-4o-mini`）
> - 调整 LLM 温度参数（降低到 0.05 增加确定性）
> - 优化 Schema 定义，使实体和关系更明确

### Neo4j 相关

**Q: Neo4j Browser 无法访问？**
> 确保 Neo4j 容器正常运行：`docker compose ps neo4j`

**Q: 如何修改 Neo4j 密码？**
> 1. 访问 http://localhost:7474
> 2. 使用默认密码登录
> 3. 执行 `ALTER CURRENT USER SET PASSWORD FROM '旧密码' TO '新密码'`

---

## 🤝 贡献指南

欢迎贡献！无论是新功能、bug 修复还是文档改进，都欢迎提交 Issue 和 Pull Request。

1. **Fork** 本仓库
2. 创建特性分支: `git checkout -b feature/AmazingFeature`
3. 提交更改: `git commit -m 'Add some AmazingFeature'`
4. 推送到分支: `git push origin feature/AmazingFeature`
5. 打开 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 — 详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- 感谢 [Streamlit](https://streamlit.io/) — 强大的 Web 应用框架
- 感谢 [LangChain](https://www.langchain.com/) — LLM 应用框架
- 感谢 [Neo4j](https://neo4j.com/) — 领先的图数据库
- 感谢所有贡献者和用户的反馈支持

---

<p align="center">
  <strong>如果这个项目对您有帮助，请给它一个 ⭐️！</strong>
</p>

<p align="center">
  <a href="https://github.com/happy-momo/EASY-Knowledge-Graph-Builder">GitHub Repository</a>
  ·
  <a href="https://github.com/happy-momo/EASY-Knowledge-Graph-Builder/issues">Report Bug</a>
  ·
  <a href="https://github.com/happy-momo/EASY-Knowledge-Graph-Builder/issues">Request Feature</a>
</p>

---

<p align="center">
  <em>Built with ❤️ by KG AI Builder community</em>
</p>