import asyncio
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService, Session
from google.adk.events import Event, EventActions
from google.genai.types import Content, Part

# Imports des Agents
from module_expert.subagents.patient.agent import patient_agent
from module_tuteur.agent import tuteur_agent

# Imports des sous-agents experts spécifiques pour la délégation
from module_expert.subagents import (
    malaria_expert,
    cardiologie_expert,
    pediatrie_expert,
    dermatologie_expert
)

class TuteurOrchestrator:
    
    def __init__(self):
        self.expert_sub_agents = { 
            "Paludisme": malaria_expert,
            "Cardiologie": cardiologie_expert,
            "Dermatologie": dermatologie_expert,
            "Pédiatrie": pediatrie_expert,
        }

    async def get_session_details(self, session_id: str, user_id: str, session_service: DatabaseSessionService):
        if not user_id:
            return None
        session = await session_service.get_session(
            app_name="sti_app", session_id=session_id, user_id=user_id
        )
        return session.state if session else None

    async def traiter_interaction(self, user_id: str, session_id: str, message_etudiant: str, session_service: DatabaseSessionService):
        print(f"\n🚀 DÉBUT INTERACTION (Session {session_id} - User {user_id})")

        # -------------------------------------------------------------
        # ÉTAPE A : AGENT PATIENT (Génération de la réponse)
        # -------------------------------------------------------------
        print("🏥 A. Le patient réfléchit et répond...")
        runner_patient = Runner(agent=patient_agent, app_name="sti_app", session_service=session_service)
        
        reponse_patient_text = "Le patient n'a pas pu formuler de réponse."
        async for event in runner_patient.run_async(user_id=user_id, session_id=session_id, new_message=Content(parts=[Part(text=message_etudiant)])):
            if event.is_final_response() and event.content and event.content.parts:
                reponse_patient_text = event.content.parts[0].text.strip('" ') # Nettoyage des guillemets
                break
        
        print(f"   💬 Réponse du patient générée : '{reponse_patient_text}'")

        # -------------------------------------------------------------
        # ÉTAPE B : MISE À JOUR DE L'HISTORIQUE
        # -------------------------------------------------------------
        print("💾 B. Persistance de l'échange dans l'historique...")
        state_before_update = await self.get_session_details(session_id, user_id, session_service)
        if not state_before_update:
             return {"error": "Impossible de récupérer la session pour mettre à jour l'historique."}

        current_history = state_before_update.get('history', [])
        current_history.append({"person": "doctor", "message": message_etudiant})
        current_history.append({"person": "patient", "message": reponse_patient_text})
        
        history_delta = {'history': current_history}
        history_update_event = Event(author="orchestrator", actions=EventActions(state_delta=history_delta))
        
        session_obj = await session_service.get_session(app_name="sti_app", session_id=session_id, user_id=user_id)
        await session_service.append_event(session_obj, history_update_event)


        await asyncio.sleep(0.2)

        # -------------------------------------------------------------
        # ÉTAPE B.1 : NETTOYAGE DE L'ANALYSE PRÉCÉDENTE (CORRECTION)
        # -------------------------------------------------------------
        print("🧹 B.1. Nettoyage de l'état d'analyse...")
        cleanup_delta = {'expert_analysis': 'Analyse en attente...'}
        cleanup_event = Event(author="orchestrator", actions=EventActions(state_delta=cleanup_delta))
        await session_service.append_event(session_obj, cleanup_event)
        
        # -------------------------------------------------------------
        # ÉTAPE C : ROUTAGE SANS IA
        # -------------------------------------------------------------
        print("🎓 C. Routage de l'expert (logique Python)...")
        domaine_nom = state_before_update.get("domaine")
        specific_expert_agent = self.expert_sub_agents.get(domaine_nom)
        
        # -------------------------------------------------------------
        # ÉTAPE D : SOUS-AGENT EXPERT SPÉCIFIQUE
        # -------------------------------------------------------------
        if specific_expert_agent:
            agent_name = specific_expert_agent.name
            print(f"🎓 D. Exécution de l'expert : {agent_name}...")
            runner_specific_expert = Runner(agent=specific_expert_agent, app_name="sti_app", session_service=session_service)
            async for _ in runner_specific_expert.run_async(user_id=user_id, session_id=session_id, new_message=Content(parts=[Part(text="Analyse le dernier échange.")])):
                pass
        else:
            print(f"❌ Erreur de routage pour le domaine '{domaine_nom}'.")

        # -------------------------------------------------------------
        # ÉTAPE E : AGENT TUTEUR
        # -------------------------------------------------------------
        print("🧠 E. Le tuteur décide du feedback...")
        runner_tuteur = Runner(agent=tuteur_agent, app_name="sti_app", session_service=session_service)
        async for _ in runner_tuteur.run_async(user_id=user_id, session_id=session_id, new_message=Content(parts=[Part(text="Analyse la situation.")])):
            pass

        # -------------------------------------------------------------
        # ÉTAPE F : CONSTRUCTION DE LA RÉPONSE FINALE
        # -------------------------------------------------------------
        final_session_state = await self.get_session_details(session_id, user_id, session_service)
        if not final_session_state:
            return {"error": "Session introuvable à la fin du traitement."}

        chat_history = final_session_state.get("history", [])
        tutor_feedback = final_session_state.get("tutor_feedback", "Le tuteur n'a pas donné de feedback.")
        
        return {
            "status": "success",
            "latest_exchange": {"patient": reponse_patient_text, "tutor": tutor_feedback},
            "chat_history": chat_history,
            "internal_reasoning": {
                # On lit la clé corrigée, sans le préfixe "temp:"
                "expert_analysis": final_session_state.get("expert_analysis", "N/A"), 
                "logs_history": final_session_state.get("internal_logs", [])
            },
            "student_profile": final_session_state.get("student_profile", {})
        }

# Singleton
orchestrator = TuteurOrchestrator()