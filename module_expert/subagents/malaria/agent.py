from google.adk.agents import Agent

from module_expert.constante import MODEL_NAME
from module_expert.tools.descriptions import DESC_MALARIA, INSTR_MALARIA, KEY_EXPERT_ANALYSIS

# Import des 3 outils nécessaires
from .tools.expert_tools import search_similar_cases
from module_expert.tools.scoring_tools import enregistrer_evaluations_multiples
from module_expert.tools.lire_conversation import lire_conversation

malaria_expert = Agent(
    name="Expert_Paludisme",
    model=MODEL_NAME,
    description=DESC_MALARIA,
    instruction=INSTR_MALARIA,
    tools=[
        lire_conversation,      # Indispensable pour voir le chat
        search_similar_cases,   # Spécifique au domaine
        enregistrer_evaluations_multiples        # Indispensable pour noter
    ],
    output_key=KEY_EXPERT_ANALYSIS
)