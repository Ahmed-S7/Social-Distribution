from rest_framework import serializers
from .models import Page, Like, RemotePost, Author, AuthorFriend, AuthorFollowing, FollowRequest, InboxItem, InboxObjectType, Entry, Comment, CommentLike
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
    

    def validate_displayName(self, value):
        # Enforce no spaces in username
        if  " " in value:
            raise serializers.ValidationError("Display name cannot contain any spaces.")
        if len(value) >= 150:
            raise serializers.ValidationError("Display name cannot be longer than 150 characters")
        return value
    
    def update(self, instance, validated_data):
        """
        Update and return an existing `Author` instance, given the validated data
        """
  
        if 'displayName' in validated_data:
            instance.displayName = validated_data['displayName']
            instance.user.username = instance.displayName  

        if 'github' in validated_data:
            instance.github = validated_data['github']
            
        if 'description' in validated_data:
            instance.description = validated_data['description']    
    
        if 'profileImage' in validated_data:
            instance.profileImage = validated_data['profileImage']
        
        instance.save()
        return instance
    
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

class AuthorSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = [
            'type', 'id', 'host', 'displayName', 'web', 'github', 'profileImage'
        ]
    type = serializers.SerializerMethodField()
    id = serializers.CharField()
    host = serializers.CharField()
    displayName = serializers.CharField()
    web = serializers.CharField()
    github = serializers.CharField()
    profileImage = serializers.SerializerMethodField()

    def get_type(self, obj):
        return 'author'
    def get_profileImage(self, obj):
        # If profileImage is an ImageField, return its URL
        if obj.profileImage:
            return obj.profileImage.url if hasattr(obj.profileImage, 'url') else obj.profileImage
        return None

class LikeSummarySerializer(serializers.Serializer):
    type = serializers.SerializerMethodField()
    author = AuthorSummarySerializer(source='user')
    published = serializers.DateTimeField(source='entry.created_at')
    id = serializers.CharField()
    object = serializers.CharField(source='entry.id')
    def get_type(self, obj):
        return 'like'

class CommentLikeSummarySerializer(serializers.Serializer):
    type = serializers.SerializerMethodField()
    author = AuthorSummarySerializer(source='user')
    published = serializers.SerializerMethodField()
    id = serializers.CharField()
    object = serializers.CharField(source='comment.id')
    
    def get_type(self, obj):
        return 'like'
    
    def get_published(self, obj):
        dt = obj.created_at.strftime('%Y-%m-%dT%H:%M:%S%z')
        # Insert colon into the timezone offset to match ISO 8601: +0000 → +00:00
        return dt[:-2] + ':' + dt[-2:]

class CommentSummarySerializer(serializers.Serializer):
    type = serializers.SerializerMethodField()
    author = AuthorSummarySerializer()
    comment = serializers.CharField(source='content')
    contentType = serializers.CharField()
    published = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    entry = serializers.CharField(source='entry.id')
    likes = serializers.SerializerMethodField()
    
    def get_type(self, obj):
        return 'comment'
    
    def get_published(self, obj):
        dt = obj.created_at.strftime('%Y-%m-%dT%H:%M:%S%z')
        # Insert colon into the timezone offset to match ISO 8601: +0000 → +00:00
        return dt[:-2] + ':' + dt[-2:]
    
    def get_id(self, obj):
        request = self.context.get('request')
        host = request.build_absolute_uri('/')[:-1] if request else 'http://localhost'

        # Extract author UUID (or last segment of URL)
        author_id = str(obj.author.id).rstrip('/').split('/')[-1]

        return f"{host}/api/authors/{author_id}/commented/{obj.id}"
    
    def get_likes(self, obj):
        # Return likes for this comment
        likes = obj.likes.filter(is_deleted=False)
        return {
            'type': 'likes',
            'id': f"{obj.id}/likes",
            'web': f"{obj.entry.web}/comments/{obj.id}/likes",
            'page_number': 1,
            'size': 50,
            'count': likes.count(),
            'src': [CommentLikeSummarySerializer(like).data for like in likes[:50]]
        }

class EntrySerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    id = serializers.CharField()
    web = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    contentType = serializers.CharField()
    content = serializers.CharField()
    author = AuthorSummarySerializer()
    comments = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    published = serializers.DateTimeField(source='created_at')
    visibility = serializers.CharField()

    class Meta:
        model = Entry
        fields = [
            'type', 'title', 'id', 'web', 'description', 'contentType', 'content',
            'author', 'comments', 'likes', 'published', 'visibility'
        ]

    def get_type(self, obj):
        return 'entry'

    def get_comments(self, obj):
        comments = obj.comments.filter(is_deleted=False).order_by('-created_at')[:5]
        total_comments = obj.comments.filter(is_deleted=False).count()
        return {
            'type': 'comments',
            'web': obj.web,
            'id': f"{obj.id}/comments",
            'page_number': 1,
            'size': 5,
            'count': total_comments,
            'src': [CommentSummarySerializer(comment).data for comment in comments]
        }

    def get_likes(self, obj):
        likes = obj.likes.filter(is_deleted=False).order_by('-id')[:50]
        total_likes = obj.likes.filter(is_deleted=False).count()
        return {
            'type': 'likes',
            'web': obj.web,
            'id': f"{obj.id}/likes",
            'page_number': 1,
            'size': 50,
            'count': total_likes,
            'src': [LikeSummarySerializer(like).data for like in likes]
        }
    