from rest_framework import serializers
from .models import Apprenant, Badge, ProfilEtudiant, NiveauCompetence, QuestionProfiling

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

class QuestionProfilingSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionProfiling
        fields = '__all__'

class ProfilingSubmissionSerializer(serializers.Serializer):
    reponses = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Dictionnaire {question_id: index_option_choisie}"
    )
