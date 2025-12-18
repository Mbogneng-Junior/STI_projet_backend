import json
from google.adk.tools import FunctionTool

def search_cardio_cases_fn(symptoms: str) -> str:
    """
    Recherche des cas cliniques similaires dans la base de connaissances
    pour le domaine de la Cardiologie.
    
    Args:
        symptoms: Une description textuelle des symptômes observés.
        
    Returns:
        Une chaîne JSON contenant les cas similaires trouvés.
    """
    from module_expert.models import CasClinique
    
    try:
        domaine_nom = "Cardiologie" 
        
        cas_similaires = CasClinique.objects.filter(
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
        return f"Erreur recherche Cardiologie: {str(e)}"

search_cardio_cases = FunctionTool(func=search_cardio_cases_fn)
