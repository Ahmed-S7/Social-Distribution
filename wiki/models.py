from django.db import models
import uuid
from django.db.models.signals import post_save, post_delete
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Manager, QuerySet, Q, UniqueConstraint
from django.dispatch import receiver
from django.forms import DateTimeField
from django.utils.timezone import make_aware
from django.utils import timezone
import pytz
from datetime import datetime
from django.utils.safestring import mark_safe
import markdown

# Create your models here.


# derived from: Django Software Foundation. (2025). Time zones. Django documentation (Version 5.2). Retrieved from https://docs.djangoproject.com/en/5.2/topics/i18n/timezones/
def get_mst_time():
    edmonton_timezone = pytz.timezone("America/Edmonton")
    naive_now = datetime.now()
    aware_now = edmonton_timezone.localize(naive_now)
    return aware_now
        
#The following soft-deletion logic (AppQuerySet, AppManager and BaseModel) was derived from Medium's article: https://medium.com/@tomisinabiodun/implementing-soft-delete-in-django-an-intuitive-guide-5c0f95da7f0d, June 15, 2025
class AppQuerySet(QuerySet):
    '''App Query Set that inherits from Django's defalt app query set
    - enables queries to update to is_deleted instead of hard deletion in the database'''
    def delete(self):
        self.update(is_deleted=True)
  
  
class AppManager(Manager):
    '''A manager that exterds from the default django app manager
        - this manager enables queries to ignore soft-deleted data
        
        '''
    def get_queryset(self):
        return AppQuerySet(self.model, using=self._db).exclude(is_deleted=True)
  
  
class BaseModel(models.Model):
    '''
       A model that extends from the Django base model
     - this model is capable of soft deletion so that deleted entities are still visible in the database  to administors
     - this way, all deleted data is visible in admin dashboards until permenantly deleted by an administrator
    '''
    class Meta:
        abstract = True
  
    is_deleted = models.BooleanField(default=False)
    
    def delete(self):
        self.is_deleted = True
        self.save()
        
class VisibilityOptions(models.TextChoices):
    '''Visibility Options For Entries Made In The Application'''
    PUBLIC = "public", "Public"
    UNLISTED = "unlisted", "Unlisted"
    FRIENDS_ONLY = "", "Friends_only"
    DELETED = "deleted", "Deleted"    



 
      
