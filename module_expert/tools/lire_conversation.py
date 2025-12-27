from google.adk.tools.tool_context import ToolContext

def lire_conversation(tool_context: ToolContext) -> str:
    """
    Lit l'historique des conversations depuis le state de la session
    et le retourne sous forme de transcript formaté.
    
    Cet outil est utilisé par les agents (Patient, Expert, Tuteur) pour
    comprendre le contexte actuel de la discussion avant de prendre une décision.

    Args:
        tool_context (ToolContext): Le contexte de l'outil, contenant l'état de la session.

    Returns:
        str: Un résumé formaté des derniers échanges de la conversation,
             ou un message d'indication si l'historique est vide.
    """
    print("--- 📚 Outil (lire_conversation): Lecture de l'historique ---")

    # 1. Récupération de l'historique depuis le state
    # L'historique est géré par l'Orchestrateur, cet outil ne fait que le lire.
    history = tool_context.state.get("history", [])

    # 2. Cas où l'historique est (anormalement) vide à ce stade.
    # Dans le flux normal, l'orchestrateur aura déjà ajouté le premier message.
    if not history:
        return "L'historique de conversation est actuellement vide. L'agent ne dispose pas de contexte."

    # 3. Construction du Contexte Conversationnel
    # On prend les derniers échanges pour fournir un contexte pertinent sans surcharger le LLM.
    # Ajuste le nombre (ex: -6, -8, -10) selon la profondeur de mémoire souhaitée pour l'agent.
    contexte_window = history[-8:] # Inclut les 8 derniers messages

    formatted_dialogue = "Voici les derniers échanges de la consultation :\n"
    
    for i, echange in enumerate(contexte_window):
        # Assurez-vous que 'person' est "doctor" ou "patient"
        role_label = "PATIENT" if echange.get("person") == "patient" else "DOCTEUR (Étudiant)"
        message_content = echange.get("message", "[Message vide]")
        formatted_dialogue += f"[{i+1}] - {role_label} : {message_content}\n"
        
    # 4. Directive pour l'agent (pourquoi il a lu l'historique)
    formatted_dialogue += "\nAnalyse attentivement ce dialogue. Détermine ta prochaine action ou réponse en fonction de ce contexte."

    return formatted_dialogue