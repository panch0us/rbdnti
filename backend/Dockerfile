FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# СОЗДАЕМ ПАПКИ ДЛЯ ДАННЫХ ВНУТРИ ПРОЕКТА
RUN mkdir -p /app/rbdnti/data/db /app/rbdnti/data/media /app/rbdnti/data/staticfiles

EXPOSE 8000

CMD ["sh", "-c", "cd /app/rbdnti && python manage.py makemigrations news_site --noinput && python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn rbdnti.wsgi:application --bind 0.0.0.0:8000 --workers 3"]