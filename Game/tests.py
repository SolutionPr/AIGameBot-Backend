from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import GameConfig


class GameConfigDetailRouteTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user = get_user_model().objects.create_user(
            username="tester",
            email="tester@example.com",
            password="password123",
        )
        self.client.force_authenticate(user=user)
        self.config = GameConfig.objects.create(
            prompt="Create a simple runner",
            template="runner",
            title="Sky Dash",
            difficulty={"level": "easy"},
            theme={"style": "sky"},
            rules={"objective": "Reach the finish"},
            assets={"playerSprite": "runner"},
            raw_config={},
        )

    def test_detail_route_accepts_numeric_id(self):
        response = self.client.get(f"/api/configs/{self.config.pk}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.config.pk)

    def test_detail_route_rejects_placeholder_id(self):
        response = self.client.get("/api/configs/%3Cid%3E/")

        self.assertEqual(response.status_code, 400)
        self.assertIn("real numeric id", response.data["error"])
