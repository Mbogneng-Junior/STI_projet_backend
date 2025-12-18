from google.adk.agents import Agent
from .tools.expert_tools import search_pedia_cases
from module_expert.constante import MODEL_NAME

pediatrie_expert = Agent(
    name="Expert_Pediatrie",
    model=MODEL_NAME,
    description="Expert médical spécialisé dans la santé des enfants et nourrissons.",
    instruction=(
        "Tu es un expert en Pédiatrie.\n"
        "Ton rôle est d'analyser les cas cliniques concernant des enfants.\n"
        "Utilise l'outil 'search_pedia_cases' pour valider tes diagnostics.\n"
        "Adapte tes explications aux spécificités physiologiques de l'enfant."
    ),
    tools=[search_pedia_cases]
)
