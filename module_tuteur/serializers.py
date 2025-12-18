from rest_framework import serializers

class DemarrerSessionSerializer(serializers.Serializer):
    email_apprenant = serializers.EmailField()
    domaine_nom = serializers.CharField()

class AnalyseReponseSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    reponse_etudiant = serializers.CharField()
    etape_actuelle = serializers.CharField(required=False, default="Diagnostic")