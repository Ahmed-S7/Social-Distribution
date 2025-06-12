from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Page, Like, RemotePost
from .serializers import PageSerializer, LikeSerializer, RemotePostSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

# Create your views here.

class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all().order_by('-updated')
    serializer_class = PageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        page = self.get_object()
        Like.objects.get_or_create(page=page, user=request.user)
        return Response({'status': 'liked'})

class RemotePostReceiver(APIView):
    def post(self, request):
        serializer = RemotePostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "received"})
        return Response(serializer.errors, status=400)
