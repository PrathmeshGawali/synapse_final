import streamlit as st

def render_summary(summary_data: dict, summary_id: str = "default"):
    """Render a structured summary view with validation"""

    # Basic validation
    if not isinstance(summary_data, dict) or 'content' not in summary_data:
        st.error("Invalid summary format - missing 'content' field")
        st.json(summary_data)
        return

    content = summary_data["content"]
    st.header("🧠 Summary")

    # Optional metadata
    if "feature_type" in summary_data:
        st.markdown(f"**Feature Type:** {summary_data['feature_type']}")
    if "timestamp" in summary_data:
        st.caption(f"🕒 Last updated: {summary_data['timestamp']}")

    # Render structured summary using markdown sections
    sections = content.split('\n\n')
    for section in sections:
        if section.strip().startswith("**") and section.strip().endswith("**"):
            st.subheader(section.strip("**"))
        elif section.strip().startswith("*"):
            bullets = section.strip().split("\n")
            for bullet in bullets:
                st.markdown(f"- {bullet.strip('* ').strip()}")
        else:
            st.markdown(section)

    st.info("End of summary content.")
