from datetime import timedelta
import math

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
import json

from django.core.mail import send_mail
from .forms import CandidateProfileForm, CompanyProfileForm, JobApplicationForm, JobOfferFilterForm, JobOfferForm, CompanyJobFilterForm, CompanyApplicationFilterForm
from .models import CandidateProfile, CompanyProfile, JobApplication, JobOffer

DEFAULT_CANDIDATE_DASHBOARD_URL = "/candidate/dashboard/"
DEFAULT_COMPANY_DASHBOARD_URL = "/company/dashboard"
User = get_user_model()

QUIZ_COMPETENCIES = [
    "Communication",
    "Logic",
    "Stress Management",
    "Interview Readiness",
    "Organization",
    "Confidence",
]

QUIZ_QUESTIONS = [
    {
        "id": "communication_1",
        "competency": "Communication",
        "question": "During an interview, how should you clearly present an internship experience?",
        "choices": [
            "Only mention the company name.",
            "Explain the context, your role, your actions, and the result.",
            "Talk mostly about your hobbies.",
            "Answer with one vague sentence.",
        ],
        "correct_index": 1,
        "explanation": "A structured answer helps the recruiter understand your real impact and your communication style.",
    },
    {
        "id": "communication_2",
        "competency": "Communication",
        "question": "If a question is unclear, what is the best response?",
        "choices": [
            "Make up an answer quickly.",
            "Stay silent and say nothing.",
            "Politely ask for clarification.",
            "Change the topic.",
        ],
        "correct_index": 2,
        "explanation": "Asking for clarification shows active listening and helps you avoid answering off-topic.",
    },
    {
        "id": "logique_1",
        "competency": "Logic",
        "question": "One task takes 20 minutes. How long do 3 similar tasks take?",
        "choices": [
            "30 minutes",
            "40 minutes",
            "60 minutes",
            "90 minutes",
        ],
        "correct_index": 2,
        "explanation": "Three tasks of 20 minutes take 60 minutes when completed one after another.",
    },
    {
        "id": "logique_2",
        "competency": "Logic",
        "question": "Which number best completes this sequence: 2, 4, 8, 16, ... ?",
        "choices": [
            "18",
            "24",
            "32",
            "34",
        ],
        "correct_index": 2,
        "explanation": "Each number doubles the previous one, so 16 x 2 = 32.",
    },
    {
        "id": "stress_1",
        "competency": "Stress Management",
        "question": "You arrive for an interview and it is running 15 minutes late. What do you do?",
        "choices": [
            "Leave immediately.",
            "Stay calm and wait professionally.",
            "Post your frustration on social media.",
            "Refuse to continue the interview.",
        ],
        "correct_index": 1,
        "explanation": "Staying calm during a delay shows maturity and strong stress management.",
    },
    {
        "id": "stress_2",
        "competency": "Stress Management",
        "question": "Before an important presentation, which action helps reduce stress the most?",
        "choices": [
            "Improvise everything.",
            "Avoid reviewing the topic.",
            "Practice and prepare key points.",
            "Wait until the last minute to start.",
        ],
        "correct_index": 2,
        "explanation": "Structured preparation reduces uncertainty and increases your sense of control.",
    },
    {
        "id": "entretien_1",
        "competency": "Interview Readiness",
        "question": "Which response is most appropriate for the question 'Tell me about yourself'?",
        "choices": [
            "A brief introduction connected to your background and the target role.",
            "A full story about your entire life.",
            "Only your age and address.",
            "No answer, to stay mysterious.",
        ],
        "correct_index": 0,
        "explanation": "Recruiters expect a relevant summary of your background, strengths, and professional goal.",
    },
    {
        "id": "entretien_2",
        "competency": "Interview Readiness",
        "question": "At the end of an interview, what best shows strong preparation?",
        "choices": [
            "Say you have no questions at all.",
            "Ask a relevant question about the role or the team.",
            "Ask only about vacation on the first minute.",
            "Interrupt the recruiter.",
        ],
        "correct_index": 1,
        "explanation": "A relevant question shows genuine interest and preparation.",
    },
    {
        "id": "organisation_1",
        "competency": "Organization",
        "question": "You have 3 job applications to send this week. Which method is the most organized?",
        "choices": [
            "Wait until the last evening to do everything.",
            "Create a list, set priorities, and schedule each submission.",
            "Send the same message to everyone without reviewing it.",
            "Write nothing down and rely on memory.",
        ],
        "correct_index": 1,
        "explanation": "Planning and prioritizing help you keep quality high for each application.",
    },
    {
        "id": "organisation_2",
        "competency": "Organization",
        "question": "What should you check before sending a job application?",
        "choices": [
            "Your CV and the company name in the message.",
            "Only your profile photo.",
            "Only today's date.",
            "Nothing, speed matters most.",
        ],
        "correct_index": 0,
        "explanation": "Checking the essentials helps you avoid mistakes the recruiter will notice immediately.",
    },
    {
        "id": "confiance_1",
        "competency": "Confidence",
        "question": "When facing a difficult question, which attitude inspires the most confidence?",
        "choices": [
            "Calmly admit your limits, then propose an approach.",
            "Pretend to know everything without explanation.",
            "Apologize endlessly.",
            "Avoid answering completely.",
        ],
        "correct_index": 0,
        "explanation": "Healthy confidence combines honesty, calmness, and the ability to reason clearly.",
    },
    {
        "id": "confiance_2",
        "competency": "Confidence",
        "question": "Which behavior strengthens confidence during an interview?",
        "choices": [
            "Speak very fast without pausing.",
            "Maintain an open posture and a steady tone.",
            "Look at the floor constantly.",
            "Avoid all eye contact.",
        ],
        "correct_index": 1,
        "explanation": "Posture and tone directly shape how confident you appear.",
    },
]


