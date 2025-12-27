import os
import django

from django.core.asgi import get_asgi_application
from django.core.management import call_command  # Import pour exécuter les commandes Django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Configure Django une seule fois au démarrage de l'application ASGI
django.setup()

# Exécuter la commande init_data
try:
    call_command('init_data')
except Exception as e:
    print(f"Erreur lors de l'exécution de init_data : {e}")

application = get_asgi_application()