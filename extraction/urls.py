"""
URLs pour l'app Extraction
Projet STI 5GI
"""

from django.urls import path
from . import views

app_name = 'extraction'

urlpatterns = [
    # Rafraîchissement des cas (admin uniquement)
    path('refresh/', views.refresh_cases, name='refresh_cases'),

    # Export
    path('export/json/', views.export_json, name='export_json'),
    path('export/csv/', views.export_csv, name='export_csv'),

    # Filtres disponibles
    path('filters/', views.get_export_filters, name='export_filters'),

    # Statistiques
    path('stats/', views.get_extraction_stats, name='extraction_stats'),
]
