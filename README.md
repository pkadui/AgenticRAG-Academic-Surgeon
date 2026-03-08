# AgenticRAG-Academic-Surgeon

AgenticRAG 是一款专为 SCI 论文润色设计的智能代理系统。不同于传统的全篇翻译或简单润色，它模拟了**“资深审稿人诊断 + 金句库对标 + 精细化手术”**的工作流。

## ✨ 核心特性

* **🔍 深度学术诊断**：基于 AcademicAudit 逻辑，自动识别弱动词、口语化表达、逻辑断层及非学术语气。
* **📚 动态金句库 RAG**：内置高频 SCI 表达库，实时检索最贴切的句式参考。
* **✂️ 微创润色手术**：拒绝“推倒重来”，仅针对问题点进行精准缝合。
* **📄 Word 全文批处理**：支持 .docx 文件一键读取，按逻辑段落流式处理。
* **📊 结构化手术报告**：一键导出 Markdown 报告，清晰对比【原文】|【修改点】|【润色后】。
* **🧠 研究背景记忆**：具备长期记忆能力，能自动记录你的研究领域。

## 🚀 快速开始

### 1. 环境准备
```bash
git clone https://github.com/your-username/AgenticRAG-Academic-Surgeon.git
cd AgenticRAG-Academic-Surgeon
pip install -r requirements.txt
2. 配置 API在项目根目录创建 .env 文件，或直接在终端设置：Bash# 设置你的 LLM API Key
export OPENAI_API_KEY="your_key_here"
# (可选) 设置网络搜索 Key
export TAVILY_API_KEY="tvly-xxxx"
3. 运行程序Bashpython main.py

