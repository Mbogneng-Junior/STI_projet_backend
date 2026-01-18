from google.genai.types import Content, Part

def get_evaluation_prompt(context_history, domaine):
    return f"""
    Context: Une simulation médicale en {domaine}.
    Historique de la conversation:
    {context_history}
    
    Tache: Générer UNE SEULE question d'évaluation formative (QCM) pour l'étudiant à ce stade de la consultation.
    La question doit tester l'une des 4 compétences suivantes :
    1. Anamnese (Collecte de données)
    2. Examen Clinique (Signes physiques)
    3. Diagnostic (Raisonnement)
    4. Prise en charge (Traitement)
    
    Choisis la compétence la plus pertinente par rapport aux derniers échanges.
    
    Format de réponse attendu (JSON uniquement) :
    {{
        "competence": "Nom de la compétence",
        "question": "L'intitulé de la question",
        "options": ["Choix A", "Choix B", "Choix C", "Choix D"],
        "correct_answer": "Choix A",
        "explanation": "Pourquoi c'est la bonne réponse."
    }}
    """
