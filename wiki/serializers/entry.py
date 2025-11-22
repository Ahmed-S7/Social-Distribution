"""
Entry and Like serializers.
"""
from rest_framework import serializers
from ..models import Entry, Like
from .author import AuthorSummarySerializer


VISIBILITY_CHOICES = [
    ('PUBLIC', 'Public'),
    ('FRIENDS', 'Friends Only'),
    ('UNLISTED', 'Unlisted'),
    ('DELETED', 'Deleted'),
]


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = '__all__'


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
        print(f"DEBUG: obj.entry: {obj.entry}")
        return obj.entry.id


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
        try:
            host = request.build_absolute_uri("/").rstrip("/") 
        except Exception as e:
            host = "http://127.0.0.1:8000/api/"
        return f"{host}/authors/{obj.author.serial}/entries/{obj.serial}"
    
    def get_description(self,obj):
        return f"entry by {obj.author}, titled: '{obj.title}"
    
    content = serializers.SerializerMethodField()
    
    def get_content(self, obj):
        return obj.content  

    def get_comments(self, obj):
        from .comment import CommentSummarySerializer
        author_id = obj.author.serial
        entry_id = obj.serial
        request = self.context.get("request")
        try:
            host = request.build_absolute_uri("/").rstrip("/") 
        except Exception as e:
            host = "http://127.0.0.1:8000/api/"

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
        try:
            host = request.build_absolute_uri("/").rstrip("/") 
        except Exception as e:
            host = "http://127.0.0.1:8000/api/"

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

