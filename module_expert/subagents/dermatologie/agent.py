from google.adk.agents import Agent
from .tools.expert_tools import search_derma_cases
from module_expert.constante import MODEL_NAME

dermatologie_expert = Agent(
    name="Expert_Dermatologie",
    model=MODEL_NAME,
    description="Expert médical spécialisé dans les maladies de la peau.",
    instruction=(
        "Tu es un expert en Dermatologie.\n"
        "Ton rôle est d'analyser les affections cutanées.\n"
        "Utilise l'outil 'search_derma_cases' pour comparer les symptômes visuels ou décrits avec ta base.\n"
        "Sois précis sur la description des lésions."
    ),
    tools=[search_derma_cases]
)
