from rest_framework import serializers
from .models import Page, Like, RemotePost

class PageSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()

    class Meta:
        model = Page
        fields = '__all__'

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = '__all__'

class RemotePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = RemotePost
        fields = '__all__'
