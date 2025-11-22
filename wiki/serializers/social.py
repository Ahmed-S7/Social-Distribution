"""
Social relationship serializers: Following, Friends, and Follow Requests.
"""
from rest_framework import serializers
from django.utils.timezone import localtime
from ..models import FollowRequest, AuthorFriend, AuthorFollowing
from .author import AuthorSerializer


class FollowRequestSerializer(serializers.ModelSerializer):
    actor = AuthorSerializer(source="requester")
    object = AuthorSerializer(source="requested_account")
    class Meta:
        model= FollowRequest
        fields = ["type","state","summary", "actor", "object"]
        
class FollowRequestReadingSerializer(serializers.ModelSerializer):
    actor = AuthorSerializer(source="requester", read_only=True)
    object = AuthorSerializer(source="requested_account", read_only=True)
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

