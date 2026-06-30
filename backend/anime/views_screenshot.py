"""
API Views для мгновенных скриншотов и фрагментов через Kodik API.
"""
import base64
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from io import BytesIO

import requests
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.utils import timezone
from django.http import StreamingHttpResponse
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from anime.models import Anime, ClipTask
from anime.serializers import ClipTaskCreateSerializer
from anime.services.kodik_video import get_anime_m3u8, get_episode_player_url, get_m3u8_url
from anime.services.direct_video import DirectVideoService
from anime.tasks import process_clip_task

# Динамически определяем путь к ffmpeg
FFMPEG_PATH = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"


class KodikInstantScreenshotView(APIView):
    """
    POST /api/anime/<id>/screenshot/

    Мгновенный скриншот из видео Kodik.
    Возвращает base64 изображение (JPEG).

    Body:
        {
            "episode": 1,
            "season": 1,
            "timestamp": 125.5,  # секунды
            "translation_id": "610",
            "quality": "720"
        }
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def post(self, request, pk):
        import traceback
        try:
            anime = Anime.objects.get(pk=pk)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)

        episode = int(request.data.get("episode", 1))
        season = int(request.data.get("season", 1))
        timestamp = float(request.data.get("timestamp", 0))
        translation_id = request.data.get("translation_id")
        quality = request.data.get("quality", "720")
        user_ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR", "1.1.1.1")

        if timestamp < 0:
            return Response({"error": "timestamp не может быть отрицательным"}, status=400)

        # Проверяем кэш скриншота
        cache_key = f"screenshot:{pk}:{episode}:{season}:{translation_id or 'any'}:{timestamp:.1f}"
        cached = cache.get(cache_key)
        if cached:
            return Response({"image_base64": cached, "cached": True})

        # Получаем m3u8 URL
        try:
            m3u8_url = get_anime_m3u8(
                anime_id=pk,
                episode=episode,
                season=season,
                translation_id=translation_id,
                user_ip=user_ip,
                quality=quality,
            )
        except Exception as e:
            print(f"[SCREENSHOT] get_anime_m3u8 error: {e}")
            traceback.print_exc()
            return Response({"error": f"Ошибка получения видео: {str(e)}"}, status=500)

        if not m3u8_url:
            return Response({"error": "Не удалось получить видео URL из Kodik"}, status=404)

        # Создаём скриншот через ffmpeg
        try:
            hours = int(timestamp // 3600)
            minutes = int((timestamp % 3600) // 60)
            seconds = int(timestamp % 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_path = tmp.name

            # ── ОПТИМИЗАЦИЯ: пробуем получить прямую MP4 ссылку ──
            # MP4 с input-seek работает в разы быстрее HLS
            video_url = m3u8_url
            is_mp4 = False
            if m3u8_url and m3u8_url.endswith(".m3u8"):
                mp4_candidate = m3u8_url.replace(".m3u8", ".mp4")
                try:
                    resp = requests.head(mp4_candidate, timeout=3, allow_redirects=True)
                    if resp.status_code == 200:
                        video_url = mp4_candidate
                        is_mp4 = True
                        print(f"[SCREENSHOT] Using direct MP4 for fast seek: {video_url[:80]}...")
                except Exception:
                    pass

            # ── ОПТИМИЗИРОВАННАЯ ffmpeg команда ──
            # Ключевое изменение: -ss ДО -i (input seek) - ffmpeg прыгает на ключевой кадр
            # ещё до полного открытия/декодирования потока. Для MP4 это почти мгновенно.
            cmd = [
                FFMPEG_PATH,
                "-y",
                "-ss", time_str,          # ← input seek: быстрый прыжок до позиции
            ]

            if not is_mp4:
                # Только для HLS: минимальные значения, чтобы не ждать анализа
                cmd.extend([
                    "-analyzeduration", "3M",
                    "-probesize", "3M",
                    "-fflags", "+discardcorrupt+nobuffer",
                ])

            cmd.extend([
                "-i", video_url,
                "-frames:v", "1",        # ровно 1 кадр
                "-q:v", "2",             # хорошее качество JPEG
                "-vf", "scale=1280:-1",
                "-an",                   # без аудио
                "-f", "image2",
                tmp_path,
            ])

            print(f"[SCREENSHOT] ffmpeg cmd: {' '.join(cmd[:8])}...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                print(f"[SCREENSHOT] ffmpeg error: {result.stderr}")
                return Response(
                    {"error": f"Ошибка ffmpeg: {result.stderr[:200]}"},
                    status=500,
                )

            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                return Response({"error": "Скриншот не создан"}, status=500)

            # Конвертируем в base64
            with open(tmp_path, "rb") as f:
                image_data = f.read()
            base64_data = base64.b64encode(image_data).decode("utf-8")
            base64_url = f"data:image/jpeg;base64,{base64_data}"

            # Кэшируем на 24 часа
            cache.set(cache_key, base64_url, 86400)

            # Удаляем временный файл
            os.unlink(tmp_path)

            return Response({
                "image_base64": base64_url,
                "cached": False,
                "timestamp": timestamp,
            })

        except subprocess.TimeoutExpired:
            return Response({"error": "Таймаут создания скриншота"}, status=504)
        except Exception as e:
            print(f"[SCREENSHOT] Internal error: {e}")
            traceback.print_exc()
            return Response({"error": f"Внутренняя ошибка: {str(e)}"}, status=500)


class KodikClipCreateView(APIView):
    """
    POST /api/anime/<id>/clip/create/

    Создание фрагмента видео (асинхронно через Celery).

    Body:
        {
            "episode": 1,
            "season": 1,
            "start": 30.0,
            "end": 60.0,
            "label": "Эпичная сцена",
            "translation_id": "610",
            "quality": "720",
            "format": "mp4"  // или "mp3"
        }
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def post(self, request, pk):
        import traceback
        try:
            anime = Anime.objects.get(pk=pk)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)

        episode = int(request.data.get("episode", 1))
        season = int(request.data.get("season", 1))
        start = float(request.data.get("start", 0))
        end = float(request.data.get("end", 0))
        label = request.data.get("label", "clip")
        translation_id = request.data.get("translation_id")
        quality = request.data.get("quality", "720")

        # Определяем формат
        fmt = request.data.get("format", "mp4")
        if fmt not in ("mp4", "mp3"):
            fmt = "mp4"

        # Проверяем премиум для фрагментов (не для полной серии)
        is_full_episode = isinstance(label, str) and label.startswith('Episode_')
        if not is_full_episode and end <= start:
            return Response({"error": "end должен быть больше start"}, status=400)
        
        if not is_full_episode and end - start > 300:
            # Фрагменты до 5 минут - только для премиум
            if not request.user.is_authenticated:
                return Response({"error": "Требуется авторизация"}, status=401)
            
            from users.models import UserProfileSettings
            try:
                profile = UserProfileSettings.objects.get(user=request.user)
                if not profile.is_premium:
                    return Response({"error": "Скачивание фрагментов доступно только для премиум пользователей"}, status=403)
            except UserProfileSettings.DoesNotExist:
                return Response({"error": "Скачивание фрагментов доступно только для премиум пользователей"}, status=403)
        
        # Для полных серий лимит 1 час
        if is_full_episode and end - start > 3600:
            return Response({"error": "Максимальная длительность серии 1 час"}, status=400)

        # Получаем video_url для задачи
        user_ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR", "1.1.1.1")
        try:
            m3u8_url = get_anime_m3u8(
                anime_id=pk,
                episode=episode,
                season=season,
                translation_id=translation_id,
                user_ip=user_ip,
                quality=quality,
            )
        except Exception as e:
            print(f"[CLIP] get_anime_m3u8 error: {e}")
            traceback.print_exc()
            return Response({"error": f"Ошибка получения видео: {str(e)}"}, status=500)

        # Создаём задачу
        serializer = ClipTaskCreateSerializer(data={
            "anime": pk,
            "task_type": "clip",
            "episode": episode,
            "season": season,
            "start_time": start,
            "end_time": end,
            "label": label,
            "quality": quality,
            "format": fmt,
        })

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        try:
            task = serializer.save(
                user=request.user if request.user.is_authenticated else None,
                video_url=m3u8_url or "",
            )
        except Exception as e:
            print(f"[CLIP] serializer.save error: {e}")
            traceback.print_exc()
            return Response({"error": f"Ошибка сохранения задачи: {str(e)}"}, status=500)

        # Запускаем Celery задачу
        try:
            process_clip_task.delay(str(task.id))
        except Exception as e:
            print(f"[CLIP] Celery error: {e}")
            # Не критично - задача создана, можно вернуть task_id

        return Response({
            "task_id": str(task.id),
            "status": "pending",
            "message": "Фрагмент создаётся",
        }, status=202)


