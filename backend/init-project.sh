#!/bin/bash
echo "Initializing Django project..."

cd /app/rbdnti

# Создаем миграции
python manage.py makemigrations news_site

# Применяем миграции
python manage.py migrate

# Собираем статику
python manage.py collectstatic --noinput

echo "Project initialization completed!"