# -*- coding: utf-8 -*-
"""
@desc: LLM链模块（已集成学术诊断、向量嵌入与手术刀逻辑）
"""

import torch
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from chromadb.utils import embedding_functions

from config import (
    LLM_MODEL_NAME, OPENAI_API_BASE,
    EMBEDDING_PROVIDER, EMBEDDING_API_BASE, EMBEDDING_MODEL_NAME, LOCAL_EMBEDDING_MODEL_PATH
)

# --- 1. LLM 与 Embedding 初始化 ---

# 构造LLM参数
llm_params = {
    "model": LLM_MODEL_NAME,
    "temperature": 0
}
if OPENAI_API_BASE:
    llm_params["base_url"] = OPENAI_API_BASE

# 定义 llm 对象
llm = ChatOpenAI(**llm_params)


def get_embedding_function():
    """获取嵌入模型函数，供检索器使用（核心修复点）"""
    if EMBEDDING_PROVIDER == 'openai':
        embedding_params = {"model": EMBEDDING_MODEL_NAME}
        api_base = EMBEDDING_API_BASE or OPENAI_API_BASE
        if api_base:
            embedding_params["base_url"] = api_base
        return OpenAIEmbeddings(**embedding_params)

    elif EMBEDDING_PROVIDER == 'local':
        device = "cuda" if torch.cuda.is_available() else "cpu"
        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=LOCAL_EMBEDDING_MODEL_PATH,
            device=device
        )
    else:
        raise ValueError(f"未知的嵌入模型提供商: {EMBEDDING_PROVIDER}")


# --- 2. 数据结构定义 ---

class AcademicIssue(BaseModel):
    """单条学术问题诊断结果"""
    original_sentence: str = Field(description="原文中需要优化的具体句子。")
    issue_type: str = Field(description="问题类型：'weak_verb', 'nominalization', 'direct_tone', 'vague'。")
    reason: str = Field(description="修改的具体理由。")
    search_query: str = Field(description="用于检索金句库的英文关键词。")


class AcademicAudit(BaseModel):
    """完整的论文诊断报告"""
    issues: list[AcademicIssue] = Field(description="发现的问题列表。")


class RouteQuery(BaseModel):
    """路由决策"""
    datasource: str = Field(
        description="从 'academic_audit', 'direct_chunk_search', 'hierarchical_search', 'web_search', 'direct' 中选择。")


class MemoryToSave(BaseModel):
    """记忆存储结构"""
    text: str = Field(description="需要记住的关键信息。")
    type: str = Field(description="类型：'fact', 'preference', 'conclusion'。")
    importance: int = Field(description="评分 1-10。")


# --- 3. LLM 链定义 ---

def get_academic_critic_chain():
    """学术诊断链"""
    parser = JsonOutputParser(pydantic_object=AcademicAudit)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位世界顶级期刊的资深审稿专家。
请扫描论文片段，找出不专业或太口语化的表达。
标准：1. 禁止弱动词(make/get)；2. 推崇名词化；3. 委婉化批评；4. 动作精准。
{format_instructions}"""),
        ("human", "待诊断论文片段：\n{paper_content}")
    ]).partial(format_instructions=parser.get_format_instructions())
    return prompt | llm | parser


def get_query_router_chain():
    """升级版智能路由"""
    parser = JsonOutputParser(pydantic_object=RouteQuery)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位查询路由专家。分析用户指令。
1. 若输入包含 '!paper' 或要求润色修改，选 `academic_audit`。
2. 若涉及本地知识库事实，选 `direct_chunk_search` 或 `hierarchical_search`。
3. 若需实时信息，选 `web_search`。
4. 简单问候选 `direct`。

历史记忆：{memories}
{format_instructions}"""),
        ("human", "问题/指令: {query}")
    ]).partial(format_instructions=parser.get_format_instructions())
    return prompt | llm | parser


def get_memory_consolidation_chain():
    """获取记忆提炼链"""
    parser = JsonOutputParser(pydantic_object=MemoryToSave)
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是一个记忆提炼专家。请分析对话提取核心信息。若无价值请回答'No valuable information to save'。\n{format_instructions}"),
        ("human", "对话历史:\n\n{conversation_history}")
    ]).partial(format_instructions=parser.get_format_instructions())
    return prompt | llm | parser