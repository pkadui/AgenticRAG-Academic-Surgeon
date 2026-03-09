# AgenticRAG-Academic-Surgeon 🔬

本项目是一个专门针对 **SCI 学术论文润色与增强** 设计的智能 Agent 系统。它基于 LangGraph 架构，集成了动态查询分析、自我纠错机制以及针对长文档的“手术级”批处理能力。

> **🙏 致谢**
> 本项目基于 [wxxzy/AgentiRAG](https://github.com/wxxzy/AgentiRAG) 进行二次开发。原项目提供了优秀的基于 LangGraph 的 Agentic RAG 架构底层。本项目在此基础上，垂直于学术科研场景，增加了 Word 文档全量解析、学术诊断工作流及科研背景长效记忆等功能。

---

## ✨ 核心特性

* **多阶段学术审计**：模拟“诊断-检索-手术”逻辑，对论文进行逻辑性、创新性及语言规范性的深度润色。
* **长文档批处理**：集成 `python-docx` 绕过 Token 长度限制，支持对整篇 SCI 论文进行结构化处理。
* **长效科研记忆**：利用 SQLite 实现用户研究背景（如 6D Pose、ARCore 等领域知识）的持久化存储，实现跨会话的上下文一致性。
* **自动化性能评估**：内置基于 Ragas 的评估工具，并在 `evaluation/` 目录下提供可视化热力图与金标准数据集。

---

## 🚀 快速开始

### 1. 克隆与安装
```bash
git clone [https://github.com/pkadui/AgenticRAG-Academic-Surgeon.git](https://github.com/pkadui/AgenticRAG-Academic-Surgeon.git)
cd AgenticRAG-Academic-Surgeon
pip install -r requirements.txt
```

### 2. 准备嵌入模型 (Embedding Model)
由于模型文件较大，未上传至仓库。本项目默认使用 `BAAI/bge-m3` 以保证高维语义检索精度：
* **下载地址**：前往 [Hugging Face - BGE-M3](https://huggingface.co/BAAI/bge-m3) 下载全部权重文件。
* **存放位置**：在项目根目录下新建 `bge-m3/` 文件夹，并将下载的文件放入其中。

### 3. 配置环境变量
在项目根目录创建 `.env` 文件，并参考以下配置（推荐使用 DeepSeek）：
```bash
# LLM API 配置 (以 DeepSeek 为例)
OPENAI_API_KEY="你的DeepSeek密钥"
OPENAI_API_BASE="[https://api.deepseek.com/v1](https://api.deepseek.com/v1)"

# Embedding 配置 (可选，如需使用 DeepSeek 的 Embedding 功能)
EMBEDDING_API_BASE="[https://api.deepseek.com/v1](https://api.deepseek.com/v1)"

# 联网搜索 (可选，用于获取最新领域前沿)
TAVILY_API_KEY="你的Tavily密钥"
```

### 4. 数据初始化与运行
1. 将你的参考资料（PDF/Markdown）放入 `data/` 目录。
2. 运行知识库构建脚本：
```bash
python ingest.py
```
3. 启动学术 Agent：
```bash
python main.py
```

---

## 📊 效果评估
项目在 `evaluation/` 文件夹下包含：
* `router_confusion_matrix.png`: 路由分类准确率分析图。
* `generator_ragas_report.csv`: 基于 Ragas 的生成质量量化评分。

---

## 🛠️ 技术栈
* **Framework**: LangGraph, LangChain
* **Vector DB**: ChromaDB
* **Embedding**: BGE-M3
* **Storage**: SQLite (Aiosqlite)
* **Evaluation**: Ragas
