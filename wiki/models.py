from django.db import models
import uuid
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# Create your models here.
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
    **Associated with an accompanying User object to keep username and password consistency**:
    """
    type = models.CharField(default="author")
    
    user = models.OneToOneField(User, on_delete= models.CASCADE)
     
    authorURL = models.URLField(unique=True)# formatted as: "http://white/api/authors/[authorID]"
     
    host = models.URLField(default=f"http://s25-project-white/api/")
    
    displayName = models.CharField(max_length=150)
    
    github = models.URLField(blank=True, null=True, default=None)
    
    serial = models.UUIDField(default=None, null=True, unique=True)
    
    profileImage  = models.URLField(blank=True, null=True, default="https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y")
    
    web = models.URLField(blank=True, null=True, default=None)
    
    def getFollowRequestsSent(self) ->list:
        '''Returns a list of all of the follow requests sent by an author'''
        return list(self.requesting.all())
        
    def getFollowRequestsRecieved(self)->list:
        '''Returns a list of all of the follow requests recieved by an author'''
        return list(self.follow_requests.all())
    
    def __str__(self):
        return self.displayName
       
   
   
class Page(models.Model):
    title = models.CharField(max_length=100, unique=True)
    content = models.TextField()
    updated = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class Like(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(Author, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('page', 'user')

class RemotePost(models.Model):
    origin = models.URLField()
    author = models.CharField(max_length=100)
    content = models.TextField()
    received_at = models.DateTimeField(auto_now_add=True)

 
    
#The following model is derived from Stackoverflow.com: https://stackoverflow.com/questions/58794639/how-to-make-follower-following-system-with-django-model, June 14, 2025+ 
class AuthorFollowing(models.Model):
    '''
    Model representing all of the instances where an author is followed or following someone\n
    
    This is effectively a *followers* and *following* list\n
    
    **"following"** in related_name means the list of authors that **"follower" has followed** (the author's following list)\n
    **"followers"** in related_name means a list of the authors that **"following" author has been followed by** (author's follower list\n
    '''
    follower = models.ForeignKey(Author, related_name="following", on_delete=models.CASCADE, null=False)
    following = models.ForeignKey(Author, related_name="followers", on_delete=models.CASCADE, null=False)
    date_followed = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("follower", "following")
        
    #derived from stackoverflow.com: https://stackoverflow.com/questions/67658422/how-to-overwrite-save-method-in-django-model-form, "How to overwrite the save method in django model form", June 15, 2025
    def save(self, *args, **kwargs):
         if self.follower == self.following:
             raise ValidationError("You cannot follow Yourself")
         return super().save(*args,**kwargs)  

class RequestState(models.TextChoices):
    """
    stores the possible follow request states 
    """
    REQUESTING = "requesting", "Requesting"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
        
    
class FollowRequest(models.Model):
    """**Models a follow Request**\n
    
    *Example Usages:*\n
    
    Get an author's list of sent follow requests:\n
        - author.requesting.all()\n\n  
        
    Get an author's list of follow requests:\n
        - author.followRequests.all()\n\n
        
    Get the state of a given follow request:\n
        - followrequest
    """
    
    type = models.CharField(default="follow")
    summary = models.CharField(default="You have recieved a follow request!")
    requester = models.ForeignKey(Author, related_name="requesting", on_delete=models.CASCADE, null=False) 
    requested_account = models.ForeignKey(Author, related_name="follow_requests", on_delete=models.CASCADE, null=False)
    
    state = models.CharField(max_length=15, choices=RequestState.choices, default=RequestState.REQUESTING)
    class Meta:
        unique_together = ("requester", "requested_account")
        
    def get_request_state(self)->str:
        return self.state
        
    def set_request_state(self, new_state:RequestState):
        '''
        **Updates the state of a sent follow request.**
        
        Example usage:
        
            - followRequest.set_request_state(RequestState.ACCEPTED)

        args:
        
            - new_state(RequestState): a valid request state to update the follow request to 
            
        Raises:
        
            - TypeError: whenever an invalid request state is passed to the function 
            
        '''
        if isinstance(new_state, RequestState):
            self.state = new_state.value
            self.save()
            
            
        else:
            raise TypeError("Could not update follow Request Status, new request state must be of Type 'RequestState'.")
        
    def save(self, *args, **kwargs):
         if self.requester == self.requested_account:
             raise ValidationError("You cannot send yourself a follow request.")
         
         return super().save(*args,**kwargs)
             
            

        
    
       
        