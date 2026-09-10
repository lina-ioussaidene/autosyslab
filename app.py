import streamlit as st
import numpy as np
import control as ct
import matplotlib.pyplot as plt 
def matrix_to_latex(matrix, name=""):
    if matrix is None: return ""
    latex_str = f"{name} = \\begin{{bmatrix}} "
    for row in matrix:
        row_str = []
        for val in row:
            if abs(val) < 1e-4:
                row_str.append("0")
            elif abs(np.imag(val)) < 1e-4:  # Nombre réel
                row_str.append(f"{np.real(val):.2f}")
            else:  # Nombre complexe (Indispensable pour Jordan !)
                r = np.real(val)
                i = np.imag(val)
                sign = "+" if i >= 0 else "-"
                if abs(r) < 1e-4:  # Imaginaire pur
                    row_str.append(f"{i:.2f}j")
                else:
                    row_str.append(f"{r:.2f} {sign} {abs(i):.2f}j")
        latex_str += " & ".join(row_str) + " \\\\ "
    latex_str += "\\end{bmatrix}"
    return latex_str
from scipy import signal
from styles import apply_custom_style
from components.header import show_header
from engine.core import AutoSystem, format_latex_poly
from engine.stability import analyze_stability, get_realizability_message
from engine.temporal import get_temporal_responses
from engine.margins import calculate_margins
from engine.bode import get_bode_diagram
from engine.state_space import (
    get_state_space_fcc, 
    get_state_space_fco, 
    get_state_space_jordan, 
    # matrix_to_latex
)
from engine.chatbot import get_autobot_response
# Import du nouveau module
from engine.guide_theorique import show_theoretical_guide
from engine.properties import analyze_properties
from engine.linearisation import module_linearisation
from engine.bode import get_margins
from engine.state_feedback import show_state_feedback_module
from engine.corr_pid import calcul_P, calcul_PI, calcul_PID
from engine.corr_avance import calcul_avance_phase
from engine.corr_retard import calcul_retard_phase 

# 1. Configuration de la page
st.set_page_config(
    page_title="AutoSysLab | UMMTO",
    layout="wide",
    page_icon="images/autosyslab logo def.png"
)
apply_custom_style()

# --- GESTION DE LA MÉMOIRE (SESSION STATE) ---
if 'analyse_active' not in st.session_state:
    st.session_state.analyse_active = False
if 'num' not in st.session_state:
    st.session_state.num = None
if 'den' not in st.session_state:
    st.session_state.den = None
if 'tau' not in st.session_state:
    st.session_state.tau = 0.0
if 'display_guide' not in st.session_state:
    st.session_state.display_guide = False
if 'display_linearisation' not in st.session_state:
    st.session_state.display_linearisation = False

# --- EN-TÊTE AVEC LOGO ET BOUTON GUIDE ---
col_head1, col_head2, col_head3 = st.columns([1, 4, 1.2])

with col_head1:
    # Logo de l'université avec cadre rond et taille ajustée
    st.markdown("""
    <style>
    div[data-testid="stImage"] > img {
        border-radius: 50% !important;
        border: 3px solid #1890ff !important;
        box-shadow: 0 4px 8px rgba(0, 212, 255, 0.3) !important;
        width: 120px !important;
        height: 120px !important;
        object-fit: cover !important;
        transition: transform 0.3s ease !important;
        margin: auto !important;
        display: block !important;
    }
    div[data-testid="stImage"] > img:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 6px 12px rgba(0, 212, 255, 0.4) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    st.image("images/autosyslab logo def.png", width=120)
with col_head2:
    st.title("AutoSysLab")
    st.caption("Plateforme Pédagogique d'Automatique • UMMTO 2026")

with col_head3:
    st.write("") # Espacement
    if st.button("📖 GUIDE THÉORIQUE", use_container_width=True):
        st.session_state.display_guide = not st.session_state.display_guide

# --- AFFICHAGE DU GUIDE (Si activé) ---
if st.session_state.display_guide:
    show_theoretical_guide()
    st.markdown("---")

# =========================================================
# --- SECTION : AUTOBOT (CHATBOT INTÉGRÉ PAR IA) ---
# =========================================================

st.markdown("""
    <style>
    /* 1. Force le bouton en BLEU (La position 'fixed' a été retirée pour qu'il reste à sa place naturelle) */
    div[data-testid="stElementContainer"]:has(#autobot-anchor) + div[data-testid="stElementContainer"] button {
        background-color: #2196F3 !important;
        border: 1px solid #2196F3 !important;
        color: white !important;
        width: 100% !important; /* Optionnel : pour qu'il prenne toute la largeur de sa colonne */
    }
    
    div[data-testid="stElementContainer"]:has(#autobot-anchor) + div[data-testid="stElementContainer"] button:hover {
        background-color: #1976D2 !important;
        border: 1px solid #1976D2 !important;
        color: white !important;
    }

    /* 2. Fenêtre de chat flottante */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(#chat-window-anchor) {
        position: fixed !important;
        top: 140px !important;
        right: 30px !important;
        width: 380px !important;
        height: 550px !important;
        background-color: #0e1117 !important;
        z-index: 999999 !important;
        box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.8) !important;
        border-radius: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)

