import json
import re
import streamlit as st
from groq import Groq
from .base import get_rag_context
from pypdf import PdfReader
from jsonschema import validate, ValidationError

# Initialize Groq client
client = Groq(api_key='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')

# -----------------------------
# 1. Prompt Template Definition
# -----------------------------
PROMPT_TEMPLATE = """
Text: {context}

Generate a 10-question multiple choice quiz (easy difficulty) based on the text. Follow these rules strictly:

1. Use EXACTLY this JSON structure:
{{
  "mcqs": [
    {{
      "mcq": "Question text?",
      "options": {{
        "a": "Option A",
        "b": "Option B",
        "c": "Option C",
        "d": "Option D"
      }},
      "correct": "a"
    }}
  ]
}}

2. Requirements:
- All 10 questions MUST follow this structure
- "options" MUST have EXACTLY keys a, b, c, d
- "correct" MUST be one letter: a, b, c, or d
- No trailing commas in JSON
- No missing fields

Example valid question:
{{
  "mcq": "What is Python?",
  "options": {{
    "a": "Snake",
    "b": "Programming language",
    "c": "Dance",
    "d": "Mountain"
  }},
  "correct": "b"
}}

Output ONLY raw JSON (no markdown, no extra text).
"""

# -----------------------------
# 2. JSON Validation & Repair
# -----------------------------
def validate_and_repair(quiz_str: str) -> dict:
    """
    Fix common JSON errors before parsing:
    - Remove trailing commas
    - Attempt to balance braces
    """
    try:
        # Remove trailing commas before objects and arrays
        quiz_str = re.sub(r',\s*}', '}', quiz_str)
        quiz_str = re.sub(r',\s*]', ']', quiz_str)

        # Fix missing quotes around keys if possible (simple heuristic)
        quiz_str = re.sub(r'(\n\s*)([a-zA-Z0-9_]+)\s*:', r'\1"\2":', quiz_str)

        # If there are more '{' than '}', append missing braces
        if quiz_str.count('{') > quiz_str.count('}'):
            quiz_str += '}' * (quiz_str.count('{') - quiz_str.count('}'))

        return json.loads(quiz_str)
    except json.JSONDecodeError as e:
        st.error(f"JSON repair failed: {str(e)}")
        return None

# -----------------------------
# 3. JSON Schema for Strict Enforcement
# -----------------------------
QUIZ_SCHEMA = {
    "type": "object",
    "properties": {
        "mcqs": {
            "type": "array",
            "minItems": 10,
            "maxItems": 10,
            "items": {
                "type": "object",
                "properties": {
                    "mcq": {"type": "string"},
                    "options": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "string"},
                            "b": {"type": "string"},
                            "c": {"type": "string"},
                            "d": {"type": "string"}
                        },
                        "required": ["a", "b", "c", "d"],
                        "additionalProperties": False
                    },
                    "correct": {
                        "type": "string",
                        "enum": ["a", "b", "c", "d"]
                    }
                },
                "required": ["mcq", "options", "correct"]
            }
        }
    },
    "required": ["mcqs"]
}

# -----------------------------
# 4. Generate Quiz with Retries
# -----------------------------
def generate_quiz(vector_store) -> dict:
    """
    Generate a 10-question MCQ quiz (easy difficulty) using a RAG context.
    Implements:
      - Retry mechanism (up to 3 attempts)
      - JSON validation & repair
      - Schema enforcement
      - Detailed error logging to Streamlit

    Returns:
      - A dict matching QUIZ_SCHEMA on success
      - None on failure
    """
    model = "llama3-70b-8192"
    max_attempts = 3

    # Step 1: Build RAG context
    try:
        context = get_rag_context(vector_store, "Generate quiz questions", k=5)
    except Exception as e:
        st.error(f"Failed to retrieve RAG context: {str(e)}")
        return None

    # Step 2: Attempt generation with retries
    for attempt in range(1, max_attempts + 1):
        try:
            # Construct prompt
            prompt = PROMPT_TEMPLATE.format(context=context)

            # Call the LLM without forcing response_format, to let it return plain text
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )

            raw_content = response.choices[0].message.content

            # 4a. Validate & Repair JSON
            quiz_data = validate_and_repair(raw_content)
            if not quiz_data:
                st.error(f"Attempt {attempt}: JSON repair returned None.")
                continue

            # 4b. Schema Validation
            try:
                validate(instance=quiz_data, schema=QUIZ_SCHEMA)
            except ValidationError as ve:
                st.error(f"Attempt {attempt}: Schema validation failed: {ve.message}")
                continue

            # 4c. Final Structure Checks
            mcqs = quiz_data.get("mcqs", [])
            if len(mcqs) != 10:
                st.error(f"Attempt {attempt}: Expected 10 questions, got {len(mcqs)}.")
                continue

            # Ensure each question has correct fields
            malformed = False
            for idx, q in enumerate(mcqs):
                if not all(k in q for k in ["mcq", "options", "correct"]):
                    st.error(f"Attempt {attempt}: Question {idx+1} missing fields.")
                    malformed = True
                    break
                if sorted(q["options"].keys()) != ["a", "b", "c", "d"]:
                    st.error(f"Attempt {attempt}: Question {idx+1} has invalid option keys.")
                    malformed = True
                    break
                if q["correct"] not in ["a", "b", "c", "d"]:
                    st.error(f"Attempt {attempt}: Question {idx+1} has invalid correct letter.")
                    malformed = True
                    break

            if malformed:
                continue

            # All checks passed
            return quiz_data

        except Exception as e:
            st.error(f"Attempt {attempt}, model '{model}' failed with error: {str(e)}")

    # If we reach here, all attempts failed
    st.error("All attempts to generate the quiz have failed.")
    return None

