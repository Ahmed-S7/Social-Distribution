from django.contrib import admin
from .models import Page, Like, RemotePost,InboxItem, Author, FollowRequest, AuthorFollowing, Entry, AuthorFriend

# Register your models here.


'''
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
    type = models.CharField(default="author")
    
    user = models.OneToOneField(User, on_delete= models.CASCADE)
     
    authorURL = models.URLField(unique=True)# formatted as: "http://white/api/authors/[authorID]"
     
    host = models.URLField(default=f"http://s25-project-white/api/")
    
    displayName = models.CharField(max_length=150)
    
    github = models.URLField(blank=True, null=True, default=None)
    
    serial = models.UUIDField(default=None, null=True, unique=True)
    
    profileImage  = models.URLField(blank=True, null=True, default="https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y")
    
    web = models.URLField(blank=True, null=False, default=None)
'''
class AuthorAdmin(admin.ModelAdmin):
    list_display = ["id","web","host","displayName", "is_deleted","github","profileImage"]
    list_filter =  ["is_deleted", "host"]
    list_editable = ['displayName', 'github', "is_deleted", "profileImage"]
    
    search_fields = ["displayName", "github"]
 
    
class FollowRequestAdmin(admin.ModelAdmin):
    list_display = ["requester", "summary", "requested_account", "state", "is_deleted","created_at"]
    list_editable = ["state", "is_deleted"]
    
class AuthorFollowingAdmin(admin.ModelAdmin):
    list_display= ["id",'follower','following']
    search_fields= ['follower__displayName']
    
admin.site.register(Page)
admin.site.register(Like)
admin.site.register(RemotePost)
admin.site.register(AuthorFollowing, AuthorFollowingAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Entry)
admin.site.register(FollowRequest, FollowRequestAdmin)
admin.site.register(AuthorFriend)
admin.site.register(InboxItem)