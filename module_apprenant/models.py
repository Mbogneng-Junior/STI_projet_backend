import uuid
from django.db import models
from django.conf import settings
# On importe les modèles externes au début (si pas de boucle d'import)
from module_expert.models import DomaineMedical, CasClinique 

class Apprenant(models.Model):
    """
    Représente l'étudiant médecin.
    Note: Idéalement, relier ceci au modèle User de Django pour l'auth.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="apprenant")
    date_inscription = models.DateTimeField(auto_now_add=True) # Utile pour le suivi

    def __str__(self):
        return self.email

class Badge(models.Model):
    """
    Récompenses gamifiées (ex: "Expert Malaria", "Premier Diagnostic").
    """
    nom = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=100, blank=True, null=True) # Pour le frontend (ex: nom d'icône FontAwesome)

    def __str__(self):
        return self.nom

class ProfilEtudiant(models.Model):
    """
    Le profil global de l'étudiant, contenant son XP et ses badges.
    """
    apprenant = models.OneToOneField(
        Apprenant, 
        on_delete=models.CASCADE, 
        primary_key=True,
        related_name="profil"
    )
    xp_total = models.PositiveIntegerField(default=0)
    
    # Utilisation de JSONField pour stocker une liste (ex: ["Ne pose pas assez de questions", "Oublie la température"])
    # C'est plus flexible pour l'IA qui peut ajouter/retirer des items.
    lacunes_identifiees = models.JSONField(default=list, blank=True) 
    
    badges = models.ManyToManyField(Badge, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profil de {self.apprenant.email} (XP: {self.xp_total})"

class NiveauCompetence(models.Model):
    """
    Détail des compétences par domaine médical (ex: Cardio, Malaria).
    C'est ICI que l'Agent Expert va écrire les scores.
    """
    profil_etudiant = models.ForeignKey(
        ProfilEtudiant, 
        on_delete=models.CASCADE, 
        related_name="competences"
    )
    domaine = models.ForeignKey(
        DomaineMedical, 
        on_delete=models.PROTECT, 
        related_name="niveaux_apprenants"
    )
    
    # On reprend les choix du CasClinique pour la difficulté atteinte
    niveau_actuel = models.CharField(
        max_length=20, 
        choices=CasClinique.NiveauDifficulté.choices,
        default=CasClinique.NiveauDifficulté.DEBUTANT
    )

    # --- SCORES DÉTAILLÉS (0 à 100 par exemple) ---
    # Ces champs correspondent aux critères que l'Agent Expert évalue
    score_anamnese = models.FloatField(default=0.0)    # Qualité de l'interrogatoire
    score_diagnostic = models.FloatField(default=0.0)  # Justesse du diagnostic
    score_traitement = models.FloatField(default=0.0)  # Pertinence de l'ordonnance
    score_relationnel = models.FloatField(default=0.0) # Empathie / Ton (optionnel)
    
    progression_globale = models.FloatField(default=0.0) # Moyenne ou % de complétion du module

    class Meta:
        unique_together = ('profil_etudiant', 'domaine') # Un seul niveau par domaine par étudiant

    def __str__(self):
        return f"{self.profil_etudiant.apprenant.email} - {self.domaine.nom} ({self.niveau_actuel})"