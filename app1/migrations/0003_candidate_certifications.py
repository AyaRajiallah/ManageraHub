from django.db import migrations, models
import django.db.models.deletion
import app1.models


def move_existing_certifications(apps, schema_editor):
    CandidateProfile = apps.get_model("app1", "CandidateProfile")
    CandidateCertification = apps.get_model("app1", "CandidateCertification")

    for profile in CandidateProfile.objects.exclude(certifications_file="").iterator():
        if profile.certifications_file:
            CandidateCertification.objects.create(
                profile_id=profile.id,
                file=profile.certifications_file,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("app1", "0002_candidate_features"),
    ]

    operations = [
        migrations.CreateModel(
            name="CandidateCertification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to=app1.models.candidate_profile_file_path)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="certifications",
                        to="app1.candidateprofile",
                    ),
                ),
            ],
            options={
                "ordering": ["-uploaded_at", "-id"],
            },
        ),
        migrations.RunPython(move_existing_certifications, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="candidateprofile",
            name="certifications_file",
        ),
    ]
