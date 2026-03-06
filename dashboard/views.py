from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Count
from datetime import date, timedelta
import requests
from django.core.cache import cache

from tasks.models import Task
from habits.models import Habit, HabitLog
from .serializers import (
    DashboardSerializer,
    TaskStatisticsSerializer,
    HabitStatisticsSerializer,
    QuoteSerializer
)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        tasks = Task.objects.filter(user=user)

        task_stats = {
            'total': tasks.count(),
            'by_status': {
                'todo': tasks.filter(status='To Do').count(),
                'in_progress': tasks.filter(status='In Progress').count(),
                'done': tasks.filter(status='Done').count(),
            },
            'by_priority': {
                'low': tasks.filter(priority='Low').count(),
                'medium': tasks.filter(priority='Medium').count(),
                'high': tasks.filter(priority='High').count(),
            },
            'overdue': tasks.filter(
                due_date__lt=today,
                status__in=['To Do', 'In Progress']
            ).count(),
            'due_today': tasks.filter(due_date=today).count(),
            'upcoming': tasks.filter(
                due_date__range=[
                    today + timedelta(days=1),
                    today + timedelta(days=7)
                ],
                status__in=['To Do', 'In Progress']
            ).count(),
            'completed_this_week': tasks.filter(
                status='Done',
                updated_at__gte=week_ago
            ).count(),
            'completed_this_month': tasks.filter(
                status='Done',
                updated_at__gte=month_ago
            ).count(),
        }

        habits = Habit.objects.filter(user=user, is_active=True).prefetch_related('logs')
        habit_streaks = []
        for habit in habits:
            streak_data = {
                'id': habit.id,
                'name': habit.name,
                'current_streak': habit.get_current_streak(),
                'longest_streak': habit.get_longest_streak(),
                'completed_today': self._is_completed_today(habit, today),
                'completion_rate': habit.get_completion_rate(days=7)
            }
            habit_streaks.append(streak_data)

        habit_streaks.sort(key=lambda x: x['current_streak'], reverse=True)

        habit_stats = {
            'total_active': habits.count(),
            'total_inactive': Habit.objects.filter(user=user, is_active=False).count(),
            'completed_today': sum(1 for h in habit_streaks if h['completed_today']),
            'total_logs_this_week': HabitLog.objects.filter(
                habit__user=user,
                date__gte=week_ago
            ).count(),
            'streaks': habit_streaks[:5],
            'best_streak': max([h['current_streak'] for h in habit_streaks], default=0),
        }

        quote = self._fetch_motivational_quote()
        productivity = self._calculate_productivity_metrics(user, today, week_ago, month_ago)

        data = {
            'tasks': task_stats,
            'habits': habit_stats,
            'quote': quote,
            'productivity': productivity,
            'user': {
                'username': user.username,
                'email': user.email,
                'member_since': user.date_joined,
            }
        }

        serializer = DashboardSerializer(data)
        return Response(serializer.data)

    def _is_completed_today(self, habit, today):
        log = habit.logs.filter(date=today).first()
        return log.completed if log else False

    def _fetch_motivational_quote(self):
        cached_quote = cache.get('daily_quote')
        if cached_quote:
            return cached_quote

        try:
            response = requests.get(
                'https://api.quotable.io/random',
                params={'tags': 'motivational|inspirational'},
                timeout=5
            )
            response.raise_for_status()

            data = response.json()
            quote = {
                'text': data.get('content', 'Stay focused and keep going!'),
                'author': data.get('author', 'Unknown'),
                'tags': data.get('tags', [])
            }

            cache.set('daily_quote', quote, 3600)
            return quote

        except Exception:
            return {
                'text': 'Success is not final, failure is not fatal: it is the courage to continue that counts.',
                'author': 'Winston Churchill',
                'tags': ['motivational']
            }

    def _calculate_productivity_metrics(self, user, today, week_ago, month_ago):
        tasks_completed_week = Task.objects.filter(
            user=user,
            status='Done',
            updated_at__gte=week_ago
        ).count()

        tasks_completed_month = Task.objects.filter(
            user=user,
            status='Done',
            updated_at__gte=month_ago
        ).count()

        total_possible_logs_week = Habit.objects.filter(
            user=user,
            is_active=True
        ).count() * 7

        actual_logs_week = HabitLog.objects.filter(
            habit__user=user,
            date__gte=week_ago,
            completed=True
        ).count()

        habit_completion_rate = (
            (actual_logs_week / total_possible_logs_week * 100)
            if total_possible_logs_week > 0 else 0
        )

        return {
            'tasks_completed_this_week': tasks_completed_week,
            'tasks_completed_this_month': tasks_completed_month,
            'habit_completion_rate_week': round(habit_completion_rate, 1),
            'total_active_days_week': self._get_active_days(user, week_ago),
        }

    def _get_active_days(self, user, since_date):
        habit_dates = HabitLog.objects.filter(
            habit__user=user,
            date__gte=since_date
        ).values_list('date', flat=True).distinct()

        task_dates = Task.objects.filter(
            user=user,
            status='Done',
            updated_at__gte=since_date
        ).values_list('updated_at__date', flat=True).distinct()

        all_dates = set(list(habit_dates) + list(task_dates))
        return len(all_dates)


class TaskSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = date.today()
        tasks = Task.objects.filter(user=user)

        tasks_by_category = tasks.values('category__name').annotate(
            count=Count('id')
        ).order_by('-count')

        recent_completed = tasks.filter(
            status='Done'
        ).order_by('-updated_at')[:5].values(
            'id', 'title', 'updated_at', 'category__name'
        )

        data = {
            'total': tasks.count(),
            'by_status': {
                'todo': tasks.filter(status='To Do').count(),
                'in_progress': tasks.filter(status='In Progress').count(),
                'done': tasks.filter(status='Done').count(),
            },
            'by_priority': {
                'low': tasks.filter(priority='Low').count(),
                'medium': tasks.filter(priority='Medium').count(),
                'high': tasks.filter(priority='High').count(),
            },
            'by_category': list(tasks_by_category),
            'recent_completed': list(recent_completed),
            'overdue_count': tasks.filter(
                due_date__lt=today,
                status__in=['To Do', 'In Progress']
            ).count(),
        }

        serializer = TaskStatisticsSerializer(data)
        return Response(serializer.data)


class HabitSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        habits = Habit.objects.filter(user=user, is_active=True).prefetch_related('logs')

        habit_data = []
        for habit in habits:
            habit_data.append({
                'id': habit.id,
                'name': habit.name,
                'frequency': habit.frequency,
                'current_streak': habit.get_current_streak(),
                'longest_streak': habit.get_longest_streak(),
                'total_completions': habit.get_total_completions(),
                'completion_rate_7d': habit.get_completion_rate(days=7),
                'completion_rate_30d': habit.get_completion_rate(days=30),
            })

        data = {
            'total_active': habits.count(),
            'total_inactive': Habit.objects.filter(user=user, is_active=False).count(),
            'habits': habit_data,
            'total_logs': HabitLog.objects.filter(habit__user=user).count(),
            'total_completions': HabitLog.objects.filter(
                habit__user=user,
                completed=True
            ).count(),
        }

        serializer = HabitStatisticsSerializer(data)
        return Response(serializer.data)


class QuoteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        category = request.query_params.get('category', 'motivational')

        try:
            response = requests.get(
                'https://api.quotable.io/random',
                params={'tags': category},
                timeout=5
            )
            response.raise_for_status()

            data = response.json()
            quote = {
                'text': data.get('content'),
                'author': data.get('author'),
                'tags': data.get('tags', []),
                'length': data.get('length'),
            }

            serializer = QuoteSerializer(quote)
            return Response(serializer.data)

        except requests.RequestException:
            return Response({
                'error': 'Failed to fetch quote',
                'message': 'The quote service is temporarily unavailable.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class WeeklyProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = date.today()

        weekly_data = []

        for i in range(4):
            week_end = today - timedelta(days=i * 7)
            week_start = week_end - timedelta(days=6)

            tasks_completed = Task.objects.filter(
                user=user,
                status='Done',
                updated_at__date__range=[week_start, week_end]
            ).count()

            habit_logs = HabitLog.objects.filter(
                habit__user=user,
                date__range=[week_start, week_end],
                completed=True
            ).count()

            weekly_data.append({
                'week_start': week_start,
                'week_end': week_end,
                'tasks_completed': tasks_completed,
                'habits_completed': habit_logs,
                'total_activities': tasks_completed + habit_logs,
            })

        return Response({
            'weeks': weekly_data,
            'total_tasks': sum(w['tasks_completed'] for w in weekly_data),
            'total_habits': sum(w['habits_completed'] for w in weekly_data),
        })