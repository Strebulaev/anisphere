from django.core.management.base import BaseCommand
from parsers.animeparsers import AnimeParsersCollector

class Command(BaseCommand):
    help = 'Test import of one anime to check functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--query',
            type=str,
            default='Наруто',
            help='Search query for testing'
        )
        parser.add_argument(
            '--source',
            type=str,
            choices=['shikimori', 'aniboom'],
            default='shikimori',
            help='Source for testing'
        )

    def handle(self, *args, **options):
        collector = AnimeParsersCollector()
        query = options['query']
        source = options['source']
        
        self.stdout.write(f'Test anime import')
        self.stdout.write(f'Search: "{query}" in source: {source}')
        self.stdout.write('=' * 50)
        
        try:
            if source == 'shikimori':
                # Test search through Shikimori
                from anime_parsers_ru import ShikimoriParser
                parser = ShikimoriParser()
                
                self.stdout.write('Search through Shikimori...')
                results = parser.search(query)
                
                if results:
                    self.stdout.write(f'Found {len(results)} results')
                    
                    # Process first result
                    anime_data = results[0]
                    self.stdout.write(f'Processing: {anime_data.get("title", "Unknown")}')
                    
                    result = collector._save_anime_data(anime_data, 'shikimori')
                    
                    if result == 'created':
                        self.stdout.write(self.style.SUCCESS('Anime successfully created!'))
                    elif result == 'updated':
                        self.stdout.write(self.style.WARNING('Anime updated'))
                    else:
                        self.stdout.write(self.style.ERROR('Failed to process anime'))
                        
                else:
                    self.stdout.write(self.style.WARNING('Nothing found'))
                    
            elif source == 'aniboom':
                # Test search through AniBoom
                from anime_parsers_ru import AniboomParser
                parser = AniboomParser()
                
                self.stdout.write('Search through AniBoom...')
                results = parser.fast_search(query)
                
                if results:
                    self.stdout.write(f'Found {len(results)} results')
                    
                    # Process first result
                    anime_data = results[0]
                    self.stdout.write(f'Processing: {anime_data.get("title", "Unknown")}')
                    
                    result = collector._save_anime_data(anime_data, 'aniboom')
                    
                    if result == 'created':
                        self.stdout.write(self.style.SUCCESS('Anime successfully created!'))
                    elif result == 'updated':
                        self.stdout.write(self.style.WARNING('Anime updated'))
                    else:
                        self.stdout.write(self.style.ERROR('Failed to process anime'))
                        
                else:
                    self.stdout.write(self.style.WARNING('Nothing found'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            import traceback
            traceback.print_exc()
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Test completed'))