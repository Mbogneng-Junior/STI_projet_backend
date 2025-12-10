# config/urls.py

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    # 1. Route pour l'interface d'administration de Django
    path('admin/', admin.site.urls),

    # 2. Routes pour la documentation de l'API (Swagger/OpenAPI)
    #    Cette route génère le fichier "schema.yml" qui décrit votre API
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    #    Cette route affiche l'interface utilisateur de Swagger
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    #    (Optionnel) Une autre interface de documentation appelée Redoc
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),


    # 3. Routes pour VOS applications (À AJOUTER PLUS TARD)
    #    Quand vous créerez les endpoints pour vos modules, vous les ajouterez ici.
    path('api/v1/expert/', include('module_expert.urls')),
    path('api/v1/apprenant/', include('module_apprenant.urls')),
    path('api/v1/interface/', include('module_interface.urls')),
]