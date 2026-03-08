# -*- coding: utf-8 -*-
"""
@desc: LangGraph 工作流节点 - 学术手术刀修复版
"""
import json
from langchain_core.prompts import ChatPromptTemplate
from agentic_rag.chains import (
    get_query_router_chain,
    get_academic_critic_chain,
    get_memory_consolidation_chain,
    llm
)
from agentic_rag.hierarchical_retriever import hierarchical_retriever, direct_chunk_retriever
from agentic_rag.state import AgentState
from agentic_rag import memory


# --- 1. 记忆相关节点 ---

def retrieve_memory_node(state: AgentState) -> dict:
    """在流程开始时，检索长期记忆"""
    print("--- 🧠 正在调取研究背景记忆 ---")
    query = state["query"]
    retrieved_memories = memory.retrieve_memories(query)
    memories_text = "\n".join([mem['text'] for mem in retrieved_memories]) if retrieved_memories else "无相关历史记忆。"
    return {
        "retrieved_memories": memories_text,
        "conversation_history": [],
        "correction_attempts": 0
    }


def consolidate_memory_node(state: AgentState) -> dict:
    """在流程结束时，巩固本次对话记忆"""
    print("--- 💾 正在复盘并存储记忆 ---")
    history = state.get("conversation_history", [])
    if not history: return {}

    history_text = "\n".join([f"{role}: {text}" for role, text in history])
    consolidation_chain = get_memory_consolidation_chain()
    try:
        result = consolidation_chain.invoke({"conversation_history": history_text})
        if isinstance(result, dict) and result.get("text") and "No valuable information" not in result.get("text"):
            memory.add_memory(text=result["text"], type=result["type"], importance=result["importance"])
    except Exception as e:
        print(f"记忆存储跳过: {e}")
    return {}


# --- 2. 核心路由与诊断节点 ---

def route_query_node(state: AgentState) -> dict:
    """智能路由：决定是普通问答还是手术刀模式"""
    print("--- 🚦 智能路由调度中 ---")
    query = state["query"]
    # 检查 main.py 是否传入了 is_academic_edit，或者 query 是否有 !paper 前缀
    is_academic = state.get("is_academic_edit", False) or query.startswith("!paper")

    if is_academic:
        print("决策：进入【学术手术刀】模式")
        return {"route": "academic_audit", "tried_routes": ["academic_audit"]}

    # 普通路由逻辑
    router_chain = get_query_router_chain()
    result = router_chain.invoke({"query": query, "memories": state.get("retrieved_memories", "")})
    route = result['datasource']
    print(f"决策：进入普通检索路径 -> {route}")
    return {"route": route, "tried_routes": [route]}


def academic_audit_node(state: AgentState) -> dict:
    """学术诊断节点：扫描论文问题"""
    print("--- 🩺 正在执行学术扫描 (手术刀诊断) ---")
    # 清理前缀
    content = state["query"].replace("!paper", "").strip()
    critic_chain = get_academic_critic_chain()
    audit_results = critic_chain.invoke({"paper_content": content})

    issues = audit_results.get("issues", [])
    print(f"扫描完成：发现 {len(issues)} 处表达优化点")
    return {"paper_content": content, "issues": issues}


# --- 3. 检索与润色节点 ---

def retrieve_documents_node(state: AgentState) -> dict:
    """检索节点：兼容普通搜索和学术金句搜索，并确保输出为纯文本列表"""
    route = state.get("route")
    query = state.get("updated_query") or state["query"]
    documents = []

    # 1. 学术手术刀模式：针对诊断出的多个 issue 循环检索
    if route == "academic_audit" and state.get("issues"):
        print(f"--- 📚 正在为 {len(state['issues'])} 个问题匹配 SCI 金句库 ---")
        for issue in state["issues"]:
            search_key = issue.get("search_query", "")
            # raw_guides 此时是 [Document(...), Document(...)]
            raw_guides = direct_chunk_retriever(search_key)
            if raw_guides:
                # 核心修复：提取每个 Document 的 page_content
                guide_texts = [doc.page_content for doc in raw_guides]
                documents.append(f"针对优化点 '{search_key}':\n" + "\n".join(guide_texts))

    # 2. 层级检索路径
    elif route == 'hierarchical_search':
        raw_docs = hierarchical_retriever(query)
        documents = [doc.page_content for doc in raw_docs]

    # 3. 直接块检索路径
    elif route == 'direct_chunk_search':
        raw_docs = direct_chunk_retriever(query)
        documents = [doc.page_content for doc in raw_docs]

    # 4. 网络搜索路径（如果后续你配置了 Key）
    elif route == 'web_search':
        from agentic_rag.retrievers import get_web_search_tool
        web_search = get_web_search_tool()
        # Tavily 等工具返回的通常也是 Document 对象或需要特殊处理的字符串
        raw_web_docs = web_search.invoke({"query": query})
        documents = [doc.page_content if hasattr(doc, 'page_content') else str(doc) for doc in raw_web_docs]

    return {"documents": documents}


def refine_paper_node(state: AgentState) -> dict:
    """精准润色节点"""
    print("--- ✂️ 正在根据金句库进行“手术”润色 ---")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一位 SCI 资深编辑。请根据参考金句对原文进行修改，返回原文、理由、修改建议。"),
        ("human", "待修改: {issues}\n参考库: {guides}")
    ])
    chain = prompt | llm
    response = chain.invoke({"issues": json.dumps(state["issues"], ensure_ascii=False), "guides": state["documents"]})
    return {"response": response.content}


# --- 4. 辅助与生成节点 (Stubbed) ---

def rewrite_query_node(state: AgentState) -> dict:
    """临时跳过重写逻辑，直接使用原句"""
    return {"updated_query": state["query"]}


def grade_documents_node(state: AgentState) -> dict:
    """默认文档均相关，直接通过"""
    return {"documents_are_relevant": True}


def generate_response_node(state: AgentState) -> dict:
    """普通 RAG 答案生成"""
    print("--- ✍️ 正在生成最终回答 ---")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "根据以下上下文回答问题：\n{context}"),
        ("human", "{query}")
    ])
    chain = prompt | llm
    res = chain.invoke({"context": "\n".join(state["documents"]), "query": state["query"]})
    return {"response": res.content}


def direct_response_node(state: AgentState) -> dict:
    """直接调用 LLM 回答"""
    print("--- 🗨️ 直接对话模式 ---")
    res = llm.invoke(state["query"])
    return {"response": res.content}


def grade_relevance_node(state: AgentState) -> dict:
    """默认答案均通过"""
    return {"is_relevant": True}