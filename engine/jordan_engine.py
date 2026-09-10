import numpy as np
import scipy.signal as signal

def get_jordan_representation(num, den, tau=0.0, use_pade=False):
    try:
        # 1. Préparation et normalisation
        n_p, d_p = np.array(num, dtype=float), np.array(den, dtype=float)
        
        # Normalisation (coefficient dominant de den = 1)
        n_p = n_p / d_p[0]
        d_p = d_p / d_p[0]
        n_order = len(d_p) - 1
        
        # 2. Identification précise des pôles
        roots = np.roots(d_p)
        roots_list = []
        mults = []
        
        # Le tri regroupe par partie réelle PUIS par valeur absolue imaginaire
        sorted_roots = sorted(roots, key=lambda x: (round(x.real, 5), abs(round(x.imag, 5)), round(x.imag, 5)))

        for r in sorted_roots:
            found = False
            for i, ex_r in enumerate(roots_list):
                if abs(r - ex_r) < 1e-4: # Seuil de tolérance
                    mults[i] += 1
                    found = True
                    break
            if not found:
                roots_list.append(r)
                mults.append(1)

        is_diag = all(m == 1 for m in mults)

        # 3. Vérification de la multiplicité
        if not is_diag:
            return None, None, None, None, {
                'message': "⚠️ Multiplicité détectée : les pôles ne sont pas distincts. Le système nécessite une forme de Jordan (pseudo-diagonale).",
                'roots': roots_list,
                'multiplicities': mults,
                'is_diagonalizable': False
            }

        # 4. Construction des matrices si diagonalisable
        # --- Calcul du terme direct k (matrice D) ---
        res, pol, k = signal.residue(n_p, d_p) 
        
        Cj = np.zeros((1, n_order), dtype=complex)
        for i, r in enumerate(roots_list):
            idx_res = np.where(np.abs(pol - r) < 1e-4)[0][0]
            Cj[0, i] = res[idx_res]

        # Dj est récupéré ici via le terme k de la décomposition
        Dj = np.array([[float(k[0])]]) if len(k) > 0 else np.array([[0.0]])
        
        # 4.5 CONVERSION EN FORME MODALE RÉELLE (Élimination des 'j')
        A_real = np.zeros((n_order, n_order), dtype=float)
        B_real = np.zeros((n_order, 1), dtype=float)
        C_real = np.zeros((1, n_order), dtype=float)

        i = 0
        while i < n_order:
            r = roots_list[i]
            if abs(r.imag) < 1e-5:  # Cas 1 : Pôle réel simple
                A_real[i, i] = r.real
                B_real[i, 0] = 1.0
                C_real[0, i] = np.real(Cj[0, i])
                i += 1
            else:  # Cas 2 : Paire de pôles complexes conjugués
                if i + 1 >= n_order:
                    A_real[i, i] = r.real
                    B_real[i, 0] = 1.0
                    C_real[0, i] = np.real(Cj[0, i])
                    i += 1
                    continue

                sigma = r.real
                omega = abs(r.imag)
                
                idx_pos = i if r.imag > 0 else i + 1
                res_val = Cj[0, idx_pos]
                
                A_real[i, i]   = sigma
                A_real[i, i+1] = omega
                A_real[i+1, i] = -omega
                A_real[i+1, i+1] = sigma
                
                B_real[i, 0]   = 2.0
                B_real[i+1, 0] = 0.0
                
                C_real[0, i]   = np.real(res_val)
                C_real[0, i+1] = np.imag(res_val)
                
                i += 2

        # On remplace les matrices complexes par les matrices 100% réelles
        Aj, Bj, Cj = A_real, B_real, C_real

        # --- Fin : Retour des matrices (Note : Le bloc 5 a été supprimé pour éviter l'écrasement de Dj) ---
        return Aj, Bj, Cj, Dj, {
            'message': "Success",
            'roots': roots_list,
            'multiplicities': mults,
            'is_diagonalizable': True,
            'ordre': n_order
        }

    except Exception as e:
        return None, None, None, None, {'message': f"Erreur de calcul : {str(e)}"}