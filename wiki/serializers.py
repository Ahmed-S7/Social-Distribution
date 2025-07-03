from rest_framework import serializers
from .models import Page, Like, RemotePost, Author,AuthorFriend, AuthorFollowing, FollowRequest, InboxItem, InboxObjectType, Entry
from django.contrib.auth.models import User
from django.utils.timezone import localtime

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
        fields = ["type", "id", "host", "displayName", "github", "profileImage", "web", "description"]
        
        
class FollowRequestSerializer(serializers.ModelSerializer):
    actor = AuthorSerializer(source="requester")
    object = AuthorSerializer(source="requested_account")
    class Meta:
        model= FollowRequest
        fields = ["type","state","summary", "actor", "object"]
        
class AuthorFriendSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorFriend
        fields = ['friending','friended','friended_at']
        
        
class AuthorFollowingSerializer(serializers.ModelSerializer):
    date_followed = serializers.SerializerMethodField()
    class Meta:
        model = AuthorFollowing
        fields = ['follower', 'following',  'date_followed']
    def get_date_followed(self,obj):
        return localtime(obj.date_followed).isoformat()
        
class InboxItemSerializer(serializers.ModelSerializer):
    created_at=serializers.SerializerMethodField()
    class Meta:
        model = InboxItem
        fields = ["type", "author", "content", "created_at"]
    def get_created_at(self,obj):
        return localtime(obj.created_at).isoformat()

class EntrySerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    created_at=serializers.SerializerMethodField()

    class Meta:
        model = Entry
        fields = ['id', 'title', 'content', 'created_at', 'author', 'url', 'visibility']
    
    def get_created_at(self,obj):
        return localtime(obj.created_at).isoformat()
    
    def get_url(self, obj):
        return f"http://s25-project-white/api/entries/{obj.serial}/"