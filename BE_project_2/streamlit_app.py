import streamlit as st
import main
import viewer

def run():
    query_params = st.query_params
    if "id" in query_params:
        viewer.show_shared_output()
    else:
        main.run_main()  # Call the main app UI

if __name__ == "__main__":
    run()
