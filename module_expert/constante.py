# module_expert/constante.py
from google.adk.models.lite_llm import LiteLlm
import os

# --- DEFINITIONS DES MODELES ---
# Gemini (Google) - Version Flash rapide
MODEL_GEMINI_FLASH = "gemini-2.0-flash"

# Mistral AI (Via LiteLLM) - Moins cher et performant
MODEL_MISTRAL_LARGE = "mistral/mistral-large-latest"
MODEL_MISTRAL_SMALL = "mistral/mistral-small-latest"

# OpenAI - Haut de gamme
MODEL_GPT4O = "openai/gpt-4o"

# MiniMax (Via LiteLLM - Anthropic Compatible)
MODEL_MINIMAX = "minimax/MiniMax-M2.1"

# Ollama (Local) - Gratuit et privé
MODEL_OLLAMA_MIXTRAL = "ollama/mixtral"
MODEL_OLLAMA_LLAMA3 = "ollama/llama3"
MODEL_OLLAMA_MISTRAL = "ollama/mistral"


# --- SÉLECTION DU MODÈLE ACTUEL ---
# Décommentez la ligne correspondant au modèle que vous souhaitez utiliser pour TOUT le système.

# OPTION 1: GEMINI (Original)
# MODEL_NAME = MODEL_GEMINI_FLASH

# OPTION 2: MISTRAL (Pour économiser les quotas Google)
# Nous enveloppons le modèle dans LiteLlm pour la compatibilité ADK.
MODEL_NAME = LiteLlm(model=MODEL_MISTRAL_LARGE)

# OPTION 3: GPT-4o
# MODEL_NAME = LiteLlm(model=MODEL_GPT4O)

# OPTION 4: OLLAMA (Local ou Distant)
# MODEL_NAME = LiteLlm(model=MODEL_OLLAMA_MISTRAL, api_base="http://localhost:11434")

# OPTION 5: GROQ (Alternative "En ligne" ultra-rapide pour Llama 3 / Mistral)
# Nécessite GROQ_API_KEY dans votre fichier .env
# Le modèle llama3-70b-8192 est obsolète, nous utilisons la nouvelle version stable.
# Utilisation de llama-3.1-8b-instant pour éviter les erreurs de Rate Limit (TPM) sur le tier gratuit.
#MODEL_NAME = LiteLlm(model="groq/llama-3.1-8b-instant")
