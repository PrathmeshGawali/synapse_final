import streamlit as st

def render_flashcards(flashcard_data: dict, flashcard_id: str = "default"):
    """Render interactive flashcards with animations and state management"""
    # Initialize session state with unique ID prefix
    state_prefix = f"fc_{flashcard_id}_"
    
    if state_prefix + 'index' not in st.session_state:
        st.session_state[state_prefix + 'index'] = 0
    if state_prefix + 'flipped' not in st.session_state:
        st.session_state[state_prefix + 'flipped'] = False
    if state_prefix + 'show_hint' not in st.session_state:
        st.session_state[state_prefix + 'show_hint'] = False

    # Validate input structure
    if not isinstance(flashcard_data, dict) or 'flashcards' not in flashcard_data:
        st.error("Invalid flashcard format - missing 'flashcards' field")
        st.json(flashcard_data)
        return
    
    flashcards = flashcard_data['flashcards']
    if not isinstance(flashcards, list) or len(flashcards) == 0:
        st.error("Invalid flashcard format - 'flashcards' must be a non-empty list")
        return

    st.header("📚 Flashcards")

    # Navigation controls
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Previous", key=f"{state_prefix}prev"):
            if st.session_state[state_prefix + 'index'] > 0:
                st.session_state[state_prefix + 'index'] -= 1
                st.session_state[state_prefix + 'flipped'] = False
                st.session_state[state_prefix + 'show_hint'] = False
    with col2:
        if st.button("Next ➡️", key=f"{state_prefix}next"):
            if st.session_state[state_prefix + 'index'] < len(flashcards)-1:
                st.session_state[state_prefix + 'index'] += 1
                st.session_state[state_prefix + 'flipped'] = False
                st.session_state[state_prefix + 'show_hint'] = False

    current_card = flashcards[st.session_state[state_prefix + 'index']]

    # Flashcard display with CSS animations
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
        transform: rotateY({"180deg" if st.session_state[state_prefix + 'flipped'] else "0deg"});
        cursor: pointer;
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
        padding: 30px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        font-size: 28px;
        text-align: center;
        font-weight: 500;
        border: 2px solid rgba(0,0,0,0.1);
        box-sizing: border-box;
        word-wrap: break-word;
        overflow: hidden;
    }}
    .flashcard-front {{
        background: #FFD700;
        color: #000000;
        border-color: #FFC000;
    }}
    .flashcard-back {{
        background: #FF6347;
        color: #FFFFFF;
        transform: rotateY(180deg);
        border-color: #FF4500;
    }}
    .flashcard:hover {{
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }}
    </style>
    
    <div class="flashcard-container">
        <div class="flashcard">
            <div class="flashcard-front">{current_card.get('question', 'Question missing')}</div>
            <div class="flashcard-back">{current_card.get('answer', 'Answer missing')}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Control buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Flip Card", key=f"{state_prefix}flip"):
            st.session_state[state_prefix + 'flipped'] = not st.session_state[state_prefix + 'flipped']
    with col2:
        if st.button("💡 Show Hint", key=f"{state_prefix}hint"):
            st.session_state[state_prefix + 'show_hint'] = not st.session_state[state_prefix + 'show_hint']

    # Hint display
    if st.session_state[state_prefix + 'show_hint']:
        st.info(f"**Hint:** {current_card.get('hint', 'No hint available')}")

    # Progress indicator
    st.write(f"Card {st.session_state[state_prefix + 'index'] + 1} of {len(flashcards)}")