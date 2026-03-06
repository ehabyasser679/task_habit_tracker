import django_filters
from .models import Task
from datetime import date


class TaskFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(
        choices=Task.STATUS_CHOICES
    )
    priority = django_filters.ChoiceFilter(
        choices=Task.PRIORITY_CHOICES
    )
    
    due_date = django_filters.DateFilter()
    due_date_after = django_filters.DateFilter(
        field_name='due_date',
        lookup_expr='gte'
    )
    due_date_before = django_filters.DateFilter(
        field_name='due_date',
        lookup_expr='lte'
    )
    
    created_after = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    created_before = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte'
    )
    
    category = django_filters.NumberFilter()
    category_name = django_filters.CharFilter(
        field_name='category__name',
        lookup_expr='icontains'
    )
    
    title_contains = django_filters.CharFilter(
        field_name='title',
        lookup_expr='icontains'
    )
    
    has_due_date = django_filters.BooleanFilter(
        method='filter_has_due_date'
    )
    is_overdue = django_filters.BooleanFilter(
        method='filter_is_overdue'
    )
    
    class Meta:
        model = Task
        fields = [
            'status',
            'priority',
            'category',
            'due_date',
        ]
    
    def filter_has_due_date(self, queryset, name, value):
        if value:
            return queryset.exclude(due_date__isnull=True)
        return queryset.filter(due_date__isnull=True)
    
    def filter_is_overdue(self, queryset, name, value):
        if value:
            return queryset.filter(
                due_date__lt=date.today(),
                status__in=['To Do', 'In Progress']
            )
        return queryset.exclude(
            due_date__lt=date.today(),
            status__in=['To Do', 'In Progress']
        )