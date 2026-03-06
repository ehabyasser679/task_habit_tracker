# Task & Habit Tracker API — Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture & Code Documentation](#architecture--code-documentation)
3. [Process & Methodology](#process--methodology)
4. [Fixes & Improvements Log](#fixes--improvements-log)
5. [Outcomes](#outcomes)

---

## Project Overview

A production-ready Django REST Framework API for personal task management, habit tracking, and productivity analytics. Users register, authenticate via tokens, and access a fully isolated set of tasks, habits, streaks, and a unified dashboard with motivational quotes.

**Tech Stack**: Python 3.13 · Django 6.0 · Django REST Framework · SQLite · drf-spectacular · django-cors-headers · django-filter · python-dotenv

---

## Architecture & Code Documentation

### Directory Structure

```
task_habit_tracker/
├── task_habit_tracker/       # Project config (settings, urls, wsgi)
├── users/                    # Authentication & user management
├── tasks/                    # Task & category CRUD with filtering
├── habits/                   # Habit tracking with streak calculations
├── dashboard/                # Aggregated analytics & quotes
├── .env                      # Environment variables (gitignored)
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

### App-by-App Breakdown

---

### `users` — Authentication & Profiles

#### [models.py](file:///c:/Users/Study/Desktop/task_habit_tracker/users/models.py)
Extends `AbstractUser` to allow future field additions without migration headaches later. Currently a pass-through; `AUTH_USER_MODEL = 'users.User'` in settings ensures all FK references point here.

#### [serializers.py](file:///c:/Users/Study/Desktop/task_habit_tracker/users/serializers.py)
- **`UserRegistrationSerializer`**: Accepts `username`, `email`, `password`, `first_name`, `last_name`. The `password` field is `write_only` so it never appears in responses. A custom `validate_password()` method runs Django's `AUTH_PASSWORD_VALIDATORS` (min-length, common password, numeric, attribute similarity) before the user is created via `create_user()` (which hashes the password).
- **`UserSerializer`**: Read-only representation for profile/login responses. Exposes `date_joined` but never the password.

#### [views.py](file:///c:/Users/Study/Desktop/task_habit_tracker/users/views.py)

| View | Method | Auth | Purpose |
|------|--------|------|---------|
| `RegistrationView` | POST | `AllowAny` | Creates user + returns token |
| `LoginView` | POST | `AllowAny` | Authenticates + returns token |
| `LogoutView` | POST | `IsAuthenticated` | Deletes user's auth token |
| `ProfileView` | GET | `IsAuthenticated` | Returns user profile (read-only) |
| `ProfileView` | PUT | `IsAuthenticated` | Updates profile fields (partial) |
| `ChangePasswordView` | POST | `IsAuthenticated` | Validates old pw, runs `validate_password()` on new pw, rotates token |

**Key design decisions**:
- `ProfileView.get()` is strictly read-only — it never calls `.save()`. Updates go through `PUT`.
- `ChangePasswordView` deletes all existing tokens and issues a fresh one after password change, invalidating any prior sessions.

#### [urls.py](file:///c:/Users/Study/Desktop/task_habit_tracker/users/urls.py)
```
POST /api/users/register/
POST /api/users/login/
POST /api/users/logout/
GET|PUT /api/users/profile/
POST /api/users/password/change/
```

#### [admin.py](file:///c:/Users/Study/Desktop/task_habit_tracker/users/admin.py)
Registers the custom `User` model using Django's built-in `UserAdmin` so it inherits the full admin interface (groups, permissions, etc.).

---

### `tasks` — Task & Category Management

#### [models.py](file:///c:/Users/Study/Desktop/task_habit_tracker/tasks/models.py)
- **`Category`**: Name + hex color, scoped per user via `unique_together = ['user', 'name']`. Ordered alphabetically by name to avoid pagination warnings.
- **`Task`**: Title, description, priority (Low/Medium/High), status (To Do/In Progress/Done), optional due date, FK to Category (nullable, `SET_NULL` on delete). Timestamps via `auto_now_add`/`auto_now`. Ordered by `-created_at`.

#### [serializers.py](file:///c:/Users/Study/Desktop/task_habit_tracker/tasks/serializers.py)
Three serializers for different use cases:
- **`TaskSerializer`**: Full CRUD serializer. Validates that the assigned category belongs to the requesting user. `category_name`/`category_color` use `allow_null=True, default=None` to handle tasks without a category.
- **`TaskListSerializer`**: Lightweight for list views (no description, no user FK).
- **`TaskDetailSerializer`**: Rich detail with nested `CategorySerializer`, username, and computed `days_until_due`.

#### [filters.py](file:///c:/Users/Study/Desktop/task_habit_tracker/tasks/filters.py)
`TaskFilter` provides advanced filtering: status, priority, category (by ID or name), date ranges (`due_date_after`, `created_before`), boolean filters (`has_due_date`, `is_overdue`).

#### [views.py](file:///c:/Users/Study/Desktop/task_habit_tracker/tasks/views.py)
`TaskViewSet` and `CategoryViewSet` — both `ModelViewSet` subclasses. Key points:
- `get_queryset()` filters to `user=request.user` for full data isolation.
- `get_serializer_class()` returns different serializers for `list` vs `retrieve` vs `create/update`.
- Custom actions: `/today/`, `/upcoming/`, `/completed/`, `/statistics/`, `/mark_complete/`, `/mark_in_progress/`.
- `perform_update`/`perform_destroy` double-check ownership (defense-in-depth beyond queryset filtering).

#### [urls.py](file:///c:/Users/Study/Desktop/task_habit_tracker/tasks/urls.py)
Uses DRF's `DefaultRouter` for automatic URL generation:
```
/api/tasks/               # List / Create
/api/tasks/{id}/           # Retrieve / Update / Delete
/api/tasks/today/          # Tasks due today
/api/tasks/upcoming/       # Tasks due within 7 days
/api/tasks/completed/      # Completed tasks
/api/tasks/statistics/     # Aggregate stats
/api/tasks/{id}/mark_complete/
/api/tasks/{id}/mark_in_progress/
/api/categories/           # Category CRUD
/api/categories/{id}/tasks/  # Tasks in a category
```

---

### `habits` — Habit Tracking & Streaks

#### [models.py](file:///c:/Users/Study/Desktop/task_habit_tracker/habits/models.py)
- **`Habit`**: Name, description, frequency (Daily/Weekly), active flag, user FK. Contains business logic methods:
  - `get_current_streak()`: Walks backward from today counting consecutive completed days. If today is not yet logged, starts from yesterday.
  - `get_longest_streak()`: Iterates all completed logs in chronological order, tracking the longest run of consecutive days.
  - `get_total_completions()`: Simple count of completed logs.
  - `get_completion_rate(days)`: Percentage of completed days over the requested window.
- **`HabitLog`**: One entry per habit per day (`unique_together`). Boolean `completed` field + optional notes.

#### [views.py](file:///c:/Users/Study/Desktop/task_habit_tracker/habits/views.py)
`HabitViewSet` with two custom actions:
- `POST /api/habits/{id}/log/` — Uses `update_or_create` so logging the same date twice updates rather than duplicates. Returns `201 CREATED` or `200 OK`.
- `GET /api/habits/{id}/logs/` — Full log history for a habit.

---

### `dashboard` — Analytics & Motivation

#### [views.py](file:///c:/Users/Study/Desktop/task_habit_tracker/dashboard/views.py)
Five views, all requiring authentication:

| View | Endpoint | Purpose |
|------|----------|---------|
| `DashboardView` | `GET /api/dashboard/` | Unified overview: task stats, habit streaks (top 5), motivational quote, productivity metrics, user info |
| `TaskSummaryView` | `GET /api/dashboard/tasks/summary/` | Task breakdown by status, priority, category; recent completions |
| `HabitSummaryView` | `GET /api/dashboard/habits/summary/` | Per-habit streaks, completion rates (7d & 30d), totals |
| `QuoteView` | `GET /api/dashboard/quote/` | On-demand quote from external API with category filter |
| `WeeklyProgressView` | `GET /api/dashboard/weekly-progress/` | 4-week rolling breakdown of completed tasks and habits |

**Performance optimizations**:
- `prefetch_related('logs')` on habit querysets to avoid N+1 queries.
- `date.today()` cached in a local variable per request to avoid repeated syscalls and ensure consistency within a single response.
- Motivational quotes cached for 1 hour via Django's cache framework (`LocMemCache`).

#### [serializers.py](file:///c:/Users/Study/Desktop/task_habit_tracker/dashboard/serializers.py)
Plain `Serializer` classes (not `ModelSerializer`) since the dashboard views construct dictionaries rather than querying single models. Includes `DashboardSerializer`, `TaskStatisticsSerializer`, `HabitStatisticsSerializer`, `QuoteSerializer`, `ProductivityMetricsSerializer`, `UserInfoSerializer`.

---

### `task_habit_tracker` — Project Configuration

#### [settings.py](file:///c:/Users/Study/Desktop/task_habit_tracker/task_habit_tracker/settings.py)

| Section | Key Settings |
|---------|-------------|
| **Secrets** | `SECRET_KEY` and `DEBUG` from `.env` via `python-dotenv` |
| **Hosts** | `ALLOWED_HOSTS = ['*']` in dev; env-configurable in prod |
| **Auth** | Token authentication globally, `IsAuthenticated` default permission |
| **Filtering** | `DjangoFilterBackend`, `SearchFilter`, `OrderingFilter` globally |
| **Pagination** | `PageNumberPagination` with `PAGE_SIZE = 10` |
| **API Docs** | `drf-spectacular` with `AutoSchema` |
| **CORS** | All origins in dev; env-configurable `CORS_ALLOWED_ORIGINS` in prod |
| **Security** | `SECURE_BROWSER_XSS_FILTER`, `X_FRAME_OPTIONS = 'DENY'`, `SECURE_CONTENT_TYPE_NOSNIFF`, secure cookies in prod |
| **Caching** | `LocMemCache` for quote caching |
| **Logging** | Structured console logging, level configurable via `DJANGO_LOG_LEVEL` env var |

#### [urls.py](file:///c:/Users/Study/Desktop/task_habit_tracker/task_habit_tracker/urls.py)
```
/admin/                  → Django admin
/api/users/*             → users app
/api/tasks/*             → tasks app (via router)
/api/categories/*        → tasks app (via router)
/api/habits/*            → habits app (via router)
/api/dashboard/*         → dashboard app
/api/schema/             → OpenAPI schema (drf-spectacular)
/api/docs/               → Swagger UI
```

---

## Process & Methodology

### Setup

1. Django project initialized with `django-admin startproject` (Django 6.0.1).
2. Four apps created: `users`, `tasks`, `habits`, `dashboard`.
3. Custom user model (`AbstractUser`) registered from the start to avoid migration conflicts.
4. Token authentication chosen for stateless API access (suitable for mobile/SPA frontends).

### Development Workflow

| Phase | Activities |
|-------|-----------|
| **Models** | Defined data models with choice fields, constraints (`unique_together`), and cascade rules |
| **Serializers** | Created per-action serializers (list vs detail vs create) with cross-model validation |
| **Views** | Implemented ViewSets with DRF routers for CRUD, plus custom `@action` endpoints |
| **Filtering** | Built `TaskFilter` with `django-filter` for advanced querying (date ranges, boolean filters) |
| **Dashboard** | Aggregated cross-app data into analytics views with productivity metrics |
| **Auth** | Registration, login, logout, profile, password change — all with token management |
| **Admin** | Registered all models with customized `ModelAdmin` classes |
| **Testing** | Unit tests for models (streak calculations), API tests for all endpoints |
| **Security Audit** | 18-issue audit and fix pass covering bugs, security, performance, and code quality |
| **Hardening** | Security headers, CSP evaluation, CORS lockdown, password validation enforcement |
| **Documentation** | API docs via Swagger (`drf-spectacular`), README, and this document |

### Tools Used

| Tool | Purpose |
|------|---------|
| Django 6.0 + DRF | Core framework |
| `django-filter` | Advanced queryset filtering |
| `drf-spectacular` | OpenAPI 3.0 schema + Swagger UI |
| `django-cors-headers` | CORS middleware |
| `python-dotenv` | Environment variable management |
| `requests` | External API calls (motivational quotes) |
| SQLite | Development database |
| Django test framework | Unit and integration testing |

---

## Fixes & Improvements Log

### Critical Bugs Fixed

| # | Bug | File | Resolution |
|---|-----|------|------------|
| 1 | `ProfileView.get()` mutated user data on GET requests | `users/views.py` | Split into read-only `get()` and separate `put()` for updates |
| 2 | Missing `get_total_completions()` → `AttributeError` crash on dashboard | `habits/models.py` | Added method returning `self.logs.filter(completed=True).count()` |
| 3 | Missing `get_completion_rate()` → `AttributeError` crash on dashboard | `habits/models.py` | Added method with percentage calculation over configurable window |

### Security Fixes

| # | Issue | Resolution |
|---|-------|------------|
| 5 | `ALLOWED_HOSTS = ['*']` hardcoded | Made conditional on `DEBUG`; env-configurable in production |
| 6 | `CORS_ALLOW_ALL_ORIGINS = True` always | Tied to `DEBUG`; production uses `CORS_ALLOWED_ORIGINS` from env |
| 7 | No password validation on registration | Added `validate_password()` to `UserRegistrationSerializer` |
| 8 | No password validation on password change | Added `validate_password()` to `ChangePasswordView` |
| 9 | `.env` exposed to version control | Created `.gitignore` excluding `.env`, `db.sqlite3`, `__pycache__` |
| — | Missing security headers | Added `SECURE_BROWSER_XSS_FILTER`, `X_FRAME_OPTIONS`, `SECURE_CONTENT_TYPE_NOSNIFF` |
| — | Cookies not secured for HTTPS | Added `CSRF_COOKIE_SECURE` and `SESSION_COOKIE_SECURE` (conditional on `not DEBUG`) |

### Performance Improvements

| # | Issue | Resolution |
|---|-------|------------|
| 10–11 | N+1 queries in dashboard habit loops | Added `prefetch_related('logs')` to habit querysets |
| 12 | `date.today()` called 8+ times per request | Cached in a single local variable |
| — | Quote API blocking requests for 5 seconds | Existing caching (1 hour) mitigates; first-miss still blocks |

### Code Quality Improvements

| # | Issue | Resolution |
|---|-------|------------|
| 14–16 | Unused imports (`settings`, `Q`, redundant `status`) | Removed |
| 17 | Custom `User` model not in admin | Registered with `UserAdmin` |
| 18 | `category_name`/`category_color` crashed on null category | Added `allow_null=True, default=None` to serializer fields |
| — | `get_longest_streak()` used truthy check on queryset | Changed to `.exists()` for clarity and correctness |
| — | `Category` model lacked ordering | Added `ordering = ['name']` to fix pagination warning |

### Test Fixes

| Issue | Resolution |
|-------|------------|
| Dashboard tests hit wrong URLs (404) | Corrected to match actual `urls.py` routes (`/summary/`, `/weekly-progress/`) |
| `test_log_habit` expected 200 for new log | Changed to expect 201 (`HTTP_201_CREATED`) |
| Pagination broke list endpoint assertions | Updated all tests to access `res.data["results"]` |

---

## Outcomes

### Deliverables

- **Fully functional REST API** with 20+ endpoints spanning user auth, task CRUD, habit tracking, and analytics
- **Interactive API documentation** at `/api/docs/` (Swagger UI)
- **14 passing tests** covering models, serializers, API endpoints, and authentication
- **Admin panel** with customized views for all models
- **Production-ready configuration** with env-based secrets, security headers, CORS lockdown, and password validation

### Known Limitations

| Limitation | Notes |
|------------|-------|
| **SQLite** | Suitable for development; should be replaced with PostgreSQL for production |
| **LocMemCache** | In-memory cache does not persist across process restarts; consider Redis for production |
| **Quote API** | First uncached request blocks for up to 5 seconds; could be moved to async/background task |
| **Streak calculation** | Queries DB per-day in a loop; could be optimized with bulk queries for large datasets |
| **No rate limiting** | Login and registration endpoints have no throttling against brute-force attacks |
| **No email verification** | Registration does not verify email addresses |

### Recommended Next Steps

1. **Switch to PostgreSQL** for production deployment
2. **Add Redis** for caching and potential Celery task queue
3. **Implement rate limiting** using DRF's throttling classes on auth endpoints
4. **Add email verification** on registration
5. **Write more tests**: edge cases for streak calculation, permission boundaries, pagination
6. **Add HTTPS enforcement** (`SECURE_SSL_REDIRECT = True`) when deploying behind a reverse proxy
7. **Consider async quote fetching** via a background task (Celery) to eliminate blocking
