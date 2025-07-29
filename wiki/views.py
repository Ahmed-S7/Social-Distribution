import mimetypes
from django.db.models import Q
from django.core.paginator import Paginator
from requests.auth import HTTPBasicAuth
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import viewsets, permissions, status
from .models import NodeConnectionCredentials, Page,InboxObjectType,Like,RemoteNode, RemotePost, Author, AuthorFriend, InboxObjectType,RequestState, FollowRequest, AuthorFollowing, Entry, InboxItem, InboxItem, Comment, CommentLike
from .serializers import FollowRequestReadingSerializer,PageSerializer, LikeSerializer, LikeSummarySerializer, AuthorFriendSerializer, AuthorFollowingSerializer, RemotePostSerializer,InboxItemSerializer,AuthorSerializer, FollowRequestSerializer, FollowRequestSerializer, EntrySerializer, CommentSummarySerializer, CommentLikeSummarySerializer
import urllib.parse
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from django.views.decorators.http import require_http_methods
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User 
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseServerError
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth import login, authenticate,get_user_model
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from .util import  author_exists, AUTHTOKEN, encoded_fqid, get_serial, get_host_and_scheme, validUserName, saveNewAuthor, remote_followers_fetched, remote_author_fetched, decoded_fqid, send_comment_to_entry_author, send_comment_like_to_comment_author, send_entry_like_to_entry_author
from urllib.parse import urlparse, unquote
import requests
import uuid
import json
import base64
import markdown
from django.utils.safestring import mark_safe
from django.middleware.csrf import get_token
from .gethub import create_entries
from django.core.paginator import Paginator
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


@api_view(['GET'])
def user_wiki_api(request, username):
    current_author = get_object_or_404(Author, user=request.user)
    if request.user.username != username:
        return redirect("wiki:login")
    
    # Followed
    followed_ids = AuthorFollowing.objects.filter(
        follower=current_author
    ).values_list('following', flat=True)

    # Friends
    friend_pairs = AuthorFriend.objects.filter(
        Q(friending=current_author) | Q(friended=current_author)
    ).values_list('friending', 'friended')

    friend_ids = set()
    for friending_id, friended_id in friend_pairs:
        if friending_id != current_author.id:
            friend_ids.add(friending_id)
        if friended_id != current_author.id:
            friend_ids.add(friended_id)

    entries = Entry.objects.filter(
        ~Q(visibility='DELETED') & (
            Q(visibility='PUBLIC') |
            Q(author=current_author) |
            Q(visibility='FRIENDS', author__id__in=friend_ids) |
            Q(visibility='UNLISTED', author__id__in=followed_ids)
        )
    ).order_by('-created_at')
    serialized_entries = []
    for entry in entries:
        entry_data = {
            "title": entry.title,
            "content": entry.content,
            "author": entry.author.displayName,
            "visibility": entry.visibility,
            "created_at": entry.created_at.isoformat(),  # Use ISO 8601 format for timestamp
            "serial": str(entry.serial),
            "contentType": entry.contentType,
        }
        serialized_entries.append(entry_data)

    # Return the entries as a JSON response
    return Response(serialized_entries)
    
@login_required
def user_wiki(request, username):
    '''Process all of the logic pertaining to a given user's wiki page'''
    
    if request.user.username != username or request.user.is_superuser:
        raise PermissionDenied("You are not allowed to view this page.")
    current_author = get_object_or_404(Author, user=request.user)

    #Add Github Entries to feed
    create_entries(current_author)

    # Followed
    followed_ids = AuthorFollowing.objects.filter(
        follower=current_author
    ).values_list('following', flat=True)

    # Friends
    friend_pairs = AuthorFriend.objects.filter(
        Q(friending=current_author) | Q(friended=current_author)
    ).values_list('friending', 'friended')

    friend_ids = set()
    for friending_id, friended_id in friend_pairs:
        if friending_id != current_author.id:
            friend_ids.add(friending_id)
        if friended_id != current_author.id:
            friend_ids.add(friended_id)

    entries = Entry.objects.filter(
        ~Q(visibility='DELETED') & (
            Q(visibility='PUBLIC') |
            Q(author=current_author) |
            Q(visibility='FRIENDS', author__id__in=friend_ids) |
            Q(visibility='UNLISTED', author__id__in=followed_ids)
        )
    ).order_by('-created_at')
    #return render(request, 'wiki.html', {'entries': entries})
    rendered_entries = []
    for entry in entries:
        rendered = (
            mark_safe(markdown.markdown(entry.content))
            if entry.contentType == "text/markdown"
            else entry.content
        )
        rendered_entries.append((entry, rendered))

    return render(request, 'wiki.html', {'entries': rendered_entries})


@require_POST
@login_required
def like_entry(request, entry_serial):
    '''Handles the logic surrounding liking an entry

       Args:
            - Request: HTTP request information
            - Entry_serial: The serial id of the entry 
    
        Returns: HTTP404 if any objects are not found, or simply redirect to the user's wiki stream

    '''
    #print(request.path)
    #print(request.POST.get("liked_from_post"))
    
    entry = get_object_or_404(Entry, serial=entry_serial)
    author = get_object_or_404(Author, user=request.user)
    liked_author = get_object_or_404(Author, id=entry.author.id) #author that liked the entry
    like, created = Like.objects.get_or_create(entry=entry, user=author)

    if created:
        # Send like to entry author's inbox if remote
        send_entry_like_to_entry_author(like, request)

    if not created:
        like.delete()  # Toggle like off

    #Redirect to the entry's author's page if the entry was liked from their page  
    if request.POST.get("liked_from_profile") == "true":
       
        return redirect('wiki:view_external_profile', author_serial=liked_author.serial)
    
    #Redirect to the entry's details's page if the entry was liked from its details  
    if request.POST.get("liked_from_details") == "true":

        return redirect('wiki:entry_detail', author_serial=entry.author.serial, entry_serial=entry.serial)
    
    #regular stream entry like
    return redirect('wiki:user-wiki', username=request.user.username)
   

def register(request):
    """ creates a new user account """
    if request.method == 'POST':
        
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password', "").strip()
        github = request.POST.get('github') or None
        profileImage = request.POST.get('profileImage') or None

        userIsValid = validUserName(username)
        
        #TODO: add password validation for pass length when connecting with other groups, leave as is for now
        if userIsValid and password == confirm_password: 
            
            if User.objects.filter(username__iexact=username).exists():
                return render(request, 'register.html', {'error': 'Username already taken.'})
            
            user = User.objects.create_user(username=username, password=password, is_active=False)
            
            #Save new author or raise an error
            newAuthor = saveNewAuthor(request, user, username, github, profileImage, is_local=True)
            if newAuthor:
                return redirect('wiki:login') 
            return HttpResponseServerError("Unable to save profile")
        
        else:
            errorList= []
            
            if password != confirm_password:
                errorList.append("Passwords do not match")

            if not userIsValid and len(username) >= 150:
                errorList.append("Username must be under 150 characters")
            
            if  not userIsValid and " " in username:
               errorList.append("Username cannot contain spaces")
            
            errors = " ".join(errorList)
            return render(request, 'register.html', {'error': errors})
            
    return render(request, 'register.html')

