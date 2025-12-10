from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SessionApprentissageViewSet, InteractionViewSet

router = DefaultRouter()
router.register(r'sessions', SessionApprentissageViewSet)
router.register(r'interactions', InteractionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