def _build_quiz_radar_points(skill_scores):
    center_x = 160
    center_y = 160
    radius = 108
    total = len(QUIZ_COMPETENCIES)
    points = []
    axis_points = []
    label_points = []
    score_points = []
    ring_polygons = []

    for ring_ratio in (0.25, 0.5, 0.75, 1):
        ring = []
        for index, competency in enumerate(QUIZ_COMPETENCIES):
            angle = -math.pi / 2 + (2 * math.pi * index / total)
            ring_x = center_x + math.cos(angle) * radius * ring_ratio
            ring_y = center_y + math.sin(angle) * radius * ring_ratio
            ring.append(f"{ring_x:.2f},{ring_y:.2f}")
        ring_polygons.append(" ".join(ring))

    for index, competency in enumerate(QUIZ_COMPETENCIES):
        angle = -math.pi / 2 + (2 * math.pi * index / total)
        outer_x = center_x + math.cos(angle) * radius
        outer_y = center_y + math.sin(angle) * radius
        value_ratio = max(0, min(skill_scores.get(competency, 0), 100)) / 100
        score_x = center_x + math.cos(angle) * radius * value_ratio
        score_y = center_y + math.sin(angle) * radius * value_ratio
        label_x = center_x + math.cos(angle) * (radius + 26)
        label_y = center_y + math.sin(angle) * (radius + 26)
        points.append(f"{score_x:.2f},{score_y:.2f}")
        axis_points.append((center_x, center_y, outer_x, outer_y))
        score_points.append({"x": f"{score_x:.2f}", "y": f"{score_y:.2f}"})
        label_points.append(
            {
                "label": competency,
                "score": skill_scores.get(competency, 0),
                "x": f"{label_x:.2f}",
                "y": f"{label_y:.2f}",
                "anchor": "middle" if abs(label_x - center_x) < 12 else ("start" if label_x > center_x else "end"),
            }
        )

    return {
        "polygon_points": " ".join(points),
        "axis_points": axis_points,
        "score_points": score_points,
        "label_points": label_points,
        "ring_polygons": ring_polygons,
        "center_x": center_x,
        "center_y": center_y,
    }


