#!/bin/bash
set -e

cd /app/rbdnti

echo "Applying database migrations..."
python manage.py makemigrations news_site --noinput || echo "No new migrations for news_site"
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Создаем суперпользователя если переменные окружения заданы
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print('Superuser created:', username)
else:
    print('Superuser already exists:', username)
"
fi

echo "Starting Gunicorn..."
exec gunicorn rbdnti.wsgi:application --bind 0.0.0.0:8000 --workers 3 --access-logfile -