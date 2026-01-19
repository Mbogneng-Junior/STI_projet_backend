from google.adk.tools import ToolContext
from google.adk.runners import Runner
# On importe l'agent racine Expert
from module_expert.agent import root_agent 

async def consulter_expert_medical(question: str, tool_context: ToolContext) -> str:
    """
    Pose une question technique à l'Expert Médical pour obtenir de l'aide ou un indice.
    L'Expert répondra en 'Mode Consultant' (sans noter).
    
    Exemple: "Quels sont les symptômes clés que l'étudiant a oubliés ?"
    """
    print(f"--- 🤝 TUTEUR: Demande d'aide à l'Expert : '{question}' ---")
    
    # On lance un runner "one-shot" juste pour cette question
    # IMPORTANT: On réutilise le session_service du contexte actuel pour éviter l'erreur de paramètre manquant
    runner = Runner(agent=root_agent, session_service=tool_context.session_service)
    
    domaine = tool_context.state.get("domaine", "Général")
    # On force le prompt pour activer le mode consultant
    full_query = f"[MODE CONSULTANT - Domaine: {domaine}] {question}"

    result = await runner.run_async(query=full_query)
    
    return result.final_response.content