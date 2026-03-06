# Task and Habit Tracker API

A comprehensive Django REST Framework API for tracking tasks, habits, and user productivity.

## Features

- **Authentication**: Token-based authentication for secure access.
- **Tasks**: Create, read, update, delete, filter, and organize tasks by category and priority.
- **Habits**: Track daily or weekly habits with automatically calculated streaks.
- **Dashboard**: Get an overview of your productivity, overdue tasks, habit streaks, and a daily motivational quote.
- **API Documentation**: Interactive API documentation via Swagger UI.

## Technologies Used

- Python 3.x
- Django & Django REST Framework
- SQLite (default for development)
- Django-Filter
- drf-spectacular (Swagger API Documentation)
- django-cors-headers
- python-dotenv

## Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd task_habit_tracker
   ```

2. **Create a virtual environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the project root containing:
   ```env
   SECRET_KEY=your_secret_key_here
   DEBUG=True
   ```
   (See `.env.example` if available)

5. **Apply Migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser** (optional, for admin panel):
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

## Endpoints

- **Admin**: `/admin/`
- **Docs (Swagger)**: `/api/docs/`
- **Schema**: `/api/schema/`
- **Users**: `/api/users/register/`, `/api/users/login/`, `/api/users/profile/`
- **Tasks**: `/api/tasks/`, `/api/categories/`
- **Habits**: `/api/habits/`, `/api/habits/<id>/log/`
- **Dashboard**: `/api/dashboard/`, `/api/dashboard/tasks/`, `/api/dashboard/habits/`, `/api/dashboard/quote/`, `/api/dashboard/weekly/`

## Testing

Run tests using:
```bash
python manage.py test
```
