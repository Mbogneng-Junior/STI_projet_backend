from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ApprenantViewSet, 
    BadgeViewSet, 
    ProfilEtudiantViewSet, 
    NiveauCompetenceViewSet,
    QuestionProfilingViewSet,
    StudentDashboardViewSet
)

router = DefaultRouter()
router.register(r'apprenants', ApprenantViewSet)
router.register(r'badges', BadgeViewSet)
router.register(r'profils', ProfilEtudiantViewSet)
router.register(r'niveaux-competence', NiveauCompetenceViewSet)
router.register(r'questions-profiling', QuestionProfilingViewSet)
router.register(r'dashboard', StudentDashboardViewSet, basename='student-dashboard')

urlpatterns = [
    path('', include(router.urls)),
]
