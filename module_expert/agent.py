

import json
from google.adk.agents import Agent

from module_expert.constante import MODEL_NAME
from .tools.domain_tools import list_available_domains

from google.adk.apps.app import App
from google.adk.agents.context_cache_config import ContextCacheConfig
from .subagents import (
    malaria_expert,
    cardiologie_expert,
    pediatrie_expert,
    dermatologie_expert
)

import os
import sys
import django

from .tools.domain_tools import list_available_domains


from dotenv import load_dotenv

# --- BLOC D'INITIALISATION DJANGO (OBLIGATOIRE POUR ADK WEB) ---

# 1. Charger les variables d'environnement (.env à la racine)
# Cela permet à Django de trouver DB_USER, DB_PASSWORD, etc.
current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(current_dir) # Remonte vers /backend
load_dotenv(os.path.join(base_dir, '.env'))

# 2. Ajouter la racine du projet au Python Path
sys.path.append(base_dir)

# 3. Configurer les settings Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 4. Démarrer Django
# C'est cette ligne qui permet ensuite d'importer les modèles
django.setup()

# --- FIN DU BLOC D'INITIALISATION ---

# --- AGENT RACINE ---

root_expert_instruction = (
    "Tu es l'Agent Expert Racine du système de Tuteur Intelligent.\n"
    "Ton rôle est d'orchestrer l'expertise médicale.\n\n"
    
    "### FONCTIONNEMENT ###\n"
    "1. Tu reçois une demande concernant un cas clinique.\n"
    "2. Tu dois identifier le DOMAINE MÉDICAL concerné (ex: Paludisme, Cardiologie, etc.).\n"
    "3. Tu dois déléguer l'analyse au sous-agent expert de ce domaine.\n"
    "   - Si le cas concerne le Paludisme, délègue à 'Expert_Paludisme'.\n"
    "   - Si le cas concerne la Cardiologie, délègue à 'Expert_Cardiologie'.\n"
    "   - Si le cas concerne la Pédiatrie, délègue à 'Expert_Pediatrie'.\n"
    "   - Si le cas concerne la Dermatologie, délègue à 'Expert_Dermatologie'.\n"
    "   - Si aucun expert spécifique n'est disponible, signale-le.\n\n"
    
    "Tu ne dois pas inventer de diagnostic toi-même si tu n'as pas les règles spécifiques. "
    "Ton intelligence réside dans ta capacité à router la demande vers le bon spécialiste."
)

root_agent = Agent(
    name="Root_Expert_Medical",
    
    model=MODEL_NAME,
    description="Orchestrateur expert médical.",
    instruction=root_expert_instruction,
    tools=[list_available_domains],
    sub_agents=[
        malaria_expert,
        cardiologie_expert,
        pediatrie_expert,
        dermatologie_expert
    ]
)


expert_app = App(
    # CORRECTION ICI : remplace les tirets par des underscores
    name='sti_expert_medical_app', 
    
    root_agent=root_agent,
    context_cache_config=ContextCacheConfig(
        min_tokens=1000,
        ttl_seconds=3600,
        cache_intervals=10,
    ),
)

# Note: La factory 'create_expert_agent' a été remplacée par l'architecture multi-agents statique/dynamique
# définie dans le dossier 'subagents'.
