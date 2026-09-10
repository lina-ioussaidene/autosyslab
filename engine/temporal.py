import control as ct
import numpy as np
import plotly.graph_objects as go
import streamlit as st

def get_temporal_responses(sys_obj, tau):
    """
    sys_obj : l'objet AutoSystem (contient .tf original)
    tau : la valeur du retard (float)
    """

    # --- 1. BOUCLIER MAGIQUE ---
    # Dans la bibliothèque 'control', les coefficients sont stockés dans un tableau 2D
    num_coeffs = sys_obj.tf.num[0][0] 
    
    is_null_system = all(c == 0 for c in num_coeffs)
    
    if is_null_system:
        st.warning("⚠️ **Système Découplé (Transfert Nul) :** La sortie ne réagit pas à l'entrée ($G(s) = 0$). L'analyse temporelle est impossible car la courbe est totalement plate.")
        return  # On quitte la fonction immédiatement ! Le crash n'aura jamais lieu.
    
    # --- 1. RÉPONSE À L'ÉCHELON (Fidèle à MATLAB) ---
    # On simule le système SANS retard d'abord
    t_orig, y_orig = ct.step_response(sys_obj.tf)
    
    if tau > 0:
        # On crée un décalage propre (Retard Pur)
        dt = t_orig[1] - t_orig[0]
        num_steps_delay = int(tau / dt)
        
        # On ajoute des zéros au début (le plat avant la montée)
        y_step = np.concatenate([np.zeros(num_steps_delay), y_orig])
        # On étend l'axe du temps
        t_step = np.linspace(0, t_orig[-1] + tau, len(y_step))
    else:
        t_step, y_step = t_orig, y_orig

    fig_step = go.Figure()
    fig_step.add_trace(go.Scatter(x=t_step, y=y_step, line=dict(color='#00ff88', width=2), name="Échelon"))
    fig_step.update_layout(
        title=f"Réponse à un échelon (Retard Pur {tau}s)",
        xaxis_title="Temps (s)", yaxis_title="Amplitude",
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )

    # --- 2. RÉPONSE NATURELLE (Ordre réel) ---
    # Le retard n'affecte pas la réponse libre (entrée nulle)
    ss_sys = ct.canonical_form(ct.tf2ss(sys_obj.tf), form='reachable')[0]
    n_states = ss_sys.A.shape[0]

    fig_nat = go.Figure()
    fig_nat.update_layout(
        title=f"Réponse naturelle (Ordre {n_states})",
        xaxis_title="Temps (s)", yaxis_title="Amplitude",
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )

    st.markdown("### Conditions initiales ($x_0$)")
    with st.form(key='natural_response_form'):
        st.write(f"Entrez les {n_states} conditions initiales :")
        cols = st.columns(n_states)
        input_values = [cols[i].text_input(f"x{i}", value="1.0") for i in range(n_states)]
        submit_button = st.form_submit_button(label='Calculer la réponse libre')

    if submit_button or st.session_state.get('has_calculated_nat', False):
        try:
            x0_arr = np.array([float(v) for v in input_values])
            st.session_state['last_x0'] = x0_arr
            st.session_state['has_calculated_nat'] = True
            
            # Temps de simulation (10s comme sur ta capture MATLAB)
            T = np.linspace(0, 10, 1000)
            t_nat, y_nat = ct.initial_response(ss_sys, T=T, X0=x0_arr)

            fig_nat.add_trace(go.Scatter(x=t_nat, y=y_nat.flatten(), line=dict(color='#00d4ff', width=2)))
        except Exception as e:
            st.error(f"Erreur : {e}")

    return fig_step, fig_nat