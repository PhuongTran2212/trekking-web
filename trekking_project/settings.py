import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-Thanh7778'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# ==============================================================================
# === APPLICATION DEFINITION (Đã gộp đầy đủ các App) ===
# ==============================================================================
INSTALLED_APPS = [
    # 1. Django Default Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize', # Giữ cái này của bạn bạn (rất hữu ích để format số)

    # 2. Third Party Apps
    'tinymce',
    'taggit', # App quản lý tag của bạn

    # 3. Local Apps (Của cả 2 người)
    'core.apps.CoreConfig',
    'accounts.apps.AccountsConfig',
    'treks.apps.TreksConfig',
    'trips.apps.TripsConfig',
    'community.apps.CommunityConfig',    # Của bạn bạn
    'knowledge.apps.KnowledgeConfig',    # Của bạn bạn
    'gamification.apps.GamificationConfig', # Của bạn bạn
    'post.apps.PostConfig',              # Của bạn
    'report_admin.apps.ReportAdminConfig', # Của bạn
    'articles.apps.ArticlesConfig',      # Của bạn
    'user_admin.apps.UserAdminConfig',   # Của bạn (Mới)
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


# ==============================================================================
# === DATABASE ===
# Lưu ý: Đang dùng Port 3306 (Của bạn). 
# Nếu máy bạn đổi port XAMPP sang 3307 thì sửa lại dòng 'PORT' bên dưới.
# ==============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'trekking_db',
        'USER': 'root',
        'PASSWORD': '1234',
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
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# ==============================================================================
# === INTERNATIONALIZATION & FORMATTING ===
# ==============================================================================
LANGUAGE_CODE = 'vi-vn' # Tiếng Việt
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_L10N = True
USE_TZ = True # Khuyến nghị dùng True để quản lý giờ giấc chuẩn quốc tế

# Định dạng số (Lấy của bạn bạn - Rất tốt cho hiển thị tiền tệ VN)
USE_THOUSAND_SEPARATOR = True 
NUMBER_GROUPING = 3
THOUSAND_SEPARATOR = '.' # Dấu chấm phân cách hàng nghìn (VD: 100.000)
DECIMAL_SEPARATOR = ','  # Dấu phẩy phân cách thập phân


# ==============================================================================
# === STATIC & MEDIA FILES ===
# ==============================================================================
STATIC_URL = '/static/'
# Sử dụng cú pháp hiện đại kết hợp os.path.join cho chắc chắn
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# === TINYMCE CONFIG (Gộp cấu hình tối ưu) ===
# ==============================================================================
TINYMCE_DEFAULT_CONFIG = {
    "height": "500px", # Giữ độ cao lớn của bạn cho dễ nhìn
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
    "language": "vi",  # Giữ tiếng Việt của bạn bạn
}
