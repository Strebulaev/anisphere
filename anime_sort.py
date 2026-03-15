import json
import requests

# Твой Codestral API ключ (работает и для обычных моделей Mistral)
API_KEY = "gO4bWgTM5n8gV00Fqo2Evw7JNUEuqiPz"  # вставь свой ключ

# Читаем файл (возьмём первые 500 для теста)
with open('anime_list.txt', 'r', encoding='utf-8') as f:
    all_titles = [line.strip().strip('"') for line in f if line.strip()]
    titles = all_titles[:500]  # пока тестируем на 500

print(f"Загружено {len(titles)} названий (тест)")

prompt = f"""Сгруппируй эти аниме по франшизам:

{chr(10).join(titles)}

Правила:
- One Piece и Ван Пис → вместе
- Наруто и Naruto → вместе
- Блич и Bleach → вместе
- Все сезоны [ТВ-1], [ТВ-2] → вместе
- Фильмы и OVA → к основному аниме

Верни ТОЛЬКО JSON."""

response = requests.post(
    "https://api.mistral.ai/v1/chat/completions",  # обычный Mistral endpoint
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "mistral-large-latest",  # используем текстовую модель
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
)

if response.status_code == 200:
    result = response.json()
    sorted_anime = json.loads(result['choices'][0]['message']['content'])
    
    with open('sorted_anime.json', 'w', encoding='utf-8') as f:
        json.dump(sorted_anime, f, ensure_ascii=False, indent=2)
    
    print("✅ Готово!")
else:
    print(f"❌ Ошибка {response.status_code}: {response.text}")