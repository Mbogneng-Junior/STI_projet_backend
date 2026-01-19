import uuid
from asgiref.sync import sync_to_async
from google.adk.sessions import DatabaseSessionService
# config.adk_session n'est plus nécessaire ici
from module_expert.agent import expert_app 

# Imports Django
from module_apprenant.models import Apprenant, ProfilEtudiant
from module_expert.models import DomaineMedical, CasClinique
from module_interface.models import SessionApprentissage, EvaluationSommative
from django.utils import timezone

class SessionManager:
    # <--- SUPPRESSION DE LA GESTION D'INSTANCE SINGLETON ---
    # _adk_service_instance: DatabaseSessionService = None
    # async def _get_adk_service(self) ...

    async def cloturer_session(self, session_id: str, bilan_data: dict):
        """
        Enregistre le bilan sommatif et met à jour le profil étudiant.
        """
        try:
            session = await SessionApprentissage.objects.select_related('apprenant').aget(id=session_id)
            profil, _ = await ProfilEtudiant.objects.aget_or_create(apprenant=session.apprenant)

            # 1. Création de l'évaluation sommative (ou mise à jour si existe déjà)
            await EvaluationSommative.objects.aupdate_or_create(
                session=session,
                defaults={
                    "score_global": bilan_data.get('score_global', 0),
                    "score_diagnostic": bilan_data.get('score_diagnostic', 0),
                    "score_anamnese": bilan_data.get('score_anamnese', 0),
                    "score_prise_en_charge": bilan_data.get('score_prise_en_charge', 0),
                    "score_communication": bilan_data.get('score_communication', 0),
                    "difficultes_identifiees": bilan_data.get('points_faibles', []),
                    "points_forts": bilan_data.get('points_forts', []),
                    "feedback_global": bilan_data.get('feedback_global', "")
                }
            )

            # 2. Mise à jour de la session
            session.date_fin = timezone.now()
            session.score_session = bilan_data.get('score_global', 0)
            await session.asave()

            # 3. Mise à jour du Profil Etudiant
            # Ajout des difficultés identifiées aux lacunes
            for lacune in bilan_data.get('points_faibles', []):
                if lacune not in profil.lacunes_identifiees:
                    profil.lacunes_identifiees.append(lacune)
            
            # Mise à jour de l'XP (Score Global ajouté au total)
            profil.xp_total += bilan_data.get('score_global', 0)
            # Mise à jour du niveau (logique simplifiée : 1000 XP = 1 Niveau)
            profil.niveau = 1 + (profil.xp_total // 1000)
            
            await profil.asave()
            
            return True, "Session clôturée avec succès."

        except SessionApprentissage.DoesNotExist:
            return False, "Session introuvable."
        except Exception as e:
            return False, f"Erreur lors de la clôture : {str(e)}"

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

            # NOTE: On retourne le message du patient pour l'initialisation du chat frontend
            return session_django, initial_patient_greeting

        except Exception as e:
            return None, f"Erreur démarrage: {str(e)}"

# Instance singleton
session_manager = SessionManager()