from django.db.models import Q
from django.shortcuts import render, redirect
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
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseServerError
from django.urls import reverse
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import redirect
from django.contrib import messages
from .util import validUserName, saveNewAuthor, get_author_id, is_valid_serial, get_logged_author
from urllib.parse import urlparse
import uuid
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
        github = request.POST.get('github') or None
        profileImage = request.POST.get('profileImage') or None

        userIsValid = validUserName(username)
        
        if userIsValid and password == confirm_password: 
            
            if User.objects.filter(username__iexact=username).exists():
                return render(request, 'register.html', {'error': 'Username already taken.'})
            
            user = User.objects.create_user(username=username, password=password)
            newAuthor = saveNewAuthor(user, username, github, profileImage)
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









@login_required
@api_view(['GET'])
def get_author(request, author_serial):
    """
    Get a specific author in the application
    
        Example Usages:
    
        To retrieve the author:
    
        Use: "GET http://s25-project-white/api/author/{serial}"
        
         - this returns Json in the following format: 
         
                {
                    "type":"author",
                    "id":"http://nodeaaaa/api/authors/{serial}",
                    "host":"http://nodeaaaa/api/",
                    "displayName":"Greg Johnson",
                    "github": "http://github.com/gjohnson",
                    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
                    "web": "http://nodeaaaa/authors/{SERIAL}"
                }
                  
    """
    

    id = get_author_id(request)
    
    if is_valid_serial(id):
           
        if Author.objects.filter(serial=id).exists():
                
            author = Author.objects.get(serial=id)
            
            #####FOR DEBUG#######
            #print(author)
            #####################      
            
            serializer = AuthorSerializer()
        
            serializer =AuthorSerializer(author)
        return Response(serializer.data)




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

@require_GET
@login_required       
def view_external_profile(request, author_serial):
    
    if  Author.objects.filter(serial=author_serial).exists():
        profile_viewing = Author.objects.get(serial=author_serial)     
        return render(request, "external_profile.html", {"author": profile_viewing})
    else:
        print("profile DNE")
        return redirect("wiki:view_authors")
        
        
        
        
  
    
 
    
    
@login_required    
def view_following(request):
    
    pass
 
 
 
    
@login_required  
@require_POST 
def follow_profile(request, author_serial):
    
    current_user = request.user
    
    if get_logged_author(current_user):
        requesting_account = get_logged_author(current_user)
    
        parsed_serial  = uuid.UUID(author_serial)
    
        try:
            
            Author.objects.get(serial=parsed_serial)
            
            requested_account = Author.objects.get(serial=parsed_serial)

            follow_request = FollowRequest(requester=requesting_account, requested_account=requested_account)
            
    
            follow_request.summary=(str(follow_request))
            ########CHECKING OUTPUT###############
            print(f"{str(follow_request)}\n")
            
            print(f"REQUESTING AUTHOR: {requesting_account}\n")
            
            print(f"AUTHOR REQUESTED: {requested_account}\n")
            ###################################################
            
            #TODO: serialize the follow request, save it, send it to the requested author's inbox
            
            
            
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
        
        except Exception as e:
            return HttpResponseServerError(f"Failed to created follow request: {e}")
        
        return redirect("wiki:view_external_profile", author_serial=author_serial)#place holder
   
    raise Http404("NO USER IS CURRENTLY LOGGED IN, OR WE WERE UNABLE TO LOCATE YOUR PROFILE")
    
   
@login_required
def check_inbox(request):
    
    pass 
    
@api_view(['GET'])
def view_inbox(request):
    pass

@login_required
def profile_view(request):
    """
    View the profile of the currently logged in user.
    """
    try:
        author = Author.objects.get(user=request.user)
    except Author.DoesNotExist:
        raise Http404("Author profile does not exist.")

    return render(request, 'profile.html', {'author': author})

@login_required
def create_entry(request):
    """
    Create a new wiki entry.
    """
    ####### FOR CREATING A NEW ENTRY ######
    if request.method == 'POST':
        # Example: get data from POST and save your entry
        title = request.POST.get('title')
        content = request.POST.get('content')
        # TODO: validate + save to database

        # TEMPORARY: Just return confirmation
        return HttpResponse(f"Entry '{title}' created successfully!")
    
    else:
        # GET: Show form to create entry
        return render(request, 'create_entry.html')

