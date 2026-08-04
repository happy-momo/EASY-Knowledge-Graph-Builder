# KG AI Builder 🧠 → 🕸️

<p align="center">
  <strong>AI-Powered Knowledge Graph Builder — Transform Text into Structured Knowledge</strong>
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
  <a href="README.zh-CN.md">
    <img src="https://img.shields.io/badge/Language-中文-blue?style=flat-square" alt="Chinese">
  </a>
</p>

---

## 📋 Table of Contents

- [Introduction](#-introduction)
- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Configuration Guide](#-configuration-guide)
- [Usage Guide](#-usage-guide)
- [Project Structure](#-project-structure)
- [Development Guide](#-development-guide)
- [FAQ](#-faq)
- [Contributing](#-contributing)
- [License](#-license)

---

## 📖 Introduction

**KG AI Builder** is a powerful AI-driven knowledge graph construction tool that automatically converts unstructured text (PDF, Word, Excel, TXT) into structured knowledge graphs. By combining the text understanding capabilities of Large Language Models (LLMs) with the storage advantages of Neo4j graph database, it achieves automated transformation from raw text to semantic networks.

Whether for scientific literature analysis, enterprise document management, or knowledge base construction, KG AI Builder helps you quickly and efficiently extract valuable structured knowledge from massive amounts of text.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎯 **Multi-Model Support** | Compatible with ZhipuAI GLM, OpenAI GPT, Anthropic Claude, Google Gemini, Alibaba Qwen, DeepSeek and more |
| 🚀 **One-Click Deploy** | Docker Compose included — one command starts the full stack (app + Neo4j) |
| 📊 **Visual Interface** | Intuitive Streamlit-based web UI with step-by-step guidance |
| 📚 **Multi-Format Documents** | PDF, DOCX, XLSX, TXT — single file or batch folder import |
| 🔗 **Smart Extraction** | Automatically extracts entities, relationships, and attributes as RDF triples |
| 📝 **Schema Definition** | Preset templates, YAML upload, or manual input for ontology definition |
| 🗄️ **Neo4j Integration** | Seamless integration with Neo4j graph database for graph visualization |
| ⚡ **Real-Time Progress** | Live progress tracking with resume support |
| 🎨 **Schema Preview** | Visualize entity-relationship diagrams before extraction |
| ✅ **Review Modes** | Auto and manual review modes to ensure data quality |
| 🐳 **Cross-Platform** | Docker support — runs on Windows, macOS, and Linux |

---

## 🏗️ Architecture

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

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

The fastest way to get started — one command launches the full stack (including Neo4j).

**Prerequisites:**

- [Docker](https://docs.docker.com/get-docker/) (24.0+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.0+)

**Steps:**

```bash
# 1. Clone the repository
git clone https://github.com/happy-momo/EASY-Knowledge-Graph-Builder.git
cd EASY-Knowledge-Graph-Builder

# 2. Configure environment variables
cp .env.example .env
# Edit .env — fill in at least one LLM API Key

# 3. Start services (first run downloads images, ~2-5 min)
docker compose up -d

# 4. Check service status
docker compose ps

# 5. Access the application
# KG Builder:    http://localhost:8501
# Neo4j Browser: http://localhost:7474  (user: neo4j, password: password123)
```

**One-click startup script (optional):**

```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

**Common commands:**

```bash
# View logs
docker compose logs -f

# Stop services
docker compose down

# Stop and delete volumes (CAUTION: removes all data)
docker compose down -v

# Restart services
docker compose restart

# Update to latest version
git pull
docker compose up -d --build
```

### Option 2: Local Development

**Prerequisites:**

- Python 3.10+
- Neo4j 5.0+ (running)
- LLM API Key

**Steps:**

```bash
# 1. Clone the repository
git clone https://github.com/happy-momo/EASY-Knowledge-Graph-Builder.git
cd EASY-Knowledge-Graph-Builder

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — fill in API Key and Neo4j connection info

# 5. Launch the application
streamlit run app.py

# Access http://localhost:8501
```

---

## 🔧 Configuration Guide

### LLM Model Configuration

KG AI Builder uses a dual-route architecture that automatically adapts to different LLM provider API formats.

#### Supported Models

| Provider | Environment Variable | Recommended Model | Registration |
|----------|--------------------|-------------------|--------------|
| ZhipuAI | `ZHIPU_API_KEY` | `glm-4-plus` | [open.bigmodel.cn](https://open.bigmodel.cn/) |
| OpenAI | `OPENAI_API_KEY` | `gpt-4o-mini` | [platform.openai.com](https://platform.openai.com/) |
| Anthropic | `ANTHROPIC_API_KEY` | `claude-sonnet-4-20250514` | [console.anthropic.com](https://console.anthropic.com/) |
| Google | `GOOGLE_API_KEY` | `gemini-2.0-flash` | [makersuite.google.com](https://makersuite.google.com/) |
| Alibaba | `DASHSCOPE_API_KEY` | `qwen-plus` | [help.aliyun.com](https://help.aliyun.com/document_detail/2712195.html) |
| DeepSeek | `DEEPSEEK_API_KEY` | `deepseek-chat` | [platform.deepseek.com](https://platform.deepseek.com/) |

**How to configure:**

1. **Environment variables (recommended for Docker)**: Set `XXX_API_KEY=your_key` in `.env` file
2. **In-app input**: Enter API Key manually in the "Configure Connection" step of the web UI

### Neo4j Database Configuration

#### Docker Compose Environment (default)

```
URI:      bolt://neo4j:7687
Username:  neo4j
Password:  password123
```

#### Local Environment

```
URI:      bolt://localhost:7687
Username:  neo4j
Password:  <your_password>
```

> **Note**: On first Neo4j login, you'll need to change the default password via Neo4j Browser (http://localhost:7474).

### Application Parameters

| Parameter | Env Variable | Default | Description |
|-----------|-------------|---------|-------------|
| Chunk Size | `CHUNK_SIZE` | 2000 | Maximum characters per text chunk |
| Min Chunk | `CHUNK_MIN_SIZE` | 500 | Minimum characters per text chunk |
| LLM Temp | `LLM_TEMPERATURE` | 0.1 | Generation temperature (0.0-1.0), lower = more deterministic |

---

## 📖 Usage Guide

### Workflow

KG AI Builder uses a step-by-step guided design with 6 steps:

```
Schema Config → Document Import → Configure Connection → Extraction → Review & Save → Complete
```

### Step 1: Schema Configuration

Define the ontology structure including entity types and relationship types.

**Three configuration methods:**

1. **Preset Templates** — Choose built-in templates (e.g., "Person-Organization"), one-click generation
2. **Upload YAML** — Upload a custom YAML Schema file
3. **Manual Input** — Type YAML Schema directly in the text editor

**Schema Example:**

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

> 💡 **Tip**: Preview the entity-relationship diagram in the "Structure Graph" tab after configuration.

### Step 2: Document Import

Upload documents for processing.

**Supported formats:**
- 📄 **PDF** (.pdf) — automatic text extraction
- 📝 **Word** (.docx) — preserves paragraph structure
- 📊 **Excel** (.xlsx) — reads all worksheets
- 📃 **Plain Text** (.txt) — direct reading

**Import methods:**
- **Single file upload** — click to select a file
- **Folder import** — enter a folder path for batch processing

### Step 3: Configure Connection

Configure LLM model and Neo4j database connection.

1. **Select LLM provider** — choose from the dropdown
2. **Enter API Key** — paste your API Key (or use the one configured in `.env`)
3. **Specify model name** — enter the exact model name
4. **Test connection** — click "Test Connection" to verify
5. **Configure Neo4j** — enter URI, username, and password
6. **Test database connection** — verify Neo4j is accessible

### Step 4: Extraction

The system automatically splits documents into chunks and extracts triples using LLM.

- **Real-time progress bar** — shows current progress and estimated remaining time
- **Processing logs** — each chunk's status updates in real time
- **Resume support** — if interrupted, processed results are preserved

### Step 5: Review & Save

**Two review modes:**

1. **Auto Review** — automatically saves all extracted triples (best when you trust the LLM results)
2. **Manual Review** — review each triple individually, confirm/edit/delete before saving (recommended for high data quality requirements)

Click "Confirm Save" after review.

### Step 6: Complete

View extraction statistics:
- Number of documents and chunks processed
- Number of entities, relationships, and attributes extracted
- Processing time

> 🗄️ View the knowledge graph in Neo4j Browser (http://localhost:7474):
> ```cypher
> MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100
> ```

---

## 📁 Project Structure

```
EASY-Knowledge-Graph-Builder/
├── app.py                          # Main application entry (Streamlit)
├── Dockerfile                      # Docker build file
├── docker-compose.yml              # Docker Compose config (with Neo4j)
├── .env.example                    # Environment variable example
├── requirements.txt                # Python dependencies
│
├── components/                     # UI components
│   ├── __init__.py
│   ├── config_page.py              # Configuration page
│   ├── file_import.py              # File import component
│   ├── icons.py                    # SVG icon library (cross-browser)
│   ├── process_display.py          # Progress display component
│   ├── review_panel.py             # Review panel component
│   ├── schema_templates.py         # Schema template selection
│   ├── step_navigation.py          # Step navigation component
│   └── welcome_page.py             # Welcome page component
│
├── config/                         # Configuration
│   └── app_config.py               # App config (schema templates, defaults)
│
├── utils/                          # Core utilities
│   ├── cypher_generator.py         # Cypher query generator
│   ├── doc_loader.py               # Document loading & chunking
│   ├── env_checker.py              # Environment variable detection
│   ├── extractor.py                # LLM triple extraction engine
│   ├── file_manager.py             # File management
│   ├── folder_loader.py            # Folder loading
│   ├── llm_config.py               # LLM config & dual-route
│   ├── neo4j_manager.py            # Neo4j database operations
│   ├── progress_tracker.py         # Progress tracking
│   ├── schema_visualizer.py        # Schema visualization
│   └── state_manager.py            # State management
│
├── styles/                         # Styles
│   └── main.css                    # Global styles
│
├── scripts/                        # Scripts
│   └── start.sh                    # One-click startup script
│
├── tests/                          # Tests
│   ├── conftest.py                 # pytest fixtures
│   ├── test_core.py                # Core functionality tests
│   └── test_new_features.py        # New feature tests
│
└── .data/                          # Data persistence (gitignored)
    ├── session/                    # Session state
    └── uploads/                    # Uploaded files
```

---

## 💻 Development Guide

### Setup

```bash
# Clone the repository
git clone https://github.com/happy-momo/EASY-Knowledge-Graph-Builder.git
cd EASY-Knowledge-Graph-Builder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov  # test dependencies

# Start development server
streamlit run app.py
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov=utils --cov=components --cov-report=term-missing -v

# Run specific tests
pytest tests/test_core.py -v -k "test_sanitize"
```

### Code Style

- Python: Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) guidelines
- Import order: standard library → third-party → local modules
- Type hints: use type annotations for function parameters and return values
- Docstrings: use Google-style docstrings

### Building Docker Image

```bash
# Build image
docker build -t kg-builder .

# Build and start with Docker Compose
docker compose up -d --build
```

---

## ❓ FAQ

### Docker

**Q: Port already in use?**
> Change the port mapping in `docker-compose.yml`, e.g., `"8502:8501"`.

**Q: How to view Neo4j logs?**
> ```bash
> docker compose logs neo4j
> ```

**Q: Where is data stored?**
> - Neo4j data: Docker volume `kg-neo4j-data`
> - App data: `.data/` directory or volume `kg-builder-data`

### LLM

**Q: Do I need to configure multiple API Keys?**
> No, only one LLM provider API Key is needed.

**Q: Extraction results are inaccurate?**
> - Try a more powerful model (e.g., `gpt-4o` instead of `gpt-4o-mini`)
> - Lower the temperature (try 0.05 for more deterministic output)
> - Refine the Schema definition for clearer entities and relationships

### Neo4j

**Q: Neo4j Browser is unreachable?**
> Ensure the Neo4j container is running: `docker compose ps neo4j`

**Q: How to change the Neo4j password?**
> 1. Visit http://localhost:7474
> 2. Log in with the default password
> 3. Run `ALTER CURRENT USER SET PASSWORD FROM 'old_password' TO 'new_password'`

---

## 🤝 Contributing

Contributions are welcome! Whether it's a new feature, bug fix, or documentation improvement, please feel free to submit Issues and Pull Requests.

1. **Fork** the repository
2. Create your feature branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m 'Add some AmazingFeature'`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- [Streamlit](https://streamlit.io/) — The powerful web app framework
- [LangChain](https://www.langchain.com/) — LLM application framework
- [Neo4j](https://neo4j.com/) — Leading graph database
- All contributors and users for their feedback and support

---

<p align="center">
  <strong>If you find this project helpful, please give it a ⭐️!</strong>
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
  <em>Built with ❤️ by the KG AI Builder community</em>
</p>