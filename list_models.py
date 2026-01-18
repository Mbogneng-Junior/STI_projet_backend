import asyncio
import os
from google.genai import Client

# On suppose que la clé API est dans l'environnement comme pour le reste du projet
async def list_models():
    client = Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    async for model in client.aio.models.list(config={"query_base": True}):
        if "generateContent" in model.supported_generation_methods:
            print(f"Model: {model.name} (Display: {model.display_name})")

if __name__ == "__main__":
    asyncio.run(list_models())