import streamlit as st
import numpy as np
import control as ct
import plotly.graph_objects as go

def get_suggested_poles(A):
    """
    Analyse la matrice A et propose une configuration optimale de pôles pour un ordre n :
    - Une paire complexe conjuguée dominante (amortissement ~0.7) pour un bon transitoire.
    - Les pôles restants repoussés plus loin à gauche sur l'axe réel.
    """
    n = A.shape[0]
    bo_poles = np.linalg.eigvals(A)
    
    # 1. Identifier le pôle le plus critique (le plus à droite)
    max_real = np.max(bo_poles.real)
    
    # 2. Définir la dynamique cible de base (partie réelle)
    if max_real >= 0:
        # Si le système est instable, on le stabilise avec une bonne marge
        target_real = -max_real - 2.0
    else:
        # Si déjà stable, on l'accélère
        target_real = max_real * 1.5
        
    # On impose une vitesse minimale de -2.0
    target_real = min(target_real, -2.0)
    
    suggested = []
    
    # 3. Création des pôles dominants (Paire complexe conjuguée si n >= 2)
    if n >= 2:
        # Amortissement idéal : Partie imaginaire = |Partie réelle|
        suggested.append(complex(target_real, abs(target_real)))
        suggested.append(complex(target_real, -abs(target_real)))
    elif n == 1:
        # Cas très rare dans ton app, mais couvert par sécurité
        suggested.append(complex(target_real, 0))
        
    # 4. Pour les systèmes d'ordre n > 2 : placer les autres pôles pour qu'ils soient non-dominants
    # On les espace sur l'axe réel pour éviter qu'ils soient identiques (évite un crash de ct.place)
    for i in range(2, n):
        # i=2 -> 3x plus rapide, i=3 -> 4x plus rapide, etc.
        p_far = complex(target_real * (i + 1), 0)
        suggested.append(p_far)
        
    return suggested

def format_poles_for_input(poles):
    """Convertit une liste de pôles en chaîne de caractères propre pour le champ de texte."""
    formatted = []
    for p in poles:
        if abs(p.imag) < 1e-4:
            formatted.append(f"{p.real:.2f}")
        else:
            sign = "+" if p.imag >= 0 else "-"
            formatted.append(f"{p.real:.2f}{sign}{abs(p.imag):.2f}j")
    return ", ".join(formatted)

