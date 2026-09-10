import control as ct

def format_latex_poly(coeffs):
    """Convertit une liste de coefficients en chaîne LaTeX propre."""
    # [Ton code original ne bouge pas ici]
    n = len(coeffs) - 1
    if n == 0 and coeffs[0] == 0: return "0"
    
    terms = []
    for i, c in enumerate(coeffs):
        pwr = n - i
        if c == 0: continue
        
        # Gestion du signe
        if i == 0:
            sign = "-" if c < 0 else ""
        else:
            sign = " + " if c > 0 else " - "
            
        abs_c = abs(c)
        # On n'affiche pas "1" devant s sauf si c'est le terme constant
        c_val = f"{abs_c:g}" if (abs_c != 1 or pwr == 0) else ""
        
        if pwr == 0: 
            term = f"{sign}{abs_c:g}"
        elif pwr == 1: 
            term = f"{sign}{c_val}s"
        else: 
            term = f"{sign}{c_val}s^{{{pwr}}}"
        terms.append(term)
        
    return "".join(terms).strip()

class AutoSystem:
    def __init__(self, num, den, tau=0):
        # 1. On garde les originaux pour le calcul mathématique pur
        self.num = num
        self.den = den
        self.tau = tau
        self.tf = ct.TransferFunction(num, den)

        # 2. Extraction du coefficient (pour le dénominateur uniquement)
        # On force k_num à 1 pour que get_latex ne modifie plus l'affichage du numérateur
        self.k_num = 1
        self.k_den = den[0] if len(den) > 0 and den[0] != 0 else 1

        # 3. Normalisation EXCLUSIVE du dénominateur
        self.norm_num = num  # Le numérateur reste intact
        self.norm_den = [c / self.k_den for c in den] if self.k_den != 0 else den

        # 4. Génération de la note de normalisation
        if self.k_den not in [0, 1]:
            self.msg_info = f"Le dénominateur a été normalisé (divisé par {self.k_den:g})."
        else:
            self.msg_info = ""

    def get_latex(self, with_delay=False):
        """
        Génère le LaTeX de la TF avec factorisation visuelle.
        """
        num_lat = format_latex_poly(self.norm_num)
        den_lat = format_latex_poly(self.norm_den)
        
        # Fonction interne pour bien placer les parenthèses lors de la factorisation
        def wrap_factor(k, poly_str):
            if k == 1:
                return poly_str
            # Si le polynôme a plusieurs termes (contient un + ou un - au milieu), on met des parenthèses
            if "+" in poly_str or " - " in poly_str:
                return f"{k:g}({poly_str})"
            # Cas particulier pour -1 sans autres termes
            if k == -1:
                return f"-{poly_str}"
            # Sinon on colle juste la constante (ex: 5s^2)
            return f"{k:g}{poly_str}"

        # Application de la factorisation visuelle
        num_final = wrap_factor(self.k_num, num_lat)
        den_final = wrap_factor(self.k_den, den_lat)
        
        base_tf = f"\\frac{{{num_final}}}{{{den_final}}}"
        
        if with_delay and self.tau > 0:
            return f"G(s) = {base_tf} \\cdot e^{{-{self.tau}s}}"
        return f"G(s) = {base_tf}"