from rest_framework import viewsets
from drf_spectacular.utils import extend_schema
from .models import DomaineMedical, ExpertHumain, ExpertIA, CasClinique, EtapeClinique
from .serializers import (
    DomaineMedicalSerializer, 
    ExpertHumainSerializer, 
    ExpertIASerializer, 
    CasCliniqueSerializer, 
    EtapeCliniqueSerializer
)

@extend_schema(tags=['Expert - Domaines Médicaux'])
class DomaineMedicalViewSet(viewsets.ModelViewSet):
    queryset = DomaineMedical.objects.all()
    serializer_class = DomaineMedicalSerializer

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

@extend_schema(tags=['Expert - Étapes Cliniques'])
class EtapeCliniqueViewSet(viewsets.ModelViewSet):
    queryset = EtapeClinique.objects.all()
    serializer_class = EtapeCliniqueSerializer
