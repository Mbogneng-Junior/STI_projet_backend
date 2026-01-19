from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .models import Apprenant, Badge, ProfilEtudiant, NiveauCompetence, QuestionProfiling
from module_expert.models import DomaineMedical
from module_interface.models import SessionApprentissage, EvaluationSommative
from django.db.models import Avg
from .serializers import (
    ApprenantSerializer, 
    BadgeSerializer, 
    ProfilEtudiantSerializer, 
    NiveauCompetenceSerializer,
    QuestionProfilingSerializer,
    ProfilingSubmissionSerializer
)

@extend_schema(tags=['Apprenant - Comptes'])
class ApprenantViewSet(viewsets.ModelViewSet):
    queryset = Apprenant.objects.all()
    serializer_class = ApprenantSerializer

@extend_schema(tags=['Apprenant - Badges'])
class BadgeViewSet(viewsets.ModelViewSet):
    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer

@extend_schema(tags=['Apprenant - Profils'])
class ProfilEtudiantViewSet(viewsets.ModelViewSet):
    queryset = ProfilEtudiant.objects.all()
    serializer_class = ProfilEtudiantSerializer

@extend_schema(tags=['Apprenant - Compétences'])
class NiveauCompetenceViewSet(viewsets.ModelViewSet):
    queryset = NiveauCompetence.objects.all()
    serializer_class = NiveauCompetenceSerializer

