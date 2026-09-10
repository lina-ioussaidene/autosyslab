import streamlit as st

def get_transfer_function_input():
    st.sidebar.header("🕹️ Configuration du Système")
    
    # Choix du mode de saisie
    mode = st.sidebar.selectbox("Type de système", ["Ordre supérieur", "Ordre 1", "Ordre 2"])
    
    if mode == "Ordre supérieur":
        num_str = st.sidebar.text_input("Numérateur (ex: 1, 2)", "1")
        den_str = st.sidebar.text_input("Dénominateur (ex: 1, 3, 2)", "1, 2, 1")
        
        # Conversion texte -> liste de nombres
        num = [float(x.strip()) for x in num_str.split(",")]
        den = [float(x.strip()) for x in den_str.split(",")]
    
    # (On ajoutera les modes Ordre 1 et 2 plus tard pour ne pas charger le code)
    else:
        num, den = [1], [1, 1] # Valeurs par défaut
        
    return num, den