from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Habit, HabitLog
from .serializers import HabitSerializer, HabitLogSerializer

class HabitViewSet(viewsets.ModelViewSet):
    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def log(self, request, pk=None):
        habit = self.get_object()
        serializer = HabitLogSerializer(data=request.data)
        if serializer.is_valid():
            date = serializer.validated_data.get('date')
            log, created = HabitLog.objects.update_or_create(
                habit=habit,
                date=date,
                defaults={
                    'completed': serializer.validated_data.get('completed', True),
                    'notes': serializer.validated_data.get('notes', '')
                }
            )
            return Response(
                HabitLogSerializer(log).data, 
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        habit = self.get_object()
        logs = habit.logs.all()
        serializer = HabitLogSerializer(logs, many=True)
        return Response(serializer.data)
