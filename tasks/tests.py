from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Task


class TaskManagementApiTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="alice", password="pass12345")
        self.other_user = User.objects.create_user(username="bob", password="pass12345")
        self.client.force_authenticate(user=self.user)

    def test_category_crud_and_user_isolation(self):
        # create
        res = self.client.post("/api/categories/", {"name": "Work", "color": "#FF0000"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        category_id = res.data["id"]

        # list (paginated)
        res = self.client.get("/api/categories/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data["results"]
        self.assertTrue(any(c["id"] == category_id for c in results))

        # retrieve
        res = self.client.get(f"/api/categories/{category_id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], "Work")
        self.assertEqual(res.data["user"], self.user.id)

        # update
        res = self.client.patch(f"/api/categories/{category_id}/", {"name": "Work Updated"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], "Work Updated")

        # user isolation: other user's category should not be visible
        other_cat = Category.objects.create(name="Hidden", color="#00FF00", user=self.other_user)
        res = self.client.get("/api/categories/")
        results = res.data["results"]
        self.assertFalse(any(c["id"] == other_cat.id for c in results))

        # delete
        res = self.client.delete(f"/api/categories/{category_id}/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_task_crud(self):
        category = Category.objects.create(name="Work", color="#FF0000", user=self.user)

        # create
        payload = {
            "title": "Write tests",
            "description": "Cover CRUD and filtering",
            "priority": "High",
            "status": "To Do",
            "due_date": str(date.today() + timedelta(days=3)),
            "category": category.id,
        }
        res = self.client.post("/api/tasks/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        task_id = res.data["id"]

        # list (paginated)
        res = self.client.get("/api/tasks/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data["results"]
        self.assertTrue(any(t["id"] == task_id for t in results))

        # retrieve
        res = self.client.get(f"/api/tasks/{task_id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["title"], payload["title"])
        self.assertEqual(res.data["user"], self.user.id)

        # update
        res = self.client.patch(f"/api/tasks/{task_id}/", {"status": "In Progress"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "In Progress")

        # delete
        res = self.client.delete(f"/api/tasks/{task_id}/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=task_id).exists())

    def test_task_filtering(self):
        cat_a = Category.objects.create(name="A", color="#111111", user=self.user)
        cat_b = Category.objects.create(name="B", color="#222222", user=self.user)

        t1 = Task.objects.create(
            title="T1",
            priority="Low",
            status="To Do",
            due_date=date.today() + timedelta(days=1),
            user=self.user,
            category=cat_a,
        )
        t2 = Task.objects.create(
            title="T2",
            priority="High",
            status="Done",
            due_date=date.today() + timedelta(days=2),
            user=self.user,
            category=cat_b,
        )
        Task.objects.create(
            title="Other user task",
            priority="High",
            status="To Do",
            due_date=date.today() + timedelta(days=2),
            user=self.other_user,
            category=Category.objects.create(name="Other", color="#333333", user=self.other_user),
        )

        res = self.client.get("/api/tasks/?status=Done")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in res.data["results"]], [t2.id])

        res = self.client.get("/api/tasks/?priority=Low")
        self.assertEqual([item["id"] for item in res.data["results"]], [t1.id])

        res = self.client.get(f"/api/tasks/?category={cat_b.id}")
        self.assertEqual([item["id"] for item in res.data["results"]], [t2.id])
