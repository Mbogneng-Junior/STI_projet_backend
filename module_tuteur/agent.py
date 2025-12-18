import json
import asyncio
from asgiref.sync import sync_to_async
from google.adk.runners import Runner
from google.genai.types import Content, Part
from google.adk.sessions import DatabaseSessionService

# AJOUT DES IMPORTS POUR LA SAUVEGARDE
from google.adk.events import Event, EventActions

# Imports internes
from config.adk_session import db_url 
from module_expert.agent import expert_app
from module_expert.models import CasClinique, DomaineMedical
from module_apprenant.models import Apprenant, ProfilEtudiant, NiveauCompetence
from module_interface.models import SessionApprentissage, Interaction
from .strategies import StrategieSocratique, StrategieDirecte, StrategieScaffolding

class TuteurIA:
    # ... (code __init__ et _get_session_service inchangé) ...

    async def demarrer_session_async(self, apprenant_email, domaine_nom):
        # ... (code demarrer_session_async inchangé) ...
        pass

    async def analyser_reponse_async(self, session_id, reponse_etudiant, etape_actuelle):
        try:
            session_django = await SessionApprentissage.objects.select_related(
                'cas_clinique__domaine', 
                'apprenant'              
            ).aget(id=session_id)
            
            cas = session_django.cas_clinique
            apprenant = session_django.apprenant
            domaine = cas.domaine  
            
            profil = await ProfilEtudiant.objects.aget(apprenant=apprenant)
            adk_service = await self._get_session_service()

            runner = Runner(
                agent=expert_app.root_agent,
                app_name=expert_app.name,
                session_service=adk_service
            )

            prompt_content = (
                f"CONTEXTE: {cas.titre}\n"
                f"ÉTAPE: {etape_actuelle}\n"
                f"RÉPONSE: '{reponse_etudiant}'\n"
                f"SOLUTION: {cas.solution_experte}\n"
                "Ta mission : Valide cette réponse médicalement.\n"
                "Format JSON impératif : { \"correct\": bool, \"raison\": \"string\", \"erreurs_detectees\": [\"string\"] }" # <--- AJOUT "erreurs_detectees" ici
            )
            
            user_message = Content(parts=[Part(text=prompt_content)])

            expert_response_text = ""
            async for event in runner.run_async(
                user_id=str(apprenant.id),
                session_id=str(session_id),
                new_message=user_message
            ):
                if event.is_final_response() and event.content:
                    expert_response_text = event.content.parts[0].text

            session_adk = await adk_service.get_session(
                app_name=expert_app.name, 
                user_id=str(apprenant.id), 
                session_id=str(session_id)
            )

            try:
                clean_json = expert_response_text.replace('```json', '').replace('```', '').strip()
                resultat_expert = json.loads(clean_json)
                est_correct = resultat_expert.get('correct', False)
                raison_expert = resultat_expert.get('raison', '')
                erreurs_expert = resultat_expert.get('erreurs_detectees', []) # <--- RÉCUPÉRATION DES ERREURS
            except:
                est_correct = False
                raison_expert = expert_response_text
                erreurs_expert = []

            current_errors = session_adk.state.get("erreurs_consecutives", 0)
            
            if not est_correct:
                new_errors = current_errors + 1
            else:
                new_errors = 0

            state_update_event = Event(
                author="system",
                actions=EventActions(state_delta={"erreurs_consecutives": new_errors})
            )
            await adk_service.append_event(session_adk, state_update_event)

            # --- MODIFICATION ICI : Appel de la fonction de mise à jour ---
            await self._update_competence_django(profil, domaine, est_correct, erreurs_expert) 
            
            strategie = self._choisir_strategie(est_correct, new_errors)
            
            if est_correct:
                feedback = f"Bien joué ! {raison_expert}"
            else:
                feedback = strategie.generer_indice(cas.donnees_patient, etape_actuelle)

            await Interaction.objects.acreate(
                session=session_django,
                question_contenu=etape_actuelle,
                reponse_contenu=reponse_etudiant,
                reponse_est_valide=est_correct,
                feedback_contenu=feedback,
                feedback_type=strategie.style_feedback()
            )

            return {
                "valide": est_correct,
                "feedback": feedback,
                "expert_raw": raison_expert
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    @sync_to_async
    def _update_competence_django(self, profil, domaine, est_correct, erreurs_expert): # <--- AJOUT 'erreurs_expert'
        """
        Met à jour les compétences et le profil de l'apprenant.
        """
        # Mise à jour du NiveauCompetence
        comp, _ = NiveauCompetence.objects.get_or_create(
            profil_etudiant=profil,
            domaine=domaine,
            defaults={'niveau_actuel': 'DEBUTANT'}
        )
        if est_correct:
            comp.score_diagnostic += 5
        else:
            comp.score_diagnostic = max(0, comp.score_diagnostic - 2)
        
        if comp.score_diagnostic > 50:
             comp.niveau_actuel = 'INTERMEDIAIRE'
             
        comp.save()

        # --- MISE À JOUR DU PROFIL ÉTUDIANT ---
        # Mise à jour de l'XP total
        if est_correct:
            profil.xp_total += 10 # Gagner plus d'XP pour une bonne réponse
        
        # Mise à jour des lacunes identifiées
        if not est_correct and erreurs_expert:
            current_lacunes = json.loads(profil.lacunes_identifiees or "[]")
            for erreur in erreurs_expert:
                if erreur not in current_lacunes:
                    current_lacunes.append(erreur)
            profil.lacunes_identifiees = json.dumps(current_lacunes)
        elif est_correct and profil.lacunes_identifiees:
            # Optionnel: Si l'élève réussit, on peut tenter de "résoudre" une lacune
            # Ici, on ne fait rien de sophistiqué, mais on pourrait vider si tout est bon.
            pass # Ou implémenter une logique de réduction/suppression des lacunes

        profil.save() # Sauvegarde le profil après toutes les modifications

    def _choisir_strategie(self, est_correct, nb_erreurs):
        if est_correct: return self.strategies['SOCRATIQUE']
        if nb_erreurs >= 2: return self.strategies['DIRECT']
        return self.strategies['SCAFFOLDING']

tuteur_service = TuteurIA()