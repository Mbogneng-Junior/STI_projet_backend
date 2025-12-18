import json
from google.adk.tools import FunctionTool

def search_pedia_cases_fn(symptoms: str) -> str:
    """
    Recherche des cas cliniques similaires dans la base de connaissances
    pour le domaine de la Pédiatrie.
    
    Args:
        symptoms: Une description textuelle des symptômes observés.
        
    Returns:
        Une chaîne JSON contenant les cas similaires trouvés.
    """
    from module_expert.models import CasClinique
    
    try:
        domaine_nom = "Pédiatrie" 
        
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
            return "Aucun cas similaire trouvé en Pédiatrie."
            
        return json.dumps(results, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"Erreur recherche Pédiatrie: {str(e)}"

search_pedia_cases = FunctionTool(func=search_pedia_cases_fn)
