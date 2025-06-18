from django.contrib import admin
from .models import Page, Like, RemotePost,InboxItem, Author, FollowRequest, AuthorFollowing, Entry, AuthorFriend, Comment

# Register your models here.




class AuthorAdmin(admin.ModelAdmin):
    list_display = ["id","web","host","displayName", "is_deleted","github","profileImage"]
    list_filter =  ["is_deleted", "host"]
    list_editable = ['displayName', 'github', "is_deleted", "profileImage"]
    
    search_fields = ["displayName", "github"]
 
    
class FollowRequestAdmin(admin.ModelAdmin):
    list_display = ["requester", "requested_account", "state", "is_deleted","created_at"]
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
admin.site.register(Comment)
