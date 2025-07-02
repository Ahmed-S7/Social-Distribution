from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import viewsets, permissions, status
from .models import Page, Like, RemotePost, Author, AuthorFriend, InboxObjectType,RequestState, FollowRequest, AuthorFollowing, Entry, InboxItem, InboxItem, Comment, CommentLike
from .serializers import PageSerializer, LikeSerializer,AuthorFriendSerializer, AuthorFollowingSerializer, RemotePostSerializer,InboxItemSerializer,AuthorSerializer, FollowRequestSerializer, FollowRequestSerializer, EntrySerializer
from rest_framework.decorators import action, api_view, permission_classes
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
from django.contrib.auth import login
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from .util import validUserName, saveNewAuthor
from urllib.parse import urlparse
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


@api_view(['GET'])
@login_required
def user_wiki(request, username):
    '''Process all of the logic pertaining to a given user's wiki page'''
    
    if request.user.username != username or request.user.is_superuser:
        raise PermissionDenied("You are not allowed to view this page.")
    current_author = get_object_or_404(Author, user=request.user)

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
    if request.accepted_renderer.format == 'json':
        serialized_entries = [{
            "title": entry.title,
            "content": entry.content,
            "author": entry.author.displayName,
            "visibility": entry.visibility,
            "created_at": entry.created_at.isoformat(),
            "serial": str(entry.serial)
        } for entry in entries]
        return Response(serialized_entries)
    return render(request, 'wiki.html', {'entries': entries})



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

    if not created:
        like.delete()  # Toggle like off

    #  Redirect to the entry's author's page if the entry was liked from their page  
    if request.POST.get("liked_from_profile") == "true":
       
        return redirect('wiki:view_external_profile', author_serial=liked_author.serial)
    
    # otherwise go back to the stream
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
        
        if userIsValid and password == confirm_password: 
            
            if User.objects.filter(username__iexact=username).exists():
                return render(request, 'register.html', {'error': 'Username already taken.'})
            
            user = User.objects.create_user(username=username, password=password)
            
            #Save new author or raise an error
            newAuthor = saveNewAuthor(request, user, username, github, profileImage, web=None)
            if newAuthor:
                return redirect('wiki:login') 
            return HttpResponseServerError("Unable to save profile")
        
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
  
    authors = Author.objects.all()
    serializer =AuthorSerializer(authors, many=True) 
    return Response({"type": "authors",
                        "authors":serializer.data})  



@login_required
@api_view(['GET'])
def get_author(request, author_serial):
    """
    Get a specific author in the application
    

    Use: "GET /api/author/{author_serial}"
    
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
    
    """
    # CHANGED FOR TESTING
    author = get_object_or_404(Author, serial=author_serial)
    serializer =AuthorSerializer(author)
    return Response(serializer.data)


@login_required   
@require_GET 
def view_authors(request):
    current_user = request.user
    
    #retrieve all authors except for the current author
    authors = Author.objects.exclude(user=current_user)
    return render(request, 'authors.html', {'authors':authors, 'current_user':current_user})

