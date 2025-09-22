# settings.py

from pathlib import Path
import os
import dj_database_url # 👈 Adicionado para configurar o banco de dados a partir de uma URL

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- INÍCIO DAS MODIFICAÇÕES DE SEGURANÇA ---

# Carrega a SECRET_KEY de uma variável de ambiente. NUNCA deixe a chave no código.
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-fallback-key-for-development')

# DEBUG é 'True' apenas se a variável de ambiente DEBUG for 'True', senão é 'False'.
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Configura os hosts permitidos a partir de uma variável de ambiente.
# No Render, ele automaticamente provê a variável RENDER_EXTERNAL_HOSTNAME.
ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# --- FIM DAS MODIFICAÇÕES DE SEGURANÇA ---


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # 👈 Adicionado para WhiteNoise
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'app',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # 👈 Adicionado WhiteNoise
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

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

WSGI_APPLICATION = 'backend.wsgi.application'


# --- MODIFICAÇÃO DO BANCO DE DADOS ---
# Usa PostgreSQL em produção (via DATABASE_URL do Render) e SQLite em desenvolvimento.
if 'DATABASE_URL' in os.environ:
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
# --- FIM DA MODIFICAÇÃO DO BANCO DE DADOS ---


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

# Internationalization
LANGUAGE_CODE = 'pt-br' # Modificado para português do Brasil
TIME_ZONE = 'America/Sao_Paulo' # Modificado para o fuso horário de São Paulo
USE_I18N = True
USE_TZ = True


# --- MODIFICAÇÃO DOS ARQUIVOS ESTÁTICOS (PARA PRODUÇÃO) ---
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') # Diretório onde os arquivos estáticos serão coletados
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# --- FIM DA MODIFICAÇÃO DOS ARQUIVOS ESTÁTICOS ---


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- MODIFICAÇÃO DO CORS (MAIS SEGURO) ---
# Em vez de permitir tudo, especifique a origem do seu frontend
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000", # Para desenvolvimento local do frontend
    "https://seu-frontend.onrender.com", # Adicione a URL do seu frontend no Render
]
# Se você realmente precisa permitir todos, use CORS_ALLOW_ALL_ORIGINS = True, mas não é recomendado.
# --- FIM DA MODIFICAÇÃO DO CORS ---


# --- MODIFICAÇÃO DA CONFIGURAÇÃO DE E-MAIL (MAIS SEGURO) ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER') # Carrega de variável de ambiente
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD') # Carrega de variável de ambiente
# --- FIM DA MODIFICAÇÃO DE E-MAIL ---