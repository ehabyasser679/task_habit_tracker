from rest_framework import serializers


class QuoteSerializer(serializers.Serializer):
    text = serializers.CharField()
    author = serializers.CharField()
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    length = serializers.IntegerField(required=False)


class TaskStatisticsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    by_status = serializers.DictField()
    by_priority = serializers.DictField()
    by_category = serializers.ListField(required=False)
    recent_completed = serializers.ListField(required=False)
    overdue_count = serializers.IntegerField(required=False)


class HabitStreakSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    current_streak = serializers.IntegerField()
    longest_streak = serializers.IntegerField()
    completed_today = serializers.BooleanField()
    completion_rate = serializers.FloatField()


class HabitStatisticsSerializer(serializers.Serializer):
    total_active = serializers.IntegerField()
    total_inactive = serializers.IntegerField()
    habits = serializers.ListField(required=False)
    total_logs = serializers.IntegerField(required=False)
    total_completions = serializers.IntegerField(required=False)
    completed_today = serializers.IntegerField(required=False)
    total_logs_this_week = serializers.IntegerField(required=False)
    streaks = serializers.ListField(required=False)
    best_streak = serializers.IntegerField(required=False)


class ProductivityMetricsSerializer(serializers.Serializer):
    tasks_completed_this_week = serializers.IntegerField()
    tasks_completed_this_month = serializers.IntegerField()
    habit_completion_rate_week = serializers.FloatField()
    total_active_days_week = serializers.IntegerField()


class UserInfoSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    member_since = serializers.DateTimeField()


class DashboardSerializer(serializers.Serializer):
    tasks = serializers.DictField()
    habits = serializers.DictField()
    quote = QuoteSerializer()
    productivity = ProductivityMetricsSerializer()
    user = UserInfoSerializer()