def _skill_level(score):
    if score >= 75:
        return "Strong"
    if score >= 45:
        return "Average"
    return "Weak"


def _build_skill_network(skill_scores):
    teamwork_score = int(round((skill_scores["Communication"] + skill_scores["Organization"]) / 2))
    technical_score = int(round((skill_scores["Logic"] + skill_scores["Interview Readiness"]) / 2))

    network_scores = {
        "Communication": skill_scores["Communication"],
        "Interview Readiness": skill_scores["Interview Readiness"],
        "Teamwork": teamwork_score,
        "Logic": skill_scores["Logic"],
        "Stress Management": skill_scores["Stress Management"],
        "Confidence": skill_scores["Confidence"],
        "Organization": skill_scores["Organization"],
        "Technical Skills": technical_score,
    }

    nodes = []
    for label, score in network_scores.items():
        level = _skill_level(score)
        radius = 34 if level == "Strong" else 27 if level == "Average" else 21
        nodes.append(
            {
                "id": label.lower().replace(" ", "_"),
                "label": label,
                "score": score,
                "level": level,
                "radius": radius,
            }
        )

    edges = [
        {"source": "communication", "target": "teamwork"},
        {"source": "communication", "target": "interview_readiness"},
        {"source": "interview_readiness", "target": "confidence"},
        {"source": "confidence", "target": "stress_management"},
        {"source": "logic", "target": "technical_skills"},
        {"source": "organization", "target": "teamwork"},
        {"source": "organization", "target": "stress_management"},
    ]

    strongest_skill = max(network_scores, key=network_scores.get)
    weakest_skill = min(network_scores, key=network_scores.get)
    average_total = sum(network_scores.values()) / len(network_scores)
    main_cluster = "Interview & Soft Skills" if average_total >= 55 else "Foundational Growth"

    return {
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "strongest_skill": strongest_skill,
            "weakest_skill": weakest_skill,
            "main_cluster": main_cluster,
        },
        "json": json.dumps({"nodes": nodes, "edges": edges}, cls=DjangoJSONEncoder),
    }


def _build_candidate_quiz_state(request):
    correction_rows = []
    skill_totals = {competency: {"correct": 0, "total": 0} for competency in QUIZ_COMPETENCIES}

    for question in QUIZ_QUESTIONS:
        submitted = request.POST.get(question["id"], "").strip()
        skill_totals[question["competency"]]["total"] += 1
        is_correct = submitted == str(question["correct_index"])
        if is_correct:
            skill_totals[question["competency"]]["correct"] += 1
        correction_rows.append(
            {
                **question,
                "submitted": submitted,
                "correct_choice": question["choices"][question["correct_index"]],
                "submitted_choice": question["choices"][int(submitted)] if submitted.isdigit() and int(submitted) < len(question["choices"]) else "",
                "is_correct": is_correct,
            }
        )

    skill_scores = {
        competency: int(round((values["correct"] / values["total"]) * 100)) if values["total"] else 0
        for competency, values in skill_totals.items()
    }
    total_correct = sum(values["correct"] for values in skill_totals.values())
    total_questions = sum(values["total"] for values in skill_totals.values())
    total_score = int(round((total_correct / total_questions) * 100)) if total_questions else 0
    skill_network = _build_skill_network(skill_scores)

    return {
        "questions": correction_rows,
        "is_submitted": True,
        "skill_scores": skill_scores,
        "total_score": total_score,
        "total_correct": total_correct,
        "total_questions": total_questions,
        "radar_chart": _build_quiz_radar_points(skill_scores),
        "skill_network": skill_network,
    }


