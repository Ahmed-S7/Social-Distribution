from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PageViewSet, RemotePostReceiver

router = DefaultRouter()
router.register(r'pages', PageViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('receive-remote-post/', RemotePostReceiver.as_view(), name='receive-remote-post'),
]
