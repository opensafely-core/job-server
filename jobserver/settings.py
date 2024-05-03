"""
Django settings for jobserver project.

Generated by 'django-admin startproject' using Django 3.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import re
from pathlib import Path

from django.contrib.messages import constants as messages
from django.urls import reverse_lazy
from environs import Env

from services.logging import logging_config_dict
from services.sentry import initialise_sentry


env = Env()
env.read_env()

# Build paths inside the project like this: BASE_DIR / ...
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("SECRET_KEY")

# Optional fallback for rotating the secret key.
# Any OLD_SECRET_KEY that is added should then be removed
# after the time in SESSION_COOKIE_AGE elapses.
# Refer to INSTALL.md for guidance.
OLD_SECRET_KEY = env.str("OLD_SECRET_KEY", default=None)
if OLD_SECRET_KEY is not None:
    SECRET_KEY_FALLBACKS = [OLD_SECRET_KEY]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False)

BASE_URL = env.str("BASE_URL", default="http://localhost:8000")

ALLOWED_HOSTS = ["*"]


# Application definition
INSTALLED_APPS = [
    "airlock",
    "applications",
    "interactive",
    "jobserver",
    "redirects",
    "staff",
    "anymail",
    "debug_toolbar",
    "django_browser_reload",
    "django_extensions",
    "django_htmx",
    "django_vite",
    "slippers",
    "rest_framework",
    "social_django",
    "zen_queries",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

MIDDLEWARE = [
    "redirects.middleware.RedirectsMiddleware",
    "jobserver.middleware.BrowserReloadMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django_permissions_policy.PermissionsPolicyMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_structlog.middlewares.RequestMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "csp.middleware.CSPMiddleware",
    "jobserver.middleware.XSSFilteringMiddleware",
    "jobserver.middleware.ClientAddressIdentification",
    "jobserver.middleware.TemplateNameMiddleware",
]

ROOT_URLCONF = "jobserver.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
                "jobserver.context_processors.can_view_staff_area",
                "jobserver.context_processors.staff_nav",
                "jobserver.context_processors.nav",
                "jobserver.context_processors.disable_creating_jobs",
                "jobserver.context_processors.login_url",
            ],
            "builtins": ["slippers.templatetags.slippers"],
        },
    },
]

WSGI_APPLICATION = "jobserver.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
DATABASES = {
    "default": env.dj_db_url("DATABASE_URL", default="postgres://localhost/jobserver")
}

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"


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


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/ref/contrib/staticfiles/#module-django.contrib.staticfiles
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# https://docs.djangoproject.com/en/4.2/howto/static-files/
# Note: these *must* be strings. If they are paths, we cannot cleanly extract them in ./scripts/collect-me-maybe.sh
BUILT_ASSETS = env.path("BUILT_ASSETS", default=BASE_DIR / "assets" / "dist")
STATICFILES_DIRS = [
    str(BASE_DIR / "static"),
    str(BUILT_ASSETS),
]
STATIC_ROOT = env.path("STATIC_ROOT", default=BASE_DIR / "staticfiles")
STATIC_URL = "/static/"

ASSETS_DEV_MODE = env.bool("ASSETS_DEV_MODE", default=False)

DJANGO_VITE = {
    "default": {
        "dev_mode": ASSETS_DEV_MODE,
        "manifest_path": BUILT_ASSETS / ".vite" / "manifest.json",
    }
}

# Vite generates files with 8 hash digits
# http://whitenoise.evans.io/en/stable/django.html#WHITENOISE_IMMUTABLE_FILE_TEST


def immutable_file_test(path, url):
    # Match filename with 12 hex digits before the extension
    # e.g. app.db8f2edc0c8a.js
    return re.match(r"^.+[\.\-][0-9a-f]{8,12}\..+$", url)


WHITENOISE_IMMUTABLE_FILE_TEST = immutable_file_test


# User uploaded files
# https://docs.djangoproject.com/en/4.0/topics/files/
MEDIA_ROOT = Path(env.str("MEDIA_STORAGE", default="uploads"))
MEDIA_URL = "/uploads/"


# Logging
# https://docs.djangoproject.com/en/3.1/topics/logging/
LOGGING = logging_config_dict


# Auth
AUTHENTICATION_BACKENDS = [
    "social_core.backends.github.GithubOAuth2",
    "django.contrib.auth.backends.ModelBackend",
]
AUTH_USER_MODEL = "jobserver.User"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_ERROR_URL = "/"
LOGIN_URL = reverse_lazy("login")
LOGIN_URL_TIMEOUT_MINUTES = 60
SOCIAL_AUTH_GITHUB_KEY = env.str("SOCIAL_AUTH_GITHUB_KEY")
SOCIAL_AUTH_GITHUB_SECRET = env.str("SOCIAL_AUTH_GITHUB_SECRET")
SOCIAL_AUTH_GITHUB_SCOPE = ["user:email"]

# Passwords
# https://docs.djangoproject.com/en/4.0/ref/settings/#password-hashers
PASSWORD_HASHERS = env.list(
    "PASSWORD_HASHERS",
    default=[
        "django.contrib.auth.hashers.Argon2PasswordHasher",
    ],
)


# Messages
# https://docs.djangoproject.com/en/3.0/ref/contrib/messages/
MESSAGE_TAGS = {
    messages.DEBUG: "alert-info",
    messages.INFO: "alert-info",
    messages.SUCCESS: "alert-success",
    messages.WARNING: "alert-warning",
    messages.ERROR: "alert-danger",
}


# Checks
# https://docs.djangoproject.com/en/3.2/topics/checks/
SILENCED_SYSTEM_CHECKS = [
    "security.W004",  # (SECURE_HSTS_SECONDS) TLS is handled by Nginx
    "security.W008",  # (SECURE_SSL_REDIRECT) HTTPS redirection is handled by CloudFlare
]

# Security
# https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-CSRF_COOKIE_SECURE
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_TRUSTED_ORIGINS = [BASE_URL]

# https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options#directives
X_FRAME_OPTIONS = "SAMEORIGIN"


# CSP
# https://django-csp.readthedocs.io/en/latest/configuration.html
CSP_REPORT_ONLY = False
CSP_EXCLUDE_URL_PREFIXES = ("/api/",)
CSP_REPORT_URI = [env.str("CSP_REPORT_URI", default="")]
CSP_DEFAULT_SRC = ["'none'"]
CSP_CONNECT_SRC = [
    "'self'",
    "https://plausible.io",
    "https://sentry.io",
    "https://*.ingest.sentry.io/",
]
CSP_FONT_SRC = ["'self'", "data:"]
CSP_IMG_SRC = [
    "'self'",
    "blob:",
    "data: w3.org/svg/2000",
    "https://github.com",
    "https://avatars.githubusercontent.com",
]
CSP_MANIFEST_SRC = ["'self'"]

# Duplicate the *_ELEM settings for Firefox
# https://bugzilla.mozilla.org/show_bug.cgi?id=1529338
CSP_SCRIPT_SRC = CSP_SCRIPT_SRC_ELEM = ["'self'", "https://plausible.io"]
CSP_STYLE_SRC = CSP_STYLE_SRC_ELEM = ["'self'"]

# which directives to set a nonce for
CSP_INCLUDE_NONCE_IN = ["script-src", "script-src-elem"]

# configure django-csp to work with Vite when using it in dev mode
if ASSETS_DEV_MODE:
    CSP_CONNECT_SRC = [
        "'self'",
        "ws://localhost:5173/static/",
        "https://plausible.io",
        "https://sentry.io",
        "https://*.ingest.sentry.io/",
    ]
    CSP_FONT_SRC = ["http://localhost:5173"]
    CSP_SCRIPT_SRC = CSP_SCRIPT_SRC_ELEM = [
        "'self'",
        "https://plausible.io",
        "http://localhost:5173",
    ]
    CSP_STYLE_SRC = CSP_STYLE_SRC_ELEM = ["'self'", "'unsafe-inline'"]


# CSRF error view
# https://docs.djangoproject.com/en/4.1/ref/settings/#csrf-failure-view
CSRF_FAILURE_VIEW = "jobserver.views.errors.csrf_failure"


# Globally set django.forms.URLField.assume_scheme to "https"
# This can be removed in the 6.0 release
# https://docs.djangoproject.com/en/5.0/ref/settings/#std-setting-FORMS_URLFIELD_ASSUME_HTTPS
FORMS_URLFIELD_ASSUME_HTTPS = True


# THIRD PARTY SETTINGS

# Anymail
ANYMAIL = {
    "MAILGUN_API_KEY": env.str("MAILGUN_API_KEY", default=None),
    "MAILGUN_API_URL": "https://api.eu.mailgun.net/v3",
    "MAILGUN_SENDER_DOMAIN": "mg.jobs.opensafely.org",
}
EMAIL_BACKEND = env.str(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = "you@example.com"
SERVER_EMAIL = "your-server@example.com"

# REST Framework
# https://www.django-rest-framework.org/api-guide/settings/
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "jobserver.api.authentication.NoAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 100,
}

# Debug Toolbar
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#configuring-internal-ips
INTERNAL_IPS = [
    "127.0.0.1",
]

# Permissions Policy
PERMISSIONS_POLICY = {
    "interest-cohort": [],
}

# Python/Django Social Auth
SOCIAL_AUTH_PIPELINE = [
    "jobserver.auth_pipeline.pipeline",
]

# Sentry
initialise_sentry()


# PROJECT SETTINGS
DISABLE_CREATING_JOBS = env.bool("DISABLE_CREATING_JOBS", default=False)

# GitHub token with write permissions
# TODO: remove default when we're happy with setting up CI with this token
GITHUB_WRITEABLE_TOKEN = env.str("GITHUB_WRITEABLE_TOKEN", default="")

# path to where local git repos live, used when developing locally, for the
# interactive functionality
LOCAL_GIT_REPOS = BASE_DIR / "repos"

# Released files per-file size limit
RELEASE_FILE_SIZE_LIMIT = env.int(
    "RELEASE_FILE_SIZE_LIMIT", default=16 * 1024 * 1024  # 16Mb
)

# Released files storage location
# Note: we deliberately don't use MEDIA_ROOT/MEDIA_URL here, to avoid any
# surprises with django's default uploads implementation.
RELEASE_STORAGE = Path(env.str("RELEASE_STORAGE", default="releases"))

# IP prefix of docker subnet on dokku 4
TRUSTED_PROXIES = env.list("TRUSTED_PROXIES", ["172.17.0."])

# Map client IP addresses to backend slugs
BACKEND_IP_MAP = {
    "62.253.26.158": "tpp",
    # uncomment to pretend your browser is on tpp
    # "127.0.0.1": "tpp",
}

# These orgs are not copiloted
BENNETT_ORG_PK = 3
GRAPHNET_ORG_PK = 12
LSHTM_ORG_PK = 4
UNIVERSITY_OF_BRISTOL_ORG_PK = 9
