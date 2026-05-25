from django.conf import settings
from django.db import models
from django.utils import timezone


def candidate_profile_file_path(instance, filename):
    user_id = getattr(instance, "user_id", None)
    if user_id is None and hasattr(instance, "profile_id"):
        user_id = instance.profile.user_id
    return f"candidate_profiles/user_{user_id}/{filename}"


def candidate_application_file_path(instance, filename):
    return f"candidate_applications/user_{instance.candidate_id}/job_{instance.job_offer_id}/{filename}"


class CandidateProfile(models.Model):
    EDUCATION_CHOICES = [
        ("high_school", "High School"),
        ("bachelor", "Bachelor"),
        ("master", "Master"),
        ("phd", "PhD"),
        ("bootcamp", "Bootcamp / Certification"),
        ("other", "Other"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidate_profile",
    )
    phone_number = models.CharField(max_length=40, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=120, blank=True)
    education_level = models.CharField(max_length=120, blank=True, choices=EDUCATION_CHOICES)
    skills = models.TextField(blank=True)
    experience_summary = models.TextField(blank=True)
    headline = models.CharField(max_length=180, blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.FileField(upload_to=candidate_profile_file_path, blank=True)
    cv_file = models.FileField(upload_to=candidate_profile_file_path, blank=True)
    cover_letter_file = models.FileField(upload_to=candidate_profile_file_path, blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__first_name", "user__last_name", "user__username"]

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        full_name = self.user.get_full_name().strip()
        return full_name or self.user.username

    @property
    def completion_percent(self):
        profile_fields = [
            bool(self.user.first_name.strip() or self.user.last_name.strip()),
            bool(self.phone_number.strip()),
            bool(self.address.strip()),
            bool(self.city.strip() or self.country.strip()),
            bool(self.education_level.strip()),
            bool(self.skills.strip()),
            bool(self.experience_summary.strip()),
            bool(self.cv_file),
            bool(self.cover_letter_file),
            self.certifications.exists(),
        ]
        return int((sum(profile_fields) / len(profile_fields)) * 100)


class CandidateCertification(models.Model):
    profile = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="certifications",
    )
    file = models.FileField(upload_to=candidate_profile_file_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at", "-id"]

    def __str__(self):
        return self.file.name.rsplit("/", 1)[-1]


def company_profile_file_path(instance, filename):
    return f"company_profiles/user_{instance.user_id}/{filename}"


class CompanyProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="company_profile",
    )
    company_name = models.CharField(max_length=180, blank=True)
    industry = models.CharField(max_length=120, blank=True)
    company_size = models.CharField(max_length=60, blank=True)
    phone_number = models.CharField(max_length=40, blank=True)
    city = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=120, blank=True)
    website = models.URLField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to=company_profile_file_path, blank=True)
    background_image = models.ImageField(upload_to=company_profile_file_path, blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Moroccan Legal Verification Fields
    ice = models.CharField(max_length=15, blank=True, null=True, verbose_name="ICE (15 digits)")
    rc_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Registre du Commerce (RC)")
    legal_document = models.FileField(upload_to=company_profile_file_path, blank=True, null=True)

    class Meta:
        ordering = ["company_name", "user__username"]

    def __str__(self):
        return self.company_name or self.user.get_full_name().strip() or self.user.username

    @property
    def display_name(self):
        return self.company_name or self.user.get_full_name().strip() or self.user.username

    @property
    def completion_percent(self):
        fields = [
            bool(self.company_name.strip()),
            bool(self.industry.strip()),
            bool(self.company_size.strip()),
            bool(self.phone_number.strip()),
            bool(self.city.strip() or self.country.strip()),
            bool(self.website),
            bool(self.description.strip()),
            bool(self.logo),
            bool(self.ice and len(self.ice.strip()) == 15),
            bool(self.legal_document),
        ]
        return int((sum(fields) / len(fields)) * 100)



class JobOffer(models.Model):
    JOB_TYPE_CHOICES = [
        ("full_time", "Full-time"),
        ("part_time", "Part-time"),
        ("internship", "Internship / Stage"),
        ("alternance", "Alternance / Apprentissage"),
        ("freelance", "Freelance / Mission"),
        ("shift", "Shift Work"),
    ]
    CONTRACT_TYPE_CHOICES = [
        ("cdi", "CDI (Permanent)"),
        ("cdd", "CDD (Fixed-term)"),
        ("anapec", "ANAPEC (Insertion)"),
        ("stage_pre", "Stage Pré-embauche"),
        ("stage_obs", "Stage d'observation"),
        ("freelance", "Freelance / Auto-entrepreneur"),
        ("ctt", "CTT (Interim)"),
    ]
    EXPERIENCE_LEVEL_CHOICES = [
        ("junior", "Junior"),
        ("mid", "Mid-Level"),
        ("senior", "Senior"),
        ("lead", "Lead"),
    ]

    title = models.CharField(max_length=180)
    company_name = models.CharField(max_length=180)
    city = models.CharField(max_length=120)
    country = models.CharField(max_length=120, default="Morocco")
    job_type = models.CharField(max_length=40, choices=JOB_TYPE_CHOICES)
    contract_type = models.CharField(max_length=40, choices=CONTRACT_TYPE_CHOICES)
    experience_level = models.CharField(max_length=40, choices=EXPERIENCE_LEVEL_CHOICES)
    summary = models.TextField()
    responsibilities = models.TextField()
    requirements = models.TextField()
    salary_range = models.CharField(max_length=120, blank=True)
    is_remote = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    posted_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-posted_at", "-created_at"]

    def __str__(self):
        return f"{self.title} - {self.company_name}"


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ("sent", "Sent"),
        ("under_review", "Under review"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("interview_scheduled", "Interview scheduled"),
    ]

    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_applications",
    )
    job_offer = models.ForeignKey(
        JobOffer,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    full_name = models.CharField(max_length=180)
    email = models.EmailField()
    phone_number = models.CharField(max_length=40, blank=True)
    application_text = models.TextField(blank=True)
    cv_file = models.FileField(upload_to=candidate_application_file_path, blank=True)
    cover_letter_file = models.FileField(upload_to=candidate_application_file_path, blank=True)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default="sent")
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "job_offer"],
                name="unique_candidate_job_application",
            )
        ]

    def __str__(self):
        return f"{self.full_name} -> {self.job_offer.title}"
