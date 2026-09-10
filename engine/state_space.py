import numpy as np
import scipy.linalg as la

def matrix_to_latex(matrix, name):
    """Convertit une matrice numpy en LaTeX pour Streamlit."""
    if matrix is None: return ""
    # Nettoyage des valeurs infinitésimales
    matrix = np.where(np.abs(matrix) < 1e-7, 0, matrix)
    lines = []
    for row in matrix:
        # Formatage propre : pas de -0.0000 et suppression des zéros inutiles
        formatted_row = [f"{val:.4f}".rstrip('0').rstrip('.') if val != 0 else "0" for val in row]
        lines.append(" & ".join(formatted_row))
    return rf"{name} = \begin{{bmatrix}} {' \\\\ '.join(lines)} \end{{bmatrix}}"

def get_state_space_fcc(num, den):
    """Génère la Forme Canonique Commandable (FCC) robuste."""
    # Nettoyage des entrées
    num = np.trim_zeros(np.atleast_1d(num), 'f')
    den = np.trim_zeros(np.atleast_1d(den), 'f')
    
    # Normalisation par le premier coefficient du dénominateur
    a0 = den[0]
    a = den / a0
    n = len(a) - 1
    
    # Ajuster numérateur pour qu'il ait la même taille que le dénominateur
    b = np.zeros(n + 1)
    b_raw = num / a0
    b[len(b)-len(b_raw):] = b_raw
    
    # Matrice A (Compagnon)
    A = np.zeros((n, n))
    if n > 1:
        for i in range(n - 1):
            A[i, i + 1] = 1.0
    A[-1, :] = -a[:0:-1] 
    
    # Matrice B
    B = np.zeros((n, 1))
    if n > 0:
        B[-1, 0] = 1.0
    
    # Matrice C et D
    bn = b[0]
    C = np.zeros((1, n))
    a_rev = a[::-1]
    b_rev = b[::-1]
    for i in range(n):
        C[0, i] = b_rev[i] - a_rev[i] * bn
        
    D = np.array([[bn]])
    return A, B, C, D

def get_state_space_fco(num, den):
    """Forme Canonique Observable (Duale)."""
    A_fcc, B_fcc, C_fcc, D = get_state_space_fcc(num, den)
    return A_fcc.T, C_fcc.T, B_fcc.T, D

def get_state_space_jordan(num, den, tau=0.0):
    """Interface sécurisée vers le moteur Jordan."""
    try:
        from engine.jordan_engine import get_jordan_representation
        # On force les types en float pour numpy
        n = [float(x) for x in np.atleast_1d(num)]
        d = [float(x) for x in np.atleast_1d(den)]
        t = float(tau)
        # Si tau est déjà géré par Padé en amont dans app.py, 
        # app.py appellera cette fonction avec tau=0.0
        return get_jordan_representation(n, d, t, use_pade=(t > 0))
    except Exception as e:
        A, B, C, D = get_state_space_fcc(num, den)
        return A, B, C, D, {'message': f"Erreur Jordan : {e}", 'used_pade': False}