"""
Commande Django pour importer les cas cliniques

Usage:
    python manage.py import_cases --count 50
    python manage.py import_cases --replace
    python manage.py import_cases --from-file /path/to/file.json
"""

from django.core.management.base import BaseCommand, CommandError
from extraction.services.importer import ClinicalCaseImporter


class Command(BaseCommand):
    help = 'Importe des cas cliniques générés dans la base de données'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            help='Nombre de cas à générer (défaut: selon configuration)',
        )
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Remplacer les cas générés existants',
        )
        parser.add_argument(
            '--from-file',
            type=str,
            help='Importer depuis un fichier JSON existant',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Initialisation de l\'importeur...'))

        try:
            importer = ClinicalCaseImporter()

            if options['from_file']:
                # Import depuis fichier
                self.stdout.write(f"Import depuis: {options['from_file']}")
                created, skipped, errors = importer.import_from_json_file(options['from_file'])
            else:
                # Génération et import
                count = options['count']
                replace = options['replace']

                if replace:
                    self.stdout.write(self.style.WARNING('Mode remplacement activé'))

                self.stdout.write(f"Génération de {count or 'N'} cas cliniques...")
                created, skipped, errors = importer.import_cases(
                    count=count,
                    replace_existing=replace
                )

            # Rapport
            self.stdout.write(self.style.SUCCESS(f'\nRésultat:'))
            self.stdout.write(f'  - Cas créés: {created}')
            self.stdout.write(f'  - Cas ignorés (déjà existants): {skipped}')

            if errors:
                self.stdout.write(self.style.ERROR(f'  - Erreurs: {len(errors)}'))
                for error in errors[:5]:  # Afficher les 5 premières erreurs
                    self.stdout.write(f'    {error}')

            # Statistiques finales
            stats = importer.get_statistics()
            self.stdout.write(f'\nTotal en base: {stats["total"]} cas cliniques')

        except Exception as e:
            raise CommandError(f'Erreur lors de l\'import: {str(e)}')
