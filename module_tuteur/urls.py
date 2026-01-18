from django.urls import path
from .views import TuteurViewSet


# On mappe manuellement les méthodes du ViewSet aux URLs
urlpatterns = [
    # Route pour démarrer la session (POST)
    path(
        'session/start/', 
        TuteurViewSet.as_view({'post': 'create_session'}), 
        name='tuteur-start-session'
    ),
    
    # Route pour envoyer une réponse et obtenir un feedback (POST)
    path(
        'session/analyser/', 
        TuteurViewSet.as_view({'post': 'analyser_reponse'}), 
        name='tuteur-analyser-reponse'
    ),
    
    # Route pour terminer la session (POST)
    path(
        'session/end/', 
        TuteurViewSet.as_view({'post': 'terminer_session'}), 
        name='tuteur-end-session'
    ),

    path('session/<str:session_id>/state/', TuteurViewSet.as_view({'get': 'get_state'})),
   
]