import os
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command # <--- AJOUTER CET IMPORT

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()

# --- AJOUTER CE BLOC ---
# On s'assure que cela ne s'exécute pas pendant les migrations ou autres commandes
# Le check 'runserver' est une sécurité simple pour le développement.
import sys
if 'runserver' in sys.argv:
    try:
        print("🚀 [WSGI] Exécution de la commande init_data au démarrage...")
        call_command('init_data')
    except Exception as e:
        print(f"Erreur lors de l'exécution de init_data via WSGI : {e}")
# --- FIN DE L'AJOUT ---