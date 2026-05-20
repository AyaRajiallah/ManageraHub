from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import include, path

from app1.views import (
    account_logout_view,
    admin_login_view,
    admin_logout_view,
    candidate_application_status_view,
    candidate_applications_view,
    candidate_dashboard_view,
    candidate_feed_view,
    candidate_job_apply_view,
    candidate_job_detail_view,
    candidate_job_offers_view,
    candidate_network_view,
    candidate_profile_view,
    candidate_quizzes_view,
    candidate_register_view,
    candidate_signin_view,
    candidate_settings_view,
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
    path('logout', account_logout_view, name='account_logout'),
    path('candidate/dashboard', candidate_dashboard_view),
    path('candidate/profile', candidate_profile_view),
    path('candidate/jobs', candidate_job_offers_view),
    path('candidate/jobs/<int:job_id>', candidate_job_detail_view),
    path('candidate/jobs/<int:job_id>/apply', candidate_job_apply_view),
    path('candidate/dashboard/', candidate_dashboard_view, name='candidate_dashboard'),
    path('candidate/profile/', candidate_profile_view, name='candidate_profile'),
    path('candidate/feed', candidate_feed_view, name='candidate_feed'),
    path('candidate/jobs/', candidate_job_offers_view, name='candidate_job_offers'),
    path('candidate/job-offers', candidate_job_offers_view),
    path('candidate/jobs/<int:job_id>/', candidate_job_detail_view, name='candidate_job_detail'),
    path('candidate/jobs/<int:job_id>/apply/', candidate_job_apply_view, name='candidate_job_apply'),
    path('candidate/applications', candidate_applications_view, name='candidate_applications'),
    path('candidate/application-status', candidate_application_status_view, name='candidate_application_status'),
    path('candidate/quizzes', candidate_quizzes_view, name='candidate_quizzes'),
    path('candidate/network', candidate_network_view, name='candidate_network'),
    path('candidate/settings', candidate_settings_view, name='candidate_settings'),
    path('admin/login/', admin_login_view, name='admin_login_redirect'),
    path('admin/logout/', admin_logout_view, name='admin_logout_redirect'),
    path('password-reset', password_reset_view, name='password_reset'),
    path('candidate/register', candidate_register_view, name='candidate_register'),
    path('company/register', company_register_view, name='company_register'),
    path('admin/', admin.site.urls),
]

if settings.HAS_ALLAUTH:
    urlpatterns.append(path('auth/', include('allauth.urls')))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