class Author(BaseModel):
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
    objects = AppManager()
    all_objects = models.Manager()
    type = models.CharField(default="author")
    
    #for future user story
    #is_registered= models.BooleanField(default=False)
    
    user = models.OneToOneField(User, on_delete= models.CASCADE, related_name="author")
     
    id = models.URLField(unique=True, primary_key=True)# formatted as: "http://{node}/api/authors/[authorID]"
     
    host = models.URLField(default=f"http://127.0.0.1:8000/")
    
    displayName = models.CharField(max_length=150)

    description = models.TextField(blank=True, null=True, default="")
    
    github = models.URLField(blank=True, null=True, default=None)
    
    serial = models.UUIDField(default=uuid.uuid4, null=True, unique=True)
    
    profileImage = models.URLField(blank=True, null=True)
    
    web = models.URLField(blank=True, null=False, default=None)
  
    
    
    @property
    def is_local(self):
        return self.host == "http://127.0.0.1:8000/" 
    def get_follow_requests_sent(self):
        '''Returns a list of all of the follow requests sent by an author'''
        return self.requesting.all()
        
    def get_follow_requests_recieved(self):
        '''Returns a list of all of the follow requests recieved by an author'''
        return self.follow_requests.order_by('-created_at')
    
    def get_all_entries(self):
        '''Returns a list of all of the entries recieved by an author'''
        return self.posts.order_by('-created_at')
    
    def get_unlisted_entries(self):
        '''Returns a list of all of the public entries created by an author'''
        return self.entries.filter(visibility=VisibilityOptions.PUBLIC)
    
    def get_web_url(self):
        '''Get the fully qualified URL to an author's page'''
        return self.web
    
    def get_inbox_items(self):
        '''return the JSON content of a user's inbox'''
        return InboxItem.objects.get(author=self)
    
    def is_already_requesting(self, other_author):
        '''checks if an author is actively requesting a specific author'''
        return FollowRequest.objects.filter(requester=self, requested_account=other_author, state=RequestState.REQUESTING, is_deleted=False).exists()
    
    def get_friends(self):
        '''
        retrieves a list of a user's friends
        '''
        pass
      
    def is_following(self, other_author):
        '''Check if an author currently follows another author'''
        if AuthorFollowing.objects.filter(follower=self, following=other_author).exists():
            return True
        return False
        
    def is_friends_with(self, other_author):
        '''checks if an author is friends with another author'''
        if AuthorFriend.objects.filter(friending=self.id, friended=other_author.id).exists() or AuthorFriend.objects.filter(friending=other_author.id, friended=self.id).exists():
            return True
        
        return False
    def get_friendship_id_with(self, other_author):
        '''Returns the frienship object between two authors, None if it does not exist'''
        ordered_friend_ids = sorted([self.id, other_author.id])
            
        try:
            friendship = AuthorFriend.objects.get(friending=ordered_friend_ids[0], friended=ordered_friend_ids[1])
        
        except AuthorFriend.DoesNotExist:
            return None
        
        return friendship.id
        
        
    def get_following_id_with(self, other_author):
        '''retrieve the id of the following object between a user and the author they follow if one exists, return None if one does not exist'''
        try:
            
            following_object = AuthorFollowing.objects.get(follower=self.id, following=other_author.id)
            follow_id = following_object.id
        
        except AuthorFollowing.DoesNotExist:
            follow_id = None
            
        return follow_id
   
    def is_following_remote(self, remoteId):
        pass
            
      
    def __str__(self):
        return self.displayName

    
@receiver(post_save, sender=User)
def update_author_name(sender, instance, **kwargs):
    try:
        author = Author.objects.get(user=instance)
        author.displayName = instance.username
        author.save()
    except Author.DoesNotExist:
        pass
         
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

    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='entry_images/', blank=True, null=True)
    created_at = models.DateTimeField(default=get_mst_time)
    id = models.URLField(unique=True, primary_key=True) 
    serial = models.UUIDField(default=uuid.uuid4, unique=True) 
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='PUBLIC')
    description = models.TextField(blank=True, null=True, default="")
    contentType = models.CharField(max_length=50, default="text/plain")
    web = models.URLField(blank=True, null=True, default=None)
    
    def get_entry_url(self):
        return f"http://s25-project-white/authors/{self.author.serial}/entries/{self.serial}"
    
    def get_web_url(self):
        return f"http://s25-project-white/authors/{self.author.serial}/entries/{self.serial}"
      

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self.get_entry_url()
        if not self.web:
            self.web = self.get_web_url()
        if self.image and not self.contentType.startswith("image/"):
            filename = self.image.name.lower()
            if filename.endswith(".png"):
               self.contentType = "image/png;base64"
            elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
               self.contentType = "image/jpeg;base64"
            else:
               self.contentType = "application/base64"
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

class Page(BaseModel):
    objects = AppManager()
    all_objects = models.Manager()
    title = models.CharField(max_length=100, unique=True)
    content = models.TextField()
    updated = models.DateTimeField(default=get_mst_time)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class Like(BaseModel):
    
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(Author, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['entry', 'user'],
                name='unique_active_like'
            )
        ]

class Comment(BaseModel):
    objects = AppManager()
    all_objects = models.Manager()
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=get_mst_time)
    contentType = models.CharField(max_length=50, default="text/plain")
    web = models.URLField(blank=True, null=True, default=None)
    
    
    def get_web_url(self):
        return f"http://s25-project-white/api/authors/{self.author.serial}/entries/{self.serial}"
    
    
    def __str__(self):
        return f"Comment by {self.author.displayName} on {self.entry.title}"

