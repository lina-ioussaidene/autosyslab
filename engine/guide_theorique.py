import streamlit as st
from fpdf import FPDF
import io

def get_pdf_bytes():
    """Génère un PDF structuré des lois de l'automatique avec conversion compatible Streamlit."""
    pdf = FPDF()
    pdf.add_page()
    
    # Titre Principal
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="AutoSysLab - Fiche de Revision Automatique", ln=True, align='C')
    pdf.ln(10)

    # Contenu théorique
    content_data = [
        ("1. Realisabilite et Fonction de Transfert", 
         "Un systeme est realisable si le degre du numerateur est inferieur ou egal a celui du denominateur. G(s) = N(s)/D(s)."),
        
        ("2. Stabilite des Systemes", 
         "Un systeme est stable si tous les poles (racines de D(s)) ont une partie reelle strictement negative : Re(pi) < 0."),
        
        ("3. Reponses Temporelles", 
         "Reponse a l'echelon : Comportement face a une consigne constante. Reponse naturelle : Comportement propre du systeme sans entree."),
        
        ("4. Marges de Stabilite (Bode)", 
         "Marge de Gain (Mg) : Gain a ajouter pour atteindre l'instabilite. Marge de Phase (Mphi) : Phase a ajouter avant d'atteindre -180 degres."),
        
        ("5. Systemes a Retard (Pade)", 
         "Le retard pur exp(-tau*s) est approche par un systeme du premier ordre : (1 - (tau/2)s) / (1 + (tau/2)s)."),
        
        ("6. Representation d'Etat", 
         "Modelisation matricielle : dx/dt = Ax + Bu et y = Cx + Du. Formes : FCC (Commandable), FCO (Observable), et Jordan (Diagonale).")
    ]

    for title, text in content_data:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, txt=title, ln=True)
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 8, txt=text)
        pdf.ln(5)

    # Conversion cruciale : bytearray -> bytes pour Streamlit
    return bytes(pdf.output())

def show_theoretical_guide():
    """Affiche l'interface de documentation pédagogique."""
    st.markdown("## 📚 Centre de Documentation AutoSysLab")
    st.write("Bienvenue dans votre espace d'apprentissage. Retrouvez ici les lois fondamentales utilisées par la plateforme.")

    # Zone de téléchargement
    try:
        pdf_data = get_pdf_bytes()
        st.download_button(
            label="📥 Télécharger la Fiche de Révision (PDF)",
            data=pdf_data,
            file_name="AutoSysLab_Revision.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Erreur lors de la préparation du PDF : {e}")

    st.divider()

    # --- ACCORDÉONS THÉORIQUES ---

    with st.expander("📖 1. Fonction de Transfert & Réalisabilité"):
        st.write("### Définition")
        st.write("La fonction de transfert $G(s)$ est le rapport des transformées de Laplace de la sortie et de l'entrée.")
        st.latex(r"G(s) = \frac{Y(s)}{U(s)} = \frac{b_m s^m + \dots + b_0}{a_n s^n + \dots + a_0}")
        st.write("**Loi de réalisation :**")
        st.info("Le système est réalisable si $n \ge m$. Si $n < m$, le système est dit 'impropre' et ne peut exister physiquement.")
        

    with st.expander("📍 2. Étude de la Stabilité"):
        st.write("### Condition de stabilité")
        st.write("Un système est stable si sa réponse impulsionnelle tend vers zéro. Mathématiquement, cela signifie que les pôles $p_i$ doivent être dans le demi-plan gauche.")
        st.latex(r"\text{Re}(p_i) < 0")
        st.write("Si un pôle a une partie réelle positive, le système diverge (instabilité).")
        

    with st.expander("📈 3. Réponses Temporelles"):
        st.write("### Réponse à l'échelon")
        st.write("Elle permet de mesurer la précision (gain statique) et la rapidité du système.")
        st.write("### Réponse Naturelle")
        st.write("C'est la réponse du système lorsqu'il est livré à lui-même (entrée nulle), dépendant uniquement de ses conditions initiales.")
        

    with st.expander("📉 4. Diagramme de Bode & Marges"):
        st.write("### Marges de stabilité")
        st.write("- **Marge de Gain ($M_g$) :** Facteur de gain minimal pour rendre le système instable.")
        st.latex(r"M_g = -20\log_{10}|G(j\omega_{180})|")
        st.write("- **Marge de Phase ($M_\phi$) :** Déphasage à ajouter pour atteindre l'instabilité.")
        st.latex(r"M_\phi = 180^\circ + \arg(G(j\omega_{c}))")
        

    with st.expander("🕒 5. Systèmes à Retard & Padé"):
        st.write("### Approximation du retard")
        st.write("Un retard pur $e^{-\tau s}$ est difficile à traiter en espace d'état. On utilise l'approximation de Padé d'ordre 1 :")
        st.latex(r"e^{-\tau s} \approx \frac{1 - \frac{\tau}{2}s}{1 + \frac{\tau}{2}s}")
        st.write("Cela permet de modéliser le retard comme un système du premier ordre.")

    with st.expander("🔢 6. Représentations d'État"):
        st.write("### Modèle Matriciel")
        st.latex(r"\begin{cases} \dot{x}(t) = Ax(t) + Bu(t) \\ y(t) = Cx(t) + Du(t) \end{cases}")
        st.write("**Formes Canoniques :**")
        st.write("- **Commandable (FCC) :** Met en évidence les coefficients du dénominateur.")
        st.write("- **Observable (FCO) :** Utile pour la conception d'observateurs.")
        st.write("- **Jordan :** Matrice A diagonale (ou blocs de Jordan), utile pour voir les modes propres.")