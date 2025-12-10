import uuid
from django.db import models
from module_expert.models import DomaineMedical # Importation inter-applications


# Create your models here.



class Apprenant(models.Model):
    id=models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom=models.CharField(max_length=255)
    email=models.EmailField(unique=True)

    def __str__(self):
        return self.email
    


class Badge(models.Model):

    nom=models.CharField(max_length=255, unique=True)

    description=models.TextField()
    def __str__(self):
        return  self.nom
    

class ProfilEtudiant(models.Model):
    apprenant=models.OneToOneField(Apprenant,on_delete=models.CASCADE,primary_key=True)
    xp_total = models.PositiveIntegerField(default=0)
    lacunes_identifiees = models.TextField(blank=True)
    badges = models.ManyToManyField(Badge, blank=True)

    def __str__(self):
        return f"Profil de {self.apprenant.email}"


class NiveauCompetence(models.Model):
    # On réutilise l'énumération de CasClinique pour la cohérence
    from module_expert.models import CasClinique
    
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
    niveau_actuel = models.CharField(
        max_length=20, 
        choices=CasClinique.NiveauDifficulté.choices
    )
    score_diagnostic = models.FloatField(default=0.0)
    score_raisonnement = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('profil_etudiant', 'domaine')

    def __str__(self):
        return f"{self.profil_etudiant.apprenant.email} - {self.domaine.nom}"