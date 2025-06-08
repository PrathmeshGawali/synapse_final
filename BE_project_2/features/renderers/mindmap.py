# features/renderers/mindmap.py
import streamlit as st
import streamlit.components.v1 as components
import re

def render_mindmap(mindmap_data: dict, mindmap_id: str = "default"):
    """Render interactive mindmap with Mermaid.js"""
    state_prefix = f"mindmap_{mindmap_id}_"
    st.session_state.setdefault(state_prefix + 'zoom', 1.0)

    st.header("🧠 Mindmap")

    # Extract Mermaid code
    mermaid_code = ""
    c = mindmap_data.get("content") if isinstance(mindmap_data, dict) else ""
    if isinstance(c, str) and c.strip().startswith("mindmap"):
        mermaid_code = c
    elif isinstance(mindmap_data, dict) and "graph" in mindmap_data:
        mermaid_code = convert_json_to_mermaid(mindmap_data)

    if not mermaid_code:
        st.error("Invalid mindmap format")
        st.json(mindmap_data)
        return

    zoom = st.session_state[state_prefix + 'zoom']
    zoom_style = f"transform: scale({zoom});"

    components.html(f"""
    <div class="mindmap-container" style="width:100%; height:600px; overflow:auto">
      <div style="{zoom_style}">
        <pre class="mermaid">
{mermaid_code}
        </pre>
      </div>
    </div>
    <script type="module">
      import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
      mermaid.initialize({{
        startOnLoad: true,
        securityLevel: 'loose',
        mindmap: {{ useMaxWidth: true }},
        theme: 'forest',
        themeVariables: {{
          primaryColor: '#FFD700',
          primaryTextColor: '#000'
        }}
      }});
    </script>
    <style>
      .mindmap-container {{
        border:1px solid #eee; border-radius:8px; padding:16px; background:#fff;
      }}
      .mermaid svg {{ transform-origin:0 0; transition:transform 0.3s ease; }}
    </style>
    """, height=600)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔍 Zoom In", key=f"{state_prefix}in"):
            st.session_state[state_prefix + 'zoom'] = min(2.0, zoom + 0.1)
            st.experimental_rerun()
    with col2:
        if st.button("🔎 Zoom Out", key=f"{state_prefix}out"):
            st.session_state[state_prefix + 'zoom'] = max(0.5, zoom - 0.1)
            st.experimental_rerun()
    with col3:
        if st.button("🗑️ Reset View", key=f"{state_prefix}reset"):
            st.session_state[state_prefix + 'zoom'] = 1.0
            st.experimental_rerun()

def convert_json_to_mermaid(json_data: dict) -> str:
    """Convert JSON structure to Mermaid mindmap syntax"""
    nodes = {n["id"]: n for n in json_data["graph"].get("nodes", [])}
    edges = json_data["graph"].get("edges", [])
    mermaid_code = "mindmap\n"

    # find roots
    child_ids = {e["to"] for e in edges}
    roots = [nid for nid in nodes if nid not in child_ids]

    def build_branch(nid, depth=0):
        indent = "  " * depth
        label = nodes[nid].get("label", nid)
        branch = f"{indent}{label}\n"
        for e in edges:
            if e["from"] == nid:
                branch += build_branch(e["to"], depth+1)
        return branch

    for r in roots:
        mermaid_code += build_branch(r)
    return mermaid_code
