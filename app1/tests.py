from django.contrib.auth.models import User
from django.test import TestCase


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

        self.assertRedirects(response, "/candidate/dashboard", fetch_redirect_response=False)

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
