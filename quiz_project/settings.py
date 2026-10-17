"""
Django settings for quiz_project project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# BASE_DIR yo'li
BASE_DIR = Path(__file__).resolve().parent.parent

# .env faylini yuklash
load_dotenv(BASE_DIR / '.env')

# Xavfsizlik kaliti
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-zvk6%7homa2!9rr23jhcg#r70ctj6)iq*mkwdj5en&sd@hz5_&'
)

# Debug rejimi
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 't', 'yes')

# Ruxsat berilgan hostlar
raw_hosts = os.environ.get('ALLOWED_HOSTS', '*')
if raw_hosts == '*':
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = [h.strip() for h in raw_hosts.split(',') if h.strip()]

# Vercel proxy orqali HTTPS
if os.environ.get('VERCEL') == '1':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CSRF ishonchli manbalar (Vercel / production)
raw_csrf = os.environ.get('CSRF_TRUSTED_ORIGINS', '').strip()
if raw_csrf:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in raw_csrf.split(',') if o.strip()]
elif os.environ.get('VERCEL') == '1':
    CSRF_TRUSTED_ORIGINS = ['https://*.vercel.app']

# Ilovalar ro'yxati
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Loyiha ilovalari
    'quiz.apps.QuizConfig',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'quiz_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'quiz_project.wsgi.application'

# Ma'lumotlar bazasi (Neon Postgres yoki lokal SQLite)
DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()

# Vercel serverless'da ulanishlarni saqlamaslik kerak
_is_serverless = os.environ.get('VERCEL') == '1'
_conn_max_age = 0 if _is_serverless else 600

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=_conn_max_age,
            conn_health_checks=not _is_serverless,
        )
    }
    DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'OPTIONS': {
                'timeout': 20,
            }
        }
    }

# Parol tekshiruvi
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Til va vaqt
LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

# Statik fayllar (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Admin tizimi sozlamalari
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
SESSION_SECRET = os.environ.get(
    'SESSION_SECRET', 
    'quiz_local_jwt_session_secret_32_characters_long_key_12345'
)
