# pages/view_outputs.py
import streamlit as st
import json, zipfile, io, uuid
from datetime import datetime

from features.renderers.quiz import render_quiz
from features.renderers.flashcards import render_flashcards
from features.renderers.summarize import render_summary
from features.renderers.flowchart import render_flowchart
from features.renderers.mindmap import render_mindmap  # NEW

# — Page Setup —
st.set_page_config(page_title="View SynapseIQ Outputs", layout="wide")
st.title("📂 View SynapseIQ Outputs")

# — Session State Init —
if 'processed_files' not in st.session_state:
    st.session_state.processed_files = []
if 'errors' not in st.session_state:
    st.session_state.errors = []

# — Feature Detection —
def detect_feature_type(raw):
    """Inspect the full JSON dict to decide feature_type."""
    if not isinstance(raw, dict):
        return "unknown"
    ft = raw.get("feature_type", "").lower()
    if ft in ("quiz", "flashcards", "summary", "flowchart", "mindmap"):
        return ft

    # fallback by keys or content prefix
    if "mcqs" in raw:
        return "quiz"
    if "flashcards" in raw:
        return "flashcards"
    c = raw.get("content")
    if isinstance(c, str):
        txt = c.strip().lower()
        if txt.startswith("flowchart"):
            return "flowchart"
        if txt.startswith("mindmap"):
            return "mindmap"
    return "unknown"

# — File Processors —
def process_json_file(blob: bytes, name: str):
    try:
        raw = json.loads(blob.decode())
        ft = detect_feature_type(raw)
        # Unwrap content if present
        content = raw.get("content", raw)
        return {
            "id":      str(uuid.uuid4()),
            "filename": name,
            "feature_type": ft,
            "content": content,
            "raw":     raw,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        st.session_state.errors.append(f"{name}: {e}")
        return None

def process_zip_file(blob: bytes):
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        for info in zf.infolist():
            if info.filename.lower().endswith(".json"):
                data = zf.read(info.filename)
                out = process_json_file(data, info.filename)
                if out:
                    st.session_state.processed_files.append(out)

# — Upload UI —
uploads = st.file_uploader(
    "Upload JSON or ZIP files",
    type=["json", "zip"],
    accept_multiple_files=True
)
if st.button("Process Uploads") and uploads:
    st.session_state.processed_files = []
    st.session_state.errors = []
    for up in uploads:
        blob = up.getvalue()
        if up.name.lower().endswith(".zip"):
            process_zip_file(blob)
        else:
            out = process_json_file(blob, up.name)
            if out:
                st.session_state.processed_files.append(out)

# — Show Errors —
if st.session_state.errors:
    with st.expander("⚠️ Processing Errors"):
        for err in st.session_state.errors:
            st.error(err)

# — Render Selected Output —
if st.session_state.processed_files:
    opts = [
        f"{f['feature_type'].title()} — {f['filename']}"
        for f in st.session_state.processed_files
    ]
    idx = st.selectbox("Select output to view", range(len(opts)), format_func=lambda i: opts[i])
    sel = st.session_state.processed_files[idx]

    st.divider()
    st.subheader(f"{sel['feature_type'].title()} — {sel['filename']}")

    ft      = sel['feature_type']
    content = sel['content']
    raw     = sel['raw']
    sid     = sel['id']

    if ft == 'quiz':
        render_quiz(content, sid)

    elif ft == 'flashcards':
        if isinstance(content, dict) and "flashcards" in content:
            render_flashcards(content, sid)
        elif isinstance(content, list):
            render_flashcards({"flashcards": content}, sid)
        else:
            st.error("Invalid flashcard format")
            st.json(content)

    elif ft == 'summary':
        # wrap metadata back in
        render_summary({
            "content":   raw.get("content", ""),
            "feature_type": raw.get("feature_type"),
            "timestamp": sel["timestamp"]
        }, sid)

    elif ft == 'flowchart':
        render_flowchart({ "content": raw.get("content", "") }, sid)

    elif ft == 'mindmap':
        render_mindmap({ "content": raw.get("content", "") }, sid)

    else:
        st.warning("No dedicated renderer for this format")
        st.json(content)

else:
    st.info("Upload JSON or ZIP files containing generated outputs")