class CommentLike(BaseModel):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(Author, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=get_mst_time)
    
    def get_like_url(self):
        # Extract numeric author ID from the author's URL
        # Author ID format: "http://s25-project-white/api/authors/{author_id}"
        author_id = self.user.id.split('/')[-1]  # Get the last part of the URL
        return f"http://s25-project-white/api/authors/{author_id}/liked/{self.pk}"
    
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

class RemotePost(BaseModel):
    objects = AppManager()
    all_objects = models.Manager()
    origin = models.URLField()
    author = models.CharField(max_length=100)
    content = models.TextField()
    received_at = models.DateTimeField(default=get_mst_time)
    
    

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
            #lower id is first so that a friendship A-B cannot also be friendship B-A
            if self.friending.id > self.friended.id:
                self.friending, self.friended = self.friended, self.friending
                
            super().save(*args, **kwargs)
            
        def __str__(self):
             if self.is_deleted==True:
                return f"{self.friending.displayName} Is No Longer Friends With {self.friended.displayName}"
             
             return f"{self.friending.displayName} Is Friends With {self.friended.displayName}"
               
    
    
    
#The following model is derived from Stackoverflow.com: https://stackoverflow.com/questions/58794639/how-to-make-follower-following-system-with-django-model, June 14, 2025+ class AuthorFollowing(BaseModel):
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

class RequestState(models.TextChoices):
    """
    stores the possible follow request states 
    """
    REQUESTING = "requesting", "Requesting"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
        
    
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
 


class InboxObjectType(models.TextChoices):
    '''stores all of the possible inbox item types'''
    
    FOLLOW = "Follow", "follow"
    LIKE = "like", "Like"
    COMMENT = "comment", "Comment"
    ENTRY = "entry", "Entry" 
    AUTHOR = "author", "Author"
                
class InboxItem(BaseModel):
    objects = AppManager()
    all_objects = models.Manager()
    '''
    A general model for all of the different objects that can be pushed to the inbox 
    
    FIELDS:
    
    author: the author recieving the inbox item
    
    type: the type of inbox item
    
    content: the JSON in the inbox item
    
    created_at: the time that the inbox item was posted

    use: author.inboxItems to retrieve all of an authors inbox items, this is effectively their inbox
    '''
    
    author = models.ForeignKey(Author, related_name="inboxItems", on_delete=models.CASCADE)
    type = models.CharField(
        max_length = 20,
        choices=InboxObjectType.choices,
        null=False
    )
    body = models.JSONField()
    created_at =models.DateTimeField(default=get_mst_time)
    objects = AppManager()
    all_objects = models.Manager()
    
    def get_follow_requester_name(self):
        try:
            return self.get_content().get("actor")["displayName"]
        except Exception as e:
            raise e
        
    def get_follow_request_state(self):
        try:
            return self.get_content().get("state")
        except Exception as e:
            raise e
      
    
    def get_content(self):
        return self.content 
    
    def __str__(self):
        return f"{self.author} received Inbox Item object of type {self.type}"
        
   
        

    
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
        
