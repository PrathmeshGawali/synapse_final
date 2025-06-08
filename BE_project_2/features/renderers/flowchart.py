import streamlit as st
import streamlit.components.v1 as components
import re

def render_flowchart(flowchart_data: dict, flowchart_id: str = "default"):
    """Render interactive flowchart with Mermaid.js"""
    # Initialize session state for this specific flowchart
    state_prefix = f"flowchart_{flowchart_id}_"
    
    if state_prefix + 'direction' not in st.session_state:
        st.session_state[state_prefix + 'direction'] = "LR"
    
    st.header("📊 Flowchart")
    
    # Extract mermaid code from different possible formats
    mermaid_code = ""
    if isinstance(flowchart_data, str) and flowchart_data.startswith("flowchart"):
        mermaid_code = flowchart_data
    elif isinstance(flowchart_data, dict) and "content" in flowchart_data:
        if isinstance(flowchart_data["content"], str) and flowchart_data["content"].startswith("flowchart"):
            mermaid_code = flowchart_data["content"]
    elif isinstance(flowchart_data, dict) and "graph" in flowchart_data:
        mermaid_code = convert_json_to_mermaid(flowchart_data)
    
    if not mermaid_code:
        st.error("Invalid flowchart format")
        st.json(flowchart_data)
        return
    
    # Update direction if present in the code
    direction_match = re.search(r"flowchart\s+(\w+)", mermaid_code)
    if direction_match:
        st.session_state[state_prefix + 'direction'] = direction_match.group(1)
    
    # Render the flowchart
    components.html(
        f"""
        <div class="flowchart-container">
            <pre class="mermaid">
            {mermaid_code}
            </pre>
        </div>
        
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10.9.3/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{
                startOnLoad: true,
                securityLevel: 'loose',
                flowchart: {{ 
                    useMaxWidth: true,
                    htmlLabels: true,
                    curve: 'basis'
                }},
                theme: 'default',
                themeVariables: {{
                    primaryColor: '#f0f2f6',
                    edgeLabelBackground: '#ffffff',
                    fontSize: '16px'
                }}
            }});
        </script>
        
        <style>
            .flowchart-container {{
                width: 100%;
                height: 600px;
                border: 1px solid #eee;
                border-radius: 8px;
                padding: 16px;
                background: white;
                overflow: auto;
            }}
            .mermaid svg {{
                transform-origin: 0 0;
                transition: transform 0.3s ease;
            }}
        </style>
        """,
        height=600
    )
    
    # Controls
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh", key=f"{state_prefix}refresh"):
            st.rerun()
    with col2:
        new_direction = st.selectbox(
            "Layout Direction",
            ["LR", "TB", "RL", "BT"],
            index=["LR", "TB", "RL", "BT"].index(st.session_state[state_prefix + 'direction']),
            key=f"{state_prefix}direction_select"
        )
        
        if new_direction != st.session_state[state_prefix + 'direction']:
            st.session_state[state_prefix + 'direction'] = new_direction
            # Update the direction in the mermaid code
            mermaid_code = re.sub(
                r"flowchart\s+\w+",
                f"flowchart {new_direction}",
                mermaid_code
            )
            st.rerun()

def convert_json_to_mermaid(json_data: dict) -> str:
    """Convert JSON structure to Mermaid syntax"""
    direction = "LR"  # Default direction
    
    if not isinstance(json_data, dict) or "graph" not in json_data:
        return ""
    
    # Get direction if specified
    if "direction" in json_data.get("graph", {}):
        direction = json_data["graph"]["direction"]
    
    mermaid_code = f"flowchart {direction}\n"
    
    # Process nodes
    node_styles = {
        "rounded": "({label})",
        "default": "[{label}]",
        "circle": "(({label}))",
        "rhombus": "{{ {label} }}"
    }
    
    for node in json_data["graph"].get("nodes", []):
        node_id = re.sub(r'[^a-zA-Z0-9_]', '_', node["id"]).lower()
        label = node.get("label", node_id).replace('"', '\\"')
        style = node_styles.get(node.get("style", "default"), "[{label}]")
        
        mermaid_code += f"    {node_id}{style.format(label=label)}\n"
    
    # Process edges
    for edge in json_data["graph"].get("edges", []):
        from_node = re.sub(r'[^a-zA-Z0-9_]', '_', edge["from"]).lower()
        to_node = re.sub(r'[^a-zA-Z0-9_]', '_', edge["to"]).lower()
        label = edge.get("label", "").replace('"', '\\"')
        
        if label:
            mermaid_code += f"    {from_node} -->|\"{label}\"| {to_node}\n"
        else:
            mermaid_code += f"    {from_node} --> {to_node}\n"
    
    return mermaid_code