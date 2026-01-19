import uuid
from asgiref.sync import sync_to_async
from google.adk.sessions import DatabaseSessionService
# config.adk_session n'est plus nécessaire ici
from module_expert.agent import expert_app 

# Imports Django
from module_apprenant.models import Apprenant, ProfilEtudiant, NiveauCompetence
from module_expert.models import DomaineMedical, CasClinique
from module_interface.models import SessionApprentissage, EvaluationSommative
from django.utils import timezone
from django.db.models import Avg

class SessionManager:
    # <--- SUPPRESSION DE LA GESTION D'INSTANCE SINGLETON ---
    # _adk_service_instance: DatabaseSessionService = None
    # async def _get_adk_service(self) ...

    async def cloturer_session(self, session_id: str, bilan_data: dict):
        """
        Enregistre le bilan sommatif et met à jour le profil étudiant.
        """
        try:
            # On charge la session avec le cas et le domaine pour la mise à jour des compétences
            session = await SessionApprentissage.objects.select_related(
                'apprenant', 
                'cas_clinique', 
                'cas_clinique__domaine'
            ).aget(id=session_id)
            
            profil, _ = await ProfilEtudiant.objects.aget_or_create(apprenant=session.apprenant)

            # 1. Création de l'évaluation sommative
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

            # 3. Mise à jour du NiveauCompetence spécifique au Domaine
            if session.cas_clinique and session.cas_clinique.domaine:
                domaine = session.cas_clinique.domaine
                niveau_comp, _ = await NiveauCompetence.objects.aget_or_create(
                    profil_etudiant=profil,
                    domaine=domaine
                )
                
                # Mise à jour avec les scores de cette session
                # Note: On pourrait faire une moyenne avec l'ancien score, mais ici on prend le dernier éval pour l'instant
                # ou on considère que l'IA a donné la note du niveau actuel.
                niveau_comp.score_anamnese = bilan_data.get('score_anamnese', 0)
                niveau_comp.score_diagnostic = bilan_data.get('score_diagnostic', 0)
                niveau_comp.score_traitement = bilan_data.get('score_prise_en_charge', 0)
                niveau_comp.score_relationnel = bilan_data.get('score_communication', 0)
                niveau_comp.progression_globale = bilan_data.get('score_global', 0)
                
                await niveau_comp.asave()

            # 4. Recalcul des Scores Globaux du Profil (Moyenne des domaines)
            # On utilise sync_to_async pour l'aggregation qui est bloquante
            def calculer_moyennes():
                avgs = NiveauCompetence.objects.filter(profil_etudiant=profil).aggregate(
                    avg_ana=Avg('score_anamnese'),
                    avg_diag=Avg('score_diagnostic'),
                    avg_trait=Avg('score_traitement'),
                    avg_rel=Avg('score_relationnel')
                )
                return avgs

            moyennes = await sync_to_async(calculer_moyennes)()
            
            # Mise à jour si on a des valeurs (sinon garde l'existant)
            if moyennes['avg_ana'] is not None:
                profil.global_anamnese = moyennes['avg_ana']
                profil.global_diagnostic = moyennes['avg_diag']
                profil.global_traitement = moyennes['avg_trait']
                profil.global_relationnel = moyennes['avg_rel']

            # 5. Mise à jour XP et Lacunes
            # Ajout des difficultés
            current_lacunes = profil.lacunes_identifiees or []
            new_lacunes = bilan_data.get('points_faibles', [])
            
            # Simple merge sans duplication
            for l in new_lacunes:
                if l not in current_lacunes:
                    current_lacunes.append(l)
            profil.lacunes_identifiees = current_lacunes

            profil.xp_total += int(bilan_data.get('score_global', 0))
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