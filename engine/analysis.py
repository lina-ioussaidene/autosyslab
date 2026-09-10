import control as ct
import numpy as np

def get_stability_analysis(sys):
    poles = ct.poles(sys)
    is_stable = all(np.real(poles) < 0)
    # Vérification limite de stabilité (pôles sur l'axe imaginaire)
    is_marginal = any(np.isclose(np.real(poles), 0)) and all(np.real(poles) <= 0)
    
    if is_stable:
        status = "Stable"
        color = "green"
    elif is_marginal:
        status = "À la limite de stabilité"
        color = "orange"
    else:
        status = "Instable"
        color = "red"
        
    return poles, status, color