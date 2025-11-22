"""
RemotePost serializer.
"""
from rest_framework import serializers
from ..models import RemotePost


class RemotePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = RemotePost
        fields = '__all__'

