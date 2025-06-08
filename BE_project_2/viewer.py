# viewer.py
import streamlit as st
from features import *
from database import get_output

def show_shared_output():
    st.set_page_config(page_title="Shared Output | SynapseIQ", layout="wide")

    query_params = st.query_params
    output_id = query_params.get("id", [None])[0]

    if not output_id:
        st.error("❌ Invalid or missing share link.")
        return

    feature, content = get_output(output_id)
    if not feature or not content:
        st.error("❌ No data found for this ID.")
        return

    st.title(f"🔗 Shared Output - {feature}")

    # Render feature
    if feature == "Quiz":
        render_quiz(content)
    elif feature == "Flashcards":
        render_flashcards(content)
    elif feature == "Flowchart":
        render_flowchart(content)
    elif feature == "Mindmap":
        render_mindmap(content)
    elif feature == "Summary":
        render_summary(content)
    else:
        st.warning("⚠️ Unsupported feature type.")
