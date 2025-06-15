from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PageViewSet, RemotePostReceiver
from .views import MyLoginView, user_wiki, register, get_authors, view_authors, view_external_profile, follow_profile
from django.contrib.auth.views import LogoutView

app_name ='wiki'
router = DefaultRouter()
router.register(r'pages', PageViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', MyLoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('login/create_account/', register, name='register'),
    path('<str:username>/wiki/', user_wiki, name='user-wiki'),
    path('api/authors/', get_authors, name='get_authors'),
    path('authors/', view_authors, name='view_authors'),
    path('authors/<str:author_serial>', view_external_profile, name="view_external_profile"),
    path('authors/<str:author_serial>/follow/', follow_profile, name="follow_profile"),
]
