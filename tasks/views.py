from datetime import date, timedelta

from rest_framework import viewsets, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from .models import Task, Category
from .serializers import TaskSerializer, CategorySerializer, TaskListSerializer, TaskDetailSerializer
from .filters import TaskFilter


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You can only update your own categories.")
        serializer.save()
    
    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You can only delete your own categories.")
        instance.delete()

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        category = self.get_object()
        tasks = Task.objects.filter(category=category, user=request.user)
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)

class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends=[
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_class = TaskFilter
    # filterset_fields = ['status', 'priority', 'category']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'priority', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        elif self.action == 'retrieve':
            return TaskDetailSerializer
        return TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You can only update your own tasks.")
        serializer.save()
    
    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You can only delete your own tasks.")
        instance.delete()

    @action(detail=False, methods=['get'])
    def today(self, request):
        tasks = self.get_queryset().filter(due_date=date.today())
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        today = date.today()
        next_week = today + timedelta(days=7)
        tasks = self.get_queryset().filter(due_date__range=[today, next_week])
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def completed(self, request):
        tasks = self.get_queryset().filter(status='Done')
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None):
        task = self.get_object()
        task.status = 'Done'
        task.save()
        serializer = self.get_serializer(task)
        return Response({'message': 'Task marked as complete.', 'task': serializer.data})
    @action(detail=True, methods=['post'])
    def mark_in_progress(self, request, pk=None):
        task = self.get_object()
        task.status = 'In Progress'
        task.save()
        serializer = self.get_serializer(task)
        return Response({'message': 'Task marked as in progress.', 'task': serializer.data})
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        queryset = self.get_queryset()
        stats = {
            'total': queryset.count(),
            'by_status': {
                'To Do': queryset.filter(status='To Do').count(),
                'In Progress': queryset.filter(status='In Progress').count(),
                'Done': queryset.filter(status='Done').count(),
            },
            'by_priority': {
                'Low': queryset.filter(priority='Low').count(),
                'Medium': queryset.filter(priority='Medium').count(),
                'High': queryset.filter(priority='High').count(),
            },
            'overdue': queryset.filter(due_date__lt=date.today(), status__in=['To Do', 'In Progress']).count() if queryset.exists() else 0,
        }
        return Response(stats)
    