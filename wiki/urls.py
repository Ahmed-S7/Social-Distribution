from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PageViewSet, RemotePostReceiver, edit_profile, edit_profile_api, entry_detail, entry_detail_api, profile_view
from .views import MyLoginView, user_wiki, register,get_local_follow_requests,process_follow_request, get_authors, view_authors, view_external_profile, follow_profile, get_author, check_follow_requests, create_entry, like_entry
from .views import edit_entry, add_comment, like_comment,view_entry_author, delete_entry, like_entry_api, add_comment_api, like_comment_api, get_entry_likes_api
from .views import get_entry_comments_api
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
    path('api/<str:username>/wiki/', user_wiki, name='user-wiki'),
    
    
    # Profile related API
    path('api/<str:username>/profile/edit/', edit_profile_api, name='edit_profile_api'),
    path('api/<str:username>/profile/', edit_profile_api, name='edit_profile_api'),

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
    path('api/entry/<uuid:entry_serial>/edit/', entry_detail_api, name='entry_detail_api'),
    path('api/entry/<uuid:entry_serial>/', entry_detail_api, name='entry_detail_api'),
    path('api/entry/<uuid:entry_serial>/like/', like_entry_api, name='like_entry_api'),
    path('api/entry/<uuid:entry_serial>/likes/', get_entry_likes_api, name='get_entry_likes_api'),
    path('api/entry/<uuid:entry_serial>/comments/', add_comment_api, name='add_comment_api'),
    path('api/entry/<uuid:entry_serial>/comments/view/', get_entry_comments_api, name='get_entry_comments_api'),
    path('api/comment/<int:comment_id>/like/', like_comment_api, name='like_comment_api'),
    
    
    # Author Related API 
    path('api/authors/', get_authors, name='get_authors'),
    path('api/author/<str:author_serial>/', get_author, name='get_author'),
    
    #Author Follow Requests API
    path('api/authors/<str:author_serial>/inbox/', get_local_follow_requests, name='get_follow_requests' ),
    
    # User Author URLS
    path('authors/', view_authors, name='view_authors'),
    path('authors/<str:author_serial>', view_external_profile, name="view_external_profile"),
    path('authors/<str:author_serial>/follow/', follow_profile, name="follow_profile"),
    
    
    #Author Follow Requests
    path('authors/<str:username>/inbox/', check_follow_requests, name='check_follow_requests' ),
    path('authors/<str:author_serial>/<str:request_id>/', process_follow_request, name='process_follow_request' ),
]