@require_GET  
def view_external_profile(request, author_serial):
    '''Presents a view of a profile other than the one that is currently logged
    - shows the current user whether they are following, are friends with or can follow the current user
    '''
    profile_viewing = Author.objects.filter(serial=author_serial).first()
    if not profile_viewing:
        return redirect("wiki:view_authors")

    # Still using the if structure
    if profile_viewing:
        logged_in = request.user.is_authenticated
        print(logged_in)
        logged_in_author = Author.objects.filter(user=request.user).first() if logged_in else None
        #NECESSARY FIELDS FOR PROFILE DISPLAY
        is_following = logged_in_author.is_following(profile_viewing)if logged_in_author else False
        followers = profile_viewing.followers.all()#stores all of the followers a given author has
        following = profile_viewing.following.all()#stores all of the followers a given author has
        all_entries = profile_viewing.get_all_entries()#stores all of the user's entries
        is_currently_requesting = logged_in_author.is_already_requesting(profile_viewing)if logged_in_author else False
        is_a_friend = logged_in_author.is_friends_with(profile_viewing)if logged_in_author else False
        friends_a = logged_in_author.friend_a.all()if logged_in_author else Author.objects.none()
        friends_b = logged_in_author.friend_b.all()if logged_in_author else Author.objects.none()
        total_friends = (friends_a | friends_b)

        
        # VISUAL REPRESENTATION TEST
        '''
        print("Entries:", all_entries or None)
        print("followers:", followers or None)
        print("following:", following or None)
        print("Is friends with this account:", is_a_friend)
        print("Is following this account:", is_following)
        '''
        
        # Followed
        followed_ids = AuthorFollowing.objects.filter(
            follower=logged_in_author
        ).values_list('following', flat=True)
        
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
            ~Q(visibility='DELETED'),
        author=profile_viewing
        ).filter(
            Q(visibility='PUBLIC') |
            Q(visibility='FRIENDS', author__in=friend_ids) |
            Q(visibility='UNLISTED', author__id__in=followed_ids)
        )
        
        
        #store existing follow request if it exists
        try:
            
            current_request = FollowRequest.objects.get(requester=logged_in_author.id, requested_account=profile_viewing.id)
            current_request_id = current_request.id
        
        except FollowRequest.DoesNotExist:
            current_request_id = None
        
        #store existing following if it exists 
        following_id = logged_in_author.get_following_id_with(profile_viewing)
        
        
            
        #store existing friendship if it exists 
        friendship_id = logged_in_author.get_friendship_id_with(profile_viewing)
        
        '''#CHECK VALUES
        print("Following ID is:",following_id)
        print("Friendship ID is:",friendship_id)
        print("The current request is:", current_request) 
        print("List of User's Entries:", all_entries)
        '''
       
        
       
        
        
        return render(request, "external_profile.html", 
                      {
                       'author': profile_viewing,
                       'entries': all_entries, 
                       "followers": followers,
                       "follower_count": len(followers),
                       "friend_count": len(total_friends),
                       "is_a_friend": is_a_friend,
                       "is_following": is_following,
                       "following_count": len(following),
                       "entries": all_entries,
                       "entry_count": len(all_entries),
                       "is_a_friend": is_a_friend,
                       "is_currently_requesting":is_currently_requesting,
                       "request_id": current_request_id,
                       "follow_id": following_id,
                       "friendship_id":friendship_id,
                       }
                      )
    else:
        return HttpResponseRedirect("wiki:view_authors")
        
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
    
    
    #retrieve the current follow request
    active_request = get_object_or_404(FollowRequest, id=request_id)
    #print("The request being changed is:", active_request)

    
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
    current_author = get_object_or_404(Author, user=request.user)
    followed_author = get_object_or_404(Author, serial=followed_author_serial)
    
    
    
    
    #retrieve the current follow request
    active_following = get_object_or_404(AuthorFollowing, id=following_id)
   
  
    
    #retrieve the accepted follow request
    active_request=get_object_or_404(FollowRequest, requester = current_author.id, requested_account=followed_author.id)
    
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
    print("Follow Request Deleted:",active_request.is_deleted)
    print("Active Following Deleted:",active_following.is_deleted)
    if active_friendship_id:
        print("Active Friendship Deleted:", active_request.is_deleted)



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
        print("You are only following him")
        base_URL = reverse("wiki:view_external_profile", kwargs={"author_serial": requested_account.serial})
        query_with_follow_status= f"{base_URL}?status=following&user={requested_account}"
        return redirect(query_with_follow_status)
    
    if requesting_account.is_already_requesting(requested_account):
        base_URL = reverse("wiki:view_external_profile", kwargs={"author_serial": requested_account.serial})
        query_with_request_status= f"{base_URL}?status=requesting&user={requested_account}"
        return redirect(query_with_request_status)
            
    try:
        serialized_follow_request = FollowRequestSerializer(
        follow_request, data={
        "type":"follow",
        },partial=True

        )

        # Valid follow requests will lead to an attempted saving of the correspondin respective inbox item
        if serialized_follow_request.is_valid():
            #print("Follow Request serializer is valid")

            # Save follow request to DB
            saved_follow_request = serialized_follow_request.save()

            #make the inbox JSON content
            inbox_content = serialized_follow_request.data     
            newInboxItem = InboxItem(
                    author=requested_account,
                    type=InboxObjectType.FOLLOW,
                    content=inbox_content
            )

            #Try to save the new follow request as an inbox item
            try:
                newInboxItem.save()
                    
                    #Exceptions and structure adjusted using copilot: https://www.bing.com/search?pglt=427&q=copilot&cvid=882b9688f1804581bd4975fbe80acc49&gs_lcrp=EgRlZGdlKgYIABBFGDkyBggAEEUYOTIGCAEQABhAMgYIAhAAGEAyBggDEAAYQDIGCAQQABhAMgYIBRAAGEAyBggGEAAYQDIGCAcQABhAMgYICBAAGEDSAQc5MDJqMGoxqAIAsAIA&FORM=ANNTA1&PC=EDGEDB, "[Adjust the structure of these error messages]", June, 2025
            except Exception as e:
                        saved_follow_request.delete()  # Rollback follow request
                        return HttpResponseServerError(f"Failed to save Inbox Item: {e}")

        else:
            return HttpResponseServerError(f"We were unable to send your follow request: {serialized_follow_request.errors}")

    except Exception as e:
                return HttpResponseServerError(f"Failed to save follow request: {e}")



    if requested_account:
        messages.success(request,f"You have successfully requested to follow {requested_account}! :)")
        return redirect(reverse("wiki:view_external_profile", kwargs={"author_serial": requested_account.serial}))

    else:
        messages.error(request,f"The author you request to follow might not exist :(")
        return redirect(reverse("wiki:view_external_profile", kwargs={"author_serial": requested_account.serial}))
        

        

