from google import genai
from google.genai import types

def get_autobot_response(user_query, system_data=None, api_key=None):
    """
    Génère une réponse via Google AI Studio (Gemini).
    """
    if not api_key:
        return "Erreur : La clé API Gemini n'est pas configurée dans les secrets."

    try:
        # Initialisation du client avec ta clé cachée
        client = genai.Client(api_key=api_key)
        
        # Le "Prompt Système" qui définit le caractère de ton IA
        system_instruction = (
            "Tu es AutoBot, l'assistant d'intelligence artificielle intégré à AutoSysLab. "
            "Ton rôle est d'expliquer les concepts d'automatique (fonctions de transfert, "
            "retards, Bode, correcteurs PID, marges de stabilité) à l'utilisateur. "
            "Sois pédagogique, clair et concis. N'utilise pas de jargon inutile."
        )
        
        # On injecte les données actuelles de l'application si elles existent
        contexte_actuel = ""
        if system_data:
            contexte_actuel = f"\n\n[CONTEXTE INVISIBLE POUR L'IA - Données actuelles du système : {system_data}]"

        prompt_final = user_query + contexte_actuel

        # Génération de la réponse avec gemini-2.5-flash (le plus rapide pour le chat)
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt_final,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3, # Température basse pour des réponses techniques précises
            ),
        )
        return response.text
        
    except Exception as e:
        return f"Désolé, une erreur de connexion à l'IA s'est produite : {e}"