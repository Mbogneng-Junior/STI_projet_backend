# module_expert/models.py

import uuid
from django.db import models
from django.conf import settings

class DomaineMedical(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.nom

class ExpertHumain(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # --- AJOUT CRUCIAL ---
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="experthumain")
    # --- FIN DE L'AJOUT ---
    nom = models.CharField(max_length=255)
    email = models.EmailField(unique=True, default="default@email.com") # Ajoutez une valeur par défaut temporaire
    matricule = models.CharField(max_length=100, unique=True)
    domaine_expertise = models.ForeignKey(
        DomaineMedical, 
        on_delete=models.PROTECT, 
        related_name="experts_humains"
    )

    def __str__(self):
        return f"{self.nom} ({self.domaine_expertise.nom})"

class ExpertIA(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    nom_ia = models.CharField(max_length=255)
    base_connaissance = models.TextField(blank=True)
    domaine_specialisation = models.ForeignKey(
        DomaineMedical, 
        on_delete=models.PROTECT, 
        related_name="experts_ia"
    )

    def __str__(self):
        return self.nom_ia

class CasClinique(models.Model):
    class StatutCas(models.TextChoices):
        BROUILLON_IA = 'BROUILLON_IA', 'Brouillon (IA)'
        EN_REVISION = 'EN_REVISION', 'En Révision'
        PUBLIE = 'PUBLIE', 'Publié'
        REJETE = 'REJETE', 'Rejeté'
        ARCHIVE = 'ARCHIVE', 'Archivé'

    class NiveauDifficulté(models.TextChoices):
        DEBUTANT = 'DEBUTANT', 'Débutant'
        INTERMEDIAIRE = 'INTERMEDIAIRE', 'Intermédiaire'
        AVANCE = 'AVANCE', 'Avancé'
        EXPERT = 'EXPERT', 'Expert'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_unique = models.CharField(max_length=50, unique=True, null=True, blank=True)
    
    titre = models.CharField(max_length=255)
    statut = models.CharField(max_length=20, choices=StatutCas.choices, default=StatutCas.BROUILLON_IA)
    difficulte = models.CharField(max_length=20, choices=NiveauDifficulté.choices)
    
    domaine = models.ForeignKey(
        DomaineMedical, 
        on_delete=models.PROTECT, 
        related_name="cas_cliniques"
    )

    # Données médicales structurées
    pathologie = models.CharField(max_length=255, blank=True)
    donnees_patient = models.JSONField(help_text="Données personnelles: age, sexe, profession...")
    motif_consultation = models.TextField(blank=True)
    mode_de_vie = models.JSONField(default=dict, blank=True)
    antecedents_medicaux = models.JSONField(default=dict, blank=True)
    
    # Signes et Examens
    symptomes = models.JSONField(default=list, blank=True)
    diagnostics_physiques = models.JSONField(default=list, blank=True)
    examens_complementaires = models.JSONField(default=list, blank=True)
    
    # Résolution
    diagnostic_final = models.CharField(max_length=255, blank=True)
    traitement = models.JSONField(default=list, blank=True)
    
    # Pédagogie
    objectifs_pedagogiques = models.JSONField(default=list, blank=True)
    indices_cliniques = models.JSONField(default=list, blank=True)
    erreurs_courantes = models.JSONField(default=list, blank=True)
    
    # Champs existants ou calculés
    solution_experte = models.TextField(blank=True, help_text="Résumé global de la solution")
    historique_medical = models.TextField(blank=True, null=True) # Gardé pour compatibilité temporaire
    date_validation = models.DateTimeField(blank=True, null=True)
    source_fultang_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    def __str__(self):
        return self.titre

class EtapeClinique(models.Model):
    cas_clinique = models.ForeignKey(
        CasClinique, 
        on_delete=models.CASCADE, 
        related_name="etapes"
    )
    ordre = models.PositiveIntegerField()
    description = models.TextField()
    type_etape = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['ordre']
        unique_together = ('cas_clinique', 'ordre')

    def __str__(self):
        return f"Étape {self.ordre} de {self.cas_clinique.titre}"