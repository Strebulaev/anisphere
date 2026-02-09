import requests
import json

# Базовый URL
base_url = "http://localhost:8000/api/anime/anime/"

# Тест 1: Базовый запрос без фильтров
print("=== Test 1: No filters ===")
response = requests.get(base_url, params={"page_size": 2})
data = response.json()
print(f"Count: {data['count']}")
print(f"Results: {[(a['title_ru'], a['status']) for a in data['results']]}")

# Тест 2: Фильтр по статусу ongoing
print("\n=== Test 2: Status=ongoing ===")
response = requests.get(base_url, params={"status": "ongoing", "page_size": 2})
data = response.json()
print(f"Count: {data['count']}")
print(f"Results: {[(a['title_ru'], a['status']) for a in data['results']]}")

# Тест 3: Фильтр по статусу finished
print("\n=== Test 3: Status=finished ===")
response = requests.get(base_url, params={"status": "finished", "page_size": 2})
data = response.json()
print(f"Count: {data['count']}")
print(f"Results: {[(a['title_ru'], a['status']) for a in data['results']]}")

# Тест 4: Фильтр по жанрам
print("\n=== Test 4: Genres=1 (Action) ===")
response = requests.get(base_url, params={"genres": "1", "page_size": 2})
data = response.json()
print(f"Count: {data['count']}")
print(f"Results: {[(a['title_ru'], a['genres']) for a in data['results']]}")

# Тест 5: Поиск
print("\n=== Test 5: Search=Action ===")
response = requests.get(base_url, params={"search": "Action", "page_size": 2})
data = response.json()
print(f"Count: {data['count']}")
print(f"Results: {[(a['title_ru'], a['title_en']) for a in data['results']]}")

# Тест 6: Фильтр по году
print("\n=== Test 6: Year from 2020 ===")
response = requests.get(base_url, params={"year_from": "2020", "page_size": 2})
data = response.json()
print(f"Count: {data['count']}")
print(f"Results: {[(a['title_ru'], a['year']) for a in data['results']]}")
