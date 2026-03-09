import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote, urlparse
import logging
import random
import re

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Список User-Agent для ротации ---
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0',
]

# --- Список студий ---
studio_names = [
    "3Hz", "8-Bit (студия)", "A-1 Pictures", "A.P.P.P.", "Actas",
    "Ajia-do Animation Works", "Anime International Company", "AnimeNation", "Aniplex",
    "Arms", "Artland", "Asahi Production", "Ashi Productions", "AXsiZ",
    "Bandai Namco Filmworks", "Bandai Namco Pictures", "Bandai Visual", "Bee Train",
    "Benten Film", "Bones", "Bridge (студия)", "BUG FILMS",
    "C2C (студия)", "CloverWorks", "CoMix Wave Films", "CygamesPictures",
    "David Production", "Digital Frontier", "Doga Kobo",
    "EMT Squared", "ENGI", "Ezo’la",
    "Feel (студия)",
    "Gainax", "Gallop", "Geno Studio", "GoHands", "Gonzo",
    "J.C.Staff",
    "Kinema Citrus", "Kyoto Animation",
    "Lay-duce", "Lerche", "Liden Films",
    "Madhouse", "Magic Bus (студия)", "MAPPA", "Mushi Production",
    "NAZ (студия)", "Nexus (анимационная студия)", "Nippon Animation", "NUT",
    "OLM, Inc.", "Ordet",
    "P.A. Works", "Passione", "Pony Canyon", "Production I.G", "Project No.9",
    "Robot Communications",
    "Sanzigen", "Satelight", "Science Saru", "Seven (анимационная студия)",
    "Seven Arcs", "Shaft (компания)", "Shin-Ei Animation", "Shuka", "Silver Link",
    "Studio 4°C", "Studio A-Cat", "Studio Bind", "Studio Comet", "Studio Deen",
    "Studio Ghibli", "Studio Gokumi", "Studio Hibari", "Studio Khara", "Studio Pierrot",
    "Studio Ponoc", "Studio VOLN",
    "Tatsunoko Production", "Tear Studio", "Tezuka Productions", "TMS Entertainment",
    "TNK", "Toei Animation", "Toho", "Trigger (компания)", "TROYCA",
    "Tsuchida Production", "TYO Animations", "Type-Moon", "Typhoon Graphics",
    "Ufotable", "Ultra Super Pictures",
    "VAP", "Victor Entertainment",
    "White Fox", "Wit Studio",
    "Zero-G", "Zexcs"
]

# --- Настройки ---
BASE_URL = "https://ru.wikipedia.org/wiki/"
OUTPUT_FOLDER = "studio_logos"
RETRY_DELAY = 30  # Уменьшаем до 30 секунд
MAX_RETRIES = 2   # Уменьшаем количество попыток

# Создаем папку для сохранения
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

def get_headers():
    """Возвращает заголовки со случайным User-Agent"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

def safe_filename(text):
    """Преобразует текст в безопасное имя файла"""
    text = re.sub(r'[<>:"/\\|?*]', '_', text)
    text = text.strip()
    if len(text) > 200:
        text = text[:200]
    return text

def get_file_extension_from_url(url):
    """Извлекает расширение файла из URL"""
    path = unquote(urlparse(url).path)
    ext = os.path.splitext(path)[1].lower()
    if ext and ext.startswith('.'):
        return ext
    return '.png'

def download_image_with_retry(img_url, studio_name, retries=MAX_RETRIES):
    """Скачивает изображение с повторными попытками"""
    for attempt in range(retries):
        try:
            safe_name = safe_filename(studio_name)
            ext = get_file_extension_from_url(img_url)
            filename = os.path.join(OUTPUT_FOLDER, f"{safe_name}{ext}")

            # Используем случайные заголовки для каждого скачивания
            headers = get_headers()
            img_response = requests.get(img_url, headers=headers, stream=True, timeout=30)
            img_response.raise_for_status()

            with open(filename, 'wb') as f:
                for chunk in img_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logging.info(f"  [OK] Изображение сохранено: {filename}")
            return True

        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                wait_time = RETRY_DELAY * (attempt + 1)  # Увеличиваем время ожидания с каждой попыткой
                logging.warning(f"  Ошибка скачивания, попытка {attempt+2}/{retries} через {wait_time}с. Ошибка: {e}")
                time.sleep(wait_time)
            else:
                logging.error(f"  [Ошибка] Не удалось скачать после {retries} попыток: {e}")
                return False
        except Exception as e:
            logging.error(f"  [Ошибка] Непредвиденная ошибка: {e}")
            return False

# --- Основной цикл по студиям ---
logging.info(f"Начинаем поиск логотипов для {len(studio_names)} студий...")
logging.info("-" * 50)

successful = 0
failed = 0

for i, name in enumerate(studio_names):
    logging.info(f"({i+1}/{len(studio_names)}) Обработка: {name}")
    
    # Генерируем случайную задержку между запросами (от 5 до 15 секунд)
    sleep_time = random.uniform(5, 15)
    
    page_url = BASE_URL + name.replace(" ", "_")
    
    for attempt in range(MAX_RETRIES):
        try:
            # Используем случайные заголовки для каждого запроса страницы
            headers = get_headers()
            response = requests.get(page_url, headers=headers, timeout=30)
            response.encoding = 'utf-8'
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')

            # Поиск изображения
            img_tag = None
            infobox = soup.find('table', class_='infobox')
            if infobox:
                img_tag = infobox.find('img')
            if not img_tag:
                content_div = soup.find('div', {'id': 'mw-content-text'})
                if content_div:
                    img_tag = content_div.find('img')

            if img_tag and img_tag.get('src'):
                img_src = img_tag['src']
                full_img_url = urljoin('https://ru.wikipedia.org', img_src)

                if '/thumb/' in full_img_url:
                    original_url = full_img_url.replace('/thumb/', '/').rsplit('/', 1)[0]
                    if original_url.startswith('//'):
                        original_url = 'https:' + original_url
                    logging.info(f"  Найдена миниатюра, пробуем оригинал")
                    if not download_image_with_retry(original_url, name):
                        logging.info("  Пробуем скачать миниатюру...")
                        download_image_with_retry(full_img_url, name)
                else:
                    download_image_with_retry(full_img_url, name)
                successful += 1
            else:
                logging.warning(f"  [Не найдено] Изображение для {name}")
                failed += 1

            break

        except requests.exceptions.HTTPError as e:
            if response.status_code in [403, 429]:
                wait_time = RETRY_DELAY * (attempt + 2)
                logging.warning(f"  Получена ошибка {response.status_code}. Ждем {wait_time}с перед повтором...")
                time.sleep(wait_time)
            else:
                logging.error(f"  HTTP ошибка для {page_url}: {e}")
                failed += 1
                break
        except requests.exceptions.RequestException as e:
            logging.error(f"  Ошибка загрузки страницы {page_url}: {e}")
            failed += 1
            break
        except Exception as e:
            logging.error(f"  Неожиданная ошибка для {name}: {e}")
            failed += 1
            break

    # Рандомная пауза между студиями
    logging.info(f"Пауза {sleep_time:.1f} секунд перед следующей студией...")
    time.sleep(sleep_time)

logging.info("-" * 50)
logging.info(f"Готово! Успешно: {successful}, Ошибок: {failed}")
logging.info(f"Проверьте папку '{OUTPUT_FOLDER}'")