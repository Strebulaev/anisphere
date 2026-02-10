#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import time

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
})

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

url = "https://graphql.anilist.co"

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

data = {
    'query': query,
    'variables': {'page': 1, 'perPage': 5}
}

print("Making request...")
print(f"URL: {url}")
print(f"Headers: {headers}")
print(f"Data keys: {data.keys()}")

try:
    response = session.post(url, json=data, headers=headers, timeout=30)
    print(f"\nResponse status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nSuccess! Keys: {result.keys()}")
        
        if 'data' in result:
            media = result['data']['Page']['media']
            print(f"Found {len(media)} anime")
        else:
            print(f"No 'data' key. Full response: {result}")
    else:
        print(f"\nError! Response text: {response.text[:500]}")
        
except Exception as e:
    print(f"\nException: {e}")
    import traceback
    traceback.print_exc()
