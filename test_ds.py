import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()

embeddings = OpenAIEmbeddings(
    model="deepseek-embedding-pro-v1",          # 模型名称
    openai_api_key=os.getenv("OPENAI_API_KEY"), # API Key
    openai_api_base="https://api.deepseek.com/v1"  # 必须包含 /v1
)

vector = embeddings.embed_query("测试文本")
print(vector[:5])