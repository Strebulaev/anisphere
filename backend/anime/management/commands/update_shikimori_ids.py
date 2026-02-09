from django.core.management.base import BaseCommand
from anime.models import Anime
import requests
import time


class Command(BaseCommand):
    help = 'Обновить Shikimori ID для всех аниме без него'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Максимальное количество аниме для обновления'
        )
    
    def handle(self, *args, **options):
        limit = options['limit']
        
        # Получаем аниме без Shikimori ID
        animes_without_shikimori = Anime.objects.filter(
            shikimori_id__isnull=True
        )[:limit]
        
        total = animes_without_shikimori.count()
        
        self.stdout.write(self.style.SUCCESS(f"Найдено {total} аниме без Shikimori ID"))
        self.stdout.write(f"Будет обновлено максимум {limit} записей")
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        updated_count = 0
        
        for anime in animes_without_shikimori:
            try:
                # Пропускаем если нет названия
                if not anime.title_ru and not anime.title_en:
                    self.stdout.write(f"❌ Пропущено: ID {anime.id} - нет названия")
                    continue
                
                search_term = anime.title_ru or anime.title_en
                self.stdout.write(f"🔍 Поиск: {search_term}")
                
                # Ищем на Shikimori
                search_url = "https://shikimori.one/api/animes"
                params = {
                    'search': search_term,
                    'limit': 1
                }
                
                response = session.get(search_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        shikimori_data = data[0]
                        shikimori_id = shikimori_data['id']
                        
                        # Обновляем запись
                        anime.shikimori_id = shikimori_id
                        anime.save()
                        
                        updated_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✅ Обновлено: {anime.title_ru or anime.title_en} "
                                f"-> Shikimori ID: {shikimori_id}"
                            )
                        )
                    else:
                        self.stdout.write(f"⚠️ Не найдено на Shikimori: {search_term}")
                else:
                    self.stdout.write(f"⚠️ Ошибка запроса: {response.status_code}")
                
                # Задержка чтобы не заблокировали
                time.sleep(1.5)
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Ошибка для {anime.title_ru}: {str(e)}")
                )
                time.sleep(2)
        
        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Готово! Обновлено {updated_count} из {total} записей"
        ))