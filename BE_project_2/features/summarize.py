from groq import Groq
from .base import get_rag_context
import streamlit as st
def generate_summary(vector_store) -> str:
    """Generate summary using RAG context"""
    context = get_rag_context(vector_store, "Generate summary", k=5)
    
    prompt = f"""Summarize this content:
    {context}
    - First introduce the content 
    - Use bullet points
    - Highlight key concepts"""
    
    client = Groq(api_key='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')
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content

def render_summary(summary_text: str):
    st.header("Summary")
    st.markdown(summary_text)