def _candidate_quiz_context(request):
    initial_questions = [{**question, "submitted": "", "is_correct": False} for question in QUIZ_QUESTIONS]
    base_state = {
        "questions": initial_questions,
        "is_submitted": False,
        "skill_scores": {competency: 0 for competency in QUIZ_COMPETENCIES},
        "total_score": None,
        "total_correct": 0,
        "total_questions": len(QUIZ_QUESTIONS),
        "radar_chart": _build_quiz_radar_points({competency: 0 for competency in QUIZ_COMPETENCIES}),
        "skill_network": None,
    }
    if request.method == "POST" and request.POST.get("candidate_quiz_submit") == "1":
        return _build_candidate_quiz_state(request)
    return base_state


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
        "industry": extra_fields.get("industry", "").strip(),
        "company_size": extra_fields.get("company_size", "").strip(),
        "website": extra_fields.get("website", "").strip(),
        "description": extra_fields.get("description", "").strip(),
        "ice": extra_fields.get("ice", "").strip() if extra_fields.get("ice") else None,
        "rc_number": extra_fields.get("rc_number", "").strip() if extra_fields.get("rc_number") else None,
        "legal_document": extra_fields.get("legal_document"),
    }
    profile, created = CompanyProfile.objects.get_or_create(user=user, defaults=defaults)
    if not created:
        changed = False
        updated_fields = []
        for field_name, value in defaults.items():
            # Treat FileField correctly
            if value is not None and not getattr(profile, field_name):

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


def _candidate_application_tracker_items(user):
    applications = (
        JobApplication.objects.filter(candidate=user)
        .select_related("job_offer")
        .order_by("-submitted_at")
    )

    tracker_items = []
    for application in applications:
        final_label = "Final Decision"

        steps = [
            {"label": "Application Sent", "state": "upcoming"},
            {"label": "Application Viewed", "state": "upcoming"},
            {"label": "Under Review", "state": "upcoming"},
            {"label": "Interview Scheduled", "state": "upcoming"},
            {"label": final_label, "state": "upcoming"},
        ]

        if application.status == "sent":
            steps[0]["state"] = "current"
        elif application.status == "under_review":
            steps[0]["state"] = "completed"
            steps[1]["state"] = "completed"
            steps[2]["state"] = "current"
        elif application.status == "interview_scheduled":
            steps[0]["state"] = "completed"
            steps[1]["state"] = "completed"
            steps[2]["state"] = "completed"
            steps[3]["state"] = "current"
        elif application.status in {"accepted", "rejected"}:
            steps[0]["state"] = "completed"
            steps[1]["state"] = "completed"
            steps[2]["state"] = "completed"
            steps[3]["state"] = "completed"
            steps[4]["state"] = "current"

        tracker_items.append(
            {
                "job_title": application.job_offer.title,
                "company_name": application.job_offer.company_name,
                "submitted_at": application.submitted_at,
                "status_label": application.get_status_display(),
                "steps": steps,
            }
        )

    return tracker_items


def _candidate_base_context(request, active_key):
    profile = _ensure_candidate_profile(request.user)
    application_count = JobApplication.objects.filter(candidate=request.user).count()
    tracker_items = _candidate_application_tracker_items(request.user)
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
        "candidate_application_tracker": tracker_items,
    }


def _company_nav_items():
    return [
        {"key": "dashboard", "label": "Home", "url": reverse("company_dashboard")},
        {"key": "jobs", "label": "My Jobs", "url": reverse("company_jobs")},
        {"key": "applications", "label": "Applications", "url": reverse("company_applications")},
        {"key": "profile", "label": "Profile", "url": reverse("company_profile")},
        {"key": "logout", "label": "Logout", "url": reverse("account_logout")},
    ]


def _is_company_user(user):
    return user.is_authenticated and not user.is_staff and hasattr(user, "company_profile")


def _company_redirect_response(request):
    signin_url = reverse("company_signin")
    if not request.user.is_authenticated:
        return redirect(f"{signin_url}?next={request.path}")
    if request.user.is_staff:
        return redirect("/admin/")
    return redirect(reverse("signin"))


