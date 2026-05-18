from django.utils import translation


class AdminEnglishMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin/"):
            translation.activate("en")
            request.LANGUAGE_CODE = "en"
            try:
                return self.get_response(request)
            finally:
                translation.deactivate()
        return self.get_response(request)
