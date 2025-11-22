"""
InboxItem serializer.
"""
from rest_framework import serializers
from django.utils.timezone import localtime
from ..models import InboxItem


class InboxItemSerializer(serializers.ModelSerializer):
    created_at=serializers.SerializerMethodField()
    class Meta:
        model = InboxItem
        fields = ["type", "author", "body", "created_at"]
    def get_created_at(self,obj):
        return localtime(obj.created_at).isoformat()

