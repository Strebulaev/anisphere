

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from .models import Report, Post, PostComment


# ==================== MODERATION REPORTS ====================


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_reports(request):
    """Получить список жалоб (только для модераторов/админов)"""
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Пагинация
        page = int(request.query_params.get("page", 1))
        per_page = int(request.query_params.get("per_page", 20))
        offset = (page - 1) * per_page

        # Фильтры
        status_filter = request.query_params.get("status")
        content_type_filter = request.query_params.get("content_type")
        reason_filter = request.query_params.get("reason")

        # Базовый запрос - все жалобы
        queryset = Report.objects.all().select_related("reporter")

        # Применяем фильтры
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if content_type_filter:
            queryset = queryset.filter(content_type=content_type_filter)
        if reason_filter:
            queryset = queryset.filter(reason=reason_filter)

        # Сортировка по дате создания (новые сначала)
        queryset = queryset.order_by("-created_at")

        # Пагинация
        total = queryset.count()
        reports_page = queryset[offset : offset + per_page]

        # Сериализация
        from .serializers import ReportSerializer

        reports_data = ReportSerializer(reports_page, many=True, context={"request": request}).data

        # Добавляем информацию о контенте
        for report_data in reports_data:
            content = None
            if report_data["content_type"] == "post":
                try:
                    post = Post.objects.get(id=report_data["content_id"])
                    content = {
                        "title": post.title,
                        "text": post.text[:200] if post.text else None,
                        "author": post.author.username,
                    }
                except Post.DoesNotExist:
                    pass
            elif report_data["content_type"] == "comment":
                try:
                    comment = PostComment.objects.get(id=report_data["content_id"])
                    content = {
                        "text": comment.text[:200] if comment.text else None,
                        "author": comment.author.username,
                    }
                except PostComment.DoesNotExist:
                    pass

            report_data["content_preview"] = content

        return Response(
            {
                "results": reports_data,
                "count": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page,
            }
        )
    except Exception as e:
        logger.error(f"Error in get_reports: {e}", exc_info=True)
        return Response({"error": "Ошибка при загрузке жалоб", "detail": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminUser])
def resolve_report(request, report_id):
    """Решить жалобу (только для модераторов/админов)"""
    import logging

    logger = logging.getLogger(__name__)

    try:
        report = get_object_or_404(Report, id=report_id)

        # Проверяем статус
        if report.status != "pending":
            return Response(
                {"error": "Жалоба уже рассмотрена"}, status=400
            )

        # Получаем статус из запроса
        status = request.data.get("status")
        if status not in ["resolved", "rejected"]:
            return Response(
                {"error": "Недопустимый статус. Используйте 'resolved' или 'rejected'"},
                status=400,
            )

        # Обновляем жалобу
        report.status = status
        report.resolved_by = request.user
        report.resolved_at = timezone.now()

        # Комментарий модератора (опционально)
        comment = request.data.get("moderator_comment", "")
        if comment:
            report.moderation_comment = comment

        report.save()

        logger.info(
            f"Report {report_id} resolved by {request.user.username} as {status}"
        )

        return Response(
            {
                "success": True,
                "message": f"Жалоба {status}",
                "report": {
                    "id": report.id,
                    "status": report.status,
                    "resolved_by": request.user.username,
                    "resolved_at": report.resolved_at.isoformat(),
                },
            }
        )
    except Exception as e:
        logger.error(f"Error in resolve_report {report_id}: {e}", exc_info=True)
        return Response(
            {"error": "Ошибка при решении жалобы", "detail": str(e)}, status=500
        )