@login_required
def check_follow_requests(request, username):
    '''Check for all of the follow  requests of a specific author'''
    
    if request.user.is_staff or request.user.is_superuser:
        return HttpResponseServerError("Admins cannot perform author actions. Please user a regular account associated with an Author.")

    requestedAuthor = Author.objects.get(user=request.user)
        
        
    incoming_follow_requests =FollowRequest.objects.filter(requested_account=requestedAuthor, state=RequestState.REQUESTING,is_deleted=False).order_by('-created_at') 
    
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
        
        if new_following_serializer.is_valid():
            try:
                new_following_serializer.save()
            except Exception as e:
                print(e)
                return check_follow_requests(request, request.user.username)

        else:
            
            return HttpResponseServerError(f"Unable to follow Author {new_following.following.displayName}.")
           
        # check if there is now a mutual following
        if follower.is_following(requestedAuthor) and requestedAuthor.is_following(follower):

            #if there is, add these two users as friends using the author friends object
            new_friendship = AuthorFriend(friending=requestedAuthor, friended=follower)
            
            try:
                new_friendship.save()  
                
                
            except Exception as e:
                # Rollback
                #set the follow  request state to requested
                follow_request.set_request_state(RequestState.REQUESTING)
        
                #create a following from requester to requested
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
        
         #Reject the follow request and delete (soft) it 
         follow_request.set_request_state(RequestState.REJECTED)
         
         follow_request.delete()

    return redirect(reverse("wiki:check_follow_requests", kwargs={"username": request.user.username}))





