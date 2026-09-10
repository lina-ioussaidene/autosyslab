import numpy as np
import scipy.linalg as la

def analyze_properties(A, B, C):
    """
    Calcule les matrices de commandabilité (Mc) et d'observabilité (Mo)
    et détermine si le système est commandable et observable.
    """
    n = A.shape[0]
    
    # --- COMMANDABILITÉ (Kalman) ---
    # Mc = [B, AB, A^2B, ..., A^(n-1)B]
    Mc = B
    for i in range(1, n):
        Mc = np.hstack((Mc, np.linalg.matrix_power(A, i).dot(B)))
    
    rank_c = np.linalg.matrix_rank(Mc)
    is_commandable = (rank_c == n)
    
    # --- OBSERVABILITÉ (Kalman) ---
    # Mo = [C; CA; CA^2; ...; CA^(n-1)]
    Mo = C
    for i in range(1, n):
        Mo = np.vstack((Mo, C.dot(np.linalg.matrix_power(A, i))))
    
    rank_o = np.linalg.matrix_rank(Mo)
    is_observable = (rank_o == n)
    
    return {
        "Mc": Mc,
        "rank_c": rank_c,
        "is_commandable": is_commandable,
        "Mo": Mo,
        "rank_o": rank_o,
        "is_observable": is_observable,
        "n": n
    }