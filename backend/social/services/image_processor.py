"""
Сервис для обработки и конвертации изображений в WebP
"""
import os
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile, UploadedFile
from django.core.files.base import ContentFile


def convert_to_webp(image_file, max_size=(1920, 1920), quality=85):
    """
    Конвертирует изображение в WebP формат
    
    Args:
        image_file: Файл изображения (InMemoryUploadedFile или путь)
        max_size: Максимальный размер (ширина, высота)
        quality: Качество WebP (1-100)
    
    Returns:
        ContentFile с WebP изображением
    """
    try:
        # Открываем изображение
        img = Image.open(image_file)
        
        # Конвертируем в RGB если нужно (для RGBA с прозрачностью)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Создаём белый фон для прозрачных изображений
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Ресайз если изображение слишком большое
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Сохраняем в WebP
        output = BytesIO()
        img.save(output, format='WEBP', quality=quality, optimize=True)
        output.seek(0)
        
        # Получаем имя файла с новым расширением
        if hasattr(image_file, 'name'):
            original_name = os.path.basename(image_file.name)
            name, _ = os.path.splitext(original_name)
            new_name = f"{name}.webp"
        else:
            new_name = "image.webp"
        
        # Создаём ContentFile
        webp_file = ContentFile(output.read(), name=new_name)
        
        return webp_file
        
    except Exception as e:
        # Если ошибка - возвращаем None
        print(f"Error converting to WebP: {e}")
        return None


def process_image_field(instance, field_name, max_size=(1920, 1920), quality=85):
    """
    Обрабатывает ImageField модели и конвертирует в WebP
    
    Args:
        instance: Экземпляр модели
        field_name: Имя поля ImageField
        max_size: Максимальный размер
        quality: Качество WebP
    
    Returns:
        True если успешно, False если ошибка
    """
    try:
        image_file = getattr(instance, field_name)
        
        if not image_file:
            return False
        
        # Конвертируем в WebP
        webp_file = convert_to_webp(image_file, max_size, quality)
        
        if webp_file:
            # Сохраняем WebP файл
            setattr(instance, field_name, webp_file)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing image field: {e}")
        return False


def get_webp_url(url):
    """
    Конвертирует URL изображения в WebP URL
    
    Args:
        url: URL изображения
    
    Returns:
        URL с .webp расширением
    """
    if not url:
        return url
    
    # Если уже WebP
    if url.endswith('.webp'):
        return url
    
    # Заменяем расширение
    if url.endswith('.png'):
        return url[:-4] + '.webp'
    elif url.endswith('.jpg') or url.endswith('.jpeg'):
        return url[:-4] + '.webp'
    
    return url
