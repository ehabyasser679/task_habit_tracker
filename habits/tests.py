from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Habit, HabitLog

class HabitModelTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.habit = Habit.objects.create(name="Exercise", user=self.user)

    def test_get_current_streak(self):
        today = date.today()
        HabitLog.objects.create(habit=self.habit, date=today, completed=True)
        HabitLog.objects.create(habit=self.habit, date=today - timedelta(days=1), completed=True)
        HabitLog.objects.create(habit=self.habit, date=today - timedelta(days=2), completed=True)
        
        self.assertEqual(self.habit.get_current_streak(), 3)
        
    def test_get_longest_streak(self):
        today = date.today()
        # Streak 1: 3 days
        HabitLog.objects.create(habit=self.habit, date=today - timedelta(days=10), completed=True)
        HabitLog.objects.create(habit=self.habit, date=today - timedelta(days=9), completed=True)
        HabitLog.objects.create(habit=self.habit, date=today - timedelta(days=8), completed=True)
        
        # Streak 2: 5 days
        HabitLog.objects.create(habit=self.habit, date=today - timedelta(days=5), completed=True)
        HabitLog.objects.create(habit=self.habit, date=today - timedelta(days=4), completed=True)
        HabitLog.objects.create(habit=self.habit, date=today - timedelta(days=3), completed=True)
        HabitLog.objects.create(habit=self.habit, date=today - timedelta(days=2), completed=True)
        HabitLog.objects.create(habit=self.habit, date=today - timedelta(days=1), completed=True)

        self.assertEqual(self.habit.get_longest_streak(), 5)

class HabitAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client.force_authenticate(user=self.user)
        self.habit = Habit.objects.create(name="Read", user=self.user)

    def test_create_habit(self):
        payload = {"name": "Meditate", "frequency": "Daily"}
        res = self.client.post("/api/habits/", payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_log_habit(self):
        payload = {"date": str(date.today()), "completed": True}
        res = self.client.post(f"/api/habits/{self.habit.id}/log/", payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(HabitLog.objects.count(), 1)
