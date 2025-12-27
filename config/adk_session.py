import os
from dotenv import load_dotenv
from google.adk.sessions import DatabaseSessionService

# 1. Chargement du .env
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(base_dir, '.env'))

# 2. Récupération des variables de connexion
DB_USER = os.environ.get('DB_USER', 'backendsti')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'backendsti')
DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'backendsti')

# 3. Construction de l'URL de la base de données (simple, sans options)
db_url = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# 4. Définition de la fonction d'instanciation du service
def get_adk_session_service():
    """
    Instancie le DatabaseSessionService en lui passant les options de connexion
    pour que son moteur interne utilise le bon schéma PostgreSQL.
    Ceci est la méthode de contournement pour le bug de l'argument 'schema'.
    """
    print("🔧 Instanciation (Workaround) du ADK DatabaseSessionService...")

    # On définit les options que SQLAlchemy `create_async_engine` comprend.
    engine_options = {
        "connect_args": {
            "server_settings": {
                # Ceci dit à PostgreSQL: "Pour cette connexion, cherche et crée les tables
                # en priorité dans 'adk_schema'."
                "search_path": "adk_schema,public"
            }
        }
    }

    # SOLUTION FINALE :
    # On ne passe QUE db_url et les options compatibles avec create_async_engine.
    # On ne passe SURTOUT PAS l'argument 'schema' qui cause le TypeError.
    # La logique du `search_path` va forcer la création et la recherche dans le bon schéma.
    return DatabaseSessionService(
        db_url=db_url,
        **engine_options
    )