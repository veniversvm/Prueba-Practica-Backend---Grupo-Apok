"""
Django settings for app_nodos project.
Adaptado para soportar Django runserver (desarrollo) y Uvicorn (producción)
"""

from datetime import timedelta
from pathlib import Path
import os
import sys

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ====================== SEGURIDAD ======================
SECRET_KEY = os.environ.get("SECRET_KEY") or os.environ.get("DB_KEY", "dev-secret-key-change-in-production")

DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',')

# ====================== APLICACIONES ======================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'corsheaders',  # Agregado para CORS
    'nodes',
    'users',
]

# ====================== MIDDLEWARE ======================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # Agregado
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'middleware.timezone_middleware.TimezoneMiddleware',
]

# ====================== REST FRAMEWORK ======================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # Throttling para producción
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/hour',
    }
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Tree Management API',
    'DESCRIPTION': 'API para gestionar árboles de nodos con soporte multi-idioma',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAuthenticated'],
}

# ====================== BASE DE DATOS ======================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "tree_db"),
        "USER": os.environ.get("POSTGRES_USER", "tree_user"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "tree_password"),
        "HOST": os.environ.get("POSTGRES_HOST", "pgbouncer"),  # Por defecto a pgbouncer
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        # Optimizaciones para producción
        'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '300')),  # 5 minutos
        'OPTIONS': {
            'connect_timeout': 10,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5,
        }
    }
}

# --- LÓGICA DE BYPASS PARA TESTS ---
if 'test' in sys.argv:
    DATABASES['default']['HOST'] = 'db'
    DATABASES['default']['PORT'] = '5432'

# ====================== CACHE DINÁMICO ======================
# Cache por defecto (desarrollo)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "node-cache",
        "TIMEOUT": 180,  # 3 minutos
    }
}

# Si hay Redis configurado (producción)
if os.environ.get('REDIS_HOST'):
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"redis://{os.environ.get('REDIS_HOST', 'redis')}:6379/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "PARSER_CLASS": "redis.connection.HiredisParser",
                "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
                "CONNECTION_POOL_KWARGS": {
                    "max_connections": 50,
                    "retry_on_timeout": True
                },
                "SOCKET_CONNECT_TIMEOUT": 5,
                "SOCKET_TIMEOUT": 5,
            },
            "KEY_PREFIX": "tree",
            "TIMEOUT": 300,  # 5 minutos en producción
        }
    }
    # Usar Redis para sesiones en producción
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"

# ====================== JWT ======================
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    # Compatibilidad con Uvicorn
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}

# ====================== AUTENTICACIÓN ======================
AUTHENTICATION_BACKENDS = [
    'users.backends.EmailOrUsernameBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_USER_MODEL = 'users.User'

# ====================== CONFIGURACIONES ASGI/WSGI ======================
ROOT_URLCONF = 'app_nodos.urls'
WSGI_APPLICATION = 'app_nodos.wsgi.application'
ASGI_APPLICATION = 'app_nodos.asgi.application'  # Importante para Uvicorn

# ====================== TEMPLATES ======================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

# ====================== PASSWORD VALIDATION ======================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ====================== INTERNATIONALIZATION ======================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ====================== STATIC FILES ======================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles' if not DEBUG else None

# ====================== CORS (Cross-Origin Resource Sharing) ======================
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Solo en desarrollo

if not DEBUG:
    # Obtener la cadena cruda
    raw_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '')
    # Hacer split y filtrar cadenas vacías o espacios
    CORS_ALLOWED_ORIGINS = [
        origin.strip() for origin in raw_origins.split(',') if origin.strip()
    ]
else:
    CORS_ALLOWED_ORIGINS = []

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
]
CORS_ALLOW_HEADERS = [
    'authorization',
    'content-type',
    'accept',
    'origin',
    'user-agent',
    'accept-encoding',
    'accept-language',
    'time-zone',
]
# ====================== CONFIGURACIONES DE PRODUCCIÓN ======================
# Función auxiliar para leer booleanos del entorno
def get_bool_from_env(var_name, default_value='False'):
    return os.environ.get(var_name, default_value).lower() == 'true'


if not DEBUG:
    # SSL Redirect: Si es False, permite HTTP. Si es True, fuerza HTTPS.
    SECURE_SSL_REDIRECT = get_bool_from_env('SECURE_SSL_REDIRECT', 'False')
    
    # Cookies: Solo deben ser Secure si estamos en HTTPS
    SESSION_COOKIE_SECURE = get_bool_from_env('SESSION_COOKIE_SECURE', 'False')
    CSRF_COOKIE_SECURE = get_bool_from_env('CSRF_COOKIE_SECURE', 'False')
    
    # HSTS (HTTP Strict Transport Security)
    # Solo activarlo si realmente estamos forzando SSL
    if SECURE_SSL_REDIRECT:
        SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', 31536000))
        SECURE_HSTS_INCLUDE_SUBDOMAINS = get_bool_from_env('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True')
        SECURE_HSTS_PRELOAD = get_bool_from_env('SECURE_HSTS_PRELOAD', 'True')
    else:
        # Desactivar HSTS para evitar que el navegador/Postman fuerce HTTPS automáticamente
        SECURE_HSTS_SECONDS = 0
        SECURE_HSTS_INCLUDE_SUBDOMAINS = False
        SECURE_HSTS_PRELOAD = False

    # Proxies: Importante si usas Traefik/Nginx delante, o Docker
    # Si estás directo contra Uvicorn en Docker, esto suele estar bien, 
    # pero si da problemas puedes comentarlo o controlarlo con env.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # XSS y Content sniffing (seguridad estándar, no rompe HTTP)
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    
    # LOGGING (Tu configuración corregida para Docker - solo consola)
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                'style': '{',
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': True,
            },
            'django.request': {
                'handlers': ['console'],
                'level': 'ERROR',
                'propagate': False,
            },
            # Añade tus apps aquí si quieres ver sus logs
             'nodes': { 'handlers': ['console'], 'level': 'INFO', 'propagate': False },
             'users': { 'handlers': ['console'], 'level': 'INFO', 'propagate': False },
        },
    }
else:
    # Logging en desarrollo
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }

# ====================== CONFIGURACIONES ADICIONALES ======================
# Para Uvicorn
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# Django Channels (opcional, para WebSockets)
# ASGI_APPLICATION = "app_nodos.asgi.application"
# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels_redis.core.RedisChannelLayer",
#         "CONFIG": {
#             "hosts": [("redis", 6379)],
#         },
#     },
# }