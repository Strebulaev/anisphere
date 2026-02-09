from django.core.management.base import BaseCommand
from parsers.animeparsers import AnimeParsersCollector

class Command(BaseCommand):
    help = 'Import anime through AnimeParsers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            choices=['kodik', 'shikimori', 'aniboom', 'all'],
            default='all',
            help='Source for import'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Number of items per page (for Kodik)'
        )
        parser.add_argument(
            '--pages',
            type=int,
            default=1,
            help='Number of pages to process (for Kodik)'
        )
        parser.add_argument(
            '--search',
            type=str,
            help='Search query (for AniBoom)'
        )
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Quiet mode (less output)'
        )

    def handle(self, *args, **options):
        collector = AnimeParsersCollector()
        source = options['source']
        quiet = options['quiet']
        
        if not quiet:
            self.stdout.write(self.style.SUCCESS('AnimeCore - Anime import through AnimeParsers'))
            self.stdout.write('=' * 50)
        
        total_imported = 0
        total_updated = 0
        total_errors = 0
        
        # Import from Kodik
        if source in ['kodik', 'all']:
            if not quiet:
                self.stdout.write(self.style.SUCCESS('Import from Kodik...'))
            try:
                result = collector.import_from_kodik(
                    limit_per_page=options['limit'],
                    pages_to_parse=options['pages']
                )
                self._print_result('Kodik', result, quiet)
                total_imported += result['imported']
                total_updated += result['updated']
                total_errors += result['errors']
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Critical error Kodik: {e}'))
                total_errors += 1
        
        # Import from Shikimori
        if source in ['shikimori', 'all']:
            if not quiet:
                self.stdout.write(self.style.SUCCESS('Import from Shikimori...'))
            try:
                result = collector.import_from_shikimori(page_limit=2)  # Limit for stability
                self._print_result('Shikimori', result, quiet)
                total_imported += result['imported']
                total_updated += result['updated']
                total_errors += result['errors']
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Critical error Shikimori: {e}'))
                total_errors += 1
        
        # Import from AniBoom
        if source in ['aniboom', 'all']:
            if not quiet:
                self.stdout.write(self.style.SUCCESS('Import from AniBoom...'))
            try:
                result = collector.import_from_aniboom(search_query=options['search'])
                self._print_result('AniBoom', result, quiet)
                total_imported += result['imported']
                total_updated += result['updated']
                total_errors += result['errors']
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Critical error AniBoom: {e}'))
                total_errors += 1
        
        # Final result
        if not quiet:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('FINAL RESULT'))
            self.stdout.write('=' * 50)
            self.stdout.write(f'Created anime: {total_imported}')
            self.stdout.write(f'Updated anime: {total_updated}')
            self.stdout.write(f'Errors: {total_errors}')
            
            if total_errors > 0:
                self.stdout.write('')
                self.stdout.write(self.style.WARNING('Errors:'))
                for i, error in enumerate(collector.errors[:10]):  # Show first 10 errors
                    self.stdout.write(f'  {i+1}. {error}')
                
                if len(collector.errors) > 10:
                    self.stdout.write(f'  ... and {len(collector.errors) - 10} more errors')
        
        # Final message
        if total_imported > 0:
            if not quiet:
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('Import completed successfully!'))
                self.stdout.write('You can now start the server: python manage.py runserver')
        else:
            self.stdout.write(self.style.WARNING('No anime were imported. Check errors above.'))
    
    def _print_result(self, source: str, result: dict, quiet: bool = False):
        """Print import result"""
        if quiet:
            if result['imported'] > 0:
                self.stdout.write(f'{source}: +{result["imported"]} (updated: {result["updated"]})')
        else:
            if result['imported'] > 0:
                self.stdout.write(self.style.SUCCESS(f'Created {result["imported"]} anime'))
            if result['updated'] > 0:
                self.stdout.write(self.style.WARNING(f'Updated {result["updated"]} anime'))
            if result['errors'] > 0:
                self.stdout.write(self.style.ERROR(f'{result["errors"]} errors'))