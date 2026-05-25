from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class NoMessagesAccountAdapter(DefaultAccountAdapter):
    """
    A custom account adapter that silences all default django-allauth messages
    (like 'Successfully signed in' or 'Successfully signed out') to keep the
    admin dashboard and templates clean.
    """
    def add_message(self, *args, **kwargs):
        # Do absolutely nothing, preventing messages from being added to the session
        pass


class NoMessagesSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    A custom social account adapter that silences all default django-allauth social messages.
    """
    def add_message(self, *args, **kwargs):
        # Do absolutely nothing, preventing social messages from being added to the session
        pass
