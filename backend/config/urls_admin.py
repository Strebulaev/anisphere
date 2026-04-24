from django.urls import path
from .views_admin import RunKodikImportView, RunJikanImportView

urlpatterns = [
    path("admin/run-kodik-import/", RunKodikImportView.as_view()),
    path("admin/run-jikan-import/", RunJikanImportView.as_view()),
]
