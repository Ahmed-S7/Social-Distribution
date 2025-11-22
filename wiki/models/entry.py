"""
Entry and Like models.
"""
import uuid
from django.db import models
from django.db.models import UniqueConstraint
from django.utils.safestring import mark_safe
import markdown
from urllib.parse import urlparse
from .base import BaseModel, AppManager, get_mst_time
from .author import Author


class Entry(BaseModel):
    '''Used to represent entries inside of the application '''
    VISIBILITY_CHOICES = [
        ('PUBLIC', 'Public'),
        ('FRIENDS', 'Friends Only'),
        ('UNLISTED', 'Unlisted'),
        ('DELETED', 'Deleted'),
    ]

    objects = AppManager()
    all_objects = models.Manager()
    origin_url = models.URLField(null=True, blank=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(default=get_mst_time)
    id = models.URLField(unique=True, primary_key=True) 
    serial = models.UUIDField(default=uuid.uuid4, unique=True) 
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='PUBLIC')
    description = models.TextField(blank=True, null=True, default="")
    contentType = models.CharField(max_length=50, default="text/plain")
    web = models.URLField(blank=True, null=True, default=None)
    is_local = models.BooleanField(default=False)
    
    def get_entry_url(self):
        host = urlparse(self.author.host).netloc
        return f"http://{host}/api/authors/{self.author.serial}/entries/{self.serial}"
    
    def get_web_url(self):
        host = urlparse(self.author.host).netloc
        return f"http://{host}/authors/{self.author.serial}/entries/{self.serial}"
      

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self.get_entry_url()
        if not self.web:
            self.web = self.get_web_url()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_formatted_content(self):
        """Return content with markdown processing if contentType is markdown"""
        if self.contentType == "text/markdown":
            return mark_safe(markdown.markdown(self.content))
        else:
            # For plain text, preserves line breaks
            return self.content.replace('\n', '<br>')


class Like(BaseModel):
    
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(Author, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, )
    is_local = models.BooleanField(default=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['entry', 'user'],
                name='unique_active_like'
            )
        ]

