# backend/Dockerfile
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

# copy project code (rbdnti/), but exclude data/ via .dockerignore
COPY rbdnti/ /app/rbdnti/

# Optional: create directories with permissive permissions for runtime user
RUN mkdir -p /app/rbdnti/data/db /app/rbdnti/data/media /app/rbdnti/data/staticfiles \
    && chown -R 1000:1000 /app/rbdnti || true

USER 1000

WORKDIR /app/rbdnti
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn rbdnti.wsgi:application --bind 0.0.0.0:8000 --workers 3"]
