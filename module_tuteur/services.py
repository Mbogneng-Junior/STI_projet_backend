import uuid
from asgiref.sync import sync_to_async
from google.adk.sessions import DatabaseSessionService
# config.adk_session n'est plus nécessaire ici
from module_expert.agent import expert_app 

# Imports Django
from module_apprenant.models import Apprenant, ProfilEtudiant
from module_expert.models import DomaineMedical, CasClinique
from module_interface.models import SessionApprentissage

class SessionManager:
    # <--- SUPPRESSION DE LA GESTION D'INSTANCE SINGLETON ---
    # _adk_service_instance: DatabaseSessionService = None
    # async def _get_adk_service(self) ...

    # <--- MODIFICATION DE LA SIGNATURE DE LA MÉTHODE ---
    async def demarrer_session(self, email_apprenant: str, domaine_nom: str, session_service: DatabaseSessionService):
        try:
            # 1. Vérifications Django (Apprenant & Domaine)
            try:
                apprenant = await Apprenant.objects.aget(email=email_apprenant)
                profil, _ = await ProfilEtudiant.objects.aget_or_create(apprenant=apprenant)
                domaine = await DomaineMedical.objects.aget(nom__iexact=domaine_nom)
            except (Apprenant.DoesNotExist, DomaineMedical.DoesNotExist):
                return None, "Apprenant ou Domaine introuvable."

            # 2. Sélection d'un cas clinique
            cas = await CasClinique.objects.filter(
                domaine=domaine, 
                statut=CasClinique.StatutCas.PUBLIE
            ).afirst()
            
            if not cas:
                return None, f"Aucun cas disponible pour {domaine_nom}."

            # 3. Création Session Django (Métier)
            session_django = await SessionApprentissage.objects.acreate(
                apprenant=apprenant,
                cas_clinique=cas
            )
            
            # 4. Création Session ADK (Mémoire Agents)
            # adk_service = await self._get_adk_service() # <--- SUPPRIMÉ
            initial_patient_greeting = "Bonjour Docteur, je ne me sens pas très bien."
            
            # On utilise l'instance passée en argument
            await session_service.create_session(
                app_name="sti_app", 
                user_id=str(apprenant.id),
                session_id=str(session_django.id),
                state={
                    "domaine": domaine.nom,       
                    "cas_context": cas.donnees_patient,
                    "history": [{"id": 1, "person": "patient", "message": initial_patient_greeting}],                
                    "user_id": str(apprenant.id),
                    "user:email": apprenant.email,
                    "student_profile": {
                        "score_global": profil.xp_total,
                        "competences": {},
                        "feedbacks": [],
                        "lacunes": profil.lacunes_identifiees
                    },
                    "internal_logs": [],
                    "temp:expert_analysis": "Aucune analyse pour le moment."
                }
            )

            return session_django, f"Session démarrée sur le cas : {cas.titre}"

        except Exception as e:
            return None, f"Erreur démarrage: {str(e)}"

# Instance singleton
session_manager = SessionManager()