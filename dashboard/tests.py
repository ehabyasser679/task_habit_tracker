from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status


class DashboardAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client.force_authenticate(user=self.user)

    def test_dashboard_get(self):
        res = self.client.get("/api/dashboard/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("tasks", res.data)
        self.assertIn("habits", res.data)
        self.assertIn("quote", res.data)
        self.assertIn("productivity", res.data)

    def test_task_summary_get(self):
        res = self.client.get("/api/dashboard/tasks/summary/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("total", res.data)
        self.assertIn("by_status", res.data)

    def test_habit_summary_get(self):
        res = self.client.get("/api/dashboard/habits/summary/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("total_active", res.data)
        self.assertIn("habits", res.data)

    def test_weekly_progress_get(self):
        res = self.client.get("/api/dashboard/weekly-progress/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("weeks", res.data)

    def test_unauthenticated_access(self):
        self.client.force_authenticate(user=None)
        res = self.client.get("/api/dashboard/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
