from rest_framework import serializers
from .models import  Page, Like, RemotePost, Author, AuthorFriend, AuthorFollowing, FollowRequest, InboxItem, InboxObjectType, Entry, Comment, CommentLike
from django.contrib.auth.models import User
from django.utils.timezone import localtime
import base64

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
    
    def create(self, validated_data):
        displayName = validated_data.get("id")
        user = User.objects.create(username=displayName, password="uniquepass")

        # Now create the Author and link the new user
        author = Author.objects.create(user=user, **validated_data)
        return author
       
        
        
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
        
        
class InboxItemSerializer(serializers.ModelSerializer):
    created_at=serializers.SerializerMethodField()
    class Meta:
        model = InboxItem
        fields = ["type", "author", "body", "created_at"]
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
    github = serializers.SerializerMethodField()
    profileImage = serializers.SerializerMethodField()

    def get_type(self, obj):
        return 'author'
    def get_profileImage(self, obj):
        # If profileImage is an ImageField, return its URL
        if obj.profileImage:
            return obj.profileImage.url if hasattr(obj.profileImage, 'url') else obj.profileImage
        return None
    def get_github(self,obj):
        return obj.github or None
    

class LikeSummarySerializer(serializers.Serializer):
    type = serializers.SerializerMethodField()
    author = AuthorSummarySerializer(source='user')
    published = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    object = serializers.SerializerMethodField()

    def get_type(self, obj):
        return 'like'

    def get_published(self, obj):
        dt = obj.created_at.strftime('%Y-%m-%dT%H:%M:%S%z')
        return dt[:-2] + ':' + dt[-2:]  # format as ISO 8601 with colon in timezone

    def get_id(self, obj):
        request = self.context.get('request')
        host = request.build_absolute_uri('/')[:-1] if request else 'http://localhost'

        # Extract author UUID from the user's id URL
        author_id = str(obj.user.id).rstrip('/').split('/')[-1]
        # fixed this
        return f"{host}/api/authors/{author_id}/liked/{obj.id}"

    def get_object(self, obj):
        # Use the entry author's host instead of the current request's host
        entry_author_host = obj.entry.author.host.rstrip('/')
        
        # Extract author UUID from the entry's author id URL
        entry_author_id = str(obj.entry.author.id).rstrip('/').split('/')[-1]
        entry_id = obj.entry.serial if hasattr(obj.entry, 'serial') else obj.entry.id
        return f"{entry_author_host}/authors/{entry_author_id}/entries/{entry_id}"


class CommentLikeSummarySerializer(serializers.Serializer):
    type = serializers.SerializerMethodField()
    author = AuthorSummarySerializer(source='user')
    published = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    object = serializers.SerializerMethodField()

    def get_type(self, obj):
        return 'like'

    def get_published(self, obj):
        dt = obj.created_at.strftime('%Y-%m-%dT%H:%M:%S%z')
        return dt[:-2] + ':' + dt[-2:]  # ISO 8601 with colon in timezone

    def get_id(self, obj):
        # Use the like author's host instead of the current request's host
        like_author_host = obj.user.host.rstrip('/')

        # Extract author UUID (or last segment of URL)
        author_id = str(obj.user.id).rstrip('/').split('/')[-1]

        return f"{like_author_host}/api/authors/{author_id}/liked/{obj.id}"

    def get_object(self, obj):
        # Use the comment author's host instead of the current request's host
        comment_author_host = obj.comment.author.host.rstrip('/')
        
        comment_author_id = str(obj.comment.author.id).rstrip('/').split('/')[-1]
        return f"{comment_author_host}/authors/{comment_author_id}/commented/{obj.comment.id}"


