# -*- coding: utf-8 -*-
"""
@desc: Agentic RAG 系统主入口 (学术论文手术刀 - Word 全文处理增强版)
"""

import uuid
import os
import json
from datetime import datetime
from docx import Document  # 需要安装: pip install python-docx
from agentic_rag.graph import build_graph
from agentic_rag import memory

# 临时解决环境变量问题
if not os.environ.get("TAVILY_API_KEY"):
    os.environ["TAVILY_API_KEY"] = "dummy_key"


# --- 1. 核心报告生成逻辑 ---

def save_academic_report(state, session_id):
    """将学术润色结果导出为详细的 Markdown 报告"""
    if not state or not state.get("is_academic_edit"):
        print("⚠️ 尚无学术诊断数据可供导出。")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Full_Paper_Report_{timestamp}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# 🔬 SCI 全文润色报告 (Session: {session_id})\n\n")
        f.write(f"> **处理时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write(f"## 🩺 诊断与修改详情 (Audit Details)\n")
        f.write(f"| 原文片段 | 问题类型 | 修改原因 | 检索关键词 |\n")
        f.write(f"| :--- | :--- | :--- | :--- |\n")

        issues = state.get("issues", [])
        for issue in issues:
            # 简单清洗数据中的换行符防止表格错乱
            orig = issue.get('original_sentence', '').replace('\n', ' ')
            f.write(f"| {orig} | {issue.get('issue_type')} | {issue.get('reason')} | `{issue.get('search_query')}` |\n")

        f.write(f"\n## ✨ 完整润色全文 (Polished Full Text)\n")
        f.write(f"```text\n{state.get('response', '未生成响应')}\n```\n")

    print(f"\n✅ 完整报告已导出至: **{filename}**")


# --- 2. Word 文件分块处理逻辑 ---

def process_word_file(file_path, graph, config):
    """
    按段落读取 Word，分块送入 Agent 进行手术，最后合并结果。
    """
    if not os.path.exists(file_path):
        print(f"❌ 找不到文件: {file_path}")
        return None

    doc = Document(file_path)
    # 提取所有非空段落
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

    # 将段落组合成批次 (Batches)，每块约 1000 个字符，保证不超 Token 限制
    batches = []
    chunk = ""
    for p in paragraphs:
        if len(chunk) + len(p) < 1500:
            chunk += p + "\n\n"
        else:
            batches.append(chunk)
            chunk = p + "\n\n"
    if chunk: batches.append(chunk)

    print(f"📖 成功解析文档，共分为 {len(batches)} 个批次进行顺序处理...")

    total_refined_text = []
    total_issues = []

    for i, batch_content in enumerate(batches):
        print(f"⏳ 正在执行批次 [{i + 1}/{len(batches)}] 的学术诊断...")

        inputs = {
            "query": f"!paper {batch_content}",
            "is_academic_edit": True,
            "conversation_history": []
        }

        # 运行工作流
        for event in graph.stream(inputs, config=config, stream_mode="values"):
            pass

        # 收集该批次的结果
        state = graph.get_state(config).values
        total_refined_text.append(state.get("response", ""))
        total_issues.extend(state.get("issues", []))

    # 构造并返回汇总状态
    return {
        "is_academic_edit": True,
        "paper_content": f"Full Document: {file_path}",
        "issues": total_issues,
        "response": "\n\n".join(total_refined_text)
    }


# --- 3. 主程序入口 ---

def main():
    memory.initialize_memory_db()
    graph = build_graph()
    session_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}

    last_state = None

    print("========================================")
    print("🚀 SCI 论文学术手术刀 (Word 全文版)")
    print("----------------------------------------")
    print("💡 使用方式：")
    print("  1. 输入 '!paper [文字]'：处理短句")
    print("  2. 输入 '!read [文件名].docx'：自动分段处理全文")
    print("  3. 输入 '!save'：导出完整修改报告")
    print("  4. 输入 'exit'：退出")
    print("========================================\n")

    while True:
        try:
            user_input = input("📝 User > ").strip()
            if user_input.lower() in ['exit', 'quit']: break
            if not user_input: continue

            # 指令逻辑：全文读取
            if user_input.startswith('!read '):
                file_path = user_input.replace('!read ', '').strip()
                last_state = process_word_file(file_path, graph, config)
                if last_state:
                    print("\n" + "=" * 20 + " 全文处理完成 " + "=" * 20)
                    print(last_state["response"][:500] + "...\n(仅展示前500字，请用 !save 查看全文)")
                continue

            # 指令逻辑：保存
            if user_input == '!save':
                save_academic_report(last_state, session_id)
                continue

            # 指令逻辑：查看记忆
            if user_input == '!show_memories':
                mems = memory.view_memories(limit=10)
                for i, m in enumerate(mems or []): print(f"{i + 1}. {m['text']}")
                continue

            # 普通处理模式
            is_paper = user_input.startswith('!paper')
            inputs = {"query": user_input, "is_academic_edit": is_paper}

            print("\n--- ⚙️ 系统处理中 ---")
            for _ in graph.stream(inputs, config={**config, "recursion_limit": 50}, stream_mode="values"):
                pass

            last_state = graph.get_state(config).values
            print(f"\n✨ 结果:\n{last_state.get('response')}\n")

        except Exception as e:
            print(f"❌ 出错: {e}")


if __name__ == "__main__":
    main()