from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.test import TestCase

from .models import CandidateCertification, CandidateProfile, JobApplication, JobOffer


class SigninRoutesTests(TestCase):
    def test_candidate_signin_route_renders(self):
        response = self.client.get("/candidate/signin")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Candidate")

    def test_company_signin_route_renders(self):
        response = self.client.get("/company/signin")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Company")

    def test_candidate_login_redirects_to_candidate_dashboard_url(self):
        User.objects.create_user(
            username="candidate@example.com",
            email="candidate@example.com",
            password="secret123",
        )

        response = self.client.post(
            "/candidate/signin",
            {
                "role": "candidate",
                "email": "candidate@example.com",
                "password": "secret123",
            },
        )

        self.assertRedirects(response, "/candidate/dashboard/", fetch_redirect_response=False)

    def test_company_login_redirects_to_company_dashboard_url(self):
        User.objects.create_user(
            username="company@example.com",
            email="company@example.com",
            password="secret123",
        )

        response = self.client.post(
            "/company/signin",
            {
                "role": "company",
                "email": "company@example.com",
                "password": "secret123",
            },
        )

        self.assertRedirects(response, "/company/dashboard", fetch_redirect_response=False)

    def test_candidate_registration_creates_profile_and_redirects_to_dashboard(self):
        response = self.client.post(
            "/candidate/register",
            {
                "first_name": "Aya",
                "last_name": "Raji",
                "email": "aya@example.com",
                "phone": "+212600000000",
                "country": "Morocco",
                "city": "Casablanca",
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!",
                "terms": "on",
            },
        )

        self.assertRedirects(response, "/candidate/dashboard/", fetch_redirect_response=False)
        user = User.objects.get(email="aya@example.com")
        self.assertTrue(CandidateProfile.objects.filter(user=user).exists())

    def test_candidate_dashboard_requires_candidate_account(self):
        response = self.client.get("/candidate/dashboard")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/candidate/signin", response.url)

    def test_candidate_dashboard_renders_for_candidate_user(self):
        user = User.objects.create_user(
            username="candidate2@example.com",
            email="candidate2@example.com",
            password="secret123",
        )
        CandidateProfile.objects.create(user=user, city="Rabat", country="Morocco")
        self.client.force_login(user)

        response = self.client.get("/candidate/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Candidate Dashboard")
        self.assertContains(response, "Home")
        self.assertContains(response, "Search jobs, companies, or keywords")

    def test_job_offers_page_shows_all_active_jobs_by_default(self):
        user = User.objects.create_user(
            username="jobs@example.com",
            email="jobs@example.com",
            password="secret123",
        )
        CandidateProfile.objects.create(user=user, city="Rabat", country="Morocco")
        JobOffer.objects.create(
            title="Product Designer",
            company_name="Atlas Studio",
            city="Rabat",
            country="Morocco",
            job_type="design",
            contract_type="full_time",
            experience_level="mid",
            summary="Shape elegant interfaces for hiring teams.",
            responsibilities="Design flows",
            requirements="Figma",
        )
        JobOffer.objects.create(
            title="Marketing Analyst",
            company_name="North Metrics",
            city="Casablanca",
            country="Morocco",
            job_type="marketing",
            contract_type="contract",
            experience_level="junior",
            summary="Support campaign reporting and analysis.",
            responsibilities="Analyze reports",
            requirements="Excel",
        )
        self.client.force_login(user)

        response = self.client.get("/candidate/jobs/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Product Designer")
        self.assertContains(response, "Marketing Analyst")
        self.assertContains(response, "Search jobs")

    def test_profile_update_saves_candidate_data(self):
        user = User.objects.create_user(
            username="profile@example.com",
            email="profile@example.com",
            password="secret123",
            first_name="Aya",
            last_name="Before",
        )
        CandidateProfile.objects.create(user=user)
        self.client.force_login(user)

        response = self.client.post(
            "/candidate/profile/",
            {
                "first_name": "Aya",
                "last_name": "After",
                "phone_number": "+212600000123",
                "address": "Casablanca-Settat",
                "city": "Casablanca",
                "country": "Morocco",
                "education_level": "master",
                "headline": "Junior software engineer",
                "skills": "Python, Django",
                "experience_summary": "Internship",
                "bio": "Looking for opportunities",
                "is_public": "on",
            },
        )

        self.assertRedirects(response, "/candidate/profile/?saved=1", fetch_redirect_response=False)
        user.refresh_from_db()
        profile = user.candidate_profile
        self.assertEqual(user.last_name, "After")
        self.assertEqual(profile.phone_number, "+212600000123")
        self.assertEqual(profile.address, "Casablanca-Settat")
        self.assertEqual(profile.education_level, "master")

    def test_candidate_can_apply_to_job_using_profile_documents(self):
        user = User.objects.create_user(
            username="apply@example.com",
            email="apply@example.com",
            password="secret123",
        )
        profile = CandidateProfile.objects.create(
            user=user,
            cv_file=SimpleUploadedFile("cv.txt", b"cv"),
            cover_letter_file=SimpleUploadedFile("cover.txt", b"cover"),
        )
        job = JobOffer.objects.create(
            title="Junior Frontend Developer",
            company_name="Atlas Digital",
            city="Casablanca",
            country="Morocco",
            job_type="engineering",
            contract_type="full_time",
            experience_level="junior",
            summary="Summary",
            responsibilities="Responsibilities",
            requirements="Requirements",
        )
        self.client.force_login(user)

        response = self.client.post(
            f"/candidate/jobs/{job.id}/apply/",
            {
                "full_name": "Aya Candidate",
                "email": "apply@example.com",
                "phone_number": "+212600000888",
                "application_text": "Ready to contribute.",
                "use_profile_cv": "on",
                "use_profile_cover_letter": "on",
            },
        )

        self.assertRedirects(response, f"/candidate/jobs/{job.id}/?applied=1", fetch_redirect_response=False)
        application = JobApplication.objects.get(candidate=user, job_offer=job)
        self.assertEqual(application.status, "sent")
        self.assertTrue(bool(application.cv_file))

    def test_profile_update_can_save_multiple_certifications(self):
        user = User.objects.create_user(
            username="certs@example.com",
            email="certs@example.com",
            password="secret123",
            first_name="Aya",
            last_name="Raji",
        )
        CandidateProfile.objects.create(user=user)
        self.client.force_login(user)

        response = self.client.post(
            "/candidate/profile/",
            {
                "first_name": "Aya",
                "last_name": "Raji",
                "phone_number": "+212600000123",
                "address": "Casablanca-Settat",
                "city": "Casablanca",
                "country": "Morocco",
                "education_level": "master",
                "headline": "Junior software engineer",
                "skills": "Python, Django",
                "experience_summary": "Internship",
                "bio": "Looking for opportunities",
                "is_public": "on",
                "certification_files": [
                    SimpleUploadedFile("cert1.txt", b"candidate certification 1"),
                    SimpleUploadedFile("cert2.txt", b"candidate certification 2"),
                ],
            },
        )

        self.assertRedirects(response, "/candidate/profile/?saved=1", fetch_redirect_response=False)
        self.assertEqual(CandidateCertification.objects.filter(profile=user.candidate_profile).count(), 2)
