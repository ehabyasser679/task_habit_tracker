from rest_framework import serializers
from .models import Task, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'color', 'user']
        read_only_fields = ['user']

    def validate_color(self, value):
        if not value.startswith('#') or len(value) != 7:
            raise serializers.ValidationError("Color must be a valid hex code (e.g., #FF5733)")
        return value

class TaskSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True, default=None)
    category_color = serializers.CharField(source='category.color', read_only=True, allow_null=True, default=None)

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'priority',
            'status',
            'due_date',
            'created_at',
            'updated_at',
            'user',
            'category',
            'category_name',
            'category_color'
        ]
        read_only_fields = ['created_at', 'updated_at', 'user']

    def validate_title(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip()

    def validate(self, data):
        request = self.context.get('request')
        category = data.get('category')
        if request and category:
            if category.user != request.user:
                raise serializers.ValidationError({'category': 'You can only assign your own categories.'})
        return data

class TaskListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True, default=None)
    
    class Meta:
        model = Task
        fields = [
            'id', 
            'title',
            'priority',
            'status',
            'due_date',
            'category_name'
        ]

class TaskDetailSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source='category', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    days_until_due = serializers.SerializerMethodField()
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'priority',
            'status',
            'due_date',
            'created_at',
            'updated_at',
            'user',
            'category',
            'category_detail',
            'username',
            'days_until_due'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_days_until_due(self, obj):
        if obj.due_date:
            from datetime import date
            delta = obj.due_date - date.today()
            return delta.days
        return None