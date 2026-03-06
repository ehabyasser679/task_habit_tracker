from django.urls import path
from .views import (
    DashboardView,
    TaskSummaryView,
    HabitSummaryView,
    QuoteView,
    WeeklyProgressView
)

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('dashboard/tasks/summary/', TaskSummaryView.as_view(), name='task-summary'),
    path('dashboard/habits/summary/', HabitSummaryView.as_view(), name='habit-summary'),
    path('dashboard/quote/', QuoteView.as_view(), name='quote'),
    path('dashboard/weekly-progress/', WeeklyProgressView.as_view(), name='weekly-progress'),
]