import json
import asyncio
from asgiref.sync import sync_to_async
from google.adk.runners import Runner
from google.genai.types import Content, Part
from google.adk.sessions import DatabaseSessionService

# AJOUT DES IMPORTS POUR LA SAUVEGARDE ADK (Event, EventActions)
from google.adk.events import Event, EventActions

# Imports internes des modèles et agents Django
from config.adk_session import db_url # On importe uniquement l'URL de la base de données
from module_expert.agent import expert_app # L'application ADK de l'expert
from module_expert.models import CasClinique, DomaineMedical
from module_apprenant.models import Apprenant, ProfilEtudiant, NiveauCompetence
from module_interface.models import SessionApprentissage, Interaction
from .strategies import StrategieSocratique, StrategieDirecte, StrategieScaffolding

class TuteurIA:
    """
    Orchestrateur principal du système de Tuteur Intelligent (STI).
    Gère le déroulement de la session d'apprentissage, interagit avec l'Agent Expert,
    met à jour le profil de l'apprenant et adapte la stratégie pédagogique.
    """
    
    def __init__(self):
        self.strategies = {
            'SOCRATIQUE': StrategieSocratique(),
            'DIRECT': StrategieDirecte(),
            'SCAFFOLDING': StrategieScaffolding()
        }

    # --- MÉTHODE CRUCIALE POUR GÉRER LE SERVICE DE SESSION ADK ---
    async def _get_session_service(self):
        """
        Crée une nouvelle instance du DatabaseSessionService de l'ADK pour la requête courante.
        Ceci est essentiel pour éviter les conflits de boucles d'événements
        lorsque l'application Django (asynchrone) interagit avec SQLAlchemy/asyncpg.
        """
        # On importe DatabaseSessionService ici pour s'assurer qu'il est créé dans le bon contexte
        from google.adk.sessions import DatabaseSessionService
        return DatabaseSessionService(db_url=db_url)

    async def demarrer_session_async(self, apprenant_email: str, domaine_nom: str):
        """
        Démarre une nouvelle session d'apprentissage pour un apprenant et un domaine donnés.
        Initialise à la fois la session Django et la session ADK associée.
        """
        try:
            # 1. Récupération des objets Django (Apprenant, Domaine, Cas Clinique)
            apprenant = await Apprenant.objects.aget(email=apprenant_email)
            domaine = await DomaineMedical.objects.aget(nom__iexact=domaine_nom)
            
            # Sélection d'un cas clinique pertinent (logique simple ici, pourrait être plus complexe)
            cas = await CasClinique.objects.filter(
                domaine=domaine, 
                statut=CasClinique.StatutCas.PUBLIE
            ).afirst()
            
            if not cas:
                return None, f"Aucun cas clinique 'PUBLIE' disponible pour le domaine '{domaine_nom}'."

            # Création de la session Django (persistance de l'historique métier)
            session_django = await SessionApprentissage.objects.acreate(
                apprenant=apprenant,
                cas_clinique=cas
            )

            # 2. Création de la session ADK (persistance de l'état de l'agent)
            # Le service est créé localement pour cette requête
            adk_session_service = await self._get_session_service()

            await adk_session_service.create_session(
                app_name=expert_app.name, # Nom de l'application ADK de l'expert
                user_id=str(apprenant.id),
                session_id=str(session_django.id), # Lier la session ADK à la session Django
                state={
                    # État initial pour le "scratchpad" de l'agent ADK
                    "etape_courante": "Anamnèse",
                    "erreurs_consecutives": 0,
                    "cas_context": cas.donnees_patient # Charger le contexte du cas clinique
                }
            )

            return session_django, f"Session démarrée sur le cas : {cas.titre}"

        except Apprenant.DoesNotExist:
            return None, f"Apprenant avec l'email '{apprenant_email}' non trouvé."
        except DomaineMedical.DoesNotExist:
            return None, f"Domaine médical '{domaine_nom}' non trouvé."
        except Exception as e:
            # En cas d'erreur inattendue, afficher la trace complète pour le débogage
            import traceback
            traceback.print_exc()
            return None, f"Erreur lors du démarrage de la session: {str(e)}"

    async def analyser_reponse_async(self, session_id: str, reponse_etudiant: str, etape_actuelle: str):
        """
        Analyse la réponse de l'apprenant, consulte l'expert IA, met à jour le profil,
        et génère un feedback pédagogique.
        """
        try:
            # 1. Récupérer la session Django et les objets liés avec `select_related`
            # Ceci permet d'éviter les requêtes synchrones bloquantes sur les Foreign Keys
            session_django = await SessionApprentissage.objects.select_related(
                'cas_clinique__domaine', # Charge le cas clinique et son domaine associé
                'apprenant'              # Charge l'apprenant associé
            ).aget(id=session_id)
            
            # Accès direct aux objets déjà chargés
            cas = session_django.cas_clinique
            apprenant = session_django.apprenant
            domaine = cas.domaine  
            
            # Récupérer le profil de l'apprenant pour la mise à jour XP/compétences
            profil = await ProfilEtudiant.objects.aget(apprenant=apprenant)

            # 2. Préparer le Runner ADK avec un service de session LOCAL
            adk_session_service = await self._get_session_service()

            runner = Runner(
                agent=expert_app.root_agent,
                app_name=expert_app.name,
                session_service=adk_session_service # Utiliser l'instance locale du service
            )

            # 3. Construire le prompt pour l'Agent Expert
            # On demande un format JSON spécifique pour faciliter le parsing
            prompt_content = (
                f"CONTEXTE DU CAS: '{cas.titre}'.\n"
                f"DONNÉES PATIENT: {cas.donnees_patient}.\n"
                f"HISTORIQUE MÉDICAL: {cas.historique_medical}.\n"
                f"SOLUTION EXPERTE ATTENDUE: '{cas.solution_experte}'.\n"
                f"L'ÉTUDIANT PROPOSE (étape '{etape_actuelle}'): '{reponse_etudiant}'.\n\n"
                "TACHE: Évalue la réponse de l'étudiant. Est-elle correcte médicalement par rapport à la solution experte ?\n"
                "Si non, quelles sont les erreurs principales détectées ?\n"
                "FORMAT DE SORTIE ATTENDU (JSON uniquement): "
                "{ \"correct\": boolean, \"raison\": \"string\", \"erreurs_detectees\": [\"string\"] }"
            )
            
            user_message = Content(parts=[Part(text=prompt_content)])

            # 4. Exécuter l'Agent Expert via le Runner ADK
            expert_response_text = ""
            async for event in runner.run_async(
                user_id=str(apprenant.id),
                session_id=str(session_id),
                new_message=user_message
            ):
                if event.is_final_response() and event.content:
                    expert_response_text = event.content.parts[0].text

            # 5. Parsing de la réponse JSON de l'Expert
            try:
                # Nettoyage pour retirer les blocs de code Markdown (```json...```)
                clean_json = expert_response_text.replace('```json', '').replace('```', '').strip()
                resultat_expert = json.loads(clean_json)
                est_correct = resultat_expert.get('correct', False)
                raison_expert = resultat_expert.get('raison', 'Analyse non disponible.')
                erreurs_expert = resultat_expert.get('erreurs_detectees', [])
            except json.JSONDecodeError:
                # Fallback si l'IA ne répond pas en JSON valide
                est_correct = False
                raison_expert = "L'expert n'a pas pu évaluer la réponse (format invalide)."
                erreurs_expert = [expert_response_text] # Mettre la réponse brute comme erreur
            except Exception as e:
                est_correct = False
                raison_expert = f"Erreur interne lors du traitement de la réponse de l'expert: {str(e)}"
                erreurs_expert = []

            # 6. Mise à jour de l'état de la session ADK (persistance des erreurs consécutives)
            # Récupérer l'état actuel de la session ADK
            session_adk = await adk_session_service.get_session(
                app_name=expert_app.name, 
                user_id=str(apprenant.id), 
                session_id=str(session_id)
            )
            
            current_errors = session_adk.state.get("erreurs_consecutives", 0)
            
            if not est_correct:
                new_errors = current_errors + 1
            else:
                new_errors = 0 # Réinitialiser les erreurs si la réponse est correcte

            # Créer un événement ADK pour persister la mise à jour de l'état dans la base de données
            state_update_event = Event(
                author="system", # L'auteur de cet événement est le système de tutorat
                actions=EventActions(state_delta={"erreurs_consecutives": new_errors})
            )
            await adk_session_service.append_event(session_adk, state_update_event)

            # 7. Mise à jour du profil de l'apprenant dans Django (XP, Compétences, Lacunes)
            await self._update_competence_django(profil, domaine, est_correct, erreurs_expert) 
            
            # 8. Choix de la stratégie pédagogique en fonction du résultat et des erreurs passées
            strategie = self._choisir_strategie(est_correct, new_errors)
            
            if est_correct:
                feedback = f"Bien joué ! {raison_expert}"
            else:
                # Utilise la stratégie choisie pour générer un indice
                feedback = strategie.generer_indice(cas.donnees_patient, etape_actuelle)

            # 9. Enregistrement de l'interaction dans la base de données Django
            await Interaction.objects.acreate(
                session=session_django,
                question_contenu=f"Étape: {etape_actuelle}",
                reponse_contenu=reponse_etudiant,
                reponse_est_valide=est_correct,
                feedback_contenu=feedback,
                feedback_type=strategie.style_feedback()
            )

            # Retourner le résultat à l'interface utilisateur
            return {
                "valide": est_correct,
                "feedback": feedback,
                "expert_raw": raison_expert
            }

        except SessionApprentissage.DoesNotExist:
            return {"error": f"Session Django avec l'ID '{session_id}' introuvable."}
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": f"Erreur interne du tuteur: {str(e)}"}

    @sync_to_async
    def _update_competence_django(self, profil: ProfilEtudiant, domaine: DomaineMedical, est_correct: bool, erreurs_expert: list):
        """
        Met à jour les scores de compétences (NiveauCompetence) et le profil global (ProfilEtudiant)
        de l'apprenant. Cette fonction s'exécute de manière synchrone.
        """
        # Mise à jour du NiveauCompetence pour le domaine spécifique
        comp, _ = NiveauCompetence.objects.get_or_create(
            profil_etudiant=profil,
            domaine=domaine,
            defaults={'niveau_actuel': 'DEBUTANT', 'score_diagnostic': 0.0, 'score_raisonnement': 0.0}
        )
        
        if est_correct:
            comp.score_diagnostic += 5
        else:
            comp.score_diagnostic = max(0, comp.score_diagnostic - 2) # Empêche le score de devenir négatif
        
        # Logique simplifiée de progression de niveau
        if comp.score_diagnostic > 80:
            comp.niveau_actuel = 'EXPERT'
        elif comp.score_diagnostic > 50:
            comp.niveau_actuel = 'AVANCE'
        elif comp.score_diagnostic > 20:
            comp.niveau_actuel = 'INTERMEDIAIRE'
        else:
            comp.niveau_actuel = 'DEBUTANT'
             
        comp.save()

        # Mise à jour du ProfilEtudiant (XP total et lacunes)
        if est_correct:
            profil.xp_total += 10 # Gagner plus d'XP pour une bonne réponse
        
        # Enregistrer les lacunes si la réponse est incorrecte et que l'expert a identifié des erreurs
        if not est_correct and erreurs_expert:
            current_lacunes_list = json.loads(profil.lacunes_identifiees or "[]")
            for erreur in erreurs_expert:
                if erreur not in current_lacunes_list: # Évite les doublons
                    current_lacunes_list.append(erreur)
            profil.lacunes_identifiees = json.dumps(current_lacunes_list)
        elif est_correct:
            # Si l'apprenant réussit, on peut envisager de "résoudre" des lacunes
            # Pour l'instant, on ne fait rien de sophistiqué ici, les lacunes persistent jusqu'à une gestion explicite
            pass 

        profil.save() # Sauvegarde toutes les modifications du profil

    def _choisir_strategie(self, est_correct: bool, nb_erreurs_consecutives: int):
        """
        Choisit la stratégie pédagogique (Socratique, Directe, Scaffolding)
        en fonction du résultat de la dernière réponse et du nombre d'erreurs consécutives.
        """
        if est_correct:
            return self.strategies['SOCRATIQUE'] # Si correct, on encourage à la réflexion
        
        # Si plusieurs erreurs, on devient plus directif
        if nb_erreurs_consecutives >= 2:
            return self.strategies['DIRECT'] 
        else:
            return self.strategies['SCAFFOLDING'] # Aide progressive

# Instance unique du TuteurIA, car elle est stateless (l'état est dans ADK Session et Django DB)
tuteur_service = TuteurIA()