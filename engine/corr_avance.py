# ==============================
# IMPORTS
# ==============================
import control as ct
import numpy as np
import math

# ==============================
# FONCTIONS UTILITAIRES (Isolées pour rendre le fichier autonome)
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
# SYNTHÈSE : AVANCE DE PHASE
# ==============================
def calcul_avance_phase(sys_tf, specs):
    """
    Correcteur à avance de phase.
    Forme : C(s) = K * (1 + a*T*s) / (1 + T*s) avec a > 1
    Centre l'apport de phase maximal exactement sur wc_desiree.
    """
    mp_desiree, wc_desiree = _extraire_specs_frequentielles(specs)
    sys_mag, sys_phase = _evaluer_systeme(sys_tf, wc_desiree)
    
    # 1. Calcul du déphasage à apporter (phi_max)
    # Marge de sécurité de 5° car l'ajout du gain K va légèrement décaler la phase
    marge_securite = 5.0 
    phi_max_deg = mp_desiree - (180.0 + sys_phase) + marge_securite
    
    # Sécurité physique : un réseau RC (avance de phase) ne peut pas donner plus de ~65°
    # Et on ne peut pas donner une avance négative (sinon c'est un retard de phase !)
    phi_max_deg = max(1.0, min(65.0, phi_max_deg))
    phi_max_rad = phi_max_deg * (math.pi / 180.0)
    
    # 2. Calcul du paramètre d'écartement 'a' (où a > 1)
    sin_phi = math.sin(phi_max_rad)
    a = (1.0 + sin_phi) / (1.0 - sin_phi)
    
    # 3. Calcul de la constante de temps 'T'
    # Pour que la phase max soit centrée sur wc_desiree, il faut : wc = 1 / (T * sqrt(a))
    T = 1.0 / (wc_desiree * math.sqrt(a))
    
    # 4. Calcul du gain 'K'
    # Le correcteur amplifie le signal de sqrt(a) à la pulsation de coupure wc_desiree.
    # Pour avoir 0 dB (gain unitaire) de la boucle ouverte à wc_desiree, il faut :
    # K * sqrt(a) * sys_mag = 1
    K = 1.0 / (sys_mag * math.sqrt(a))
    
    # ==============================
    # CRÉATION DE LA FONCTION DE TRANSFERT
    # ==============================
    # C(s) = K * (a*T*s + 1) / (T*s + 1)
    num_c = [K * a * T, K]
    den_c = [T, 1.0]
    
    C_s = ct.TransferFunction(num_c, den_c)
    
    # Formatage LaTeX propre
    latex_str = rf"C(s) = {K:.3f} \frac{{1 + {a*T:.3f}s}}{{1 + {T:.3f}s}}"
    
    return C_s, latex_str

# ==============================
# TEST RAPIDE
# ==============================
if __name__ == "__main__":
    # Test avec un intégrateur + constante de temps : G(s) = 1 / (s * (s + 1))
    sys_test = ct.TransferFunction([1], [1, 1, 0])
    
    # On demande une bonne marge de phase (60°) à une pulsation de 2 rad/s
    specs_test = {"type_cahier": "frequentiel", "marge_phase": 60.0, "omega_c": 2.0}
    
    print("--- CORRECTEUR AVANCE DE PHASE ---")
    C_avance, latex_avance = calcul_avance_phase(sys_test, specs_test)
    print("LaTeX :", latex_avance)
    print("TF    :\n", C_avance)