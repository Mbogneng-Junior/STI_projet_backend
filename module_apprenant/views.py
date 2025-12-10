from rest_framework import viewsets
from drf_spectacular.utils import extend_schema
from .models import Apprenant, Badge, ProfilEtudiant, NiveauCompetence
from .serializers import (
    ApprenantSerializer, 
    BadgeSerializer, 
    ProfilEtudiantSerializer, 
    NiveauCompetenceSerializer
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
