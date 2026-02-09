from django.core.management.base import BaseCommand
import time

class Command(BaseCommand):
    help = 'Диагностика доступности источников аниме'

    def handle(self, *args, **options):
        self.stdout.write('DIAGNOSTICS: Anime Sources')
        self.stdout.write('=' * 50)
        
        # Check AnimeParsers
        self.stdout.write('1. AnimeParsers check...')
        try:
            import anime_parsers_ru
            try:
                version = anime_parsers_ru.__version__
            except AttributeError:
                version = 'unknown'
            self.stdout.write(f'   OK: AnimeParsers v{version} installed')
        except ImportError:
            self.stdout.write('   ERROR: AnimeParsers not installed!')
            self.stdout.write('   Install: pip install anime-parsers-ru')
            return
        
        # Test Shikimori
        self.stdout.write('')
        self.stdout.write('2. Shikimori test...')
        try:
            from anime_parsers_ru import ShikimoriParser
            parser = ShikimoriParser()
            
            print('   Search "Naruto"...')
            results = parser.search('Naruto')
            
            if results and len(results) > 0:
                self.stdout.write(f'   OK: Shikimori works! Found {len(results)} results')
                self.stdout.write(f'   Example: {results[0].get("title", "Unknown")}')
            else:
                self.stdout.write('   WARNING: Shikimori: no results')
                
        except Exception as e:
            self.stdout.write(f'   ERROR: Shikimori error: {e}')
        
        # Test AniBoom
        self.stdout.write('')
        self.stdout.write('3. AniBoom test...')
        try:
            from anime_parsers_ru import AniboomParser
            parser = AniboomParser()
            
            # Try fast search
            print('   Fast search "Naruto"...')
            results = parser.fast_search('Naruto')
            
            if results and len(results) > 0:
                self.stdout.write(f'   OK: AniBoom fast search works! Found {len(results)} results')
                self.stdout.write(f'   Example: {results[0].get("title", "Unknown")}')
            else:
                self.stdout.write('   WARNING: AniBoom fast search: no results')
            
            # Try normal search
            print('   Normal search "Naruto"...')
            time.sleep(1)  # Pause between requests
            results = parser.search('Naruto')
            
            if results and len(results) > 0:
                self.stdout.write(f'   OK: AniBoom normal search works! Found {len(results)} results')
            else:
                self.stdout.write('   ERROR: AniBoom normal search: no results')
                
        except Exception as e:
            self.stdout.write(f'   ERROR: AniBoom error: {e}')
        
        # Test Kodik
        self.stdout.write('')
        self.stdout.write('4. Kodik test...')
        try:
            from anime_parsers_ru import KodikParser
            parser = KodikParser()
            
            # Try to get list (limited)
            print('   Getting anime list...')
            anime_list, next_page_id = parser.get_list(
                limit_per_page=5,
                pages_to_parse=1,
                include_material_data=False,
                only_anime=True
            )
            
            if anime_list and len(anime_list) > 0:
                self.stdout.write(f'   OK: Kodik works! Found {len(anime_list)} anime')
                self.stdout.write(f'   Example: {anime_list[0].get("title", "Unknown")}')
            else:
                self.stdout.write('   WARNING: Kodik: empty list')
                
        except Exception as e:
            self.stdout.write(f'   ERROR: Kodik error: {e}')
        
        # Recommendations
        self.stdout.write('')
        self.stdout.write('RECOMMENDATIONS:')
        
        # Determine best source
        working_sources = []
        
        try:
            from anime_parsers_ru import ShikimoriParser
            parser = ShikimoriParser()
            results = parser.search('Test')
            if results:
                working_sources.append('shikimori')
        except:
            pass
            
        try:
            from anime_parsers_ru import AniboomParser
            parser = AniboomParser()
            results = parser.fast_search('Test')
            if results:
                working_sources.append('aniboom')
        except:
            pass
            
        try:
            from anime_parsers_ru import KodikParser
            parser = KodikParser()
            results = parser.get_list(limit_per_page=1)
            if results[0]:
                working_sources.append('kodik')
        except:
            pass
        
        if working_sources:
            self.stdout.write(f'   RECOMMENDED SOURCE: {working_sources[0]}')
            self.stdout.write(f'   AVAILABLE SOURCES: {", ".join(working_sources)}')
            
            if 'shikimori' in working_sources:
                self.stdout.write('')
                self.stdout.write('   IMPORT COMMANDS:')
                self.stdout.write('      python manage.py import_popular_anime --source shikimori')
                self.stdout.write('      python manage.py import_all_anime --sources shikimori')
                
            if 'aniboom' in working_sources:
                self.stdout.write('')
                self.stdout.write('   SEARCH SPECIFIC ANIME:')
                self.stdout.write('      python manage.py import_all_anime --sources aniboom --search "Naruto"')
                
        else:
            self.stdout.write('   ERROR: No sources available!')
            self.stdout.write('   POSSIBLE REASONS:')
            self.stdout.write('      • Internet connection issues')
            self.stdout.write('      • API blocking')
            self.stdout.write('      • Changes in source APIs')
            self.stdout.write('   SOLUTIONS:')
            self.stdout.write('      • Check internet connection')
            self.stdout.write('      • Try later')
            self.stdout.write('      • Use VPN')
        
        self.stdout.write('')
        self.stdout.write('Diagnostics completed!')