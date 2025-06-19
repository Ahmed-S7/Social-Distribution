from django.contrib import admin
from .models import Page, Like, RemotePost,InboxItem,AuthorFriend, Author, FollowRequest, AuthorFollowing, Entry, AuthorFriend, Comment, CommentLike

# Register your models here.




class AuthorAdmin(admin.ModelAdmin):
    '''Follow Request Author following objects'''
    def get_queryset(self, request):
        return Author.all_objects.all()
    list_display = ["id","web","host","serial","displayName", "is_deleted","github","profileImage"]
    list_filter =  ["is_deleted", "host"]
    list_editable = ['displayName', 'github',"serial", "is_deleted", "profileImage"]
    search_fields = ["displayName", "github"]
 
    
class FollowRequestAdmin(admin.ModelAdmin):
    '''Admin Display For Follow Request following objects'''
    def get_queryset(self, request):
        return FollowRequest.all_objects.all()
    def follow_request(self, obj):
        return str(obj)

    
    list_display = ["follow_request","requester", "requested_account", "state", "is_deleted","created_at"]
    list_editable = ["state", "is_deleted"]
    list_filter =  ["is_deleted"]
    
class AuthorFollowingAdmin(admin.ModelAdmin):
    '''admin display for all author following objects'''
    def get_queryset(self, request):
        return AuthorFollowing.all_objects.all()
    def follow_standing(self, obj):
        return str(obj)
    list_display= ["follow_standing","id",'follower','following']
    search_fields= ['follower__displayName']
    
    
class AuthorFriendsAdmin(admin.ModelAdmin):
    '''admin display for all author friend objects'''
    def get_queryset(self, request):
        return AuthorFriend.all_objects.all()

    def friendship_update(self, obj):
        return str(obj)
    
    list_display= ['friendship_update',"id",'friended','friending']
    search_fields= ['friending__displayName','friended__displayName']
    list_filter =  ["is_deleted"]
    
    
class EntryAdmin(admin.ModelAdmin):
    '''dashboard display for all entries'''
    def get_queryset(self, request):
        return Entry.all_objects.all()
    def entry(self, obj):
        return str(obj)

    list_display= ['entry','id','author','is_deleted',"title",'content','image','created_at', 'serial','visibility']
    list_editable = ['author',"title",'content','image', 'serial','visibility']
    list_filter =  ["is_deleted"]
    
admin.site.register(Page)
admin.site.register(Like)
admin.site.register(RemotePost)
admin.site.register(AuthorFollowing, AuthorFollowingAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Entry, EntryAdmin)
admin.site.register(FollowRequest, FollowRequestAdmin)
admin.site.register(AuthorFriend, AuthorFriendsAdmin)
admin.site.register(InboxItem)
admin.site.register(Comment)
admin.site.register(CommentLike)
