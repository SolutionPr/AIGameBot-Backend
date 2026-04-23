from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_accepts_first_and_last_name_without_username(self):
        payload = {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "password": "Password123!",
            "password_confirm": "Password123!",
        }

        response = self.client.post("/register", payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["user"]["first_name"], "Ada")
        self.assertEqual(response.data["user"]["last_name"], "Lovelace")
        self.assertEqual(response.data["user"]["email"], "ada@example.com")
        self.assertTrue(response.data["user"]["username"])
        self.assertFalse(get_user_model().objects.filter(username="").exists())

    def test_register_rejects_duplicate_email(self):
        User = get_user_model()
        User.objects.create_user(
            username="existing-user",
            email="ada@example.com",
            password="Password123!",
            first_name="Ada",
            last_name="Lovelace",
        )

        payload = {
            "first_name": "Ada",
            "last_name": "Byron",
            "email": "ada@example.com",
            "password": "Password123!",
            "password_confirm": "Password123!",
        }

        response = self.client.post("/register", payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data)

    def test_login_rotates_token_on_each_login(self):
        User = get_user_model()
        User.objects.create_user(
            username="login-user",
            email="user@example.com",
            password="Password123!",
            first_name="Ada",
            last_name="Lovelace",
        )

        payload = {
            "email": "user@example.com",
            "password": "Password123!",
        }

        first_response = self.client.post("/login", payload, format="json")
        second_response = self.client.post("/login", payload, format="json")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertNotEqual(first_response.data["access"], second_response.data["access"])

    def test_login_accepts_login_identifier(self):
        User = get_user_model()
        User.objects.create_user(
            username="username-login",
            email="username@example.com",
            password="Password123!",
            first_name="Ada",
            last_name="Lovelace",
        )

        response = self.client.post(
            "/login",
            {"login": "username-login", "password": "Password123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_profile_works_with_jwt_auth(self):
        User = get_user_model()
        User.objects.create_user(
            username="profile-user",
            email="profile@example.com",
            password="Password123!",
            first_name="Ada",
            last_name="Lovelace",
        )

        login_response = self.client.post(
            "/login",
            {"email": "profile@example.com", "password": "Password123!"},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200)

        token = login_response.data["access"]
        profile_response = self.client.get(
            "/profile",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.data["profile"]["email"], "profile@example.com")
