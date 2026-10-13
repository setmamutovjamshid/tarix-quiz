"""
URL configuration for quiz_project project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Maxsus Quiz va Admin paneli marshrutlari
    path('', include('quiz.urls')),
    # Ixtiyoriy Django standart superuser admini
    path('django-admin/', admin.site.urls),
]
