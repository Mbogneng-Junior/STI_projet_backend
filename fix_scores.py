import os
import django
import sys

# Setup Django Environment
sys.path.append('/home/mbogneng-junior/Documents/5GI/Projets/STI/STI_GLOBAL/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from module_apprenant.models import NiveauCompetence, ProfilEtudiant
from module_expert.models import CasClinique

def run_fix():
    print("--- FIXING DOMAIN vs GLOBAL SCORES ---")
    
    # 1. Migrate Data: If Global is 0 but Domains have data (legacy case), copy one domain's data to Global.
    #    (Since the user complained about all domains having the same copied score, we can pick any).
    profils = ProfilEtudiant.objects.all()
    migrated_count = 0
    
    for p in profils:
        # Check if globals are empty/zero
        if (p.global_anamnese == 0 and p.global_diagnostic == 0 and 
            p.global_traitement == 0 and p.global_relationnel == 0):
            
            # Find a domain with data
            # Use filter to find non-zero
            comp = NiveauCompetence.objects.filter(profil_etudiant=p, score_anamnese__gt=0).first()
            
            if comp:
                print(f"Migrating stats for {p.apprenant.email} from domain {comp.domaine.nom}...")
                p.global_anamnese = comp.score_anamnese
                p.global_diagnostic = comp.score_diagnostic
                p.global_traitement = comp.score_traitement
                p.global_relationnel = comp.score_relationnel
                p.est_profile = True # Ensure this is true
                p.save()
                migrated_count += 1
    
    print(f"Migrated global stats for {migrated_count} profiles.")
    
    # 2. Reset ALL Domain Competences to 0.
    #    The user specifically requested this: "scores of each domain must be 0 at start".
    
    updated_count = NiveauCompetence.objects.update(
        score_anamnese=0.0,
        score_diagnostic=0.0,
        score_traitement=0.0,
        score_relationnel=0.0,
        progression_globale=0.0,
        niveau_actuel=CasClinique.NiveauDifficulté.DEBUTANT
    )
    
    print(f"SUCCESS: Reset scores for {updated_count} domain-competence entries.")

if __name__ == '__main__':
    run_fix()
