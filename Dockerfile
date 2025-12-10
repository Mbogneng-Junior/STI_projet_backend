FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/

# Création d'un utilisateur non-root pour la sécurité
RUN adduser --disabled-password --no-create-home appuser
USER appuser

# Commande de lancement pour la production avec Gunicorn
CMD ["sh", "-c", "python wait_for_db.py && python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:8000"]
