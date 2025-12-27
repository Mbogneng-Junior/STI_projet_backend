import json
from django.core.management.base import BaseCommand
from module_expert.models import DomaineMedical, CasClinique

class Command(BaseCommand):
    help = 'Initialise les Domaines Médicaux et un Cas Clinique de test (Requis pour le fonctionnement).'

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Démarrage de l'initialisation des données de référence...")

        # -----------------------------------------------------------
        # 1. CRÉATION DES DOMAINES MÉDICAUX
        # -----------------------------------------------------------
        domaines = ["Paludisme", "Cardiologie", "Dermatologie", "Pédiatrie"]
        objs_domaines = {}
        
        for nom in domaines:
            d, created = DomaineMedical.objects.get_or_create(
                nom=nom,
                defaults={"description": f"Domaine spécialisé en {nom}"}
            )
            objs_domaines[nom] = d
            if created:
                self.stdout.write(f"✅ Domaine créé : {nom}")
            else:
                self.stdout.write(f"ℹ️ Domaine existant : {nom}")

        # -----------------------------------------------------------
        # 2. CRÉATION D'UN CAS CLINIQUE (PALUDISME)
        # -----------------------------------------------------------
        # Sans ce cas, l'API renverra "Aucun cas disponible" même si le domaine existe.
        cas_titre = "Cas #1: Fièvre au retour du village"
        
        cas_data = {
            "nom": "Jean",
            "age": 25,
            "motif": "Fièvre et maux de tête",
            "histoire": "Revient d'un séjour de 2 semaines au village (zone marécageuse). A commencé à chauffer hier soir.",
            "constantes": {"temperature": "39.5°C", "tension": "12/8", "poids": "70kg"},
            "symptomes": ["Céphalées", "Frissons", "Courbatures", "Nausées"],
            "test_tdr": "Positif (Pf)"
        }

        cas, created = CasClinique.objects.get_or_create(
            titre=cas_titre,
            domaine=objs_domaines["Paludisme"],
            defaults={
                "statut": CasClinique.StatutCas.PUBLIE, # CRITIQUE : Seuls les cas PUBLIE sont sélectionnables
                "difficulte": CasClinique.NiveauDifficulté.DEBUTANT,
                "donnees_patient": cas_data,
                "historique_medical": "Patient sans antécédents particuliers. Pas d'allergie connue.",
                "solution_experte": (
                    "1. Suspecter un Paludisme simple devant la fièvre au retour de zone endémique.\n"
                    "2. Confirmer par un TDR ou Goutte Épaisse.\n"
                    "3. Traiter par ACT (Artemether-Lumefantrine)."
                )
            }
        )

        if created:
            self.stdout.write(f"✅ Cas Clinique de test créé : {cas_titre}")
        else:
            self.stdout.write(f"ℹ️ Cas Clinique de test existant : {cas_titre}")

        self.stdout.write(self.style.SUCCESS("🎉 Initialisation terminée ! Les domaines sont prêts."))