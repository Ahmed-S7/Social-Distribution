from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import viewsets, permissions, status
from .models import Page, Like, RemotePost, Author,AuthorFriend, InboxObjectType,RequestState, FollowRequest, AuthorFollowing, Entry, InboxItem, InboxItem
from .serializers import PageSerializer, LikeSerializer,AuthorFriendSerializer, AuthorFollowingSerializer, RemotePostSerializer,InboxItemSerializer,AuthorSerializer, FollowRequestSerializer, FollowRequestSerializer
from rest_framework.decorators import action, api_view
from django.views.decorators.http import require_http_methods
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
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from .util import validUserName, saveNewAuthor, get_author_id, is_valid_serial, get_logged_author
from urllib.parse import urlparse
import uuid
import requests
import json
from django.middleware.csrf import get_token
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
            
            #Save new author or raise an error
            newAuthor = saveNewAuthor(user, username, github, profileImage)
            if newAuthor:
                return redirect('wiki:login') 
            raise HttpResponseServerError("Unable to save profile")
        
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
        return HttpResponseRedirect("wiki:view_authors")
        
        
        
        
  
    
 
    
    
@login_required    
def view_following(request):
    
    pass
 

@login_required  
@require_http_methods(["GET", "POST"]) 
def follow_profile(request, author_serial):
    if request.user.is_staff or request.user.is_superuser:
        return HttpResponseServerError("Admins cannot perform author actions. Please use a regular account associated with an Author.")

    current_user = request.user
    print(f"Current user is: {current_user}\n")
    
    if get_logged_author(current_user):
        requesting_account = get_logged_author(current_user)

        parsed_serial = uuid.UUID(author_serial)

        try:
            requested_account = Author.objects.get(serial=parsed_serial)

            follow_request = FollowRequest(requester=requesting_account, requested_account=requested_account)
            follow_request.summary = str(follow_request)

            ########CHECKING OUTPUT###############
            print(f"{str(follow_request)}\n")
            print(f"REQUESTING AUTHOR: {requesting_account}\n")
            print(f"AUTHOR REQUESTED: {requested_account}\n")
            ###################################################

            inbox_url = f"{requested_account.get_web_url()}/inbox/"
            print(inbox_url)

            try:
                serialized_follow_request = FollowRequestSerializer(
                    follow_request, data={
                        "type":"follow",
                    },partial=True

                )

                if serialized_follow_request.is_valid():
                    print("Follow Request serializer is valid")

                    # Save follow request to DB
                    saved_follow_request = serialized_follow_request.save()

                    #make the inbox JSON content
                    inbox_content = serialized_follow_request.data
                    
                    
                    newInboxItem = InboxItem(
                        author=requested_account,
                        type=InboxObjectType.FOLLOW,
                        content=inbox_content
                    )

                    try:
                        newInboxItem.save()
                        print("Inbox item successfully saved")
                    
                    #Exceptions and structure adjusted using copilot: https://www.bing.com/search?pglt=427&q=copilot&cvid=882b9688f1804581bd4975fbe80acc49&gs_lcrp=EgRlZGdlKgYIABBFGDkyBggAEEUYOTIGCAEQABhAMgYIAhAAGEAyBggDEAAYQDIGCAQQABhAMgYIBRAAGEAyBggGEAAYQDIGCAcQABhAMgYICBAAGEDSAQc5MDJqMGoxqAIAsAIA&FORM=ANNTA1&PC=EDGEDB, "[Adjust the structure of these error messages]", June, 2025
                    except Exception as e:
                        saved_follow_request.delete()  # Rollback follow request
                        return HttpResponseServerError(f"Failed to save Inbox Item: {e}")

                else:
                    return HttpResponseServerError(f"FollowRequest serializer errors: {serialized_follow_request.errors}")

            except Exception as e:
                return HttpResponseServerError(f"Failed to validate follow request and inbox item: {e}")

        except Exception as e:
            return HttpResponseServerError(f"Failed to create follow request: {e}")

    return redirect('wiki:successful_follow', author_serial=author_serial)

           

@login_required
def follow_success_page(request, author_serial):
    
    if request.user.is_staff or request.user.is_superuser:
        return HttpResponseServerError("Admins cannot perform author actions. Please user a regular account associated with an Author.")
    requestedAuthor = Author.objects.get(serial=author_serial)
    
    return render(request,"follow_success.html", {'author':requestedAuthor})


@login_required
def check_follow_requests(request, username):
    
        print(username)
        if request.user.is_staff or request.user.is_superuser:
            return HttpResponseServerError("Admins cannot perform author actions. Please user a regular account associated with an Author.")

        requestedAuthor = Author.objects.get(user=request.user)
        
        incoming_follow_requests =[FollowRequest.objects.filter(requested_account=requestedAuthor, state=RequestState.REQUESTING).first()]
       
        if not incoming_follow_requests:
            incoming_follow_requests = []

        return render(request,'follow_requests.html', {'author':requestedAuthor, "follow_requests": incoming_follow_requests})

