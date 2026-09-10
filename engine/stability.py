import control as ct
import numpy as np
import plotly.graph_objects as go

def get_realizability_message(num, den):
    """Analyse les degrés pour déterminer la réalisabilité du système."""
    deg_num = len(num) - 1
    deg_den = len(den) - 1
    
    if deg_num < deg_den:
        msg = f"Système strictement propre : le degré du dénominateur ({deg_den}) est supérieur au degré du numérateur ({deg_num}). Le système est réalisable."
        color = "#28a745"
    elif deg_num == deg_den:
        msg = f"Système propre : les degrés sont égaux ({deg_num}). Le système est réalisable (présence d'une transmission directe D)."
        color = "#17a2b8"
    else:
        msg = f"Système impropre : le degré du numérateur ({deg_num}) est supérieur au degré du dénominateur ({deg_den}). Le système n'est pas réalisable physiquement."
        color = "#dc3545"
        
    return msg, color

def analyze_stability(sys):
    """
    Calcule les pôles, détermine la stabilité et génère le graphique du plan complexe.
    """
    # 1. Calcul des pôles
    poles = ct.poles(sys)
    real_parts = np.real(poles)
    imag_parts = np.imag(poles)

    # 2. Logique de stabilité
    is_stable = all(real_parts < -1e-9)
    is_marginal = any(np.isclose(real_parts, 0, atol=1e-9)) and all(real_parts <= 1e-9)

    if is_stable:
        status, color = "Stable", "green"
    elif is_marginal:
        status, color = "À la limite de stabilité", "orange"
    else:
        status, color = "Instable", "red"

    # 3. Création du graphique Plotly (Plan Complexe)
    fig = go.Figure()

    # Ajout des axes cardinaux (Ligne horizontale et verticale à 0)
    fig.add_hline(y=0, line_width=1, line_color="white", opacity=0.6)
    fig.add_vline(x=0, line_width=1, line_color="white", opacity=0.6)

    # Ajout des pôles (Marqués par des 'X')
    fig.add_trace(go.Scatter(
        x=real_parts,
        y=imag_parts,
        mode='markers',
        marker=dict(color='red', size=12, symbol='x', line=dict(width=2)),
        name='Pôles',
        hovertemplate='Réel: %{x:.4f}<br>Imag: %{y:.4f}j<extra></extra>'
    ))

    # Mise en page du graphique
    fig.update_layout(
        title="Localisation des Pôles (Plan Complexe)",
        xaxis_title="Axe Réel (σ)",
        yaxis_title="Axe Imaginaire (jω)",
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode='closest'
    )

    return poles, status, color, fig