class CommentSummarySerializer(serializers.Serializer):
    type = serializers.SerializerMethodField()
    author = AuthorSummarySerializer()
    comment = serializers.CharField(source='content')
    contentType = serializers.CharField()
    published = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    entry = serializers.SerializerMethodField()
    web = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    
    def get_type(self, obj):
        return 'comment'
    
    def get_published(self, obj):
        dt = obj.created_at.strftime('%Y-%m-%dT%H:%M:%S%z')
        # Insert colon into the timezone offset to match ISO 8601: +0000 → +00:00
        return dt[:-2] + ':' + dt[-2:]
    
    def get_id(self, obj):
        # Use the comment author's host instead of the current request's host
        comment_author_host = obj.author.host.rstrip('/')

        # Extract author UUID (or last segment of URL)
        author_id = str(obj.author.id).rstrip('/').split('/')[-1]

        return f"{comment_author_host}/authors/{author_id}/commented/{obj.id}"
    
    def get_likes(self, obj):
        request = self.context.get('request')
        host = request.build_absolute_uri('/')[:-1] if request else 'http://localhost'

        author_id = str(obj.author.id).rstrip('/').split('/')[-1]

        likes = obj.likes.filter(is_deleted=False)
        return {
            "type": "likes",
            "id": f"{host}/api/authors/{author_id}/comments/{obj.id}/likes",
            "web": f"{host}/entries/{obj.entry.serial}",
            "page_number": 1,
            "size": 50,
            "count": likes.count(),
            "src": [CommentLikeSummarySerializer(like, context=self.context).data for like in likes[:50]]
        }
    
    def get_web(self, obj):
        request = self.context.get('request')
        host = request.build_absolute_uri("/").rstrip("/")

        return f"{host}/entries/{obj.entry.serial}"
    
    def get_entry(self, obj):
        # If the entry is remote, use its true FQID
        if not obj.entry.is_local:
            print(f"DEBUG: Remote entry URL: {obj.entry.serial}")
            print(f"DEBUG: Remote entry ID: {obj.entry.id}")
            return str(obj.entry.id)
        
        # Otherwise construct local URL
        entry_author_host = obj.entry.author.host.rstrip('/')
        if entry_author_host.endswith('/api'):
            entry_author_host = entry_author_host[:-4]

        return f"{entry_author_host}/api/authors/{obj.entry.author.serial}/entries/{obj.entry.serial}"


VISIBILITY_CHOICES = [
        ('PUBLIC', 'Public'),
        ('FRIENDS', 'Friends Only'),
        ('UNLISTED', 'Unlisted'),
        ('DELETED', 'Deleted'),
    ]
class EntrySerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    web = serializers.SerializerMethodField()
    title = serializers.CharField(required=True, min_length=5)
    description = serializers.SerializerMethodField()
    contentType = serializers.CharField( default="text/plain")
    content = serializers.CharField(required=True)
    author = AuthorSummarySerializer()
    comments = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    published = serializers.DateTimeField(source='created_at')
    visibility = serializers.ChoiceField(required=True, choices=VISIBILITY_CHOICES)
    class Meta:
        model = Entry
        fields = [
            'type', 'title', 'id', 'web', 'description', 'contentType', 'content',
            'author', 'comments', 'likes', 'published', 'visibility'
        ]

    def get_type(self, obj):
        return "entry"
    
    def get_web(self,obj):
        request = self.context.get('request')
        host = request.build_absolute_uri("/").rstrip("/")
        return f"{host}/authors/{obj.author.serial}/entries/{obj.serial}"
    
    def get_description(self,obj):
        return f"entry by {obj.author}, titled: '{obj.title}"
    
    content = serializers.SerializerMethodField()
    
    def get_content(self, obj):
        return obj.content  

    def get_comments(self, obj):
        author_id = obj.author.serial
        entry_id = obj.serial
        request = self.context.get("request")
        host = request.build_absolute_uri("/").rstrip("/")

        comments = obj.comments.filter(is_deleted=False).order_by('-created_at')[:5]
        total_comments = obj.comments.filter(is_deleted=False).count()

        return {
            "type": "comments",
            "web": f"{host}/entries/{entry_id}/",
            "id": f"{host}/api/authors/{author_id}/entries/{entry_id}/comments",
            "page_number": 1,
            "size": 5,
            "count": total_comments,
            "src": [CommentSummarySerializer(comment, context=self.context).data for comment in comments]
        }


    def get_likes(self, obj):
        author_id = obj.author.serial
        entry_id = obj.serial
        request = self.context.get("request")
        host = request.build_absolute_uri("/").rstrip("/")

        likes = obj.likes.filter(is_deleted=False).order_by('-id')[:50]
        total_likes = obj.likes.filter(is_deleted=False).count()

        return {
            "type": "likes",
            "web": f"{host}/authors/{author_id}/entries/{entry_id}",
            "id": f"{host}/api/authors/{author_id}/entries/{entry_id}/likes",
            "page_number": 1,
            "size": 50,
            "count": total_likes,
            "src": [LikeSummarySerializer(like, context=self.context).data for like in likes]
        }


    
    def update(self, instance, validated_data):
        validated_data.pop('author', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
        
        
