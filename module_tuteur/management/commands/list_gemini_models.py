from django.core.management.base import BaseCommand
import os
import asyncio
from google.genai import Client

class Command(BaseCommand):
    help = 'List available Gemini models'

    def handle(self, *args, **options):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            self.stdout.write(self.style.ERROR("GOOGLE_API_KEY not found in environment"))
            # Fallback check if it's in settings?
            # from django.conf import settings
            # api_key = getattr(settings, "GOOGLE_API_KEY", None)
            
        if not api_key:
             self.stdout.write(self.style.ERROR("Cannot proceed without API KEY"))
             return

        async def list_models():
            client = Client(api_key=api_key)
            self.stdout.write("Fetching models...")
            # Correction : il faut await l'itérateur retourné par list() 
            # ou l'utiliser correctement selon la version du SDK.
            # D'après la doc récente 'genai', models.list n'est PAS une coroutine directe,
            # mais elle retourne un AsyncIterator si utilisée avec aio.
            # L'erreur dit "got coroutine", donc client.aio.models.list(...) EST une coroutine.
            
            # Essayons d'abord d'obtenir l'itérateur
            pager = await client.aio.models.list(config={"query_base": True})
            async for model in pager:
                # Inspecter les attributs disponibles si besoin, ou juste afficher le modèle
                # self.stdout.write(f"Raw model: {model}")
                self.stdout.write(self.style.SUCCESS(f"Model ID: {model.name}"))

        asyncio.run(list_models())
