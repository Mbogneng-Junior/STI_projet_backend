from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DomaineMedicalViewSet, 
    ExpertHumainViewSet, 
    ExpertIAViewSet, 
    CasCliniqueViewSet, 
    EtapeCliniqueViewSet
)

router = DefaultRouter()
router.register(r'domaines', DomaineMedicalViewSet)
router.register(r'experts-humains', ExpertHumainViewSet)
router.register(r'experts-ia', ExpertIAViewSet)
router.register(r'cas-cliniques', CasCliniqueViewSet)
router.register(r'etapes-cliniques', EtapeCliniqueViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
