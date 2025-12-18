from google.adk.agents import Agent
from .tools.expert_tools import search_similar_cases
from module_expert.constante import MODEL_NAME

# Définition de l'agent expert en Paludisme
malaria_expert = Agent(
    name="Expert_Paludisme",
    model=MODEL_NAME,
    description="Expert médical spécialisé dans le diagnostic et le traitement du Paludisme.",
    instruction=(
        "Tu es un expert médical spécialisé dans le Paludisme.\n"
        "Ton rôle est d'analyser les cas suspects de paludisme et de valider les diagnostics.\n"
        "Utilise l'outil 'search_similar_cases' pour consulter ta base de connaissances (règles de production) "
        "et comparer le cas actuel avec des cas validés.\n"
        "Base tes explications UNIQUEMENT sur les preuves médicales et les cas similaires trouvés."
    ),
    tools=[search_similar_cases]
)