@extend_schema(tags=['Apprenant - Profiling'])
class QuestionProfilingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = QuestionProfiling.objects.all()
    serializer_class = QuestionProfilingSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=ProfilingSubmissionSerializer, responses={200: None})
    @action(detail=False, methods=['post'])
    def submit(self, request):
        serializer = ProfilingSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reponses = serializer.validated_data['reponses']
        
        scores = { 'anamnese': 0, 'diagnostic': 0, 'traitement': 0, 'relationnel': 0 }
        max_possible = { 'anamnese': 0, 'diagnostic': 0, 'traitement': 0, 'relationnel': 0 }

        # Fetch relevant questions
        q_ids = [int(k) for k in reponses.keys()]
        questions = QuestionProfiling.objects.in_bulk(q_ids)

        for q_id_str, option_index in reponses.items():
            q_id = int(q_id_str)
            if q_id in questions:
                question = questions[q_id]
                try:
                    selected_option = question.options[option_index]
                    score_value = selected_option.get('score', 0)
                except IndexError:
                    continue 
                
                cat = self._get_category(question.competence)
                scores[cat] += score_value
                max_possible[cat] += 10 

        # Calculate percentages
        final_scores = {}
        for k in scores:
            if max_possible[k] > 0:
                final_scores[k] = (scores[k] / max_possible[k]) * 100
            else:
                final_scores[k] = 0

        # Update Apprenant
        try:
            if not hasattr(request.user, 'apprenant'):
                # Auto-recovery: If user has no apprenant profile (e.g. admin/old user), create it
                if request.user.is_authenticated:
                    apprenant = Apprenant.objects.create(
                        user=request.user,
                        email=request.user.email or f"{request.user.username}@example.com",
                        nom=request.user.username
                    )
                    ProfilEtudiant.objects.create(apprenant=apprenant)
                    # Refresh user instance to see the relation
                    request.user.refresh_from_db()
                else:
                     return Response(
                        {"error": "Utilisateur non lié à un apprenant"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            apprenant = request.user.apprenant
            # Ensure profil exists (legacy check)
            if not hasattr(apprenant, 'profil'):
                 ProfilEtudiant.objects.create(apprenant=apprenant)
                 apprenant.refresh_from_db()
                 
            profil = apprenant.profil
            
            # Update all domains (or default ones) with these base competencies
            domaines = DomaineMedical.objects.all()
                
            for domaine in domaines:
                niveau, created = NiveauCompetence.objects.get_or_create(
                    profil_etudiant=profil,
                    domaine=domaine
                )
                niveau.score_anamnese = final_scores['anamnese']
                niveau.score_diagnostic = final_scores['diagnostic']
                niveau.score_traitement = final_scores['traitement']
                niveau.score_relationnel = final_scores['relationnel']
                niveau.save()
            
            profil.est_profile = True
            profil.save()
            
            return Response({
                "status": "success", 
                "scores": final_scores,
                "message": "Profil mis à jour avec succès"
            })
            
        except AttributeError:
            return Response(
                {"error": "Erreur serveur lors de la mise à jour du profil"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_category(self, competence):
        c = competence.lower()
        if "raisonnement" in c: return 'anamnese'
        if "diagnostic" in c: return 'diagnostic'
        if "ordonnance" in c or "traitement" in c: return 'traitement'
        if "empathie" in c or "relationnel" in c: return 'relationnel'
        return 'anamnese'

@extend_schema(tags=['Apprenant - Dashboard'])
class StudentDashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def full_profile(self, request):
        """
        Retourne toutes les informations du profil de l'apprenant pour la page /profile.
        """
        user = request.user
        try:
            apprenant = user.apprenant
            profil = apprenant.profil
        except AttributeError:
             return Response({"error": "Profil non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        
        # Sérialisation manuelle ou via Serializers existants
        apprenant_data = ApprenantSerializer(apprenant).data
        profil_data = ProfilEtudiantSerializer(profil).data
        
        # Compétences détaillées par domaine
        competences = NiveauCompetence.objects.filter(profil_etudiant=profil)
        competences_data = NiveauCompetenceSerializer(competences, many=True).data

        # Enrichir avec les noms de domaines
        for comp in competences_data:
            try:
                domaine_id = comp['domaine']
                domaine_obj = DomaineMedical.objects.get(id=domaine_id)
                comp['domaine_nom'] = domaine_obj.nom
            except DomaineMedical.DoesNotExist:
                comp['domaine_nom'] = "Inconnu"
        
        return Response({
            "apprenant": apprenant_data,
            "profil": profil_data,
            "competences": competences_data
        })

    @action(detail=False, methods=['get'])
    def stats(self, request):
        user = request.user
        
        # 1. Global Stats (Sessions)
        try:
             apprenant = user.apprenant
        except AttributeError:
             # Fallback for admins or users without 'apprenant' profile
             return Response({
                "global_stats": {"cas_completes": 0, "score_moyen": 0, "temps_etude": 0, "jours_consecutifs": 0},
                "proficiency_data": [],
                "difficulties": []
            })

        sessions = SessionApprentissage.objects.filter(apprenant=apprenant)
        total_sessions = sessions.count()
        
        # Calculate streaks or other metrics 
        streak_days = 5 
        study_time = 4.2
        avg_score = 0
        
        # 2. Proficiency & Difficulties
        proficiency_data = []
        difficulties_list = []

        try:
            if hasattr(apprenant, 'profil'):
                profil = apprenant.profil
                competences = NiveauCompetence.objects.filter(profil_etudiant=profil)
                
                # Aggregate scores
                if competences.exists():
                    scores = competences.aggregate(
                        avg_anamnese=Avg('score_anamnese'),
                        avg_diagnostic=Avg('score_diagnostic'),
                        avg_traitement=Avg('score_traitement'),
                        avg_relationnel=Avg('score_relationnel'),
                        avg_total=Avg('progression_globale')
                    )
                    avg_score = scores['avg_total'] or 0
                    
                    proficiency_data = [
                        {
                            "id": "communication",
                            "label": "Communication",
                            "value": int(scores['avg_relationnel'] or 0),
                            "color": "from-green-500 to-emerald-500",
                            "bgColor": "bg-green-50",
                            "description": "Capacité relationnelle et empathie"
                        },
                         {
                            "id": "anamnese",
                            "label": "Anamnèse", 
                            "value": int(scores['avg_anamnese'] or 0),
                            "color": "from-red-500 to-rose-500",
                            "bgColor": "bg-red-50",
                            "description": "Qualité de l'interrogatoire médical"
                        },
                        {
                            "id": "diagnostic",
                            "label": "Diagnostic",
                            "value": int(scores['avg_diagnostic'] or 0),
                            "color": "from-blue-500 to-indigo-500",
                            "bgColor": "bg-blue-50",
                            "description": "Pertinence des hypothèses"
                        },
                         {
                            "id": "prise_en_charge",
                            "label": "Prise en Charge",
                            "value": int(scores['avg_traitement'] or 0),
                            "color": "from-amber-500 to-orange-500",
                            "bgColor": "bg-amber-50",
                            "description": "Stratégie thérapeutique"
                        }
                    ]

            # Fetch Difficulties from Evaluations
            evaluations = EvaluationSommative.objects.filter(session__apprenant=apprenant).order_by('-date_evaluation')
            all_difficulties = []
            for eval in evaluations:
                if eval.difficultes_identifiees:
                   # Ensure it's a list
                   diffs = eval.difficultes_identifiees if isinstance(eval.difficultes_identifiees, list) else []
                   all_difficulties.extend(diffs)
            
            # Deduplicate and take top 10 unique
            seen = set()
            difficulties_list = [x for x in all_difficulties if not (x in seen or seen.add(x))][:10]

        except Exception as e:
            print(f"Error fetching stats: {e}")
            
        # Default mock if empty
        if not proficiency_data:
            proficiency_data = [
                {"id": "communication", "label": "Communication", "value": 0, "color": "from-green-500 to-emerald-500", "bgColor": "bg-green-50", "description": "Aucune donnée"},
                {"id": "anamnese", "label": "Anamnèse", "value": 0, "color": "from-red-500 to-rose-500", "bgColor": "bg-red-50", "description": "Aucune donnée"},
                {"id": "diagnostic", "label": "Diagnostic", "value": 0, "color": "from-blue-500 to-indigo-500", "bgColor": "bg-blue-50", "description": "Aucune donnée"},
                {"id": "prise_en_charge", "label": "Prise en Charge", "value": 0, "color": "from-amber-500 to-orange-500", "bgColor": "bg-amber-50", "description": "Aucune donnée"}
            ]

        return Response({
            "global_stats": {
                "cas_completes": total_sessions,
                "score_moyen": int(avg_score),
                "temps_etude": study_time,
                "jours_consecutifs": streak_days
            },
            "proficiency_data": proficiency_data,
            "difficulties": difficulties_list
        })

    @action(detail=False, methods=['get'])
    def sessions(self, request):
        """
        Retourne la liste des sessions d'apprentissage passées de l'apprenant.
        """
        user = request.user
        try:
            apprenant = user.apprenant
        except AttributeError:
            return Response([])

        sessions = SessionApprentissage.objects.filter(apprenant=apprenant).select_related('cas_clinique', 'cas_clinique__domaine', 'evaluation').order_by('-date_debut')
        
        data = []
        for session in sessions:
            eval_obj = getattr(session, 'evaluation', None)
            score = eval_obj.score_global if eval_obj else 0
            
            data.append({
                "id": str(session.id),
                "cas_titre": session.cas_clinique.titre if session.cas_clinique else "Session libre",
                "domaine": session.cas_clinique.domaine.nom if (session.cas_clinique and session.cas_clinique.domaine) else "Général",
                "date": session.date_debut,
                "score": score,
                "status": "Terminée" if session.date_fin else "En cours"
            })
            
        return Response(data)
