"""
Django settings for lytyfy_rest project.

Generated by 'django-admin startproject' using Django 1.9.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '*4f*p6zb_%6*!!6do*-@_vg+pc))36%@zpiojxx786q$bve6w2'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

#SERVER IP
HOST_IP= "54.169.235.117"

#SERVER DOMAIN
HOST_DOMAIN= "dev.api.lytyfy.org"

#CLIENT DOMAIN
CLIENT_DOMAIN= "dev.lytyfy.org"

# Application definition

INSTALLED_APPS = [
    'lytyfy_rest',
    'rest_framework',
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lytyfy_rest.urls'

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

WSGI_APPLICATION = 'lytyfy_rest.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', 
        'NAME': 'develop',
        'USER': 'mrrobot',
        'PASSWORD': 'DiVaNe_47',
        'HOST': 'lytyfy-rds-dev.c4py8eplysvm.ap-southeast-1.rds.amazonaws.com',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Calcutta'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR,'static') 
STATIC_URL = '/static/'
CORS_ORIGIN_ALLOW_ALL = True

#EMAIL CONFIG
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'support@lytyfy.org'
EMAIL_HOST_PASSWORD = 'divane_47'

# AWS keys
AWS_ACCESS_KEY_ID = 'AKIAIDB6M7RJCSGQDLWQ'
AWS_SECRET_ACCESS_KEY = 'P6SiX5ABghiDM0im4Oj+iMtDsMidG2FUhoZSIyDe'
AWS_STORAGE_BUCKET_NAME = 'lytyfy'

# The region of your bucket, more info:
# http://docs.aws.amazon.com/general/latest/gr/rande.html#s3_region
S3DIRECT_REGION = 'ap-southeast-1'

# Destinations, with the following keys:
#
# key [required] Where to upload the file to
# auth [optional] An ACL function to whether the current user can perform this action
# allowed [optional] List of allowed MIME types
# acl [optional] Give the object another ACL rather than 'public-read'
# cache_control [optional] Cache control headers, eg 'max-age=2592000'
# content_disposition [optional] Useful for sending files as attachements
# bucket [optional] Specify a different bucket for this particular object
#
S3DIRECT_DESTINATIONS = {
    # Allow staff users to upload any MIME type
    'borrower_img': {
        'key': 'uploads/borrowers/images', 
        'auth': lambda u: u.is_staff,
        'allowed': ['image/jpeg', 'image/png'],
    },
}
