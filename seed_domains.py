
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from module_expert.models import DomaineMedical

domaines = ["Cardiologie", "Infectiologie", "Pneumologie", "Neurologie", "Pédiatrie", "Dermatologie"]

for nom in domaines:
    obj, created = DomaineMedical.objects.get_or_create(nom=nom, defaults={"description": f"Spécialité {nom}"})
    if created:
        print(f"Created domain: {nom}")
    else:
        print(f"Domain exists: {nom}")
