from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import PasswordResetForm
from django.shortcuts import redirect, render

DEFAULT_CANDIDATE_DASHBOARD_URL = "/candidate/dashboard"
DEFAULT_COMPANY_DASHBOARD_URL = "/company/dashboard"


def home(request):
    return render(request, "home.html")


def admin_login_view(request):
    return redirect("/admin/login/")


def admin_dashboard_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("/admin/")
    return redirect("/admin/login/")


def admin_logout_view(request):
    logout(request)
    return redirect("/signin")


def candidate_register_view(request):
    error_message = None
    success_message = None

    if request.method == "POST":
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if password != confirm_password:
            error_message = "Passwords do not match. Please try again."
        else:
            success_message = "Registration successful! You can now sign in."

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
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if password != confirm_password:
            error_message = "Passwords do not match. Please try again."
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


def _signin_context(**extra):
    context = {
        "social_auth_enabled": settings.HAS_ALLAUTH,
        "google_auth_enabled": getattr(settings, "GOOGLE_AUTH_CONFIGURED", False) and settings.HAS_ALLAUTH,
        "github_auth_enabled": getattr(settings, "GITHUB_AUTH_CONFIGURED", False) and settings.HAS_ALLAUTH,
    }
    context.update(extra)
    return context


def _role_dashboard_url(role):
    if role == "company":
        return DEFAULT_COMPANY_DASHBOARD_URL
    return DEFAULT_CANDIDATE_DASHBOARD_URL


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
            login(request, user)
            if user.is_staff:
                return redirect("/admin/")
            next_url = request.GET.get("next") or _role_dashboard_url(active_role)
            return redirect(next_url)

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
