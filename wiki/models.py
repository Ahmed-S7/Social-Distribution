from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Page(models.Model):
    title = models.CharField(max_length=100, unique=True)
    content = models.TextField()
    updated = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class Like(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('page', 'user')

class RemotePost(models.Model):
    origin = models.URLField()
    author = models.CharField(max_length=100)
    content = models.TextField()
    received_at = models.DateTimeField(auto_now_add=True)


