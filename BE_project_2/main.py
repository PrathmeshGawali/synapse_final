import streamlit as st
from utils.processing import process_inputs, create_vector_db
from features import *
from streamlit.components.v1 import html
import uuid
import json
from datetime import datetime

def run_main():
    # Page configuration
    st.set_page_config(page_title="SynapseIQ", layout="wide")

    # Initialize session state
    if 'vector_store' not in st.session_state:
        st.session_state.vector_store = None
    if 'all_outputs' not in st.session_state:
        st.session_state.all_outputs = {}
    if 'current_feature' not in st.session_state:
        st.session_state.current_feature = None

    # ----------------------
    # Left Panel: Inputs
    # ----------------------
    def input_panel():
        st.header("📥 Upload Content")
        files = st.file_uploader("Upload PDFs", accept_multiple_files=True)
        url   = st.text_input("Enter Website URL")
        yt    = st.text_input("YouTube Link")
        if st.button("🚀 Process Documents"):
            if files or url or yt:
                with st.spinner("Processing..."):
                    try:
                        text = process_inputs(pdf_files=files, url=url, yt_link=yt)
                        st.session_state.vector_store = create_vector_db(text)
                        st.success("✅ Done!")
                    except Exception as e:
                        st.error(f"❌ {e}")
            else:
                st.warning("⚠️ Provide input first!")

    # ----------------------
    # Middle Panel: Output
    # ----------------------
    def output_panel():
        st.header("📊 Output")
        key = st.session_state.current_feature
        if key and key in st.session_state.all_outputs:
            render_feature_output(st.session_state.all_outputs[key])

        if st.session_state.all_outputs:
            with st.expander("📚 All Generated Outputs"):
                for feat, out in st.session_state.all_outputs.items():
                    if st.button(f"View {feat}", key=f"view_{feat}"):
                        st.session_state.current_feature = feat

        if st.session_state.all_outputs and st.button("💾 Download All"):
            download_all_outputs()

    def render_feature_output(o):
        # download / screenshot buttons
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📥 Download JSON", key=f"dl_{o['id']}"):
                download_output(o)
        with c2:
            if st.button("📸 Capture Page", key=f"snap_{o['id']}"):
                capture_full_page()

        # actual content
        ft, content = o['feature_type'], o['content']
        if ft == "Quiz":
            render_quiz(content)
        elif ft == "Flashcards":
            render_flashcards(content)
        elif ft == "Flowchart":
            render_flowchart(content)
        elif ft == "Mindmap":
            render_mindmap(content)
        elif ft == "Summary":
            render_summary(content)

    # ----------------------
    # Full-Page Screenshot
    # ----------------------
    def capture_full_page():
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"synapseiq-fullpage-{ts}.png"
        # height must be > 0 or Streamlit will drop it
        html(f"""
        <script>
          // 1) Dynamically load html2canvas
          const s = document.createElement('script');
          s.src = 'https://html2canvas.hertzen.com/dist/html2canvas.min.js';
          s.onload = () => {{
            // 2) Once ready, capture the entire document
            html2canvas(document.documentElement, {{
              useCORS: true,
              scrollY: -window.scrollY,
              windowWidth: document.documentElement.scrollWidth,
              windowHeight: document.documentElement.scrollHeight
            }}).then(canvas => {{
              const link = document.createElement('a');
              link.download = '{filename}';
              link.href = canvas.toDataURL('image/png');
              link.click();
            }}).catch(e => {{
              alert('Screenshot failed: ' + e);
            }});
          }};
          document.body.appendChild(s);
        </script>
        """, height=1)

    # ----------------------
    # Right Panel: Features
    # ----------------------
    def feature_panel():
        st.header("✨ Features")
        feat = st.radio("Choose Feature", ["Quiz","Flashcards","Flowchart","Mindmap","Summary"])
        if st.button("🚀 Run Feature"):
            if not st.session_state.vector_store:
                st.warning("⚠️ Process docs first!")
                return
            with st.spinner(f"Generating {feat}…"):
                try:
                    if feat == "Quiz":
                        out = generate_quiz(st.session_state.vector_store)
                    elif feat == "Flashcards":
                        out = generate_flashcards(st.session_state.vector_store)
                    elif feat == "Flowchart":
                        out = generate_flowchart(st.session_state.vector_store)
                    elif feat == "Mindmap":
                        out = generate_mindmap(st.session_state.vector_store)
                    else:
                        out = generate_summary(st.session_state.vector_store)
                except Exception as e:
                    st.error(f"❌ {e}")
                    return

            if out:
                id_ = str(uuid.uuid4())
                st.session_state.all_outputs[feat] = {
                    "id": id_,
                    "feature_type": feat,
                    "content": out,
                    "timestamp": datetime.now().isoformat()
                }
                st.session_state.current_feature = feat
                st.success("✅ Saved!")

    # ----------------------
    # Utilities
    # ----------------------
    def download_output(o):
        data = json.dumps(o, indent=2)
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button("Download JSON", data=data,
            file_name=f"synapseiq_{o['feature_type']}_{ts}.json",
            mime="application/json")

    def download_all_outputs():
        import zipfile, io
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for feat,o in st.session_state.all_outputs.items():
                zf.writestr(f"{feat}.json", json.dumps(o,indent=2))
        st.download_button("Download ZIP", data=buf.getvalue(),
            file_name=f"synapseiq_outputs_{ts}.zip",
            mime="application/zip")

    # ----------------------
    # Layout
    # ----------------------
    c1, c2, c3 = st.columns([1,2,1])
    with c1: input_panel()
    with c2: output_panel()
    with c3: feature_panel()

if __name__ == "__main__":
    run_main()
