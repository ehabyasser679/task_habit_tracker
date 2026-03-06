from django.contrib import admin
from .models import Habit, HabitLog

@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'frequency', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'user__username')
    list_filter = ('frequency', 'is_active', 'created_at')
    date_hierarchy = 'created_at'

@admin.register(HabitLog)
class HabitLogAdmin(admin.ModelAdmin):
    list_display = ('habit', 'get_user', 'date', 'completed')
    search_fields = ('habit__name', 'habit__user__username', 'notes')
    list_filter = ('completed', 'date')
    date_hierarchy = 'date'
    
    def get_user(self, obj):
        return obj.habit.user
    get_user.short_description = 'User'
    get_user.admin_order_field = 'habit__user'
