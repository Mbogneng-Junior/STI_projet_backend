import json
import asyncio
from asgiref.sync import sync_to_async
from google.adk.runners import Runner
from google.genai.types import Content, Part
from google.adk.sessions import DatabaseSessionService

# --- AJOUT DES IMPORTS POUR LA SAUVEGARDE ---
from google.adk.events import Event, EventActions

# Imports internes
from config.adk_session import db_url 
from module_expert.agent import expert_app
from module_expert.models import CasClinique, DomaineMedical
from module_apprenant.models import Apprenant, ProfilEtudiant, NiveauCompetence
from module_interface.models import SessionApprentissage, Interaction
from .strategies import StrategieSocratique, StrategieDirecte, StrategieScaffolding

class TuteurIA:
    
    def __init__(self):
        self.strategies = {
            'SOCRATIQUE': StrategieSocratique(),
            'DIRECT': StrategieDirecte(),
            'SCAFFOLDING': StrategieScaffolding()
        }

    async def _get_session_service(self):
        return DatabaseSessionService(db_url=db_url)

    async def demarrer_session_async(self, apprenant_email, domaine_nom):
        try:
            apprenant = await Apprenant.objects.aget(email=apprenant_email)
            domaine = await DomaineMedical.objects.aget(nom__iexact=domaine_nom)
            
            cas = await CasClinique.objects.filter(
                domaine=domaine, 
                statut=CasClinique.StatutCas.PUBLIE
            ).afirst()
            
            if not cas:
                return None, "Aucun cas disponible."

            session_django = await SessionApprentissage.objects.acreate(
                apprenant=apprenant,
                cas_clinique=cas
            )

            adk_service = await self._get_session_service()
            
            await adk_service.create_session(
                app_name=expert_app.name,
                user_id=str(apprenant.id),
                session_id=str(session_django.id),
                state={
                    "etape_courante": "Anamnèse",
                    "erreurs_consecutives": 0,
                    "cas_context": cas.donnees_patient
                }
            )

            return session_django, f"Session démarrée : {cas.titre}"

        except Exception as e:
            return None, str(e)

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
                "Valide la réponse (JSON: correct, raison)."
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

            # Récupération session ADK
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
            except:
                est_correct = False
                raison_expert = expert_response_text

            # --- LOGIQUE DE PERSISTANCE DU STATE ---
            current_errors = session_adk.state.get("erreurs_consecutives", 0)
            
            if not est_correct:
                new_errors = current_errors + 1
            else:
                new_errors = 0

            # IMPORTANT : On crée un "System Event" pour forcer la sauvegarde dans Postgres
            # C'est la méthode officielle ADK pour modifier l'état manuellement
            state_update_event = Event(
                author="system",
                actions=EventActions(state_delta={"erreurs_consecutives": new_errors})
            )
            # On utilise 'append_event' qui écrit en DB
            await adk_service.append_event(session_adk, state_update_event)

            # Mise à jour des autres systèmes
            await self._update_competence_django(profil, domaine, est_correct)
            
            # On utilise la nouvelle valeur pour la stratégie
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
    def _update_competence_django(self, profil, domaine, est_correct):
        comp, _ = NiveauCompetence.objects.get_or_create(
            profil_etudiant=profil,
            domaine=domaine,
            defaults={'niveau_actuel': 'DEBUTANT'}
        )
        if est_correct:
            comp.score_diagnostic += 5
        else:
            comp.score_diagnostic = max(0, comp.score_diagnostic - 2)
        comp.save()

    def _choisir_strategie(self, est_correct, nb_erreurs):
        if est_correct: return self.strategies['SOCRATIQUE']
        # Si 2 erreurs ou plus, stratégie DIRECTE
        if nb_erreurs >= 2: return self.strategies['DIRECT']
        return self.strategies['SCAFFOLDING']

tuteur_service = TuteurIA()