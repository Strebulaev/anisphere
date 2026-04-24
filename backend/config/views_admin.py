"""
Admin views для запуска импортов.
"""

import subprocess
import os
import sys
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser


class RunKodikImportView(APIView):
    """Запуск импорта аниме из Kodik"""

    permission_classes = [IsAdminUser]

    def post(self, request):
        print("RunKodikImportView called!")
        # Для теста вернём простой ответ
        return Response({"success": True, "log": "Test response", "returncode": 0})


class RunJikanImportView(APIView):
    """Запуск обновления анонсов из Jikan"""

    permission_classes = [IsAdminUser]

    def post(self, request):
        script_path = request.data.get("script_path", "").strip()
        if not script_path:
            return Response({"error": "Не указан путь к скрипту"}, status=400)

        # Проверяем, что путь безопасный (внутри проекта)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if not os.path.abspath(script_path).startswith(project_root):
            return Response({"error": "Недопустимый путь к скрипту"}, status=400)

        if not os.path.exists(script_path):
            return Response({"error": f"Файл не найден: {script_path}"}, status=400)

        try:
            # Запуск скрипта
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=180,
            )  # 3 мин таймаут

            log = result.stdout
            if result.stderr:
                log += "\nSTDERR:\n" + result.stderr

            return Response(
                {
                    "success": result.returncode == 0,
                    "log": log,
                    "returncode": result.returncode,
                }
            )

        except subprocess.TimeoutExpired:
            return Response(
                {"error": "Обновление превысило время ожидания (3 мин)"}, status=500
            )
        except Exception as e:
            return Response({"error": str(e)}, status=500)
