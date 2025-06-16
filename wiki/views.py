from django.db.models import Q
from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from .models import Page, Like, RemotePost, Author, FollowRequest, AuthorFollowing
from .serializers import PageSerializer, LikeSerializer, RemotePostSerializer, AuthorSerializer
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User 
from django.shortcuts import redirect
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import redirect
from django.contrib import messages
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
    if request.user.username != username or request.user.is_superuser:
        raise PermissionDenied("You are not allowed to view this page.")
   
    return render(request, 'wiki.html') 
    
  

def register(request):
    """ creates a new user account """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password', "").strip()

        userIsValid = validUserName(username)
        
        if userIsValid and password == confirm_password: 
            
            if User.objects.filter(username__iexact=username).exists():
                return render(request, 'register.html', {'error': 'Username already taken.'})
            
            user = User.objects.create_user(username=username, password=password)
            newAuthor = saveNewAuthor(user, username) 
            return redirect('wiki:login') 
        
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
        return redirect('wiki:user-wiki', username=username)
    
@api_view(['GET'])
def get_authors(request):
    """
    Gets the list of all authors on the application
    
        Example Usages:
    
        To get a list of all authors (no pagination):
    
        Use: "GET http://s25-project-white/api/authors/"
        
         - this returns Json in the following format: 
         
             {
                "type": "authors",      
                "authors":[
                    {
                        "type":"author",
                        "id":"http://nodeaaaa/api/authors/111",
                        "host":"http://nodeaaaa/api/",
                        "displayName":"Greg Johnson",
                        "github": "http://github.com/gjohnson",
                        "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
                        "web": "http://nodeaaaa/authors/greg"
                    },
                    {
                        // A second author object...
                    },
                    {
                        // A third author object...
                    }
                ]
            }
    """
  

    authors = Author.objects.all()
    serializer =AuthorSerializer(authors, many=True) #many=True specifies that the input is not just a single question
    return Response({"type": "authors",
                        "authors":serializer.data})    

@api_view(['GET'])
def get_author(request):
    """
    Gets the list of all authors on the application
    
        Example Usages:
    
        To get a list of all authors (no pagination):
    
        Use: "GET http://s25-project-white/api/authors/{}"
        
         - this returns Json in the following format: 
         
             {
                "type": "authors",      
                "authors":[
                    {
                        "type":"author",
                        "id":"http://nodeaaaa/api/authors/{serial}",
                        "host":"http://nodeaaaa/api/",
                        "displayName":"Greg Johnson",
                        "github": "http://github.com/gjohnson",
                        "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
                        "web": "http://nodeaaaa/authors/{SERIAL}"
                    },
                    {
                        // A second author object...
                    },
                    {
                        // A third author object...
                    }
                ]
            }
    """
  

    authors = Author.objects.all()
    serializer =AuthorSerializer(authors, many=True) #many=True specifies that the input is not just a single question
    return Response({"type": "authors",
                        "authors":serializer.data})
@login_required   
@require_GET 
def view_authors(request):
    current_user = request.user
   
    #######DEBUGGING PURPOSES##########
    #print(current_user)
    ###################################
    
    #retrieve all authors except for the current author
    authors = Author.objects.exclude(user=current_user)
    
    return render(request, 'authors.html', {'authors':authors, 'current_user':current_user})

@login_required       
def view_external_profile(request, author_serial):
    
    
    profile_viewing = Author.objects.get(serial=author_serial)
    if profile_viewing:
    
        return render(request, "external_profile.html", {"author": profile_viewing})
    else:
        return Http404("Profile Does Not Exist")
    
    
@login_required    
def view_following(request):
    
    pass
    
@login_required   
def follow_profile(request, author_serial):
    
    
    
    '''
    Creates and sends a follow request object to a user's inbox
    #TODO: send follow request with status "requesting" to corresponding account's inbox
    - do not allow duplicate follows
        - make views reflect this
    - allow recipient to accept follow request
        - update follow request status to accepted
    - allow recipient to reject follow request
        - update follow request status to rejected 
    - add follower to reciever
    - add followed user to sender
    - if both accounts follow each other:
        - add friends
    '''
    
    return HttpResponseRedirect('')#place holder
    pass
    
    
@api_view(['GET'])
def view_inbox(request):
    pass