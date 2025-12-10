from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ApprenantViewSet, 
    BadgeViewSet, 
    ProfilEtudiantViewSet, 
    NiveauCompetenceViewSet
)

router = DefaultRouter()
router.register(r'apprenants', ApprenantViewSet)
router.register(r'badges', BadgeViewSet)
router.register(r'profils', ProfilEtudiantViewSet)
router.register(r'niveaux-competence', NiveauCompetenceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
