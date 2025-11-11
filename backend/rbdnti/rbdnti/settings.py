"""
Django settings for rbdnti project adapted for Docker production deployment.
"""

from pathlib import Path
import os

# BASE_DIR = /app/rbdnti
BASE_DIR = Path(__file__).resolve().parent.parent

# Простая загрузка .env
env_path = BASE_DIR.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ.setdefault(key, value)

# SECRET_KEY & DEBUG
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-fallback-key")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set in .env file!")

DEBUG = os.getenv("DEBUG", "False").lower() in ("1", "true", "yes")

# ALLOWED_HOSTS
raw_hosts = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost")
ALLOWED_HOSTS = [h.strip() for h in raw_hosts.split(",") if h.strip()]

# ⬇️ ДОБАВЛЕНО: Настройки для больших файлов (5GB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 5368709120  # 5GB в байтах
FILE_UPLOAD_MAX_MEMORY_SIZE = 5368709120  # 5GB в байтах
DATA_UPLOAD_MAX_NUMBER_FIELDS = 5000      # Увеличиваем лимит полей

# ⬇️ ДОБАВЛЕНО: Настройки прав для файлов
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

INSTALLED_APPS = [
    'news_site.apps.NewsSiteConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ckeditor',
    'ckeditor_uploader',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'news_site.middleware.StatisticsMiddleware',
]

ROOT_URLCONF = 'rbdnti.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'rbdnti.wsgi.application'

# SQLite — в папке /app/rbdnti/db/db.sqlite3
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db' / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'news_site' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CKEditor settings
CKEDITOR_UPLOAD_PATH = "news_files/ckeditor_uploads/"
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-',
             'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink'],
            ['Image', 'Table', 'HorizontalRule', 'Smiley', 'SpecialChar'],
            ['RemoveFormat', 'Source']
        ],
        'height': 300,
        'width': '100%',
        'language': 'ru',
    },
}