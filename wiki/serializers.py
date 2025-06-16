from rest_framework import serializers
from .models import Page, Like, RemotePost, Author, FollowRequest
from django.contrib.auth.models import User

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

class AuthorSerializer(serializers.ModelSerializer):
    
    class Meta:
        model= Author
        fields = ["type", "id", "host", "displayName", "github", "profileImage", "web"]
        
        
class FollowRequestSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source="type")
    summary = serializers.CharField(source="summary")
    actor = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all())
    object = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all())
    
    class Meta:
        model= FollowRequest
        fields = ["type","summary","actor", "object"]
    