@login_required
@api_view(['GET'])
def get_local_followers(request, author_serial):   
    """
    Get a specific author's followers list requests in the application
    
    Use: "GET /api/authors/{author_serial}/followers/"

    returns Json in the following format: 
         
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
     """
    current_user = request.user  
    
    try: 
        current_author = get_object_or_404(Author, user=current_user)
        requested_author = get_object_or_404(Author,serial=author_serial)   
    except Exception as e:
        return Response({"Error":"User Not Located Within Our System"}, status=status.HTTP_404_NOT_FOUND )
    
    #If the user is local, make sure they're logged in 
    if request.user: 
        
        if requested_author == current_author:
  
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
        else:
            return Response({"error":"user requesting information is not currently logged in, you do not have access to this information"}, status=status.HTTP_401_UNAUTHORIZED )
    else:   
        #for now, all external hosts can make get requests
        followers_list=[]
            
        follower_relations = current_author.followers.all()
            
        if follower_relations:
            for followers in follower_relations:
                print(followers.follower)
                follower = followers.follower
                followers_list.append(follower)
            print(followers_list)
    
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
    
    Use: "GET /api/authors/{author_serial}/inbox/"

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
    if request.user: 
        
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
    else:   
        #for now, all external hosts can make get requests
        all_follow_requests = current_author.get_follow_requests_recieved()
        
        if all_follow_requests:  
            try:
                serialized_follow_requests = FollowRequestSerializer( all_follow_requests, many=True)
                response = serialized_follow_requests.data
                return Response(response, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"Error" : f" We were unable to authenticate the follow requests for this user: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )   
        
        return Response({"type": "follow", "follows":{}}, status=status.HTTP_200_OK)
    
    


def profile_view(request, username):
    """
    View the profile of the currently logged in user.
    """
    try:
        author = Author.objects.get(user__username=username)
    except Author.DoesNotExist:
        return HttpResponse("Author profile does not exist.")
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
    
    
    
    return render(
        request, 'profile.html', 
        {
        'author': author,
        'entries': all_entries,
        "followers": followers,
        "follower_count": len(followers),
        "following": following,
        "following_count": len(following),
        "entries": all_entries,
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
        image_file = request.FILES.get('profileImage')

        # Check if the new username is already taken by someone else
        if new_username and new_username != request.user.username:
            if User.objects.filter(username=new_username).exclude(id=request.user.id).exists():
                return render(request, 'edit_profile.html', {
                    'author': author,
                    'error': 'Username is already taken.'
                })

            request.user.username = new_username
            request.user.save()
            author.displayName = new_username

        author.github = github
        author.description = description

        if image_file:
            author.profileImage = image_file

        author.save()
        return redirect('wiki:profile', username=new_username)

    return render(request, 'edit_profile.html', {'author': author})

@api_view(['PUT', 'GET']) 
def edit_profile_api(request, username):
    """
    GET /api/profile/edit/{username}/
    View the author's profile.

    PUT /api/profile/edit/{username}/
    Edits the author's profile.
    """
    try:
        author = Author.objects.get(user__username=username)
    except Author.DoesNotExist:
        return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        author_data = AuthorSerializer(author).data
        entries = Entry.objects.filter(author=author).order_by('-created_at')
        entry_data = EntrySerializer(entries, many=True).data
        author_data['entries'] = entry_data
        return Response(author_data, status=status.HTTP_200_OK)

    # PUT
    serializer = AuthorSerializer(author, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@login_required
def create_entry(request):
    """
    Create a new wiki entry.
    """
    if request.method == 'POST':
        # Example: get data from POST and save your entry
        title = request.POST.get('title')
        content = request.POST.get('content')
        image = request.FILES.get('image')
        visibility = request.POST.get('visibility')

        if title and content:
            author = get_object_or_404(Author, user=request.user)
            entry = Entry.objects.create(author=author, title=title, content=content, image=image if image else None, visibility=visibility)

            return redirect('wiki:entry_detail', entry_serial=entry.serial)
        else:
            return HttpResponse("Both title and content are required.")
    # GET: Show form to create entry
    return render(request, 'create_entry.html')

def entry_detail(request, entry_serial):
    entry = get_object_or_404(Entry, serial=entry_serial)
    if entry.visibility == 'FRIENDS' and not request.user.is_authenticated:
        return HttpResponse("This entry is private. Please log in to view it.")
    is_owner = (entry.author.user == request.user)
    comments = entry.comments.filter(is_deleted=False).order_by('created_at')
    return render(request, 'entry_detail.html', {'entry': entry, 'is_owner': is_owner, 'comments': comments})

@login_required
def edit_entry(request, entry_serial):
    author = get_object_or_404(Author, user=request.user)
    entry = get_object_or_404(Entry, serial=entry_serial, author=author)
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        image = request.FILES.get('image')
        visibility = request.POST.get('visibility')
        if visibility in dict(Entry.VISIBILITY_CHOICES):
            entry.visibility = visibility
        if title and content:
            entry.title = title
            entry.content = content
            if image:
                entry.image = image
            if request.POST.get('remove_image'):
               entry.image.delete(save=False)
               entry.image = None
            entry.save()
            return redirect('wiki:entry_detail', entry_serial=entry.serial)
        else:
            return HttpResponse("Both title and content are required.")
        
    return render(request, 'edit_entry.html', {'entry': entry})


@login_required
def delete_entry(request, entry_serial):
    entry = get_object_or_404(Entry, serial=entry_serial, author__user=request.user)
    
    if request.method == 'POST':
        entry.delete() 
        messages.success(request, "Entry deleted successfully.")
        return redirect('wiki:user-wiki', username=request.user.username)
    
    return render(request, 'confirm_delete.html', {'entry': entry})

@api_view(['GET', 'PUT'])
def entry_detail_api(request, entry_serial):
    """
    GET /api/entries/<entry_serial>/ — View a single entry
    PUT /api/entries/<entry_serial>/edit/ — Update a single entry (only by the author)
    """
    entry = get_object_or_404(Entry, serial=entry_serial)

    if request.method == 'GET':
        serializer = EntrySerializer(entry)
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = EntrySerializer(entry, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



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
    return redirect('wiki:entry_detail', entry_serial=entry_serial)



@require_POST
@login_required
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    author = Author.objects.get(user=request.user)
    like, created = CommentLike.objects.get_or_create(comment=comment, user=author)

    if not created:
        like.delete()  # Toggle like off


    return redirect('wiki:entry_detail', entry_serial=comment.entry.serial)




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
    author = get_object_or_404(Author, user=request.user)
    
    like, created = Like.objects.get_or_create(entry=entry, user=author)
    
    if created:
        return Response({
            "status": "liked",
            "message": "Entry liked successfully",
            "likes_count": entry.likes.count()
        }, status=status.HTTP_201_CREATED)
    else:
        return Response({
            "status": "already_liked", 
            "message": "You have already liked this entry",
            "likes_count": entry.likes.count()
        }, status=status.HTTP_400_BAD_REQUEST)





@api_view(['POST'])
def add_comment_api(request, entry_serial):
    """
    POST /api/entry/{entry_serial}/comments/
    Add a comment to an entry via API.

    WHEN
    - Add thoughts or feedback to an entry
    - User Story 1.1 in Comments/Likes
   
    HOW
    1. Send a POST request to /api/entry/{entry_serial}/comments/
    2. Include comment content in the request body

    WHY
    - Authors can interact with entries and other Authors

    WHY NOT
    - Don't use if the entry doesn't exist
    - Don't use with empty or whitespace-only content

    Request Fields:
        content (string): The comment text content
            - Example: "Great post! Thanks for sharing."
            - Purpose: The actual comment text to be displayed


    Response Fields:
        status (string): Status of the comment addition
            - Example: "comment_added"
            - Purpose: Indicates the result of the comment attempt.
        message (string): A description of the result.
            - Example: "Comment added successfully"
            - Purpose: Displays status in the UI.
        comment_id (integer): ID for the comment.
            - Example: 123
            - Purpose: Reference the comment for future operations.
        content (string): The comment text that was added.
            - Example: "Great post! Thanks for sharing."
            - Purpose: Confirm the comment content was saved correctly.
        author (string): Display name of the comment author.
            - Example: "test_author2"
            - Purpose: Show who wrote the comment.
        created_at (string): Timestamp when the comment was created.
            - Example: "2024-01-15T10:30:00Z"
            - Purpose: Track when the comment was posted.
        comments_count (integer): Total number of comments on the entry.
            - Example: 5
            - Purpose: Update comment count in the UI.

    Example Usage:

        # Example 1: Adding a comment
        POST /api/entry/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763/comments/
        Authorization: Token abc123
        Content-Type: application/json

        {
            "content": "Great post! Thanks for sharing."
        }

        Response:
        {
            "status": "comment_added",
            "message": "Comment added successfully",
            "comment_id": 123,
            "content": "Great post! Thanks for sharing.",
            "author": "test_author2",
            "created_at": "2024-01-15T10:30:00Z",
            "comments_count": 5
        }

        # Example 2: Trying to add empty comment
        POST /api/entry/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763/comments/
        Authorization: Token abc123
        Content-Type: application/json

        {
            "content": ""
        }

        Response:
        {
            "error": "Comment content is required"
        }
    """
    entry = get_object_or_404(Entry, serial=entry_serial)
    author = get_object_or_404(Author, user=request.user)
    
    content = request.data.get('content', '').strip()
    
    if not content:
        return Response({
            "error": "Comment content is required"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    comment = Comment.objects.create(
        entry=entry,
        author=author,
        content=content
    )
    
    return Response({
        "status": "comment_added",
        "message": "Comment added successfully",
        "comment_id": comment.id,
        "content": comment.content,
        "author": author.displayName,
        "created_at": comment.created_at,
        "comments_count": entry.comments.count()
    }, status=status.HTTP_201_CREATED)


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
        status (string): Status of the like attempt. "liked" or "already_liked"
            - Example: "liked"
            - Purpose: Indicates the result of the like attempt.
        message (string): A user-friendly description of the result.
            - Example: "Comment liked successfully"
            - Purpose: Displays status in the UI.
        likes_count (integer): Total number of likes in the comment
            - Example: 3
            - Purpose: To understand how many likes the comment has.

    Example Usage:

        # Example 1: Liking a comment
        POST /api/comment/123/like/
        Authorization: Token abc123

        Response:
        {
            "status": "liked",
            "message": "Comment liked successfully",
            "likes_count": 3
        }

        # Example 2: Trying to like an already liked comment
        POST /api/comment/123/like/
        Authorization: Token abc123

        Response:
        {
            "status": "already_liked",
            "message": "You have already liked this comment",
            "likes_count": 3
        }
    """
    comment = get_object_or_404(Comment, id=comment_id)
    author = get_object_or_404(Author, user=request.user)
    
    like, created = CommentLike.objects.get_or_create(comment=comment, user=author)
    
    if created:
        return Response({
            "status": "liked",
            "message": "Comment liked successfully",
            "likes_count": comment.likes.count()
        }, status=status.HTTP_201_CREATED)
    else:
        return Response({
            "status": "already_liked", 
            "message": "You have already liked this comment",
            "likes_count": comment.likes.count()
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_entry_likes_api(request, entry_serial):
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

    Response Fields:
        entry_id (string): UUID of the entry
            - Example: "7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763"
            - Purpose: Identify the entry being queried
        entry_title (string): Title of the entry
            - Example: "My Amazing Post"
            - Purpose: Display context for the likes
        total_likes (integer): Total number of likes on the entry
            - Example: 5
            - Purpose: Quick summary of engagement
        likes[] (array): Array of like objects
            - Example: [{"id": 1, "author": {...}}]
            - Purpose: list with detaild of who liked the entry

    Example Usage:

        # Example 1: Getting likes for a public entry
        GET /api/entry/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763/likes/

        Response:
        {
            "entry_id": "7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763",
            "entry_title": "title",
            "total_likes": 2,
            "likes": [
                {
                    "id": 1,
                    "author": {
                        "id": "http://s25-project-white/api/authors/test1",
                        "displayName": "test_author1"
                    }
                },
                {
                    "id": 2,
                    "author": {
                        "id": "http://s25-project-white/api/authors/test2",
                        "displayName": "test_author2"
                    }
                }
            ]
        }

        # Example 2: Getting likes for a friends-only entry
        GET /api/entry/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763/likes/

        Response:
        {
            "error": "Entry is not public"
        }
    """
    entry = get_object_or_404(Entry, serial=entry_serial)
    
    # Check if entry is public
    if entry.visibility != "PUBLIC":
        return Response({
            "error": "Entry is not public"
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get all likes for the entry
    likes = entry.likes.filter(is_deleted=False)
    
    # Serialize the likes
    like_data = []
    for like in likes:
        like_data.append({
            "id": like.id,
            "author": {
                "id": like.user.id,
                "displayName": like.user.displayName
            }
        })
    
    return Response({
        "entry_id": entry.serial,
        "entry_title": entry.title,
        "total_likes": likes.count(),
        "likes": like_data
    }, status=status.HTTP_200_OK)





@api_view(['GET'])
def get_entry_comments_api(request, entry_serial):
    """
    GET /api/entry/{entry_serial}/comments/view/
    Get comments for an entry via API with visibility control.

    WHEN
    - View comments on an entry
    - User Story 1.5 in Comments/Likes
   
    HOW
    1. Send a GET request to /api/entry/{entry_serial}/comments/view/

    WHY
    - Obtain comments from entries

    WHY NOT
    - Don't use for entries you don't have permission to view

    Response Fields:
        entry_id (string): ID of the entry
            - Example: "7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763"
            - Purpose: Identify the entry being queried
        entry_title (string): title of the entry
            - Example: "My Amazing Post"
            - Purpose: Display context for the comments
        entry_visibility (string): Visibility setting of the entry
            - Example: "PUBLIC", "FRIENDS", "UNLISTED"
            - Purpose: Understand entry access level
        total_comments (integer): Total number of visible comments
            - Example: 3
            - Purpose: Quick summary of engagement
        comments (array): Array of comment objects
            - Example: [{"id": 1, "content": "...", "author": {...}}]
            - Purpose: Detailed list of comments

    Example Usage:

        # Example 1: Getting comments on a public entry
        GET /api/entry/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763/comments/view/

        Response:
        {
            "entry_id": "7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763",
            "entry_title": "Title",
            "entry_visibility": "PUBLIC",
            "total_comments": 2,
            "comments": [
                {
                    "id": 1,
                    "content": "idk",
                    "author": {
                        "id": "http://s25-project-white/api/authors/test1",
                        "displayName": "test_author1"
                    },
                    "created_at": "2024-01-15T10:30:00Z"
                },
                {
                    "id": 2,
                    "content": "comment 2",
                    "author": {
                        "id": "http://s25-project-white/api/authors/test2",
                        "displayName": "test_author2"
                    },
                    "created_at": "2024-01-15T11:15:00Z"
                }
            ]
        }

        Example 2: Getting comments on a friends-only entry (non-friend)
        GET /api/entry/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763/comments/view/
        Authorization: Token abc123

        Response:
        {
            "error": "Only frieds can view comments on friends-only entries"
        }
    """
    entry = get_object_or_404(Entry, serial=entry_serial)
    
    # Get the requesting user's author object if authenticated
    requesting_author = None
    if request.user.is_authenticated:
        try:
            requesting_author = Author.objects.get(user=request.user)
        except Author.DoesNotExist:
            pass
    
    # Check visibility permissions
    if entry.visibility == "PUBLIC":
        # Public entries - anyone can view comments
        pass
    elif entry.visibility == "FRIENDS":
        # Friends-only entries - only friends and comment authors can view
        if not requesting_author:
            return Response({
                "error": "Authentication required to view friends-only entry comments"
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if they are friends
        is_friend = AuthorFriend.objects.filter(
            Q(friending=entry.author, friended=requesting_author) |
            Q(friending=requesting_author, friended=entry.author),
            is_deleted=False
        ).exists()
        
        if not is_friend:
            return Response({
                "error": "Only friends can view comments on friends-only entries"
            }, status=status.HTTP_403_FORBIDDEN)
    
    # Get all comments for the entry
    comments = entry.comments.filter(is_deleted=False).order_by('created_at')
    
    # Filter comments based on visibility and friendship
    visible_comments = []
    for comment in comments:
        # Always show comment to its author
        if requesting_author and comment.author == requesting_author:
            visible_comments.append(comment)
            continue
        
        # For friends-only entries, only show comments to friends
        if entry.visibility == "FRIENDS":
            if requesting_author and requesting_author == entry.author:
                # Entry author can see all comments
                visible_comments.append(comment)
            elif requesting_author:
                # Check if comment author is a friend
                is_friend = AuthorFriend.objects.filter(
                    Q(friending=entry.author, friended=comment.author) |
                    Q(friending=comment.author, friended=entry.author),
                    is_deleted=False
                ).exists()
                if is_friend:
                    visible_comments.append(comment)
        else:
            # For public entries, show all comments
            visible_comments.append(comment)
    
    # Serialize the comments
    comment_data = []
    for comment in visible_comments:
        comment_data.append({
            "id": comment.id,
            "content": comment.content,
            "author": {
                "id": comment.author.id,
                "displayName": comment.author.displayName
            },
            "created_at": comment.created_at
        })
    
    return Response({
        "entry_id": entry.serial,
        "entry_title": entry.title,
        "entry_visibility": entry.visibility,
        "total_comments": len(visible_comments),
        "comments": comment_data
    }, status=status.HTTP_200_OK)





