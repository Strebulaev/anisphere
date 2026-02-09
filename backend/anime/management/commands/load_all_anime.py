"""Команда для загрузки всех аниме из API в базу данных"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from anime.services.anime_parser_service import AnimeParserService
from anime.models import Anime

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Загружает все аниме из API в базу данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=1000,
            help='Максимальное количество аниме для загрузки'
        )
        parser.add_argument(
            '--source',
            type=str,
            default='kodik',
            choices=['kodik', 'shikimori', 'aniboom', 'all'],
            help='Источник для загрузки данных'
        ),
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие данные перед загрузкой'
        )
        parser.add_argument(
            '--page',
            type=int,
            default=1,
            help='Страница для загрузки (для пагинации)'
        )
        
    def handle(self, *args, **options):
        limit = options['limit']
        source = options['source']
        clear_data = options['clear']
        page = options['page']
        
        self.stdout.write(
            self.style.SUCCESS(f'Загружаем все аниме из {source} (лимит: {limit}, страница: {page})')
        )
        
        if clear_data:
            self.stdout.write(self.style.WARNING('Очищаем существующие данные...'))
            Anime.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Данные очищены'))
        
        parser_service = AnimeParserService()
        
        try:
            # Загружаем все аниме
            self.stdout.write('Загружаем все аниме...')
            loaded_count = self._load_all_anime(parser_service, limit, source, page)
            
            self.stdout.write(
                self.style.SUCCESS(f'Успешно загружено {loaded_count} аниме')
            )
            
            # Показываем статистику
            total_anime = Anime.objects.count()
            self.stdout.write(
                self.style.SUCCESS(f'Всего аниме в БД: {total_anime}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при загрузке: {str(e)}')
            )
            logger.exception('Ошибка при загрузке аниме')

    def _load_all_anime(self, parser_service, limit, source, page):
        """Загружает все аниме"""
        loaded_count = 0
        
        # Получаем все аниме из источника
        self.stdout.write(f'Получаем аниме из {source}...')
        all_anime = parser_service.get_all_anime(source=source, page=page, limit=limit)
        
        if not all_anime:
            self.stdout.write(self.style.WARNING(f'Не удалось получить аниме из {source}'))
            return 0
        
        self.stdout.write(f'Найдено {len(all_anime)} аниме для импорта')
        
        # Сохраняем аниме
        for anime_data in all_anime:
            try:
                # Проверяем, нет ли уже такого аниме
                shikimori_id = anime_data.get('shikimori_id')
                if shikimori_id and Anime.objects.filter(shikimori_id=shikimori_id).exists():
                    self.stdout.write(f'Пропускаем (уже есть): {anime_data.get("title_ru", "Unknown")}')
                    continue
                
                # Импортируем в БД
                anime = parser_service.import_anime_to_db(anime_data, source)
                loaded_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f'Добавлено: {anime.title_ru} (ID: {anime.shikimori_id})')
                )   
                
                # Показываем прогресс каждые 50 аниме
                if loaded_count % 50 == 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'Прогресс: {loaded_count} аниме загружено')
                    )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Ошибка импорта аниме {anime_data.get("title_ru", "Unknown")}: {str(e)}')
                )
                continue
        
        return loaded_count