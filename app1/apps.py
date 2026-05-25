from django.apps import AppConfig


class App1Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app1'

    def ready(self):
        # Hide allauth/social models from admin after autodiscover completes
        # They still work in background for Google login
        from django.contrib import admin

        try:
            from allauth.account.models import EmailAddress
            admin.site.unregister(EmailAddress)
        except Exception:
            pass

        try:
            from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
            # admin.site.unregister(SocialAccount)
            # admin.site.unregister(SocialApp)
            # admin.site.unregister(SocialToken)
        except Exception:
            pass

        try:
            from django.contrib.sites.models import Site
            # admin.site.unregister(Site)
        except Exception:
            pass