from rest_framework import viewsets
from drf_spectacular.utils import extend_schema
from .models import SessionApprentissage, Interaction
from .serializers import SessionApprentissageSerializer, InteractionSerializer
from django_filters.rest_framework import DjangoFilterBackend

@extend_schema(tags=['Interface - Sessions'])
class SessionApprentissageViewSet(viewsets.ModelViewSet):
    queryset = SessionApprentissage.objects.all().order_by('-date_debut') # On trie par défaut
    serializer_class = SessionApprentissageSerializer
    
    # --- AJOUTS POUR LE FILTRAGE ---
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'apprenant': ['exact'],
        'cas_clinique__domaine__nom': ['iexact'],
    }

@extend_schema(tags=['Interface - Interactions'])
class InteractionViewSet(viewsets.ModelViewSet):
    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer
