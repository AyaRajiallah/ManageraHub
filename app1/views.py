from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import CandidateProfileForm, JobApplicationForm, JobOfferFilterForm
from .models import CandidateProfile, CompanyProfile, JobApplication, JobOffer

DEFAULT_CANDIDATE_DASHBOARD_URL = "/candidate/dashboard/"
DEFAULT_COMPANY_DASHBOARD_URL = "/company/dashboard"
User = get_user_model()


def home(request):
    return render(request, "home.html")


def admin_login_view(request):
    next_url = request.GET.get("next", "").strip()
    signin_url = reverse("signin")
    if next_url:
        return redirect(f"{signin_url}?next={next_url}")
    return redirect(signin_url)


def admin_dashboard_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("/admin/")
    return redirect(reverse("signin"))


def admin_logout_view(request):
    logout(request)
    return redirect("/signin")


def account_logout_view(request):
    logout(request)
    return redirect(reverse("candidate_signin"))


def _build_full_name(first_name, last_name):
    return " ".join(part for part in [first_name.strip(), last_name.strip()] if part).strip()


def _candidate_dashboard_url():
    return reverse("candidate_dashboard")


def _create_candidate_profile(user, **extra_fields):
    defaults = {
        "phone_number": extra_fields.get("phone_number", "").strip(),
        "address": extra_fields.get("address", "").strip(),
        "city": extra_fields.get("city", "").strip(),
        "country": extra_fields.get("country", "").strip(),
        "headline": extra_fields.get("headline", "").strip(),
    }
    profile, created = CandidateProfile.objects.get_or_create(user=user, defaults=defaults)
    if not created:
        changed = False
        updated_fields = []
        for field_name, value in defaults.items():
            if value and not getattr(profile, field_name):
                setattr(profile, field_name, value)
                changed = True
                updated_fields.append(field_name)
        if changed:
            profile.save(update_fields=updated_fields)
    return profile


def _create_company_profile(user, **extra_fields):
    defaults = {
        "company_name": extra_fields.get("company_name", "").strip(),
        "phone_number": extra_fields.get("phone_number", "").strip(),
        "city": extra_fields.get("city", "").strip(),
        "country": extra_fields.get("country", "").strip(),
    }
    profile, created = CompanyProfile.objects.get_or_create(user=user, defaults=defaults)
    if not created:
        changed = False
        updated_fields = []
        for field_name, value in defaults.items():
            if value and not getattr(profile, field_name):
                setattr(profile, field_name, value)
                changed = True
                updated_fields.append(field_name)
        if changed:
            profile.save(update_fields=updated_fields)
    return profile


def _ensure_candidate_profile(user):
    if (
        user.is_authenticated
        and not user.is_staff
        and not hasattr(user, "candidate_profile")
        and not hasattr(user, "company_profile")
    ):
        return _create_candidate_profile(user, headline=user.get_full_name().strip())
    return getattr(user, "candidate_profile", None)


def _is_candidate_user(user):
    return user.is_authenticated and not user.is_staff and hasattr(user, "candidate_profile")


def _candidate_redirect_response(request):
    signin_url = reverse("candidate_signin")
    if not request.user.is_authenticated:
        return redirect(f"{signin_url}?next={request.path}")
    if request.user.is_staff:
        return redirect("/admin/")
    return redirect(reverse("signin"))


def _candidate_nav_items():
    return [
        {"key": "dashboard", "label": "Home", "url": reverse("candidate_dashboard")},
        {"key": "profile", "label": "My Profile", "url": reverse("candidate_profile")},
        {"key": "jobs", "label": "Job Offers", "url": reverse("candidate_job_offers")},
        {"key": "settings", "label": "Logout", "url": reverse("account_logout")},
    ]


def _candidate_base_context(request, active_key):
    profile = _ensure_candidate_profile(request.user)
    application_count = JobApplication.objects.filter(candidate=request.user).count()
    saved_docs_count = sum(
        1
        for field in [profile.cv_file, profile.cover_letter_file]
        if field
    )
    saved_docs_count += profile.certifications.count()
    initials = "".join(
        part[0].upper() for part in (request.user.first_name, request.user.last_name) if part
    )[:2] or request.user.username[:2].upper()
    return {
        "active_section": active_key,
        "candidate_nav_items": _candidate_nav_items(),
        "candidate_profile": profile,
        "candidate_display_name": profile.display_name,
        "candidate_completion_percent": profile.completion_percent,
        "candidate_initials": initials,
        "candidate_stats": {
            "applications": application_count,
            "saved_docs": saved_docs_count,
            "recent_jobs": JobOffer.objects.filter(is_active=True).count(),
        },
    }


def _signin_context(**extra):
    context = {
        "social_auth_enabled": settings.HAS_ALLAUTH,
        "google_auth_enabled": getattr(settings, "GOOGLE_AUTH_CONFIGURED", False) and settings.HAS_ALLAUTH,
        "github_auth_enabled": getattr(settings, "GITHUB_AUTH_CONFIGURED", False) and settings.HAS_ALLAUTH,
    }
    context.update(extra)
    return context


def candidate_register_view(request):
    error_message = None
    success_message = None

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        phone = request.POST.get("phone", "").strip()
        city = request.POST.get("city", "").strip()
        country = request.POST.get("country", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("password_confirm", "")

        if password != confirm_password:
            error_message = "Passwords do not match. Please try again."
        elif not email:
            error_message = "Email is required."
        elif User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
            error_message = "An account with this email already exists."
        else:
            try:
                validate_password(password)
            except ValidationError as exc:
                error_message = " ".join(exc.messages)
            else:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
                _create_candidate_profile(
                    user,
                    phone_number=phone,
                    city=city,
                    country=country,
                    headline=_build_full_name(first_name, last_name),
                )
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                return redirect(_candidate_dashboard_url())

    return render(
        request,
        "candidate_register.html",
        {
            "error_message": error_message,
            "success_message": success_message,
        },
    )


def company_register_view(request):
    error_message = None
    success_message = None

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("password_confirm", "")

        if password != confirm_password:
            error_message = "Passwords do not match. Please try again."
        elif email and (User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists()):
            error_message = "An account with this email already exists."
        else:
            success_message = "Company registration successful! You can now sign in."

    return render(
        request,
        "company_register.html",
        {
            "error_message": error_message,
            "success_message": success_message,
        },
    )


def _signin_view(request, selected_role=None):
    error_message = None
    active_role = selected_role

    if request.method == "POST":
        active_role = request.POST.get("role", active_role or "candidate").strip().lower()
        if active_role not in {"candidate", "company"}:
            active_role = "candidate"

        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.is_staff:
                login(request, user)
                next_url = request.GET.get("next", "").strip()
                return redirect(next_url or "/admin/")

            is_candidate = hasattr(user, "candidate_profile")
            is_company = hasattr(user, "company_profile")

            if active_role == "candidate" and is_company and not is_candidate:
                error_message = "This account is registered as a company. Please use the company sign in page."
            elif active_role == "company" and is_candidate and not is_company:
                error_message = "This account is registered as a candidate. Please use the candidate sign in page."
            else:
                login(request, user)
                next_url = request.GET.get("next", "").strip()
                if active_role == "candidate":
                    if not is_candidate:
                        _create_candidate_profile(user, headline=user.get_full_name().strip())
                    return redirect(next_url or _candidate_dashboard_url())
                if not is_company:
                    _create_company_profile(user, company_name=user.get_full_name().strip() or user.username)
                return redirect(next_url or DEFAULT_COMPANY_DASHBOARD_URL)
        else:
            error_message = "Invalid email or password. Please try again."

    active_role = active_role or "candidate"
    return render(
        request,
        "signin.html",
        _signin_context(
            error_message=error_message,
            active_role=active_role,
            is_role_specific_page=selected_role in {"candidate", "company"},
            role_page_title="Candidate Sign In" if active_role == "candidate" else "Company Sign In",
            form_action=request.path,
        ),
    )


def signin_view(request):
    return _signin_view(request)


def candidate_signin_view(request):
    return _signin_view(request, selected_role="candidate")


def company_signin_view(request):
    return _signin_view(request, selected_role="company")


def candidate_dashboard_view(request):
    _ensure_candidate_profile(request.user)
    if not _is_candidate_user(request.user):
        return _candidate_redirect_response(request)

    profile = request.user.candidate_profile
    applications = JobApplication.objects.filter(candidate=request.user).select_related("job_offer")[:3]
    recent_jobs = JobOffer.objects.filter(is_active=True)[:4]
    context = _candidate_base_context(request, "dashboard")
    context.update(
        {
            "profile_missing_items": [
                label
                for label, ready in [
                    ("Phone number", bool(profile.phone_number)),
                    ("Region", bool(profile.address)),
                    ("Education", bool(profile.education_level)),
                    ("Skills", bool(profile.skills)),
                    ("Experience", bool(profile.experience_summary)),
                    ("CV upload", bool(profile.cv_file)),
                    ("Cover letter upload", bool(profile.cover_letter_file)),
                ]
                if not ready
            ],
            "applications": applications,
            "recent_jobs": recent_jobs,
        }
    )
    return render(request, "candidate/dashboard.html", context)


def candidate_profile_view(request):
    _ensure_candidate_profile(request.user)
    if not _is_candidate_user(request.user):
        return _candidate_redirect_response(request)

    profile = request.user.candidate_profile
    if request.method == "POST":
        form = CandidateProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            return redirect(f"{reverse('candidate_profile')}?saved=1")
    else:
        form = CandidateProfileForm(instance=profile, user=request.user)

    context = _candidate_base_context(request, "profile")
    context.update(
        {
            "form": form,
            "saved": request.GET.get("saved") == "1",
        }
    )
    return render(request, "candidate/profile.html", context)


def candidate_job_offers_view(request):
    _ensure_candidate_profile(request.user)
    if not _is_candidate_user(request.user):
        return _candidate_redirect_response(request)

    form = JobOfferFilterForm(request.GET or None)
    jobs = JobOffer.objects.filter(is_active=True)
    if form.is_valid():
        keyword = form.cleaned_data.get("keyword")
        city = form.cleaned_data.get("city")
        company = form.cleaned_data.get("company")
        job_type = form.cleaned_data.get("job_type")
        contract_type = form.cleaned_data.get("contract_type")
        experience_level = form.cleaned_data.get("experience_level")
        date_posted = form.cleaned_data.get("date_posted")

        if keyword:
            jobs = jobs.filter(
                Q(title__icontains=keyword)
                | Q(company_name__icontains=keyword)
                | Q(summary__icontains=keyword)
                | Q(requirements__icontains=keyword)
            )
        if city:
            jobs = jobs.filter(city__icontains=city)
        if company:
            jobs = jobs.filter(company_name__icontains=company)
        if job_type:
            jobs = jobs.filter(job_type=job_type)
        if contract_type:
            jobs = jobs.filter(contract_type=contract_type)
        if experience_level:
            jobs = jobs.filter(experience_level=experience_level)
        if date_posted:
            jobs = jobs.filter(posted_at__gte=timezone.now() - timedelta(days=int(date_posted)))

    context = _candidate_base_context(request, "jobs")
    context.update(
        {
            "filter_form": form,
            "jobs": jobs,
        }
    )
    return render(request, "candidate/jobs.html", context)


def candidate_job_detail_view(request, job_id):
    _ensure_candidate_profile(request.user)
    if not _is_candidate_user(request.user):
        return _candidate_redirect_response(request)

    job = get_object_or_404(JobOffer, pk=job_id, is_active=True)
    existing_application = JobApplication.objects.filter(candidate=request.user, job_offer=job).first()
    context = _candidate_base_context(request, "jobs")
    context.update(
        {
            "job": job,
            "existing_application": existing_application,
            "application_success": request.GET.get("applied") == "1",
        }
    )
    return render(request, "candidate/job_detail.html", context)


def candidate_job_apply_view(request, job_id):
    _ensure_candidate_profile(request.user)
    if not _is_candidate_user(request.user):
        return _candidate_redirect_response(request)

    job = get_object_or_404(JobOffer, pk=job_id, is_active=True)
    profile = request.user.candidate_profile
    existing_application = JobApplication.objects.filter(candidate=request.user, job_offer=job).first()
    if existing_application is not None:
        return redirect(f"{reverse('candidate_job_detail', args=[job.id])}?applied=1")

    if request.method == "POST":
        form = JobApplicationForm(request.POST, request.FILES, profile=profile)
        if form.is_valid():
            application = form.save(commit=False)
            application.candidate = request.user
            application.job_offer = job
            application.status = "sent"
            application.save()
            return redirect(f"{reverse('candidate_job_detail', args=[job.id])}?applied=1")
    else:
        form = JobApplicationForm(profile=profile)

    context = _candidate_base_context(request, "jobs")
    context.update(
        {
            "job": job,
            "form": form,
        }
    )
    return render(request, "candidate/job_apply.html", context)


def candidate_feed_view(request):
    return redirect(_candidate_dashboard_url())


def candidate_applications_view(request):
    return redirect(_candidate_dashboard_url())


def candidate_application_status_view(request):
    return redirect(_candidate_dashboard_url())


def candidate_quizzes_view(request):
    return redirect(_candidate_dashboard_url())


def candidate_network_view(request):
    return redirect(_candidate_dashboard_url())


def candidate_settings_view(request):
    return redirect(reverse("account_logout"))


def password_reset_view(request):
    success = False
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        form = PasswordResetForm({"email": email})
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                email_template_name="registration/password_reset_email.html",
            )
        success = True

    return render(request, "signin.html", _signin_context(reset_success=success, active_role="candidate"))
