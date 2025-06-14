from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Page, Like, RemotePost, Author
from .serializers import PageSerializer, LikeSerializer, RemotePostSerializer, AuthorSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User 
from django.shortcuts import redirect
from django.http import Http404
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.shortcuts import redirect
from .util import validUserName, saveNewAuthor
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

@login_required
def user_wiki(request, username):
    if request.user.username != username:
        raise Http404("You are not allowed to view this page.")

    return render(request, 'wiki.html') 

def register(request):
    """ creates a new user account """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password', "").strip()

        userIsValid = validUserName(username)
        
        if userIsValid and password == confirm_password: 
                
            if User.objects.filter(username=username).exists():
                
                return render(request, 'register.html', {'error': 'Username already taken.'})
            
            user = User.objects.create_user(username=username, password=password)
            newAuthor = saveNewAuthor(user, username) 
            return redirect('login') 
        
        else:
            errorList= []
            
            if password != confirm_password:
                errorList.append("Passwords do not match")

            if not userIsValid:
                errorList.append("Username must be under 150 characters")
                
                
            errors = " ".join(errorList)
            return render(request, 'register.html', {'error': errors})
            
    
    return render(request, 'register.html')

class MyLoginView(LoginView):
    def form_valid(self, form):
        login(self.request, form.get_user())
        username = self.request.user.username
        return redirect('user-wiki', username=username)