from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

class AuthAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="password", email="test@example.com")

    def test_register(self):
        payload = {
            "username": "newuser", 
            "password": "newpassword123", 
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User"
        }
        res = self.client.post("/api/users/register/", payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", res.data)

    def test_login(self):
        payload = {"username": "testuser", "password": "password"}
        res = self.client.post("/api/users/login/", payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("token", res.data)
