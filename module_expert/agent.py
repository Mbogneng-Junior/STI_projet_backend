import json
from google.adk.agents import Agent

from module_expert.constante import MODEL_NAME

from google.adk.apps.app import App
from google.adk.agents.context_cache_config import ContextCacheConfig

from module_expert.tools.descriptions import KEY_ROOT_DELEGATION
from .subagents import (
    malaria_expert,
    cardiologie_expert,
    pediatrie_expert,
    dermatologie_expert
)

import os
import sys
import django
from dotenv import load_dotenv


# NOUVEL IMPORT DE L'OUTIL DE LECTURE DE DOMAINE
from .tools.domain_tools import get_session_domain # <--- NOUVEL IMPORT

# --- AGENT RACINE ---

root_expert_instruction = (
    "Tu es un routeur d'experts médicaux. Ton UNIQUE et SEUL objectif est de déterminer le nom de l'expert spécifique à appeler.\n"
    "### PROCÉDURE OBLIGATOIRE ###\n"
    "1. Commence TOUJOURS par appeler l'outil 'get_session_domain()' pour obtenir le domaine médical actuel de la session.\n"
    "2. En te basant sur le RÉSULTAT de cet outil, tu DOIS retourner UNIQUEMENT le nom EXACT du sous-agent expert correspondant, et RIEN D'AUTRE.\n"
    "   Ceci est un MAPPING STRICT. Ne génère ABSOLUMENT PAS de code Python, de raisonnement, ou d'autres phrases.\n"
    "   Utilise le résultat de 'get_session_domain()' pour ce mapping :\n"
    "   - Si le domaine est 'Paludisme', réponds: 'Expert_Paludisme'.\n"
    "   - Si le domaine est 'Cardiologie', réponds: 'Expert_Cardiologie'.\n"
    "   - Si le domaine est 'Dermatologie', réponds: 'Expert_Dermatologie'.\n"
    "   - Si le domaine est 'Pédiatrie', réponds: 'Expert_Pediatrie'.\n"
    "   - Si le domaine retourné par l'outil n'est pas l'un de ceux-ci, réponds: 'Domaine_Inconnu'.\n"
    "RÉPONDS UNIQUEMENT avec le nom de l'agent. Par exemple: 'Expert_Paludisme'."
)

root_agent = Agent(
    name="Root_Expert_Medical",
    model=MODEL_NAME, 
    description="Routeur strict pour les experts médicaux.",
    instruction=root_expert_instruction,
    tools=[get_session_domain], # <--- L'AGENT RACINE UTILISE MAINTENANT CET OUTIL
    sub_agents=[
        malaria_expert,
        cardiologie_expert,
        pediatrie_expert,
        dermatologie_expert
    ],
    output_key=KEY_ROOT_DELEGATION
)

expert_app = App(
    name='sti_app', # Assurez-vous que c'est 'sti_app'
    root_agent=root_agent,
    context_cache_config=ContextCacheConfig(
        min_tokens=1000,
        ttl_seconds=3600,
        cache_intervals=10,
    ),
)