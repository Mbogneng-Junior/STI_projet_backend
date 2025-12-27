from google.adk.tools import FunctionTool
from google.adk.tools import ToolContext

async def get_session_domain_fn(tool_context: ToolContext) -> str:
    """
    Récupère le nom du domaine médical actuellement actif dans la session.
    Cet outil ne prend aucun paramètre LLM et retourne directement la chaîne du domaine.
    """
    print(f"--- ⚙️ TOOL (get_session_domain): Lecture du domaine depuis le state: {tool_context.state.get('domaine', 'Inconnu')} ---")
    return tool_context.state.get("domaine", "Domaine_Non_Defini_Dans_Session")

get_session_domain = FunctionTool(func=get_session_domain_fn)