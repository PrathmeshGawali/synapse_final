# features.py
import json
import re
import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
from .base import get_rag_context

client = Groq(api_key='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')

FLOWCHART_JSON_TEMPLATE = {
    "graph": {
        "nodes": [
            {"id": "start", "label": "[Start]", "style": "rounded"},
            {"id": "process1", "label": "[Process 1]", "style": "default"}
        ],
        "edges": [
            {"from": "start", "to": "process1", "label": ""}
        ]
    }
}

def generate_flowchart(vector_store) -> str:
    """Generate flowchart using RAG context with JSON validation"""
    try:
        context = get_rag_context(vector_store, "Generate flowchart structure", k=5)
        
        PROMPT_TEMPLATE = """
        Generate Mermaid.js flowchart from this context:
        {context}
        
        Requirements:
        - Use Flowchart LR (left-right) syntax
        - 4 levels maximum hierarchy
        - Clear node relationships
        - Valid JSON format
        - Node IDs must be lowercase with underscores
        - Labels must be in quotes if containing spaces
        
        Template: {template}
        """
        
        prompt = PROMPT_TEMPLATE.format(
            context=context,
            template=json.dumps(FLOWCHART_JSON_TEMPLATE, indent=2)
        )
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        json_data = json.loads(response.choices[0].message.content)
        return convert_json_to_mermaid(json_data)
        
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON response: {str(e)}")
        return ""
    except Exception as e:
        st.error(f"Flowchart generation failed: {str(e)}")
        return ""

def convert_json_to_mermaid(json_data: dict) -> str:
    """Convert JSON structure to Mermaid flowchart syntax with proper escaping"""
    direction = st.session_state.get("flowchart_direction", "LR")
    mermaid_code = f"flowchart {direction}\n"
    
    # Node styles mapping
    styles = {
        "rounded": "()",
        "default": "[]"
    }
    
    # Process nodes with sanitization
    nodes = {}
    id_mapping = {}
    for node in json_data.get("graph", {}).get("nodes", []):
        # Sanitize node ID
        original_id = node["id"]
        clean_id = re.sub(r'[^a-zA-Z0-9_]', '_', original_id).lower()
        id_mapping[original_id] = clean_id
        
        # Process label
        label = node["label"].strip("[]()")
        if any(c in label for c in {' ', '"', "'", '(', ')', '{', '}'}):
            label = f'"{label}"'
        
        style = styles.get(node.get("style", "default"), "[]")
        nodes[clean_id] = f"{clean_id}{style[0]}{label}{style[1]}"
    
    # Process edges with sanitized IDs
    edges = []
    for edge in json_data.get("graph", {}).get("edges", []):
        from_node = id_mapping.get(edge["from"], edge["from"])
        to_node = id_mapping.get(edge["to"], edge["to"])
        label = edge.get("label", "")
        
        from_node = re.sub(r'[^a-zA-Z0-9_]', '_', from_node).lower()
        to_node = re.sub(r'[^a-zA-Z0-9_]', '_', to_node).lower()
        
        if label:
            edges.append(f"{from_node} -->|\"{label}\"| {to_node}")
        else:
            edges.append(f"{from_node} --> {to_node}")
    
    # Build final code
    mermaid_code += "\n".join(nodes.values()) + "\n"
    mermaid_code += "\n".join(edges)
    
    return mermaid_code

def render_flowchart(mermaid_code: str):
    """Render interactive flowchart with proper Mermaid 10.9.3 initialization"""
    st.header("Interactive Flowchart")
    
    if not mermaid_code.startswith("flowchart"):
        st.error("Invalid flowchart format")
        st.code(mermaid_code)
        return
    
    components.html(
        f"""
        <div class="container" style="width:100%; height:800px; overflow:auto">
            <pre class="mermaid" style="font-size:1.2rem">
            {mermaid_code}
            </pre>
        </div>
        
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10.9.3/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{
                startOnLoad: true,
                securityLevel: 'loose',
                flowchart: {{ 
                    curve: 'basis',
                    htmlLabels: true
                }},
                theme: 'base',
                themeVariables: {{
                    primaryColor: '#D3D3D3',
                    edgeLabelBackground: '#F8F9FA'
                }}
            }});
        </script>
        
        <style>
            .mermaid svg {{
                transform-origin: 0 0;
                transition: transform 0.3s ease;
            }}
            .container {{
                border: 1px solid #eee;
                border-radius: 10px;
                padding: 20px;
                background: white;
            }}
        </style>
        """,
        height=800
    )
    
    # Diagram controls
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh Diagram"):
            st.rerun()
    with col2:
        st.selectbox("Layout Direction", ["LR", "TB"], key="flowchart_direction")