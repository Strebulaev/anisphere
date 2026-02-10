#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import os

# Test downloading one poster
url = "https://s4.anilist.co/file/anilistcdn/media/anime/cover/medium/bx154587-fO8BcC7I1xS1.jpg"
filename = "test_poster.jpg"

print(f"Downloading from: {url}")

try:
    response = requests.get(url, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    
    if response.status_code == 200:
        filepath = f'backend/media/anime_posters/{filename}'
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"Saved to: {filepath}")
        print(f"Size: {len(response.content)} bytes")
    else:
        print(f"Failed: HTTP {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
