"""
API Views pour l'extraction et l'export des cas cliniques
Projet STI 5GI
"""

import csv
import json
from io import StringIO
from datetime import datetime

from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Avg, Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter

from module_expert.models import CasClinique, DomaineMedical
from .services.importer import ClinicalCaseImporter
from .services.transformer import ClinicalCaseTransformer


@extend_schema(
    tags=['Extraction'],
    description='Rafraîchit les cas cliniques en générant de nouveaux cas',
    parameters=[
        OpenApiParameter(name='count', type=int, description='Nombre de cas à générer'),
        OpenApiParameter(name='replace', type=bool, description='Remplacer les cas existants'),
    ]
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def refresh_cases(request):
    """
    Génère et importe de nouveaux cas cliniques.
    Réservé aux administrateurs.
    """
    count = request.data.get('count', None)
    replace = request.data.get('replace', False)

    try:
        importer = ClinicalCaseImporter()
        created, skipped, errors = importer.import_cases(
            count=int(count) if count else None,
            replace_existing=replace
        )

        return Response({
            'status': 'success',
            'message': f'{created} cas générés/mis à jour.',
            'created': created,
            'skipped': skipped,
            'errors': errors[:5] if errors else [],
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Extraction'],
    description='Exporte les cas cliniques filtrés au format JSON',
    parameters=[
        OpenApiParameter(name='pathologie', type=str, description='Filtrer par pathologie'),
        OpenApiParameter(name='specialite', type=str, description='Filtrer par spécialité'),
        OpenApiParameter(name='niveau', type=str, description='Filtrer par niveau (DEBUTANT, INTERMEDIAIRE, EXPERT)'),
        OpenApiParameter(name='status', type=str, description='Filtrer par statut'),
        OpenApiParameter(name='min_age', type=int, description='Âge minimum'),
        OpenApiParameter(name='max_age', type=int, description='Âge maximum'),
        OpenApiParameter(name='symptom', type=str, description='Filtrer par symptôme'),
    ]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_json(request):
    """
    Exporte les cas cliniques filtrés au format JSON.
    """
    queryset = _apply_filters(request)

    # Conversion en liste de dictionnaires
    cases_data = []
    for case in queryset:
        cases_data.append({
            'id_unique': case.id_unique,
            'titre': case.titre,
            'statut': case.statut,
            'difficulte': case.difficulte,
            'pathologie': case.pathologie,
            'specialite': case.domaine.nom if case.domaine else None,
            'donnees_patient': case.donnees_patient,
            'motif_consultation': case.motif_consultation,
            'mode_de_vie': case.mode_de_vie,
            'antecedents_medicaux': case.antecedents_medicaux,
            'symptomes': case.symptomes,
            'diagnostics_physiques': case.diagnostics_physiques,
            'examens_complementaires': case.examens_complementaires,
            'diagnostic_final': case.diagnostic_final,
            'traitement': case.traitement,
            'objectifs_pedagogiques': case.objectifs_pedagogiques,
            'indices_cliniques': case.indices_cliniques,
            'erreurs_courantes': case.erreurs_courantes,
        })

    # Réponse JSON téléchargeable
    response = HttpResponse(
        json.dumps(cases_data, indent=2, ensure_ascii=False),
        content_type='application/json'
    )
    filename = f"cas_cliniques_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


@extend_schema(
    tags=['Extraction'],
    description='Exporte les cas cliniques filtrés au format CSV',
    parameters=[
        OpenApiParameter(name='pathologie', type=str, description='Filtrer par pathologie'),
        OpenApiParameter(name='specialite', type=str, description='Filtrer par spécialité'),
        OpenApiParameter(name='niveau', type=str, description='Filtrer par niveau (DEBUTANT, INTERMEDIAIRE, EXPERT)'),
        OpenApiParameter(name='status', type=str, description='Filtrer par statut'),
        OpenApiParameter(name='min_age', type=int, description='Âge minimum'),
        OpenApiParameter(name='max_age', type=int, description='Âge maximum'),
        OpenApiParameter(name='symptom', type=str, description='Filtrer par symptôme'),
    ]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_csv(request):
    """
    Exporte les cas cliniques filtrés au format CSV.
    """
    queryset = _apply_filters(request)

    # Création du CSV
    output = StringIO()
    writer = csv.writer(output)

    # En-têtes
    headers = [
        'ID', 'Titre', 'Statut', 'Difficulté', 'Pathologie', 'Spécialité',
        'Âge', 'Sexe', 'Profession', 'Région',
        'Motif Consultation', 'Diagnostic Final',
        'Symptômes', 'Examens'
    ]
    writer.writerow(headers)

    # Données
    for case in queryset:
        patient = case.donnees_patient or {}
        symptomes = ', '.join([s.get('nom', '') for s in (case.symptomes or [])])
        examens = ', '.join([e.get('nom', '') for e in (case.examens_complementaires or [])])

        row = [
            case.id_unique,
            case.titre,
            case.statut,
            case.difficulte,
            case.pathologie,
            case.domaine.nom if case.domaine else '',
            patient.get('age', ''),
            patient.get('sexe', ''),
            patient.get('profession', ''),
            patient.get('region_origine', ''),
            case.motif_consultation,
            case.diagnostic_final,
            symptomes,
            examens
        ]
        writer.writerow(row)

    # Réponse CSV
    output.seek(0)
    response = HttpResponse(output.read(), content_type='text/csv')
    filename = f"cas_cliniques_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


@extend_schema(
    tags=['Extraction'],
    description='Retourne les filtres disponibles pour l\'export'
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_export_filters(request):
    """
    Retourne les valeurs disponibles pour les filtres d'export.
    """
    # Spécialités (domaines)
    specialites = list(DomaineMedical.objects.values_list('nom', flat=True).distinct())

    # Pathologies
    pathologies = list(CasClinique.objects.values_list('pathologie', flat=True).distinct())
    pathologies = [p for p in pathologies if p]  # Filtrer les valeurs vides

    # Niveaux
    niveaux = ['DEBUTANT', 'INTERMEDIAIRE', 'AVANCE', 'EXPERT']

    # Statuts
    statuts = ['BROUILLON_IA', 'EN_REVISION', 'PUBLIE', 'REJETE', 'ARCHIVE']

    # Symptômes uniques
    symptoms_set = set()
    for case in CasClinique.objects.all():
        for symptom in (case.symptomes or []):
            if isinstance(symptom, dict) and symptom.get('nom'):
                symptoms_set.add(symptom['nom'])

    return Response({
        'specialites': sorted(specialites),
        'pathologies': sorted(pathologies),
        'niveaux': niveaux,
        'statuts': statuts,
        'symptomes': sorted(list(symptoms_set))
    })


@extend_schema(
    tags=['Extraction'],
    description='Retourne les statistiques des cas cliniques'
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_extraction_stats(request):
    """
    Retourne des statistiques sur les cas cliniques.
    """
    total = CasClinique.objects.count()

    # Par statut
    by_status = {}
    for item in CasClinique.objects.values('statut').annotate(count=Count('id')):
        by_status[item['statut']] = item['count']

    # Par spécialité
    by_specialite = {}
    for item in CasClinique.objects.values('domaine__nom').annotate(count=Count('id')):
        nom = item['domaine__nom'] or 'Non défini'
        by_specialite[nom] = item['count']

    # Par difficulté
    by_difficulty = {}
    for item in CasClinique.objects.values('difficulte').annotate(count=Count('id')):
        by_difficulty[item['difficulte']] = item['count']

    # Par pathologie
    by_pathologie = {}
    for item in CasClinique.objects.values('pathologie').annotate(count=Count('id')):
        if item['pathologie']:
            by_pathologie[item['pathologie']] = item['count']

    # Statistiques démographiques
    ages = []
    sexes = {'M': 0, 'F': 0}
    for case in CasClinique.objects.all():
        patient = case.donnees_patient or {}
        if patient.get('age'):
            ages.append(patient['age'])
        sexe = patient.get('sexe')
        if sexe in sexes:
            sexes[sexe] += 1

    return Response({
        'total_cas': total,
        'par_statut': by_status,
        'par_specialite': by_specialite,
        'par_difficulte': by_difficulty,
        'par_pathologie': by_pathologie,
        'par_sexe': sexes,
        'age_moyen': sum(ages) / len(ages) if ages else 0,
        'timestamp': datetime.now().isoformat()
    })


def _apply_filters(request):
    """
    Applique les filtres à partir des paramètres de requête.
    """
    queryset = CasClinique.objects.select_related('domaine').all()

    # Filtre par pathologie
    pathologie = request.query_params.get('pathologie')
    if pathologie:
        queryset = queryset.filter(pathologie__icontains=pathologie)

    # Filtre par spécialité
    specialite = request.query_params.get('specialite')
    if specialite:
        queryset = queryset.filter(domaine__nom__icontains=specialite)

    # Filtre par niveau/difficulté
    niveau = request.query_params.get('niveau')
    if niveau:
        queryset = queryset.filter(difficulte=niveau.upper())

    # Filtre par statut
    status_filter = request.query_params.get('status')
    if status_filter:
        queryset = queryset.filter(statut=status_filter.upper())

    # Filtre par âge (JSONField)
    min_age = request.query_params.get('min_age')
    max_age = request.query_params.get('max_age')

    if min_age or max_age:
        filtered_ids = []
        for case in queryset:
            patient = case.donnees_patient or {}
            age = patient.get('age')
            if age is not None:
                if min_age and age < int(min_age):
                    continue
                if max_age and age > int(max_age):
                    continue
                filtered_ids.append(case.id)
        queryset = queryset.filter(id__in=filtered_ids)

    # Filtre par symptôme
    symptom = request.query_params.get('symptom')
    if symptom:
        filtered_ids = []
        for case in queryset:
            for s in (case.symptomes or []):
                if isinstance(s, dict) and symptom.lower() in s.get('nom', '').lower():
                    filtered_ids.append(case.id)
                    break
        queryset = queryset.filter(id__in=filtered_ids)

    return queryset