@login_required
def process_follow_request(request, author_serial, request_id):
    
    if request.user.is_staff or request.user.is_superuser:
        return HttpResponseServerError("Admins cannot perform author actions. Please user a regular account associated with an Author.")
    requestedAuthor = Author.objects.get(serial=author_serial)
    
    choice = request.POST.get("action")
    
    if choice.lower() == "accept":
        
        #if follow request gets accepted, 
        follow_request = FollowRequest.objects.filter(id=request_id).first()
    
        try:
            follower = follow_request.requester
                
        except follower.DoesNotExist:
            return Http404("Follow request was not found between you and this author")
        
        #set the follow  request state to accepted
        follow_request.set_request_state(RequestState.ACCEPTED)
        
        #create a following from requester to requested
        new_following = AuthorFollowing(follower=follower, following=requestedAuthor)
        new_following_serializer = AuthorFollowingSerializer(new_following, data={
            "follower":new_following.follower.id,
            "following":new_following.following.id,
        }, partial=True)
        
        print(new_following_serializer)
        if new_following_serializer.is_valid():
            try:
                new_following_serializer.save()
            except Exception as e:
                incoming_follow_requests = FollowRequest.objects.filter(requested_account=requestedAuthor, state=RequestState.REQUESTING)    
                return render(request,'follow_requests.html', {'author':requestedAuthor, "follow_requests": incoming_follow_requests})
               # return HttpResponseServerError("Unable to accept follow request, make sure this author does not already follow you.")

        else:
            
            return HttpResponseServerError(f"Unable to follow Author {new_following.following.displayName}.")
            
        # check if there is now a mutual following
        if follower.is_following(requestedAuthor) and requestedAuthor.is_following(follower):

            #if there is, add these two users as friends using the author friends object
            new_friendship = AuthorFriend(friending=requestedAuthor, friended=follower)
            
            friendship_serializer = AuthorFriendSerializer(new_friendship, data={
                "friending":new_friendship.friending.id,
                "friended":new_friendship.friended.id,
            },partial=True) 
            
            if friendship_serializer.is_valid():
                
                friendship_serializer.save()  
                
            else:
                
                return HttpResponseServerError(f"Unable to friend Author {new_following.following.displayName}")
                
                    

          
            
    else:
        #if follow request is denied,
         follow_request = FollowRequest.objects.filter(id=request_id).first()
    
         try:
            follower = follow_request.requester
                
         except follower.DoesNotExist:
            return Http404("Follow request was not found between you and this author")
        
         #Set the request state to rejected 
         follow_request.set_request_state(RequestState.REJECTED)
         
         #SOFT DELETE the follow request so the requester may request again
         follow_request.is_deleted=True
   
    
    
    incoming_follow_requests = FollowRequest.objects.filter(requested_account=requestedAuthor, state=RequestState.REQUESTING)    
    return render(request,'follow_requests.html', {'author':requestedAuthor, "follow_requests": incoming_follow_requests})
    
    
   
    
    
    
    
    

@api_view(['GET'])
def check_remote_inbox(request):
    pass

@login_required
def profile_view(request):
    """
    View the profile of the currently logged in user.
    """
    try:
        author = Author.objects.get(user=request.user)
    except Author.DoesNotExist:
        return HttpResponse("Author profile does not exist.")
    entries = Entry.objects.filter(author=request.user).order_by('-created_at')    # displays entries from newest first
    return render(request, 'profile.html', {'author': author, 'entries': entries})

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
        if title and content:
            entry = Entry.objects.create(author=request.user, title=title, content=content)
            return redirect('wiki:entry_detail', entry_serial=entry.serial)
        else:
            return HttpResponse("Both title and content are required.")
    # GET: Show form to create entry
    return render(request, 'create_entry.html')

@login_required
def entry_detail(request, entry_serial):
    entry = get_object_or_404(Entry, serial=entry_serial)
    return render(request, 'entry_detail.html', {'entry': entry})




































'''IGNORE FOR NOW, FOR API IT MAY BECOME USEFUL
                    
                    try:
                        response = requests.post(
                            inbox_url,
                            json=serial_follow_data,
                            headers={'Content-Type': 'application/json'}
                        )

                        if response.status_code == 201:
                            print("SUCCEEDED TO POST THE REQUEST")

                            # Save to our local inbox
                            newInboxItem = InboxItem(
                                author=requested_account,
                                type=InboxObjectType.FOLLOW,
                                content=serial_follow_data
                            )
                            newInboxItem.save()
                            serialized_follow_request.save()

                            print("sent the follow request to recipient inbox")
                        else:
                            print(f"Failed with status {response.status_code}")
                            print(f"Response: {response.text}")
                            return HttpResponseServerError("Remote inbox rejected the follow request.")

                    except Exception as e:
                        print(f"Failed to send request: {e}")
                        return HttpResponseServerError(f"Failed to send request: {e}")

                
    
            except Exception as e:
         
                return HttpResponseServerError(f"Unexpected error occurred: {e}")
        except Exception as e:
            
                return HttpResponseServerError(f"Unexpected error occurred: {e}")
            
    return redirect("wiki:successful_follow", author_serial=author_serial)
    #return redirect('wiki:successful_follow', author_serial=author_serial)'''
