import json
from google.adk.tools import FunctionTool
from google.adk.tools import ToolContext # NOUVEL IMPORT : pour le contexte de l'outil
from asgiref.sync import sync_to_async # NOUVEL IMPORT : pour appeler le code synchrone depuis l'async

# Importation différée de models à l'intérieur de la fonction pour assurer l'initialisation de Django
# from module_expert.models import CasClinique # Retire cet import global

async def search_cardio_cases_fn(symptoms: str, tool_context: ToolContext) -> str:
    """
    Recherche des cas cliniques similaires dans la base de connaissances
    pour le domaine de la Cardiologie.
    
    Args:
        symptoms: Une description textuelle des symptômes observés.
        tool_context: Le contexte de l'outil fourni par l'ADK.
        
    Returns:
        Une chaîne JSON contenant les cas similaires trouvés.
    """
    # Importation locale pour garantir que Django est configuré au moment de l'appel de la fonction.
    from module_expert.models import CasClinique
    
    try:
        domaine_nom = "Cardiologie" 
        
        # Appel asynchrone à l'ORM Django (qui est synchrone par nature)
        # On utilise sync_to_async pour ne pas bloquer la boucle d'événements de l'ADK.
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
            return "Aucun cas similaire trouvé en Cardiologie."
            
        return json.dumps(results, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"Erreur lors de la recherche en Cardiologie: {str(e)}"

# Le FunctionTool doit être marqué comme asynchrone (is_async=True)
search_cardio_cases = FunctionTool(func=search_cardio_cases_fn, is_async=True)