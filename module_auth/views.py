from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .serializers import RegisterSerializer, LoginSerializer
from module_apprenant.models import Apprenant
from module_expert.models import ExpertHumain, DomaineMedical
from .serializers import RegisterSerializer, LoginSerializer, ExpertRegisterSerializer, ExpertLoginSerializer
class RegisterView(APIView):
    """Vue pour l'inscription d'un nouvel apprenant."""
    permission_classes = [] # Pas besoin d'être authentifié pour s'inscrire

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            # Crée un 'Apprenant' et un 'User' Django associé
            apprenant = serializer.save()
            return Response({
                "id": apprenant.id,
                "nom": apprenant.nom,
                "email": apprenant.email,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    """Vue pour la connexion et la récupération d'un token."""
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Le serializer valide que l'utilisateur existe
        email = serializer.validated_data['email']
        apprenant = Apprenant.objects.get(email=email)
        
        # Créer ou récupérer le token
        token, created = Token.objects.get_or_create(user=apprenant.user)
        
        # Vérifier si le profil existe (legacy support)
        est_profile = False
        try:
            if hasattr(apprenant, 'profil'):
                est_profile = apprenant.profil.est_profile
        except Exception:
            # Si le profil n'existe pas (RelatedObjectDoesNotExist), on considère False
            est_profile = False

        return Response({
            'token': token.key,
            'apprenant': {
                'id': apprenant.id,
                'nom': apprenant.nom,
                'email': apprenant.email,
                'est_profile': est_profile
            }
        })

class LogoutView(APIView):
    """Vue pour la déconnexion (suppression du token)."""
    def post(self, request):
        try:
            request.user.auth_token.delete()
        except (AttributeError, Token.DoesNotExist):
            pass # L'utilisateur n'était pas connecté ou n'avait pas de token
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class ExpertRegisterView(APIView):
    """Vue pour l'inscription d'un nouvel expert."""
    permission_classes = []

    def post(self, request):
        serializer = ExpertRegisterSerializer(data=request.data)
        if serializer.is_valid():
            expert = serializer.save()
            return Response({
                "id": expert.id,
                "nom": expert.nom,
                "email": expert.email,
                "matricule": expert.matricule
            }, status=status.HTTP_201_CREATED)
        # Afficher les erreurs exactes dans le terminal
        print("❌ Erreur validation ExpertRegister:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ExpertLoginView(APIView):
    """Vue pour la connexion d'un expert et la récupération d'un token."""
    permission_classes = []

    def post(self, request):
        serializer = ExpertLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        expert = ExpertHumain.objects.get(email=email)
        token, created = Token.objects.get_or_create(user=expert.user)
        
        return Response({
            'token': token.key,
            'expert': {
                'id': expert.id,
                'nom': expert.nom,
                'email': expert.email,
                'matricule': expert.matricule,
                'domaine': expert.domaine_expertise.nom
            }
        })