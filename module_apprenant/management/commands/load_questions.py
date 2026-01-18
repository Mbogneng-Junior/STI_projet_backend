import json
import os
from django.core.management.base import BaseCommand
from module_apprenant.models import QuestionProfiling
from django.conf import settings

class Command(BaseCommand):
    help = 'Charge les questions de profiling depuis qcm.json'

    def handle(self, *args, **options):
        # Base path assumption: script runs from backend/ manage.py context
        # qcm.json is in the same directory as manage.py
        file_path = os.path.join(settings.BASE_DIR, 'qcm.json')

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Fichier introuvable : {file_path}'))
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        questions_data = data.get('questions', [])
        
        # Clear existing questions to avoid duplication if running multiple times
        # Or you could update_or_create based on text/id
        QuestionProfiling.objects.all().delete()
        self.stdout.write(self.style.WARNING('Anciennes questions supprimées.'))

        count = 0
        for q_data in questions_data:
            QuestionProfiling.objects.create(
                competence=q_data.get('competence'),
                situation=q_data.get('situation'),
                question_text=q_data.get('question'),
                options=q_data.get('options')
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'{count} questions de profiling chargées avec succès.'))
