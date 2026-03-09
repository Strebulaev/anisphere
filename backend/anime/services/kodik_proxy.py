# anime/views/kodik_proxy.py
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import logging

logger = logging.getLogger(__name__)

KODIK_TOKEN = "74ecb013335271e4344ebc994956dd75"
KODIK_API_URL = "https://kodikapi.com"

@csrf_exempt
@require_http_methods(["GET"])
def kodik_studios(request):
    """
    Прокси для получения списка аниме студий из Kodik API
    """
    try:
        # 1. Получаем список аниме с material_data
        response = requests.get(
            f"{KODIK_API_URL}/list",
            params={
                'token': KODIK_TOKEN,
                'types': 'anime-serial,anime',
                'with_material_data': 'true',
                'limit': 100,  # Можно увеличить до 1000, но будет дольше
                'sort': 'title',
                'order': 'asc'
            },
            timeout=30
        )
        
        if response.status_code != 200:
            return JsonResponse({
                'error': 'Kodik API error',
                'status': response.status_code
            }, status=response.status_code)
        
        data = response.json()
        
        # 2. Извлекаем уникальные студии
        studios = set()
        studio_counter = {}
        
        for item in data.get('results', []):
            material_data = item.get('material_data', {})
            anime_studios = material_data.get('anime_studios', [])
            
            for studio in anime_studios:
                studios.add(studio)
                studio_counter[studio] = studio_counter.get(studio, 0) + 1
        
        # 3. Сортируем студии (сначала самые популярные)
        sorted_studios = sorted(
            [{'name': s, 'count': studio_counter.get(s, 0)} for s in studios],
            key=lambda x: (-x['count'], x['name'])
        )
        
        return JsonResponse({
            'studios': sorted_studios,
            'total': len(sorted_studios),
            'source': 'kodik'
        })
        
    except requests.Timeout:
        return JsonResponse({'error': 'Kodik API timeout'}, status=504)
    except requests.RequestException as e:
        logger.error(f"Kodik API error: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def kodik_proxy(request):
    """
    Универсальный прокси для любых запросов к Kodik API
    """
    try:
        # Копируем все GET параметры из оригинального запроса
        params = request.GET.copy()
        params['token'] = KODIK_TOKEN  # Подставляем токен
        
        # Определяем эндпоинт (по умолчанию /list)
        endpoint = params.pop('endpoint', ['list'])[0]
        
        response = requests.get(
            f"{KODIK_API_URL}/{endpoint}",
            params=params,
            timeout=30
        )
        
        return JsonResponse(response.json(), status=response.status_code)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)