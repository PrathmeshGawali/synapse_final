from langchain.vectorstores import FAISS
from typing import List

def get_rag_context(vector_store: FAISS, query: str = "", k: int = 5) -> str:
    """Get relevant context from vector store"""
    docs = vector_store.similarity_search(query, k=k)
    return "\n".join([doc.page_content for doc in docs])