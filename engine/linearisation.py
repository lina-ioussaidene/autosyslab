import streamlit as st
import sympy as sp
import numpy as np
from scipy import signal # Indispensable pour la conversion ss2tf

def module_linearisation():
    st.subheader("Générateur de Modèle Linéarisé (Ordre n universel)")

    # 1. Sélection dynamique des dimensions (n états, m commandes)
    col_dim1, col_dim2 = st.columns(2)
    with col_dim1:
        n = st.number_input("Ordre du système (nombre d'états n)", min_value=1, max_value=20, value=3, step=1)
    with col_dim2:
        m = st.number_input("Nombre de commandes (entrées m)", min_value=1, max_value=10, value=1, step=1)

    # Génération 100% automatique des noms par défaut : x1, x2... xn et u1, u2... um
    default_x = ", ".join([f"x{i+1}" for i in range(n)])
    default_u = "u" if m == 1 else ", ".join([f"u{j+1}" for j in range(m)])

    # 2. Déclaration des symboles par l'utilisateur
    col1, col2 = st.columns(2)
    with col1:
        str_etats = st.text_input("Variables d'état (X)", value=default_x)
    with col2:
        str_commandes = st.text_input("Variables de commande (U)", value=default_u)
    
    etats = sp.symbols(str_etats)
    commandes = sp.symbols(str_commandes)
    
    # Sécurisation : conversion en liste Python pour éviter les erreurs d'index si n=1
    liste_etats = list(etats) if isinstance(etats, (tuple, list)) else [etats]
    liste_commandes = list(commandes) if isinstance(commandes, (tuple, list)) else [commandes]

    # 3. Saisie DYNAMIQUE des n équations différentielles
    st.markdown("### Saisie des équations différentielles ($\dot{X} = f(X, U)$)")
    
    st.info("📝 **Note de syntaxe importante** : Utilisez `*` pour multiplier (ex: `2*x`), `**` pour les puissances (ex: `x**2`), et les fonctions comme `sin()`, `cos()`, `exp()`, `sqrt()`.")
    
    eq_strs = []
    for i in range(n):
        # Récupère le nom réel de la variable tapée par l'utilisateur (ex: x1, z, theta...)
        nom_var = str(liste_etats[i]) if i < len(liste_etats) else f"x{i+1}"
        
        # Génère automatiquement le champ pour l'équation de cette variable précise
        eq = st.text_input(
            label=f"$\dot{{{nom_var}}} =$ (Dérivée de {nom_var})", 
            value="0", 
            key=f"eq_input_{i}_n{n}_m{m}" # Clé unique qui s'adapte au changement de n et m
        )
        eq_strs.append(eq)

    if st.button("🔄 Linéariser le système", type="primary"):
        try:
            # Transformation dynamique de toute la liste d'équations en symboles SymPy
            f_list = [sp.sympify(eq) for eq in eq_strs]
            
            Matrice_F = sp.Matrix(f_list)
            Matrice_X = sp.Matrix(liste_etats)
            Matrice_U = sp.Matrix(liste_commandes)

            # Avertissement de sécurité si l'utilisateur a tapé moins de variables que l'ordre n
            if len(liste_etats) != n:
                st.warning(f"⚠️ Attention : Vous avez choisi un ordre {n}, mais vous avez déclaré {len(liste_etats)} variables d'état dans le champ X.")
            if len(liste_commandes) != m:
                st.warning(f"⚠️ Attention : Vous avez choisi {m} commandes, mais vous avez déclaré {len(liste_commandes)} variables dans le champ U.")

            # Calcul symbolique de la Jacobienne (A sera de taille n*n, B de taille n*m)
            A_sym = Matrice_F.jacobian(Matrice_X)
            B_sym = Matrice_F.jacobian(Matrice_U)

            # Stockage en session pour affichage et export ultérieur
            st.session_state['temp_A_latex'] = sp.latex(A_sym)
            st.session_state['temp_B_latex'] = sp.latex(B_sym)
            st.session_state['temp_A_sym'] = A_sym
            st.session_state['temp_B_sym'] = B_sym
            st.session_state['has_results'] = True

        except sp.SympifyError:
            st.error("❌ Erreur de syntaxe dans une ou plusieurs équations. Vérifiez les `*` pour les multiplications et les `**` pour les puissances.")
        except Exception as e:
            st.error(f"❌ Erreur de calcul symbolique : {str(e)}")

    # 4. Affichage et Export vers le module d'étude
    if st.session_state.get('has_results', False):
        st.divider()
        st.markdown("### 📊 Matrices Générées")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**Matrice de Dynamique $A$ ({n}×{n}) :**")
            st.latex(f"A = {st.session_state['temp_A_latex']}")
        with col_b:
            st.markdown(f"**Matrice de Commande $B$ ({n}×{m}) :**")
            st.latex(f"B = {st.session_state['temp_B_latex']}")

        st.markdown("")
        
        # --- EXPORTATION ET CONFIGURATION DES MATRICES POUR L'ÉTUDE ---
        if st.button("🚀 Exporter vers le module d'étude", type="primary"):
            try:
                A_sym = st.session_state['temp_A_sym']
                B_sym = st.session_state['temp_B_sym']

                # Conversion des matrices SymPy en tableaux NumPy numériques (float)
                A_num = np.array(A_sym.evalf(), dtype=float)
                B_num = np.array(B_sym.evalf(), dtype=float)

                # Matrice C par défaut : sélection de la première variable d'état x1 comme sortie y(t)
                n_states = A_num.shape[0]
                C_num = np.zeros((1, n_states), dtype=float)
                C_num[0, 0] = 1.0
                
                # Matrice D par défaut (système strictement propre)
                D_num = np.zeros((1, 1), dtype=float)

                # Extraction de la première colonne de B si le système est multi-entrées (MIMO)
                B_siso = B_num[:, 0:1] if B_num.shape[1] > 0 else B_num

                # Conversion de l'espace d'état vers la Fonction de Transfert G(s)
                num_ss, den_ss = signal.ss2tf(A_num, B_siso, C_num, D_num)

                # Nettoyage des imprécisions numériques (valeurs proches de zéro)
                num_clean = np.where(np.abs(num_ss.flatten()) < 1e-10, 0, num_ss.flatten())
                den_clean = np.where(np.abs(den_ss.flatten()) < 1e-10, 0, den_ss.flatten())

                num_clean = np.trim_zeros(num_clean, 'f')
                if len(num_clean) == 0:
                    num_clean = np.array([0.0])

                den_clean = np.trim_zeros(den_clean, 'f')
                if len(den_clean) == 0:
                    den_clean = np.array([1.0])

                # Injection directe dans le Session State principal d'AutoSysLab
                st.session_state.input_mode = "SS"
                st.session_state.is_ss_input = True
                st.session_state.A = A_num
                st.session_state.B = B_siso
                st.session_state.C = C_num
                st.session_state.D = D_num
                st.session_state.num = num_clean.tolist()
                st.session_state.den = den_clean.tolist()
                st.session_state.tau = 0.0
                st.session_state.analyse_active = True

                st.success("✅ Matrices exportées avec succès ! Le module d'étude est à jour.")
                st.rerun()

            except TypeError:
                st.error("⚠️ La matrice contient encore des symboles non numériques. Assurez-vous d'évaluer les variables avant de lancer l'exportation.")
            except Exception as e:
                st.error(f"❌ Erreur lors de l'exportation : {str(e)}")