import chromadb
from agentic_rag.chains import get_embedding_function


def semantic_search(query_text, section_filter=None):
    client = chromadb.PersistentClient(path="chroma_db")
    embedding_function = get_embedding_function()
    collection = client.get_collection("doc_chunks", embedding_function=embedding_function)

    # 构造过滤器
    where_clause = {"section": section_filter} if section_filter else None

    results = collection.query(
        query_texts=[query_text],
        n_results=3,
        where=where_clause
    )

    print(f"\n🔍 搜索关键词: '{query_text}'")
    if section_filter:
        print(f"📁 限定章节: {section_filter}")

    for i in range(len(results['ids'][0])):
        content = results['documents'][0][i]
        meta = results['metadatas'][0][i]
        print(f"\n--- 匹配结果 {i + 1} (来自: {meta.get('subsection', '未知')}) ---")
        print(f"内容: {content[:200]}...")  # 只看前200字
        print(f"所在页码: {meta.get('page')}")


if __name__ == "__main__":
    # 场景 1：全库搜索如何表达“差异”
    semantic_search("如何委婉地批评前人的研究不足")

    # 场景 2：只在“结果讨论”章节搜索
    # semantic_search("这些结果表明了什么", section_filter="Discussing Findings")
