import json
from google.adk.tools import ToolContext
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist

from module_apprenant.models import Apprenant, NiveauCompetence, ProfilEtudiant
from module_expert.models import DomaineMedical

async def enregistrer_evaluations_multiples(evaluations_json: str, tool_context: ToolContext) -> str:
    """
    Met à jour PLUSIEURS compétences de l'étudiant en un seul appel.
    """
    print("--- 🎓 TOOL (enregistrer_evaluations_multiples): Données reçues ---")
    print(evaluations_json)
    print("---------------------------------------------------------------")
    
    try:
        evaluations = json.loads(evaluations_json)
        if not isinstance(evaluations, list):
            return "Erreur : le JSON fourni n'est pas une liste."
    except json.JSONDecodeError as e:
        return f"Erreur : La chaîne de caractères fournie n'est pas un JSON valide. Erreur : {e}"

    user_id = tool_context.state.get("user_id")
    domaine_nom = tool_context.state.get("domaine")

    if not user_id or not domaine_nom:
        return "Erreur système : user_id ou domaine manquant dans le state."

    # --- CORRECTION MAJEURE : MISE À JOUR DU STATE EN PREMIER ---

    # 1. On récupère le profil depuis l'état de la session (notre source de vérité)
    state_profile = tool_context.state.get("student_profile", {})

    # 2. On s'assure que les structures de données existent
    if "competences" not in state_profile or not isinstance(state_profile["competences"], dict):
        state_profile["competences"] = {}
    if "feedbacks" not in state_profile or not isinstance(state_profile["feedbacks"], list):
        state_profile["feedbacks"] = []
    if "score_global" not in state_profile:
        # On initialise avec le score de la BDD si c'est la première fois
        initial_profil = await sync_to_async(ProfilEtudiant.objects.get)(apprenant__id=user_id)
        state_profile["score_global"] = initial_profil.xp_total

    # 3. On applique les nouvelles évaluations à l'état en mémoire
    total_points_gagnes_ce_tour = 0
    for eval_item in evaluations:
        competence = eval_item.get("competence")
        points = eval_item.get("points", 0)
        
        if not all([competence, isinstance(points, int)]):
            continue # On ignore les items malformés

        # On ajoute les points au score existant dans le state
        current_score = state_profile["competences"].get(competence, 0)
        state_profile["competences"][competence] = current_score + points
        
        total_points_gagnes_ce_tour += points
        
        # On ajoute le feedback à la liste
        state_profile["feedbacks"].append({
            "competence": competence,
            "points": points,
            "message": eval_item.get("feedback"),
            "timestamp": "Now"
        })
    
    # On met à jour le score global
    state_profile["score_global"] += total_points_gagnes_ce_tour

    # 4. On sauvegarde l'état mis à jour dans le contexte de l'ADK.
    # C'est cette action qui garantit que l'UI verra les bonnes données.
    tool_context.state["student_profile"] = state_profile
    
    # --- FIN DE LA CORRECTION MAJEURE ---

    # --- MISE À JOUR DE LA BASE DE DONNÉES (pour la persistance à long terme) ---
    @sync_to_async
    def update_database_sync():
        try:
            apprenant = Apprenant.objects.get(id=user_id)
            profil, _ = ProfilEtudiant.objects.get_or_create(apprenant=apprenant)
            domaine_obj = DomaineMedical.objects.get(nom__iexact=domaine_nom)
            niveau_comp, _ = NiveauCompetence.objects.get_or_create(profil_etudiant=profil, domaine=domaine_obj)

            # La logique ici reste la même, elle garantit la cohérence de la BDD
            for eval_item in evaluations:
                competence = eval_item.get("competence")
                points = eval_item.get("points", 0)
                feedback = eval_item.get("feedback")

                if competence == "anamnese": niveau_comp.score_anamnese += points
                elif competence == "diagnostic": niveau_comp.score_diagnostic += points
                elif competence == "traitement": niveau_comp.score_traitement += points
                elif competence == "relationnel": niveau_comp.score_relationnel += points
                
                if points < 0 and feedback:
                    if not isinstance(profil.lacunes_identifiees, list): profil.lacunes_identifiees = []
                    profil.lacunes_identifiees.append({"domaine": domaine_nom, "feedback": feedback, "competence": competence})
            
            profil.xp_total += total_points_gagnes_ce_tour
            profil.save()
            niveau_comp.save()
            return {"success": True, "new_xp_db": profil.xp_total}

        except Exception as e:
            return {"success": False, "error": str(e)}

    db_result = await update_database_sync()

    if not db_result["success"]:
        # Même si la BDD échoue, l'état de la session est à jour. On signale juste l'erreur.
        return f"Échec de la persistance en base de données : {db_result['error']}"

    return f"✅ {len(evaluations)} évaluations traitées. XP Global (état session): {state_profile['score_global']}."