"""
Transformer - Générateur de Cas Cliniques pour Django
Projet STI 5GI

Ce module génère des cas cliniques à partir des fichiers JSON
et les prépare pour l'import dans la base de données Django.
"""

import json
import uuid
import random
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any


class ClinicalCaseTransformer:
    """
    Transformateur qui génère des cas cliniques à partir des fichiers JSON.
    Utilise une logique probabiliste pour la distribution des cas.

    Fichiers requis dans le dossier data/:
    - pathologies_knowledge.json
    - patients_templates.json
    - contexte_cameroun.json
    """

    def __init__(self, data_folder: str = None):
        if data_folder is None:
            # Chemin par défaut relatif à ce fichier
            data_folder = Path(__file__).parent / "data"
        self.data_folder = Path(data_folder)

        # Chargement des 3 fichiers JSON
        self.pathologies = self._load_json("pathologies_knowledge.json")
        self.patients_templates = self._load_json("patients_templates.json")
        self.contexte = self._load_json("contexte_cameroun.json")

        # Hash source pour traçabilité
        self.source_hash = self._generate_source_hash()

    def _load_json(self, filename: str) -> Dict:
        """Charge un fichier JSON depuis le dossier data"""
        filepath = self.data_folder / filename
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Fichier non trouvé: {filepath}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Erreur JSON dans {filename}: {e}")

    def _generate_source_hash(self) -> str:
        """Génère un hash unique basé sur les fichiers source"""
        combined = json.dumps({
            "pathologies": list(self.pathologies.keys()),
            "timestamp": datetime.now().isoformat()
        }, sort_keys=True)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _generate_id(self, index: int) -> str:
        """Génère un ID unique anonymisé"""
        unique_str = f"{index}-{self.source_hash}-{uuid.uuid4().hex[:4]}"
        return f"CASE-{hashlib.md5(unique_str.encode()).hexdigest()[:8].upper()}"

    def _pick_weighted_option(self, options_dict: Dict) -> str:
        """Choisit une option au hasard en respectant les pourcentages"""
        choices = list(options_dict.keys())
        weights = []

        for key in choices:
            val = options_dict[key]
            if isinstance(val, dict) and "poids" in val:
                weights.append(val["poids"])
            else:
                weights.append(val)

        return random.choices(choices, weights=weights, k=1)[0]

    def _get_random_profession(self, categorie_age: str) -> str:
        """Retourne une profession aléatoire selon la catégorie d'âge"""
        professions_map = self.contexte["professions_par_age"]

        if categorie_age == "jeune_adulte":
            professions = professions_map.get("jeune_adulte", ["Étudiant(e)"])
        elif categorie_age == "senior":
            professions = professions_map.get("senior", ["Retraité(e)"])
        else:
            professions = professions_map.get("adulte", ["Commerçant(e)"])

        return random.choice(professions)

    def _generate_mode_vie(self, categorie_age: str) -> Dict:
        """Génère un mode de vie réaliste"""
        habitat = random.choice(self.contexte["habitats"])
        habitat_key = habitat.replace("é", "e")
        qualites_eau = self.contexte["qualite_eau_par_habitat"].get(
            habitat_key, ["Eau du robinet"]
        )

        # Moustiquaire selon habitat
        if habitat == "rural":
            moustiquaire = random.choice([True, False, False])
        elif habitat == "périurbain":
            moustiquaire = random.choice([True, True, False])
        else:
            moustiquaire = random.choice([True, True, True, False])

        # Voyages (40% de chance)
        voyages = []
        if random.random() < 0.4:
            lieu = random.choice(self.contexte["lieux_voyage_frequents"])
            voyages.append({
                "lieu": lieu,
                "duree": random.choice(["1 semaine", "2 semaines", "1 mois"]),
                "date": "Récent"
            })

        # Addictions (20% de chance)
        addictions = []
        if random.random() < 0.2:
            addiction_data = random.choice(self.contexte["addictions_courantes"])
            addictions.append({
                "nom": addiction_data["nom"],
                "quantite": random.choice(addiction_data["quantites"])
            })

        return {
            "qualite_eau": random.choice(qualites_eau),
            "moustiquaire": moustiquaire,
            "type_habitat": habitat,
            "voyages": voyages,
            "addictions": addictions,
            "activites_physiques": []
        }

    def _generate_antecedents(self, categorie_age: str, pathologie_key: str) -> Dict:
        """Génère des antécédents médicaux cohérents"""
        antecedents = {
            "antecedents_familiaux": [],
            "allergies": [],
            "maladies": [],
            "chirurgies": [],
            "vaccinations": []
        }

        # Antécédents familiaux
        if pathologie_key in ["hypertension_arterielle", "diabete"] and random.random() < 0.6:
            antecedents["antecedents_familiaux"] = [random.choice([
                "HTA chez le père",
                "HTA chez la mère",
                "Diabète chez le père",
                "Diabète chez la mère"
            ])]
        elif random.random() < 0.2:
            antecedents["antecedents_familiaux"] = [random.choice(
                self.contexte["antecedents_familiaux_courants"]
            )]

        # Allergies (15% de chance)
        if random.random() < 0.15:
            allergie_data = random.choice(self.contexte["allergies_courantes"])
            antecedents["allergies"] = [{
                "nom": allergie_data["nom"],
                "manifestation": allergie_data["manifestation"]
            }]

        # Maladies chroniques (seniors et adultes, 25% de chance)
        if categorie_age in ["senior", "adulte"] and random.random() < 0.25:
            maladie_data = random.choice(self.contexte["maladies_chroniques_courantes"])
            antecedents["maladies"] = [{
                "nom": maladie_data["nom"],
                "observation": maladie_data["observation"]
            }]

        # Vaccinations (50% de chance)
        if random.random() < 0.5:
            nb_vaccins = random.randint(1, 3)
            antecedents["vaccinations"] = random.sample(
                self.contexte["vaccinations_courantes"],
                min(nb_vaccins, len(self.contexte["vaccinations_courantes"]))
            )

        return antecedents

    def _generate_symptomes(self, pathologie_data: Dict) -> List[Dict]:
        """Génère une liste de symptômes variés pour la pathologie"""
        symptomes_possibles = pathologie_data["symptomes_possibles"]

        nb_symptomes = random.randint(2, min(4, len(symptomes_possibles)))
        symptomes_selectionnes = random.sample(symptomes_possibles, nb_symptomes)

        symptomes = []
        for s in symptomes_selectionnes:
            symptomes.append({
                "nom": s["nom"],
                "localisation": s.get("localisation"),
                "degre": s.get("degre"),
                "duree": s.get("duree"),
                "frequence": s.get("frequence"),
                "evolution": s.get("evolution"),
                "description_patient": s.get("description_patient", f"J'ai {s['nom'].lower()}")
            })

        return symptomes

    def _generate_ordonnance(self, pathologie_data: Dict) -> List[Dict]:
        """Génère l'ordonnance idéale"""
        lignes = []
        for t in pathologie_data.get("traitement_attendu", []):
            lignes.append({
                "nom_medicament": t["nom_medicament"],
                "dosage": t["dosage"],
                "forme": t.get("forme", "Non spécifié"),
                "frequence": t["frequence"],
                "duree": t["duree"],
                "voie": t.get("voie", "Orale"),
                "consigne": t.get("consigne", "")
            })
        return lignes

    def _generate_examens(self, pathologie_data: Dict) -> List[Dict]:
        """Génère les examens complémentaires"""
        examens = []
        for exam in pathologie_data.get("examens", []):
            examens.append({
                "nom": exam["nom"],
                "resultat": exam["resultat_positif"],
                "interpretation": exam.get("interpretation"),
                "valeur_normale": exam.get("valeur_normale"),
                "anatomie": exam.get("anatomie")
            })
        return examens

    def _generate_diagnostics_physiques(self, pathologie_data: Dict) -> List[Dict]:
        """Génère les diagnostics physiques avec variation"""
        diagnostics = []
        for diag in pathologie_data.get("diagnostics_physiques", []):
            valeur = diag["resultat"]

            # Variation pour les températures
            if "°C" in valeur and "-" not in valeur:
                try:
                    base_temp = float(valeur.replace("°C", ""))
                    variation = random.uniform(-0.3, 0.3)
                    valeur = f"{base_temp + variation:.1f}°C"
                except:
                    pass

            diagnostics.append({
                "nom": diag["nom"],
                "resultat": valeur
            })
        return diagnostics

    def _map_difficulty_to_django(self, niveau: str) -> str:
        """Mappe le niveau de difficulté vers les choix Django"""
        mapping = {
            "debutant": "DEBUTANT",
            "intermediaire": "INTERMEDIAIRE",
            "expert": "EXPERT",
            "avance": "AVANCE"
        }
        return mapping.get(niveau.lower(), "INTERMEDIAIRE")

    def transform_single_patient(self, virtual_template: Dict, domaine_id: str = None) -> Dict:
        """Transforme un template virtuel en dictionnaire prêt pour Django"""

        pathologie_key = virtual_template["pathologie"]
        pathologie_data = self.pathologies[pathologie_key]
        categorie_age = virtual_template["categorie_age"]
        sexe = virtual_template["sexe"]

        # Génération de l'âge
        age = random.randint(virtual_template["age_min"], virtual_template["age_max"])

        # Données personnelles (pour JSONField)
        donnees_patient = {
            "age": age,
            "sexe": sexe,
            "profession": self._get_random_profession(categorie_age),
            "groupe_sanguin": random.choice(self.contexte["groupes_sanguins"]),
            "region_origine": random.choice(self.contexte["regions"]),
            "etat_civil": random.choice(self.contexte["etats_civils"])
        }

        # Mode de vie
        mode_vie = self._generate_mode_vie(categorie_age)

        # Antécédents
        antecedents = self._generate_antecedents(categorie_age, pathologie_key)

        # Symptômes
        symptomes = self._generate_symptomes(pathologie_data)

        # Motif de consultation
        motif = symptomes[0]["description_patient"] if symptomes else pathologie_data["nom"]

        # Examens et diagnostics
        examens = self._generate_examens(pathologie_data)
        diagnostics_physiques = self._generate_diagnostics_physiques(pathologie_data)

        # Ordonnance
        ordonnance = self._generate_ordonnance(pathologie_data)

        # Dictionnaire prêt pour Django CasClinique
        return {
            "id_unique": self._generate_id(virtual_template["id"]),
            "titre": f"Cas de {pathologie_data['nom']} - Patient {age} ans",
            "statut": "EN_REVISION",  # Statut Django
            "difficulte": self._map_difficulty_to_django(pathologie_data["niveau_difficulte"]),
            "pathologie": pathologie_data["nom"],
            "donnees_patient": donnees_patient,
            "motif_consultation": motif,
            "mode_de_vie": mode_vie,
            "antecedents_medicaux": antecedents,
            "symptomes": symptomes,
            "diagnostics_physiques": diagnostics_physiques,
            "examens_complementaires": examens,
            "diagnostic_final": pathologie_data["nom"],
            "traitement": ordonnance,
            "objectifs_pedagogiques": [
                f"Reconnaître les signes de {pathologie_data['nom']}",
                "Prescrire les examens appropriés",
                "Établir un diagnostic différentiel"
            ],
            "indices_cliniques": pathologie_data.get("indices_cliniques", []),
            "erreurs_courantes": pathologie_data.get("erreurs_courantes", []),
            "specialite_medicale": pathologie_data.get("specialite", "Médecine générale"),
            "source_fultang_id": f"GEN-{self.source_hash}-{virtual_template['id']}"
        }

    def process(self, count: int = None) -> List[Dict]:
        """
        Génère les cas cliniques basé sur les probabilités définies.
        Retourne une liste de dictionnaires prêts pour Django.
        """
        try:
            config = self.patients_templates["configuration_generale"]
            dist_age = self.patients_templates["distribution_age"]
            dist_patho = self.patients_templates["distribution_pathologies"]
        except KeyError as e:
            raise ValueError(f"Clé manquante dans patients_templates.json: {e}")

        target_count = count or config["nombre_cas_a_generer"]
        cases = []

        for i in range(target_count):
            try:
                # Tirage au sort des caractéristiques
                cat_age = self._pick_weighted_option(dist_age)
                pathologie_key = self._pick_weighted_option(dist_patho)

                # Tirage du sexe
                sexe_ratio = config["repartition_sexe"]
                sexe = "F" if random.random() < sexe_ratio["F"] else "M"

                # Récupération des bornes d'âge
                age_rules = dist_age[cat_age]

                # Template virtuel
                virtual_template = {
                    "id": i + 1,
                    "pathologie": pathologie_key,
                    "categorie_age": cat_age,
                    "age_min": age_rules["min"],
                    "age_max": age_rules["max"],
                    "sexe": sexe
                }

                # Transformation
                cas = self.transform_single_patient(virtual_template)
                cases.append(cas)

            except Exception as e:
                print(f"Erreur cas #{i+1}: {e}")

        return cases

    def get_available_specialites(self) -> List[str]:
        """Retourne la liste des spécialités disponibles"""
        specialites = set()
        for patho_data in self.pathologies.values():
            if "specialite" in patho_data:
                specialites.add(patho_data["specialite"])
        return sorted(list(specialites))

    def get_available_pathologies(self) -> List[str]:
        """Retourne la liste des pathologies disponibles"""
        return sorted([p["nom"] for p in self.pathologies.values()])
