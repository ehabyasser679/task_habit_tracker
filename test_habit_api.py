import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_habit_tracker.settings')
django.setup()

from django.test import Client
from users.models import User
from habits.models import Habit
from rest_framework.authtoken.models import Token

client = Client()

user, created = User.objects.get_or_create(username='testhabituser', email='testhabit@test.com')
if created:
    user.set_password('testpass123')
    user.save()

token, _ = Token.objects.get_or_create(user=user)
auth_headers = {'HTTP_AUTHORIZATION': f'Token {token.key}'}

print("Testing Habit Creation...")
response = client.post('/api/habits/', {
    'name': 'Drink Water',
    'frequency': 'Daily'
}, **auth_headers)
print("Create Habit:", response.status_code, response.json())
habit_id = response.json().get('id', None)

if habit_id:
    print("\nTesting Habit Logging...")
    response = client.post(f'/api/habits/{habit_id}/log/', {
        'date': '2026-03-06',
        'completed': True,
        'notes': 'Drank 2L'
    }, content_type='application/json', **auth_headers)
    print("Log Habit:", response.status_code, response.json())

    print("\nTesting Logs History...")
    response = client.get(f'/api/habits/{habit_id}/logs/', **auth_headers)
    print("Log History:", response.status_code, response.json())

    print("\nTesting Streak Display...")
    response = client.get(f'/api/habits/{habit_id}/', **auth_headers)
    print("Get Habit Streaks:", response.status_code, response.json())
