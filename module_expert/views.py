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
    permission_classes = [AllowAny]

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
        # On commence par récupérer tous les cas
        queryset = CasClinique.objects.all().select_related('domaine')
        
        # 1. Filtre par domaine de l'expert (Si authentifié)
        # Note: Enlève le commentaire si tu veux restreindre l'expert à sa spécialité
        # if self.request.user.is_authenticated and hasattr(self.request.user, 'experthumain'):
        #    queryset = queryset.filter(domaine=self.request.user.experthumain.domaine_expertise)

        # 2. Récupération des paramètres de l'URL
        status_param = self.request.query_params.get('status')
        keyword = self.request.query_params.get('keyword')
        pathologie = self.request.query_params.get('pathologie')
        specialite = self.request.query_params.get('specialite') # Nouveau
        niveau = self.request.query_params.get('niveau')
        gender = self.request.query_params.get('gender')
        min_age = self.request.query_params.get('min_age')
        max_age = self.request.query_params.get('max_age')
        symptom = self.request.query_params.get('symptom')

        # 3. Application des filtres simples
        if status_param:
            queryset = queryset.filter(statut=status_param)
        if pathologie:
            queryset = queryset.filter(pathologie__icontains=pathologie)
        if specialite and specialite != 'all':
            queryset = queryset.filter(domaine__nom__icontains=specialite)
        if niveau:
            queryset = queryset.filter(difficulte=niveau.upper())
        if keyword:
            queryset = queryset.filter(Q(titre__icontains=keyword) | Q(pathologie__icontains=keyword))
        if gender:
             queryset = queryset.filter(donnees_patient__sexe=gender)

        # 4. Filtres complexes sur JSONField (Âge et Symptômes)
        # On utilise une liste d'IDs pour filtrer car les requêtes sur JSON list sont complexes
        if min_age or max_age or symptom:
            filtered_ids = []
            for case in queryset:
                keep = True
                
                # Vérification âge
                age = case.donnees_patient.get('age')
                if age is not None:
                    if min_age and int(age) < int(min_age): keep = False
                    if max_age and int(age) > int(max_age): keep = False
                
                # Vérification symptômes
                if symptom:
                    symptomes_du_cas = case.symptomes or []
                    # On cherche si au moins un symptôme correspond
                    found_symptom = False
                    for s in symptomes_du_cas:
                        nom_s = s.get('nom', '').lower() if isinstance(s, dict) else str(s).lower()
                        if symptom.lower() in nom_s:
                            found_symptom = True
                            break
                    if not found_symptom: keep = False
                
                if keep:
                    filtered_ids.append(case.id)
            
            # On applique le filtre final sur le queryset
            queryset = queryset.filter(id__in=filtered_ids)

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
