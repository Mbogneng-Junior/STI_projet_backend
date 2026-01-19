from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Count, Avg, F
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import DomaineMedical, ExpertHumain, ExpertIA, CasClinique, EtapeClinique
from .serializers import (
    DomaineMedicalSerializer,
    ExpertHumainSerializer,
    ExpertIASerializer,
    CasCliniqueSerializer,
    EtapeCliniqueSerializer
)
import json

@extend_schema(tags=['Expert - Domaines Médicaux'])
class DomaineMedicalViewSet(viewsets.ModelViewSet):
    queryset = DomaineMedical.objects.all()
    serializer_class = DomaineMedicalSerializer
    permission_classes = [AllowAny]

@extend_schema(tags=['Expert - Experts Humains'])
class ExpertHumainViewSet(viewsets.ModelViewSet):
    queryset = ExpertHumain.objects.all()
    serializer_class = ExpertHumainSerializer

@extend_schema(tags=['Expert - Experts IA'])
class ExpertIAViewSet(viewsets.ModelViewSet):
    queryset = ExpertIA.objects.all()
    serializer_class = ExpertIASerializer

@extend_schema(tags=['Expert - Cas Cliniques'])
class CasCliniqueViewSet(viewsets.ModelViewSet):
    queryset = CasClinique.objects.all()
    serializer_class = CasCliniqueSerializer
    lookup_field = 'id_unique'
    permission_classes = [AllowAny]
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by Expert's domain if applicable
        #if self.request.user.is_authenticated and hasattr(self.request.user, 'experthumain'):
         #   queryset = queryset.filter(domaine=self.request.user.experthumain.domaine_expertise)

        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(statut=status)
        
        # Add filtering logic here to match frontend filters
        # keyword, min_age, max_age, gender, profession, symptom, pathologie, niveau, limit
        keyword = self.request.query_params.get('keyword')
        if keyword:
            queryset = queryset.filter(titre__icontains=keyword) | queryset.filter(pathologie__icontains=keyword)

        pathologie = self.request.query_params.get('pathologie')
        if pathologie:
            queryset = queryset.filter(pathologie__icontains=pathologie)

        niveau = self.request.query_params.get('niveau')
        if niveau:
            queryset = queryset.filter(difficulte=niveau)

        # JSON field filtering (PostgreSQL specific usually, but works in Django for JSONField)
        gender = self.request.query_params.get('gender')
        if gender:
             queryset = queryset.filter(donnees_patient__sexe=gender)

        return queryset

    @action(detail=False, methods=['get'])
    def stats(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        total_cas = queryset.count()
        
        # Par Pathologie
        par_pathologie = {}
        for item in queryset.values('pathologie').annotate(count=Count('id')):
            if item['pathologie']:
                par_pathologie[item['pathologie']] = item['count']

        # Par Niveau
        par_niveau = {}
        for item in queryset.values('difficulte').annotate(count=Count('id')):
            par_niveau[item['difficulte']] = item['count']

        # Par Status
        par_status = {}
        for item in queryset.values('statut').annotate(count=Count('id')):
            par_status[item['statut']] = item['count']

        # Par Sexe (JSON Field)
        par_sexe = {}
        males = queryset.filter(donnees_patient__sexe='M').count()
        females = queryset.filter(donnees_patient__sexe='F').count()
        par_sexe['M'] = males
        par_sexe['F'] = females

        # Age moyen
        cases_with_age = queryset.exclude(donnees_patient__age=None)
        total_age = 0
        count_age = 0
        for c in cases_with_age:
            age = c.donnees_patient.get('age')
            if age and isinstance(age, (int, float)):
                total_age += age
                count_age += 1
        
        age_moyen = total_age / count_age if count_age > 0 else 0

        data = {
            "total_cas": total_cas,
            "par_pathologie": par_pathologie,
            "par_niveau": par_niveau,
            "par_status": par_status,
            "par_sexe": par_sexe,
            "age_moyen": round(age_moyen, 1)
        }
        return Response(data)

    @action(detail=False, methods=['get'])
    def filters(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        # Extract distinct values for filters
        pathologies = queryset.values_list('pathologie', flat=True).distinct().order_by('pathologie')
        niveaux = queryset.values_list('difficulte', flat=True).distinct()
        statuses = queryset.values_list('statut', flat=True).distinct()

        # From JSON fields
        all_patients = queryset.values_list('donnees_patient', flat=True)
        genders = set()
        professions = set()
        for p in all_patients:
            if p.get('sexe'): genders.add(p.get('sexe'))
            if p.get('profession'): professions.add(p.get('profession'))

        all_symptoms = queryset.values_list('symptomes', flat=True)
        symptoms_set = set()
        for s_list in all_symptoms:
            if not s_list: continue
            for s in s_list:
                if isinstance(s, dict) and s.get('nom'):
                    symptoms_set.add(s.get('nom'))
                elif isinstance(s, str):
                     symptoms_set.add(s)

        data = {
            "genders": list(genders),
            "professions": sorted(list(professions)),
            "symptoms": sorted(list(symptoms_set)),
            "pathologies": list(pathologies),
            "niveaux": list(niveaux),
            "statuses": list(statuses)
        }
        return Response(data)

    # ========== ACTIONS DE VALIDATION (selon PDF) ==========

    @extend_schema(
        description="Valide un cas clinique (statut -> PUBLIE)",
        request={'application/json': {'type': 'object', 'properties': {
            'commentaire': {'type': 'string', 'description': 'Commentaire optionnel'}
        }}}
    )
    @action(detail=True, methods=['post'])
    def valider(self, request, id_unique=None):
        """Valide un cas clinique et le publie"""
        cas = self.get_object()
        commentaire = request.data.get('commentaire', '')

        cas.statut = CasClinique.StatutCas.PUBLIE
        cas.date_validation = timezone.now()
        cas.commentaire_expert = commentaire

        # Associer l'expert si connecté
        if hasattr(request.user, 'experthumain'):
            cas.expert_responsable = request.user.experthumain

        cas.save()

        return Response({
            'status': 'success',
            'message': 'Cas clinique validé et publié',
            'id': cas.id_unique,
            'nouveau_statut': cas.statut
        })

    @extend_schema(
        description="Rejette un cas clinique avec formulaire (selon PDF: parties concernées, raison, email)",
        request={'application/json': {'type': 'object', 'properties': {
            'raison': {'type': 'string', 'description': 'Raison du rejet'},
            'parties_concernees': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Parties du cas concernées'},
            'email_notification': {'type': 'string', 'description': 'Email pour notification (Fultang)'},
            'commentaire': {'type': 'string', 'description': 'Commentaire additionnel'}
        }, 'required': ['raison']}}
    )
    @action(detail=True, methods=['post'])
    def rejeter(self, request, id_unique=None):
        """Rejette un cas clinique avec formulaire détaillé"""
        cas = self.get_object()

        raison = request.data.get('raison', '')
        parties = request.data.get('parties_concernees', [])
        email = request.data.get('email_notification', '')
        commentaire = request.data.get('commentaire', '')

        if not raison:
            return Response(
                {'error': 'La raison du rejet est obligatoire'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cas.statut = CasClinique.StatutCas.REJETE
        cas.raison_rejet = raison
        cas.parties_concernees = parties
        cas.email_notification_rejet = email
        cas.commentaire_expert = commentaire
        cas.date_validation = timezone.now()

        # Associer l'expert si connecté
        if hasattr(request.user, 'experthumain'):
            cas.expert_responsable = request.user.experthumain

        cas.save()

        # Envoi d'email si fourni (selon PDF: implémenter l'envoi)
        if email:
            try:
                expert_nom = request.user.experthumain.nom if hasattr(request.user, 'experthumain') else 'Expert'
                send_mail(
                    subject=f'Rejet du cas clinique {cas.id_unique}',
                    message=f"""
Bonjour,

Le cas clinique {cas.id_unique} a été rejeté par {expert_nom}.

Raison du rejet: {raison}

Parties concernées: {', '.join(parties) if parties else 'Non spécifié'}

Commentaire: {commentaire}

Cordialement,
Système STI
                    """,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@sti.local'),
                    recipient_list=[email],
                    fail_silently=True
                )
            except Exception as e:
                # Log l'erreur mais ne bloque pas le rejet
                print(f"Erreur envoi email: {e}")

        return Response({
            'status': 'success',
            'message': 'Cas clinique rejeté',
            'id': cas.id_unique,
            'nouveau_statut': cas.statut,
            'email_envoye': bool(email)
        })

    @extend_schema(
        description="Met un cas clinique en cours de traitement par l'expert",
        request={'application/json': {'type': 'object', 'properties': {
            'commentaire': {'type': 'string', 'description': 'Commentaire optionnel'}
        }}}
    )
    @action(detail=True, methods=['post'], url_path='en-cours')
    def mettre_en_cours(self, request, id_unique=None):
        """Met un cas en cours de traitement par l'expert"""
        cas = self.get_object()
        commentaire = request.data.get('commentaire', '')

        cas.statut = CasClinique.StatutCas.EN_COURS
        cas.date_mise_en_cours = timezone.now()
        cas.commentaire_expert = commentaire

        # Associer l'expert si connecté
        if hasattr(request.user, 'experthumain'):
            cas.expert_responsable = request.user.experthumain

        cas.save()

        return Response({
            'status': 'success',
            'message': 'Cas clinique mis en cours',
            'id': cas.id_unique,
            'nouveau_statut': cas.statut
        })

@extend_schema(tags=['Expert - Étapes Cliniques'])
class EtapeCliniqueViewSet(viewsets.ModelViewSet):
    queryset = EtapeClinique.objects.all()
    serializer_class = EtapeCliniqueSerializer