class RemoteFollowing(BaseModel):
    """**Models a Remote Following**\n
    
    *Example Usages:*\n
        
    Get an author's list of remote follower objects:\n
        - author.remotefollowers.all()\n\n
        
    Get the state of a given follow request:\n
        - followrequest.get_request_state()
        
    FIELDS:
    - followerId: the ID of the remote following author
    - follower: the JSON object of the author that is the follower
    - following: the JSON object of the author getting followed
    - local_profile: the author object from this node
    - data_followed: the time that the following took place 
    """
    objects = AppManager()
    all_objects = models.Manager()
    followerId = models.URLField(null=False)#remote author ID
    follower = models.JSONField(null=False)#following author object
    following = models.JSONField(null=False)#followed author object
    local_profile= models.ForeignKey(Author, related_name="remotefollowers", on_delete=models.CASCADE, null=False)
    date_followed = models.DateTimeField(default=get_mst_time)
    
    class Meta:
        constraints = [
                UniqueConstraint(
                fields=['follower', 'following'],
                condition=Q(is_deleted=False),
                name='unique_active_remote_following'
            )
                
            ]
        
    def save(self, *args, **kwargs):
         if self.followerId == self.following['id']:
             raise ValidationError("You cannot follow Yourself")

        
         return super().save(*args,**kwargs)  
     
    def __str__(self):
        if self.is_deleted==True:
            return f"{self.followerId} No Longer Follows {self.local_profile.id}"
        else:
            return f"{self.followerId} Has Followed {self.local_profile.id}"


class RemoteFollowRequest(BaseModel):
    """**Models a follow Request**\n
    
    *Example Usages:*\n
        
    Get an author's list of follow requests:\n
        - author.remote_follow_requests.all()\n\n
        
    Get the state of a given follow request:\n
        - followrequest.get_request_state()
        
    FIELDS:
    - requesterId: the author sending the follow request
    - requested_account: the author recieving the follow request
    - type: indicates that this is a follow request
    - state: that state of the follow request (requesting, accepted, or rejected)
    
    """
    
    objects = AppManager()
    all_objects = models.Manager()
    requesterId = models.URLField(null=False)#foreign author ID
    requester = models.JSONField(null=False)#requesting author object
    requested_account = models.JSONField(null=False)#requested author object
    local_profile = models.ForeignKey(Author, related_name="remote_follow_requests", on_delete=models.CASCADE)
    type = models.CharField(default="follow")
    summary = models.CharField(default="You have recieved a follow request!")
    state = models.CharField(max_length=15, choices=RequestState.choices, default=RequestState.REQUESTING)
    created_at = models.DateTimeField(default=get_mst_time)
    class Meta:
        constraints = [
            UniqueConstraint(
            fields=['requesterId', 'requested_account', 'state'],
            condition=Q(is_deleted=False),
            name='unique_active_remote_follow_request'
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
         if self.requesterId == self.local_profile.id:
              raise ValidationError("You cannot send a follow request to  yourself.")
          
         #Validation Error Raised if a follow request already exists with:  
         if RemoteFollowRequest.objects.filter(
             requesterId=self.requesterId, # the same requesting user
             requested_account=self.requested_account, # the same requested user
             state__in=[RequestState.ACCEPTED, RequestState.REQUESTING] # with a status of requesting (current request is still pending) or accepted (meaning they follow the user already)
             ).exclude(pk=self.pk).exists():
            
            raise ValidationError("User already has an active follow request or relationship with this user")
        
        
         return super().save(*args,**kwargs)
    def __str__(self):
        return f"{self.requesterId} has requested to follow {self.local_profile.displayName}"  


class RemoteFriend(BaseModel):
    objects = AppManager()
    all_objects = models.Manager()
    friendingId = models.URLField(null=False)#foreign author's ID
    friended = models.ForeignKey(Author, related_name="remote_friends", null=False, on_delete=models.CASCADE)
    friended_at =  models.DateTimeField(default=get_mst_time)
       
    #prevents any duplicate friend requests
    class Meta:
            
    
        constraints = [
            UniqueConstraint(fields=['friendingId', 'friended'],
                                    condition=Q(is_deleted=False),
                                    name='unique_active_remote_friendship'
        )
        ]
        
    def save(self, *args, **kwargs):
        if self.friendingId == self.friended.id:
              raise ValidationError("You cannot be friends with yourself.")   
          
        return super().save(*args,**kwargs)    
     
    def __str__(self):
        if self.is_deleted==True:
            return f"{self.friendingId} Is No Longer Friends With {self.friended.displayName}"
             
        return f"{self.friendingId} Is Friends With {self.friended.displayName}"   
    