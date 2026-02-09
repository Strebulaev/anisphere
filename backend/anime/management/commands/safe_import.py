from django.core.management.base import BaseCommand
from parsers.animeparsers import AnimeParsersCollector

class Command(BaseCommand):
    help = 'Safe anime import (only from reliable sources)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Number of anime to import'
        )
        parser.add_argument(
            '--source',
            type=str,
            choices=['shikimori', 'all'],
            default='shikimori',
            help='Source for import'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreate existing anime'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Safe anime import'))
        self.stdout.write('=' * 50)
        
        collector = AnimeParsersCollector()
        limit = options['limit']
        source = options['source']
        
        if source == 'shikimori':
            self.stdout.write('Import only from Shikimori (most reliable source)')
            
            try:
                # Import limited amount
                result = collector.import_from_shikimori(page_limit=1)
                
                self.stdout.write(self.style.SUCCESS(f'Import result:'))
                self.stdout.write(f'   Created: {result["imported"]} anime')
                self.stdout.write(f'   Updated: {result["updated"]} anime')
                self.stdout.write(f'   Errors: {result["errors"]}')
                
                if result['errors'] == 0:
                    self.stdout.write(self.style.SUCCESS('Import completed without errors!'))
                else:
                    self.stdout.write(self.style.WARNING(f'There were errors. Check logs above.'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Critical error: {e}'))
                return
        
        elif source == 'all':
            self.stdout.write('Import from all sources (be careful!)')
            
            # First try Shikimori
            try:
                result = collector.import_from_shikimori(page_limit=1)
                self.stdout.write(self.style.SUCCESS(f'Shikimori: +{result["imported"]} anime'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Shikimori unavailable: {e}'))
            
            # Then try AniBoom (only search)
            try:
                result = collector.import_from_aniboom(search_query='Наруто')
                self.stdout.write(self.style.SUCCESS(f'AniBoom: +{result["imported"]} anime'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'AniBoom unavailable: {e}'))
        
        # Show statistics
        from anime.models import Anime
        total = Anime.objects.count()
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Statistics:'))
        self.stdout.write(f'   Total anime in database: {total}')
        
        if total > 0:
            # Show recently added
            recent = Anime.objects.order_by('-created_at')[:5]
            self.stdout.write('   Recently added:')
            for anime in recent:
                self.stdout.write(f'     • {anime.title_ru} ({anime.year or "N/A"})')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Safe import completed!'))
        self.stdout.write('You can now start the server: python manage.py runserver')