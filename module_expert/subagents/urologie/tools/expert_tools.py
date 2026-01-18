import json
from google.adk.tools import FunctionTool
from google.adk.tools import ToolContext
from asgiref.sync import sync_to_async

async def search_uro_cases(symptoms: str, tool_context: ToolContext) -> str:
    """
    Recherche des cas cliniques similaires dans la base de connaissances
    pour le domaine : Urologie.
    
    Args:
        symptoms: Une description textuelle des symptômes observés.
        tool_context: Le contexte de l'outil fourni par l'ADK.
        
    Returns:
        Une chaîne JSON contenant les cas similaires trouvés.
    """
    from module_expert.models import CasClinique
    
    try:
        domaine_nom = "Urologie" 
        
        cas_similaires = await sync_to_async(CasClinique.objects.filter)(
            domaine__nom__iexact=domaine_nom,
            statut=CasClinique.StatutCas.PUBLIE
        )[:3]
        
        results = []
        for cas in cas_similaires:
            results.append({
                "titre": cas.titre,
                "contexte": cas.donnees_patient,
                "diagnostic_expert": cas.solution_experte,
                "explication": cas.historique_medical
            })
            
        if not results:
            return "Aucun cas similaire trouvé en Urologie."
            
        return json.dumps(results, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"Erreur lors de la recherche en Urologie: {str(e)}"

search_uro_cases = FunctionTool(func=search_uro_cases)
