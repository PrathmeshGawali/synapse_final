import streamlit as st

def render_quiz(quiz_data: dict, quiz_id: str = "default"):
    """Render interactive quiz with improved validation"""
    # Validate input structure
    if not isinstance(quiz_data, dict) or 'mcqs' not in quiz_data:
        st.error("Invalid quiz format - missing 'mcqs' field")
        st.json(quiz_data)
        return

    if not isinstance(quiz_data['mcqs'], list) or len(quiz_data['mcqs']) == 0:
        st.error("Invalid quiz format - 'mcqs' must be a non-empty list")
        return

    state_prefix = f"quiz_{quiz_id}_"

    # Initialize session state
    if f"{state_prefix}submitted" not in st.session_state:
        st.session_state[f"{state_prefix}submitted"] = False
    if f"{state_prefix}selected" not in st.session_state:
        st.session_state[f"{state_prefix}selected"] = [None] * len(quiz_data["mcqs"])

    st.header("📝 Quiz")

    for idx, question in enumerate(quiz_data["mcqs"]):
        options = [f"{k}: {v}" for k, v in question["options"].items()]

        prev_sel = st.session_state[f"{state_prefix}selected"][idx]
        default_idx = options.index(prev_sel) if prev_sel in options else 0

        with st.expander(f"Question {idx + 1}"):
            selection = st.radio(
                question["mcq"],
                options=options,
                index=default_idx,
                key=f"{state_prefix}q{idx}"
            )
            st.session_state[f"{state_prefix}selected"][idx] = selection

    if st.button("Submit Quiz", key=f"{state_prefix}submit"):
        st.session_state[f"{state_prefix}submitted"] = True

        score = 0
        for idx, q in enumerate(quiz_data["mcqs"]):
            selected = st.session_state[f"{state_prefix}selected"][idx]
            if selected and selected.startswith(f"{q['correct']}:"):
                score += 1

        st.success(f"Score: {score}/{len(quiz_data['mcqs'])}")
        st.subheader("Quiz Review")

        for idx, q in enumerate(quiz_data["mcqs"]):
            with st.expander(f"Question {idx + 1}: {q['mcq']}", expanded=False):
                user_answer = st.session_state[f"{state_prefix}selected"][idx] or "Not answered"
                correct_answer = f"{q['correct']}: {q['options'][q['correct']]}"
                st.markdown(f"**Your answer:** {user_answer}")
                st.markdown(f"**Correct answer:** {correct_answer}")
