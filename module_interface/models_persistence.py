from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class PersistentSession(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    app_name = models.CharField(max_length=100)
    state = models.JSONField(default=dict)
    last_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session {self.id} ({self.user})"

class SessionEvent(models.Model):
    session = models.ForeignKey(PersistentSession, on_delete=models.CASCADE, related_name='events')
    author = models.CharField(max_length=100)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    state_delta = models.JSONField(default=dict)

    def __str__(self):
        return f"Event {self.id} in Session {self.session_id}"

class SessionMemory(models.Model):
    session = models.ForeignKey(PersistentSession, on_delete=models.CASCADE, related_name='memories')
    key = models.CharField(max_length=255)
    value = models.JSONField()
    scope = models.CharField(max_length=20, choices=[('session', 'Session'), ('user', 'User'), ('app', 'App')], default='session')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Memory {self.key} (scope: {self.scope})"
