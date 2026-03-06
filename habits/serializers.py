from rest_framework import serializers
from .models import Habit, HabitLog

class HabitLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = HabitLog
        fields = ['id', 'date', 'completed', 'notes']
        read_only_fields = ['id']

    def create(self, validated_data):
        # habit is passed in save()
        return HabitLog.objects.create(**validated_data)

class HabitSerializer(serializers.ModelSerializer):
    current_streak = serializers.SerializerMethodField()
    longest_streak = serializers.SerializerMethodField()

    class Meta:
        model = Habit
        fields = ['id', 'name', 'description', 'frequency', 'is_active', 'created_at', 'current_streak', 'longest_streak']
        read_only_fields = ['id', 'created_at']

    def get_current_streak(self, obj):
        return obj.get_current_streak()

    def get_longest_streak(self, obj):
        return obj.get_longest_streak()
