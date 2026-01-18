from google.adk.agents import Agent
from module_expert.constante import MODEL_NAME

# Imports des outils
from module_expert.tools.descriptions import KEY_TUTOR_FEEDBACK
from module_tuteur.tools.introspection_tools import lire_profil_etudiant, lire_analyse_expert # <--- MODIFICATION
from module_tuteur.tools.expert_interface import consulter_expert_medical
from module_expert.tools.lire_conversation import lire_conversation


# <--- MODIFICATION MAJEURE DE LA STRATÉGIE DU TUTEUR ---
tuteur_instruction = (
    "Tu es un TUTEUR PÉDAGOGIQUE INTELLIGENT.\n"
    "Tu accompagnes un étudiant en médecine qui diagnostique un patient virtuel.\n\n"
    
    "### TA MISSION ###\n"
    "Analyser la situation (Contexte fourni dans le prompt) et décider du feedback.\n"
    
    "### PROCESSUS DE DÉCISION (Données déjà fournies) ###\n"
    "1. L'échange Docteur-Patient t'es donné.\n"
    "2. L'analyse de l'expert t'es donnée.\n"
    "3. Le profil étudiant t'es donné.\n"
    
    "### STRATÉGIE DE FEEDBACK OBLIGATOIRE ###\n"
    "   - CAS A (Analyse positive) : Donne un encouragement concis.\n"
    "   - CAS B (Analyse mitigée) : Stratégie SOCRATIQUE (Question guidante).\n"
    "   - CAS C (Erreur grave) : Stratégie DIRECTIVE (Correction).\n"
    "   - CAS D (Blocage) : Donne un indice sur la prochaine étape logique.\n\n"
    
    "Ton feedback doit être clair, constructif et pédagogique."
)

tuteur_agent = Agent(
    name="Tuteur_Intelligent",
    model=MODEL_NAME,
    description="Orchestre la pédagogie et fournit des feedbacks.",
    instruction=tuteur_instruction,
    # Optimisation radicale : Suppression des outils de lecture.
    # L'orchestrateur injecte tout le contexte nécessaire directement dans le prompt.
    tools=[consulter_expert_medical],
    output_key=KEY_TUTOR_FEEDBACK 
)