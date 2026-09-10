import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import signal

def _interpolate_crossing(x1, x2, y1, y2, y_target):
    """Interpolation linéaire précise pour trouver la fréquence exacte de croisement."""
    if y2 == y1:
        return x1
    return x1 + (y_target - y1) * (x2 - x1) / (y2 - y1)

def get_margins(num, den, tau=0.0, w_min=1e-4, w_max=1e4, n_points=10000):
    """
    Calcule les marges de stabilité (Gain et Phase) et les pulsations associées
    de manière scientifiquement exacte.
    """
    w = np.logspace(np.log10(w_min), np.log10(w_max), n_points)

    # Réponse complexe
    try:
        w, h_complex = signal.freqs(num, den, worN=w)
    except TypeError:
        w, h_complex = signal.freqs(num, den, w=w)
        
    mag_db = 20 * np.log10(np.abs(h_complex))
    
    # Phase en radians déroulée (unwrap) puis convertie en degrés
    phase_rad = np.unwrap(np.angle(h_complex))
    phase_deg_sys = np.rad2deg(phase_rad)
    
    # Ajout du retard pur : phi_total = phi_sys - (tau * w * 180 / pi)
    phase_deg_total = phase_deg_sys - np.rad2deg(tau * w)

    # --- 1. Recherche de Wcp (Marge de Phase : quand Gain = 0 dB) ---
    sign_mag = np.sign(mag_db)
    idx_gain_cross = np.where(np.diff(sign_mag) != 0)[0]
    
    if len(idx_gain_cross) > 0:
        all_w_cp = []
        all_pm_deg = []
        
        for idx in idx_gain_cross:
            w_cp_cand = _interpolate_crossing(w[idx], w[idx+1], mag_db[idx], mag_db[idx+1], 0.0)
            phase_at_w_cp = np.interp(w_cp_cand, w, phase_deg_total)
            
            # Marge de Phase = 180° + Phase(w_cp)
            pm_cand = 180.0 + phase_at_w_cp
            
            all_w_cp.append(w_cp_cand)
            all_pm_deg.append(pm_cand)
            
        # On prend la marge la plus critique (la plus proche de 0 ou la plus faible)
        best_idx = np.argmin(all_pm_deg)
        w_cp = all_w_cp[best_idx]
        pm_deg = all_pm_deg[best_idx]
    else:
        w_cp = np.nan
        pm_deg = np.inf

    # --- 2. Recherche de Wcg (Marge de Gain : quand Phase = -180°) ---
    # On cherche où la phase croise -180°
    sign_phase = np.sign(phase_deg_total - (-180.0))
    idx_phase_cross = np.where(np.diff(sign_phase) != 0)[0]
    
    if len(idx_phase_cross) > 0:
        all_w_cg = []
        all_gm_db = []
        
        for idx in idx_phase_cross:
            w_cg_cand = _interpolate_crossing(w[idx], w[idx+1], phase_deg_total[idx], phase_deg_total[idx+1], -180.0)
            gain_at_w_cg = np.interp(w_cg_cand, w, mag_db)
            
            # Marge de Gain = 0 dB - Gain(w_cg) = -Gain(w_cg)
            gm_cand = -gain_at_w_cg
            
            all_w_cg.append(w_cg_cand)
            all_gm_db.append(gm_cand)
            
        best_idx = np.argmin(np.abs(all_gm_db))
        w_cg = all_w_cg[best_idx]
        gm_db = all_gm_db[best_idx]
    else:
        w_cg = np.nan
        gm_db = np.inf
        
    return {
        'GM_dB': gm_db,
        'PM_deg': pm_deg,
        'Wcg': w_cg,
        'Wcp': w_cp
    }

def get_bode_diagram(num, den, tau=0.0, w_min=1e-3, w_max=1e4, n_points=3000):
    """
    Génère le diagramme de Bode parfait (Figure Plotly).
    """
    w = np.logspace(np.log10(w_min), np.log10(w_max), n_points)

    try:
        w, h_complex = signal.freqs(num, den, worN=w)
    except TypeError:
        w, h_complex = signal.freqs(num, den, w=w)
    
    mag_db = 20 * np.log10(np.abs(h_complex))
    
    # Phase sans décalage artificiel
    phase_rad = np.unwrap(np.angle(h_complex))
    phase_deg = np.rad2deg(phase_rad)
    
    # Prise en compte du retard pur
    phase_deg_total = phase_deg - np.rad2deg(tau * w)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.1,
                        subplot_titles=("Gain (dB)", "Phase (°)"))

    # Courbe de Gain
    fig.add_trace(go.Scatter(x=w, y=mag_db, mode='lines', name='Gain',
                             line=dict(color='#00ff88', width=2)), row=1, col=1)

    # Courbe de Phase
    fig.add_trace(go.Scatter(x=w, y=phase_deg_total, mode='lines', name='Phase',
                             line=dict(color='#00d4ff', width=2)), row=2, col=1)

    # Ligne de référence à -180° pour la phase
    fig.add_shape(type="line", x0=w_min, x1=w_max, y0=-180, y1=-180,
                  line=dict(color="red", width=1, dash="dash"), row=2, col=1)

    # Ligne de référence à 0 dB pour le gain
    fig.add_shape(type="line", x0=w_min, x1=w_max, y0=0, y1=0,
                  line=dict(color="rgba(255,255,255,0.4)", width=1, dash="dot"), row=1, col=1)

    # Configuration des axes
    fig.update_xaxes(type="log", row=1, col=1)
    fig.update_xaxes(type="log", title_text="Pulsation (rad/s)", row=2, col=1)
    
    fig.update_yaxes(title_text="Gain (dB)", row=1, col=1)
    fig.update_yaxes(title_text="Phase (°)", row=2, col=1)

    fig.update_layout(height=700, template="plotly_dark", 
                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      margin=dict(t=50, b=50, l=50, r=50))

    return fig