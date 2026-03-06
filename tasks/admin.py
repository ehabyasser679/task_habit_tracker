from django.contrib import admin
from .models import Category, Task

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'color')
    search_fields = ('name', 'user__username')
    list_filter = ('user',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'status', 'priority', 'due_date')
    search_fields = ('title', 'description', 'user__username')
    list_filter = ('status', 'priority', 'category', 'due_date')
    date_hierarchy = 'due_date'
