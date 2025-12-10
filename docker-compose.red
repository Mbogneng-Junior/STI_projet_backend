version: '3.9'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: backendsti
      POSTGRES_USER: backendsti
      POSTGRES_PASSWORD: backendsti
    volumes:
      - postgres_data_v2:/var/lib/postgresql/data
    ports:
      - "5433:5432"

  web:
    build: .
    command: sh -c "python wait_for_db.py && python manage.py migrate && python3 manage.py runserver 0.0.0.0:8000"
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      - DJANGO_SUPERUSER_USERNAME=admin
      - DJANGO_SUPERUSER_PASSWORD=admin
      - DJANGO_SUPERUSER_EMAIL=admin@example.com
      - DB_NAME=backendsti
      - DB_USER=backendsti
      - DB_PASSWORD=backendsti
      - DB_HOST=db
      - DB_PORT=5432

volumes:
  postgres_data_v2:
