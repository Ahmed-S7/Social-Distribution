"""
Social relationship models: Following, Friends, and Follow Requests.
"""
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.core.exceptions import ValidationError
from .base import BaseModel, AppManager, RequestState, get_mst_time
from .author import Author


#The following model is derived from Stackoverflow.com: https://stackoverflow.com/questions/58794639/how-to-make-follower-following-system-with-django-model, June 14, 2025
class AuthorFollowing(BaseModel):
    '''
    Model representing all of the instances where an author is followed or following someone\n
    
    This is effectively a *followers* and *following* list (not stored as a list, but can be queried to retrieve a list)\n
    
    **"following"** in related_name means the list of authors that **"follower" has followed** (the author's following list)\n
    **"followers"** in related_name means a list of the authors that **"following" author has been followed by** (author's follower list\n
    
    FIELDS: 
    
    follower: the one who initiated the following
    
    following: the one getting followed
    '''
    objects = AppManager()
    all_objects = models.Manager()
    follower = models.ForeignKey(Author, related_name="following", on_delete=models.CASCADE, null=False)
    following = models.ForeignKey(Author, related_name="followers", on_delete=models.CASCADE, null=False)
    date_followed = models.DateTimeField(default=get_mst_time)
    
    class Meta:
        constraints = [
                UniqueConstraint(
                fields=['follower', 'following'],
                condition=Q(is_deleted=False),
                name='unique_active_following'
            )
                
            ]
        
    #derived from stackoverflow.com: https://stackoverflow.com/questions/67658422/how-to-overwrite-save-method-in-django-model-form, "How to overwrite the save method in django model form", June 15, 2025
    def save(self, *args, **kwargs):
         if self.follower == self.following:
             raise ValidationError("You cannot follow Yourself")
         
         if self.follower.is_deleted or self.following.is_deleted:
            raise ValidationError("Cannot follow or be followed by a deleted author")
        
         return super().save(*args,**kwargs)  
     
    def __str__(self):
        if self.is_deleted==True:
                return f"{self.follower} No Longer Follows {self.following}"
            
        return f"{self.follower} Has Followed {self.following}"


class AuthorFriend(BaseModel):
        '''
        represents a friendship between 2 authors
        
        friending: is the arbitrary friend A
        friended: is the arbitrary friend B
        
        IMPORTANT: to collect all of a user's friendships, you must get all of the friend items where the user is Friend A OR Friend B
        
        FIELDS:
        
        friending: the arbitrary friend A
        
        friended: the arbitrary friend B
        
        friended_at: time the friendship was instantiated
      
        ''' 
        objects = AppManager()
        all_objects = models.Manager()
        friending = models.ForeignKey(Author, related_name="friend_a", on_delete=models.CASCADE, null=False)
        friended = models.ForeignKey(Author, related_name="friend_b", null=False, on_delete=models.CASCADE)
        friended_at =  models.DateTimeField(default=get_mst_time)
       
        #prevents any duplicate friend requests
        class Meta:
            
    
            constraints = [
                UniqueConstraint(fields=['friending', 'friended'],
                                        condition=Q(is_deleted=False),
                                        name='unique_active_friendship'
            )
            ]
            
        #prevent self-friending
        def save(self, *args, **kwargs):
            if self.friending == self.friended:
                raise ValidationError("You cannot send yourself a friend request")

            #corrected using ChatGPT: "How do I prevent duplicate friendships in reverse order?": https://chatgpt.com/, June 15, 2025
            #follower id is first so that a friendship A-B cannot also be friendship B-A
            if self.friending.id > self.friended.id:
                self.friending, self.friended = self.friended, self.friending
                
            super().save(*args, **kwargs)
            
        def __str__(self):
             if self.is_deleted==True:
                return f"{self.friending.displayName} Is No Longer Friends With {self.friended.displayName}"
             
             return f"{self.friending.displayName} Is Friends With {self.friended.displayName}"


class FollowRequest(BaseModel):
    """**Models a follow Request**\n
    
    *Example Usages:*\n
    
    Get an author's list of sent follow requests:\n
        - author.requesting.all()\n\n  
        
    Get an author's list of follow requests:\n
        - author.followRequests.all()\n\n
        
    Get the state of a given follow request:\n
        - followrequest.get_request_state()
        
    FIELDS:
    - requester: the author sending the follow request
    - requested_account: the author recieving the follow request
    - state: that state of the follow request (requesting, accepted, or rejected)
    """
    objects = AppManager()
    all_objects = models.Manager()
    type = models.CharField(default="follow")
    summary = models.CharField(default="You have recieved a follow request!")
    requester = models.ForeignKey(Author, related_name="requesting", on_delete=models.CASCADE, null=False) 
    requested_account = models.ForeignKey(Author, related_name="follow_requests", on_delete=models.CASCADE, null=False)
    state = models.CharField(max_length=15, choices=RequestState.choices, default=RequestState.REQUESTING)
    created_at = models.DateTimeField(default=get_mst_time)
    class Meta:
        constraints = [
            UniqueConstraint(
            fields=['requester', 'requested_account', 'state'],
            condition=Q(is_deleted=False),
            name='unique_active_follow_request'
        )
            
        ]
        
    def get_request_state(self):
        """returns the state of active follow requests"""
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
            self.state = new_state
            self.save() 
            
        else:
            raise TypeError("Could not update follow Request Status, new request state must be of Type 'RequestState'.")
        
    def save(self, *args, **kwargs):
         if self.requester == self.requested_account:
             raise ValidationError("You cannot send yourself a follow request.")
         
         #Validation Error Raised if a follow request already exists with:  
         if FollowRequest.objects.filter(
             requester=self.requester, # the same requesting user
             requested_account=self.requested_account, # the same requested user
             state__in=[RequestState.ACCEPTED, RequestState.REQUESTING] # with a status of requesting (current request is still pending) or accepted (meaning they follow the user already)
             ).exclude(pk=self.pk).exists():
            
            raise ValidationError("User already has an active follow request or relationship with this user")
        
        
         return super().save(*args,**kwargs)
    def __str__(self):
        return f"{self.requester.displayName} has requested to follow {self.requested_account.displayName}"