def get_bo_bf_comparison_fig(A, B, C, D, K, g, t_max=10.0):
    """Génère le graphique Plotly comparant la Boucle Ouverte et la Boucle Fermée."""
    t_sim = np.linspace(0, t_max, 1000)
    fig = go.Figure()

    # --- 1. Simulation Boucle Ouverte (BO) ---
    sys_bo = ct.StateSpace(A, B, C, D)
    try:
        t_bo, y_bo = ct.step_response(sys_bo, t_sim)
        if y_bo.ndim > 1: y_bo = y_bo[0]
        
        # Vérification si le système diverge fortement (instable)
        is_unstable = np.max(np.abs(y_bo)) > 1e4 or np.isnan(y_bo).any()
        nom_bo = "Boucle Ouverte (Instable / Divergence)" if is_unstable else "Boucle Ouverte (BO)"
        
        # Suration visuelle de la courbe rouge pour éviter d'écraser l'échelle
        y_bo_visuel = np.clip(y_bo, -0.5, 2.5)
        
        fig.add_trace(go.Scatter(
            x=t_bo, y=y_bo_visuel, 
            name=nom_bo,
            line=dict(color="#ff4b4b", width=2, dash="dash")
        ))
    except Exception:
        fig.add_trace(go.Scatter(
            x=t_sim, y=np.zeros_like(t_sim), 
            name="Boucle Ouverte (Erreur / Divergence extrême)",
            line=dict(color="#ff4b4b", width=2, dash="dot")
        ))

    # --- 2. Simulation Boucle Fermée (BF) ---
    A_bf = A - B @ K.reshape(1, -1)
    B_bf = B * g
    sys_bf = ct.StateSpace(A_bf, B_bf, C, D)
    t_bf, y_bf = ct.step_response(sys_bf, t_sim)
    if y_bf.ndim > 1: y_bf = y_bf[0]

    fig.add_trace(go.Scatter(
        x=t_bf, y=y_bf, 
        name="Boucle Fermée (BF - Retour d'État)",
        line=dict(color="#00ff88", width=3)
    ))

    # --- 3. Consigne ---
    fig.add_shape(
        type="line", x0=t_sim[0], x1=t_sim[-1], y0=1.0, y1=1.0,
        line=dict(color="white", width=1, dash="dot"),
        name="Consigne (1.0)"
    )

    fig.update_layout(
        title="Comparaison Temporelle : Boucle Ouverte vs Boucle Fermée",
        xaxis_title="Temps (s)",
        yaxis_title="Amplitude y(t)",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def show_state_feedback_module(A, B, C, D):
    """Affiche l'interface complète du module de commande par retour d'état."""
    n = A.shape[0]
    
    # Suggestion automatique de pôles (Ton algorithme dynamique !)
    suggested_poles = get_suggested_poles(A)
    default_str = format_poles_for_input(suggested_poles)
    
    # Message adapté pour responsabiliser l'utilisateur
    st.info(f"💡 **Indication AutoSysLab :** C'est à vous d'imposer la dynamique ! Pour votre système d'ordre **{n}**, voici une configuration recommandée pour assurer la stabilité et accélérer le régime transitoire.")
    
    # MODIFICATION ICI : On utilise "placeholder" au lieu de "value"
    poles_input = st.text_input(
        f"Entrez exactement {n} pôles désirés (séparés par des virgules) :", 
        value="", # Le champ est vide par défaut
        placeholder=f"Exemple suggéré : {default_str}", # La suggestion apparaît en grisé
        key="state_feedback_poles_input"
    )
    
    if st.button("⚡ CALCULER LA COMMANDE ET SIMULER", use_container_width=True, key="btn_sim_bf"):
        
        # NOUVELLE SÉCURITÉ : On bloque si l'utilisateur clique sans rien écrire
        if not poles_input.strip():
            st.warning(f"⚠️ Veuillez saisir vos pôles désirés avant de calculer. (Astuce : essayez {default_str})")
            return # On stoppe l'exécution ici
            
        try:
            # Parsing des pôles saisis
            raw_poles = [p.strip().replace(' ', '') for p in poles_input.split(",") if p.strip()]
            desired_poles = [complex(p) for p in raw_poles]
            
            if len(desired_poles) != n:
                st.error(f"⚠️ Erreur : Vous devez entrer exactement **{n} pôles** pour ce système (vous en avez entré {len(desired_poles)}).")
                return
                
            # Calcul de K par placement de pôles
            placement = ct.place(A, B, desired_poles)
            K = np.array(placement)
            if K.ndim == 2:
                K = K[0]
                
            # Calcul de A_bf et du gain de pré-filtrage g
            A_bf = A - B @ K.reshape(1, -1)
            inv_A_bf = np.linalg.inv(A_bf)
            g = -1.0 / (C @ inv_A_bf @ B + D)[0, 0]
            
            # Affichage des résultats mathématiques
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.success("✅ Vecteur de gain de retour d'état calculé !")
                k_str = " & ".join([f"{val:.4f}" for val in K])
                st.latex(rf"K = \begin{{bmatrix}} {k_str} \end{{bmatrix}}")
            with col_res2:
                st.success("✅ Gain de pré-filtrage de consigne !")
                st.latex(rf"g = {g:.4f}")
                st.caption("Ce gain garantit une erreur statique nulle en boucle fermée.")
                
            # Affichage du graphique Plotly
            fig_comp = get_bo_bf_comparison_fig(A, B, C, D, K, g)
            st.plotly_chart(fig_comp, use_container_width=True)
            
        except np.linalg.LinAlgError:
            st.error("⚠️ Erreur de calcul : Le système bouclé est singulier ou non inversible. Vérifiez la commandabilité du système.")
        except Exception as e:
            st.error(f"⚠️ Erreur lors du calcul du retour d'état : {str(e)}")
            st.info("Astuce : Si vous utilisez des pôles complexes, assurez-vous de toujours inclure leurs conjugués (ex: -2+1j, -2-1j).")