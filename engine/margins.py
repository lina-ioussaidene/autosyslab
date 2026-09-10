import numpy as np
from scipy import signal
from scipy.optimize import fsolve

def calculate_margins(num, den, tau=0.0):
    """
    Calcule les marges de stabilité (Gain et Phase) et les pulsations de coupure.
    Méthode haute précision identique à MATLAB.
    """
    # 1. Définition de la fonction système H(jw) * exp(-j*w*tau)
    def get_response(w):
        w_poly = complex(0, w)
        # Calcul de la partie rationnelle
        num_val = np.polyval(num, w_poly)
        den_val = np.polyval(den, w_poly)
        rational_part = num_val / den_val
        # Ajout du retard pur : exp(-j*w*tau)
        retard_part = np.exp(-1j * w * tau)
        return rational_part * retard_part

    # 2. Fonctions pour trouver les racines (0 dB et -180°)
    def gain_condition(w):
        if w <= 0: return 999
        return 20 * np.log10(np.abs(get_response(w)))

    def phase_condition(w):
        if w <= 0: return 999
        resp = get_response(w)
        # On cherche l'angle et on le normalise par rapport à -180
        angle = np.angle(resp) # rad entre -pi et pi
        return np.rad2deg(angle) + 180

    # 3. Recherche de w_gc (Gain Crossover Frequency) -> |H(jw)| = 1 (0 dB)
    # On commence par une estimation large
    w_range = np.logspace(-3, 5, 1000)
    gains = [gain_condition(w) for w in w_range]
    
    # Trouver le passage par zéro du gain
    w_gc = None
    for i in range(len(gains)-1):
        if gains[i] * gains[i+1] <= 0:
            w_start = w_range[i]
            w_gc_found = fsolve(gain_condition, w_start)[0]
            w_gc = float(w_gc_found)
            break

    # 4. Recherche de w_pc (Phase Crossover Frequency) -> Phase = -180°
    w_pc = None
    phases = [phase_condition(w) for w in w_range]
    for i in range(len(phases)-1):
        if phases[i] * phases[i+1] <= 0:
            w_start = w_range[i]
            w_pc_found = fsolve(phase_condition, w_start)[0]
            w_pc = float(w_pc_found)
            break

    # 5. Calcul des marges finales
    margin_gain = float('inf')
    margin_phase = float('inf')

    if w_pc is not None and w_pc > 0:
        gain_at_wpc = 20 * np.log10(np.abs(get_response(w_pc)))
        margin_gain = -gain_at_wpc # MG = 0 - Gain(w_pc)
    
    if w_gc is not None and w_gc > 0:
        resp_at_wgc = get_response(w_gc)
        phase_at_wgc = np.rad2deg(np.angle(resp_at_wgc))
        # Marge de phase = 180 + phase (en restant dans le domaine classique)
        margin_phase = 180 + phase_at_wgc
        if margin_phase > 180: margin_phase -= 360

    return {
        "w_gc": w_gc,       # Pulsation de coupure (rad/s)
        "margin_phase": margin_phase, # Marge de phase (deg)
        "w_pc": w_pc,       # Pulsation de phase (rad/s)
        "margin_gain": margin_gain,   # Marge de gain (dB)
        "is_stable": (margin_gain > 0 and margin_phase > 0) if (w_gc and w_pc) else True
    }