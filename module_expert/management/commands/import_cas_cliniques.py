import json
import os
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from module_expert.models import CasClinique, DomaineMedical
from django.conf import settings

class Command(BaseCommand):
    help = 'Import clinical cases from JSON file'

    def handle(self, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, 'cas-cliniques.json')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        created_count = 0
        updated_count = 0

        for item in data:
            # 1. Get/Create Domaine
            domaine_nom = item.get('specialite_medicale', 'Généraliste')
            if not domaine_nom:
                domaine_nom = 'Généraliste'
            domaine, _ = DomaineMedical.objects.get_or_create(nom=domaine_nom)

            # 2. Map Status
            status_map = {
                'valide': CasClinique.StatutCas.PUBLIE,
                'brouillon': CasClinique.StatutCas.BROUILLON_IA,
                'archive': CasClinique.StatutCas.ARCHIVE
            }
            statut = status_map.get(item.get('status', 'brouillon'), CasClinique.StatutCas.BROUILLON_IA)

            # 3. Map Difficulty
            diff_map = {
                'debutant': CasClinique.NiveauDifficulté.DEBUTANT,
                'intermediaire': CasClinique.NiveauDifficulté.INTERMEDIAIRE,
                'avance': CasClinique.NiveauDifficulté.AVANCE,
                'expert': CasClinique.NiveauDifficulté.EXPERT
            }
            diff_val = item.get('niveau_difficulte', 'debutant')
            # Handle if value is None
            if diff_val is None:
                diff_val = 'debutant'
            difficulte = diff_map.get(diff_val.lower(), CasClinique.NiveauDifficulté.DEBUTANT)

            # 4. Prepare Data
            pathologie = item.get('pathologie_principale', '')
            age = item.get('donnees_personnelles', {}).get('age', '?')
            titre = f"{pathologie} - {age} ans" if pathologie else f"Cas {item.get('id_unique')}"
            
            date_val_str = item.get('date_validation')
            date_val = None
            if date_val_str:
                date_val = parse_datetime(date_val_str)
                if date_val and timezone.is_naive(date_val):
                    date_val = timezone.make_aware(date_val)

            # Create/Update
            cas, created = CasClinique.objects.update_or_create(
                id_unique=item.get('id_unique'),
                defaults={
                    'titre': titre,
                    'statut': statut,
                    'difficulte': difficulte,
                    'domaine': domaine,
                    'pathologie': pathologie,
                    'donnees_patient': item.get('donnees_personnelles', {}),
                    'motif_consultation': item.get('motif_consultation', ''),
                    'mode_de_vie': item.get('mode_de_vie', {}),
                    'antecedents_medicaux': item.get('antecedents_medicaux', {}),
                    'symptomes': item.get('symptomes', []),
                    'diagnostics_physiques': item.get('diagnostic_physique', []),
                    'examens_complementaires': item.get('examens_complementaires', []),
                    'diagnostic_final': item.get('diagnostic_final', ''),
                    'traitement': item.get('traitement_en_cours', []),
                    'objectifs_pedagogiques': item.get('objectifs_pedagogiques', []),
                    'indices_cliniques': item.get('indices_cliniques', []),
                    'erreurs_courantes': item.get('erreurs_courantes', []),
                    'date_validation': date_val,
                    # Backward compat matches
                    'historique_medical': json.dumps(item.get('antecedents_medicaux', {})),
                    'solution_experte': f"Diagnostic: {item.get('diagnostic_final', 'N/A')}.\nSynthèse: {len(item.get('examens_complementaires', []))} examens, {len(item.get('symptomes', []))} symptômes."
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
                
        self.stdout.write(self.style.SUCCESS(f'Successfully processed cases. Created: {created_count}, Updated: {updated_count}'))
