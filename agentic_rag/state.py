# -*- coding: utf-8 -*-
"""
@desc: 定义Agentic RAG工作流的状态（增加学术诊断支持）。
"""
from typing import List, TypedDict, Optional, Any


class AgentState(TypedDict):
    """
    Agentic RAG的状态表示

    Attributes:
        query (str): 用户的原始输入（可能是问题，也可能是待润色的论文）。
        is_academic_edit (bool): 是否进入学术手术刀模式（!paper 触发）。
        paper_content (str): 存储提取出的原始论文正文。
        issues (List[dict]): 诊断出的学术问题列表，每项包含：句子、类型、原因、检索关键词。

        updated_query (str): 经过优化的查询。
        documents (List[str]): 从知识源（或SCI金句库）检索到的文档列表。
        response (str): LLM生成的中间或最终答案（润色后的对比结果）。
        route (str): 查询路由的结果（新增 'academic_audit' 路由）。
        is_relevant (bool): 答案是否满足用户需求。
        error (Optional[str]): 工作流中的错误信息。
        retrieved_memories (Optional[List[str]]): 从长期记忆库中检索到的相关背景。
        conversation_history (List): 存储当前对话历史。
        correction_attempts (int): 修复尝试次数。
        tried_routes (List[str]): 已尝试过的路由策略。
        documents_are_relevant (bool): 检索到的金句或文档是否相关。
    """
    # 基础信息
    query: str
    is_academic_edit: bool  # 新增：标记是否为论文修改模式
    paper_content: Optional[str]  # 新增：存放论文正文

    # 学术诊断核心字段
    # 结构示例：[{"original": "...", "issue_type": "weak_verb", "search_query": "...", "reason": "..."}]
    issues: Optional[List[dict]]

    # 检索与生成
    updated_query: str
    documents: List[str]
    response: str
    route: str
    is_relevant: bool
    error: Optional[str]
    retrieved_memories: Optional[List[str]]
    conversation_history: List
    correction_attempts: int
    tried_routes: List[str]
    documents_are_relevant: bool