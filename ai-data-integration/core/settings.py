from pathlib import Path
import os 
import dotenv
from datetime import datetime

dotenv.load_dotenv()

dbname = os.getenv(key = "POSTGRES_DATABASE")
dbhost = os.getenv(key = "POSTGRES_HOST")
dbport = os.getenv(key = "POSTGRES_PORT")
dbuser = os.getenv(key = "POSTGRES_USER")
dbpassword = os.getenv(key = "POSTGRES_PASSWORD")


AWS_ACCESS_KEY_ID = os.getenv(key="AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv(key="AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv(key="AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.getenv(key="AWS_S3_REGION_NAME")  # Set your region here
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
AWS_S3_OBJECT_PARAMETERS = {
"CacheControl": "max-age=86400",
}
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"    
BASE_DIR = Path(__file__).resolve().parent.parent
current_date = str(datetime.now().date())

LOG_DIR = BASE_DIR / 'logs' / current_date
LOG_DIR.mkdir(parents=True, exist_ok=True)  # This will create any missing parent directories

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'verbose': {
            'format': '%(asctime)s [%(levelname)s] %(name)s [%(filename)s:%(lineno)d]: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'application.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 10,
            'formatter': 'standard',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'errors.log',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'console', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django': {
            'handlers': ['default', 'error_file',],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

SECRET_KEY ='django-insecure-cblh%7!puoz38h$1lb4p2sl@ggsop7e2k5jlxdj##&cqj48ht5'

DEBUG =  os.getenv(key='DEBUG')

ALLOWED_HOSTS = ["*"]

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'deficiency_reports',
    'storages',
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

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'core.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': dbname,
        'USER': dbuser,
        'PASSWORD': dbpassword,
        'HOST':dbhost,
        'PORT': dbport,
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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_ROOT = '/static/'
STATIC_URL = '/static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',  # Add this
        # 'rest_framework_simplejwt.authentication.JWTAuthentication',
        
        # 'rest_framework.authentication.SessionAuthentication',  # Optional
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema', 
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Inspect Point API",
}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'basic': {
            'type': 'basic'
        }
    },
}
CORS_ALLOW_ALL_ORIGINS = True