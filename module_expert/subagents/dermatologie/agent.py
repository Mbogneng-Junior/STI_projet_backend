from google.adk.agents import Agent

from module_expert.constante import MODEL_NAME
from module_expert.tools.descriptions import DESC_DERMATOLOGIE, INSTR_DERMATOLOGIE, KEY_EXPERT_ANALYSIS

# Import des 3 outils nécessaires
from .tools.expert_tools import search_derma_cases
from module_expert.tools.scoring_tools import enregistrer_evaluations_multiples
from module_expert.tools.lire_conversation import lire_conversation

dermatologie_expert = Agent(
    name="Expert_Dermatologie",
    model=MODEL_NAME,
    description=DESC_DERMATOLOGIE,
    instruction=INSTR_DERMATOLOGIE,
    tools=[
        lire_conversation,      
        search_derma_cases,     
        enregistrer_evaluations_multiples
                      
    ],
    output_key=KEY_EXPERT_ANALYSIS
)