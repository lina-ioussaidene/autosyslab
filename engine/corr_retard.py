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
    """ Traduit les spécifications temporelles en fréquentielles si nécessaire. """
    if specs.get("type_cahier") == "temporel":
        dep = specs.get("depassement", 5.0)
        tr5 = specs.get("tr5", 2.0)
        
        dep_frac = max(0.001, dep / 100.0)
        zeta = -np.log(dep_frac) / np.sqrt(np.pi**2 + np.log(dep_frac)**2)
        wn = 3.0 / (zeta * tr5)
        
        mp_desiree = min(85.0, zeta * 100.0)
        wc_desiree = wn
        return mp_desiree, wc_desiree
    else:
        return specs.get("marge_phase", 45.0), specs.get("omega_c", 10.0)

def _evaluer_systeme(sys_tf, wc):
    """ Évalue le gain et la phase du système à la pulsation wc. """
    mag, phase, _ = ct.bode(sys_tf, [wc], plot=False)
    return mag[0], phase[0] * (180.0 / math.pi)

# ==============================
# SYNTHÈSE : RETARD DE PHASE
# ==============================
def calcul_retard_phase(sys_tf, specs):
    """
    Correcteur à retard de phase.
    Forme : C(s) = K * (1 + a*T*s) / (1 + T*s) avec a < 1
    Conçu pour garantir la pulsation de coupure wc_desiree sans trop dégrader la phase.
    """
    _, wc_desiree = _extraire_specs_frequentielles(specs)
    sys_mag, sys_phase = _evaluer_systeme(sys_tf, wc_desiree)
    
    # 1. Choix du facteur d'atténuation 'a' (a < 1)
    # En pratique, on fixe souvent a = 0.1 pour avoir une bonne atténuation haute fréquence
    # sans décaler les pôles de manière irréaliste.
    a = 0.1
    
    # 2. Règle d'or du retard de phase : 
    # Placer le zéro (1 / aT) une décade en dessous de wc_desiree
    # Cela garantit que le retard de phase maximal ne tombe pas sur wc (il ajouterait de l'instabilité).
    # Équation : 1 / (a * T) = wc_desiree / 10
    T = 10.0 / (a * wc_desiree)
    
    # 3. Calcul du gain K pour forcer la coupure à wc_desiree
    # On évalue le gain de la partie (1 + a*T*s)/(1 + T*s) à s = j*wc
    module_retard = math.sqrt((1.0 + (a * T * wc_desiree)**2) / (1.0 + (T * wc_desiree)**2))
    
    # Pour que |C(jwc) * G(jwc)| = 1, il faut :
    K = 1.0 / (sys_mag * module_retard)
    
    # ==============================
    # CRÉATION DE LA FONCTION DE TRANSFERT
    # ==============================
    # C(s) = K * (a*T*s + 1) / (T*s + 1)
    num_c = [K * a * T, K]
    den_c = [T, 1.0]
    
    C_s = ct.TransferFunction(num_c, den_c)
    
    # Formatage LaTeX pour l'interface
    latex_str = rf"C(s) = {K:.3f} \frac{{1 + {a*T:.3f}s}}{{1 + {T:.3f}s}}"
    
    return C_s, latex_str

# ==============================
# TEST RAPIDE
# ==============================
if __name__ == "__main__":
    # Test avec un système classique
    sys_test = ct.TransferFunction([1], [1, 2, 1])
    
    # Specs
    specs_test = {"type_cahier": "frequentiel", "marge_phase": 45.0, "omega_c": 5.0}
    
    print("--- CORRECTEUR RETARD DE PHASE ---")
    C_retard, latex_retard = calcul_retard_phase(sys_test, specs_test)
    print("LaTeX :", latex_retard)
    print("TF    :\n", C_retard)