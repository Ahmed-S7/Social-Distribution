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


class Author(models.Model):
    """
    **Model that represents an author object in the application**\n
    *Fields*:\n
    id: the full API URL for the author (the path to the author's page on their given node)\n
    host: the full API URL for the author's node (the path to the author's node)\n
    displayName: the author's chosen username\n
    github: the (optional) user's github profile\n
    profileImage: the URL of the user's profile image\n
    web: the URL to the user's page on their node\n
    

    **Inherits from the default user model with these fields**:\n
    
    username – Unique identifier (max 150 characters).\n  
    
    id – Auto-generated primary key.\n 

    password – Hashed password storage.\n 

    first_name – Optional first name.\n 

    last_name – Optional last name.\n 

    email – Email address.\n 

    is_staff – Boolean flag for admin privileges.\n 

    is_active – Determines if the account is active.\n 

    is_superuser – Grants all permissions.\n 

    last_login – Timestamp of last login.\n 

    date_joined – Timestamp of account creation.\n 
    """
    type = models.CharField(default="author")
    
    user = models.OneToOneField(User, on_delete= models.CASCADE)
     
    authorURL = models.URLField(unique=True)# formatted as: "http://white/api/authors/[authorID]"
     
    host = models.URLField(default=f"http://s25-project-white/api/")
    
    displayName = models.CharField(max_length=150)
    
    github = models.URLField(blank=True, null=True, default=None)
    
    profileImage  = models.URLField(blank=True, null=True, default="https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y")
    
    web = models.URLField(blank=True, null=True, default=None)