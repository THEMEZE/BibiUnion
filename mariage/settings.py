import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================
# SÉCURITÉ
# ============================================
# IMPORTANT : changez cette clé en production
SECRET_KEY = 'django-insecure-CHANGEZ-MOI-AVEC-UNE-VRAIE-CLE-SECRETE-AVANT-DEPLOIEMENT'

DEBUG = False

# Domaines autorisés (ajoutez votre domaine Cloudflare)
ALLOWED_HOSTS = [
    'likewise-reporters-health-null.trycloudflare.com',
    'localhost',
    '127.0.0.1',
]

# Cloudflare Tunnel transmet en HTTPS -> faire confiance au header proxy
CSRF_TRUSTED_ORIGINS = [
    'https://likewise-reporters-health-null.trycloudflare.com',
]

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ============================================
# APPLICATIONS
# ============================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'gallery',
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

ROOT_URLCONF = 'mariage.urls'

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

WSGI_APPLICATION = 'mariage.wsgi.application'

# ============================================
# BASE DE DONNÉES
# ============================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ============================================
# VALIDATION MOTS DE PASSE (admin)
# ============================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================
# INTERNATIONALISATION
# ============================================
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# ============================================
# FICHIERS STATIQUES ET MEDIA
# ============================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================
# UPLOAD - LIMITES DE TAILLE
# ============================================
# 50 Mo par fichier (photos HEIC peuvent être volumineuses)
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 Mo

# Extensions et types MIME autorisés
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'heic', 'webp']
ALLOWED_IMAGE_MIME_TYPES = [
    'image/jpeg',
    'image/png',
    'image/heic',
    'image/heif',
    'image/webp',
]

# Redimensionnement max
MAX_IMAGE_WIDTH = 1920
THUMBNAIL_WIDTH = 400

# URL publique du site (pour le QR Code)
SITE_PUBLIC_URL = 'https://likewise-reporters-health-null.trycloudflare.com'

# Liste des tables (modifiable selon votre plan de salle)
TABLE_CHOICES = [
    ('', 'Aucune table'),
    ('1', 'Table 1'),
    ('2', 'Table 2'),
    ('3', 'Table 3'),
    ('4', 'Table 4'),
    ('5', 'Table 5'),
    ('6', 'Table 6'),
    ('7', 'Table 7'),
    ('8', 'Table 8'),
    ('honneur', "Table d'honneur"),
]

# Session settings - login admin
LOGIN_URL = '/admin/login/'
