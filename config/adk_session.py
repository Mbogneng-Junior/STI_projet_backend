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
# NOTE: On instance le service à chaque demande pour être "Loop-Safe" avec asgiref/asyncio.
# Le problème de "Race Condition" sur la création des tables/types doit être géré
# par des retries au niveau de l'appelant.

def get_adk_session_service():
    """
    Instancie le DatabaseSessionService.
    Retourne une nouvelle instance à chaque appel pour garantir la compatibilité
    avec la boucle d'événements courante (Event Loop) du thread de la requête.
    """
    # print("🔧 Instanciation (Factory) du ADK DatabaseSessionService...")

    # On définit les options que SQLAlchemy `create_async_engine` comprend.
    engine_options = {
        "connect_args": {
            "server_settings": {
                # Ceci dit à PostgreSQL: "Pour cette connexion, cherche et crée les tables
                # en priorité dans 'adk_schema'."
                "search_path": "adk_schema,public"
            }
        },
        # Optionnel: Réduire la taille du pool pour éviter de saturer postgres
        # si on crée beaucoup d'instances.
        "pool_size": 2,
        "max_overflow": 5,
    }

    # SOLUTION FINALE :
    # On ne passe QUE db_url et les options compatibles avec create_async_engine.
    return DatabaseSessionService(
        db_url=db_url,
        **engine_options
    )
