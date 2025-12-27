

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from module_apprenant.models import Apprenant
from module_expert.models import ExpertHumain, DomaineMedical

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    nom = serializers.CharField(required=True, max_length=100)
    
    class Meta:
        model = Apprenant
        fields = ('email', 'password', 'nom')

    def create(self, validated_data):
        # On sépare les données de User et de Apprenant
        user_email = validated_data['email']
        user_password = validated_data['password']
        apprenant_nom = validated_data['nom']

        # Création de l'utilisateur Django standard
        user = User.objects.create_user(
            username=user_email, # On utilise l'email comme username pour la simplicité
            email=user_email,
            password=user_password
        )
        
        # Création de l'apprenant lié
        apprenant = Apprenant.objects.create(
            user=user,
            email=user_email,
            nom=apprenant_nom
        )
        return apprenant

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Email ou mot de passe incorrect.")
        
        if not hasattr(user, 'apprenant'):
             raise serializers.ValidationError("Ce compte n'est pas un compte apprenant.")

        return data
    

class ExpertRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    # On s'attend à recevoir l'UUID du domaine d'expertise
    domaine_expertise_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = ExpertHumain
        fields = ('email', 'password', 'nom', 'matricule', 'domaine_expertise_id')

    def create(self, validated_data):
        user_email = validated_data['email']
        user_password = validated_data['password']
        
        # Création de l'utilisateur Django
        user = User.objects.create_user(
            username=user_email,
            email=user_email,
            password=user_password
        )
        
        # Récupération du domaine d'expertise
        try:
            domaine = DomaineMedical.objects.get(id=validated_data['domaine_expertise_id'])
        except DomaineMedical.DoesNotExist:
            raise serializers.ValidationError("Le domaine d'expertise spécifié n'existe pas.")

        # Création de l'expert lié
        expert = ExpertHumain.objects.create(
            user=user,
            email=user_email,
            nom=validated_data['nom'],
            matricule=validated_data['matricule'],
            domaine_expertise=domaine
        )
        return expert

class ExpertLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Email ou mot de passe incorrect.")
        
        # On vérifie que cet utilisateur est bien un expert
        if not hasattr(user, 'experthumain'):
             raise serializers.ValidationError("Ce compte n'est pas un compte expert.")

        return data