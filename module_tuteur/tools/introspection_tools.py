import json
from google.adk.tools import ToolContext
from asgiref.sync import sync_to_async
from module_apprenant.models import Apprenant, ProfilEtudiant, NiveauCompetence

async def lire_profil_etudiant(tool_context: ToolContext) -> str:
    """
    Récupère les statistiques, le niveau et les lacunes récentes de l'étudiant.
    À utiliser pour décider si l'étudiant a besoin d'aide ou non.
    """
    # ... (code existant, pas de changement)
    print("--- 📊 TUTEUR: Lecture du profil étudiant ---")
    user_id = tool_context.state.get("user_id")
    domaine_nom = tool_context.state.get("domaine")

    if not user_id:
        return "Erreur: ID étudiant manquant."

    def get_data_sync():
        try:
            apprenant = Apprenant.objects.get(id=user_id)
            profil = ProfilEtudiant.objects.get(apprenant=apprenant)
            
            # On cherche les compétences du domaine actuel
            comp = NiveauCompetence.objects.filter(
                profil_etudiant=profil, 
                domaine__nom__iexact=domaine_nom
            ).first()

            stats = {
                "xp_total": profil.xp_total,
                "lacunes_relevees": profil.lacunes_identifiees,
                "domaine": domaine_nom,
                "scores_actuels": "Aucun score pour ce domaine"
            }

            if comp:
                stats["scores_actuels"] = {
                    "anamnese": comp.score_anamnese,
                    "diagnostic": comp.score_diagnostic,
                    "traitement": comp.score_traitement,
                    "niveau": comp.niveau_actuel
                }
            
            return json.dumps(stats, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Erreur DB: {str(e)}"

    return await sync_to_async(get_data_sync)()


# <--- NOUVEL OUTIL À AJOUTER CI-DESSOUS ---

async def lire_analyse_expert(tool_context: ToolContext) -> str:
    """
    Lit le raisonnement interne de l'agent Expert Médical pour le tour actuel.
    Utilise cette information pour comprendre pourquoi l'étudiant a été bien ou mal noté.
    """
    print("--- 👁️ TUTEUR: Lecture de l'analyse de l'expert ---")
    
    # La clé "temp:expert_analysis" est remplie par l'output_key de l'agent expert
    analyse = tool_context.state.get("temp:expert_analysis", "L'expert n'a fourni aucune analyse pour ce tour.")
    
    return f"Voici le raisonnement de l'expert superviseur pour le dernier échange : \"{analyse}\""