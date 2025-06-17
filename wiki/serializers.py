from rest_framework import serializers
from .models import Page, Like, RemotePost, Author, FollowRequest, InboxItem, InboxObjectType
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
    actor = AuthorSerializer(source="requester")
    object = AuthorSerializer(source="requested_account")
    class Meta:
        model= FollowRequest
        fields = ["type","summary", "actor", "object"]
        
    
class InboxItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = InboxItem
        fields = ["type", "author", "content", "created_at"]
    
    