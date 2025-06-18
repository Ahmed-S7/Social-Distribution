from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PageViewSet, RemotePostReceiver, entry_detail, profile_view
from .views import MyLoginView, user_wiki, register,follow_success_page,process_follow_request, get_authors, view_authors, view_external_profile, follow_profile, get_author, check_follow_requests, create_entry, like_entry
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
    path('profile/', profile_view, name='profile'),

    # Entry Related URLs
    path('entry/<uuid:entry_serial>/', entry_detail, name='entry_detail'),
    path('entry/<uuid:entry_serial>/like/', like_entry, name='like-entry'),
    path('create_entry/', create_entry, name='create_entry'),

    # Author Related API 
    path('api/authors/', get_authors, name='get_authors'),
    path('api/author/<str:author_serial>', get_author, name='get_author'),
    path('api/author/<str:author_serial>/', get_author, name='get_author'),
    
    # User Author URLS
    path('authors/', view_authors, name='view_authors'),
    path('authors/<str:author_serial>', view_external_profile, name="view_external_profile"),
    path('authors/<str:author_serial>/follow/', follow_profile, name="follow_profile"),
    #path('api/authors/<str:author_serial>/inbox/', check_remote_inbox, name='get_inbox' ),
    path('authors/<str:username>/inbox/', check_follow_requests, name='check_follow_requests' ),
    #path('authors/<str:author_serial>/request_sent', follow_success_page, name='successful_follow' ),
    path('authors/<str:author_serial>/<str:request_id>/', process_follow_request, name='process_follow_request' ),
]
