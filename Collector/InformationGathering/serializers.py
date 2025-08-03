from rest_framework import serializers
from .models import Target

class TargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Target
        fields = ['id', 'name', 'host', 'type', 'is_local', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']
