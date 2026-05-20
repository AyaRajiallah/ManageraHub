from .settings import *  # noqa: F403,F401

HAS_ALLAUTH = False
SOCIAL_AUTH_CONFIGURED = False
GOOGLE_AUTH_CONFIGURED = False
GITHUB_AUTH_CONFIGURED = False

INSTALLED_APPS = [app for app in INSTALLED_APPS if not app.startswith("allauth")]  # noqa: F405
MIDDLEWARE = [mw for mw in MIDDLEWARE if mw != "allauth.account.middleware.AccountMiddleware"]  # noqa: F405
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
