from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from app1.views import (
    admin_logout_view,
    candidate_register_view,
    candidate_signin_view,
    company_register_view,
    company_signin_view,
    home,
    password_reset_view,
    signin_view,
)

urlpatterns = [
    path('', home, name='home'),
    path('signin', signin_view, name='signin'),
    path('candidate/signin', candidate_signin_view, name='candidate_signin'),
    path('company/signin', company_signin_view, name='company_signin'),
    path('admin/logout/', admin_logout_view, name='admin_logout_redirect'),
    path('password-reset', password_reset_view, name='password_reset'),
    path('candidate/register', candidate_register_view, name='candidate_register'),
    path('company/register', company_register_view, name='company_register'),
    path('admin/', admin.site.urls),
]

if settings.HAS_ALLAUTH:
    urlpatterns.append(path('auth/', include('allauth.urls')))
