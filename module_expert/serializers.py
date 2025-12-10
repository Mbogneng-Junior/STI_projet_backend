from rest_framework import serializers
from .models import DomaineMedical, ExpertHumain, ExpertIA, CasClinique, EtapeClinique

class DomaineMedicalSerializer(serializers.ModelSerializer):
    class Meta:
        model = DomaineMedical
        fields = '__all__'

class ExpertHumainSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpertHumain
        fields = '__all__'

class ExpertIASerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpertIA
        fields = '__all__'

class EtapeCliniqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtapeClinique
        fields = '__all__'

class CasCliniqueSerializer(serializers.ModelSerializer):
    etapes = EtapeCliniqueSerializer(many=True, read_only=True)
    
    class Meta:
        model = CasClinique
        fields = '__all__'
