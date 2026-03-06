from django.db import models
from django.conf import settings
from datetime import date, timedelta


class Habit(models.Model):
    FREQUENCY_CHOICES = [
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='Daily')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='habits')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_current_streak(self):
        today = date.today()
        streak = 0
        current_date = today
        today_log = self.logs.filter(date=today, completed=True).first()
        if not today_log:
            current_date = today - timedelta(days=1)
        while True:
            log = self.logs.filter(date=current_date, completed=True).first()
            if not log:
                break
            streak += 1
            current_date -= timedelta(days=1)
        return streak

    def get_longest_streak(self):
        completed_logs = self.logs.filter(completed=True).order_by('date')

        if not completed_logs.exists():
            return 0

        max_streak = 0
        current_streak = 1
        previous_date = None

        for log in completed_logs:
            if previous_date is None:
                previous_date = log.date
                continue

            if log.date == previous_date + timedelta(days=1):
                current_streak += 1
            else:
                max_streak = max(max_streak, current_streak)
                current_streak = 1
            previous_date = log.date

        max_streak = max(max_streak, current_streak)
        return max_streak

    def get_total_completions(self):
        """Return total number of completed logs for this habit."""
        return self.logs.filter(completed=True).count()

    def get_completion_rate(self, days=7):
        """Return completion rate as a percentage over the given number of days."""
        today = date.today()
        start_date = today - timedelta(days=days)
        completed_count = self.logs.filter(
            date__gte=start_date,
            date__lte=today,
            completed=True,
        ).count()
        if days == 0:
            return 0.0
        return round((completed_count / days) * 100, 1)


class HabitLog(models.Model):
    habit = models.ForeignKey(Habit, related_name='logs', on_delete=models.CASCADE)
    date = models.DateField()
    completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('habit', 'date')
        ordering = ['-date']

    def __str__(self):
        return f'{self.habit.name} - {self.date} - {"✓" if self.completed else "✗"}'
