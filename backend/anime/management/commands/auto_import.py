from django.core.management.base import BaseCommand
import time
from parsers.animeparsers import AnimeParsersCollector

class Command(BaseCommand):
    help = 'Автоматический импорт аниме из рабочих источников'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Максимальное количество аниме для импорта'
        )
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Тихий режим'
        )

    def handle(self, *args, **options):
        if not options['quiet']:
            self.stdout.write(self.style.SUCCESS('🤖 АВТОМАТИЧЕСКИЙ ИМПОРТ АНИМЕ'))
            self.stdout.write('=' * 50)
            self.stdout.write('Определение рабочих источников...')
            self.stdout.write('')
        
        # Определяем рабочие источники
        working_sources = self._find_working_sources(options['quiet'])
        
        if not working_sources:
            if not options['quiet']:
                self.stdout.write(self.style.ERROR('❌ Не найдено ни одного рабочего источника!'))
                self.stdout.write('💡 Запустите диагностику: python manage.py diagnose_sources')
            return
        
        if not options['quiet']:
            self.stdout.write(self.style.SUCCESS(f'✅ Найдено рабочих источников: {", ".join(working_sources)}'))
            self.stdout.write('')
        
        # Импортируем из рабочих источников
        collector = AnimeParsersCollector()
        limit = options['limit']
        
        total_stats = {
            'imported': 0,
            'updated': 0,
            'errors': 0
        }
        
        for source in working_sources:
            try:
                if not options['quiet']:
                    self.stdout.write(f'🔄 Импорт из {source.upper()}...')
                
                if source == 'shikimori':
                    pages = min(3, max(1, limit // 20))
                    result = collector.import_from_shikimori(page_limit=pages)
                    
                elif source == 'aniboom':
                    # Для AniBoom используем ограниченный поиск
                    popular_queries = ['Наруто', 'Блич', 'Атака титанов', 'Моя геройская академия']
                    queries_to_use = popular_queries[:min(len(popular_queries), limit // 10)]
                    
                    result = {'imported': 0, 'updated': 0, 'errors': 0}
                    for query in queries_to_use:
                        try:
                            query_result = collector.import_from_aniboom(search_query=query)
                            result['imported'] += query_result.get('imported', 0)
                            result['updated'] += query_result.get('updated', 0)
                            result['errors'] += query_result.get('errors', 0)
                            time.sleep(1)
                        except Exception as e:
                            if not options['quiet']:
                                self.stdout.write(self.style.WARNING(f'⚠️ Ошибка "{query}": {e}'))
                            result['errors'] += 1
                            
                elif source == 'kodik':
                    pages = min(2, max(1, limit // 50))
                    result = collector.import_from_kodik(
                        limit_per_page=50,
                        pages_to_parse=pages
                    )
                
                # Обновляем статистику
                total_stats['imported'] += result.get('imported', 0)
                total_stats['updated'] += result.get('updated', 0)
                total_stats['errors'] += result.get('errors', 0)
                
                if not options['quiet']:
                    if result.get('imported', 0) > 0:
                        self.stdout.write(self.style.SUCCESS(f'✅ {source}: +{result["imported"]} аниме'))
                    if result.get('updated', 0) > 0:
                        self.stdout.write(self.style.WARNING(f'🔄 {source}: обновлено {result["updated"]} аниме'))
                    if result.get('errors', 0) > 0:
                        self.stdout.write(self.style.ERROR(f'❌ {source}: {result["errors"]} ошибок'))
                    self.stdout.write('')
                
                time.sleep(1)  # Пауза между источниками
                
            except Exception as e:
                if not options['quiet']:
                    self.stdout.write(self.style.ERROR(f'❌ Критическая ошибка {source}: {e}'))
                total_stats['errors'] += 1
        
        # Финальная статистика
        from anime.models import Anime
        final_count = Anime.objects.count()
        
        if not options['quiet']:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('📊 РЕЗУЛЬТАТ'))
            self.stdout.write('=' * 50)
            self.stdout.write(f'✅ Создано: {total_stats["imported"]} аниме')
            self.stdout.write(f'🔄 Обновлено: {total_stats["updated"]} аниме')
            self.stdout.write(f'❌ Ошибок: {total_stats["errors"]}')
            self.stdout.write(f'📈 Всего в базе: {final_count}')
            self.stdout.write('')
            
            if total_stats['errors'] == 0:
                self.stdout.write(self.style.SUCCESS('🎉 Автоимпорт завершен успешно!'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️ Завершено с {total_stats["errors"]} ошибками'))
            
            self.stdout.write('')
            self.stdout.write('💡 Следующие шаги:')
            self.stdout.write('   • python manage.py runserver')
            self.stdout.write('   • http://localhost:3000/anime/')
        
        return f"Автоимпорт: {total_stats['imported']} создано, {total_stats['updated']} обновлено, {total_stats['errors']} ошибок"
    
    def _find_working_sources(self, quiet=False):
        """Определяет какие источники работают"""
        working_sources = []
        
        # Тест Shikimori
        try:
            if not quiet:
                print('   🔍 Тест Shikimori...')
            from anime_parsers_ru import ShikimoriParser
            parser = ShikimoriParser()
            results = parser.search('Тест')
            if results and len(results) > 0:
                working_sources.append('shikimori')
                if not quiet:
                    print('      ✅ Shikimori работает')
            else:
                if not quiet:
                    print('      ⚠️ Shikimori: нет результатов')
        except Exception as e:
            if not quiet:
                print(f'      ❌ Shikimori: {e}')
        
        # Тест AniBoom
        try:
            if not quiet:
                print('   🔍 Тест AniBoom...')
            from anime_parsers_ru import AniboomParser
            parser = AniboomParser()
            results = parser.fast_search('Тест')
            if results and len(results) > 0:
                working_sources.append('aniboom')
                if not quiet:
                    print('      ✅ AniBoom работает')
            else:
                if not quiet:
                    print('      ⚠️ AniBoom: нет результатов')
        except Exception as e:
            if not quiet:
                print(f'      ❌ AniBoom: {e}')
        
        # Тест Kodik
        try:
            if not quiet:
                print('   🔍 Тест Kodik...')
            from anime_parsers_ru import KodikParser
            parser = KodikParser()
            results = parser.get_list(limit_per_page=1)
            if results[0] and len(results[0]) > 0:
                working_sources.append('kodik')
                if not quiet:
                    print('      ✅ Kodik работает')
            else:
                if not quiet:
                    print('      ⚠️ Kodik: нет результатов')
        except Exception as e:
            if not quiet:
                print(f'      ❌ Kodik: {e}')
        
        return working_sources