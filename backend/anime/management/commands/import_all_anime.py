from django.core.management.base import BaseCommand
from parsers.animeparsers import AnimeParsersCollector

class Command(BaseCommand):
    help = 'Полный импорт аниме из всех источников (рекомендуется)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=1000,
            help='Максимальное количество аниме для импорта'
        )
        parser.add_argument(
            '--sources',
            nargs='+',
            choices=['kodik', 'shikimori', 'aniboom'],
            default=['shikimori', 'aniboom'],
            help='Источники для импорта'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительно пересоздать существующие аниме'
        )
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Тихий режим (меньше вывода)'
        )

    def handle(self, *args, **options):
        if not options['quiet']:
            self.stdout.write('FULL ANIME IMPORT')
            self.stdout.write('=' * 60)
            self.stdout.write('This process may take several minutes...')
            self.stdout.write('')
        
        collector = AnimeParsersCollector()
        sources = options['sources']
        limit = options['limit']
        
        total_stats = {
            'imported': 0,
            'updated': 0,
            'errors': 0,
            'sources_processed': 0,
            'detailed_errors': []
        }
        
        # Check available sources
        available_sources = []
        if 'shikimori' in sources:
            available_sources.append('shikimori')
        if 'kodik' in sources:
            available_sources.append('kodik')
        if 'aniboom' in sources:
            available_sources.append('aniboom')
        
        if not available_sources:
            self.stdout.write(self.style.ERROR('No available sources specified'))
            return
        
        if not options['quiet']:
            self.stdout.write(f'Sources for import: {", ".join(available_sources)}')
            self.stdout.write(f'Limit: {limit}')
            self.stdout.write('')
        
        # Import from each source
        for source in available_sources:
            try:
                if not options['quiet']:
                    self.stdout.write(f'Import from {source.upper()}...')
                
                if source == 'shikimori':
                    # Shikimori - most reliable source
                    pages_to_import = min(3, max(1, limit // 20))  # ~20 anime per page
                    if not options['quiet']:
                        self.stdout.write(f'   Pages to import: {pages_to_import}')
                    
                    result = collector.import_from_shikimori(page_limit=pages_to_import)
                    
                elif source == 'kodik':
                    # Kodik - may require token
                    pages_to_import = min(2, max(1, limit // 50))  # ~50 anime per page
                    if not options['quiet']:
                        self.stdout.write(f'   Pages to import: {pages_to_import}')
                    
                    result = collector.import_from_kodik(
                        limit_per_page=50,
                        pages_to_parse=pages_to_import
                    )
                    
                elif source == 'aniboom':
                    # AniBoom - search by popular queries
                    if not options['quiet']:
                        self.stdout.write('   Search by popular queries...')
                    
                    popular_queries = [
                        'Naruto', 'Bleach', 'One Punch Man', 'Attack on Titan',
                        'My Hero Academia', 'Jujutsu Kaisen', 'Demon Slayer',
                        'Fullmetal Alchemist', 'Death Note', 'Evangelion',
                        'Cowboy Bebop', 'One Punch Man', 'Hunter x Hunter'
                    ]
                    
                    # Take queries depending on limit
                    queries_to_use = popular_queries[:min(len(popular_queries), limit // 5)]
                    if not options['quiet']:
                        self.stdout.write(f'   Queries to search: {len(queries_to_use)}')
                    
                    result = {'imported': 0, 'updated': 0, 'errors': 0}
                    
                    for i, query in enumerate(queries_to_use, 1):
                        try:
                            if not options['quiet']:
                                self.stdout.write(f'   [{i}/{len(queries_to_use)}] Search "{query}"...')
                            
                            query_result = collector.import_from_aniboom(search_query=query)
                            imported = query_result.get('imported', 0)
                            updated = query_result.get('updated', 0)
                            errors = query_result.get('errors', 0)
                            
                            result['imported'] += imported
                            result['updated'] += updated
                            result['errors'] += errors
                            
                            if not options['quiet']:
                                if imported > 0:
                                    self.stdout.write(f'      OK: Found {imported} anime')
                                elif updated > 0:
                                    self.stdout.write(f'      UPDATE: Updated {updated} anime')
                                elif errors > 0:
                                    self.stdout.write(f'      ERROR: {errors} errors')
                                else:
                                    self.stdout.write(f'      WARNING: Nothing found')
                            
                            # Pause between requests
                            import time
                            time.sleep(1)
                            
                        except Exception as e:
                            error_msg = f'Search error "{query}": {str(e)}'
                            if not options['quiet']:
                                self.stdout.write(f'      ERROR: {error_msg}')
                            total_stats['detailed_errors'].append(f'{source}: {error_msg}')
                            result['errors'] += 1
                
                # Update statistics
                total_stats['imported'] += result.get('imported', 0)
                total_stats['updated'] += result.get('updated', 0)
                total_stats['errors'] += result.get('errors', 0)
                total_stats['sources_processed'] += 1
                
                if not options['quiet']:
                    if result.get('imported', 0) > 0:
                        self.stdout.write(self.style.SUCCESS(f'OK {source}: +{result["imported"]} anime'))
                    if result.get('updated', 0) > 0:
                        self.stdout.write(self.style.WARNING(f'UPDATE {source}: updated {result["updated"]} anime'))
                    if result.get('errors', 0) > 0:
                        self.stdout.write(self.style.ERROR(f'ERROR {source}: {result["errors"]} errors'))
                    self.stdout.write('')
                
                # Small pause between sources
                import time
                time.sleep(1)
                
            except Exception as e:
                error_msg = f'Critical error {source}: {str(e)}'
                if not options['quiet']:
                    self.stdout.write(self.style.ERROR(f'ERROR: {error_msg}'))
                total_stats['detailed_errors'].append(error_msg)
                total_stats['errors'] += 1
        
        # Final statistics
        from anime.models import Anime
        final_count = Anime.objects.count()
        
        if not options['quiet']:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('FINAL STATISTICS'))
            self.stdout.write('=' * 60)
            self.stdout.write(f'OK Created anime: {total_stats["imported"]}')
            self.stdout.write(f'UPDATE Updated anime: {total_stats["updated"]}')
            self.stdout.write(f'ERROR Errors: {total_stats["errors"]}')
            self.stdout.write(f'PROCESSED Sources: {total_stats["sources_processed"]}')
            self.stdout.write(f'TOTAL Anime in DB: {final_count}')
            self.stdout.write('')
            
            # Show detailed errors
            if total_stats['detailed_errors'] and not options['quiet']:
                self.stdout.write(self.style.WARNING('DETAILED ERRORS:'))
                for i, error in enumerate(total_stats['detailed_errors'][:10], 1):
                    self.stdout.write(f'  {i}. {error}')
                if len(total_stats['detailed_errors']) > 10:
                    self.stdout.write(f'  ... and {len(total_stats["detailed_errors"]) - 10} more errors')
                self.stdout.write('')
            
            if total_stats['errors'] == 0:
                self.stdout.write(self.style.SUCCESS('IMPORT COMPLETED SUCCESSFULLY!'))
            else:
                self.stdout.write(self.style.WARNING(f'IMPORT COMPLETED WITH {total_stats["errors"]} ERRORS'))
                self.stdout.write('Check logs above for details')
        
        # Recommendations
        if not options['quiet']:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('NEXT STEPS:'))
            self.stdout.write('   • Start server: python manage.py runserver')
            self.stdout.write('   • Open http://anisphere.ru/anime/')
            self.stdout.write('   • Check imported anime')
            
            if total_stats['imported'] == 0:
                self.stdout.write('')
                self.stdout.write(self.style.WARNING('NO ANIME WAS IMPORTED!'))
                self.stdout.write('Possible reasons:')
                self.stdout.write('   • All anime already exist in DB')
                self.stdout.write('   • API sources unavailable')
                self.stdout.write('   • Network issues')
                self.stdout.write('   • Insufficient access rights')
                self.stdout.write('')
                self.stdout.write('Run diagnostics:')
                self.stdout.write('   python manage.py diagnose_sources')
        
        return f"Imported: {total_stats['imported']}, updated: {total_stats['updated']}, errors: {total_stats['errors']}"