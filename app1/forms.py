from django import forms
from django.contrib.auth import get_user_model

from .models import CandidateCertification, CandidateProfile, JobApplication, JobOffer

User = get_user_model()


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(item, initial) for item in data]
        if not data:
            return []
        return [single_file_clean(data, initial)]


class CandidateProfileForm(forms.ModelForm):
    MOROCCO_REGION_CHOICES = [
        ("", "Select a region"),
        ("Tanger-Tetouan-Al Hoceima", "Tanger-Tetouan-Al Hoceima"),
        ("Oriental", "Oriental"),
        ("Fes-Meknes", "Fes-Meknes"),
        ("Rabat-Sale-Kenitra", "Rabat-Sale-Kenitra"),
        ("Beni Mellal-Khenifra", "Beni Mellal-Khenifra"),
        ("Casablanca-Settat", "Casablanca-Settat"),
        ("Marrakesh-Safi", "Marrakesh-Safi"),
        ("Draa-Tafilalet", "Draa-Tafilalet"),
        ("Souss-Massa", "Souss-Massa"),
        ("Guelmim-Oued Noun", "Guelmim-Oued Noun"),
        ("Laayoune-Sakia El Hamra", "Laayoune-Sakia El Hamra"),
        ("Dakhla-Oued Ed-Dahab", "Dakhla-Oued Ed-Dahab"),
    ]

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    certification_files = MultipleFileField(required=False)

    class Meta:
        model = CandidateProfile
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "address",
            "city",
            "country",
            "education_level",
            "headline",
            "skills",
            "experience_summary",
            "bio",
            "profile_picture",
            "cv_file",
            "cover_letter_file",
            "is_public",
        ]
        widgets = {
            "skills": forms.Textarea(attrs={"rows": 3}),
            "experience_summary": forms.Textarea(attrs={"rows": 5}),
            "bio": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "phone_number": "Phone",
            "address": "Region",
            "education_level": "Education",
            "experience_summary": "Experience",
            "cv_file": "CV upload",
            "cover_letter_file": "Cover letter upload",
            "is_public": "Show this profile publicly",
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["first_name"].initial = self.user.first_name
        self.fields["last_name"].initial = self.user.last_name
        self.fields["address"].widget = forms.Select(choices=self.MOROCCO_REGION_CHOICES)
        self.fields["certification_files"].label = "Certifications upload"

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.first_name = self.cleaned_data["first_name"].strip()
        self.user.last_name = self.cleaned_data["last_name"].strip()
        if commit:
            self.user.save(update_fields=["first_name", "last_name"])
            profile.user = self.user
            profile.save()
            for certification_file in self.cleaned_data["certification_files"]:
                CandidateCertification.objects.create(profile=profile, file=certification_file)
        return profile


class JobOfferFilterForm(forms.Form):
    keyword = forms.CharField(required=False)
    city = forms.CharField(required=False)
    company = forms.CharField(required=False)
    job_type = forms.ChoiceField(
        required=False,
        choices=[("", "All job types")] + JobOffer.JOB_TYPE_CHOICES,
    )
    contract_type = forms.ChoiceField(
        required=False,
        choices=[("", "All contract types")] + JobOffer.CONTRACT_TYPE_CHOICES,
    )
    experience_level = forms.ChoiceField(
        required=False,
        choices=[("", "All experience levels")] + JobOffer.EXPERIENCE_LEVEL_CHOICES,
    )
    date_posted = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Any date"),
            ("7", "Last 7 days"),
            ("30", "Last 30 days"),
            ("90", "Last 90 days"),
        ],
    )


class JobApplicationForm(forms.ModelForm):
    use_profile_cv = forms.BooleanField(required=False, initial=True)
    use_profile_cover_letter = forms.BooleanField(required=False, initial=True)

    class Meta:
        model = JobApplication
        fields = [
            "full_name",
            "email",
            "phone_number",
            "application_text",
            "cv_file",
            "cover_letter_file",
        ]
        widgets = {
            "application_text": forms.Textarea(attrs={"rows": 6}),
        }
        labels = {
            "application_text": "Application message",
            "cv_file": "Upload a specific CV",
            "cover_letter_file": "Upload a specific cover letter",
        }

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop("profile")
        super().__init__(*args, **kwargs)
        self.fields["full_name"].initial = self.profile.display_name
        self.fields["email"].initial = self.profile.user.email
        self.fields["phone_number"].initial = self.profile.phone_number
        self.fields["application_text"].initial = self.profile.bio or self.profile.experience_summary

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("cv_file") and not (
            cleaned_data.get("use_profile_cv") and self.profile.cv_file
        ):
            self.add_error("cv_file", "Add a CV or use the CV already saved in your profile.")
        if not cleaned_data.get("cover_letter_file") and not (
            cleaned_data.get("use_profile_cover_letter") and self.profile.cover_letter_file
        ):
            self.add_error(
                "cover_letter_file",
                "Add a cover letter or use the cover letter already saved in your profile.",
            )
        return cleaned_data

    def save(self, commit=True):
        application = super().save(commit=False)
        if not self.cleaned_data.get("cv_file") and self.cleaned_data.get("use_profile_cv"):
            application.cv_file = self.profile.cv_file
        if not self.cleaned_data.get("cover_letter_file") and self.cleaned_data.get("use_profile_cover_letter"):
            application.cover_letter_file = self.profile.cover_letter_file
        if commit:
            application.save()
        return application
