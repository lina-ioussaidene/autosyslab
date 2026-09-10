import streamlit as st

def show_header():
    st.markdown("""
        <div style="text-align: center; padding: 10px;">
            <h1 style='color: #00d4ff; margin-bottom: 0;'>UNIVERSITÉ MOULOUD MAMMERI TIZI OUZOU</h1>
            <h3 style='color: #1890ff; margin-top: 5px;'>Faculté du Génie Électrique et de l'Informatique</h3>
            <hr style="border: 1px solid #1890ff;">
        </div>
    """, unsafe_allow_html=True)