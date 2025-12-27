from rest_framework import status
from rest_framework.response import Response
from adrf.viewsets import ViewSet
from drf_spectacular.utils import extend_schema
from google.api_core.exceptions import ResourceExhausted

# --- IMPORTS NETTOYÉS ---
# 'DatabaseSessionService' et 'db_url' ne sont plus utilisés directement ici.
# On importe uniquement la fonction qui fait le travail.
from config.adk_session import get_adk_session_service
# --- FIN DU NETTOYAGE ---

from .serializers import AnalyseReponseSerializer, DemarrerSessionSerializer
from .orchestrator import orchestrator
from .services import session_manager
from module_interface.models import SessionApprentissage

class TuteurViewSet(ViewSet):
    """
    ViewSet Asynchrone pour le Tuteur Intelligent.
    """
    
    @extend_schema(request=DemarrerSessionSerializer)
    async def create_session(self, request):
        serializer = DemarrerSessionSerializer(data=request.data)
        if serializer.is_valid():
            # On utilise notre fonction pour obtenir une instance correctement configurée
            session_service = get_adk_session_service()
            
            session, msg = await session_manager.demarrer_session(
                serializer.validated_data['email_apprenant'],
                serializer.validated_data['domaine_nom'],
                session_service=session_service
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
            session_id = str(serializer.validated_data['session_id'])
            message = serializer.validated_data['reponse_etudiant']

            try:
                session_obj = await SessionApprentissage.objects.select_related('apprenant').aget(id=session_id)
                user_id = str(session_obj.apprenant.id)
            except SessionApprentissage.DoesNotExist:
                return Response({"error": "Session ID invalide"}, status=404)

            session_service = get_adk_session_service()

            try:
                result = await orchestrator.traiter_interaction(
                    user_id=user_id, 
                    session_id=session_id, 
                    message_etudiant=message,
                    session_service=session_service
                )
                return Response(result)
            except ResourceExhausted as e:
                print(f"Quota API Gemini dépassé : {e.message}")
                return Response(
                    {"error": "Le service d'IA est temporairement surchargé. Veuillez réessayer dans quelques instants."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    async def get_state(self, request, session_id=None):
        try:
            session_obj = await SessionApprentissage.objects.select_related('apprenant').aget(id=session_id)
            user_id = str(session_obj.apprenant.id)
            
            session_service = get_adk_session_service()
            
            state = await orchestrator.get_session_details(session_id, user_id=user_id, session_service=session_service)
            
            if state:
                return Response({
                    "chat_history": state.get("history", []),
                    "internal_logs": state.get("internal_logs", []),
                    "student_profile": state.get("student_profile", {})
                })
            return Response({"error": "Etat introuvable"}, status=404)
            
        except SessionApprentissage.DoesNotExist:
            return Response({"error": "Session Django introuvable"}, status=404)