# -----------------------------
# 5. Render Quiz with Resilience
# -----------------------------
def render_quiz(quiz_data: dict):
    """
    Render an interactive 10-question quiz.
    Stores:
      - st.session_state.selected_options: List of user-selected answers (strings)
      - st.session_state.correct_answers: List of correct answer texts
      - st.session_state.quiz_submitted: Bool to prevent multiple submissions

    Fault-tolerant:
      - Uses safe getters with defaults
      - Catches exceptions per question
    """
    if not quiz_data or "mcqs" not in quiz_data:
        st.error("Quiz data is missing or malformed. Cannot render quiz.")
        return

    # Initialize session state variables
    if 'quiz_submitted' not in st.session_state:
        st.session_state.quiz_submitted = False
    if 'selected_options' not in st.session_state:
        st.session_state.selected_options = [None] * len(quiz_data["mcqs"])
    if 'correct_answers' not in st.session_state:
        # Build correct answer texts or empty strings if missing
        correct_list = []
        for q in quiz_data.get("mcqs", []):
            opts = q.get("options", {})
            corr_key = q.get("correct", "")
            correct_list.append(opts.get(corr_key, ""))
        st.session_state.correct_answers = correct_list

    st.header("Generated Quiz")

    # Render each question inside an expander
    for idx, q in enumerate(quiz_data.get("mcqs", [])):
        try:
            question_text = q.get("mcq", f"Question {idx+1} is malformed.")
            options_dict = q.get("options", {})
            sorted_keys = sorted(options_dict.keys())
            # Build a list like ["a: Option A", "b: Option B", ...]
            options_list = [f"{k}: {options_dict.get(k, '')}" for k in sorted_keys]

            with st.expander(f"Question {idx+1}"):
                # Default index to 0 if previously answered, else 0
                default_index = 0
                prev_selection = st.session_state.selected_options[idx]
                if isinstance(prev_selection, str):
                    try:
                        default_index = options_list.index(prev_selection)
                    except ValueError:
                        default_index = 0

                selection = st.radio(
                    question_text,
                    options=options_list,
                    index=default_index,
                    key=f"q{idx}"
                )
                st.session_state.selected_options[idx] = selection

        except Exception:
            st.error(f"Error rendering question {idx+1}")

    # Submission Button
    if st.button("Submit Quiz") and not st.session_state.quiz_submitted:
        st.session_state.quiz_submitted = True

        # Calculate score: compare "a: Option A" style strings
        score = 0
        for idx, q in enumerate(quiz_data.get("mcqs", [])):
            selected = st.session_state.selected_options[idx]
            correct_key = q.get("correct", "")
            correct_text = q.get("options", {}).get(correct_key, "")
            if selected == f"{correct_key}: {correct_text}":
                score += 1

        st.success(f"Score: {score}/{len(quiz_data['mcqs'])}")
        st.header("Quiz Review")

        # Show review for each question
        for idx, q in enumerate(quiz_data["mcqs"]):
            try:
                question_text = q.get("mcq", f"Question {idx+1} is malformed.")
                selected = st.session_state.selected_options[idx]
                correct_key = q.get("correct", "")
                correct_text = q.get("options", {}).get(correct_key, "")

                st.subheader(f"Question {idx+1}: {question_text}")
                st.write(f"Your answer: {selected if selected else 'No answer provided'}")
                st.write(f"Correct answer: {correct_key}: {correct_text}")
                st.write("---")
            except Exception:
                st.error(f"Error showing review for question {idx+1}")
