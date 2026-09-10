# ==============================
# IMPORTS
# ==============================
import control as ct
import numpy as np
import math

# ==============================
# FONCTIONS UTILITAIRES
# ==============================
def _extraire_specs_frequentielles(specs):
    """
    Traduit les spécifications temporelles en spécifications fréquentielles (si nécessaire).
    Cela permet d'avoir un algorithme universel qui fonctionne pour n'importe quel ordre.
    """
    if specs.get("type_cahier") == "temporel":
        dep = specs.get("depassement", 5.0)
        tr5 = specs.get("tr5", 2.0)
        
        # 1. Calcul du coefficient d'amortissement (zeta) à partir du dépassement
        dep_frac = max(0.001, dep / 100.0) # Évite le log(0)
        zeta = -np.log(dep_frac) / np.sqrt(np.pi**2 + np.log(dep_frac)**2)
        
        # 2. Calcul de la pulsation naturelle (wn) à partir du tr5%
        wn = 3.0 / (zeta * tr5)
        
        # 3. Équivalence empirique (très utilisée en industrie)
        mp_desiree = min(85.0, zeta * 100.0) # Mp ≈ 100*zeta (en degrés)
        wc_desiree = wn                      # Wc ≈ Wn
        
        return mp_desiree, wc_desiree
    else:
        # Si c'est déjà fréquentiel, on récupère directement
        return specs.get("marge_phase", 45.0), specs.get("omega_c", 10.0)


def _evaluer_systeme(sys_tf, wc):
    """ Évalue le gain et la phase du système non corrigé à la pulsation wc """
    mag, phase, _ = ct.bode(sys_tf, [wc], plot=False)
    # Conversion de la phase en degrés et du gain en scalaire
    return mag[0], phase[0] * (180.0 / math.pi)

# ==============================
# SYNTHÈSE : CORRECTEURS P, PI, PID
# ==============================

def calcul_P(sys_tf, specs):
    """
    Correcteur Proportionnel : C(s) = Kp
    Force la pulsation de coupure wc_desiree.
    """
    _, wc_desiree = _extraire_specs_frequentielles(specs)
    
    # Gain du système actuel à wc_desiree
    sys_mag, _ = _evaluer_systeme(sys_tf, wc_desiree)
    
    # Pour que |C(jwc)*G(jwc)| = 1, il faut que Kp = 1 / |G(jwc)|
    Kp = 1.0 / sys_mag
    
    C_s = ct.TransferFunction([Kp], [1])
    latex_str = rf"C(s) = {Kp:.3f}"
    
    return C_s, latex_str


def calcul_PI(sys_tf, specs):
    """
    Correcteur Proportionnel Intégral : C(s) = Kp * (1 + 1/(Ti*s))
    Garantit la marge de phase et la pulsation de coupure.
    """
    mp_desiree, wc_desiree = _extraire_specs_frequentielles(specs)
    sys_mag, sys_phase = _evaluer_systeme(sys_tf, wc_desiree)
    
    # 1. Phase que le correcteur doit apporter
    # Règle : Phase_C + Phase_G = -180 + Marge_Phase
    phi_c_deg = -180.0 + mp_desiree - sys_phase
    
    # Un PI ne peut apporter qu'une phase entre -90° et 0°.
    # On borne la phase pour éviter un plantage mathématique si le système nécessite une avance.
    phi_c_deg = max(-85.0, min(-5.0, phi_c_deg))
    phi_c_rad = phi_c_deg * (math.pi / 180.0)
    
    # 2. Calcul de Ti
    # Phase d'un PI = arctan(-1 / (wc * Ti)) => Ti = -1 / (wc * tan(phi_c))
    Ti = -1.0 / (wc_desiree * math.tan(phi_c_rad))
    
    # 3. Calcul de Kp
    # Gain d'un PI = Kp * sqrt(1 + (1/(wc*Ti))^2) = 1 / sys_mag
    module_PI = math.sqrt(1.0 + (1.0 / (wc_desiree * Ti))**2)
    Kp = (1.0 / sys_mag) / module_PI
    
    C_s = ct.TransferFunction([Kp * Ti, Kp], [Ti, 0])
    latex_str = rf"C(s) = {Kp:.3f} \left(1 + \frac{{1}}{{{Ti:.3f}s}}\right)"
    
    return C_s, latex_str


def calcul_PID(sys_tf, specs):
    """
    Correcteur PID : C(s) = Kp * (1 + 1/(Ti*s) + Td*s)
    Algorithme robuste avec ratio de Ziegler-Nichols (Ti = 4*Td).
    """
    mp_desiree, wc_desiree = _extraire_specs_frequentielles(specs)
    sys_mag, sys_phase = _evaluer_systeme(sys_tf, wc_desiree)
    
    # 1. Phase que le correcteur doit apporter
    phi_c_deg = -180.0 + mp_desiree - sys_phase
    
    # Un PID peut apporter du retard ou de l'avance (borne entre -85° et +85° par sécurité)
    phi_c_deg = max(-85.0, min(85.0, phi_c_deg))
    phi_c_rad = phi_c_deg * (math.pi / 180.0)
    
    X = math.tan(phi_c_rad)
    
    # 2. Calcul de Td et Ti (en imposant Ti = 4*Td pour une bosse de phase symétrique)
    # Équation : wc*Td - 1/(4*wc*Td) = X  => Résolution d'un polynôme du 2nd degré
    y = (X + math.sqrt(X**2 + 1.0)) / 2.0
    Td = y / wc_desiree
    Ti = 4.0 * Td
    
    # 3. Calcul de Kp
    module_PID = math.sqrt(1.0 + X**2)
    Kp = (1.0 / sys_mag) / module_PID
    
    # Construction de la fonction de transfert : Kp + Kp/(Ti*s) + Kp*Td*s
    # Sous forme fraction : Kp * (Ti*Td*s^2 + Ti*s + 1) / (Ti*s)
    num_c = [Kp * Ti * Td, Kp * Ti, Kp]
    den_c = [Ti, 0]
    
    C_s = ct.TransferFunction(num_c, den_c)
    latex_str = rf"C(s) = {Kp:.3f} \left(1 + \frac{{1}}{{{Ti:.3f}s}} + {Td:.3f}s\right)"
    
    return C_s, latex_str

# ==============================
# TEST RAPIDE
# ==============================
if __name__ == "__main__":
    # Test avec un système d'ordre 3
    sys_test = ct.TransferFunction([1], [1, 3, 3, 1])
    
    # Simulation d'un cahier des charges (Dépassement 5%, Temps rep 2s)
    specs_test = {"type_cahier": "temporel", "depassement": 5.0, "tr5": 2.0}
    
    print("--- CORRECTEUR PID ---")
    C_pid, latex_pid = calcul_PID(sys_test, specs_test)
    print(latex_pid)
    print(C_pid)