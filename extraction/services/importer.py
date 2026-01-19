"""
Service d'import des cas cliniques vers la base de données Django
Projet STI 5GI
"""

from typing import List, Dict, Tuple
from django.db import transaction
from module_expert.models import CasClinique, DomaineMedical
from .transformer import ClinicalCaseTransformer


class ClinicalCaseImporter:
    """
    Service pour importer les cas cliniques générés dans la base de données Django.
    """

    def __init__(self):
        self.transformer = ClinicalCaseTransformer()
        self._ensure_domains_exist()

    def _ensure_domains_exist(self):
        """Crée les domaines médicaux s'ils n'existent pas"""
        specialites = self.transformer.get_available_specialites()
        for specialite in specialites:
            DomaineMedical.objects.get_or_create(
                nom=specialite,
                defaults={"description": f"Domaine de {specialite}"}
            )

    def _get_or_create_domain(self, specialite: str) -> DomaineMedical:
        """Récupère ou crée un domaine médical"""
        domain, _ = DomaineMedical.objects.get_or_create(
            nom=specialite,
            defaults={"description": f"Domaine de {specialite}"}
        )
        return domain

    @transaction.atomic
    def import_cases(self, count: int = None, replace_existing: bool = False) -> Tuple[int, int, List[str]]:
        """
        Importe les cas cliniques générés dans la base de données.

        Args:
            count: Nombre de cas à générer (None = utiliser la config)
            replace_existing: Si True, supprime les cas existants générés

        Returns:
            Tuple (nombre_créés, nombre_ignorés, erreurs)
        """
        # Génération des cas
        cases_data = self.transformer.process(count)

        created = 0
        skipped = 0
        errors = []

        # Suppression des anciens cas générés si demandé
        if replace_existing:
            deleted_count, _ = CasClinique.objects.filter(
                source_fultang_id__startswith="GEN-"
            ).delete()
            print(f"Supprimé {deleted_count} cas existants")

        for case_data in cases_data:
            try:
                # Vérifier si le cas existe déjà (basé sur id_unique)
                if CasClinique.objects.filter(id_unique=case_data["id_unique"]).exists():
                    skipped += 1
                    continue

                # Récupérer le domaine
                specialite = case_data.pop("specialite_medicale", "Médecine générale")
                domain = self._get_or_create_domain(specialite)

                # Créer le cas clinique
                CasClinique.objects.create(
                    domaine=domain,
                    **case_data
                )
                created += 1

            except Exception as e:
                errors.append(f"Erreur pour {case_data.get('id_unique', 'N/A')}: {str(e)}")

        return created, skipped, errors

    def import_from_json_file(self, filepath: str) -> Tuple[int, int, List[str]]:
        """
        Importe des cas cliniques depuis un fichier JSON existant.

        Args:
            filepath: Chemin vers le fichier JSON

        Returns:
            Tuple (nombre_créés, nombre_ignorés, erreurs)
        """
        import json

        with open(filepath, 'r', encoding='utf-8') as f:
            cases_data = json.load(f)

        created = 0
        skipped = 0
        errors = []

        for case_raw in cases_data:
            try:
                # Convertir le format extraction vers format Django
                case_data = self._convert_extraction_format(case_raw)

                # Vérifier si le cas existe déjà
                id_unique = case_data.get("id_unique")
                if id_unique and CasClinique.objects.filter(id_unique=id_unique).exists():
                    skipped += 1
                    continue

                # Récupérer le domaine
                specialite = case_data.pop("specialite_medicale", "Médecine générale")
                domain = self._get_or_create_domain(specialite)

                # Créer le cas clinique
                CasClinique.objects.create(
                    domaine=domain,
                    **case_data
                )
                created += 1

            except Exception as e:
                errors.append(f"Erreur: {str(e)}")

        return created, skipped, errors

    def _convert_extraction_format(self, raw_case: Dict) -> Dict:
        """Convertit un cas du format extraction vers le format Django"""

        # Mapping du statut
        status_mapping = {
            "en_attente": "EN_REVISION",
            "valide": "PUBLIE",
            "rejete": "REJETE"
        }

        # Mapping de la difficulté
        difficulty_mapping = {
            "debutant": "DEBUTANT",
            "intermediaire": "INTERMEDIAIRE",
            "expert": "EXPERT"
        }

        # Extraction des données personnelles
        donnees_perso = raw_case.get("donnees_personnelles", {})

        return {
            "id_unique": raw_case.get("id_unique"),
            "titre": f"Cas de {raw_case.get('pathologie_principale', 'inconnu')} - Patient {donnees_perso.get('age', '?')} ans",
            "statut": status_mapping.get(raw_case.get("status", "en_attente"), "EN_REVISION"),
            "difficulte": difficulty_mapping.get(raw_case.get("niveau_difficulte", "intermediaire"), "INTERMEDIAIRE"),
            "pathologie": raw_case.get("pathologie_principale", ""),
            "donnees_patient": donnees_perso,
            "motif_consultation": raw_case.get("motif_consultation", ""),
            "mode_de_vie": raw_case.get("mode_de_vie", {}),
            "antecedents_medicaux": raw_case.get("antecedents_medicaux", {}),
            "symptomes": raw_case.get("symptomes", []),
            "diagnostics_physiques": raw_case.get("diagnostic_physique", []),
            "examens_complementaires": raw_case.get("examens_complementaires", []),
            "diagnostic_final": raw_case.get("diagnostic_final", ""),
            "traitement": raw_case.get("ordonnance_ideale", []),
            "objectifs_pedagogiques": raw_case.get("objectifs_pedagogiques", []),
            "indices_cliniques": raw_case.get("indices_cliniques", []),
            "erreurs_courantes": raw_case.get("erreurs_courantes", []),
            "specialite_medicale": raw_case.get("specialite_medicale", "Médecine générale"),
            "source_fultang_id": raw_case.get("hash_authentification", "")
        }

    def get_statistics(self) -> Dict:
        """Retourne des statistiques sur les cas importés"""
        from django.db.models import Count

        total = CasClinique.objects.count()
        generated = CasClinique.objects.filter(source_fultang_id__startswith="GEN-").count()

        by_status = dict(CasClinique.objects.values('statut').annotate(count=Count('id')))
        by_domain = dict(CasClinique.objects.values('domaine__nom').annotate(count=Count('id')))
        by_difficulty = dict(CasClinique.objects.values('difficulte').annotate(count=Count('id')))

        return {
            "total": total,
            "generated": generated,
            "by_status": by_status,
            "by_domain": by_domain,
            "by_difficulty": by_difficulty
        }