def _company_base_context(request, active_key):
    profile = request.user.company_profile
    company_name = profile.company_name or request.user.get_full_name() or request.user.username
    company_jobs = JobOffer.objects.filter(company_name=company_name)
    company_applications = JobApplication.objects.filter(job_offer__company_name=company_name)
    initials = "".join(word[0].upper() for word in company_name.split() if word)[:2] or "CO"
    return {
        "active_section": active_key,
        "company_nav_items": _company_nav_items(),
        "company_profile": profile,
        "company_display_name": company_name,
        "company_initials": initials,
        "company_stats": {
            "posted_jobs": company_jobs.filter(is_active=True).count(),
            "total_applications": company_applications.count(),
            "pending_applications": company_applications.filter(status="sent").count(),
            "accepted_applications": company_applications.filter(status="accepted").count(),
        },
    }


def company_dashboard_view(request):
    if not _is_company_user(request.user):
        return _company_redirect_response(request)
    if not request.user.company_profile.is_approved:
        return redirect(reverse("company_pending_approval"))
    ctx = _company_base_context(request, "dashboard")
    company_name = ctx["company_display_name"]
    ctx["recent_applications"] = (
        JobApplication.objects.filter(job_offer__company_name=company_name)
        .select_related("job_offer")
        .order_by("-submitted_at")[:5]
    )
    ctx["active_jobs"] = (
        JobOffer.objects.filter(company_name=company_name, is_active=True)
        .prefetch_related("applications")
        .order_by("-created_at")[:5]
    )
    return render(request, "company/dashboard.html", ctx)



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
        company_name = request.POST.get("company_name", "").strip()
        industry = request.POST.get("industry", "").strip()
        industry_other = request.POST.get("industry_other", "").strip()
        company_size = request.POST.get("company_size", "").strip()
        country = request.POST.get("country", "").strip()
        city = request.POST.get("city", "").strip()
        website = request.POST.get("website", "").strip()
        description = request.POST.get("description", "").strip()
        first_name = request.POST.get("admin_first", "").strip()
        last_name = request.POST.get("admin_last", "").strip()
        email = request.POST.get("email", "").strip().lower()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("password_confirm", "")

        # Legal Verification fields
        ice = request.POST.get("ice", "").strip()
        rc_number = request.POST.get("rc_number", "").strip()
        legal_document = request.FILES.get("legal_document")

        if password != confirm_password:
            error_message = "Passwords do not match. Please try again."
        elif not email:
            error_message = "Email is required."
        elif not company_name:
            error_message = "Company name is required."
        elif ice and (not ice.isdigit() or len(ice) != 15):
            error_message = "The ICE number must contain exactly 15 digits."
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
                resolved_industry = industry_other if industry == "Other" and industry_other else industry
                _create_company_profile(
                    user,
                    company_name=company_name,
                    phone_number=phone,
                    city=city,
                    country=country,
                    industry=resolved_industry,
                    company_size=company_size,
                    website=website,
                    description=description,
                    ice=ice,
                    rc_number=rc_number,
                    legal_document=legal_document,
                )
                return redirect(reverse("company_pending_approval"))

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

        email = request.POST.get("email", "").strip().lower()
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
            elif is_company and not user.company_profile.is_approved:
                return redirect(reverse("company_pending_approval"))
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
            "candidate_quiz": _candidate_quiz_context(request),
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
    return redirect(f"{_candidate_dashboard_url()}#candidate-quiz-lab")


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


def company_profile_view(request):
    if not _is_company_user(request.user):
        return _company_redirect_response(request)
    if not request.user.company_profile.is_approved:
        return redirect(reverse("company_pending_approval"))
    profile = request.user.company_profile
    success = False
    if request.method == "POST":
        form = CompanyProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            success = True
    else:
        form = CompanyProfileForm(instance=profile)
    ctx = _company_base_context(request, "profile")
    ctx["form"] = form
    ctx["success"] = success
    return render(request, "company/profile.html", ctx)


