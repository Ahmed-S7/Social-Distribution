"""
Comment serializers.
"""
from rest_framework import serializers
from .author import AuthorSummarySerializer


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

        return f"{like_author_host}/authors/{author_id}/liked/{obj.id}"

    def get_object(self, obj):
        # If the comment is remote and has a stored remote_id, use that
        if not obj.comment.is_local and obj.comment.remote_url:
            return obj.comment.remote_url.rstrip("/")

        # fallback to local construction (your current logic)
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
        try:
            host = request.build_absolute_uri("/").rstrip("/") 
        except Exception as e:
            host = "http://127.0.0.1:8000/api/"

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

