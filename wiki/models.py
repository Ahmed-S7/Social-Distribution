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
    
    
#The following model is derived from Stackoverflow.com: https://stackoverflow.com/questions/58794639/how-to-make-follower-following-system-with-django-model, June 14, 2025+ 
class AuthorFollowing(models.Model):
    '''
    Model representing all of the instances where an author is followed or following someone\n
    This is effectively a *followers* and *following* list\n
    **"following"** in related_name means the list of authors that **"follower" has followed** (the author's following list)\n
    **"followers"** in related_name means a list of the authors that **"following" author has been followed by** (author's follower list\n
    '''
    follower = models.ForeignKey(Author, related_name="following", on_delete=models.CASCADE)
    following = models.ForeignKey(Author, related_name="followers", on_delete=models.CASCADE)
    date_followed = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("follower", "following")
        

class RequestStatus(models.TextChoices):
    """
    stores the possible follow request states 
    """
    REQUESTING = "requesting", "Requesting"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
        
    
class FollowRequest(models.Model):
    """Models a follow Request"""
    
    type = models.CharField(default="follow")
    summary = models.CharField(default="You have recieved a follow request!")
    
    requester = models.ForeignKey(Author, related_name="requesting", on_delete=models.CASCADE) #store an association of every author that a given author is requesting 
    requestedAccount = models.ForeignKey(Author, related_name="followRequests", on_delete=models.CASCADE)
    
    state = models.CharField(max_length=15, choices=RequestStatus.choices, default=RequestStatus.REQUESTING)
    class Meta:
        unique_together = ("requester", "requestedAccount")