def company_post_job_view(request):
    if not _is_company_user(request.user):
        return _company_redirect_response(request)
    if not request.user.company_profile.is_approved:
        return redirect(reverse("company_pending_approval"))
    profile = request.user.company_profile
    if request.method == "POST":
        form = JobOfferForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company_name = profile.company_name
            job.save()
            return redirect(reverse("company_jobs"))
    else:
        form = JobOfferForm(initial={"country": profile.country or "Morocco", "city": profile.city})
    ctx = _company_base_context(request, "jobs")
    ctx["form"] = form
    return render(request, "company/post_job.html", ctx)


def company_jobs_view(request):
    if not _is_company_user(request.user):
        return _company_redirect_response(request)
    if not request.user.company_profile.is_approved:
        return redirect(reverse("company_pending_approval"))
    ctx = _company_base_context(request, "jobs")
    company_name = ctx["company_display_name"]

    form = CompanyJobFilterForm(request.GET or None)
    jobs = (
        JobOffer.objects.filter(company_name=company_name)
        .prefetch_related("applications")
        .order_by("-created_at")
    )

    if form.is_valid():
        keyword = form.cleaned_data.get("keyword")
        job_type = form.cleaned_data.get("job_type")
        contract_type = form.cleaned_data.get("contract_type")
        experience_level = form.cleaned_data.get("experience_level")
        status = form.cleaned_data.get("status")
        date_posted = form.cleaned_data.get("date_posted")

        if keyword:
            jobs = jobs.filter(
                Q(title__icontains=keyword)
                | Q(summary__icontains=keyword)
                | Q(requirements__icontains=keyword)
            )
        if job_type:
            jobs = jobs.filter(job_type=job_type)
        if contract_type:
            jobs = jobs.filter(contract_type=contract_type)
        if experience_level:
            jobs = jobs.filter(experience_level=experience_level)
        if status == "active":
            jobs = jobs.filter(is_active=True)
        elif status == "inactive":
            jobs = jobs.filter(is_active=False)
        if date_posted:
            jobs = jobs.filter(
                created_at__gte=timezone.now() - timedelta(days=int(date_posted))
            )

    ctx["filter_form"] = form
    ctx["jobs"] = jobs
    return render(request, "company/jobs.html", ctx)


def company_job_edit_view(request, job_id):
    if not _is_company_user(request.user):
        return _company_redirect_response(request)
    profile = request.user.company_profile
    job = get_object_or_404(JobOffer, pk=job_id, company_name=profile.company_name)
    success = False
    if request.method == "POST":
        form = JobOfferForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            success = True
    else:
        form = JobOfferForm(instance=job)
    ctx = _company_base_context(request, "jobs")
    ctx["form"] = form
    ctx["job"] = job
    ctx["success"] = success
    return render(request, "company/job_edit.html", ctx)


def company_job_toggle_view(request, job_id):
    if not _is_company_user(request.user):
        return _company_redirect_response(request)
    profile = request.user.company_profile
    job = get_object_or_404(JobOffer, pk=job_id, company_name=profile.company_name)
    job.is_active = not job.is_active
    job.save(update_fields=["is_active"])
    return redirect(reverse("company_jobs"))


def company_job_delete_view(request, job_id):
    if not _is_company_user(request.user):
        return _company_redirect_response(request)
    profile = request.user.company_profile
    job = get_object_or_404(JobOffer, pk=job_id, company_name=profile.company_name)
    if request.method == "POST":
        job.delete()
    return redirect(reverse("company_jobs"))


