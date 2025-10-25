import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-u$y90evy-ca)59%h1i@=5p8&8lw8+hhiwjj=e&gco=@ofyu&&z'
RESERVATIONS_GATEWAY_TOKEN = os.getenv("RESERVATION_TOKEN")
AUTH_SERVICE_TOKEN = os.getenv("AUTH_SERVICE_TOKEN")
HOTELS_GATEWAY_TOKEN = os.getenv("HOTEL_SERVICE_TOKEN")
NOTIFICATION_TOKEN = os.getenv("NOTIFICATION_TOKEN")

GATEWAY_SERVICE_URL = os.getenv("GATEWAY_SERVICE_URL")
AUTH_SERVICE_URL = os.getenv("USERS_SERVICE_URL")
HOTELS_SERVICE_URL = os.getenv("HOTELS_SERVICE_URL")
RESERVATIONS_SERVICE_URL = os.getenv("RESERVATIONS_SERVICE_URL")
NOTIFICATIONS_SERVICE_URL = os.getenv("NOTIFICATIONS_SERVICE_URL")
DEBUG = True

ALLOWED_HOSTS = ["*"]


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'llama'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

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

LANGUAGE_CODE = 'es-MX'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
