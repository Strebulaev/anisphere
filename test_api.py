#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json

# Тест AniList API
print("Testing AniList API...")
query = '''
query ($page: Int, $perPage: Int) {
    Page(page: $page, perPage: $perPage) {
        pageInfo {
            hasNextPage
        }
        media(type: ANIME, sort: TRENDING_DESC) {
            id
            title {
                romaji
                english
                native
            }
        }
    }
}
'''

try:
    data = requests.post(
        'https://graphql.anilist.co',
        json={'query': query, 'variables': {'page': 1, 'perPage': 5}},
        timeout=10
    )
    result = data.json()
    print("AniList Response:")
    print(json.dumps(result, indent=2))
except Exception as e:
    print(f"AniList Error: {e}")

print("\n" + "="*80 + "\n")

# Тест Jikan API
print("Testing Jikan API...")
try:
    data = requests.get(
        'https://api.jikan.moe/v4/top/anime',
        params={'page': 1, 'limit': 5},
        timeout=10
    )
    result = data.json()
    print("Jikan Response:")
    print(json.dumps(result, indent=2))
except Exception as e:
    print(f"Jikan Error: {e}")
