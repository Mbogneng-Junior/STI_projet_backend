import asyncio
import json
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService, Session
from google.adk.events import Event, EventActions
from google.genai.types import Content, Part

# Imports des Agents
from module_expert.subagents.patient.agent import patient_agent
from module_tuteur.agent import tuteur_agent
# Import de l'agent d'évaluation
from module_tuteur.evaluation_agent import evaluation_agent, summative_agent
import logging

logger = logging.getLogger(__name__)

# Imports des sous-agents experts spécifiques pour la délégation
from module_expert.subagents import (
    cardiologie_expert,
    medecine_generale_expert,
    endocrinologie_expert,
    medecine_interne_expert,
    pneumologie_expert,
    urgences_expert,
    urologie_expert
)

class TuteurOrchestrator:
    
    def __init__(self):
        self.expert_sub_agents = { 
            "Cardiologie": cardiologie_expert,
            "Endocrinologie": endocrinologie_expert,
            "Médecine générale": medecine_generale_expert,
            "Médecine interne": medecine_interne_expert,
            "Pneumologie": pneumologie_expert,
            "Urgences": urgences_expert,
            "Urologie": urologie_expert,
            # Compatibilité
            "Paludisme": medecine_generale_expert, 
        }

    async def get_session_details(self, session_id: str, user_id: str, session_service: DatabaseSessionService):
        if not user_id:
            return None
        session = await session_service.get_session(
            app_name="sti_app", session_id=session_id, user_id=user_id
        )
        return session.state if session else None

    async def generer_bilan_sommatif(self, session_id: str, user_id: str, session_service: DatabaseSessionService):
        """
        Génère le bilan sommatif de fin de session.
        """
        print(f"📊 Génération du bilan sommatif pour {session_id}...")
        
        # 1. Récupérer l'état de la session
        session = await session_service.get_session(
            app_name="sti_app", session_id=session_id, user_id=user_id
        )
        if not session:
            return None
            
        state = session.state
        history = state.get("history", [])
        
        # 2. Préparer le contexte pour l'agent
        history_text = "\n".join([f"{msg['person']}: {msg['message']}" for msg in history])
        cas_context = json.dumps(state.get("cas_context", {}), indent=2, ensure_ascii=False)

        prompt = f"""
        CONTEXTE DU CAS CLINIQUE :
        {cas_context}

        HISTORIQUE COMPLET DE LA CONSULTATION :
        {history_text}
        
        Génère le bilan sommatif JSON maintenant selon tes instructions.
        """

        # 3. Appeler l'agent sommatif via un Runner éphémère
        response_text = ""
        # Pour une évaluation ponctuelle sans session persistante, on peut utiliser Model.generate_content
        # ou un runner avec une session en mémoire pour cet agent.
        # Ici on utilise model.generate_content() directement via l'agent (plus simple pour du one-shot)
        
        # NOTE: agent.model.generate_content_async attend "contents"
        # On peut aussi utiliser un runner mais il faut lui passer un session_service 
        # (même si on ne veut pas persisté, le Runner l'exige souvent dans les versions récentes du SDK).
        # On va utiliser le session_service passé en paramètre, mais avec un new ID temporaire pour ne pas polluer.
        
        temp_eval_id = f"eval-temp-{session_id}"

        # Création explicite de la session temporaire avant exécution
        try:
            # On essaie de créer la session. Si elle existe, cela peut lever une erreur selon l'implémentation.
            # Dans le doute, on ignore l'erreur de duplication.
            # L'argument app_name est OBLIGATOIRE.
            await session_service.create_session(app_name="sti_app", session_id=temp_eval_id, user_id=user_id)
        except Exception as e:
            # Si erreur (ex: exist déjà), on logue pour debug mais on continue voir si le Runner la trouve
            logger.warning(f"Warning creation session temp: {str(e)}")
            pass

        runner = Runner(
            agent=summative_agent,
            app_name="sti_app", 
            session_service=session_service
        )
        
        # Exécution dans une session temporaire distincte de la session du patient
        async for event in runner.run_async(
            new_message=Content(parts=[Part(text=prompt)]),
            session_id=temp_eval_id,
            user_id=user_id
        ):
             if event.content and event.content.parts:
                 for part in event.content.parts:
                     if part.text:
                         response_text += part.text

        # 4. Parser le JSON
        try:
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            # Parfois le modèle met du texte autour, on essaie de trouver le premier { et le dernier }
            start_idx = clean_text.find("{")
            end_idx = clean_text.rfind("}")
            if start_idx != -1 and end_idx != -1:
                clean_text = clean_text[start_idx:end_idx+1]
                
            bilan_json = json.loads(clean_text)
            return bilan_json
        except json.JSONDecodeError:
            logger.error(f"Erreur parsing JSON bilan sommatif: {response_text}")
            return None

    async def traiter_interaction(self, user_id: str, session_id: str, message_etudiant: str, session_service: DatabaseSessionService):
        print(f"\n🚀 DÉBUT INTERACTION (Session {session_id} - User {user_id})")

        # -------------------------------------------------------------
        # ÉTAPE A : AGENT PATIENT (Génération de la réponse)
        # -------------------------------------------------------------
        print("🏥 A. Le patient réfléchit et répond...")
        # OPTIMISATION : On récupère l'historique pour l'injecter dans le prompt
        # au lieu de forcer l'agent à faire un appel d'outil couteux.
        history_state = await self.get_session_details(session_id, user_id, session_service)
        history_list = history_state.get('history', []) if history_state else []
        
        # Formatage simple de l'historique pour le prompt
        context_str = "\n".join([f"{h['person'].upper()} : {h['message']}" for h in history_list[-10:]]) # On garde les 10 derniers échanges
        
        prompt_with_context = f"""
        HISTORIQUE RÉCENT DE LA CONVERSATION :
        {context_str}
        
        MESSAGE DU DOCTEUR (à traiter maintenant) :
        "{message_etudiant}"
        
        Réponds directement en tant que patient.
        """

        runner_patient = Runner(agent=patient_agent, app_name="sti_app", session_service=session_service)
        
        reponse_patient_text = "Le patient n'a pas pu formuler de réponse."
        # Pour le run du Patient, on utilise la session principale
        async for event in runner_patient.run_async(
            user_id=user_id, 
            session_id=session_id, 
            new_message=Content(parts=[Part(text=prompt_with_context)])
        ):
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
        
        # Calcul du nombre d'échanges pour les triggers d'évaluation
        # Un échange = 1 message docteur + 1 message patient = 2 entrées
        turn_count = len(current_history) // 2
        
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
            # OPTIMISATION EXPERT : On injecte aussi contexte et dernière interaction pour éviter les lectures
            prompt_expert = f"""
            Voici la dernière interaction médicale :
            DOCTEUR: "{message_etudiant}"
            PATIENT: "{reponse_patient_text}"
            
            ANALYSE CETTE INTERACTION MAINTENANT. Évalue la pertinence médicale, détecte les erreurs ou oublis.
            Mets à jour le score et l'analyse dans l'état de la session.
            """
            runner_specific_expert = Runner(agent=specific_expert_agent, app_name="sti_app", session_service=session_service)
            async for _ in runner_specific_expert.run_async(user_id=user_id, session_id=session_id, new_message=Content(parts=[Part(text=prompt_expert)])):
                pass
        else:
            print(f"❌ Erreur de routage pour le domaine '{domaine_nom}'.")

        # -------------------------------------------------------------
        # ÉTAPE E : AGENT TUTEUR
        # -------------------------------------------------------------
        print("🧠 E. Le tuteur décide du feedback...")
        
        # Récupération de l'état APRÈS l'analyse de l'expert
        state_after_expert = await self.get_session_details(session_id, user_id, session_service)
        expert_analysis_content = state_after_expert.get("expert_analysis", "Pas d'analyse disponible")
        student_profile_snapshot = json.dumps(state_after_expert.get("student_profile", {}), ensure_ascii=False)
        
        prompt_tuteur = f"""
        CONTEXTE PÉDAGOGIQUE (Injecté pour économiser les appels outils) :
        
        1. DERNIER ÉCHANGE :
           - Docteur : "{message_etudiant}"
           - Patient : "{reponse_patient_text}"
           
        2. ANALYSE DE L'EXPERT MÉDICAL :
           "{expert_analysis_content}"
           
        3. PROFIL ÉTUDIANT (Snapshot) :
           {student_profile_snapshot}
           
        TA MISSION :
        Génère un feedback court et pédagogique pour l'étudiant en te basant SURTOUT sur l'analyse de l'expert.
        Si l'expert dit que c'est bien : Encourage.
        Si l'expert signale une erreur : Corrige ou guide (Socratique).
        """
        
        runner_tuteur = Runner(agent=tuteur_agent, app_name="sti_app", session_service=session_service)
        # On passe le prompt complet. L'agent n'a plus besoin de ses outils de lecture.
        async for _ in runner_tuteur.run_async(user_id=user_id, session_id=session_id, new_message=Content(parts=[Part(text=prompt_tuteur)])):
            pass

        # -------------------------------------------------------------
        # ÉTAPE F : GÉNÉRATION ÉVALUATION FORMATIVE (OPTIONNEL)
        # -------------------------------------------------------------
        formative_eval_data = None
        # On déclenche tous les 3 tours (6 messages) pour le test
        if turn_count > 0 and turn_count % 3 == 0:
            print(f"📝 F. Génération d'une évaluation formative (Tour {turn_count})...")
            
            # Injection contextuelle pour l'évaluation aussi
            prompt_eval = f"""
            Génère une évaluation formative (QCM JSON) basée sur cet historique :
            {context_str}
            """
            
            runner_eval = Runner(agent=evaluation_agent, app_name="sti_app", session_service=session_service)
            async for eval_event in runner_eval.run_async(user_id=user_id, session_id=session_id, new_message=Content(parts=[Part(text=prompt_eval)])):
                if eval_event.is_final_response() and eval_event.content and eval_event.content.parts:
                    raw_json = eval_event.content.parts[0].text
                    raw_json = raw_json.replace("```json", "").replace("```", "").strip()
                    try:
                        formative_eval_data = json.loads(raw_json)
                        print("   ✅ Évaluation générée avec succès.")
                    except json.JSONDecodeError:
                        print(f"   ❌ Erreur décodage JSON évaluation: {raw_json}")

        # -------------------------------------------------------------
        # ÉTAPE G : CONSTRUCTION DE LA RÉPONSE FINALE
        # -------------------------------------------------------------
        final_session_state = await self.get_session_details(session_id, user_id, session_service)
        if not final_session_state:
            return {"error": "Session introuvable à la fin du traitement."}

        chat_history = final_session_state.get("history", [])
        tutor_feedback = final_session_state.get("tutor_feedback", "Le tuteur n'a pas donné de feedback.")
        
        response_payload = {
            "status": "success",
            "latest_exchange": {"patient": reponse_patient_text, "tutor": tutor_feedback},
            "chat_history": chat_history,
            "internal_reasoning": {
                "expert_analysis": final_session_state.get("expert_analysis", "N/A"), 
                "logs_history": final_session_state.get("internal_logs", [])
            },
            "student_profile": final_session_state.get("student_profile", {})
        }
        
        if formative_eval_data:
            response_payload["formative_evaluation"] = formative_eval_data
            
        return response_payload

# Singleton
orchestrator = TuteurOrchestrator()