def company_applications_view(request):
    if not _is_company_user(request.user):
        return _company_redirect_response(request)
    if not request.user.company_profile.is_approved:
        return redirect(reverse("company_pending_approval"))
    ctx = _company_base_context(request, "applications")
    company_name = ctx["company_display_name"]

    form = CompanyApplicationFilterForm(request.GET or None)
    qs = JobApplication.objects.filter(
        job_offer__company_name=company_name
    ).select_related("job_offer")

    if form.is_valid():
        keyword = form.cleaned_data.get("keyword")
        status = form.cleaned_data.get("status")
        job_title = form.cleaned_data.get("job_title")
        date_received = form.cleaned_data.get("date_received")

        if keyword:
            qs = qs.filter(
                Q(full_name__icontains=keyword)
                | Q(email__icontains=keyword)
            )
        if status:
            qs = qs.filter(status=status)
        if job_title:
            qs = qs.filter(job_offer__title__icontains=job_title)
        if date_received:
            qs = qs.filter(
                submitted_at__gte=timezone.now() - timedelta(days=int(date_received))
            )

    ctx["filter_form"] = form
    ctx["applications"] = qs.order_by("-submitted_at")
    ctx["status_choices"] = JobApplication.STATUS_CHOICES
    return render(request, "company/applications.html", ctx)


def company_application_detail_view(request, application_id):
    if not _is_company_user(request.user):
        return _company_redirect_response(request)
    profile = request.user.company_profile
    application = get_object_or_404(
        JobApplication.objects.select_related("job_offer"),
        pk=application_id,
        job_offer__company_name=profile.company_name,
    )
    if request.method == "POST":
        new_status = request.POST.get("status", "").strip()
        if new_status and new_status in dict(JobApplication.STATUS_CHOICES):
            application.status = new_status
            application.save(update_fields=["status", "updated_at"])
            return redirect(reverse("company_application_detail", args=[application_id]))
    ctx = _company_base_context(request, "applications")
    ctx["application"] = application
    ctx["status_choices"] = JobApplication.STATUS_CHOICES
    return render(request, "company/application_detail.html", ctx)


def company_pending_approval_view(request):
    return render(request, "company_pending_approval.html")


def admin_approve_company_view(request, company_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect("/admin/login/")
    company = get_object_or_404(CompanyProfile, pk=company_id)
    company.is_approved = True
    company.save(update_fields=["is_approved"])
    
    # Send simulation email to console
    subject = f"Your Company Account '{company.company_name}' has been APPROVED! ✦"
    message = f"""Bonjour {company.user.first_name} {company.user.last_name},

Félicitations! Your company account for '{company.company_name}' has been reviewed and APPROVED by our administration team.

Here is your company profile details we verified:
- ICE (Identifiant Commun): {company.ice or "Not provided"}
- RC Number: {company.rc_number or "Not provided"}
- City/Location: {company.city}, {company.country}

You can now log in to the Company Portal and start posting job offers!
Access here: http://127.0.0.1:8000/company/signin

Best regards,
The ManageraHub Admin Team (Morocco)
"""
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [company.user.email],
        fail_silently=True,
    )
    return redirect("/admin/")


def admin_reject_company_view(request, company_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect("/admin/login/")
    company = get_object_or_404(CompanyProfile, pk=company_id)
    company.is_approved = False
    company.save(update_fields=["is_approved"])
    
    # Send simulation email to console
    subject = f"Update regarding your Company Account request for '{company.company_name}'"
    message = f"""Bonjour {company.user.first_name} {company.user.last_name},

Thank you for your interest in ManageraHub. 

After reviewing the legal documents and details provided for '{company.company_name}', our administration team has rejected or deactivated your company profile.

If you believe this was an error, please ensure your 15-digit ICE and Registre du Commerce (RC) numbers are correct and that you uploaded a valid Modèle J certificate.

You can update your registration or get in touch with our support.

Best regards,
The ManageraHub Admin Team (Morocco)
"""
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [company.user.email],
        fail_silently=True,
    )
    return redirect("/admin/")


def admin_verify_company_offline_view(request, company_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect("/admin/login/")
    company = get_object_or_404(CompanyProfile, pk=company_id)
    ctx = {
        "company": company,
        "verified_at": timezone.now(),
    }
    return render(request, "admin/verify_company_offline.html", ctx)

