import os
from dotenv import load_dotenv # Import nécessaire
from google.adk.sessions import DatabaseSessionService

# 1. On force le chargement du .env situé à la racine
# (On remonte d'un niveau par rapport à 'config/')
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(base_dir, '.env'))

# 2. Récupération des variables avec des valeurs par défaut pour le LOCAL
# Note: On force '127.0.0.1' si la variable est vide
DB_USER = os.environ.get('DB_USER', 'backendsti')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'backendsti')
DB_HOST = os.environ.get('DB_HOST', '127.0.0.1') 
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'backendsti')

# 3. Construction de l'URL
# Important : asyncpg est requis pour l'async
db_url = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Debug : Affiche l'URL (masque le mot de passe pour sécurité si tu veux)
print(f"🔌 ADK Connect to: postgresql+asyncpg://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}")

session_service = DatabaseSessionService(db_url=db_url)