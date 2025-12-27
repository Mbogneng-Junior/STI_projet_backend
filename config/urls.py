# config/urls.py

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from module_auth.views import RegisterView, LoginView, LogoutView
from module_auth.views import (
    RegisterView, LoginView, LogoutView, 
    ExpertRegisterView, ExpertLoginView
)

urlpatterns = [
    # 1. Route pour l'interface d'administration de Django
    path('admin/', admin.site.urls),

    # 2. Routes pour la documentation de l'API (Swagger/OpenAPI)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # Interface Swagger UI (pour tester)
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Interface Redoc (optionnel)
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),


    # 3. Routes des modules de l'application
    path('api/v1/expert/', include('module_expert.urls')),
    path('api/v1/apprenant/', include('module_apprenant.urls')),
    path('api/v1/interface/', include('module_interface.urls')),
    
    # AJOUT : Route pour le Tuteur Intelligent (Chat & Logique Pédagogique)
    path('api/v1/tuteur/', include('module_tuteur.urls')),
    path('api/v1/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/v1/auth/login/', LoginView.as_view(), name='auth_login'),
    path('api/v1/auth/logout/', LogoutView.as_view(), name='auth_logout'),
    # --- NOUVELLES ROUTES POUR LES EXPERTS ---
    path('api/v1/auth/expert/register/', ExpertRegisterView.as_view(), name='auth_expert_register'),
    path('api/v1/auth/expert/login/', ExpertLoginView.as_view(), name='auth_expert_login'),
]