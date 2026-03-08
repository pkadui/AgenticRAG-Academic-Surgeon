# -*- coding: utf-8 -*-
"""
@desc: 数据注入脚本（稳健版：支持目录过滤与内存优化）
"""

import os
import shutil
import multiprocessing
import re
import gc
from tqdm import tqdm
import pandas as pd
import chromadb
import fitz  # PyMuPDF

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    TextLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredMarkdownLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 假设这些是你已有的自定义模块
from agentic_rag.chains import get_embedding_function, get_summarizer_chain
from config import EXCEL_METADATA_COLUMNS

# --- 配置 ---
DATA_PATH = "data"
PERSIST_PATH = "chroma_db"
SUMMARY_COLLECTION_NAME = "doc_summaries"
CHUNK_COLLECTION_NAME = "doc_chunks"

# --- 核心改进 1：降低并发数，防止 OOM ---
# 建议设为 2，如果显存依然紧张，请设为 1
NUM_WORKERS = 2


def process_document_worker(doc):
    """
    对单个文档进行摘要生成和文本切分的工作函数。
    """
    # 局部加载，减少内存占用
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)

    doc_content = doc.page_content
    doc_source = doc.metadata.get('source', 'unknown_source')
    doc_type = doc.metadata.get('data_type', 'narrative')

    if 'row_index' in doc.metadata:
        doc_source = f"{doc_source}_row_{doc.metadata['row_index']}"
    elif 'section' in doc.metadata and 'subsection' in doc.metadata:
        doc_source = f"{doc_source}_{doc.metadata['section']}_{doc.metadata['subsection']}"

    try:
        summary = ""
        if doc_type == 'phrase_bank':
            section = doc.metadata.get('section', 'Unknown Section')
            subsection = doc.metadata.get('subsection', 'Unknown Subsection')
            summary = f"此段落归类为【{section}】，具体功能：{subsection}。"
        elif doc_type == 'tabular':
            summary = doc_content
        else:
            # 只有叙事型文档才动用 LLM
            summarizer_chain = get_summarizer_chain()
            summary = summarizer_chain.invoke({"document_content": doc_content}).content

        summary_metadata = {"source": doc_source}
        for key in ['section', 'subsection', 'data_type']:
            if key in doc.metadata:
                summary_metadata[key] = doc.metadata[key]

        splits = text_splitter.split_documents([doc])
        chunk_docs = [split.page_content for split in splits]
        chunk_metadatas = [split.metadata for split in splits]
        chunk_ids = [f"{doc_source}_chunk_{i}" for i in range(len(splits))]

        # 主动清理内存
        gc.collect()

        return (doc_source, summary, summary_metadata, chunk_ids, chunk_docs, chunk_metadatas)
    except Exception as e:
        print(f"处理文档 {doc_source} 时出错: {e}")
        return None


