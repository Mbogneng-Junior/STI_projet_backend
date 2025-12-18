from google.adk.tools import FunctionTool

def list_available_domains_fn() -> str:
    """
    Liste tous les domaines médicaux disponibles dans le système pour lesquels un expert existe.
    
    Returns:
        Une liste des noms de domaines (ex: "Paludisme", "Cardiologie").
    """
    from module_expert.models import DomaineMedical
    try:
        domaines = DomaineMedical.objects.values_list('nom', flat=True)
        return list(domaines)
    except Exception:
        return []

list_available_domains = FunctionTool(func=list_available_domains_fn)
