from abc import ABC, abstractmethod
import random

class StrategieApprentissage(ABC):
    """
    Interface pour les stratégies d'apprentissage du Tuteur Intelligent.
    """
    
    @abstractmethod
    def generer_indice(self, contexte_clinique, etape_actuelle):
        """Génère un indice adapté à la stratégie."""
        pass

    @abstractmethod
    def choisir_prochaine_question(self, etape_actuelle):
        """Choisit la prochaine question à poser."""
        pass

    @abstractmethod
    def style_feedback(self):
        """Retourne le type de feedback (DIRECT, SOCRATIQUE, SCAFFOLDING)."""
        pass

class StrategieSocratique(StrategieApprentissage):
    """
    Stratégie qui pose des questions pour guider l'étudiant vers la réponse
    sans la donner directement.
    """
    def generer_indice(self, contexte_clinique, etape_actuelle):
        questions_indices = [
            "Quels éléments du dossier patient contredisent ton hypothèse ?",
            "Si tu regardes attentivement les constantes vitales, que remarques-tu ?",
            "Quel lien fais-tu entre ce symptôme et tes connaissances théoriques ?"
        ]
        return random.choice(questions_indices)

    def choisir_prochaine_question(self, etape_actuelle):
        return f"Pourquoi penses-tu que l'étape '{etape_actuelle}' est pertinente ici ?"

    def style_feedback(self):
        return "SOCRATIQUE"

class StrategieDirecte(StrategieApprentissage):
    """
    Stratégie qui donne des feedbacks clairs et correctifs immédiats.
    """
    def generer_indice(self, contexte_clinique, etape_actuelle):
        return f"Pour l'étape '{etape_actuelle}', concentre-toi sur les données : {list(contexte_clinique.keys())[:2]}."

    def choisir_prochaine_question(self, etape_actuelle):
        return f"Quel est le résultat attendu pour : {etape_actuelle} ?"

    def style_feedback(self):
        return "DIRECT"

class StrategieScaffolding(StrategieApprentissage):
    """
    Stratégie d'étayage : fournit beaucoup d'aide au début et réduit progressivement.
    """
    def generer_indice(self, contexte_clinique, etape_actuelle):
        return f"Rappel : Dans ce type de cas, on commence généralement par vérifier {etape_actuelle}. Regarde la valeur..."

    def choisir_prochaine_question(self, etape_actuelle):
        return f"Commençons ensemble. Quelle est la première chose à vérifier pour {etape_actuelle} ?"

    def style_feedback(self):
        return "SCAFFOLDING"
