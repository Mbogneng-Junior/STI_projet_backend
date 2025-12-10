# module_interface/models.py

import uuid
from django.db import models
from module_apprenant.models import Apprenant
from module_expert.models import CasClinique

class SessionApprentissage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    apprenant = models.ForeignKey(
        Apprenant, 
        on_delete=models.CASCADE, 
        related_name="sessions"
    )
    cas_clinique = models.ForeignKey(
        CasClinique, 
        on_delete=models.SET_NULL, # On garde la session même si le cas est supprimé
        null=True, 
        related_name="sessions"
    )
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(blank=True, null=True)
    score_session = models.IntegerField(default=0, null=True)

    def __str__(self):
        return f"Session de {self.apprenant.email} sur '{self.cas_clinique.titre}'"

class Interaction(models.Model):
    class TypeFeedback(models.TextChoices):
        DIRECT = 'DIRECT', 'Direct'
        SOCRATIQUE = 'SOCRATIQUE', 'Socratique'
        SCAFFOLDING = 'SCAFFOLDING', 'Scaffolding'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        SessionApprentissage, 
        on_delete=models.CASCADE, 
        related_name="interactions"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    question_contenu = models.TextField()
    reponse_contenu = models.TextField(blank=True)
    reponse_est_valide = models.BooleanField(null=True)
    feedback_contenu = models.TextField(blank=True)
    feedback_type = models.CharField(max_length=20, choices=TypeFeedback.choices, blank=True)
    
    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Interaction du {self.timestamp.strftime('%Y-%m-%d %H:%M')}"