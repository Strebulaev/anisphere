#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест без Django setup
"""
import requests
import time

class TestImporter:
    ANILIST_API = "https://graphql.anilist.co"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
        })
    
    def make_anilist_request(self, query, variables=None, max_retries=3):
        """Выполняет GraphQL запрос к AniList"""
        url = self.ANILIST_API
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        data = {
            'query': query,
            'variables': variables or {}
        }
        
        print(f"DEBUG: Making request to {url}")
        print(f"DEBUG: Headers = {headers}")
        print(f"DEBUG: Data keys = {data.keys()}")
        
        for attempt in range(max_retries):
            try:
                print(f"DEBUG: Attempt {attempt + 1}/{max_retries}")
                response = self.session.post(url, json=data, headers=headers, timeout=30)
                
                print(f"DEBUG: Response status = {response.status_code}")
                
                if response.status_code == 429:
                    wait_time = 5 * (attempt + 1)
                    print(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                
                print(f"DEBUG: Success! Returning response")
                return response.json()
                
            except Exception as e:
                print(f"DEBUG: Exception: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        print("DEBUG: Failed to get data")
        return None

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

importer = TestImporter()
result = importer.make_anilist_request(query, {'page': 1, 'perPage': 5})

if result and 'data' in result:
    media = result['data']['Page']['media']
    print(f"\nSUCCESS! Found {len(media)} anime")
    for m in media[:3]:
        title = m['title']['english'] or m['title']['romaji']
        print(f"  - {title}")
else:
    print("\nFAILED!")
    print(f"Result: {result}")
