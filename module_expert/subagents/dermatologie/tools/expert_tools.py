import json
from google.adk.tools import FunctionTool
from google.adk.tools import ToolContext # NOUVEL IMPORT
from asgiref.sync import sync_to_async # NOUVEL IMPORT

# Importation différée de models à l'intérieur de la fonction
# from module_expert.models import CasClinique # Retire cet import global

async def search_derma_cases_fn(symptoms: str, tool_context: ToolContext) -> str:
    """
    Recherche des cas cliniques similaires dans la base de connaissances
    pour le domaine de la Dermatologie.
    
    Args:
        symptoms: Une description textuelle des symptômes observés.
        tool_context: Le contexte de l'outil fourni par l'ADK.
        
    Returns:
        Une chaîne JSON contenant les cas similaires trouvés.
    """
    # Importation locale pour garantir que Django est configuré au moment de l'appel de la fonction.
    from module_expert.models import CasClinique
    
    try:
        domaine_nom = "Dermatologie" 
        
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
            return "Aucun cas similaire trouvé en Dermatologie."
            
        return json.dumps(results, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"Erreur lors de la recherche en Dermatologie: {str(e)}"

search_derma_cases = FunctionTool(func=search_derma_cases_fn)