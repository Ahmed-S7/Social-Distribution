"""
Other models: Page, RemotePost, RemoteNode, NodeConnectionCredentials.
"""
from django.db import models
from .base import BaseModel, AppManager, get_mst_time
from .author import Author


class Page(BaseModel):
    objects = AppManager()
    all_objects = models.Manager()
    title = models.CharField(max_length=100, unique=True)
    content = models.TextField()
    updated = models.DateTimeField(default=get_mst_time)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class RemotePost(BaseModel):
    objects = AppManager()
    all_objects = models.Manager()
    origin = models.URLField()
    author = models.CharField(max_length=100)
    content = models.TextField()
    received_at = models.DateTimeField(default=get_mst_time)


class RemoteNode(BaseModel):
    objects = AppManager()
    all_objects = models.Manager()

    url = models.URLField(unique=True)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        status = "active" if not self.is_deleted and self.is_active else "inactive"
        return f"{self.url} ({status})"
        
class NodeConnectionCredentials(BaseModel):
    username = models.CharField()
    password = models.CharField()

