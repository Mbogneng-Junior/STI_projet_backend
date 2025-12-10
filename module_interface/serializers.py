from rest_framework import serializers
from .models import SessionApprentissage, Interaction

class InteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = '__all__'

class SessionApprentissageSerializer(serializers.ModelSerializer):
    interactions = InteractionSerializer(many=True, read_only=True)
    
    class Meta:
        model = SessionApprentissage
        fields = '__all__'
