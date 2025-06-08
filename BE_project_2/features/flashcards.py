# features.py
import json
import streamlit as st
from groq import Groq
from .base import get_rag_context

client = Groq(api_key='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')

# Common response format
FLASHCARD_JSON = {
    "flashcards": [
        {
            "question": "sample question",
            "answer": "sample answer",
            "hint": "sample hint"
        }
    ] * 5
}

def generate_flashcards(vector_store) -> list:
    """Generate flashcards using RAG context with validation"""
    try:
        context = get_rag_context(vector_store, "Generate flashcards", k=5)
        
        PROMPT_TEMPLATE = """
        Text: {context}
        You are an expert in generating flashcards based on provided content.
        Create 5 easy level flashcards with questions, answers, and hints.
        Requirements:
        - Questions must be directly based on the text
        - Answers should be concise but complete
        - Hints should help without giving away answers
        - No duplicate questions
        
        Format using this JSON structure:
        {response_json}
        """
        
        prompt = PROMPT_TEMPLATE.format(
            context=context,
            response_json=json.dumps(FLASHCARD_JSON)
        )
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        flashcard_data = json.loads(response.choices[0].message.content)
        
        # Validate response structure
        if "flashcards" not in flashcard_data or len(flashcard_data["flashcards"]) != 5:
            st.error("Invalid flashcard format generated")
            return None
            
        return flashcard_data
        
    except Exception as e:
        st.error(f"Error generating flashcards: {str(e)}")
        return None

def render_flashcards(flashcard_data: dict):
    """Render interactive flashcard interface with animations"""
    # Initialize session state
    if 'fc_index' not in st.session_state:
        st.session_state.fc_index = 0
    if 'fc_flipped' not in st.session_state:
        st.session_state.fc_flipped = False
    if 'fc_show_hint' not in st.session_state:
        st.session_state.fc_show_hint = False

    flashcards = flashcard_data.get("flashcards", [])
    
    st.header("Flashcards")
    
    if not flashcards:
        st.warning("No flashcards generated")
        return

    # Navigation controls
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Previous") and st.session_state.fc_index > 0:
            st.session_state.fc_index -= 1
            st.session_state.fc_flipped = False
            st.session_state.fc_show_hint = False
    with col2:
        if st.button("Next ➡️") and st.session_state.fc_index < len(flashcards)-1:
            st.session_state.fc_index += 1
            st.session_state.fc_flipped = False
            st.session_state.fc_show_hint = False

    current_card = flashcards[st.session_state.fc_index]

    # Flashcard display
    st.markdown(f"""
    <style>
    .flashcard-container {{
        width: 640px;
        height: 360px;
        perspective: 1000px;
        margin: 20px auto;
    }}
    .flashcard {{
        width: 100%;
        height: 100%;
        position: relative;
        transform-style: preserve-3d;
        transition: transform 0.6s;
        transform: rotateY({"180deg" if st.session_state.fc_flipped else "0deg"});
    }}
    .flashcard-front, .flashcard-back {{
        position: absolute;
        width: 100%;
        height: 100%;
        backface-visibility: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        font-size: 24px;
        text-align: center;
    }}
    .flashcard-front {{
        background: #FFD700;
        color: #000;
    }}
    .flashcard-back {{
        background: #FF6347;
        color: #fff;
        transform: rotateY(180deg);
    }}
    </style>
    
    <div class="flashcard-container">
        <div class="flashcard">
            <div class="flashcard-front">{current_card['question']}</div>
            <div class="flashcard-back">{current_card['answer']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Control buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Flip Card"):
            st.session_state.fc_flipped = not st.session_state.fc_flipped
    with col2:
        if st.button("💡 Show Hint"):
            st.session_state.fc_show_hint = not st.session_state.fc_show_hint

    if st.session_state.fc_show_hint:
        st.info(f"**Hint:** {current_card.get('hint', 'No hint available')}")

    # Progress indicator
    st.write(f"Card {st.session_state.fc_index + 1} of {len(flashcards)}")