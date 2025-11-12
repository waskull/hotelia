from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")
RESERVATION_TOKEN = os.getenv("RESERVATION_TOKEN")
HOTEL_SERVICE_TOKEN = os.getenv("HOTEL_SERVICE_TOKEN")
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if os.getenv("DEBUG", "False") == "True" else False
ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'gateway',
    'drf_spectacular',
    'drf_spectacular_sidecar',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False, # Permite que se utilicen loggers preexistentes (como 'django')

    'formatters': {
        # Define cómo se ve cada línea de log
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },

    'handlers': {
        # Define dónde van los logs
        'console': {
            'level': 'INFO', # Nivel mínimo para el output de la consola
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'DEBUG', # Nivel mínimo para el output del archivo
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'gateway.log'), # Ruta del archivo de log
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },

    'loggers': {
        # Define qué loggers existen y qué handlers usan
        '': {  # Logger "root" (captura todo lo que no tiene un logger más específico)
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': { # Logs específicos de las peticiones HTTP (DRF)
            'handlers': ['console'],
            'level': 'WARNING', # Por defecto, Django sólo loggea WARNING o superior de peticiones
            'propagate': False,
        },
        'gateway': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        }
    }
}

ROOT_URLCONF = 'core.urls'

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
ASGI_APPLICATION = 'core.asgi.application'
WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

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
]

USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL")
HOTELS_SERVICE_URL = os.getenv("HOTELS_SERVICE_URL")
RESERVATIONS_SERVICE_URL = os.getenv("RESERVATIONS_SERVICE_URL")
CHATBOT_SERVICE_URL = os.getenv("CHATBOT_SERVICE_URL")

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'gateway.auth_schemes.ExternalServiceAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

LANGUAGE_CODE = 'es-MX'

TIME_ZONE = 'America/Caracas'

USE_I18N = True

USE_TZ = True

SPECTACULAR_SETTINGS = {
    'TITLE': 'Hotelia GATEWAY',
    'DESCRIPTION': 'Gateway API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayRequestDuration': True,
    },
    # 'AUTHENTICATION_SCHEMES': {
    #     'jwt': {
    #         'type': 'http',
    #         'scheme': 'bearer',
    #         'bearerFormat': 'JWT',
    #     },
    # },
    # 'SECURITY': [
    #     {
    #         'jwt': [],
    #         'BearerAuth': [],
    #     },
    # ],
    # 'COMPONENTS': {
    #     'securitySchemes': {
    #         'BearerAuth': {
    #             'type': 'http',
    #             'scheme': 'bearer',
    #             'bearerFormat': 'JWT',
    #         }
    #     }
    # }
}


STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')



DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
