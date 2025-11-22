"""
Comment and CommentLike models.
"""
from django.db import models
from django.db.models import UniqueConstraint
from urllib.parse import urlparse
from .base import BaseModel, AppManager, get_mst_time
from .author import Author
from .entry import Entry


class Comment(BaseModel):
    objects = AppManager()
    all_objects = models.Manager()
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=get_mst_time)
    contentType = models.CharField(max_length=50, default="text/plain")
    web = models.URLField(blank=True, null=True, default=None)
    is_local = models.BooleanField(default=True)
    remote_url = models.URLField(null=True, blank=True)
    

    def get_web_url(self):
        host = urlparse(self.author.host).netloc
        return f"http://{host}/api/authors/{self.author.serial}/entries/{self.serial}"
    
    
    def __str__(self):
        return f"Comment by {self.author.displayName} on {self.entry.title}"


class CommentLike(BaseModel):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(Author, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=get_mst_time)
    is_local = models.BooleanField(default=True)
    
    def get_like_url(self):
        # Extract numeric author ID from the author's URL
        # Author ID format: "http://localhost:8000/api/authors/{author_id}"
        author_id = self.user.id.split('/')[-1]  # Get the last part of the URL
        host = urlparse(self.user.host).netloc
        return f"http://{host}/api/authors/{author_id}/liked/{self.pk}"
    
    @property
    def id(self):
        return self.get_like_url()
    
    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['comment', 'user'],
                name='unique_comment_like'
            )
        ]

