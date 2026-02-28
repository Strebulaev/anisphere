from django.test import TestCase
from .models import Anime
from .views import fuzzy_search_anime, fuzzy_match, normalize_search_string


class FuzzySearchTestCase(TestCase):
    """Тесты для нечеткого поиска аниме"""

    def setUp(self):
        """Создаем тестовые данные"""
        # Создаем несколько аниме с похожими названиями
        self.anime1 = Anime.objects.create(
            title_ru='Фурен: За гранью пути',
            title_en='Frieren: Beyond Journey\'s End',
            title_jp='Sousou no Frieren',
            year=2023,
            status='ongoing',
            episodes=28,
            score=9.1
        )

        self.anime2 = Anime.objects.create(
            title_ru='Наруто',
            title_en='Naruto',
            title_jp='ナルト',
            year=2002,
            status='finished',
            episodes=220,
            score=8.3
        )

        self.anime3 = Anime.objects.create(
            title_ru='Атака титанов',
            title_en='Attack on Titan',
            title_jp='進撃の巨人',
            year=2013,
            status='finished',
            episodes=75,
            score=9.0
        )

    def test_normalize_search_string(self):
        """Тест нормализации строки поиска"""
        self.assertEqual(normalize_search_string('Фурен'), 'фурен')
        self.assertEqual(normalize_search_string('Frieren'), 'frieren')
        self.assertEqual(normalize_search_string('  Fri  ren  '), 'fri ren')
        self.assertEqual(normalize_search_string('Фурен!'), 'фурен')

    def test_fuzzy_match_exact(self):
        """Тест точного совпадения"""
        score = fuzzy_match('Frieren', 'Frieren: Beyond Journey\'s End')
        self.assertEqual(score, 1.0)

        score = fuzzy_match('Фурен', 'Фурен: За гранью пути')
        self.assertEqual(score, 1.0)

    def test_fuzzy_match_substring(self):
        """Тест вхождения подстроки"""
        score = fuzzy_match('Frieren', 'Frieren: Beyond Journey\'s End')
        self.assertEqual(score, 1.0)

        score = fuzzy_match('Fri', 'Frieren: Beyond Journey\'s End')
        self.assertGreater(score, 0.8)

    def test_fuzzy_match_similar(self):
        """Тест похожих строк (опечатки)"""
        score = fuzzy_match('Friren', 'Frieren: Beyond Journey\'s End')
        self.assertGreater(score, 0.7)  # Должно быть > 0.7 для похожих строк

        score = fuzzy_match('Furien', 'Frieren: Beyond Journey\'s End')
        self.assertGreater(score, 0.6)

    def test_fuzzy_search_exact_match(self):
        """Тест точного поиска"""
        results = fuzzy_search_anime('Frieren', limit=10)
        self.assertGreater(len(results), 0)

        # Проверяем, что первое результат - это Frieren
        first_result = results[0]
        self.assertIn('Frieren', first_result['title_en'])
        self.assertEqual(first_result['match_type'], 'exact')

    def test_fuzzy_search_partial_match(self):
        """Тест частичного совпадения"""
        results = fuzzy_search_anime('Fri', limit=10)
        self.assertGreater(len(results), 0)

    def test_fuzzy_search_typo(self):
        """Тест поиска с опечаткой"""
        # 'Friren' вместо 'Frieren'
        results = fuzzy_search_anime('Friren', limit=10)
        self.assertGreater(len(results), 0)

        # Проверяем, что результат найден через нечеткое сравнение
        frieren_found = any('Frieren' in r['title_en'] for r in results)
        self.assertTrue(frieren_found, "Frieren должен быть найден при поиске 'Friren'")

    def test_fuzzy_search_no_results(self):
        """Тест поиска без результатов"""
        results = fuzzy_search_anime('NonExistentAnime12345', limit=10)
        # Может вернуть нечеткие совпадения или пустой список
        # Главное - не должно падать с ошибкой
        self.assertIsInstance(results, list)

    def test_fuzzy_search_short_query(self):
        """Тест короткого запроса"""
        results = fuzzy_search_anime('A', limit=10)
        self.assertEqual(len(results), 0)  # Меньше 2 символов - пустой результат

    def test_fuzzy_search_russian(self):
        """Тест поиска на русском языке"""
        results = fuzzy_search_anime('Фурен', limit=10)
        self.assertGreater(len(results), 0)

        frieren_found = any('Фурен' in r['title_ru'] or 'Frieren' in r['title_en'] for r in results)
        self.assertTrue(frieren_found, "Фурен должен быть найден при поиске 'Фурен'")

    def test_fuzzy_search_mixed_case(self):
        """Тест поиска в разных регистрах"""
        results1 = fuzzy_search_anime('frieren', limit=10)
        results2 = fuzzy_search_anime('FRIEREN', limit=10)
        results3 = fuzzy_search_anime('FrIeReN', limit=10)

        # Все должны возвращать одинаковые результаты
        self.assertEqual(len(results1), len(results2))
        self.assertEqual(len(results2), len(results3))

