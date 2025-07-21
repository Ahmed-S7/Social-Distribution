from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PageViewSet, RemotePostReceiver,follow_remote_profile,view_remote_profile, edit_profile, entry_detail, entry_detail_api, profile_view, get_profile_api, view_external_profile, get_or_edit_author_api
from .views import MyLoginView, user_wiki, register,user_inbox_api,foreign_followers_api,get_local_follow_requests,add_local_follower,process_follow_request, get_authors, view_local_authors, follow_profile, check_follow_requests, get_local_followers
from .views import edit_entry, add_comment, like_comment,view_entry_author, unfollow_profile, cancel_follow_request, delete_entry, like_entry_api, like_comment_api, get_entry_likes_api, create_entry, like_entry
from .views import get_entry_comments_api, register_api, login_api, get_author_likes_api, get_single_like_api, get_entry_image_api, get_author_image_api, get_author_comments_api,user_wiki_api
from django.contrib.auth.views import LogoutView

app_name ='wiki'
router = DefaultRouter()
router.register(r'pages', PageViewSet)

urlpatterns = [
    # Profile related URLs
    path('admin/', admin.site.urls),
    path('', MyLoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='wiki:login'), name='logout'),
    path('login/create_account/', register, name='register'),
    path('<str:username>/wiki/', user_wiki, name='user-wiki'),
    path('<str:username>/profile/', profile_view, name='profile'),
    path('<str:username>/profile/edit/', edit_profile, name='edit_profile'),

    path('api/<str:username>/wiki/', user_wiki_api, name='user_wiki_api'),
    
    #INBOX API, SHOULD BE USED FOR EVERY SINGLE TYPE OF INBOX OBJECT, SEE INBOX OBJECT STRUCTURE
    path('api/authors/<str:author_serial>/inbox/', user_inbox_api, name='user_inbox_api' ),
    
    # Author URLS
    path('authors/', view_local_authors, name='view_local_authors'),
    path('authors/<str:author_serial>', view_external_profile, name="view_external_profile"),
    path('authors/remote/<path:FOREIGN_AUTHOR_FQID>', view_remote_profile, name='view_remote_profile'),
    
    # Author Related API 
    path('api/authors/', get_authors, name='get_authors'),
    path('api/authors/<str:author_serial>/', get_or_edit_author_api, name='get_or_edit_author'),
    path('api/authors/<str:author_serial>/liked/', get_author_likes_api, name='get_author_likes_api'),
    path('api/authors/<str:author_serial>/liked/<int:like_serial>/', get_single_like_api, name='get_single_like_api'),
    path('api/authors/<str:author_serial>/commented/', get_author_comments_api, name='get_author_comments_api'),

     
    # Profile related API
    path('api/register/', register_api, name='register_api'),
    path('api/login/', login_api, name='login_api'),
    path('api/<str:username>/profile/', get_profile_api, name='get_profile_api'),

    # Entry Related URLs
    path('entry/<uuid:entry_serial>/', entry_detail, name='entry_detail'),
    path('entry/<uuid:entry_serial>/like/', like_entry, name='like-entry'),
    path('comment/<int:comment_id>/like/', like_comment, name='like-comment'),
    path('entry/<uuid:entry_serial>/comment/', add_comment, name='add_comment'),
    path('create_entry/', create_entry, name='create_entry'),
    path('entry/<uuid:entry_serial>/edit/', edit_entry, name='edit_entry'),
    path('entry/<uuid:entry_serial>/delete/', delete_entry, name='delete_entry'),
    path('entry/<uuid:entry_serial>/author/', view_entry_author, name="view_entry_author"),

    # Entry Related API
    path('api/authors/<str:author_serial>/entries/<uuid:entry_serial>/', entry_detail_api, name='entry_detail_api'),
    path('api/entry/<uuid:entry_serial>/like/', like_entry_api, name='like_entry_api'),
    path('api/authors/<str:author_serial>/entries/<uuid:entry_serial>/likes/', get_entry_likes_api, name='get_entry_likes_api'),
    #path('api/entry/<uuid:entry_serial>/comments/', add_comment_api, name='add_comment_api'),
    #path('api/entry/<uuid:entry_serial>/comments/view/', get_entry_comments_api, name='get_entry_comments_api'),
    path('api/authors/<str:author_serial>/entries/<uuid:entry_serial>/comments/', get_entry_comments_api, name='get_entry_comments_api'),
    path('api/comment/<int:comment_id>/like/', like_comment_api, name='like_comment_api'),

    # Image Entries API
    path('api/authors/<str:author_serial>/entry/<uuid:entry_serial>/image/', get_author_image_api, name='get_author_image_api'),
    path('api/entries/<uuid:entry_serial>/image/', get_entry_image_api, name='get_entry_image_api'),

    #Follow Requests/Followers API
    path('api/authors/<str:author_serial>/follow_requests/', get_local_follow_requests, name='get_follow_requests' ),
    path('api/authors/<str:author_serial>/followers/<path:FOREIGN_AUTHOR_FQID>/', foreign_followers_api, name='foreign_followers_api'),
    path('api/authors/<str:author_serial>/followers/', get_local_followers, name='get_local_followers' ),
    path('api/authors/local/<str:author_serial>/followers/<str:new_follower_serial>', add_local_follower, name='add_local_followers' ),
   
   
   #Follow Requests/Followers URLS 
    path('authors/<str:author_serial>/follow/', follow_profile, name="follow_profile"),
    path('authors/remotefollow/<path:FOREIGN_AUTHOR_FQID>', follow_remote_profile, name="follow_remote_profile"),
    path('authors/<str:username>/follow_requests/', check_follow_requests, name='check_follow_requests' ),
    path('authors/<str:author_serial>/<str:request_id>/', process_follow_request, name='process_follow_request' ),
    path('authors/<str:author_serial>/<str:request_id>/cancel_request', cancel_follow_request, name='cancel_follow_request' ),
    path('authors/<str:author_serial>/<str:following_id>/unfollow', unfollow_profile, name='unfollow_profile'),
   
   
]