def load_documents_from_directory(directory_path):
    documents = []
    loader_map = {
        '.txt': TextLoader,
        '.md': UnstructuredMarkdownLoader,
        '.docx': UnstructuredWordDocumentLoader,
        '.doc': UnstructuredWordDocumentLoader
    }
    supported_files = []

    for root, _, files in os.walk(directory_path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in loader_map or ext in ['.xlsx', '.xls', '.pdf']:
                supported_files.append(os.path.join(root, file))

    for file_path in tqdm(supported_files, desc="加载文档"):
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == '.pdf':
                doc_obj = fitz.open(file_path)
                current_section = "General"
                current_subsection = "General Overview"

                section_pattern = re.compile(r'^([A-G]\.)\s+(.+)')
                subsection_pattern = re.compile(r'^([a-z]\))\s+(.+)')

                buffer = []

                for page_num, page in enumerate(doc_obj):
                    text = page.get_text()

                    # --- 核心改进 2：目录页初筛 ---
                    # 如果页面包含大量点号或特定关键字，直接跳过全页
                    if text.count('.') > 100 or "CONTENTS" in text.upper() or "目录" in text:
                        continue

                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()

                        # --- 核心改进 3：行级过滤 ---
                        # 过滤掉带有长虚线/点号的目录行 (如: Introduction ..... 4)
                        if not line or line.isdigit() or line.count('.') > 5:
                            continue

                        sec_match = section_pattern.match(line)
                        if sec_match:
                            if buffer:
                                metadata = {"source": file_path, "page": page_num, "section": current_section,
                                            "subsection": current_subsection, "data_type": "phrase_bank"}
                                documents.append(Document(page_content="\n".join(buffer), metadata=metadata))
                                buffer = []
                            current_section = sec_match.group(2).strip()
                            current_subsection = "General Overview"
                            continue

                        subsec_match = subsection_pattern.match(line)
                        if subsec_match:
                            if buffer:
                                metadata = {"source": file_path, "page": page_num, "section": current_section,
                                            "subsection": current_subsection, "data_type": "phrase_bank"}
                                documents.append(Document(page_content="\n".join(buffer), metadata=metadata))
                                buffer = []
                            current_subsection = subsec_match.group(2).strip()
                            continue

                        buffer.append(line)

                if buffer:
                    metadata = {"source": file_path, "page": doc_obj.page_count, "section": current_section,
                                "subsection": current_subsection, "data_type": "phrase_bank"}
                    documents.append(Document(page_content="\n".join(buffer), metadata=metadata))

            elif ext in ['.xlsx', '.xls']:
                # (保持 Excel 加载逻辑不变)
                df = pd.read_excel(file_path)
                for index, row in df.iterrows():
                    content_parts = []
                    metadata = {"source": file_path, "row_index": index, "data_type": "tabular"}
                    for col_name in df.columns:
                        value_str = str(row[col_name]) if not pd.isna(row[col_name]) else ""
                        content_parts.append(f"{col_name}: {value_str}")
                        if col_name in EXCEL_METADATA_COLUMNS:
                            metadata[col_name] = value_str
                    documents.append(Document(page_content="\n".join(content_parts), metadata=metadata))

            elif ext in loader_map:
                loader = loader_map[ext](file_path)
                loaded_docs = loader.load()
                for d in loaded_docs:
                    d.metadata["data_type"] = "narrative"
                    documents.append(d)

        except Exception as e:
            print(f"加载文件 {file_path} 失败: {e}")

    return documents


def main():
    print("--- 启动稳健版数据注入流程 ---")
    if os.path.exists(PERSIST_PATH):
        print(f"清理旧数据库...")
        shutil.rmtree(PERSIST_PATH)

    documents = load_documents_from_directory(DATA_PATH)
    if not documents: return

    print(f"\n加载完成，共有 {len(documents)} 条结构化段落。")
    print(f"--- 使用 {NUM_WORKERS} 个进程进行处理，以保护显存/内存 ---")

    with multiprocessing.Pool(processes=NUM_WORKERS) as pool:
        results = list(tqdm(pool.imap_unordered(process_document_worker, documents),
                            total=len(documents), desc="处理中"))

    # 合并结果与数据库存储逻辑 (与之前一致，略)
    all_summary_ids, all_summaries, all_summary_metadatas = [], [], []
    all_chunk_ids, all_chunks, all_chunk_metadatas = [], [], []

    for r in results:
        if r:
            source, summary, s_meta, c_ids, c_docs, c_metas = r
            all_summary_ids.append(source)
            all_summaries.append(summary)
            all_summary_metadatas.append(s_meta)
            all_chunk_ids.extend(c_ids)
            all_chunks.extend(c_docs)
            all_chunk_metadatas.extend(c_metas)

    # 存入 ChromaDB
    client = chromadb.PersistentClient(path=PERSIST_PATH)
    embedding_function = get_embedding_function()

    # 存入摘要
    s_coll = client.get_or_create_collection(SUMMARY_COLLECTION_NAME, embedding_function=embedding_function)
    s_coll.add(ids=all_summary_ids, documents=all_summaries, metadatas=all_summary_metadatas)

    # 存入金句
    c_coll = client.get_or_create_collection(CHUNK_COLLECTION_NAME, embedding_function=embedding_function)
    # 分批存入，防止单次请求过大
    batch_size = 500
    for i in range(0, len(all_chunk_ids), batch_size):
        end = i + batch_size
        c_coll.add(ids=all_chunk_ids[i:end], documents=all_chunks[i:end], metadatas=all_chunk_metadatas[i:end])

    print("\n--- 注入成功！数据库已准备就绪 ---")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()