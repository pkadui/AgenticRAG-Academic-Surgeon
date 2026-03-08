# -*- coding: utf-8 -*-
"""
@desc: 构建并编译Agentic RAG的工作流图（学术手术刀增强版 - 检查点修复）
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver  # 核心导入：内存检查点

from agentic_rag.state import AgentState
from agentic_rag.nodes import (
    retrieve_memory_node,
    consolidate_memory_node,
    route_query_node,
    rewrite_query_node,
    retrieve_documents_node,
    grade_documents_node,
    generate_response_node,
    grade_relevance_node,
    direct_response_node,
    # 学术节点
    academic_audit_node,
    refine_paper_node
)


def build_graph():
    """构建集成了检查点支持的学术手术刀工作流。"""
    workflow = StateGraph(AgentState)

    # --- 1. 添加所有节点 ---
    workflow.add_node("retrieve_memory", retrieve_memory_node)
    workflow.add_node("consolidate_memory", consolidate_memory_node)
    workflow.add_node("route_query", route_query_node)
    workflow.add_node("rewrite_query", rewrite_query_node)
    workflow.add_node("academic_audit", academic_audit_node)
    workflow.add_node("refine_paper", refine_paper_node)
    workflow.add_node("retrieve_documents", retrieve_documents_node)
    workflow.add_node("grade_documents", grade_documents_node)
    workflow.add_node("generate_response", generate_response_node)
    workflow.add_node("direct_response", direct_response_node)
    workflow.add_node("grade_relevance", grade_relevance_node)

    # --- 2. 定义边与连接逻辑 ---

    # 入口
    workflow.set_entry_point("retrieve_memory")
    workflow.add_edge("retrieve_memory", "route_query")

    # 路由决策
    workflow.add_conditional_edges(
        "route_query",
        lambda state: state["route"],
        {
            "academic_audit": "academic_audit",
            "web_search": "rewrite_query",
            "hierarchical_search": "rewrite_query",
            "direct_chunk_search": "rewrite_query",
            "direct": "direct_response"
        }
    )

    # A 分支：学术手术刀路径
    workflow.add_edge("academic_audit", "retrieve_documents")
    workflow.add_edge("retrieve_documents", "refine_paper")
    workflow.add_edge("refine_paper", "grade_relevance")

    # B 分支：普通 RAG 路径
    workflow.add_edge("rewrite_query", "retrieve_documents")
    workflow.add_edge("retrieve_documents", "grade_documents")

    # 内循环决策
    def decide_after_document_grading(state: AgentState):
        if state.get("documents_are_relevant"):
            return "generate"
        tried_routes = state.get("tried_routes", [])
        available_routes = ['hierarchical_search', 'direct_chunk_search', 'web_search']
        for next_route in available_routes:
            if next_route not in tried_routes:
                return "retry_retrieve"
        return "fallback"

    workflow.add_conditional_edges(
        "grade_documents",
        decide_after_document_grading,
        {
            "generate": "generate_response",
            "retry_retrieve": "retrieve_documents",
            "fallback": END
        }
    )

    # 最终汇合
    workflow.add_edge("generate_response", "grade_relevance")
    workflow.add_edge("direct_response", "grade_relevance")

    # 外循环决策（包含重试逻辑）
    def decide_after_answer_grading(state: AgentState):
        if state.get("is_relevant", True):
            return "end"
        if state.get("correction_attempts", 0) >= 2:
            return "end"
        return "retry"

    workflow.add_conditional_edges(
        "grade_relevance",
        decide_after_answer_grading,
        {
            "end": "consolidate_memory",
            "retry": "rewrite_query"
        }
    )

    workflow.add_edge("consolidate_memory", END)

    # --- 3. 关键修复：实例化并绑定 Checkpointer ---
    # MemorySaver 在内存中保存对话状态
    memory_saver = MemorySaver()

    # 编译图并注入 checkpointer
    graph = workflow.compile(checkpointer=memory_saver)
    return graph