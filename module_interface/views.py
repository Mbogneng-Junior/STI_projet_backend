from rest_framework import viewsets
from drf_spectacular.utils import extend_schema
from .models import SessionApprentissage, Interaction
from .serializers import SessionApprentissageSerializer, InteractionSerializer

@extend_schema(tags=['Interface - Sessions'])
class SessionApprentissageViewSet(viewsets.ModelViewSet):
    queryset = SessionApprentissage.objects.all()
    serializer_class = SessionApprentissageSerializer

@extend_schema(tags=['Interface - Interactions'])
class InteractionViewSet(viewsets.ModelViewSet):
    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer
