from google.adk.agents import Agent

from module_expert.constante import MODEL_NAME
from module_expert.tools.descriptions import DESC_PEDIATRIE, INSTR_PEDIATRIE, KEY_EXPERT_ANALYSIS

# Import des 3 outils nécessaires
from .tools.expert_tools import search_pedia_cases
from module_expert.tools.scoring_tools import enregistrer_evaluations_multiples
from module_expert.tools.lire_conversation import lire_conversation

pediatrie_expert = Agent(
    name="Expert_Pediatrie",
    model=MODEL_NAME,
    description=DESC_PEDIATRIE,
    instruction=INSTR_PEDIATRIE,
    tools=[
        lire_conversation,      # Indispensable pour voir le chat
        search_pedia_cases,     # Spécifique au domaine
        enregistrer_evaluations_multiples      # Indispensable pour noter
    ],
    output_key=KEY_EXPERT_ANALYSIS
)