from rest_framework import serializers
from .models import Apprenant, Badge, ProfilEtudiant, NiveauCompetence

class ApprenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apprenant
        fields = '__all__'

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = '__all__'

class ProfilEtudiantSerializer(serializers.ModelSerializer):
    badges = BadgeSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProfilEtudiant
        fields = '__all__'

class NiveauCompetenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NiveauCompetence
        fields = '__all__'
