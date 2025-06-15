from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PageViewSet, RemotePostReceiver
from .views import MyLoginView, user_wiki, register, get_authors
from django.contrib.auth.views import LogoutView

router = DefaultRouter()
router.register(r'pages', PageViewSet)

urlpatterns = [
    path('', MyLoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('login/create_account/', register, name='register'),
    path('<str:username>/wiki/', user_wiki, name='user-wiki'),
    path('s25-project-white/api/authors/', get_authors, name='get_authors'),
]
