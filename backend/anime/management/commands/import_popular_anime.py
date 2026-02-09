from django.core.management.base import BaseCommand
from parsers.animeparsers import AnimeParsersCollector

class Command(BaseCommand):
    help = 'Быстрый импорт популярных аниме (рекомендуется для начала)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Количество популярных аниме для импорта'
        )
        parser.add_argument(
            '--source',
            type=str,
            choices=['shikimori', 'aniboom', 'all'],
            default='shikimori',
            help='Источник для импорта'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('⚡ БЫСТРЫЙ ИМПОРТ ПОПУЛЯРНЫХ АНИМЕ'))
        self.stdout.write('=' * 50)
        
        collector = AnimeParsersCollector()
        count = options['count']
        source = options['source']
        
        try:
            if source == 'shikimori':
                self.stdout.write('📥 Импорт популярных аниме из Shikimori...')
                pages = min(2, max(1, count // 15))  # ~15 аниме на страницу
                result = collector.import_from_shikimori(page_limit=pages)
                
            elif source == 'aniboom':
                self.stdout.write('📥 Импорт популярных аниме из AniBoom...')
                # Популярные запросы
                popular_queries = [
                    'Наруто', 'Блич', 'Ванпанчмен', 'Атака титанов',
                    'Моя геройская академия', 'Джujutsu Kaisen', 'Демон-убийца',
                    'Фуллметал Алхимик', 'Тетрадь смерти', 'Евангелион',
                    'Ковбой Бибоп', 'Один удар', 'Хантер x Хантер',
                    'Штейнс;Гейт', 'Код Гиас', 'Драгонболл'
                ]
                
                # Берем нужное количество запросов
                queries_to_use = popular_queries[:min(len(popular_queries), count)]
                
                result = {'imported': 0, 'updated': 0, 'errors': 0}
                for query in queries_to_use:
                    try:
                        query_result = collector.import_from_aniboom(search_query=query)
                        result['imported'] += query_result.get('imported', 0)
                        result['updated'] += query_result.get('updated', 0)
                        result['errors'] += query_result.get('errors', 0)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'⚠️ Ошибка поиска "{query}": {e}'))
                        result['errors'] += 1
                        
            elif source == 'all':
                self.stdout.write('📥 Импорт из всех источников...')
                
                # Сначала Shikimori
                shikimori_result = collector.import_from_shikimori(page_limit=1)
                
                # Затем AniBoom
                aniboom_result = collector.import_from_aniboom(search_query='Наруто')
                
                result = {
                    'imported': shikimori_result.get('imported', 0) + aniboom_result.get('imported', 0),
                    'updated': shikimori_result.get('updated', 0) + aniboom_result.get('updated', 0),
                    'errors': shikimori_result.get('errors', 0) + aniboom_result.get('errors', 0)
                }
            
            # Показываем результат
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('📊 РЕЗУЛЬТАТ:'))
            self.stdout.write(f'✅ Создано: {result["imported"]} аниме')
            self.stdout.write(f'🔄 Обновлено: {result["updated"]} аниме')
            self.stdout.write(f'❌ Ошибок: {result["errors"]}')
            
            # Статистика в базе
            from anime.models import Anime
            total = Anime.objects.count()
            self.stdout.write(f'📈 Всего аниме в базе: {total}')
            
            if result['errors'] == 0:
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('🎉 Быстрый импорт завершен успешно!'))
                self.stdout.write('💡 Теперь можете запустить сервер и проверить аниме')
            else:
                self.stdout.write('')
                self.stdout.write(self.style.WARNING(f'⚠️ Импорт завершен с ошибками'))
            
            return f"Результат: создано {result['imported']}, обновлено {result['updated']}, ошибок {result['errors']}"
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка импорта: {e}'))
            return f"Ошибка: {e}"