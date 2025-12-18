from rest_framework import status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from adrf.viewsets import ViewSet # Indispensable pour l'async natif

from .agent import tuteur_service
from .serializers import AnalyseReponseSerializer, DemarrerSessionSerializer

class TuteurViewSet(ViewSet):
    """
    ViewSet 100% Asynchrone.
    """
    
    @extend_schema(request=DemarrerSessionSerializer)
    async def create_session(self, request):
        serializer = DemarrerSessionSerializer(data=request.data)
        if serializer.is_valid():
            # Appel direct avec await, sans wrapper
            session, msg = await tuteur_service.demarrer_session_async(
                serializer.validated_data['email_apprenant'],
                serializer.validated_data['domaine_nom']
            )
            
            if session:
                return Response({
                    "session_id": session.id,
                    "message": msg
                }, status=status.HTTP_201_CREATED)
            return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(request=AnalyseReponseSerializer)
    async def analyser_reponse(self, request):
        serializer = AnalyseReponseSerializer(data=request.data)
        if serializer.is_valid():
            # Appel direct avec await
            result = await tuteur_service.analyser_reponse_async(
                serializer.validated_data['session_id'],
                serializer.validated_data['reponse_etudiant'],
                serializer.validated_data.get('etape_actuelle', 'Diagnostic')
            )
            
            if "error" in result:
                 return Response(result, status=status.HTTP_400_BAD_REQUEST)
                 
            return Response(result)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)