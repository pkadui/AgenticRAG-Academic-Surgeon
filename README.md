# AgenticRAG-Academic-Surgeon
AgenticRAG 是一款专为 SCI 论文润色设计的智能代理系统。不同于传统的全篇翻译或简单润色，它模拟了**“资深审稿人诊断 + 金句库对标 + 精细化手术”**的工作流，旨在通过局部微创手术大幅提升论文的学术格调。✨ 核心特性🔍 深度学术诊断：基于 AcademicAudit 逻辑，自动识别弱动词、口语化表达、逻辑断层及非学术语气。📚 动态金句库 RAG：内置高频 SCI 表达库，针对每个诊断出的问题，实时检索最贴切的句式参考。✂️ 微创润色手术：拒绝“推倒重来”，仅针对问题点进行精准缝合，保持原作者的技术意图。📄 Word 全文批处理：支持 .docx 文件一键读取，按逻辑段落流式处理，无惧 Token 限制。📊 结构化手术报告：一键导出 Markdown 报告，清晰对比【原文】|【修改点】|【修改理由】|【润色后】，直接用于回复审稿意见。🧠 研究背景记忆：具备长期记忆能力，能自动记录你的研究领域（如 6D Pose, ARCore），使润色建议随对话深入越来越懂你。🚀 快速开始1. 环境准备Bashgit clone https://github.com/your-username/AgenticRAG-Academic-Surgeon.git
cd AgenticRAG-Academic-Surgeon
pip install -r requirements.txt
2. 配置 API在项目根目录创建 .env 文件，或直接在终端设置：Bash# 设置你的 LLM API Key (支持 OpenAI/Claude/Gemini 等)
export OPENAI_API_KEY="your_key_here"
# (可选) 设置网络搜索 Key
export TAVILY_API_KEY="tvly-xxxx"
3. 运行程序Bashpython main.py
🛠️ 使用指令指令说明示例!paper [文本]快速润色一小段文字!paper This project uses AR to show...!read [文件名]处理整个 Word 文档!read my_abstract.docx!save导出刚才的手术报告生成 Academic_Report_2026.md!show_memories查看 Agent 记住的研究背景检查它是否知道你在做 CV/ARexit退出程序📐 工作流图解 (Workflow)系统采用了基于 LangGraph 的循环有向图结构：Retrieve Memory: 提取用户研究背景。Academic Audit: 扫描原文，识别优化点。RAG Retrieval: 从本地 SCI 语料库检索针对性建议。Refine Paper: 执行润色，缝合文本。Memory Consolidation: 复盘并存储新的知识。🤝 贡献欢迎提交 Issue 或 Pull Request！无论是增加新的金句库，还是优化诊断提示词，我们都非常欢迎。
