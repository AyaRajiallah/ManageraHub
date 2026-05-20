from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import app1.models
from django.utils import timezone


def seed_job_offers(apps, schema_editor):
    JobOffer = apps.get_model("app1", "JobOffer")
    offers = [
        {
            "title": "Junior Frontend Developer",
            "company_name": "Atlas Digital",
            "city": "Casablanca",
            "country": "Morocco",
            "job_type": "engineering",
            "contract_type": "full_time",
            "experience_level": "junior",
            "summary": "Work on modern web interfaces for recruitment and HR products in a collaborative product team.",
            "responsibilities": "Build reusable UI components.\nCollaborate with designers.\nImprove user journeys and accessibility.",
            "requirements": "Knowledge of HTML, CSS, JavaScript.\nBasic React or Django template experience.\nStrong curiosity and communication.",
            "salary_range": "8,000 - 11,000 MAD / month",
            "is_remote": False,
        },
        {
            "title": "Talent Acquisition Assistant",
            "company_name": "People First",
            "city": "Rabat",
            "country": "Morocco",
            "job_type": "operations",
            "contract_type": "internship",
            "experience_level": "junior",
            "summary": "Support recruitment coordination, interview planning, and candidate communication in a fast-moving HR team.",
            "responsibilities": "Screen applications.\nCoordinate interviews.\nMaintain candidate records.",
            "requirements": "Good organization.\nStrong communication in French or English.\nInterest in HR and talent acquisition.",
            "salary_range": "Paid internship",
            "is_remote": False,
        },
        {
            "title": "Marketing Content Specialist",
            "company_name": "Nova Reach",
            "city": "Marrakesh",
            "country": "Morocco",
            "job_type": "marketing",
            "contract_type": "contract",
            "experience_level": "mid",
            "summary": "Create compelling content for campaigns, social channels, and brand storytelling across digital products.",
            "responsibilities": "Write campaign copy.\nPlan editorial content.\nCoordinate with design and growth teams.",
            "requirements": "Experience in marketing content.\nGood copywriting skills.\nCreative and structured mindset.",
            "salary_range": "Project-based contract",
            "is_remote": True,
        },
        {
            "title": "Data Analyst",
            "company_name": "Insight Bridge",
            "city": "Tangier",
            "country": "Morocco",
            "job_type": "data",
            "contract_type": "full_time",
            "experience_level": "mid",
            "summary": "Analyze hiring and business data, create dashboards, and help teams make better decisions from reliable insights.",
            "responsibilities": "Prepare data reports.\nCreate dashboards.\nIdentify trends and recommendations.",
            "requirements": "SQL or Excel experience.\nAnalytical thinking.\nComfort with data visualization.",
            "salary_range": "14,000 - 18,000 MAD / month",
            "is_remote": True,
        },
    ]
    for offer in offers:
        JobOffer.objects.get_or_create(
            title=offer["title"],
            company_name=offer["company_name"],
            defaults={
                **offer,
                "posted_at": timezone.now(),
                "is_active": True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("app1", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="candidateprofile",
            name="certifications_file",
            field=models.FileField(blank=True, upload_to=app1.models.candidate_profile_file_path),
        ),
        migrations.AddField(
            model_name="candidateprofile",
            name="cover_letter_file",
            field=models.FileField(blank=True, upload_to=app1.models.candidate_profile_file_path),
        ),
        migrations.AddField(
            model_name="candidateprofile",
            name="cv_file",
            field=models.FileField(blank=True, upload_to=app1.models.candidate_profile_file_path),
        ),
        migrations.AddField(
            model_name="candidateprofile",
            name="profile_picture",
            field=models.FileField(blank=True, upload_to=app1.models.candidate_profile_file_path),
        ),
        migrations.CreateModel(
            name="JobOffer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("company_name", models.CharField(max_length=180)),
                ("city", models.CharField(max_length=120)),
                ("country", models.CharField(default="Morocco", max_length=120)),
                ("job_type", models.CharField(choices=[("engineering", "Engineering"), ("marketing", "Marketing"), ("design", "Design"), ("sales", "Sales"), ("operations", "Operations"), ("data", "Data")], max_length=40)),
                ("contract_type", models.CharField(choices=[("full_time", "Full Time"), ("part_time", "Part Time"), ("internship", "Internship"), ("contract", "Contract"), ("freelance", "Freelance")], max_length=40)),
                ("experience_level", models.CharField(choices=[("junior", "Junior"), ("mid", "Mid-Level"), ("senior", "Senior"), ("lead", "Lead")], max_length=40)),
                ("summary", models.TextField()),
                ("responsibilities", models.TextField()),
                ("requirements", models.TextField()),
                ("salary_range", models.CharField(blank=True, max_length=120)),
                ("is_remote", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("posted_at", models.DateTimeField(default=timezone.now)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-posted_at", "-created_at"]},
        ),
        migrations.CreateModel(
            name="JobApplication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=180)),
                ("email", models.EmailField(max_length=254)),
                ("phone_number", models.CharField(blank=True, max_length=40)),
                ("application_text", models.TextField(blank=True)),
                ("cv_file", models.FileField(blank=True, upload_to=app1.models.candidate_application_file_path)),
                ("cover_letter_file", models.FileField(blank=True, upload_to=app1.models.candidate_application_file_path)),
                ("status", models.CharField(choices=[("sent", "Sent"), ("under_review", "Under review"), ("accepted", "Accepted"), ("rejected", "Rejected"), ("interview_scheduled", "Interview scheduled")], default="sent", max_length=40)),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("candidate", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="job_applications", to=settings.AUTH_USER_MODEL)),
                ("job_offer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="applications", to="app1.joboffer")),
            ],
            options={"ordering": ["-submitted_at"]},
        ),
        migrations.AddConstraint(
            model_name="jobapplication",
            constraint=models.UniqueConstraint(fields=("candidate", "job_offer"), name="unique_candidate_job_application"),
        ),
        migrations.RunPython(seed_job_offers, migrations.RunPython.noop),
    ]
