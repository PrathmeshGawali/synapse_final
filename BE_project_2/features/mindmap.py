import json
import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
from .base import get_rag_context

client = Groq(api_key='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')

MINDMAP_JSON_TEMPLATE = {
    "graph": {
        "nodes": [
            {"id": "main_topic", "label": "(Central Concept)", "style": "rounded"},
            {"id": "subtopic1", "label": "[Key Aspect 1]", "style": "default"}
        ],
        "edges": [
            {"from": "main_topic", "to": "subtopic1", "label": ""}
        ]
    }
}

def generate_mindmap(vector_store) -> str:
    """Generate mindmap using RAG context with JSON validation"""
    try:
        context = get_rag_context(vector_store, "Generate mindmap structure", k=5)
        
        PROMPT_TEMPLATE = """
        Generate Mermaid.js mindmap from this context:
        {context}
        
        Requirements:
        - JSON format with nodes and edges
        - 3 hierarchical levels max
        - Short concise labels
        - No duplicate concepts
        
        Template: {template}
        """
        
        prompt = PROMPT_TEMPLATE.format(
            context=context,
            template=json.dumps(MINDMAP_JSON_TEMPLATE, indent=2)
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
        st.error(f"Mindmap generation failed: {str(e)}")
        return ""

def convert_json_to_mermaid(json_data: dict) -> str:
    """Convert JSON structure to Mermaid syntax"""
    mermaid_code = "mindmap\n"
    
    # Build node hierarchy
    nodes = {n["id"]: n for n in json_data.get("graph", {}).get("nodes", [])}
    edges = json_data.get("graph", {}).get("edges", [])
    
    # Find root nodes
    child_nodes = set(e["to"] for e in edges)
    root_nodes = [n for n in nodes if n not in child_nodes]
    
    # Recursive build function
    def build_branch(node_id, depth=0):
        nonlocal nodes, edges
        node = nodes.get(node_id, {})
        branch = "  " * depth + node.get("label", "") + "\n"
        
        children = [e["to"] for e in edges if e["from"] == node_id]
        for child in children:
            branch += build_branch(child, depth+1)
            
        return branch
    
    for root in root_nodes:
        mermaid_code += build_branch(root)
        
    return mermaid_code

def render_mindmap(mermaid_code: str):
    """Render interactive mindmap with zoom capabilities"""
    st.header("Interactive Mindmap")
    
    if not mermaid_code.startswith("mindmap"):
        st.error("Invalid mindmap format")
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
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{
                startOnLoad: true,
                securityLevel: 'loose',
                theme: 'base',
                themeVariables: {{
                    primaryColor: '#FFD700',
                    edgeLabelBackground: '#F6F6F6'
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
            }}
        </style>
        """,
        height=800
    )
    
    # Zoom controls
    col1, col2, col3 = st.columns(3)
    with col1: st.button("🔍 Zoom In", help="Increase zoom level")
    with col2: st.button("🔎 Zoom Out", help="Decrease zoom level")
    with col3: st.button("🗑️ Reset View", help="Reset to default zoom")