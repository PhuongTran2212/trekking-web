# trekking_project/settings.py

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-Thanh7778' # Giữ nguyên key tự tạo của dự án của bạn

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles', # Đã có sẵn, rất tốt
    'tinymce',
    
    # KHAI BÁO CÁC APP CỦA BẠN
    'core.apps.CoreConfig',
    'accounts.apps.AccountsConfig',
    'treks.apps.TreksConfig',
    'trips.apps.TripsConfig',
    'community.apps.CommunityConfig',
    'knowledge.apps.KnowledgeConfig',
    'gamification.apps.GamificationConfig',
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

ROOT_URLCONF = 'trekking_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'trekking_project.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'trekking_db',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '3307',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    # ... (giữ nguyên)
]


# Internationalization
LANGUAGE_CODE = 'vi-vn'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I1N = True
USE_TZ = True


# ==============================================================================
# === PHẦN CẤU HÌNH STATIC & MEDIA (ĐÃ ĐƯỢC DỌN DẸP VÀ SỬA LỖI) ===
# ==============================================================================

# URL để truy cập các file tĩnh (CSS, JS) trong trình duyệt
STATIC_URL = 'static/'

# Đường dẫn đến thư mục chứa các file tĩnh chung của project
# SỬA LỖI: Sử dụng BASE_DIR / 'static' cho cú pháp Pathlib hiện đại
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# URL để truy cập các file do người dùng upload (ảnh, video)
MEDIA_URL = '/media/'

# Đường dẫn đến thư mục chứa các file media trên server
MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
TINYMCE_DEFAULT_CONFIG = {
    "height": "320px",
    "width": "100%",
    "menubar": "file edit view insert format tools table help",
    "plugins": "advlist autolink lists link image charmap print preview anchor searchreplace visualblocks code "
    "fullscreen insertdatetime media table paste code help wordcount spellchecker",
    "toolbar": "undo redo | bold italic underline strikethrough | fontselect fontsizeselect formatselect | alignleft "
    "aligncenter alignright alignjustify | outdent indent |  numlist bullist checklist | forecolor "
    "backcolor casechange permanentpen formatpainter removeformat | pagebreak | charmap emoticons | "
    "fullscreen  preview save print | insertfile image media pageembed template link anchor codesample | "
    "a11ycheck ltr rtl | showcomments addcomment code",
    "custom_undo_redo_levels": 10,
    "language": "vi",  # Hỗ trợ tiếng Việt
}

# --- ĐÃ XÓA CÁC DÒNG BỊ LẶP LẠI VÀ LỖI CHÍNH TẢ Ở CUỐI FILE ---