class KodikStreamView(APIView):
    """
    GET /api/anime/<id>/stream/

    Потоковое скачивание серии целиком или фрагмента напрямую с сервера.
    ffmpeg склеивает m3u8 и отдаёт поток пользователю без сохранения на диск.

    Query params:
        episode=1
        season=1
        translation_id=610
        quality=720
        format=mp4|mp3 (опционально, по умолчанию mp4)
        filename=optional_name.mp4
        start=30 (опционально, начало фрагмента в секундах)
        end=60 (опционально, конец фрагмента в секундах)
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        import traceback
        try:
            anime = Anime.objects.get(pk=pk)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)

        episode = int(request.GET.get("episode", 1))
        season = int(request.GET.get("season", 1))
        translation_id = request.GET.get("translation_id")
        quality = request.GET.get("quality", "720")
        fmt = request.GET.get("format", "mp4")
        filename = request.GET.get("filename", f"Episode_{episode}.{fmt}")

        # Опциональные параметры для фрагмента
        start = request.GET.get("start")
        end = request.GET.get("end")
        
        # Проверяем нужно ли ограничивать время
        # Если start=0 и end не указан или очень большой - скачиваем всю серию без ограничений
        is_clip = False
        if start is not None and end is not None:
            start_float = float(start)
            end_float = float(end)
            # Если разница меньше 1 секунды от конца - считаем что это полная серия
            if end_float - start_float > 8000:  # > 2 часа
                is_clip = False
                start = None
                end = None
            else:
                is_clip = True
                start = start_float
                end = end_float
        else:
            is_clip = False
            start = None
            end = None

        if fmt not in ("mp4", "mp3"):
            fmt = "mp4"

        user_ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR", "1.1.1.1")

        # Получаем m3u8 URL
        try:
            m3u8_url = get_anime_m3u8(
                anime_id=pk,
                episode=episode,
                season=season,
                translation_id=translation_id,
                user_ip=user_ip,
                quality=quality,
            )
            print(f"[STREAM] m3u8_url for anime={pk} ep={episode}: {m3u8_url[:100] if m3u8_url else None}...")
        except Exception as e:
            print(f"[STREAM] get_anime_m3u8 error: {e}")
            traceback.print_exc()
            return Response({"error": f"Ошибка получения видео: {str(e)}"}, status=500)

        if not m3u8_url:
            print(f"[STREAM] No m3u8_url returned for anime={pk} ep={episode}")
            return Response({"error": "Не удалось получить видео URL из Kodik"}, status=404)

        # Создаём генератор для потока
        def generate():
            import signal
            
            tmp_output = None
            try:
                # Создаём временный файл
                tmp_output = tempfile.mktemp(suffix=f".{fmt}")
                print(f"[STREAM] Creating temp file: {tmp_output}")

                # Формируем команду ffmpeg
                cmd = [FFMPEG_PATH, "-y"]
                
                # Добавляем настройки для HLS
                cmd.extend(["-analyzeduration", "20M"])
                cmd.extend(["-probesize", "20M"])
                cmd.extend(["-fflags", "nobuffer"])
                
                # Если это фрагмент (не полная серия), добавляем -ss и -to ПЕРЕД -i
                if is_clip and start is not None and end is not None:
                    cmd.extend(["-ss", str(start), "-to", str(end)])
                
                cmd.extend(["-i", m3u8_url])
                
                # Дополнительные настройки для выхода
                if fmt == "mp3":
                    cmd.extend([
                        "-vn",
                        "-c:a", "libmp3lame",
                        "-b:a", "192k",
                        "-ar", "44100",
                        "-ac", "2",
                        "-movflags", "+faststart"
                    ])
                else:
                    cmd.extend([
                        "-c:v", "copy",
                        "-c:a", "copy",
                        "-bsf:a", "aac_adtstoasc",
                        "-movflags", "+faststart"
                    ])
                
                cmd.append(tmp_output)

                print(f"[STREAM] Running ffmpeg: {' '.join(cmd)}")
                print(f"[STREAM] is_clip={is_clip}, start={start}, end={end}, fmt={fmt}")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=7200  # 2 часа для полной серии
                )
                
                print(f"[STREAM] ffmpeg returncode: {result.returncode}")
                if result.stderr:
                    print(f"[STREAM] ffmpeg stderr (last 500 chars): {result.stderr[-500:]}")
                
                if result.returncode != 0:
                    error_msg = f"FFmpeg error: {result.stderr[:1000] if result.stderr else 'Unknown error'}"
                    print(f"[STREAM] {error_msg}")
                    # Возвращаем ошибку как текст
                    yield error_msg.encode()
                    return

                if not tmp_output or not os.path.exists(tmp_output):
                    error_msg = "Error: No output file created"
                    print(f"[STREAM] {error_msg}")
                    yield error_msg.encode()
                    return

                file_size = os.path.getsize(tmp_output)
                print(f"[STREAM] Output file size: {file_size} bytes")
                
                if file_size == 0:
                    error_msg = "Error: Output file is empty"
                    print(f"[STREAM] {error_msg}")
                    yield error_msg.encode()
                    return

                # Читаем файл и отдаём частями
                with open(tmp_output, "rb") as f:
                    while True:
                        chunk = f.read(65536)  # 64KB chunks
                        if not chunk:
                            break
                        yield chunk

            except subprocess.TimeoutExpired:
                error_msg = "Error: Processing timeout"
                print(f"[STREAM] {error_msg}")
                yield error_msg.encode()
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                print(f"[STREAM] Exception: {error_msg}")
                import traceback
                traceback.print_exc()
                yield error_msg.encode()
            finally:
                if tmp_output and os.path.exists(tmp_output):
                    try:
                        os.unlink(tmp_output)
                        print(f"[STREAM] Cleaned up temp file")
                    except Exception as e:
                        print(f"[STREAM] Failed to cleanup: {e}")

        # Возвращаем потоковый ответ
        extension = "mp3" if fmt == "mp3" else "mp4"
        response = StreamingHttpResponse(
            generate(),
            content_type="audio/mpeg" if fmt == "mp3" else "video/mp4",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}.{extension}"'
        return response


class DirectVideoUrlView(APIView):
    """
    GET /api/anime/<id>/direct_url/

    Получение прямой MP4 ссылки на эпизод (без ffmpeg обработки).
    Возвращает прямую ссылку если доступна, или m3u8 как fallback.

    Query params:
        episode=1
        season=1
        translation_id=610
        quality=720
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        import asyncio
        import traceback
        
        try:
            anime = Anime.objects.get(pk=pk)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)

        episode = int(request.GET.get("episode", 1))
        season = int(request.GET.get("season", 1))
        translation_id = request.GET.get("translation_id")
        quality = request.GET.get("quality", "720")

        # Получаем прямую ссылку
        try:
            result = asyncio.run(DirectVideoService.get_anime_episode_url(
                anime_id=pk,
                episode=episode,
                season=season,
                translation_id=translation_id,
                quality=quality
            ))
            
            if not result:
                return Response({"error": "Не удалось получить видео"}, status=404)
            
            return Response({
                "url": result["url"],
                "quality": result["quality"],
                "source": result["source"],
                "is_m3u8": result.get("is_m3u8", False),
            })
            
        except Exception as e:
            print(f"[DIRECT_URL] Error: {e}")
            traceback.print_exc()
            return Response({"error": f"Ошибка получения видео: {str(e)}"}, status=500)
