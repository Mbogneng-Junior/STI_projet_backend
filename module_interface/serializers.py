from rest_framework import serializers
from .models import SessionApprentissage, Interaction
from module_expert.serializers import CasCliniqueSerializer # <--- NOUVEL IMPORT

class InteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = '__all__'

class SessionApprentissageSerializer(serializers.ModelSerializer):
    # --- MODIFICATIONS CI-DESSOUS ---
    
    # On ajoute un champ qui va compter le nombre d'interactions
    interaction_count = serializers.SerializerMethodField()
    
    # On remplace le simple ID du cas clinique par l'objet complet
    cas_clinique = CasCliniqueSerializer(read_only=True)

    class Meta:
        model = SessionApprentissage
        # On ajoute les nouveaux champs à la liste des champs à sérialiser
        fields = ['id', 'apprenant', 'cas_clinique', 'date_debut', 'date_fin', 'score_session', 'interaction_count']

    def get_interaction_count(self, obj):
        # Cette méthode est appelée pour chaque session et compte les interactions associées
        return obj.interactions.count()