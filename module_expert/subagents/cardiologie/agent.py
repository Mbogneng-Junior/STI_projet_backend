from google.adk.agents import Agent
from .tools.expert_tools import search_cardio_cases
from module_expert.constante import MODEL_NAME

cardiologie_expert = Agent(
    name="Expert_Cardiologie",
    model=MODEL_NAME,
    description="Expert médical spécialisé dans les maladies cardiaques et vasculaires.",
    instruction=(
        "Tu es un expert en Cardiologie.\n"
        "Ton rôle est d'analyser les cas cliniques liés au cœur (douleurs thoraciques, hypertension, etc.).\n"
        "Utilise l'outil 'search_cardio_cases' pour valider tes hypothèses avec la base de connaissances.\n"
        "Sois vigilant sur les signes d'urgence vitale."
    ),
    tools=[search_cardio_cases]
)
