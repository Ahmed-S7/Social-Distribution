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
    current_author = get_object_or_404(Author, user=request.user)

    # Followed
    followed_ids = AuthorFollowing.objects.filter(
        follower=current_author,
        is_deleted=False
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

    # Combine all visible author IDs (yourself + followed + friends)
    visible_author_ids = set(followed_ids) | friend_ids | {current_author.id}

    entries = Entry.objects.filter(
        ~Q(visibility='DELETED') & (
            Q(visibility='PUBLIC') |
            Q(author=current_author) |
            Q(visibility='FRIENDS', author__id__in=friend_ids) |
            Q(author__id__in=followed_ids)
        )
    ).order_by('-created_at')
   
    return render(request, 'wiki.html', {'entries': entries})

    

@require_POST
@login_required
def like_entry(request, entry_serial):
    entry = get_object_or_404(Entry, serial=entry_serial)
    author = Author.objects.get(user=request.user)
    like, created = Like.objects.get_or_create(entry=entry, user=author)

    if not created:
        like.delete()  # Toggle like off

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
    
        Use: "GET /api/authors/"
        
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
    
        Use: "GET /api/author/{author_serial}"
        
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
    # CHANGED FOR TESTING
    author = get_object_or_404(Author, serial=author_serial)
    serializer =AuthorSerializer(author)
    return Response(serializer.data)

    # id = get_author_id(request)
    
    # if is_valid_serial(id):
           
    #     if Author.objects.filter(serial=id).exists():
                
    #         author = Author.objects.get(serial=id)
            
    #         #####FOR DEBUG#######
    #         #print(author)
    #         #####################      
            
    #         serializer = AuthorSerializer()
    #         serializer =AuthorSerializer(author)
    #         return Response(serializer.data)




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
        current_author = get_object_or_404(Author, user=request.user) 
        
        follow_status = current_author.is_following(profile_viewing)
        print(follow_status)
              
        return render(request, "external_profile.html", {"author": profile_viewing, "is_following": follow_status})
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

            if requesting_account.is_already_requesting(requested_account):
                messages.error(request,f"You must really like {requested_account}, but they still need to respond to your follow request.")
                return redirect(reverse("wiki:view_external_profile", kwargs={"author_serial": requested_account.serial}))
            
            if requesting_account.is_following(requested_account):
                messages.error(request,f"You already follow {requested_account}, maybe view their profile?")
                base_URL = reverse("wiki:view_external_profile", kwargs={"author_serial": requested_account.serial})
                query_with_follow_status= f"{base_URL}?is_following=True"
                return redirect(query_with_follow_status)
                
            
            
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
    if requested_account:
        messages.success(request,f"You have successfully requested to follow {requested_account}! :)")
        return redirect(reverse("wiki:view_external_profile", kwargs={"author_serial": requested_account.serial}))

    else:
        messages.error(request,f"The author you request to follow might not exist :(")
        return redirect(reverse("wiki:view_external_profile", kwargs={"author_serial": requested_account.serial}))
        

           

@login_required
def follow_success_page(request, author_serial):
    
    if request.user.is_staff or request.user.is_superuser:
        return HttpResponseServerError("Admins cannot perform author actions. Please user a regular account associated with an Author.")
    requestedAuthor = Author.objects.get(serial=author_serial)
    
    return render(request,"follow_success.html", {'author':requestedAuthor})

@login_required
def check_follow_requests(request, username):
    
        if request.user.is_staff or request.user.is_superuser:
            return HttpResponseServerError("Admins cannot perform author actions. Please user a regular account associated with an Author.")

        requestedAuthor = Author.objects.get(user=request.user)
        
        
        incoming_follow_requests =FollowRequest.objects.filter(requested_account=requestedAuthor, state=RequestState.REQUESTING,is_deleted=False).order_by('-created_at') 
        #print(f"I HAVE {len(incoming_follow_requests)} FOLLOW REQUESTS")
    
        if not incoming_follow_requests:
        
            incoming_follow_requests = []
           

        return render(request, 'follow_requests.html', {'author':requestedAuthor, "follow_requests": incoming_follow_requests})

@csrf_exempt
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
   
    

    return redirect(reverse("wiki:check_follow_requests", kwargs={"username": request.user.username}))


    
    
   
    
    
    
    
    

@api_view(['GET'])
def check_remote_inbox(request):
    pass


def profile_view(request, username):
    """
    View the profile of the currently logged in user.
    """
    try:
        author = Author.objects.get(user__username=username)
    except Author.DoesNotExist:
        return HttpResponse("Author profile does not exist.")
    entries = Entry.objects.filter(author=author).order_by('-created_at')    # displays entries from newest first
    return render(request, 'profile.html', {'author': author, 'entries': entries})

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
        serializer = AuthorSerializer(author)
        return Response(serializer.data, status=status.HTTP_200_OK)

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

@login_required
def entry_detail(request, entry_serial):
    entry = get_object_or_404(Entry, serial=entry_serial)
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
        entry.delete()  # This should soft-delete because of BaseModel
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