@api_view(['POST'])
def register_api(request):
    
    '''Allows users to register through POST requests'''
    username = request.data.get('username')
    password = request.data.get('password')
    confirm_password = request.data.get('confirm_password', "").strip()
    github = request.data.get('github') or None

    if not username or not password or not confirm_password:
        return Response({"detail": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

    if password != confirm_password:
        return Response({"detail": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

    if not validUserName(username):
        return Response({"detail": "Invalid username"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username__iexact=username).exists():
        return Response({"detail": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password, is_active=False)

    author = saveNewAuthor(request, user, username, github, profileImage=None)
    if not author:
        return Response({"detail": "Failed to create author"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"detail": "Registration successful, pending admin approval"}, status=status.HTTP_201_CREATED)

class MyLoginView(LoginView):
    def form_valid(self, form):
        login(self.request, form.get_user())
        user = form.get_user()
        author = Author.objects.filter(user=user).first()
        if not author:
            return redirect("wiki:register")
        else:
            username = author.displayName
        #Populate the db with users from other valid (active) nodes
        active_nodes = RemoteNode.objects.filter(is_active=True)
        print("ACTIVE REMOTE NODES:", active_nodes,'\n')
        remote_authors_lists = []
        for node in active_nodes:
                        
            normalized_url = node.url.rstrip("/")
            try:
                
                #get the response from pulling another node's authors
                node_authors_pull_attempt = requests.get(normalized_url+"/api/authors/", auth=AUTHTOKEN)
                
                #If the request was successful (got a 200) we can move on to storing the JSON and converting them into author objects
                if node_authors_pull_attempt.status_code == 200:
                    print(f"successful pull of authors from {node}, status: {node_authors_pull_attempt.status_code}")
                    
                    #retrieve any valid JSON if the GET request was successful, store them in a list of the authors to convert to author objects
                    try:
                        node_authors = node_authors_pull_attempt.json()
                    except Exception as e:
                        raise e
                    
                    #add the json list of the authors to the complete list of authors
                    remote_authors_lists.append(node_authors['authors']) #->[[{node1 authors}], [[{node2 authors}]]
                    
                print("\n")
                
            except Exception as e:
                raise e
            
        all_remote_authors = []
        for remote_author_list in remote_authors_lists:
            for author_json in remote_author_list:
                all_remote_authors.append(author_json)#contains a json of all of the remote authors 
             
        for remote_author in all_remote_authors:
            if remote_author.get("id"):
                author_id = remote_author.get("id")
                try:
                    
                    if author_exists(author_id):
                        print("EXISTING AUTHOR FOUND")
                        existing_author = Author.objects.get(id=author_id)
                        account_serialized = AuthorSerializer(existing_author, data=remote_author, partial=True)
                    else:
                        #SERIALIZE AND SAVE IF THEIR DATA IS VALID
                        print("NEW AUTHOR FOUND")
                        account_serialized = AuthorSerializer(data=remote_author)    
                        
                    #IF THEIR DATA IS INVALID, INFORM THE REQUESTER
                    if not account_serialized.is_valid():
                            print("NEW AUTHOR OBJECT STRUCTURE INVALID")
                            print(account_serialized.errors)
                            
               
                           
                    #IF THEIR DATA IS INVALID, INFORM THE REQUESTER
                    else:
                        
                        if not author_exists(author_id):
                            print("AUTHOR OBJECT VALIDATED, SAVING TO DB")
                        else:
                            print("EXISTING AUTHOR UPDATED, SAVING TO DB")
                        #IF THEY DO NOT ALREADY EXIST, SAVE THEM TO THE NODE, SHOULD UPDATE EXIS
                        profile = account_serialized.save()
                        profile.is_local=False
                        profile.save()
                        print(f"AUTHOR {profile} SAVED TO DATABASE")
        
                        
                except Exception as e:
                    print(e)     
            
        # redirects to the login if the redirection to the wiki page fails
        try:
            return redirect('wiki:user-wiki', username=username)
        except Exception as e:
            return redirect("wiki:login")
        
    def form_invalid(self, form):
        username = self.request.POST.get('username')
        password = self.request.POST.get('password')

        User = get_user_model()
        try:
            user = User.objects.get(username=username)
            if user.check_password(password) and not user.is_active:
                form.add_error(None, "Your account is pending admin approval. Please wait for confirmation before logging in.")
        except User.DoesNotExist:
            pass  # normal invalid credentials case

        return super().form_invalid(form)
@csrf_exempt   
@api_view(['POST'])
def login_api(request):
    username = request.data.get('username')
    password = request.data.get('password')
    if not username or not password:
        return Response({"detail": "Missing username or password"}, status=400)
    User = get_user_model()
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({"detail": "Invalid credentials"}, status=403)
    if not user.check_password(password):
        return Response({"detail": "Invalid credentials"}, status=403)
    if not user.is_active:
        return Response({"detail": "pending admin approval"}, status=403)
    return Response({"detail": "Login successful"}, status=200)

@api_view(['GET'])
@authentication_classes([]) #DJANGO was causing most of our problems. the 403 was caused by django enforcing a user object to exist for every request that gets sent
def get_authors(request):
    """
    Gets the list of all authors on the application
    
    Use: "GET /api/authors/"
        
    This returns Json in the following format: 
         
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
    # Authentication disabled for browser testing
    # auth_header = request.META.get('HTTP_AUTHORIZATION')
    # 
    # #need to have auth in request to connect with us
    # if not auth_header:
    #     return Response({"unauthorized": "please include authentication with your requests"}, status=status.HTTP_401_UNAUTHORIZED)
    # print(f"AUTH HEADER FOUND.\nENCODED AUTH HEADER: {'*' * len(auth_header)}")
    # 
    # 
    # #If the auth header has basic auth token in it
    # if not auth_header.startswith("Basic"):
    #     return Response({"Poorly formatted auth": "please include BASIC authentication with your requests to access the inbox."}, status=status.HTTP_401_UNAUTHORIZED)
    # print(f"AUTH HEADER STARTS WITH BASIC: {auth_header.startswith('Basic')}")
    # 
    # #Gets the user and pass using basic auth
    # username, password = decoded_auth_token(auth_header)
    # 
    # #make sure the auth is properly formatted
    # if not (username and password):
    #     print("COULD NOT PARSE USER AND PASS FROM POORLY FORMATTED AUTH.")
    #     return Response({"ERROR" :"Poorly formed authentication header. please send a valid auth token so we can verify your access"}, status = status.HTTP_400_BAD_REQUEST)
    # 
    # if not node_valid(username, password):
    #     return Response({"Node Unauthorized": "This node does not match the credentials of any validated remote nodes","detail":"please check your authorization details (case-sensitive)"}, status=status.HTTP_401_UNAUTHORIZED)
    # 
    # print("AUTHENTICATION COMPLETE.")
    # print(f"{username} may now access the node.")
    authors = Author.objects.all()
    
     # Get pagination parameters
    page_number = request.GET.get('page', 1)
    page_size = min(int(request.GET.get('size', 50)), 50)  # Cap at 50 items per page
    
    # Paginate the results
    paginator = Paginator(authors, page_size)
    
    try:
        page_obj = paginator.page(page_number)
    except (ValueError, TypeError):
        return Response({"error": "Invalid page number"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response({"error": "Page not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Serialize the authors
    authors_data = []
    for author in page_obj:
        serializer = AuthorSerializer(author, context={'request': request})
        authors_data.append(serializer.data)
    


    # Build response
    host = request.build_absolute_uri('/').rstrip('/')
    response_data = {
        "page_number": int(page_number),
        "size": page_size,
        "count": paginator.count,
        "type": "authors",  
        "authors": authors_data
    }
    
    # Add pagination URLs if needed
    if page_obj.has_next():
        response_data["next_url"] = f"?page={page_obj.next_page_number()}&size={page_size}"
    if page_obj.has_previous():
        response_data["previous_url"] = f"?page={page_obj.previous_page_number()}&size={page_size}"
    
    if authors_data:     
        return Response(response_data, status=status.HTTP_200_OK)  
    else:
        return Response({"type":"authors", "authors": []}, status=status.HTTP_200_OK)



@api_view(['GET', "PUT"])
def get_or_edit_author_api(request, author_serial):
    """
    Get a specific author in the application
    

    Use: "GET /api/authors/{author_serial}"
    
    Args: 
    
        - request: HTTP request information
        
        - author_serial: the serial id of the author in the get request
        
    This returns:
    
        - Json in the following format (given the author was found): 
   
                {
                    "type":"author",
                    "id":"http://nodeaaaa/api/authors/{serial}",
                    "host":"http://nodeaaaa/api/",
                    "displayName":"Greg Johnson",
                    "github": "http://github.com/gjohnson",
                    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
                    "web": "http://nodeaaaa/authors/{SERIAL}"
                }  
                
        - returns error details if they arise     
        
        
    Use: "PUT /api/authors/{author_serial}"
    
    Args: 
    
        - request: HTTP request information
        
        - author_serial: the serial id of the author in the get request
        
    This returns:
    
        - Json in the following format (given the author was found and the information was validated and updated): 
   
                {
                    "type":"author",
                    "id":"http://nodeaaaa/api/authors/{serial}",
                    "host":"http://nodeaaaa/api/",
                    "displayName":"Greg Johnson",
                    "github": "http://github.com/gjohnson",
                    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
                    "web": "http://nodeaaaa/authors/{SERIAL}"
                }  
                
        - returns error details if they arise    
    
    """
    if 'http' in author_serial:
        author_serial = author_serial.split('/')[-1]
    author = get_object_or_404(Author, serial=author_serial)
    
    if request.method=="GET":
        # CHANGED FOR TESTING
        
        serializer =AuthorSerializer(author)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # PUT
    #If the user is local, make sure they're logged in 
    if request.user.is_authenticated and author.user == request.user :
  
            updated_author_serializer = AuthorSerializer(author, data=request.data, partial=True)
            
            if updated_author_serializer.is_valid(raise_exception=True):

                try:
                    updated_author_serializer.save()
                except Exception as e:
                    return Response({"Failed to update author info": e}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                return Response(updated_author_serializer.data, status=status.HTTP_200_OK)
            
            return Response(updated_author_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    else:
        return Response({"Failed to update author info":f"You must log in as '{author}' to update this information"}, status=status.HTTP_401_UNAUTHORIZED)

@login_required   
@require_GET 
def view_local_authors(request):
    current_user = request.user
    
    #retrieve all authors except for the current author
    authors = Author.objects.filter(user__is_active=True).exclude(user=current_user)
    return render(request, 'authors.html', {'authors':authors, 'current_user':current_user})

@login_required 
@require_GET  
def view_external_profile(request, author_serial):
    '''Presents a view of a profile other than the one that is currently logged
    - shows the current user whether they are following, are friends with or can follow the current user
    '''
    profile_viewing = Author.objects.filter(serial=author_serial).first()
    if not profile_viewing.user.is_active:
        messages.error(request, "This user is not yet approved by admin.")
        return redirect("wiki:view_local_authors")
    if not profile_viewing:
        return redirect("wiki:view_local_authors")

    if profile_viewing:
        logged_in = request.user.is_authenticated
        logged_in_author = Author.objects.filter(user=request.user).first() if logged_in else None
        #NECESSARY FIELDS FOR PROFILE DISPLAY
        is_following = logged_in_author.is_following(profile_viewing)if logged_in_author else False
        followers = profile_viewing.followers.all()#stores all of the followers a given author has
        following = profile_viewing.following.all()#stores all of the followers a given author has
        all_entries = profile_viewing.get_all_entries()#stores all of the user's entries
        is_currently_requesting = logged_in_author.is_already_requesting(profile_viewing)if logged_in_author else False
        is_a_friend = logged_in_author.is_friends_with(profile_viewing)if logged_in_author else False
        friends_a = profile_viewing.friend_a.all()if logged_in_author else Author.objects.none()
        friends_b = profile_viewing.friend_b.all()if logged_in_author else Author.objects.none()
        total_friends = (friends_a | friends_b)
        is_local =  profile_viewing.is_local
        
        # VISUAL REPRESENTATION TEST
        '''
        print("Entries:", all_entries or None)
        print("followers:", followers or None)
        print("follower count:", len(followers) or None)
        print("following:", following or None)
        print(f"Accounts {profile_viewing} is following:", len(following) or None)
        print(f"{logged_in_author} is friends with this account:", is_a_friend)
        print(f"{logged_in_author} is following this account:", is_following)
        print(f"{profile_viewing} friend count:", len(total_friends) or None)
        '''
        
        # Followed
        followed_ids = AuthorFollowing.objects.filter(
            following=profile_viewing
        ).values_list('follower', flat=True)
        
        # Friends
        friend_pairs = AuthorFriend.objects.filter(
            Q(friending=logged_in_author) | Q(friended=logged_in_author)
        ).values_list('friending', 'friended')

        friend_ids = set()
        for friending_id, friended_id in friend_pairs:
            if friending_id != logged_in_author.id:
                friend_ids.add(friending_id)
            if friended_id != logged_in_author.id:
                friend_ids.add(friended_id)
     
                 
        #Entries the current user is permitted to view
        all_entries = Entry.objects.filter(
        author=profile_viewing
        ).filter(
            Q(visibility='PUBLIC') |
            (Q(visibility='FRIENDS') & Q(author__id__in=friend_ids)) |
            (Q(visibility='UNLISTED') & Q(author__id__in=followed_ids))
        ).order_by('-created_at')
        
        #store existing follow request if it exists
        try:
            if logged_in_author:
                current_request = FollowRequest.objects.get(requester=logged_in_author.id, requested_account=profile_viewing.id)
                current_request_id = current_request.id
            else:
                current_request_id = None
        
        except FollowRequest.DoesNotExist or not logged_in_author:
            current_request_id = None
        
    
        #for logged in users only:
        if logged_in_author:
            
            #store existing following if it exists 
            following_id = logged_in_author.get_following_id_with(profile_viewing)
            
            #store existing friendship if it exists 
            friendship_id = logged_in_author.get_friendship_id_with(profile_viewing)
        
        else:
            
            following_id,friendship_id = None, None
            
            
        #CHECK VALUES
        '''
        print("Following ID is:",following_id)
        print("Friendship ID is:",friendship_id)
        print("The current request is:", current_request_id) 
        print("List of User's Entries:", all_entries)
        '''
        rendered_entries = []
        for entry in all_entries:
         rendered = (
            mark_safe(markdown.markdown(entry.content))
            if entry.contentType == "text/markdown"
            else entry.content
         )
         rendered_entries.append((entry, rendered)) 
        
        return render(request, "external_profile.html", 
                      {
                       'is_local': is_local,
                       'author': profile_viewing,
                       'entries': rendered_entries,
                       "followers": followers,
                       "follower_count": len(followers),
                       "friend_count": len(total_friends),
                       "is_a_friend": is_a_friend,
                       "is_following": is_following,
                       "following_count": len(following),
                       "entry_count": len(all_entries),
                       "is_a_friend": is_a_friend,
                       "is_currently_requesting":is_currently_requesting,
                       "request_id": current_request_id,
                       "follow_id": following_id,
                       "friendship_id":friendship_id ,
                       }
                      )

    else:
        return HttpResponseRedirect("wiki:view_local_authors")

        
   
    
    
    
          
@login_required
def cancel_follow_request(request, author_serial, request_id):
    '''Cancels an active follow request that a user has sent to another author
    
        ARGS:
            - author_serial: the requested author's serial 
            - request_id: the id of the sent follow request
            - request: the request details
            
        RETURNS:
            - a redirection to the requested author's page
    
    '''
    
    requested_author_serial = author_serial
    #print(request_id)
    try:
        #retrieve the current follow request
        active_request = FollowRequest.objects.get(id=request_id)
        #print("The request being changed is:", active_request)
    except FollowRequest.DoesNotExist:
        #print(f"{request_id} is not a valid existing follow request id")
        return redirect(reverse("wiki:view_external_profile", kwargs={"author_serial": requested_author_serial})) 

    
    #set the follow request as deleted
    try:
        active_request.delete()
    except Exception as e:
        print(e)
        return HttpResponseServerError(f"Could Not Cancel Your Follow Request, Please Try Again.")
    

    #redirect to the requested user's page 
    return redirect(reverse("wiki:view_external_profile", kwargs={"author_serial": requested_author_serial}))      
@login_required


def unfollow_profile(request, author_serial, following_id):
    '''Cancels an active follow request that a user has sent to another author
    
        ARGS:
            - author_serial: the requested author's serial 
            - request_id: the id of the sent follow request
            - request: the hhtp request details
            
        RETURNS:
            - a redirection to the requested author's page
    
    '''
    
    followed_author_serial = author_serial
    
    try:
        #retrieve the current follow request
        followed_author = Author.objects.get(serial=followed_author_serial)
        current_author = Author.objects.get(user=request.user)
        #print("The request being changed is:", active_request)
    except Author.DoesNotExist:
        #print(f"{following_id} is not a valid existing following id")
        return redirect(reverse("wiki:view_local_authors"))
        
    
    try:
        #retrieve the current follow request
        active_following = AuthorFollowing.objects.get(id=following_id)
    
        #retrieve the accepted follow request
        active_request=FollowRequest.objects.get(requester = current_author.id, requested_account=followed_author.id)
    
    except AuthorFollowing.DoesNotExist or FollowRequest.DoesNotExist:
        return redirect(reverse("wiki:view_external_profile", kwargs={"author_serial": followed_author_serial}))     
     
    # ID of friendship object or None
    active_friendship_id = current_author.get_friendship_id_with(followed_author)
    
    
    '''#VISUAL REPRESENTATION TEST
    print("Current Author is:",current_author,followed_author)
    print("Followed Author is:", followed_author)
    print("The Following being deleted is:", active_following)   
    print("The active request being deleted is:", active_request)   
    '''
    
    #set the follow request as deleted
    try:
        active_request.delete()
        active_following.delete()
        #IMPORTANT: DO NOT CHANGE AS THIS CHECK IS HERE IN CASE A USER IS FOLLOWING A USER AND IS FRIENDS WITH THEM
        # -alternatively, if the user is only following them, nothing happens to any friendship objects because the users are not friends
        if active_friendship_id:
            active_friendship = AuthorFriend.objects.get(id=active_friendship_id)
            active_friendship.delete()
    except Exception as e:
        #Roll back any changes upon any failures
        active_request.is_deleted=False
        active_following.is_deleted=False
        if active_friendship:
            active_friendship.is_deleted=False
        
        print(e)
        return HttpResponseServerError(f"Failed to Unfollow This User.")
    
    #CHECK FOR SUCCESSFUL DELETIONS
    '''
    print("Follow Request Deleted:",active_request.is_deleted)
    print("Active Following Deleted:",active_following.is_deleted)
    if active_friendship_id:
        print("Active Friendship Deleted:", active_request.is_deleted)
    '''

    #redirect to the requested user's page 
    return redirect(reverse("wiki:view_external_profile", kwargs={"author_serial": followed_author_serial}))          


@login_required    
def view_following(request):
    pass

def view_entry_author(request, entry_serial):
    '''Redirects users to view the page of an author whose entry they are looking at'''
    entry = get_object_or_404(Entry, serial=entry_serial)
    author_id = entry.author.id
    entry_author=get_object_or_404(Author, id=author_id)
    return HttpResponseRedirect(reverse("wiki:view_external_profile", kwargs={"author_serial": entry_author.serial}))

            
        
def node_valid(username, password):
    '''checks if the node associated with a given host is valid'''
    
    #Log the information of the node attempting to connect to this node
    print("\nUSERNAME",username,"\nPASSWORD:","*" * len(password))
    #check if the following conditions are met by the connecting node:
    #the host is one of the active remote nodes currently in our database
    #the credentials in the BASIC auth token match our current Node Connection Credentials
    remoteNodes = RemoteNode.objects.filter(is_active=True)
    print(f"ACTIVE NODES: {remoteNodes}")

    if RemoteNode.objects.filter(username=username, password=password).exists():
        return True #access is granted to the node
         
    print("CREDENTIALS NOT VALIDATED WITHIN OUR DATABASE, ACCESS DENIED.")
    return False #access denied
        

@login_required  
@require_http_methods(["GET", "POST"]) 
def follow_profile(request, author_serial):
    
    
    if request.user.is_staff or request.user.is_superuser:
        return HttpResponseServerError("Admins cannot perform author actions. Please use a regular account associated with an Author.")

    current_user = request.user
    
    requesting_account = get_object_or_404(Author, user=current_user)
    requested_account = get_object_or_404(Author, serial=author_serial)
    

    follow_request = FollowRequest(requester=requesting_account, requested_account=requested_account)
    follow_request.summary = str(follow_request)
    
    ##CHECK REQUESTING AND REQUESTED ACCOUNT##
    #print(requesting_account)
    #print(requested_account)
    ##########################################
    
    if requesting_account.is_friends_with(requested_account):
        base_URL = reverse("wiki:view_external_profile", kwargs={"author_serial": requested_account.serial})
        query_with_friend_status= f"{base_URL}?status=friends&user={requested_account}"
        return redirect(query_with_friend_status)
    
    
    if requesting_account.is_following(requested_account):
        base_URL = reverse("wiki:view_external_profile", kwargs={"author_serial": requested_account.serial})
        query_with_follow_status= f"{base_URL}?status=following&user={requested_account}"
        return redirect(query_with_follow_status)
    
    #if the author is not following or friends with the receiving author:        
    try:
        serialized_follow_request = FollowRequestSerializer(
        follow_request, data={
        "type":"follow",
        },partial=True

        )
         # Valid follow requests will lead to an attempted saving of the corresponding respective inbox item
        if not serialized_follow_request.is_valid():
            return HttpResponseServerError(f"We were unable to send your follow request: {serialized_follow_request.errors}")
        
        #remote profiles will automatically send a following
        if  not requested_account.is_local:
            print("requested isn't local")
                
            inbox_url = str(requested_account.id).rstrip('/')+"/inbox/"
            print(f"sending request to {inbox_url}")
            print(serialized_follow_request.data)
                
            try:
                remote_follow_request = FollowRequest(requester=requesting_account, requested_account=requested_account,  state=RequestState.REQUESTING)
                requesting = remote_follow_request.requester
                requested = remote_follow_request.requested_account
                remote_serialized_request = FollowRequestSerializer(remote_follow_request)
                # attempt to save the follow request
                try:
                    
                    # try to push the follow request to the remote inbox to send them a follow request, then automatically follow them if succeeds
                    try:
                            follow_request_response = requests.post(
                            inbox_url,
                            json=remote_serialized_request.data,  
                            auth=AUTHTOKEN,
                            timeout=2
                            )
                    except Exception as e:
                        print(e)
                        
                    if len(follow_request_response.content) < 200:
                        print(f"RESPONSE: {follow_request_response.content}")
                    
       
                    # at this point, you've pushed the follow request SUCCESSFULLY to their node and they need to deal with the inbox item to generate a follow request 
                    # in the node sending the follow request, a following relationship can now be assumed, so you immediately follow the remote author 
                    if follow_request_response.status_code == 200:
                        local_request = remote_follow_request
                        local_request.set_request_state(RequestState.ACCEPTED)
                        try:
                            local_request.save()    
                        except Exception as e:
                            raise e
                        
                        print("remote follow request was saved")
                        print(f"{requesting} is attempting to follow {requested}")
                        saved_following_to_remote = AuthorFollowing(follower=requesting, following=requested)
                        print(f"ATTEMPTED TO SAVE FOLLOWING: {saved_following_to_remote}")  
                        #save the new following
                        print("TRYING TO SAVE NEW FOLLOWING...")
                        saved_following_to_remote.save()
                        print("valid follow request, saved following for remote node.")
                        #CHECK FOR A FRIENDSHIP AND MAKE ONE IF THERE IS A MUTUAL FOLLOWING
                        print(f"requesting author: {requesting}, requested author: {requested}")   
                        if requesting.is_following(requested) and requested.is_following(requesting): 
                            newRemoteFriendship = AuthorFriend(friending=requested, friended=requesting)   
                            print("MUTUAL FOLLOWING FOUND! MAKING FRIENDS NOW...")
                            try:
                                newRemoteFriendship.save()
                                print("SUCCESSFULLY CREATED MUTUAL REMOTE FOLLOWING, THESE AUTHORS ARE NOW FRIENDS")
                            except Exception as e:
                                 raise e
      
                except Exception as e:
                    raise e
                       
            except Exception as e:
                raise e  
                      
    except Exception as e:
        print(f"Failed to save follow request: {e}")
    try:
        follow_request.save()        
        print("REMOTE REQUEST FAILED, YOU MAY STILL BE FOLLOWING THIS AUTHOR ON THEIR NODE, SWITCHING TO LOCAL FOLLOW REQUEST")
        return redirect(reverse("wiki:view_external_profile", kwargs={"author_serial": requested_account.serial}))       
    except Exception as e:
        print(e)
        
    return redirect(reverse("wiki:view_external_profile", kwargs={"author_serial": requested_account.serial}))                
    
        
    
        
@api_view(['GET']) 
def get_profile_api(request, username):
    """
    GET /api/profile/edit/{username}/
    View the author's profile.
    """
    try:
        author = Author.objects.get(user__username=username)
    except Author.DoesNotExist:
        return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        author_data = AuthorSerializer(author).data
        entries = Entry.objects.filter(author=author).order_by('-created_at')
        entry_data = EntrySerializer(entries, many=True, context={'request': request}).data
        author_data['entries'] = entry_data
        return Response(author_data, status=status.HTTP_200_OK)
        

@login_required
def check_follow_requests(request, username):
    '''Check for all of the follow  requests of a specific author'''
    
    if request.user.is_staff or request.user.is_superuser:
        return HttpResponseServerError("Admins cannot perform author actions. Please user a regular account associated with an Author.")

    requestedAuthor = Author.objects.get(user=request.user)
        
        
    incoming_follow_requests =FollowRequest.objects.filter(requested_account=requestedAuthor, state=RequestState.REQUESTING).order_by('-created_at') 
    
    if not incoming_follow_requests:
        
        incoming_follow_requests = []
           

    return render(request, 'follow_requests.html', {'author':requestedAuthor, "follow_requests": incoming_follow_requests})

@csrf_exempt
@login_required
def process_follow_request(request, author_serial, request_id):
    '''
        Args: 
        
            request: the HTTP request information,
            serial: the author's serial id, 
            request_id: the follow request's IDS
            
        Returns: HTTPResponseError for any issues, a redirection otherwise
        
    '''
   
    if request.user.is_staff or request.user.is_superuser:
        return HttpResponseServerError("Admins cannot perform author actions. Please user a regular account associated with an Author.")
    requestedAuthor = Author.objects.get(serial=author_serial)
    
    choice = request.POST.get("action")
    if choice.lower() == "accept":
    
        #if follow request gets accepted, 
        follow_request = FollowRequest.objects.filter(id=request_id).first()
        print(f"THE STATE OF THE SELECTED FOLLOW REQUEST IS: {follow_request.state}")
    
        try:
            #set the following account, and store whether they are local or not
            follower = follow_request.requester
            followed_account_remote = follow_request.requested_account.is_local == False
            print(f"this account is remote: {followed_account_remote}")
            print("succeeded in setting follower and followed account")
            print(f"{follower} (local author: {follower.is_local}) is trying to follow {follow_request.requested_account}")
        except follower.DoesNotExist:
            return Http404("Follow request was not found between you and this author")
        
        # create a following after accepted request
        try:
            
            #create a following from requester to requested (for local author object, because remote author objects will already have an automatic following once requested)
            follow_request.set_request_state(RequestState.ACCEPTED)
            new_following = AuthorFollowing(follower=follower, following=requestedAuthor)
            new_following_serializer = AuthorFollowingSerializer(new_following, data={
                    "follower":new_following.follower.id,
                    "following":new_following.following.id,
            }, partial=True)
                
                
            if new_following_serializer.is_valid():
                try:
                        new_following_serializer.save()
                        # Send all appropriate entries to new remote follower
                        # from .util import send_all_entries_to_follower
                        # send_all_entries_to_follower(local_author=requestedAuthor, remote_follower=follower, request=request)
                            
                except Exception as e:
                        print(e)
                        return check_follow_requests(request, request.user.username)

            else:
                    
                return HttpResponseServerError(f"Unable to follow Author {new_following.following.displayName}.")  
        
        except Exception as e:
            print(e) 
            
             
        # check if there is now a mutual following
        if follower.is_following(requestedAuthor) and requestedAuthor.is_following(follower):
            print("there is a mutual following between these authors")

            #if there is, add these two users as friends using the author friends object
            new_friendship = AuthorFriend(friending=requestedAuthor, friended=follower)
            print("new friendship")
            
            try:
                new_friendship.save()  
                
                
            except Exception as e:
                # Rollback
                #set the follow  request state to requested
                follow_request.set_request_state(RequestState.REQUESTING)
        
                #delete the new following
                new_following.delete()
                
                #print the exception
                print(e)
            
                return HttpResponseServerError(f"Unable to friend Author {new_following.following.displayName}")      
                      
    else:
        #if follow request is denied,
         follow_request = FollowRequest.objects.filter(id=request_id).first()
    
         try:
            follower = follow_request.requester
                
         except follower.DoesNotExist:
            return Http404("Follow request was not found between you and this author")
        
         #Reject the follow request and delete it 
         follow_request.set_request_state(RequestState.REJECTED)
         follow_request.delete()

    return redirect(reverse("wiki:check_follow_requests", kwargs={"username": request.user.username}))




def decoded_auth_token(auth_header):
    if isinstance(auth_header, str):
        print("AUTH ENCODED IN UTF-8")
        print("AUTH ENCODED AS BYTES, DECODED TO STRING")
        auth_header_split = auth_header.split(" ")# -> ["Basic", "{auth encoded in bytes}"]
        auth = auth_header_split[1]# -> [takes the last part of ^^ (auth encoded in bytes) and stores it as the auth token] -> {auth_encoded}
        decoded_auth = base64.b64decode(auth.encode('UTF-8'))# -> decodes string auth, encodes it into uft-8 ( a readable string)
        decoded_username, decoded_pass = decoded_auth.decode().split(":", 1)# -> username, password
    else:
        return False
        
    #print(f"AUTH INFO SPLIT: {auth_header_split}")
    #print(f"ENCODED AUTH INFO: {auth}")
    #print(f"DECODED AUTH : {decoded_auth}")
    #print(f"USDERNAME AND PASSWORD: {decoded_username, decoded_pass}")
    
    return decoded_username, decoded_pass
    
    
@csrf_exempt
@api_view(['GET','POST'])
@authentication_classes([]) #DJANGO was causing most of our problems. the 403 was caused by django enforcing a user object to exist for every request that gets sent
@permission_classes([]) 
def user_inbox_api(request, author_serial):
    '''
    Used to get a User's inbox items, is able to accomodate all types of inbox items
    Fields:
    
    type: the type of inbox item
    body: the JSON content of the inbox object
    created_at: the time the inbox object was posted to the inbox
    
    
    In its most basic form, we have: 
    
         {
            "type": {the type of inbox item}
            "author":{the recieving author's ID}
            "body": {the object sent to this inbox}
            "created_at": {the time this inbox object was recieved}
        }
                
                
    Example usage:
    
    GET:
    
    GET /api/authors/{author_serial}/inbox/
    
    for a successful GET request:
    
    HTTP 200 OK
    Allow: GET, OPTIONS, DELETE, POST
    Content-Type: application/json
    Vary: Accept

    
    [
        {
        "type": "Follow",
        "author": "http://127.0.0.1:8000/api/authors/99f75995-a05e-497f-afd4-5af96cf3b0b4",
        "body": {
            "type": "follow",
            "state": "requesting",
            "summary": "b has requested to follow GUTS",
            "actor": {
                "type": "author",
                "id": "http://127.0.0.1:8000/api/authors/57790772-f318-42bd-bb0c-838da9562720",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "b",
                "github": "",
                "profileImage": "/media/profile_images/aliceinwonderlandcover.jpg",
                "web": "http://127.0.0.1:8000/authors/57790772-f318-42bd-bb0c-838da9562720",
                "description": ""
            },
            "object": {
                "type": "author",
                "id": "http://127.0.0.1:8000/api/authors/99f75995-a05e-497f-afd4-5af96cf3b0b4",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "GUTS",
                "github": "",
                "profileImage": "/media/profile_images/gutspfp.jpg",
                "web": "http://127.0.0.1:8000/authors/99f75995-a05e-497f-afd4-5af96cf3b0b4",
                "description": ""
            }
        },
        "created_at": "2025-07-19T21:59:33.076302-06:00"
        }
    ]
    
    for a failed get Request:
    
    HTTP 400 Bad Request
    Allow: GET, OPTIONS, POST
    Content-Type: application/json
    Vary: Accept
    
    {
    "Error": "We were unable to locate the user who made this request, dev notes: ['"99f5-a05e-497f-afd4-5af96cf3b0b4" is not a valid UUID.']"
    }
    
    POST:
    Use POST /api/authors/{author_serial}/inbox/
    
    for a successful POST request, you will recieve the new serialized inbox object:
    
    HTTP 200 OK
    Allow: GET, POST, OPTIONS
    Content-Type: application/json
    Vary: Accept
    
    
    {
    
    {
        "type": "follow",
        "state": "requesting",
        "summary": "b has requested to follow GUTS",
        "actor": {
            "type": "author",
            "id": "http://127.0.0.1:8000/api/authors/57790772-f318-42bd-bb0c-838da9562720",
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "b",
            "github": "",
            "profileImage": "/media/profile_images/aliceinwonderlandcover.jpg",
            "web": "http://127.0.0.1:8000/authors/57790772-f318-42bd-bb0c-838da9562720",
            "description": ""
        },
        "object": {
            "type": "author",
            "id": "http://127.0.0.1:8000/api/authors/99f75995-a05e-497f-afd4-5af96cf3b0b4",
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "GUTS",
            "github": "",
            "profileImage": "/media/profile_images/gutspfp.jpg",
            "web": "http://127.0.0.1:8000/authors/99f75995-a05e-497f-afd4-5af96cf3b0b4",
            "description": ""
        }
    }
   
    For a failed POST request, the requester will recieve the error info:
    
    HTTP 404 Not Found
    Allow: OPTIONS, GET, POST
    Content-Type: application/json
    Vary: Accept
    
    {
    "detail": "JSON parse error - Expecting value: line 1 column 1 (char 0)"
    }
    
    '''
    
    auth_header = request.META.get('HTTP_AUTHORIZATION')

    #need to have auth in request to connect with us
    if not auth_header:
        return Response({"unauthorized": "please include authentication with your requests"}, status=status.HTTP_401_UNAUTHORIZED)
    print(f"AUTH HEADER FOUND.\nENCODED AUTH HEADER: {auth_header}")
    
    #If the auth header has basic auth token in it
    if not auth_header.startswith("Basic"):
        return Response({"Poorly formatted auth": "please include BASIC authentication with your requests to access the inbox."}, status=status.HTTP_401_UNAUTHORIZED)
    print(f"AUTH HEADER STARTS WITH BASIC: {auth_header.startswith('Basic')}")
    
    #Gets the user and pass using basic auth
    username, password = decoded_auth_token(auth_header)
    
    #make sure the auth is properly formatted
    if not (username and password):
        print("COULD NOT PARSE USER AND PASS FROM POORLY FORMATTED AUTH.")
        return Response({"ERROR" :"Poorly formed authentication header. please send a valid auth token so we can verify your access"}, status = status.HTTP_400_BAD_REQUEST)

    #for an invalid node
    if not node_valid(username, password):
        return Response({"Node Unauthorized": "This node does not match the credentials of any validated remote nodes", "detail":"please check your authorization details (case-sensitive)"}, status=status.HTTP_401_UNAUTHORIZED)
    print("AUTHENTICATION COMPLETE.")
    print(f"{username} may now access the node.")

    currentNodes = RemoteNode.objects.all()
    print(f"CONNECTED NODES {currentNodes}")
    
    requested_author = get_object_or_404(Author, serial=author_serial)

    #retrieve all of the author's inbox objects
    if request.method =="GET":
        
        if not request.user.is_authenticated:
            return Response({"Error":f"You are unauthorized to view this user's inbox"}, status=status.HTTP_401_UNAUTHORIZED)
        
        inboxItems = requested_author.inboxItems.order_by('-created_at')
        serializedInboxItems = InboxItemSerializer(inboxItems, many=True)
        return Response(serializedInboxItems.data, status=status.HTTP_200_OK)
   
        
    #sends an inbox object to a specific author
    elif request.method =="POST": 
        
        #################################TEST##################################### 
        print(f"\n\n\n\n\n\n\n\n\nTHIS IS THE REQUEST:\n\n{request.data}\n\n\n")
        #########################################################################
        type = request.data.get("type")
        
        if not type:
            return Response({"failed to save Inbox item":f"dev notes: inbox objects require a 'type' field."}, status=status.HTTP_400_BAD_REQUEST)    
        
        ############## PROCESSES  FOLLOW REQUEST INBOX OBJECTS ###################################################################################################################
        

        # Handle remote entry
        if type.lower() == "entry":
            entry_data = request.data
            entry_id = entry_data.get("id")
            entry_serial = entry_id.rstrip('/').split('/')[-1]
            if not entry_data:
                return Response({"error": "No entry data provided"}, status=status.HTTP_400_BAD_REQUEST)
            origin_url = entry_data.get("id")
            # Find or create the remote author
            author_data = entry_data.get("author")
            if not author_data:
                return Response({"error": "No author data in entry"}, status=status.HTTP_400_BAD_REQUEST)
            
            remote_author, _ = Author.objects.get_or_create(
                id=author_data["id"],
                defaults={
                    "serial": author_data.get("serial", ""),
                    "displayName": author_data.get("displayName", ""),
                    "host": author_data.get("host", ""),
                    "web": author_data.get("web", ""),
                    "github": author_data.get("github", ""),
                    "profileImage": author_data.get("profileImage", ""),
                }
            )
            # Find or create the entry
            
            entry, created = Entry.objects.update_or_create(
                origin_url=origin_url,
                defaults={
                    "id": entry_id,
                    "serial": entry_serial,
                    "author": remote_author,
                    "title": entry_data.get("title", ""),
                    "content": entry_data.get("content", ""),
                    "contentType": entry_data.get("contentType", "text/plain"),
                    "description": entry_data.get("description", ""),
                    "visibility": entry_data.get("visibility", "PUBLIC"),
                    "web": entry_data.get("web", ""),
                    "is_deleted": False,
                    "is_local": False
                }
            )
            
            
           

            return Response({"success": "Entry received and stored", "created": created}, status=status.HTTP_200_OK)
        
        ############## PROCESSES  FOLLOW REQUEST INBOX OBJECTS ###################################################################################################################
                
        #for follow requests
        if type.lower() == "follow":
            
            try:
                body = request.data
                authorFQID = request.data['actor']['id']
            except Exception as e:
                return Response({"failed to save Inbox item": "could not fetch author object, improperly formatted author"}, status=status.HTTP_400_BAD_REQUEST)
            
            print("AUTHOR FQID IS:")
            remoteAuthorObject = remote_author_fetched(authorFQID)

            if not remoteAuthorObject or not authorFQID:
                 return Response({"failed to save Inbox item": "could not fetch author object"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)     
             ################################################################TEST#####################################################################################################
             #print("FOLLOW REQUEST BODY:","\n\n\n",body,'\n\n\n',"REQUESTER FQID:\n\n\n",authorFQID,'\n\n\n',"REQUESTED AUTHOR (LOCAL) FQID:\n\n\n",requested_author.id,'\n\n\n')
             ####################################################################################################################################################################
            
            #CHECK FOR THE EXISTENCE OF THE AUTHOR
            if not author_exists(authorFQID):
                
                #SERIALIZE AND SAVE IF THEIR DATA IS VALID
                requesting_account_serialized = AuthorSerializer(data=remoteAuthorObject)
                
                #IF THEIR DATA IS INVALID, INFORM THE REQUESTER
                if not requesting_account_serialized.is_valid():
                    return Response({"failed to save Inbox item":f"dev notes: {requesting_account_serialized.errors}"}, status=status.HTTP_400_BAD_REQUEST)
                
                #IF THEY DO NOT ALREADY EXIST, SAVE THEM TO THE NODE
                requester = requesting_account_serialized.save()
                requester.is_local=False
                requester.save()
                   
            #OTHERWISE GET THE AUTHOR SINCE THEY MUST EXIST
            else:
                requester = Author.objects.get(id=authorFQID)
              
            if requester.is_already_requesting(requested_author):
                return Response({"failed to save Inbox item":f"dev notes: you have already requested to follow this author."}, status=status.HTTP_400_BAD_REQUEST)    

            remote_follow_request = FollowRequest(requester=requester, requested_account=requested_author,  state=RequestState.REQUESTING)
            remote_serialized_request = FollowRequestSerializer(remote_follow_request)

          
            #attempt to save the follow request
            try:
                remote_follow_request.save()
                type="Follow"
                print("valid follow request")
            except Exception as e:
                print(remote_serialized_request.data)
                return Response({"Unable to save follow request" : f"dev notes:{e}"}, status=status.HTTP_400_BAD_REQUEST)
                
            #set the inbox body to the validated inbox object 
            #This goes in the inbox item body now so WE can retrieve it later wherever need be
            body = remote_serialized_request.data
            ################TEST##############
            print('\n\n\n',body,'\n\n\n')
            ################TEST##############
            
        ##################################### END OF FOLLOW REQUEST PROCESSING ######################################################################################################################################
        
        ############## PROCESSES LIKE INBOX OBJECTS ###################################################################################################################
        
        elif type == "like" or type == "Like":
            
            try:
                body = request.data
                authorFQID = request.data['author']['id']
                objectFQID = request.data['object']
            except Exception as e:
                return Response({"failed to save Inbox item": "could not fetch like object, improperly formatted like"}, status=status.HTTP_400_BAD_REQUEST)
            
            print("LIKE REQUEST BODY:", "\n\n\n", request.data, '\n\n\n')
            remoteAuthorObject = remote_author_fetched(authorFQID)

            if not remoteAuthorObject or not authorFQID:
                return Response({"failed to save Inbox item": "could not fetch author object"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # CHECK FOR THE EXISTENCE OF THE AUTHOR
            if not author_exists(authorFQID):
                
                # SERIALIZE AND SAVE IF THEIR DATA IS VALID
                requesting_account_serialized = AuthorSerializer(data=remoteAuthorObject)
                
                # IF THEIR DATA IS INVALID, INFORM THE REQUESTER
                if not requesting_account_serialized.is_valid():
                    return Response({"failed to save Inbox item":f"dev notes: {requesting_account_serialized.errors}"}, status=status.HTTP_400_BAD_REQUEST)
                
                # IF THEY DO NOT ALREADY EXIST, SAVE THEM TO THE NODE
                requester = requesting_account_serialized.save()
                requester.is_local=False
                requester.save()
                   
            # OTHERWISE GET THE AUTHOR SINCE THEY MUST EXIST
            else:
                requester = Author.objects.get(id=authorFQID)
            
            # Check if the like is for an entry or comment
            if '/entries/' in objectFQID and '/comments/' in objectFQID:
                # This is a comment like
                try:
                    # Parse the comment FQID to extract entry and comment info
                    # Format: http://host/api/authors/{author_serial}/entries/{entry_serial}/comments/{comment_serial}
                    parts = objectFQID.split('/')
                    entry_author_serial = parts[-4]  # author serial
                    entry_serial = parts[-2]  # entry serial
                    comment_serial = parts[-1]  # comment serial
                    
                    # Find the local entry
                    entry = Entry.objects.get(serial=entry_serial)
                    
                    # Find the existing comment
                    comment = Comment.objects.get(id=comment_serial)
                    
                    # Check if like already exists
                    if CommentLike.objects.filter(comment=comment, user=requester, is_deleted=False).exists():
                        return Response({"failed to save Inbox item": "Comment like already exists"}, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Create the comment like
                    comment_like = CommentLike.objects.create(
                        comment=comment,
                        user=requester,
                        is_local=False
                    )
                    
                    # Serialize the like for the inbox
                    like_serializer = CommentLikeSummarySerializer(comment_like, context={'request': request})
                    body = like_serializer.data
                    type = "Like"
                    
                except Comment.DoesNotExist:
                    return Response({"failed to save Inbox item": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)
                except Exception as e:
                    return Response({"failed to save Inbox item": f"Error processing comment like: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
                    
            elif '/entries/' in objectFQID:
                # This is an entry like
                try:
                    # Parse the entry FQID to extract entry info
                    # Format: http://host/api/authors/{author_serial}/entries/{entry_serial}
                    parts = objectFQID.split('/')
                    entry_author_serial = parts[-3]  # author serial (third from end)
                    entry_serial = parts[-1]  # entry serial (last)
                    
                    # Find the local entry
                    entry = Entry.objects.get(serial=entry_serial)
                    
                    # Check if like already exists
                    if Like.objects.filter(entry=entry, user=requester, is_deleted=False).exists():
                        return Response({"failed to save Inbox item": "Like already exists"}, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Create the entry like
                    entry_like = Like.objects.create(
                        entry=entry,
                        user=requester,
                        is_local=False
                    )
                    
                    # Serialize the like for the inbox
                    like_serializer = LikeSummarySerializer(entry_like, context={'request': request})
                    body = like_serializer.data
                    type = "Like"
                    
                except Entry.DoesNotExist:
                    return Response({"failed to save Inbox item": "Entry not found"}, status=status.HTTP_404_NOT_FOUND)
                except Exception as e:
                    return Response({"failed to save Inbox item": f"Error processing entry like: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"failed to save Inbox item": "Invalid object FQID format"}, status=status.HTTP_400_BAD_REQUEST)
            
            ################TEST##############
            print('\n\n\n',body,'\n\n\n')
            ################TEST##############
            
        ##################################### END OF LIKE PROCESSING ######################################################################################################################################
        
        ############## PROCESSES COMMENT INBOX OBJECTS ###################################################################################################################
        
        elif type == "comment" or type == "Comment":
            print(f"DEBUG: Processing comment in inbox")
            print(f"DEBUG: Request data: {request.data}")
            
            try:
                body = request.data.get('body', {})
                print(f"DEBUG: Body: {body}")
                authorFQID = body.get('author', {}).get('id')
                comment_content = body.get('comment', '')
                contentType = body.get('contentType', 'text/plain')
                entryFQID = body.get('entry')
                print(f"DEBUG: Extracted authorFQID: {authorFQID}")
                print(f"DEBUG: Extracted comment_content: {comment_content}")
                print(f"DEBUG: Extracted contentType: {contentType}")
                print(f"DEBUG: Extracted entryFQID: {entryFQID}")
            except Exception as e:
                print(f"DEBUG: Exception in comment processing: {e}")
                return Response({"failed to save Inbox item": "could not fetch comment object, improperly formatted comment"}, status=status.HTTP_400_BAD_REQUEST)
            
            print("COMMENT REQUEST BODY:", "\n\n\n", request.data, '\n\n\n')
            remoteAuthorObject = remote_author_fetched(authorFQID)

            if not remoteAuthorObject or not authorFQID:
                return Response({"failed to save Inbox item": "could not fetch author object"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # CHECK FOR THE EXISTENCE OF THE AUTHOR
            if not author_exists(authorFQID):
                
                # SERIALIZE AND SAVE IF THEIR DATA IS VALID
                requesting_account_serialized = AuthorSerializer(data=remoteAuthorObject)
                
                # IF THEIR DATA IS INVALID, INFORM THE REQUESTER
                if not requesting_account_serialized.is_valid():
                    return Response({"failed to save Inbox item":f"dev notes: {requesting_account_serialized.errors}"}, status=status.HTTP_400_BAD_REQUEST)
                
                # IF THEY DO NOT ALREADY EXIST, SAVE THEM TO THE NODE
                requester = requesting_account_serialized.save()
                requester.is_local=False
                requester.save()
                   
            # OTHERWISE GET THE AUTHOR SINCE THEY MUST EXIST
            else:
                requester = Author.objects.get(id=authorFQID)
            
            # Parse the entry FQID to extract entry info
            # Format: http://host/api/authors/{author_serial}/entries/{entry_serial}
            print(f"DEBUG: Parsing entryFQID: {entryFQID}")
            try:
                parts = entryFQID.split('/')
                print(f"DEBUG: Split parts: {parts}")
                entry_author_serial = parts[-3]  # author serial (third from end)
                entry_serial = parts[-1]  # entry serial (last)
                print(f"DEBUG: Extracted author_serial: {entry_author_serial}")
                print(f"DEBUG: Extracted entry_serial: {entry_serial}")
                
                # Find the local entry
                try:
                    entry = Entry.objects.get(serial=entry_serial)
                except Entry.DoesNotExist:
                    entry = None  # Accept that it’s a remote entry
                print(f"DEBUG: Saving comment with entry_url={entryFQID}, entry={entry}")
                comment = Comment.objects.create(
                    entry=entry,
                    author=requester,
                    content=comment_content,
                    contentType=contentType,
                    is_local=False
                )
                print(f"DEBUG: Created comment: {comment}")
                # Serialize the comment for the inbox
                comment_serializer = CommentSummarySerializer(comment, context={'request': request})
                body = comment_serializer.data
                type = "comment"
                print(f"DEBUG: Serialized comment for inbox: {body}")
            except Entry.DoesNotExist:
                return Response({"failed to save Inbox item": "Entry not found"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"failed to save Inbox item": f"Error processing comment: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            
            ################TEST##############
            print('\n\n\n',body,'\n\n\n')
            ################TEST##############
            
        ##################################### END OF COMMENT PROCESSING ######################################################################################################################################
        else:
            return Response({"succeeded to post":"other methods are not yet implemented"}, status=status.HTTP_200_OK) 
        
        # This follows successful validation of the inbox post request, and inbox object will be saved, and the recieving author's ID will be the ID field
        # this allows us to track all of an author's inbox items, as well as the sender's ID if we want to retrieve the author object
        # Use author.inboxitems to retrieve all of an author's inbox items
        print("this is the requested other: " + str(requested_author))
        newItemSerializer = InboxItemSerializer(data= {
            "type":type,
            "author":requested_author.id,
            "body":body
        }, partial=True)
                
        #TODO: ADD VALIDATION FOR DIFFERENT TYPES OF INBOX OBJECTS:
        # likes
        # comments
        # follows
        # entry items
                
        #This will be the final save once the specific type of inbox item is validated
        #validates general Inbox item structure
        if newItemSerializer.is_valid():
            try:
                newItemSerializer.save()
                return Response(newItemSerializer.data['body'], status=status.HTTP_200_OK)    
            except Exception as e:
                return Response({"failed to save Inbox item":f"dev notes: {e}"}, status=status.HTTP_400_BAD_REQUEST)    

        
        else:
            return Response({f"FAILED TO SAVE INBOX ITEM":f"{newItemSerializer.errors}"} ,status=status.HTTP_400_BAD_REQUEST)
                
        
        
        
@csrf_exempt
@api_view(['GET','PUT','DELETE'])
def foreign_followers_api(request, author_serial, FOREIGN_AUTHOR_FQID):
    'GET api/authors/{AUTHOR_SERIAL}/followers/{FOREIGN_AUTHOR_FQID}'

    current_user = request.user
    try:
        current_author = Author.objects.get(serial=author_serial)
    except Author.DoesNotExist:
         return Response({"NOT FOUND": "We could not locate an author with this specific serial"}, status=status.HTTP_404_NOT_FOUND)
    
    #decode the foreign author's ID
    decodedId = decoded_fqid(FOREIGN_AUTHOR_FQID)
     

    remote_author_object = remote_author_fetched(decodedId)
    
    #get the author if it exists (using decoded ID)
    if not remote_author_object:
       return Response({"error": "the URL is you provided does not belong to an author we recognize"}, status=status.HTTP_404_NOT_FOUND)      
    print(f"Remote Author: {remote_author_object}")    

    
    try:  
        #get the response at the author followers endpoint
            followers_uri =decodedId + "/followers"
            response = requests.get(followers_uri,auth=AUTHTOKEN)
            if response.status_code != 200:
                response_data = response.json()
                return Response(response_data, response.status_code)
        
            followers_dict = response.json() 
            follower_ids = [follower["id"] for follower in followers_dict["followers"]]
            
    except Exception as e:
        return Response({"Failed to retrieve author object": f"{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    if request.method=="GET":
  
        
        if current_author.id in follower_ids:
            return Response(followers_dict, status=status.HTTP_200_OK)
           
        else:
            return Response({"FOLLOWING NOT FOUND": "You are not following this author"}, status=status.HTTP_404_NOT_FOUND)
        
    #TODO:
    # PUT and DELETE endpoint
    'PUT api/authors/{AUTHOR_SERIAL}/followers/{FOREIGN_AUTHOR_FQID}'  
    if request.method=="PUT":
        if current_user != current_author.user:
            return Response({"Unauthorized": "You do not have permission to use this method"}, status=status.HTTP_401_UNAUTHORIZED)
        if is_local_url(request,remote_author_object['id']):
            return Response({"Unauthorized": "You do not have permission to use this method, local authors cannot be added as followers through this endpoint"}, status=status.HTTP_401_UNAUTHORIZED)
        
        remote_author = Author.objects.get_or_create(id=remote_author_object['id'], 
                                                     displayName=remote_author_object['displayName'],
                                                     github=remote_author_object['github'],
                                                     is_local=False,
                                                     host=get_host_and_scheme(decodedId),
                                                     description = remote_author_object['description'],
                                                     profileImage=remote_author_object["profileImage"],
                                                     web=remote_author_object['web']              
                                                    )
        
        newRemoteFollowing= AuthorFollowing(follower=remote_author,following=current_author)
        newFollowingSerialized = AuthorFollowingSerializer(newRemoteFollowing, 
                                                            data={
                                                                "follower":newRemoteFollowing.follower,
                                                                "following":newRemoteFollowing.following,
                                                                "followerId":newRemoteFollowing.followerId,
                                                                },partial=True)
        
        if newFollowingSerialized.is_valid():
            print("SERIALIZER IS VALID")
            try:
                newFollowingSerialized.save()
                print("NEW FOLLOWING:\n\n\n", newFollowingSerialized.data)
                return Response({"Successfully added follower": f"{newFollowingSerialized.data}"}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": f"We were unable to add this follower: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
        else:
            return Response({"error": f"We were unable to add this follower: {newFollowingSerialized.errors}"}, status=status.HTTP_400_BAD_REQUEST) 
        
    
        
       
           
        
        
        
    
    
   
 

@api_view(['PUT', 'DELETE'])
def add_local_follower(request, author_serial, new_follower_serial): 
        """
         Add a follower to a specific user's following list after validating the new follow object
                
                Use: "PUT api/authors/local/<str:author_serial>/followers/<str:new_follower_serial>"

                Returns:
                
                    -  JSON in the format:
               
                    {   "follower addition status": "successful",
                        
                        "type": "new follower",
                        
                        "follow summary": 
                        {
                            "follower": "http://127.0.0.1:8000/api/authors/01fcb29d-3241-43b1-a2ef-d6599b8aa951",
                            "following": "http://127.0.0.1:8000/api/authors/57790772-f318-42bd-bb0c-838da9562720",
                            "date_followed": "2025-07-03T22:36:30.094650-06:00"
                        },
                        
                        "follower": {
                            "type": "author",
                            "id": "http://127.0.0.1:8000/api/authors/01fcb29d-3241-43b1-a2ef-d6599b8aa951",
                            "host": "http://127.0.0.1:8000/api/",
                            "displayName": "v",
                            "github": null,
                            "profileImage": "/media/https%3A/cdn.pixabay.com/photo/2016/08/08/09/17/avatar-1577909_640.png",
                            "web": "http://127.0.0.1:8000/authors/01fcb29d-3241-43b1-a2ef-d6599b8aa951",
                            "description": ""
                        }
                    }
                    
                    Upon successful follows   
                - returns 401 in the event of an unauthorized user adding a follower to a follow list
                - returns 400 in the event of a PUT request that violates any restrictions
                     
        """ 
        #If the user is local, make sure they're logged in 
        if request.user: 
              
            current_user = request.user  
            #IF LOCAL AUTHOR IS LOGGED IN
            try: 
                current_author = get_object_or_404(Author, user=current_user)
                requested_author = get_object_or_404(Author,serial=author_serial)   
                pending_follower = get_object_or_404(Author,serial=new_follower_serial)
            except Exception as e:
                return Response({"Error":f"We were unable to locate the user who made this request, dev notes: {e}"}, status=status.HTTP_404_NOT_FOUND )
            
            if requested_author == current_author:

                follower_relations = current_author.followers.all()
                
                #get and serialize all of the authors followers     
                if follower_relations:
                    followers_list=[followers.follower for followers in follower_relations]          
                #print(followers_list)   
                    
                    
                #check if the new follower has an existing follow with the current author
                for follower in followers_list:
                    #print(follower.serial)
                    #print(new_follower_serial)
                    if str(follower.serial) == new_follower_serial:
                        return Response({"Error": f"{pending_follower} already follows {current_author}"}, status=status.HTTP_400_BAD_REQUEST)
                
                #CHECK THAT THERE IS A PENDING FOLLOW REQUEST FROM NEW FOLLOWER TO CURRENT AUTHOR 
                existing_request = FollowRequest.objects.filter( 
                        Q(requester=pending_follower, requested_account=current_author),
                        Q(state=RequestState.REQUESTING)
                    ).exists()
                    
                #IF THERE IS, PREVENT THE CREATION OF A FOLLOW, REQUEST NEEDS PROCESSING
                if existing_request:
                        return Response({"Error": f"{pending_follower} has a pending follow request to {current_author}"}, status=status.HTTP_400_BAD_REQUEST) 
                    
                #CHECK for existing accepted follow request, if one exists, attempt a save:
                elif FollowRequest.objects.filter( 
                        Q(requester=pending_follower, requested_account=current_author),
                        Q(state=RequestState.ACCEPTED)
                        ).exists():
                       
                    #Try to make a new following between the pending follower and the current author, save it and send a 200 response
                    try:
                        new_following = AuthorFollowing.objects.create(follower=pending_follower, following=current_author)
                        new_following.save()
                        # Send all appropriate entries to new remote follower
                        if not pending_follower.is_local:
                            from .util import send_all_entries_to_follower
                            send_all_entries_to_follower(local_author=current_author, remote_follower=pending_follower, request=request)
                        return Response({"follower addition status":"successful","type": "new follower", "follow summary": AuthorFollowingSerializer(new_following).data, "follower": AuthorSerializer(pending_follower).data}, status=status.HTTP_200_OK)
                    except Exception as e:
                        return Response({"Follow creation failed": f"{e}"}, status= status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                return Response({"Cannot Create New Following": f"{pending_follower} has yet to send a follow request accepted by {current_author}"}, status=status.HTTP_400_BAD_REQUEST)
                
        else:
            return Response({"error":"user requesting information is not currently logged in, you do not have access to this information"}, status=status.HTTP_401_UNAUTHORIZED )                   
       
    
                       
                    

@api_view(['GET'])
def get_local_followers(request, author_serial):   
    """
        Get a specific author's followers list requests in the application
        
        Use: "GET /api/authors/{author_serial}/followers/"

        returns Json in the following format upon a successful request: 
            
                    {
                        "type": "followers",      
                        "followers":[
                            {
                                "type":"author",
                                "id":"http://nodebbbb/api/authors/222",
                                "host":"http://nodebbbb/api/",
                                "displayName":"Lara Croft",
                                "web":"http://nodebbbb/authors/222",
                                "github": "http://github.com/laracroft",
                                "profileImage": "http://nodebbbb/api/authors/222/entries/217/image"
                            },
                            {
                                // Second follower author object
                            },
                            {
                                // Third follower author object
                            }
                        ]
                    } 
                    
        - a successful request will yield a status 200 HTTP response
        - a failed response will yield:
        
            - 404 Not found for a non existing author
            - 500 Internal Server Error if there was an internal failure in retrieving the followers for the given author
    """
    if request.method =='GET':
       
        
        '''
        uncheck for now
        #If the user is local, make sure they're logged in 
        if not request.user.is_authenticated:
            return Response({"error":"user requesting information is not currently logged in, you do not have access to this information"}, status=status.HTTP_401_UNAUTHORIZED )
       ''' 
        try:
            current_author = Author.objects.get(serial=author_serial)  
        except Exception as e:
             return Response({"Error" : f"We were unable to locate this account: {e}"}, status=status.HTTP_404_NOT_FOUND )    
       
            
        #get and serialize all of the authors followers 
        followers_list=[]
                
        follower_relations = current_author.followers.all()
                  
        if follower_relations:
            for followers in follower_relations:
                #print(followers.follower)
                follower = followers.follower
                followers_list.append(follower)
            #print(followers_list)
        
        try:
            serialized_followers = AuthorSerializer( followers_list, many=True)
            response = serialized_followers.data
            return Response({"type": "followers", "followers":response}, status=status.HTTP_200_OK)
            
        except Exception as e:
                return Response({"Error" : f"We were unable to get the followers for this user: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )         
                
    


@login_required
@api_view(['GET'])
def get_local_follow_requests(request, author_serial):   
    """
    Get a specific author's follow requests in the application
    
    Use: "GET /api/authors/{author_serial}/follow_requests/"

    returns Json in the following format: 
         
                {
                    "type": "follow",
                    "state": "requesting" //default is requesting, is one of the options in [requesting, accepted or rejected]      
                    "summary":"actor wants to follow object",
                    "actor":{
                        "type":"follow",
                        // The rest of the author object for the author who wants to follow
                    },
                    "object":{
                        "type":"follow",
                        // The rest of the author object for the author they want to follow
                    }
                }      
     """
    current_user = request.user  
    
    try: 
        current_author = get_object_or_404(Author, user=current_user)
        requested_author = get_object_or_404(Author,serial=author_serial)   
    except Exception as e:
        return Response({"Error":"User Not Located Within Our System"}, status=status.HTTP_404_NOT_FOUND )
    
    #If the user is local, make sure they're logged in 
    if request.user.is_authenticated: 
        
        if requested_author == current_author:
  
            #get and serialize all of the follow requests
            all_follow_requests = current_author.get_follow_requests_recieved() 
            try:
                serialized_follow_requests = FollowRequestSerializer( all_follow_requests, many=True)
                response = serialized_follow_requests.data
                return Response(response, status=status.HTTP_200_OK)
        
            except Exception as e:
                    return Response({"Error" : f"We were unable to authenticate the follow requests for this user: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )            
        else:
            return Response({"error":"user requesting information is not currently logged in, you do not have access to this information"}, status=status.HTTP_401_UNAUTHORIZED )
    

def friends_list(request, author_serial):
    author = get_object_or_404(Author, serial=author_serial)
    friendships = AuthorFriend.objects.filter(
        Q(friending=author) | Q(friended=author),
        is_deleted=False
    )

    friends = []
    for friendship in friendships:
        if friendship.friending == author:
            friends.append(friendship.friended)
        else:

            friends.append(friendship.friending)
    return render(request, "relationship_list.html", {
        "title": "Friends",
        "people": friends,
    })

def followers_list(request, author_serial):
    author = get_object_or_404(Author, serial=author_serial)

    follower_relationships = AuthorFollowing.objects.filter(
        following=author,
        is_deleted=False
    )

    followers = []
    for relationship in follower_relationships:
        follower = relationship.follower
        followers.append(follower)

    return render(request, "relationship_list.html", {
        "title": "Followers",
        "people": followers,
    })

def following_list(request, author_serial):
    author = get_object_or_404(Author, serial=author_serial)

    # Get all people this author is following
    following_relationships = AuthorFollowing.objects.filter(
        follower=author,
        is_deleted=False
    )
    
    following = []
    for relationship in following_relationships:
        followed_author = relationship.following
        following.append(followed_author)

    return render(request, "relationship_list.html", {
        "title": "Following",
        "people": following,
    })


def profile_view(request, username):
    """
    View the profile of the currently logged in user.
    """
    author = Author.objects.get(user__username=username)
    if not request.user.is_authenticated or request.user.username != username:
        if not author:
            return HttpResponse("Author profile does not exist.")
        return redirect('wiki:view_external_profile', author_serial=author.serial)
    # entries = Entry.objects.filter(author=author).order_by('-created_at')    # displays entries from newest first
    
    followers = author.followers.all()#stores all of the followers a given author has
    following = author.following.all()#stores all of the followers a given author has
    friends_a = author.friend_a.all()
    friends_b = author.friend_b.all()
    total_friends = (friends_a | friends_b)
    friend_count=len(total_friends)
    all_entries = author.get_all_entries()#stores all of the user's entries
    
    # VISUAL REPRESENTATION TEST
    #print("Entries:", all_entries)
    #print("followers:", followers)
    #print("following:", following)
   
    rendered_entries = []
    for entry in all_entries:
        rendered = (
            mark_safe(markdown.markdown(entry.content))
            if entry.contentType == "text/markdown"
            else entry.content
        )
        rendered_entries.append((entry, rendered)) 
    
    
    return render(
        request, 'profile.html', 
        {
        'author': author,
        'entries': rendered_entries,
        "followers": followers,
        "follower_count": len(followers),
        "following": following,
        "following_count": len(following),
        "entry_count": len(all_entries),
        "friend_count":friend_count,
        "friends":total_friends} 
    )

@login_required
def edit_profile(request, username):

    try:
        author = Author.objects.get(user__username=username)
    except Author.DoesNotExist:
        return HttpResponse("Author profile does not exist.")

    if request.method == 'POST':
        new_username = request.POST.get('displayName')
        github = request.POST.get('github')
        description = request.POST.get('description')
        profile_image_url = request.POST.get('profileImage')

        # Check if the new username is already taken by someone else
        if new_username and new_username != request.user.username:
            if User.objects.filter(username=new_username).exclude(id=request.user.id).exists():
                return render(request, 'edit_profile.html', {
                    'author': author,
                    'error': 'Username is already taken.'
                })

            #ensures a valid username is entered (no spaces, less than 50 characters)
            if not validUserName(new_username):
                return render(request, 'edit_profile.html', {
                    'author': author,
                    'error': 'Please select a username with no spaces that is under 150 characters in length.'
                })
                
            request.user.username = new_username
            request.user.save()
            author.displayName = new_username

        author.github = github
        author.description = description

        if profile_image_url: 
            author.profileImage = profile_image_url

        author.save()
        return redirect('wiki:profile', username=new_username)

    return render(request, 'edit_profile.html', {'author': author})



@login_required
def create_entry(request):
    """
    Create a new wiki entry.
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        text_content = request.POST.get('content', '').strip()
        content_type_input = request.POST.get('contentType', '').strip()
        description = request.POST.get('description', '').strip()
        visibility = request.POST.get('visibility')
        use_markdown = request.POST.get('use_markdown') == 'on'
        content_type = "text/markdown" if use_markdown else "text/plain"
        image = request.FILES.get('image')


        if not title:
            return HttpResponse("Title is required.")

        if image and text_content:
            return HttpResponse("Please provide either an image or text content, not both.")
        
        author = get_object_or_404(Author, user=request.user)

        # Determine content type
        if image:
            image_data = image.read()
            encoded = base64.b64encode(image_data).decode('utf-8')
            if image.content_type == 'image/png':
                content_type = 'image/png;base64'
            elif image.content_type == 'image/jpeg':
                content_type = 'image/jpeg;base64'
            else:
                content_type = 'application/base64'  # fallback for unsupported images
            content = encoded
        elif text_content:
            content = text_content
            # Use the dropdown or text input to choose between plain or markdown
            content_type = content_type_input if content_type_input in ['text/plain', 'text/markdown'] else 'text/plain'
        else:
            return HttpResponse("Either an image or text content must be provided.")

        # entry save
        entry = Entry.objects.create(
            author=author,
            title=title,
            content=content,
            contentType=content_type,
            description=description,
            visibility=visibility
        )
        
        if visibility in ["PUBLIC", "FRIENDS", "UNLISTED"]:
            from .util import send_entry_to_remote_followers
            print("sending entry to remote followers")
            send_entry_to_remote_followers(entry, request)
            print(request.get_host())
        
        return redirect('wiki:entry_detail',author_serial=author.serial, entry_serial=entry.serial)

    return render(request, 'create_entry.html')

def entry_detail(request, author_serial, entry_serial):
    entry = get_object_or_404(Entry, serial=entry_serial)
    is_owner = (entry.author.user == request.user)
    current_author = get_object_or_404(Author, serial=author_serial)
    

    is_friend = False
    if current_author:  # if the current user is authenticated, check if they are friends with the entry author
        is_friend = AuthorFriend.objects.filter(
            Q(friending=current_author, friended=entry.author) |
            Q(friending=entry.author, friended=current_author)
        ).exists()

    # if entry is FRIENDS and user is not the owner or a friend, return 403
    if entry.visibility == 'FRIENDS' and not (is_owner or (request.user.is_authenticated and is_friend)):
        if not request.user.is_authenticated:
            return HttpResponse("This entry is private. You must log in to view it.", status=403)
        else:
            return HttpResponse("This entry is private. You are not allowed to view it.", status=403)
    comments = entry.comments.filter(is_deleted=False).order_by('created_at')
    #return render(request, 'entry_detail.html', {'entry': entry, 'is_owner': is_owner, 'comments': comments})
    if entry.contentType == "text/markdown":
        rendered_content = mark_safe(markdown.markdown(entry.content))
    else:
        rendered_content = entry.content

    return render(
        request,
        'entry_detail.html',
        {
            'entry': entry,
            'rendered_content': rendered_content,
            'is_owner': is_owner,
            'comments': comments
        }, status=status.HTTP_200_OK
    )

@login_required
def edit_entry(request, entry_serial):
    entry = get_object_or_404(Entry, serial=entry_serial)
    author = get_object_or_404(Author, serial=entry.author.serial)
    author_serial=entry.author.serial
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        content_type = request.POST.get('contentType')
        visibility = request.POST.get('visibility')
        image = request.FILES.get('image')
        if visibility in dict(Entry.VISIBILITY_CHOICES):
            entry.visibility = visibility
        if (title and content) or (title and image):
            entry.title = title
            if image:
                image_data = image.read()            
                encoded = base64.b64encode(image_data).decode('utf-8')
                if image.content_type == 'image/png':
                    entry.contentType = 'image/png;base64'
                elif image.content_type == 'image/jpeg':
                    entry.contentType = 'image/jpeg;base64'
                else:
                    entry.contentType = 'application/base64'
                entry.content = encoded
            elif content:
                entry.content = content
                entry.contentType = content_type

            entry.save()
            #post to remote followers/friends
            from .util import send_entry_to_remote_followers
            print("sending entry to remote followers")
            send_entry_to_remote_followers(entry, request)
            
            #print(entry.serial)
            return redirect('wiki:entry_detail', author_serial=author_serial, entry_serial=entry.serial)
        else:
            return HttpResponse("Either text content or an image is required.")
        
        
    return render(request, 'edit_entry.html', {'entry': entry})


@login_required
def delete_entry(request, entry_serial):
    entry = get_object_or_404(Entry, serial=entry_serial, author__user=request.user)
    author = get_object_or_404(Author, serial=entry.author.serial)
    if request.method == 'POST':
        entry.delete() 
        #post to remote followers/friends
        
        messages.success(request, "Entry deleted successfully.")
        return redirect('wiki:user-wiki', username=request.user.username)
    
    return render(request, 'confirm_delete.html', {'entry': entry, 'author':author})


@api_view(['GET', 'PUT', 'DELETE'])
def entry_detail_api(request, entry_serial, author_serial):
    """
    GET /api/authors/<author_serial>/entries/<entry_serial>/ — View a single entry
    
    PUT /api/authors/<author_serial>/entries/<entry_serial>/ — Update a single entry (only by the author)
    """

    entry = get_object_or_404(Entry, serial=entry_serial)
    current_author = get_object_or_404(Author, user=request.user)
    author_in_request = get_object_or_404(Author, serial=author_serial)
    
   #checks if the current author isn't the one getting the entry information, if so there will be visibility restrictions
    if current_author!= author_in_request:
        
        if entry.visibility == "PUBLIC":
            pass
        
        elif entry.visibility=="FRIENDS" and not current_author.is_friends_with(author_in_request):
            return Response({
                "error": "You are not friends with this author, you cannot view this entry"
            }, status=status.HTTP_403_FORBIDDEN)
            
        elif entry.visibility=="UNLISTED" and not current_author.is_following(author_in_request):
            return Response({
                "error": "You are not following this author, you cannot view this entry"
            }, status=status.HTTP_403_FORBIDDEN)
   

    if request.method == 'GET':
        serializer = EntrySerializer(entry, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
        

    elif request.method == 'PUT':
        serializer = EntrySerializer(entry, data=request.data, partial=True, context={"request": request})  
        if serializer and serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        if current_author!=entry.author:
            return Response({
                "error": "You are not authorized to delete this entry."
            })
        try:
            entry.delete()
            deleted_entry = Entry._base_manager.get(serial=entry_serial, is_deleted=True)
            deleted_entry.visibility='DELETED'
            serializer = EntrySerializer(deleted_entry, context={"request": request})
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@login_required
@api_view(['GET'])
def entry_detail_fqid_api(request, entry_fqid):
    """
    GET /api/authors/<author_serial>/entries/<entry_serial>/ — View a single entry
    
    """

    decoded_entry_fqid = urllib.parse.unquote(entry_fqid)
    entry = get_object_or_404(Entry, id=decoded_entry_fqid)
    current_author = get_object_or_404(Author, user=request.user)
    author_id = entry.author.id
    entry_author=get_object_or_404(Author, id=author_id)
    
   #checks if the current author isn't the one getting the entry information, if so there will be visibility restrictions
    if current_author == entry_author:
        pass
    else:
        if entry.visibility == "PUBLIC":
            pass
        
        elif entry.visibility=="FRIENDS" and not current_author.is_friends_with(entry_author):
            return Response({
                "error": "You are not friends with this author, you cannot view this entry"
            }, status=status.HTTP_403_FORBIDDEN)
            
        elif entry.visibility=="UNLISTED" and not current_author.is_following(entry_author):
            return Response({
                "error": "You are not following this author, you cannot view this entry"
            }, status=status.HTTP_403_FORBIDDEN)
   

    if request.method == 'GET':
        serializer = EntrySerializer(entry, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
        

    elif request.method == 'PUT':
        serializer = EntrySerializer(entry, data=request.data, partial=True, context={"request": request})  
        if serializer and serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        if current_author!=entry.author:
            return Response({
                "error": "You are not authorized to delete this entry."
            })
        try:
            entry.delete()
            deleted_entry = Entry._base_manager.get(serial=entry.serial, is_deleted=True)
            deleted_entry.visibility='DELETED'
            serializer = EntrySerializer(deleted_entry, context={"request": request})
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
@require_POST
@login_required
def add_comment(request, entry_serial):
    """
    Add a comment to an entry.
    """
    entry = get_object_or_404(Entry, serial=entry_serial)
    author = get_object_or_404(Author, user=request.user)
    content = request.POST.get('content', '').strip()
    
    if content:
        comment = Comment.objects.create(
            entry=entry,
            author=author,
            content=content
        )
        
        # Send comment to entry author's inbox
        send_comment_to_entry_author(comment, request)
    
    return redirect('wiki:entry_detail', author_serial=entry.author.serial, entry_serial=entry_serial)



@require_POST
@login_required
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    author = Author.objects.get(user=request.user)
    like, created = CommentLike.objects.get_or_create(comment=comment, user=author)

    if created:
        # Send comment like to comment author's inbox
        send_comment_like_to_comment_author(like, request)

    if not created:
        like.delete()  # Toggle like off


    return redirect('wiki:entry_detail', author_serial=comment.entry.author.serial, entry_serial=comment.entry.serial)




@api_view(['POST'])
def like_entry_api(request, entry_serial):
    """
    POST /api/entry/{entry_serial}/like/
    Like an entry via API.

    WHEN
    - Show appreciation for an entry
    - User Story 1.1 in Comments/Likes
  
    HOW
    1. send a POST request to /api/entry/{entry_serial}/like/

    WHY
    - Provide a way for authors to show appreciation for content
    - social interaction between users

    WHY NOT
    - Dont use if the entry doesn't exist
    - If you dont appreciate the entry

    Request Fields:
        None

    Response Fields:
        status (string): Status of the like attempt. "liked" or "already_liked"
            - Example: "liked"
            - Purpose: Indicates the result of the like attempt.
        message (string): A user-friendly description of the result.
            - Example: "Entry liked successfully"
            - Purpose: Displays status in the UI.
        likes_count (integer): Total number of likes the entry has.
            - Example: 8
            - Purpose: To understand how many likes the entry has.

    Example Usage:

        # Example 1: Liking an entry
        POST /api/entry/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763/like/
        Authorization: Token abc123

        Response:
        {
            "status": "liked",
            "message": "Entry liked successfully",
            "likes_count": 8
        }

        # Example 2: Trying to like an already liked entry
        POST /api/entry/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763/like/
        Authorization: Token abc123

        Response:
        {
            "status": "already_liked",
            "message": "You have already liked this entry",
            "likes_count": 8
        }
    """
    entry = get_object_or_404(Entry, serial=entry_serial)
    current_author = get_object_or_404(Author, user=request.user)
    author_in_request = get_object_or_404(Author, id=entry.author.id)
    
   #checks if the current author isn't the one getting the entry information, if so there will be visibility restrictions
    if current_author!= author_in_request:
        
        if entry.visibility == "PUBLIC":
            pass
        
        elif entry.visibility=="FRIENDS" and not current_author.is_friends_with(author_in_request):
            return Response({
                "error": "You are not friends with this author, you cannot view this entry"
            }, status=status.HTTP_403_FORBIDDEN)
            
        elif entry.visibility=="UNLISTED" and not current_author.is_following(author_in_request):
            return Response({
                "error": "You are not following this author, you cannot view this entry"
            }, status=status.HTTP_403_FORBIDDEN)
    
    like, created = Like.objects.get_or_create(entry=entry, user=current_author)
    
    if created:
        # Send like to entry author's inbox if remote
        send_entry_like_to_entry_author(like, request)
        
        # Return the properly formatted like object
        serializer = LikeSummarySerializer(like, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response({
            "error": "Entry already liked"
        }, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
def like_comment_api(request, comment_id):
    """
    POST /api/comment/{comment_id}/like/
    User Story 1.3 in Comments/Likes

    WHEN
    - Show appreciation for a comment
    - User Story 1.3 in Comments/Likes
   
    HOW
    1. Ensure the user is authenticated
    2. Send a POST request to /api/comment/{comment_id}/like/

    WHY
    - Provide a way for authors to show appreciation for comments
    - Social interaction between users

    WHY NOT
    - Don't use if the comment doesn't exist
    - If you don't appreciate the comment

    Request Fields:
        None

    Response Fields:
        Returns the complete like object in the required format
    """
    comment = get_object_or_404(Comment, id=comment_id)
    author = get_object_or_404(Author, user=request.user)
    
    like, created = CommentLike.objects.get_or_create(comment=comment, user=author)
    
    if created:
        # Send comment like to comment author's inbox
        send_comment_like_to_comment_author(like, request)
        
        # Return the properly formatted like object
        serializer = CommentLikeSummarySerializer(like, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response({
            "error": "Comment already liked"
        }, status=status.HTTP_400_BAD_REQUEST)
        
@login_required
@api_view(['GET'])
def get_entry_likes_api(request, author_serial, entry_serial):
    """
    GET /api/entry/{entry_serial}/likes/
    User Story 1.4 in Comments/Likes

    WHEN
    - View how many people have liked a public entry
    - User Story 1.4 in Comments/Likes
   
    HOW
    1. Send a GET request to /api/entry/{entry_serial}/likes/

    WHY
    - See who appreciates an entry 

    WHY NOT
    - Dont use if the entry doesn't exist

    Request Fields:
        None

    Example Usage:

        # Example 1: Getting likes for a public entry
        GET 'api/authors/{author_serial}/entry/<uuid:entry_serial>/likes/

Response:
{
 
    "type": "likes",
    "web": "http://authors/201fc5b1-38f8-451d-8807-fbe326fd0f5e/entries/5a720bf2-3d55-4007-a5e7-3dcf9eabdc4b",
    "id": "http://127.0.0.1:8000/entry/5a720bf2-3d55-4007-a5e7-3dcf9eabdc4b/likes",
    "page_number": 1,
    "size": 50,
    "count": 4,
    "src": [
        {
            "type": "like",
            "author": {
                "type": "author",
                "id": "http://127.0.0.1:8000/api/authors/f802fa6a-c7e5-40e5-907f-6ff25b63ff80",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "AB",
                "web": "http://127.0.0.1:8000/authors/f802fa6a-c7e5-40e5-907f-6ff25b63ff80",
                "github": null,
                "profileImage": "/media/profile_images/90s_background_e8A8ndq.jpg"
            },
            "published": "2025-07-10T11:56:34+00:00",
            "id": "http://localhost/api/authors/f802fa6a-c7e5-40e5-907f-6ff25b63ff80/liked/43",
            "object": "http://localhost/api/authors/201fc5b1-38f8-451d-8807-fbe326fd0f5e/entries/5a720bf2-3d55-4007-a5e7-3dcf9eabdc4b"
        },
        {
            "type": "like",
            "author": {
                "type": "author",
                "id": "http://127.0.0.1:8000/api/authors/e025f287-059d-47ae-8201-e6be03082102",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "author_2",
                "web": "http://127.0.0.1:8000/authors/e025f287-059d-47ae-8201-e6be03082102",
                "github": null,
                "profileImage": "/media/profile_images/90s_background.jpg"
            },
            "published": "2025-07-10T05:15:36+00:00",
            "id": "http://localhost/api/authors/e025f287-059d-47ae-8201-e6be03082102/liked/33",
            "object": "http://localhost/api/authors/201fc5b1-38f8-451d-8807-fbe326fd0f5e/entries/5a720bf2-3d55-4007-a5e7-3dcf9eabdc4b"
        }
       }
     ]
    }

    """
    entry = get_object_or_404(Entry, serial=entry_serial)
    serialized_entry = EntrySerializer(entry, context={'request': request})
    current_author = get_object_or_404(Author, user=request.user)
    author_in_request = get_object_or_404(Author, serial=author_serial)
    
    #checks if the current author isn't the one getting the likes information, if so there will be visibility restrictions
    if current_author!= author_in_request:
        
        if entry.visibility == "PUBLIC":
            pass
        
        elif entry.visibility=="FRIENDS" and not current_author.is_friends_with(author_in_request):
            return Response({
                "error": "You are not friends with this author, you cannot view this entry"
            }, status=status.HTTP_403_FORBIDDEN)
            
        elif entry.visibility=="UNLISTED" and not current_author.is_following(author_in_request):
            return Response({
                "error": "You are not following this author, you cannot view this entry"
            }, status=status.HTTP_403_FORBIDDEN)  
    
    # Get all likes for the entry and serialize them
    likes_serialized = serialized_entry.get_likes(entry)
    
    return Response(
        likes_serialized 
    , status=status.HTTP_200_OK)



@api_view(['GET'])
def get_entry_comments_fqid_api(request, entry_fqid):
    """
    GET /api/entries/{ENTRY_FQID}/comments
    Returns comments on the entry (that our server knows about)
    Body is a "comments" object
    """
    # Decode the URL-encoded FQID
    decoded_entry_fqid = urllib.parse.unquote(entry_fqid)
    
    # Find entry by its full URL (FQID)
    entry = get_object_or_404(Entry, id=decoded_entry_fqid)

    # Get the requesting user's author object if authenticated
    requesting_author = None
    if request.user.is_authenticated:
        try:
            requesting_author = Author.objects.get(user=request.user)
        except Author.DoesNotExist:
            pass

    # Visibility check
    if entry.visibility == "FRIENDS":
        if not requesting_author:
            return Response({
                "error": "Authentication required to view friends-only entry comments"
            }, status=status.HTTP_401_UNAUTHORIZED)

        is_friend = AuthorFriend.objects.filter(
            Q(friending=entry.author, friended=requesting_author) |
            Q(friending=requesting_author, friended=entry.author),
            is_deleted=False
        ).exists()

        if not is_friend and entry.author != requesting_author:
            return Response({
                "error": "Only friends can view comments on friends-only entries"
            }, status=status.HTTP_403_FORBIDDEN)

    # Pagination logic
    PAGE_SIZE = 5
    page_number = int(request.GET.get('page', 1))
    offset = (page_number - 1) * PAGE_SIZE
    limit = offset + PAGE_SIZE

    all_comments = entry.comments.filter(is_deleted=False).order_by('-created_at')
    paginated_comments = all_comments[offset:limit]

    serialized_comments = [
        CommentSummarySerializer(comment, context={'request': request}).data
        for comment in paginated_comments
    ]

    # Build the request host for URLs
    request_host = request.build_absolute_uri("/").rstrip("/")
    
    # URL encode the entry FQID for the path
    encoded_entry_fqid = urllib.parse.quote(entry.id, safe='')

    response_data = {
        "type": "comments",
        "web": f"{request_host}/entry/{entry.serial}/",
        "id": f"{request_host}/api/entries/{encoded_entry_fqid}/comments",
        "page_number": page_number,
        "size": PAGE_SIZE,
        "count": all_comments.count(),
        "src": serialized_comments
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_comment_fqid_api(request, author_serial, entry_serial, remote_comment_fqid):
    """
    GET /api/authors/{AUTHOR_SERIAL}/entries/{ENTRY_SERIAL}/comment/{REMOTE_COMMENT_FQID}
    Get a specific comment by its FQID (can be local or remote)
    """
    # Decode the URL-encoded comment FQID
    decoded_comment_fqid = urllib.parse.unquote(remote_comment_fqid)
    
    # First, find the entry
    entry = get_object_or_404(Entry, serial=entry_serial)
    
    # Check if this is a local comment (stored in our database)
    try:
        # Parse the FQID to extract the comment ID
        # FQID format: http://127.0.0.1:8000/api/authors/{author_serial}/commented/{comment_id}
        if decoded_comment_fqid.startswith(f'http://{request.get_host()}/api/authors/'):
            # Extract the comment ID from the FQID
            comment_id = decoded_comment_fqid.split('/commented/')[-1]
            comment = Comment.objects.get(id=comment_id)
            
            # Serialize the local comment
            serialized_comment = CommentSummarySerializer(comment, context={'request': request}).data
            
            return Response(serialized_comment, status=status.HTTP_200_OK)
        else:
            # This might be a remote comment
            return Response({
                "error": "Remote comment fetching not implemented yet."
            }, status=status.HTTP_404_NOT_FOUND)
        
    except (Comment.DoesNotExist, ValueError, IndexError):
        # Comment not found locally or FQID format is invalid
        return Response({
            "error": "Comment not found locally. Remote comment fetching not implemented yet."
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def author_comments_fqid(request, author_fqid):
    """
    GET /api/authors/{AUTHOR_FQID}/commented
    Get the list of comments author has made on any entry (that local node knows about)
    Returns a comments object
    """
    # Decode the URL-encoded author FQID
    decoded_author_fqid = urllib.parse.unquote(author_fqid)
    

    # Extract the author serial from the FQID
    author_serial = decoded_author_fqid.split('/api/authors/')[-1].rstrip('/')
    
    try:
        # Find the author by serial
        author = Author.objects.get(serial=author_serial)
        
        # Get all comments by this author
        all_comments = Comment.objects.filter(author=author, is_deleted=False).order_by('-created_at')
        
        # Pagination logic
        PAGE_SIZE = 5
        page_number = int(request.GET.get('page', 1))
        offset = (page_number - 1) * PAGE_SIZE
        limit = offset + PAGE_SIZE
        
        paginated_comments = all_comments[offset:limit]
        
        serialized_comments = [
            CommentSummarySerializer(comment, context={'request': request}).data
            for comment in paginated_comments
        ]
        
        # Build the request host for URLs
        request_host = request.build_absolute_uri("").rstrip("/")
        
        response_data = {
            "type": "comments",
            "web": f"{request_host}/authors/{author.serial}",
            "id": f"{request_host}/api/authors/{author.serial}/commented/",
            "page_number": page_number,
            "size": PAGE_SIZE,
            "count": all_comments.count(),
            "src": serialized_comments
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Author.DoesNotExist:
        return Response({
            "error": "Author not found"
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_entry_comments_api(request, author_serial, entry_serial):
    entry = get_object_or_404(Entry, serial=entry_serial)

    # Get the requesting user's author object if authenticated
    requesting_author = None
    if request.user.is_authenticated:
        try:
            requesting_author = Author.objects.get(user=request.user)
        except Author.DoesNotExist:
            pass

    # Visibility check
    if entry.visibility == "FRIENDS":
        if not requesting_author:
            return Response({
                "error": "Authentication required to view friends-only entry comments"
            }, status=status.HTTP_401_UNAUTHORIZED)

        is_friend = AuthorFriend.objects.filter(
            Q(friending=entry.author, friended=requesting_author) |
            Q(friending=requesting_author, friended=entry.author),
            is_deleted=False
        ).exists()

        if not is_friend and entry.author != requesting_author:
            return Response({
                "error": "Only friends can view comments on friends-only entries"
            }, status=status.HTTP_403_FORBIDDEN)

    # Pagination logic
    PAGE_SIZE = 5
    page_number = int(request.GET.get('page', 1))
    offset = (page_number - 1) * PAGE_SIZE
    limit = offset + PAGE_SIZE

    all_comments = entry.comments.filter(is_deleted=False).order_by('-created_at')
    paginated_comments = all_comments[offset:limit]

    serialized_comments = [
        CommentSummarySerializer(comment, context={'request': request}).data
        for comment in paginated_comments
    ]

    response_data = {
        "type": "comments",
        "web": entry.web,
        "id": f"{entry.web}/comments",
        "page_number": page_number,
        "size": PAGE_SIZE,
        "count": all_comments.count(),
        "src": serialized_comments
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def get_author_comments_api(request, author_serial):

    if request.method == 'POST':
        # Get the authenticated user's author object
        authenticated_author = get_object_or_404(Author, user=request.user)
        
        # Validate that the request contains a comment object
        if not isinstance(request.data, dict):
            return Response({
                "error": "Request must contain a comment object"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the object type is "comment"
        if request.data.get('type') != 'comment':
            return Response({
                "error": "Object type must be 'comment'"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get comment content
        content = request.data.get('comment', '').strip()
        if not content:
            return Response({
                "error": "Comment content is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get content type (default to text/plain if not provided)
        content_type = request.data.get('contentType', 'text/plain')
        
        # Get the entry ID from the request body
        entry_id = request.data.get('entry')
        if not entry_id:
            return Response({
                "error": "Entry ID is required in the comment object"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find the entry
        try:
            entry = Entry.objects.get(serial=entry_id)
        except Entry.DoesNotExist:
            return Response({
                "error": "Entry not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if the authenticated user can comment on this entry
        if entry.visibility == "FRIENDS":
            is_friend = AuthorFriend.objects.filter(
                Q(friending=entry.author, friended=authenticated_author) |
                Q(friending=authenticated_author, friended=entry.author),
                is_deleted=False
            ).exists()
            if not is_friend and entry.author != authenticated_author:
                return Response({
                    "error": "You can only comment on friends-only entries if you are friends with the author"
                }, status=status.HTTP_403_FORBIDDEN)
        elif entry.visibility == "UNLISTED":
            is_following = AuthorFollowing.objects.filter(
                follower=authenticated_author,
                following=entry.author,
                is_deleted=False
            ).exists()
            if not is_following and entry.author != authenticated_author:
                return Response({
                    "error": "You can only comment on unlisted entries if you are following the author"
                }, status=status.HTTP_403_FORBIDDEN)
        
        comment = Comment.objects.create(
            entry=entry,
            author=authenticated_author,
            content=content,
            contentType=content_type
        )
        
        # Send comment to entry author's inbox
        send_comment_to_entry_author(comment, request)
        
        # Return the properly formatted comment object
        serializer = CommentSummarySerializer(comment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    if request.method == 'GET':
        author = get_object_or_404(Author, serial=author_serial)
        
        # Get the requesting user's author object if authenticated
        requesting_author = None
        if request.user.is_authenticated:
            try:
                requesting_author = Author.objects.get(user=request.user)
            except Author.DoesNotExist:
                pass
        
        # Get all comments by this author
        all_comments = Comment.objects.filter(author=author, is_deleted=False)
        
        # Filter comments based on entry visibility
        visible_comments = []
        for comment in all_comments:
            entry = comment.entry
            
            # Skip deleted entries
            if entry.is_deleted:
                continue
                
            # Check visibility permissions
            if entry.visibility == "PUBLIC":
                visible_comments.append(comment)
            elif entry.visibility == "FRIENDS":
                if requesting_author and (entry.author == requesting_author or 
                    AuthorFriend.objects.filter(
                        Q(friending=entry.author, friended=requesting_author) |
                        Q(friending=requesting_author, friended=entry.author),
                        is_deleted=False
                    ).exists()):
                    visible_comments.append(comment)
            elif entry.visibility == "UNLISTED":
                if requesting_author and (entry.author == requesting_author or 
                    AuthorFollowing.objects.filter(
                        follower=requesting_author, 
                        following=entry.author,
                        is_deleted=False
                    ).exists()):
                    visible_comments.append(comment)
        
        # Sort comments by creation date (newest first)
        visible_comments.sort(key=lambda x: x.created_at, reverse=True)
        
        # Pagination logic
        PAGE_SIZE = 5
        page_number = int(request.GET.get('page', 1))
        offset = (page_number - 1) * PAGE_SIZE
        limit = offset + PAGE_SIZE
        
        paginated_comments = visible_comments[offset:limit]
        
        # Serialize comments
        serialized_comments = [
            CommentSummarySerializer(comment, context={'request': request}).data
            for comment in paginated_comments
        ]
        
        # Build response
        request_host = request.build_absolute_uri('/')[:-1] if request else 'http://localhost:8000'
        
        response_data = {
            "type": "comments",
            "web": f"{request_host}/authors/{author_serial}/commented",
            "id": f"{request_host}/api/authors/{author_serial}/commented",
            "page_number": page_number,
            "size": PAGE_SIZE,
            "count": len(visible_comments),
            "src": serialized_comments
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_entry_image_api(request, entry_fqid):
    pass
#     entry_fqid = unquote(entry_fqid) 
#     entry = None
#     try:
#         entry = Entry.objects.get(id=entry_fqid)
#     except Entry.DoesNotExist:
#         pass
    
#     # REMOTE
#     if entry is None:
#         try:
#             response = requests.get(entry_fqid, headers={"Accept": "application/json"})
#             if response.status_code != 200:
#                 return HttpResponse("Entry not found or remote entry does not exist.", status=404)
            
#             try:
#                 data = response.json()
#             except Exception:
#                 return HttpResponse(f"Remote did not return valid JSON: {response.text}", status=502)
#             content_type = data.get("contentType", "")
#             content = data.get("content", "")
#             if not content_type.startswith('image/'):
#                 return HttpResponse("Content is not an image.", status=400)
#             image_data = base64.b64decode(content)
#             return HttpResponse(image_data, content_type=content_type)
#         except Exception as e:
#             print("Response content:", response.text)
#             print("Content-Type:", response.headers.get("Content-Type"))
#             return HttpResponse(f"Error fetching remote entry: {str(e)}", status=500)
        
#     # LOCAL
#     if not entry.contentType.startswith('image/'):
#         return HttpResponse("Content is not an image.", status=400)
#     try:
#         image_data = base64.b64decode(entry.content)
#         return HttpResponse(image_data, content_type=entry.contentType)
#     except Exception as e:
#         return HttpResponse(f"Error decoding image data: {str(e)}", status=500)

@api_view(['GET'])
def get_author_image_api(request, author_serial, entry_serial):
    author = get_object_or_404(Author, serial=author_serial)
    entry = get_object_or_404(Entry, serial=entry_serial, author=author)
    if not entry.content:
        return HttpResponse("No image available for this entry.", status=404)
        
    content_type = entry.contentType.split(";")[0]
    # Determine MIME type from contentType
    if entry.contentType.startswith('image/png'):
        mime_type = 'image/png'
    elif entry.contentType.startswith('image/jpeg'):
        mime_type = 'image/jpeg'
    else:
        mime_type = 'application/octet-stream'  # fallback

    # Decode the base64 image data
    try:
        image_data = base64.b64decode(entry.content)
    except Exception:
        return HttpResponse("Failed to decode image.", status=500)

    # Return as binary response
    return HttpResponse(image_data, content_type=mime_type)
    

@api_view(['GET'])
def get_author_likes_api(request, author_serial):
    author = get_object_or_404(Author, serial=author_serial)
    
    # Get all likes by this author (both entry likes and comment likes)
    entry_likes = Like.objects.filter(user=author, is_deleted=False)
    comment_likes = CommentLike.objects.filter(user=author, is_deleted=False)
    
    # Serialize the likes
    likes_data = []
    
    # Add entry likes
    for like in entry_likes:
        likes_data.append(LikeSummarySerializer(like, context={'request': request}).data)
    
    # Add comment likes
    for like in comment_likes:
        likes_data.append(CommentLikeSummarySerializer(like, context={'request': request}).data)
    
    # Sort by creation date (most recent first)
    likes_data.sort(key=lambda x: x.get('published', ''), reverse=True)
    
    return Response({
        "type": "likes",
        "web": f"{author.web}",
        "id": f"{author.id}/liked",
        "page_number": 1,
        "size": 50,
        "count": len(likes_data),
        "src": likes_data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_single_like_api(request, author_serial, like_serial):
    author = get_object_or_404(Author, serial=author_serial)
    
    # Try to find the like in both entry likes and comment likes
    entry_like = Like.objects.filter(user=author, id=like_serial, is_deleted=False).first()
    comment_like = CommentLike.objects.filter(user=author, id=like_serial, is_deleted=False).first()
    
    if entry_like:
        # Return entry like
        return Response(LikeSummarySerializer(entry_like, context={'request': request}).data, status=status.HTTP_200_OK)
    elif comment_like:
        # Return comment like
        return Response(CommentLikeSummarySerializer(comment_like, context={'request': request}).data, status=status.HTTP_200_OK)
    else:
        return Response({
            "error": "Like not found"
        }, status=status.HTTP_404_NOT_FOUND)
    

@api_view(['GET'])
def get_comment_fqid(request, comment_fqid):
    """
    Get a single comment by its FQID.
    URL: /api/commented/{COMMENT_FQID}
    """
    # URL decode the FQID
    decoded_comment_fqid = urllib.parse.unquote(comment_fqid)
    
    print(f"DEBUG: Received comment FQID: {decoded_comment_fqid}")
    
    # Parse the FQID to extract the comment ID
    # FQID format: http://{host}/api/authors/{author_serial}/entries/{entry_serial}/comments/{comment_id}
    # or http://127.0.0.1:8000/api/authors/{author_serial}/entries/{entry_serial}/comments/{comment_id}
    if (decoded_comment_fqid.startswith(f'http://{request.get_host()}/api/authors/') or 
        decoded_comment_fqid.startswith('http://127.0.0.1:8000/api/authors/')):
        
        # Extract the comment ID from the FQID
        # Split by '/comments/' and take the last part
        if '/comments/' in decoded_comment_fqid:
            comment_id = decoded_comment_fqid.split('/comments/')[-1].rstrip('/')
            
            print(f"DEBUG: Extracted comment ID: {comment_id}")
            
            try:
                # Find the comment by ID
                comment = Comment.objects.get(id=comment_id)
                
                # Serialize the comment
                serializer = CommentSummarySerializer(comment, context={'request': request})
                
                return Response(serializer.data, status=status.HTTP_200_OK)
                
            except Comment.DoesNotExist:
                return Response({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"error": f"Error fetching comment: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"error": "Invalid comment FQID format."}, status=status.HTTP_400_BAD_REQUEST)
    else:
        # Handle remote comments (not implemented yet)
        return Response({"error": "Remote comment fetching not implemented yet."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_single_comment_fqid(request, comment_fqid):
    """
    Get a single comment by its FQID.
    """
    # URL decode the FQID
    decoded_comment_fqid = urllib.parse.unquote(comment_fqid)
    
    # Parse the FQID to extract the comment ID
    
    # Extract the comment ID from the FQID

    if '/commented/' in decoded_comment_fqid:
        comment_id = decoded_comment_fqid.split('/commented/')[-1].rstrip('/')
    else:
        return Response({"error": "Invalid comment FQID format."}, status=status.HTTP_400_BAD_REQUEST)
    

    
    try:
        # Find the comment by ID
        comment = Comment.objects.get(id=comment_id)
        
        # Serialize the comment
        serializer = CommentSummarySerializer(comment, context={'request': request})
        
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Comment.DoesNotExist:
        return Response({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": f"Error fetching comment: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_author_comment_by_serial(request, author_serial, comment_serial):
    """
    Get a single comment by author serial and comment serial.
    URL: /api/authors/{AUTHOR_SERIAL}/commented/{COMMENT_SERIAL}
    """
    
    try:
        # Find the author by serial
        author = Author.objects.get(serial=author_serial)
        
        # Find the comment by serial (assuming comment has a serial field)
        # If comment doesn't have a serial field, we'll use the ID
        try:
            comment = Comment.objects.get(id=comment_serial, author=author)
        except Comment.DoesNotExist:
            return Response({"error": "Comment not found for this author."}, status=status.HTTP_404_NOT_FOUND)
        
        # Serialize the comment
        serializer = CommentSummarySerializer(comment, context={'request': request})
        
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Author.DoesNotExist:
        return Response({"error": "Author not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": f"Error fetching comment: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
def get_entry_likes_by_fqid(request, entry_fqid):
    """
    Get all likes for an entry by its FQID.
    URL: /api/entries/{ENTRY_FQID}/likes
    "Who Liked This Entry"
    """
    # URL decode the FQID
    decoded_entry_fqid = urllib.parse.unquote(entry_fqid)
    
    print(f"DEBUG: Received entry FQID: {decoded_entry_fqid}")

    if '/entries/' in decoded_entry_fqid:
        entry_serial = decoded_entry_fqid.split('/entries/')[-1].rstrip('/')
        
        print(f"DEBUG: Extracted entry serial: {entry_serial}")
        
        try:
            # Find the entry by serial
            entry = Entry.objects.get(serial=entry_serial)
            
            # Get all likes for this entry
            likes = Like.objects.filter(entry=entry, is_deleted=False).order_by('-created_at')
            
            # Pagination logic
            PAGE_SIZE = 5
            page_number = int(request.GET.get('page', 1))
            offset = (page_number - 1) * PAGE_SIZE
            limit = offset + PAGE_SIZE
            
            paginated_likes = likes[offset:limit]
            
            serialized_likes = [
                LikeSummarySerializer(like, context={'request': request}).data
                for like in paginated_likes
            ]
            
            # Build the request host for URLs
            request_host = request.build_absolute_uri("/").rstrip("/")

            response_data = {
                "type": "likes",
                "web": f"{request_host}/entries/{entry.serial}",
                "id": f"{request_host}/api/entries/{entry.serial}/likes",
                "page_number": page_number,
                "size": PAGE_SIZE,
                "count": likes.count(),
                "src": serialized_likes
            }
                
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Entry.DoesNotExist:
            return Response({"error": "Entry not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Error fetching likes: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({"error": "Invalid entry FQID format."}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_comment_likes_by_fqid(request, author_serial, entry_serial, comment_fqid):
    """
    Get all likes for a comment by its FQID.
    URL: /api/authors/{AUTHOR_SERIAL}/entries/{ENTRY_SERIAL}/comments/{COMMENT_FQID}/likes
    "Who Liked This Comment"
    """
    # URL decode the FQID
    decoded_comment_fqid = urllib.parse.unquote(comment_fqid)
    
    print(f"DEBUG: Received comment FQID: {decoded_comment_fqid}")
    print(f"DEBUG: Author serial: {author_serial}, Entry serial: {entry_serial}")
    

    # Extract the comment ID from the FQID
    # Split by '/comments/' or '/commented/' and take the last part
    if '/comments/' in decoded_comment_fqid:
        comment_id = decoded_comment_fqid.split('/comments/')[-1].rstrip('/')
    elif '/commented/' in decoded_comment_fqid:
        comment_id = decoded_comment_fqid.split('/commented/')[-1].rstrip('/')
    else:
        return Response({"error": "Invalid comment FQID format."}, status=status.HTTP_400_BAD_REQUEST)
        
    print(f"DEBUG: Extracted comment ID: {comment_id}")
    
    try:
        # Find the comment by ID
        comment = Comment.objects.get(id=comment_id)
        
        # Verify the comment belongs to the specified entry and author
        # Convert to strings for comparison and handle potential None values
        comment_entry_serial = str(comment.entry.serial) if comment.entry else None
        comment_author_serial = str(comment.entry.author.serial) if comment.entry and comment.entry.author else None
        
        print(f"DEBUG: Comment entry serial: {comment_entry_serial}, expected: {entry_serial}")
        print(f"DEBUG: Comment author serial: {comment_author_serial}, expected: {author_serial}")
        print(f"DEBUG: Entry serial lengths: {len(str(comment_entry_serial))} vs {len(str(entry_serial))}")
        print(f"DEBUG: Author serial lengths: {len(str(comment_author_serial))} vs {len(str(author_serial))}")
        print(f"DEBUG: Entry serial match: {comment_entry_serial == entry_serial}")
        print(f"DEBUG: Author serial match: {comment_author_serial == author_serial}")
        
        # Convert both sides to strings for proper comparison
        if str(comment_entry_serial) != str(entry_serial) or str(comment_author_serial) != str(author_serial):
            print(f"DEBUG: Validation failed - values don't match")
            return Response({"error": "Comment does not belong to the specified entry or author."}, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"DEBUG: Validation passed - values match")
        
        # Get all likes for this comment
        likes = CommentLike.objects.filter(comment=comment, is_deleted=False).order_by('-created_at')
        
        # Pagination logic
        PAGE_SIZE = 5
        page_number = int(request.GET.get('page', 1))
        offset = (page_number - 1) * PAGE_SIZE
        limit = offset + PAGE_SIZE
        
        paginated_likes = likes[offset:limit]
        
        serialized_likes = [
            CommentLikeSummarySerializer(like, context={'request': request}).data
            for like in paginated_likes
        ]
        
        # Build the request host for URLs
        request_host = request.build_absolute_uri("/").rstrip("/")
        
        response_data = {
            "type": "likes",
            "web": f"{request_host}/entries/{entry_serial}",
            "id": f"{request_host}/api/authors/{author_serial}/entries/{entry_serial}/comments/{decoded_comment_fqid}/likes",
            "page_number": page_number,
            "size": PAGE_SIZE,
            "count": likes.count(),
            "src": serialized_likes
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Comment.DoesNotExist:
        return Response({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": f"Error fetching comment likes: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_author_likes_by_fqid(request, author_fqid):
    """
    Get all likes by an author using the author's FQID.
    URL: /api/authors/{AUTHOR_FQID}/liked
    "Things Liked By Author"
    """
    # URL decode the FQID
    decoded_author_fqid = urllib.parse.unquote(author_fqid)
    
    print(f"DEBUG: Received author FQID: {decoded_author_fqid}")

    # Extract the author serial from the FQID
    author_serial = decoded_author_fqid.split('/api/authors/')[-1].rstrip('/')
    
    print(f"DEBUG: Extracted author serial: {author_serial}")
    
    try:
        # Find the author by serial
        author = Author.objects.get(serial=author_serial)
        
        # Get all likes by this author (both entry likes and comment likes)
        entry_likes = Like.objects.filter(user=author, is_deleted=False)
        comment_likes = CommentLike.objects.filter(user=author, is_deleted=False)
        
        # Serialize the likes
        likes_data = []
        
        # Add entry likes
        for like in entry_likes:
            likes_data.append(LikeSummarySerializer(like, context={'request': request}).data)
        
        # Add comment likes
        for like in comment_likes:
            likes_data.append(CommentLikeSummarySerializer(like, context={'request': request}).data)
        
        # Sort by creation date (most recent first)
        likes_data.sort(key=lambda x: x.get('published', ''), reverse=True)
        
        # Pagination logic
        PAGE_SIZE = 5
        page_number = int(request.GET.get('page', 1))
        offset = (page_number - 1) * PAGE_SIZE
        limit = offset + PAGE_SIZE
        
        paginated_likes = likes_data[offset:limit]
        
        # Build the request host for URLs
        request_host = request.build_absolute_uri("/").rstrip("/")
        
        response_data = {
            "type": "likes",
            "web": f"{request_host}/authors/{author.serial}",
            "id": f"{request_host}/api/authors/{author.serial}/liked",
            "page_number": page_number,
            "size": PAGE_SIZE,
            "count": len(likes_data),
            "src": paginated_likes
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Author.DoesNotExist:
        return Response({"error": "Author not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": f"Error fetching likes: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_single_like_by_fqid(request, like_fqid):
    """
    Get a single like by its FQID.
    URL: /api/liked/{LIKE_FQID}
    """
    # URL decode the FQID
    decoded_like_fqid = urllib.parse.unquote(like_fqid)
    
    print(f"DEBUG: Received like FQID: {decoded_like_fqid}")
    
    # Extract the like ID from the FQID
    # Split by '/liked/' and take the last part
    if '/liked/' in decoded_like_fqid:
        like_id = decoded_like_fqid.split('/liked/')[-1].rstrip('/')
        
        print(f"DEBUG: Extracted like ID: {like_id}")
        
        try:
            # Try to find the like in both entry likes and comment likes
            entry_like = Like.objects.filter(id=like_id, is_deleted=False).first()
            comment_like = CommentLike.objects.filter(id=like_id, is_deleted=False).first()
            
            if entry_like:
                # Return entry like
                serializer = LikeSummarySerializer(entry_like, context={'request': request})
                return Response(serializer.data, status=status.HTTP_200_OK)
            elif comment_like:
                # Return comment like
                serializer = CommentLikeSummarySerializer(comment_like, context={'request': request})
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Like not found."}, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({"error": f"Error fetching like: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({"error": "Invalid like FQID format."}, status=status.HTTP_400_BAD_REQUEST)



def is_local_url(current_host, url):
    
    url_host = urlparse(url).netloc
    print("CURRENT HOST", current_host)
    return current_host == url_host
     

@api_view(['GET'])
def get_author_entries_api(request, author_serial):
    """
    GET /api/authors/{AUTHOR_SERIAL}/entries/
    
    Get the recent entries from author AUTHOR_SERIAL (paginated)
    
    Authentication scenarios:
    - Not authenticated: only public entries
    - Authenticated locally as author: all entries
    - Authenticated locally as follower of author: public + unlisted entries
    - Authenticated locally as friend of author: all entries
    - Authenticated as remote node: should not happen (entries are sent via inbox)
    
    Query parameters:
    - page: page number (default: 1)
    - size: items per page (default: 10, max: 50)
    """
    from django.core.paginator import Paginator
    
    
    
    # Get the author
    try:
        author = Author.objects.get(serial=author_serial)
    except Author.DoesNotExist:
        return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Get pagination parameters
    page_number = request.GET.get('page', 1)
    page_size = min(int(request.GET.get('size', 10)), 50)  # Cap at 50 items per page
    
    # Get base queryset (exclude deleted entries)
    entries_queryset = Entry.objects.filter(
        author=author,
        is_deleted=False
    ).order_by('-created_at')
    
    # Determine which entries to show based on authentication and relationship
    if not request.user.is_authenticated:
        # Not authenticated: only public entries
        entries_queryset = entries_queryset.filter(visibility='PUBLIC')
        print(f"Unauthenticated user: showing {entries_queryset.count()} public entries")
        
    elif hasattr(request.user, 'author'):
        # Authenticated locally
        current_author = request.user.author
        
        if current_author == author:
            # Authenticated as the author: show all entries
            print(f"Author viewing own entries: showing {entries_queryset.count()} entries")
            
        elif current_author.is_friends_with(author):
            # Authenticated as friend: show all entries
            print(f"Friend viewing entries: showing {entries_queryset.count()} entries")
            
        elif current_author.is_following(author):
            # Authenticated as follower: show public + unlisted entries
            entries_queryset = entries_queryset.filter(
                visibility__in=['PUBLIC', 'UNLISTED']
            )
            print(f"Follower viewing entries: showing {entries_queryset.count()} public/unlisted entries")
            
        else:
            # Authenticated but not related: only public entries
            entries_queryset = entries_queryset.filter(visibility='PUBLIC')
            print(f"Authenticated user viewing entries: showing {entries_queryset.count()} public entries")
    else:
        # Remote node authentication (should not happen for this endpoint)
        return Response(
            {"error": "Remote nodes should not access this endpoint directly"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Paginate the results
    paginator = Paginator(entries_queryset, page_size)
    
    try:
        page_obj = paginator.page(page_number)
    except (ValueError, TypeError):
        return Response({"error": "Invalid page number"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response({"error": "Page not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Serialize the entries
    entries_data = []
    for entry in page_obj:
        serializer = EntrySerializer(entry, context={'request': request})
        entries_data.append(serializer.data)
    
    # Build response
    response_data = {
        "type": "entries",
        "page_number": int(page_number),
        "size": page_size,
        "count": paginator.count,
        "src": entries_data
    }

    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_comment_likes_api(request, author_serial, comment_id):
    """
    GET /api/authors/{AUTHOR_SERIAL}/comments/{COMMENT_ID}/likes/
    
    Get all likes for a specific comment.
    
    Response format:
    {
        "type": "likes",
        "web": "http://nodeaaaa/authors/greg/comments/130/likes",
        "id": "http://nodeaaaa/api/authors/greg/comments/130/likes",
        "page_number": 1,
        "size": 50,
        "count": 5,
        "src": [
            {
                "type": "like",
                "author": {...},
                "published": "2025-01-27T10:30:00+00:00",
                "id": "...",
                "object": "..."
            }
        ]
    }
    """
    # Get the author
    try:
        author = Author.objects.get(serial=author_serial)
    except Author.DoesNotExist:
        return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Get the comment
    try:
        comment = Comment.objects.get(id=comment_id)
    except Comment.DoesNotExist:
        return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Verify the comment belongs to the specified author
    if comment.author != author:
        return Response({"error": "Comment does not belong to the specified author"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get pagination parameters
    page_number = request.GET.get('page', 1)
    page_size = min(int(request.GET.get('size', 50)), 50)  # Cap at 50 items per page
    
    # Get all likes for this comment (exclude deleted likes)
    likes_queryset = CommentLike.objects.filter(
        comment=comment,
        is_deleted=False
    ).order_by('-created_at')
    
    # Paginate the results
    paginator = Paginator(likes_queryset, page_size)
    
    try:
        page_obj = paginator.page(page_number)
    except (ValueError, TypeError):
        return Response({"error": "Invalid page number"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response({"error": "Page not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Serialize the likes
    likes_data = []
    for like in page_obj:
        serializer = CommentLikeSummarySerializer(like, context={'request': request})
        likes_data.append(serializer.data)
    


    # Build response
    host = request.build_absolute_uri('/').rstrip('/')
    response_data = {
        "type": "likes",
        "web": f"{host}/entries/{comment.entry.serial}",
        "id": f"{host}/api/authors/{author_serial}/comments/{comment_id}/likes",
        "page_number": int(page_number),
        "size": page_size,
        "count": paginator.count,
        "src": likes_data
    }
    
    # Add pagination URLs if needed
    if page_obj.has_next():
        response_data["next_url"] = f"?page={page_obj.next_page_number()}&size={page_size}"
    if page_obj.has_previous():
        response_data["previous_url"] = f"?page={page_obj.previous_page_number()}&size={page_size}"
    
    return Response(response_data, status=status.HTTP_200_OK)

