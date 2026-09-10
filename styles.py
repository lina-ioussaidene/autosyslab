import streamlit as st

def apply_custom_style():
    st.markdown("""
    <style>
    /* Arrière-plan animé doux */
    .stApp {
        background: linear-gradient(125deg, #000b1a 0%, #001a33 50%, #000b1a 100%);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        color: #e0e0e0;
    }
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* On cache la barre latérale si elle existe */
    [data-testid="stSidebar"] { display: none; }

    /* Style des cartes de saisie */
    .stTextInput input {
        background-color: #002140 !important;
        color: #00d4ff !important;
        border: 1px solid #1890ff !important;
    }

    /* Style pour le champ de saisie du retard (stNumberInput) */
    .stNumberInput input {
        background-color: #002140 !important;
        color: #00d4ff !important;
        border: 1px solid #1890ff !important;
    }

    .stNumberInput div[data-baseweb="input"] {
        background-color: #002140 !important;
        border: 1px solid #1890ff !important;
    }

    .stNumberInput div[data-baseweb="input"]:focus-within {
        border-color: #00d4ff !important;
        box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2) !important;
    }

    /* Style pour les boutons + et - du stNumberInput */
    .stNumberInput button[aria-label="Decrease value"],
    .stNumberInput button[aria-label="Increase value"] {
        background-color: #1890ff !important;
        color: #ffffff !important;
        border: 1px solid #00d4ff !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        width: 24px !important;
        height: 24px !important;
    }
    
    .stNumberInput button[aria-label="Decrease value"]:hover,
    .stNumberInput button[aria-label="Increase value"]:hover {
        background-color: #00d4ff !important;
        color: #002140 !important;
        border: 1px solid #1890ff !important;
        transform: scale(1.1) !important;
        box-shadow: 0 2px 4px rgba(0, 212, 255, 0.3) !important;
    }
    
    .stNumberInput button[aria-label="Decrease value"]:active,
    .stNumberInput button[aria-label="Increase value"]:active {
        transform: scale(0.95) !important;
        box-shadow: 0 1px 2px rgba(0, 212, 255, 0.2) !important;
    }

    /* Style cohérent pour tous les boutons */
    .stButton > button {
        background-color: #1890ff !important;
        color: #ffffff !important;
        border: 1px solid #00d4ff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #00d4ff !important;
        color: #002140 !important;
        border: 1px solid #1890ff !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0, 212, 255, 0.3) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
        box-shadow: 0 2px 4px rgba(0, 212, 255, 0.2) !important;
    }

    /* Style pour les expanders (comme 'Détails des pôles et blocs') */
    .streamlit-expanderHeader {
        background-color: #1890ff !important;
        color: #ffffff !important;
        border: 1px solid #00d4ff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        padding: 10px !important;
    }

    .streamlit-expanderHeader:hover {
        background-color: #00d4ff !important;
        color: #002140 !important;
        border: 1px solid #1890ff !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0, 212, 255, 0.3) !important;
    }

    /* Style pour le contenu de l'expander */
    .streamlit-expanderContent {
        background-color: #001a33 !important;
        border: 1px solid #1890ff !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
        padding: 15px !important;
    }

    .footer {
        position: fixed;
        left: 0; bottom: 0; width: 100%;
        background-color: rgba(0, 11, 26, 0.8);
        text-align: center;
        padding: 10px;
        color: #555;
        border-top: 0.5px solid #1890ff;
    }
    </style>
    """, unsafe_allow_html=True)