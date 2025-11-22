"""
Author model and related signals.
"""
import uuid
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models import Q
from django.conf import settings
from .base import BaseModel, AppManager, VisibilityOptions, RequestState


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
     
    id = models.URLField(unique=True, primary_key=True)# formatted as: "http://{node}/api/authors/{AUTHOR_SERIAL}"
     
    host = models.URLField(default=f"http://127.0.0.1:8000/api")
    
    displayName = models.CharField(max_length=150)

    description = models.TextField(blank=True, default="")
    
    github = models.URLField(blank=True, default="")
    
    serial = models.UUIDField(default=uuid.uuid4, null=False, unique=True)
    
    profileImage = models.URLField(blank=True, default="")
    
    web = models.URLField(blank=True, null=False, default=None)
    
    is_local = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['displayName']
    
    def get_followers(self):
        from .social import AuthorFollowing
        follower_relationships = AuthorFollowing.objects.filter(following=self)
        followers = [relationship.follower for relationship in follower_relationships]
        print("This author's followers list: ", followers)
        return followers
    
    def get_followings(self):
        from .social import AuthorFollowing
        follow_relationships = AuthorFollowing.objects.filter(follower=self)
        followings = [relationship.following for relationship in follow_relationships]
        print(f"This author's followings are: {followings}")
        return followings
    
    def get_friends(self):
        '''
        retrieves a list of a user's friends
        '''
        from .social import AuthorFriend
        friendships = AuthorFriend.objects.filter(
        Q(friending=self) | Q(friended=self),
        is_deleted=False
        )

        friends = []
        for friendship in friendships:
            if friendship.friending == self:
                friends.append(friendship.friended)
            else:
                friends.append(friendship.friending) 
        print("This author's friends list: ", friends)
        return friends 
            
        
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
        from .inbox import InboxItem
        return InboxItem.objects.get(author=self)
    
    def is_already_requesting(self, other_author):
        '''checks if an author is actively requesting a specific author'''
        from .social import FollowRequest
        return FollowRequest.objects.filter(requester=self, requested_account=other_author, state=RequestState.REQUESTING, is_deleted=False).exists()
 
    def is_following(self, other_author):
        '''Check if an author currently follows another author'''
        from .social import AuthorFollowing
        if AuthorFollowing.objects.filter(follower=self, following=other_author).exists():
            return True
        return False
        
    def is_friends_with(self, other_author):
        '''checks if an author is friends with another author'''
        from .social import AuthorFriend
        if AuthorFriend.objects.filter(friending=self, friended=other_author).exists() or AuthorFriend.objects.filter(friending=other_author, friended=self).exists():
            return True
        
        return False
    def get_friendship_id_with(self, other_author):
        '''Returns the frienship object between two authors, None if it does not exist'''
        from .social import AuthorFriend
        # Try both orderings since friendship can be stored either way
        try:
            friendship = AuthorFriend.objects.get(friending=self, friended=other_author)
        except AuthorFriend.DoesNotExist:
            try:
                friendship = AuthorFriend.objects.get(friending=other_author, friended=self)
            except AuthorFriend.DoesNotExist:
                return None
        
        return friendship.id
    
     
    def get_following_id_with(self, other_author):
        '''retrieve the id of the following object between a user and the author they follow if one exists, return None if one does not exist'''
        from .social import AuthorFollowing
        try:
            following_object = AuthorFollowing.objects.get(follower=self, following=other_author)
            follow_id = following_object.id
        
        except AuthorFollowing.DoesNotExist:
            follow_id = None
            
        return follow_id
      
    def __str__(self):
        return self.displayName

    
def create_author_for_superuser(user):
    """
    Helper function to create an Author object for a superuser.
    Used when creating authors for admin users without a request context.
    """
    # Skip if author already exists
    if hasattr(user, 'author'):
        return user.author
    
    serial_id = uuid.uuid4()
    string_serial = str(serial_id)
    
    # Try to get host from settings or use default
    # Check if we're in a request context via thread-local
    try:
        from django.contrib.sites.models import Site
        current_site = Site.objects.get_current()
        scheme = 'https' if getattr(settings, 'USE_HTTPS', False) else 'http'
        host = f"{scheme}://{current_site.domain}"
    except Exception:
        # Fallback to default localhost
        host = "http://127.0.0.1:8000"
    
    base_id = f"{host}/api/authors/{string_serial}"
    base_web = f"{host}/authors/{string_serial}"
    
    new_author = Author(
        user=user,
        id=base_id,
        displayName=user.username,
        serial=serial_id,
        host=f"{host}/api/",
        github="",
        web=base_web,
        is_local=True
    )
    new_author.save()
    return new_author

@receiver(post_save, sender=User)
def handle_user_save(sender, instance, created, **kwargs):
    """
    Signal handler for User model post_save.
    - Creates Author for superusers if they don't have one
    - Updates author displayName when username changes
    """
    if created and instance.is_superuser:
        # Create author for newly created superuser
        try:
            create_author_for_superuser(instance)
        except Exception as e:
            print(f"Error creating author for superuser {instance.username}: {e}")
    elif hasattr(instance, 'author'):
        # Update author displayName if username changed
        try:
            author = instance.author
            if author.displayName != instance.username:
                author.displayName = instance.username
                author.save()
        except Exception:
            pass
    elif instance.is_superuser:
        # If user became superuser but doesn't have author, create one
        try:
            create_author_for_superuser(instance)
        except Exception as e:
            print(f"Error creating author for superuser {instance.username}: {e}")

@receiver(post_delete, sender=User)
def handle_user_delete(sender, instance, **kwargs):
    """
    Signal handler for User model post_delete.
    Note: Author will be automatically deleted due to CASCADE,
    but this signal can be used for additional cleanup if needed.
    """
    # The Author will be automatically deleted due to CASCADE on_delete
    # This signal is here for any additional cleanup if needed in the future
    pass

@receiver(post_save, sender=Author)
def update_user_username(sender, instance, **kwargs):
    """Update user's username when author's displayName changes"""
    user = instance.user
    if user and user.username != instance.displayName:
        user.username = instance.displayName
        user.save()

