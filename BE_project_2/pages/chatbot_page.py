import streamlit as st
import fitz  # PyMuPDF for PDF rendering
from groq import Groq
import threading

# ✅ Groq Client Initialization
client = Groq(api_key='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')


# 💡 Custom CSS for larger and sharper PDF viewer
# 🔧 Custom CSS for smaller UI layout
st.markdown(
    """
    <style>
    .reportview-container {
        max-width: 90%;
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100px;
        height: 38px;
        font-size: 14px;
    }
    .stTextInput>div>div>input {
        font-size: 13px;
        padding: 6px;
    }
    .stTextArea>div>textarea {
        font-size: 13px;
        padding: 6px;
    }
    .stImage > img {
        max-width: 100%;
        height: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.title("📚 PDF Viewer with Chatbot")

# ✅ Session state for page navigation
if "current_page" not in st.session_state:
    st.session_state.current_page = 0

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "pdf_context" not in st.session_state:
    st.session_state.pdf_context = ""

# ✅ PDF Viewer (Top Section)
st.header("📄 PDF Viewer")

uploaded_file = st.file_uploader("Upload PDF", type="pdf")

def extract_pdf_content(uploaded_file):
    """Extract full PDF content in the background."""
    pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    full_text = ""
    
    for page_num in range(len(pdf)):
        page = pdf.load_page(page_num)
        full_text += page.get_text()

    # Store the PDF content in session state as context
    st.session_state.pdf_context = full_text

if uploaded_file:
    pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")

    # Navigation buttons with wider spacing
    total_pages = len(pdf)
    col_left, col_mid, col_right = st.columns([1, 3, 1])

    # Page Up and Down buttons
    with col_left:
        if st.button("⬅️ Prev"):
            st.session_state.current_page = max(0, st.session_state.current_page - 1)

    with col_right:
        if st.button("➡️ Next"):
            st.session_state.current_page = min(total_pages - 1, st.session_state.current_page + 1)

    # Display current page
    st.write(f"📄 Page {st.session_state.current_page + 1} of {total_pages}")

    # ✅ Render the current page with high resolution
    current_page = pdf.load_page(st.session_state.current_page)

    # 🛠️ High-resolution rendering
    zoom = 1.8  # 2x magnification for sharpness
    mat = fitz.Matrix(zoom, zoom)  # Zooming for higher DPI
    img = current_page.get_pixmap(matrix=mat)

    # Display sharper PDF image
    st.image(img.tobytes(), use_container_width=True, caption=f"Page {st.session_state.current_page + 1}")

    # Extract and display text
    text = current_page.get_text()
    if text:
        st.text_area("📄 Extracted Text", text, height=400)
    else:
        st.warning("No text detected on this page!")

# 🛠️ Add some vertical spacing
st.write("\n\n")

# 🤖 Chatbot (Bottom Section)
st.header("💬 Chatbot")


# Display chat history
for message in st.session_state.chat_history:
    st.write(message)

# User input
user_input = st.text_input("Ask your question")

def chat_with_model(user_input):
    """Chat with Groq API and include background PDF context."""
    
    # Include background PDF context if available
    context = st.session_state.pdf_context if "pdf_context" in st.session_state else ""

    # Construct prompt
    prompt = f"""
    Context: {context}
    User: {user_input}
    Model: Provide a detailed and contextually accurate response based on the PDF content.
    """

    # Groq API call
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_completion_tokens=1024,
        top_p=1,
        stream=False,
    )

    return response.choices[0].message.content

if user_input:
    # Backend call to LLM
    response = chat_with_model(user_input)

    # Store the interaction
    st.session_state.chat_history.append(f"🧑: {user_input}")
    st.session_state.chat_history.append(f"🤖: {response}")

    # Display the latest exchange
    st.write(f"🧑: {user_input}")
    st.write(f"🤖: {response}")