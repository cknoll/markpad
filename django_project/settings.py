"""
Django settings for markpad django project.
"""

import os
import sys
import deploymentutils as du


# this allows: `export PELIANGO_CONFIG=/path/to/config.ini; manage.py runserver`
configpath = os.getenv("PELIANGO_CONFIG", "config-production.ini")

# export DJANGO_DEVMODE=True; py3 manage.py custom_command
env_devmode = os.getenv("DJANGO_DEVMODE")
if env_devmode is None:
    DEVMODE = "runserver" in sys.argv
else:
    DEVMODE = env_devmode.lower() == "true"


cfg = du.get_nearest_config(configpath, devmode=DEVMODE)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = cfg("SECRET_KEY")


URL_ENCRYPTION_KEY = cfg("URL_ENCRYPTION_KEY").encode("utf8")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = cfg("DEBUG")

ALLOWED_HOSTS = cfg("ALLOWED_HOSTS", cast=cfg.Csv())

DJANGO_URL_PREFIX = cfg("django_url_prefix").lstrip("/")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # for improved testing experience
    "django_nose",
    # necessary utility package
    "django_bleach",
    # the actual app
    "mainapp.apps.MainAppConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # 'django.middleware.csrf.CsrfViewMiddleware',
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "django_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "django_project.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASEDIR, "db.sqlite3"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


TEST_RUNNER = "django_nose.NoseTestSuiteRunner"

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

# this is the url used for static files of this project
STATIC_URL = f'/{cfg("static_url_prefix")}/'

# this is the target directory of `python manage.py collectstatic`
# the files might be copied to anotherplace during deployment
STATIC_ROOT = cfg("STATIC_ROOT").replace("__BASEDIR__", BASEDIR)

SITE_ID = 1

BLEACH_ALLOWED_TAGS = [
    "p",
    "b",
    "i",
    "u",
    "em",
    "strong",
    "a",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "ul",
    "ol",
    "li",
    "pre",
    "code",
    "hr",
    "br",
    "span",
    "div",
    "script",
    "blockquote"
]

# to get meaningful results here, run `touch requirements.txt` during deployment (see deploy.py)
LAST_DEPLOYMENT = du.get_deployment_date(os.path.join(BASEDIR, "requirements.txt"))


def allow_attributes(tag, name, value):
    """
    Use callable to decide which attributes we allow.
    Background: "script" should only be allowed for type="math/tex".

    see also: https://bleach.readthedocs.io/en/latest/clean.html#allowed-tags-tags
    """
    if name in ['href', 'title', 'style']:
        return True
    elif tag in ("span", "div") and name == "class":
        return True
    elif tag == "script" and name == "type" and value.startswith("math/tex"):
        return True
    else:
        return False


BLEACH_ALLOWED_ATTRIBUTES = allow_attributes


# MARKDOWNIFY_WHITELIST_TAGS defaults to bleach.sanitizer.ALLOWED_TAGS
MARKDOWNIFY_STRIP = False