if "show_chat" not in st.session_state:
    st.session_state.show_chat = False

# L'ancre invisible pour cibler le bouton
st.markdown('<span id="autobot-anchor"></span>', unsafe_allow_html=True)

# Le bouton s'affichera ici, à l'endroit exact où vous l'avez placé dans votre code
if st.button("🤖 AutoBot", help="Ouvrir AutoBot", type="primary"):
    st.session_state.show_chat = not st.session_state.show_chat
    st.rerun()

# --- (Placez votre bouton de Linéarisation juste en dessous ici) ---

# La fenêtre de discussion
if st.session_state.show_chat:
    with st.container(border=True):
        st.markdown('<span id="chat-window-anchor"></span>', unsafe_allow_html=True)
        
        col_title, col_close = st.columns([4, 1])
        with col_title:
            st.write("### 🤖 AutoBot")
        with col_close:
            if st.button("✖", key="close_chat_btn"):
                st.session_state.show_chat = False
                st.rerun()

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = [
                {"role": "assistant", "content": "Bonjour ! Je suis l'IA d'AutoSysLab. Comment puis-je vous aider ?"}
            ]

        chat_container = st.container(height=350)
        for message in st.session_state.chat_history:
            chat_container.chat_message(message["role"]).write(message["content"])

        if prompt := st.chat_input("Posez votre question..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            system_context = None
            if st.session_state.get('analyse_active', False):
                system_context = {
                    'numérateur': st.session_state.get('num'),
                    'dénominateur': st.session_state.get('den'),
                    'retard_tau': st.session_state.get('tau'),
                }

            api_key = st.secrets.get("GEMINI_API_KEY", None)

            from engine.chatbot import get_autobot_response
            response = get_autobot_response(prompt, system_context, api_key)
            
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()

# --- BOUTON LINÉARISATION ---
if st.button("📐 LINÉARISATION", use_container_width=False):
    st.session_state.display_linearisation = not st.session_state.display_linearisation

if st.session_state.display_linearisation:
    module_linearisation()
    st.markdown("---")

# ==========================================
# 2. ZONE DE SAISIE CENTRALE
# ==========================================
st.write("### ⌨️ Configuration du Système")

# Initialisation du mode de saisie dans la mémoire
if "input_mode" not in st.session_state:
    st.session_state.input_mode = "FT"

# --- DEUX GRANDS BOUTONS BLEUS POUR LE CHOIX ---
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("📊 FONCTION DE TRANSFERT", use_container_width=True, type="primary" if st.session_state.input_mode == "FT" else "secondary"):
        st.session_state.input_mode = "FT"
        st.rerun()
with col_btn2:
    if st.button("🟦 MATRICES (ESPACE D'ÉTAT)", use_container_width=True, type="primary" if st.session_state.input_mode == "SS" else "secondary"):
        st.session_state.input_mode = "SS"
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

if st.session_state.input_mode == "FT":
    # --- SAISIE CLASSIQUE (FT) ---
    col_in1, col_in2, col_in3 = st.columns([2, 2, 1])
    with col_in1:
        num_raw = st.text_input("Numérateur (ex: 1)", placeholder="Coefficients (ex: 1, 2)...", key="input_num")
    with col_in2:
        den_raw = st.text_input("Dénominateur (ex: 1, 2, 1)", placeholder="Coefficients (ex: 1, 5, 6)...", key="input_den")
    with col_in3:
        tau_raw = st.number_input("Retard (τ)", min_value=0.0, step=0.1, format="%.2f", key="input_tau_ft")

else:
    # --- SAISIE MATRICIELLE DYNAMIQUE (SS) ---
    col_ord1, col_ord2, col_ord3 = st.columns([1, 1, 2])
    with col_ord1:
        # On lit l'ordre depuis la mémoire s'il a été exporté (par défaut 2)
        default_n = int(st.session_state.get('ss_order_n', 2))
        n = st.number_input("Ordre du système (n)", min_value=1, max_value=10, value=default_n, step=1)
        st.session_state.ss_order_n = n # Mise à jour si l'utilisateur change manuellement
        
    with col_ord2:
        tau_raw = st.number_input("Retard (τ)", min_value=0.0, step=0.1, format="%.2f", key="input_tau_ss")

    st.caption(f"Éditez les valeurs des matrices pour un système d'ordre {n}:")
    
    # --- PRÉPARATION DES MATRICES PAR DÉFAUT ---
    # Récupère les matrices de la mémoire (exportées ou déjà analysées) si elles ont la bonne taille
    def get_initial_matrix(key_name, shape):
        if key_name in st.session_state:
            mat = st.session_state[key_name]
            # Vérifie que la matrice existe et correspond à la dimension n actuelle
            if isinstance(mat, np.ndarray) and mat.shape == shape:
                return mat.tolist()
        return np.zeros(shape).tolist()

    default_A = get_initial_matrix('A', (n, n))
    default_B = get_initial_matrix('B', (n, 1))
    default_C = get_initial_matrix('C', (1, n))
    default_D = get_initial_matrix('D', (1, 1))
    
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.write(f"**Matrice $A$ ({n}x{n})**")
        A_data = st.data_editor(default_A, key=f"mat_A_{n}", use_container_width=True)
    with col_b:
        st.write(f"**Vecteur $B$ ({n}x1)**")
        B_data = st.data_editor(default_B, key=f"mat_B_{n}", use_container_width=True)

    col_c, col_d = st.columns([2, 1])
    with col_c:
        st.write(f"**Vecteur $C$ (1x{n})**")
        C_data = st.data_editor(default_C, key=f"mat_C_{n}", use_container_width=True)
    with col_d:
        st.write("**Matrice $D$ (1x1)**")
        D_data = st.data_editor(default_D, key=f"mat_D_{n}", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- BOUTON D'ACTION PRINCIPAL ---
if st.button("🚀 ANALYSER LE SYSTÈME", use_container_width=True, type="primary"):
    st.session_state.analyse_active = False # Reset par défaut
    
    if st.session_state.input_mode == "FT":
        if num_raw and den_raw:
            try:
                st.session_state.num = [float(x.strip()) for x in num_raw.split(",")]
                st.session_state.den = [float(x.strip()) for x in den_raw.split(",")]
                st.session_state.tau = tau_raw
                st.session_state.is_ss_input = False 
                st.session_state.analyse_active = True
            except ValueError:
                st.error("⚠️ Erreur : Veuillez entrer des nombres valides.")
    
    else:
        # --- CORRECTION : Traitement du mode Matrices ---
        try:
            # 1. On récupère les valeurs directement depuis les grilles de l'interface
            A = np.array(A_data, dtype=float)
            B = np.array(B_data, dtype=float)
            C = np.array(C_data, dtype=float)
            D = np.array(D_data, dtype=float)
            
            # 2. Conversion Espace d'état vers FT
            num_ss, den_ss = signal.ss2tf(A, B, C, D)
            
            # 3. Nettoyage des petites erreurs de précision
            num_clean = np.where(np.abs(num_ss.flatten()) < 1e-10, 0, num_ss.flatten())
            den_clean = np.where(np.abs(den_ss.flatten()) < 1e-10, 0, den_ss.flatten())
            
            num_clean = np.trim_zeros(num_clean, 'f')
            if len(num_clean) == 0: num_clean = np.array([0.0])
                
            den_clean = np.trim_zeros(den_clean, 'f')
            if len(den_clean) == 0: den_clean = np.array([1.0])
            
            # 4. On met à jour les FT pour le diagramme de Bode, les pôles, etc.
            st.session_state.num = num_clean.tolist()
            st.session_state.den = den_clean.tolist()
            st.session_state.tau = tau_raw
            
            # 5. ON ÉCRASE L'ANCIENNE MÉMOIRE AVEC LES MATRICES MODIFIÉES !
            st.session_state.is_ss_input = True
            st.session_state.A = A
            st.session_state.B = B
            st.session_state.C = C
            st.session_state.D = D
            
            st.session_state.analyse_active = True
            
        except Exception as e:
            st.error(f"⚠️ Erreur lors de la conversion des matrices : {e}")

# ==========================================
# 3. AFFICHAGE DES RÉSULTATS
# ==========================================
if st.session_state.analyse_active:
    try:
        num = st.session_state.num
        den = st.session_state.den
        tau = st.session_state.tau
        
        st.markdown("---")
        
        # --- NOUVEAU : AFFICHAGE DES MATRICES EN LATEX SI SAISIE MATRICIELLE ---
        if st.session_state.get('is_ss_input', False):
            st.write("### 📐 Matrices du Système (Espace d'État)")
            col_mat1, col_mat2 = st.columns(2)
            
            # On utilise ta fonction matrix_to_latex déjà importée en haut !
            with col_mat1:
                st.latex(matrix_to_latex(st.session_state.A, "A"))
                st.latex(matrix_to_latex(st.session_state.C, "C"))
            with col_mat2:
                st.latex(matrix_to_latex(st.session_state.B, "B"))
                st.latex(matrix_to_latex(st.session_state.D, "D"))
                
            st.markdown("---")

        # --- A. AFFICHAGE DE LA FONCTION DE TRANSFERT ---
        if st.session_state.get('is_ss_input', False):
            st.write("### 🔄 Fonction de Transfert Équivalente G(s)")
        else:
            st.write("### 🎯 Fonction de Transfert G(s)")
        
        sys_obj = AutoSystem(num, den, tau)
        
        # On récupère le LaTeX directement généré et normalisé par la classe AutoSystem
        tf_latex_base = sys_obj.get_latex(with_delay=False).replace("G(s) = ", "")
        
        col_tf1, col_tf2 = st.columns([2, 1])
        with col_tf1:
            if tau > 0:
                st.latex(rf"G(s) = {tf_latex_base} \cdot e^{{-{tau}s}}")
                
                # Ajout du message explicatif en rouge juste en dessous si une normalisation a eu lieu
                if sys_obj.msg_info:
                    st.markdown(f":red[⚠️ **Note de normalisation :** {sys_obj.msg_info}]")
                
                st.write("**Approximation de Padé (ordre 1) :**")
                st.latex(rf"e^{{-{tau}s}} \approx \frac{{1 - {tau/2}s}}{{1 + {tau/2}s}}")
                
                # Calcul et affichage de la fonction de transfert approximée complète
                # Calcul et affichage de la fonction de transfert approximée complète
                pade_tf = ct.TransferFunction([-tau/2, 1], [tau/2, 1])
                approximated_tf = sys_obj.tf * pade_tf
                
                # Récupérer les coefficients
                num_approx = list(approximated_tf.num[0][0])
                den_approx = list(approximated_tf.den[0][0])
                
                # Normalisation (diviser par le premier coefficient pour avoir 1 devant s^n)
                leading_coeff = den_approx[0]
                num_norm = [c / leading_coeff for c in num_approx]
                den_norm = [c / leading_coeff for c in den_approx]
                
                # Utilisation de ta fonction robuste format_latex_poly
                num_str = format_latex_poly(num_norm)
                den_str = format_latex_poly(den_norm)
                
                st.write("**Système approximé complet :**")
                st.latex(rf"G_{{approx}}(s) = \frac{{{num_str}}}{{{den_str}}}")
            else:
                st.latex(f"G(s) = {tf_latex_base}")
                
                # Ajout du message explicatif en rouge si pas de retard
                if sys_obj.msg_info:
                    st.markdown(f":red[⚠️ **Note de normalisation :** {sys_obj.msg_info}]")
        
        with col_tf2:
            msg, m_color = get_realizability_message(num, den)
            st.markdown(f"<div style='background-color:{m_color}22; padding:10px; border-radius:5px; border:1px solid {m_color}; color:{m_color}; font-weight:bold;'>{msg}</div>", unsafe_allow_html=True)

        # --- B. SÉCURITÉ : BLOCAGE SI SYSTÈME IMPROPRE ---
        if len(num) > len(den):
            st.warning("⚠️ L'analyse est interrompue : le système est irréalisable (degré Num > degré Den).")
            st.stop() 

        # --- C. CALCULS ---
        sys_to_analyze = sys_obj.tf
        if tau > 0:
            pade_tf = ct.TransferFunction([-tau/2, 1], [tau/2, 1])
            sys_to_analyze = sys_obj.tf * pade_tf

        # 1. STABILITÉ
        st.write("## 1. Étude de la Stabilité")
        poles, status, s_color, fig_p = analyze_stability(sys_to_analyze)
        col_stab1, col_stab2 = st.columns([1, 2])
        with col_stab1:
            st.markdown(f"Statut : <b style='color:{s_color}; font-size:24px;'>{status}</b>", unsafe_allow_html=True)
            for p in poles:
                val_p = f"{p.real:.4f} {'+' if p.imag >= 0 else '-'} {abs(p.imag):.4f}j" if p.imag != 0 else f"{p.real:.4f}"
                st.write(f"• `{val_p}`")
        with col_stab2:
            st.plotly_chart(fig_p, use_container_width=True)

        # 2. TEMPOREL

        st.write("## 2. Réponses Temporelles")
        f_step, f_nat = get_temporal_responses(sys_obj, tau)
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.write("### 📈 Réponse à un échelon")
            st.plotly_chart(f_step, use_container_width=True)
        with col_t2:
            st.write("### 📉 Réponse naturelle")
            st.plotly_chart(f_nat, use_container_width=True)

        # 3. FRÉQUENTIEL (Bode et Marges)
        st.write("## 3. Étude Fréquentielle")

        try:
            margins = get_margins(num, den, tau=tau, w_min=1e-2, w_max=1e3, n_points=5000)
              # adapte "num", "den", "tau" aux noms exacts utilises pour construire sys_to_analyze

            gm_db = margins['GM_dB']
            pm    = margins['PM_deg']
            w_cg  = margins['Wcg']   # pulsation ou phase = -180 deg
            w_cp  = margins['Wcp']   # pulsation ou gain = 0 dB

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Marge de Gain (GM)", f"{gm_db:.2f} dB" if np.isfinite(gm_db) else "∞")
            m2.metric("Marge de Phase (PM)", f"{pm:.2f} °" if np.isfinite(pm) else "N/A")
            m3.metric("ω critique — Wcg (phase=-180°)", f"{w_cg:.4f} rad/s" if not np.isnan(w_cg) else "N/A")
            m4.metric("ω coupure — Wcp (gain=0dB)", f"{w_cp:.4f} rad/s" if not np.isnan(w_cp) else "N/A")

        except Exception as e:
            st.error(f"Erreur de calcul des marges : {e}")

        # --- C. DIAGRAMME DE BODE ---
        st.plotly_chart(get_bode_diagram(num, den, tau), use_container_width=True)
        
         # 4. ÉTAT
        st.write("## 4. Représentations d'État")
        
        num_m, den_m = ct.tfdata(sys_to_analyze)
        num_m, den_m = num_m[0][0], den_m[0][0]
        
        form_choice = st.radio("Sélectionner la forme :", ["Commandable (FCC)", "Observable (FCO)"], horizontal=True)
        
        if form_choice == "Commandable (FCC)": 
            A, B, C, D = get_state_space_fcc(num_m, den_m)
        elif form_choice == "Observable (FCO)": 
            A, B, C, D = get_state_space_fco(num_m, den_m)
        
        col_mat1, col_mat2 = st.columns(2)
        with col_mat1:
            st.latex(matrix_to_latex(A, "A"))
            st.latex(matrix_to_latex(B, "B"))
        with col_mat2:
            st.latex(matrix_to_latex(C, "C"))
            st.latex(matrix_to_latex(D, "D"))
        
        # 5. PROPRIÉTÉS DU SYSTÈME
        st.write("## 5. Propriétés du Système")
        
        # On utilise les matrices de la forme sélectionnée (FCC ou FCO)
        props = analyze_properties(A, B, C)
        
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            st.write(".Matrice de commandabilité")
            if props["is_commandable"]:
                st.success(f"Système Commandable (Rang = {props['rank_c']})")
            else:
                st.error(f"Système Non Commandable (Rang = {props['rank_c']} / {props['n']})")
            
            st.latex(matrix_to_latex(props["Mc"], "M_c"))

        with col_p2:
            st.write(".Matrice d'observabilité")
            if props["is_observable"]:
                st.success(f"Système Observable (Rang = {props['rank_o']})")
            else:
                st.error(f"Système Non Observable (Rang = {props['rank_o']} / {props['n']})")
                
            st.latex(matrix_to_latex(props["Mo"], "M_o"))
        
        st.markdown("---")
        
       # --- SECTION JORDAN CORRIGÉE AVEC COULEURS ---
        st.write("### Forme de Jordan (Décomposition complète)")
        try:
            A_j, B_j, C_j, D_j, jordan_info = get_state_space_jordan(num_m, den_m, tau=0.0)
            
            # Cas 1 : Système non diagonalisable (multiplicité détectée)
            if not jordan_info.get('is_diagonalizable', True):
                st.warning(jordan_info.get('message', "⚠️ Le système n'est pas diagonalisable (présence de pôles multiples)."))
                
                # Afficher quand même les détails des pôles
                with st.expander("📊 Détails des pôles et blocs", expanded=True):
                    if jordan_info.get('roots'):
                        for r, m in zip(jordan_info['roots'], jordan_info['multiplicities']):
                            r_format = f"{r.real:.4f} {'+' if r.imag >= 0 else '-'} {abs(r.imag):.4f}j" if abs(r.imag) > 1e-4 else f"{r.real:.4f}"
                            st.write(f"• Pôle $\lambda = {r_format}$ (Multiplicité : {m})")
            
            # Cas 2 : Système diagonalisable (matrices disponibles)
            elif jordan_info.get('is_diagonalizable', False) and A_j is not None:
                st.success("✅ Le système est diagonalisable (pôles simples).")
                
                # Affichage des matrices
                col_j1, col_j2 = st.columns(2)
                with col_j1:
                     st.latex(matrix_to_latex(A_j, "A_j"))
                     st.latex(matrix_to_latex(B_j, "B_j"))
                with col_j2:
                     st.latex(matrix_to_latex(C_j, "C_j"))
                     st.latex(matrix_to_latex(D_j, "D_j"))
                
                # Détails techniques
                with st.expander("📊 Détails des pôles et blocs"):
                    if jordan_info.get('roots'):
                        for r, m in zip(jordan_info['roots'], jordan_info['multiplicities']):
                            r_format = f"{r.real:.4f} {'+' if r.imag >= 0 else '-'} {abs(r.imag):.4f}j" if abs(r.imag) > 1e-4 else f"{r.real:.4f}"
                            st.write(f"• Pôle $\lambda = {r_format}$ (Multiplicité : {m})")
            
            # Cas 3 : Erreur de calcul
            else:
                st.error(jordan_info.get('message', "Impossible de calculer la forme de Jordan pour ce système."))
        
        except Exception as e:
            st.error(f"Erreur lors du calcul de Jordan : {e}")

        # =========================================================================
        # --- 6. COMMANDE PAR RETOUR D'ÉTAT & COMPARAISON (BO vs BF) ---
        # =========================================================================
        st.write("---")
        st.write("## 6. Commande par Retour d'État (BO vs BF)")
        show_state_feedback_module(A, B, C, D)

    # --- FIN UNIQUE DU GRAND BLOC TRY PRINCIPAL ---
    except Exception as e:
        st.error(f"⚠️ Erreur lors de l'analyse : {e}")

# =========================================================
# --- 5. CAHIER DES CHARGES ---
# =========================================================
# On affiche cette suite UNIQUEMENT si l'analyse principale a été lancée
if st.session_state.get("analyse_active", False):
    st.markdown("---")
    st.write("### 7. Cahier des Charges")
    
    # Message d'information pédagogique bien visible
    st.info("💡 **Note de calcul :** Le correcteur sera synthétisé uniquement selon le domaine sélectionné ci-dessous. Mathématiquement, les approches temporelles et fréquentielles ne peuvent pas être mixées simultanément.")

    

    approche = st.radio(
        "Type d'exigences :",
        ["Spécifications Temporelles", "Spécifications Fréquentielles"],
        horizontal=True
    )

    col_c1, col_c2, col_c3 = st.columns(3)

    if "Temporelles" in approche:
        with col_c1:
            st.session_state.depassement = st.number_input("Dépassement max (%)", min_value=0.0, value=5.0, step=1.0)
        with col_c2:
            st.session_state.tr5 = st.number_input("Temps de réponse à 5% (s)", min_value=0.01, value=2.0, step=0.1)
        with col_c3:
            st.session_state.erreur_stat = st.number_input("Erreur statique (%)", min_value=0.0, value=0.0, step=1.0)
        st.session_state.type_cahier = "temporel"
    else:
        with col_c1:
            st.session_state.marge_phase = st.number_input("Marge de phase désirée (°)", min_value=10.0, value=45.0, step=5.0)
        with col_c2:
            st.session_state.omega_c = st.number_input("Pulsation de coupure (rad/s)", min_value=0.01, value=10.0, step=0.1)
        with col_c3:
            st.session_state.erreur_stat_freq = st.number_input("Erreur statique (%)", min_value=0.0, value=0.0, step=1.0, key="err_freq")
        st.session_state.type_cahier = "frequentiel"

    # =========================================================
    # --- 6. CHOIX DU CORRECTEUR ---
    # =========================================================
    st.markdown("---")
    st.write("### 8.Synthèse et Comparaison")
    
    col_sel, col_empty = st.columns([1, 1])
    with col_sel:
        correcteur_choisi = st.selectbox(
            "Sélectionnez le type de correcteur à appliquer :",
            ["Proportionnel (P)", 
             "Proportionnel Intégral (PI)", 
             "Proportionnel Intégral Dérivé (PID)", 
             "Avance de phase", 
             "Retard de phase"]
        )
    
    # =========================================================
    # --- 7. CALCUL ET AFFICHAGE ---
    # =========================================================
    if st.button("SYNTHÉTISER ET COMPARER", type="primary", use_container_width=True):
        
        # 1. On sécurise les variables : on reconstruit G(s) proprement
        import control as ct
        num = st.session_state.num
        den = st.session_state.den
        tau = st.session_state.tau
        
        G_s = ct.TransferFunction(num, den)
        
        if tau > 0:
            # Si le système a un retard, on applique Padé (ordre 4 pour plus de précision mathématique)
            pade_num, pade_den = ct.pade(tau, 4)
            G_s = G_s * ct.TransferFunction(pade_num, pade_den)

        # 2. Préparation du dictionnaire de spécifications
        specs = {
            "type_cahier": st.session_state.type_cahier,
            "depassement": st.session_state.get("depassement", 5.0),
            "tr5": st.session_state.get("tr5", 2.0),
            "erreur_stat": st.session_state.get("erreur_stat", 0.0),
            "marge_phase": st.session_state.get("marge_phase", 45.0),
            "omega_c": st.session_state.get("omega_c", 10.0)
        }
        
        # 3. Appel au bon correcteur
        try:
            if correcteur_choisi == "Proportionnel (P)":
                C_s, latex_c = calcul_P(G_s, specs)
            elif correcteur_choisi == "Proportionnel Intégral (PI)":
                C_s, latex_c = calcul_PI(G_s, specs)
            elif correcteur_choisi == "Proportionnel Intégral Dérivé (PID)":
                C_s, latex_c = calcul_PID(G_s, specs)
            elif correcteur_choisi == "Avance de phase":
                C_s, latex_c = calcul_avance_phase(G_s, specs)
            elif correcteur_choisi == "Retard de phase":
                C_s, latex_c = calcul_retard_phase(G_s, specs)
            
            st.success(f"✅ Correcteur synthétisé avec succès !")
            st.write("**Fonction de transfert du correcteur :**")
            st.latex(latex_c)
            
            # --- CALCUL DES BOUCLES FERMÉES ---
            H_uncorr = ct.feedback(G_s, 1)
            H_corr = ct.feedback(C_s * G_s, 1)
            
            def get_metrics(sys_bf):
                try:
                    import numpy as np
                    info = ct.step_info(sys_bf)
                    dc_gain = sys_bf.dcgain()
                    err_stat = abs(1.0 - dc_gain) * 100.0 if not np.isinf(dc_gain) else 0.0
                    return info['Overshoot'], info['SettlingTime'], err_stat
                except:
                    return None, None, None
            
            ov_u, tr_u, err_u = get_metrics(H_uncorr)
            ov_c, tr_c, err_c = get_metrics(H_corr)
            
            # --- AFFICHAGE DU TABLEAU DES SCORES ---
            st.write("#### 📊 Analyse des Performances (Boucle Fermée)")
            
            def format_metric(val): return f"{val:.2f}" if val is not None else "Instable"
            def format_delta(val_c, val_u):
                if val_c is None or val_u is None: return None
                return f"{val_c - val_u:+.2f}"

            m1, m2, m3 = st.columns(3)
            m1.metric("Dépassement (%)", format_metric(ov_c), format_delta(ov_c, ov_u), delta_color="inverse")
            m2.metric("Temps de réponse 5% (s)", format_metric(tr_c), format_delta(tr_c, tr_u), delta_color="inverse")
            m3.metric("Erreur statique (%)", format_metric(err_c), format_delta(err_c, err_u), delta_color="inverse")
            
           # --- GRAPHIQUES AVANT / APRÈS ---
            st.write("#### 📈 Comparaison Graphique")
            tab_temp, tab_freq = st.tabs(["⏱️ Réponse Indicielle (Step)", "🌊 Diagramme de Bode"])
            
            import matplotlib.pyplot as plt
            
            with tab_temp:
                # Création de 3 colonnes : [1 espace vide, 3 pour le graphe, 1 espace vide]
                # Cela force le graphique à ne prendre que le centre de l'écran
                col_vide1, col_graphe, col_vide2 = st.columns([1, 3, 1])
                
                with col_graphe:
                    fig_step, ax_step = plt.subplots(figsize=(6, 4))
                    T_u, yout_u = ct.step_response(H_uncorr)
                    T_c, yout_c = ct.step_response(H_corr)
                    
                    ax_step.plot(T_u, yout_u, 'r--', label='Non Corrigé (BF)', linewidth=2)
                    ax_step.plot(T_c, yout_c, 'b-', label='Corrigé (BF)', linewidth=2)
                    ax_step.axhline(1, color='k', linestyle=':', label='Consigne')
                    
                    ax_step.set_title("Réponse à un échelon unitaire")
                    ax_step.set_xlabel("Temps (s)")
                    ax_step.set_ylabel("Amplitude")
                    ax_step.grid(True)
                    ax_step.legend()
                    st.pyplot(fig_step, use_container_width=True)
                
            with tab_freq:
                # La même technique pour le diagramme de Bode
                col_vide3, col_graphe_bode, col_vide4 = st.columns([1, 3, 1])
                
                with col_graphe_bode:
                    fig_bode = plt.figure(figsize=(6, 5))
                    ct.bode(G_s, plot=True, color='r', linestyle='--', label='Non Corrigé (BO)')
                    ct.bode(C_s * G_s, plot=True, color='b', linestyle='-', label='Corrigé (BO)')
                    plt.legend()
                    st.pyplot(fig_bode, use_container_width=True)
                
        except Exception as e:
            st.error(f"❌ Une erreur mathématique s'est produite lors du calcul : {e}")
            st.info("Vérifiez que vos spécifications sont compatibles avec votre système.")
# --- Style pour le container de chat ---
st.markdown("""
<style>
.chat-box {
    border: 1px solid rgba(128, 128, 128, 0.2);
    border-radius: 10px;
    padding: 10px;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)

# --- 4. PIED DE PAGE (FOOTER) ---
st.markdown("---")
footer_html = """
<div style="
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: rgba(14, 17, 23, 0.85);
    color: #ffffff;
    text-align: center;
    padding: 10px;
    font-size: 14px;
    border-top: 1px solid #4a4a4a;
    z-index: 1000;
    box-shadow: 0px -2px 10px rgba(0,0,0,0.2);
">
    Créé par <b>Ioussaidene Lina</b> - Étudiante en Automatique | UMMTO 2026
</div>
<div style="height: 60px;"></div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
