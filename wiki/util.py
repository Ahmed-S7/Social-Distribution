import requests
from .models import Author, Entry, RemoteNode, AuthorFollowing, AuthorFriend, RequestState
from django.http import HttpResponse, Http404
import uuid
from django.shortcuts import redirect
import traceback
from rest_framework.response import Response
from rest_framework import status
import urllib
from urllib.parse import urlparse, unquote
from django.http import Http404, HttpResponseRedirect, HttpResponseServerError, HttpResponse
import traceback
import sys
from django.db.models import Q
from django.urls import reverse
import requests, base64, filetype
from requests.auth import HTTPBasicAuth
from .serializers import AuthorSerializer, EntrySerializer, CommentSummarySerializer, CommentLikeSummarySerializer, LikeSummarySerializer
from .gethub import create_entries
#AUTH TOKEN TO BE USED WITH REQUESTS
#YOU NEED TO HAVE A USER WITH THIS GIVEN AUTH ON THE NODE YOU ARE CONNECTING TO IN ORDER TO BE VALIDATED
#YOU ALSO NEED A NODE CREDENTIALS OBJECT WITH THIS USERNAME AND PASSWORD, THIS IS HOW VALIDATION WILL BE DONE
AUTH =  {"username":"JKIl1PX95JA3UwO8",
        "password":"1Mls9oMrP5FzJSHHyPmQLkig"}

AUTHTOKEN = HTTPBasicAuth(AUTH['username'],AUTH['password'])



def validUserName(username):
    '''Checks the username to ensure validity using a serializer'''
    from .serializers import AuthorSerializer  
    usernameCheck = AuthorSerializer( 
    data={

            "displayName": username,
                
        }, partial=True)
            
    if usernameCheck.is_valid():
        return True
    
    return False

def saveNewAuthor(request, user, username, github, profileImage, is_local):
    '''Saves a new author instance from the signup'''
    
    serial_id = uuid.uuid4()
    string_serial = str(serial_id)
    try:
        if request.is_secure():
            port = 'https'
        else: 
            port = 'http'

        host = request.get_host()

        base_id = f"{port}://{host}/api/authors/{string_serial}"
        base_web = f"{port}://{host}/authors/{string_serial}"

        newAuthor = Author(
                    
        user = user,
      
        id = base_id,
                    
        displayName = username,
        
        serial = serial_id,
        
        host=port+'://'+host+'/api/',

        github=github,
    
        web =base_web,
        
        is_local=True
        
        )
        if profileImage:  # only set if user uploaded one
            newAuthor.profileImage = profileImage
        newAuthor.save()
        return newAuthor
    
    except Exception as e:
        print(f"[saveNewAuthor] Exception: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return None
    

def remote_followers_fetched(FOREIGN_AUTHOR_FQID):
    '''retrieves a list of a remote authors followers or returns False'''
    remote_followers_fetch = requests.get(FOREIGN_AUTHOR_FQID+"/followers", auth=AUTHTOKEN, timeout=3)
    if not remote_followers_fetch.status_code ==200:
        return False
    else:
        return remote_followers_fetch.json()
    
def remote_author_fetched(FOREIGN_AUTHOR_FQID):
    '''returns the author JSONified object from a remote author's FQID (if valid), false otherwise'''
    authorFQID = FOREIGN_AUTHOR_FQID.rstrip('/')
    remote_author_fetch = requests.get(FOREIGN_AUTHOR_FQID,auth=AUTHTOKEN, timeout=3)
    if not remote_author_fetch.status_code == 200:
       return False
    else:
        return remote_author_fetch.json()
    
def encoded_fqid(FOREIGN_AUTHOR_FQID):
    '''percent encodes an author's fqid'''  
    return urllib.parse.quote(FOREIGN_AUTHOR_FQID, safe="")     

 
def decoded_fqid(FOREIGN_AUTHOR_FQID):
    '''percent decodes and author's fqid'''
    fqid = FOREIGN_AUTHOR_FQID 
    for _ in range(5): 
        decoded = unquote(fqid)
        fqid = decoded
    return fqid

def get_host_and_scheme(FOREIGN_AUTHOR_FQID):
    '''gets the scheme and host name for a DECODED foreign author FQID'''
    parsed = urlparse(FOREIGN_AUTHOR_FQID)
    host = parsed.netloc
    scheme = parsed.scheme
    return host,scheme

def get_serial(FOREIGN_AUTHOR_FQID):
    '''gets the serial of a DECODED foreign author FQID'''
    author_serial = FOREIGN_AUTHOR_FQID.split('/')[-1]
    return author_serial

def get_remote_followers(author):
    """Return a list of FQIDs of remote authors following the given local author"""
    # filter followers whose host is not local
    return [
        follower.follower.id
        for follower in author.followers.all()
        if not follower.follower.is_local
    ]

def create_automatic_following(requesting, requested, local_request):
    '''creates an automatic following between the requested and requesting author'''
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

def send_entry_to_remote_followers(entry, request=None):
    # Don't send deleted entries
    if entry.visibility == 'DELETED':
        print(f"Not sending deleted entry {entry.id} to remote followers")
        return
    # Find all remote followers (not local)
    remote_followers = AuthorFollowing.objects.filter(
        following=entry.author,
    ).exclude(follower__is_local=True)
    # Get all remote friends (mutual following)
    remote_friends = AuthorFriend.objects.filter(
        (Q(friending=entry.author) | Q(friended=entry.author)),
    ) 
    print(f"THIS AUTHOR'S REMOTE FRIENDS ARE: {remote_friends}")
    print(f"THIS AUTHOR'S REMOTE FOLLOWERS ARE: {remote_followers}")
    
    if not remote_followers.exists() and not remote_friends.exists():
        print(f"No remote followers or friends to send entry to.")
        return
    # Determine who should receive this entry based on visibility
    recipients = set()
    
    if entry.visibility == 'PUBLIC' or entry.visibility == 'UNLISTED':
        # Send to all remote followers
        for rel in remote_followers:
            recipients.add(rel.follower)
     
    elif entry.visibility == 'FRIENDS':
        print("VISIBILITY OF THE POST IS FRIENDS ONLY")
        # Send only to remote friends
        for rel in remote_friends:
            if rel.friending == entry.author:  
                recipients.add(rel.friended)
                print(f"FRIEND RECEIVING ENTRY: {rel.friended}")  
            else:
                recipients.add(rel.friending)
                print(f"FRIEND RECEIVING ENTRY: {rel.friending}")
                
    # Serialize entry
    serialized_entry = EntrySerializer(entry, context={"request": request}).data


    for recipient in recipients:
        try:
            # Construct inbox url
            inbox_url = recipient.id.rstrip('/') + '/inbox/'
            
            # Create payload
            payload = serialized_entry
            
            # Send POST request to remote inbox
            response = requests.post(
                inbox_url,
                json=payload,
                auth=AUTHTOKEN,
                headers={"Content-Type": "application/json"},
              
            ) 
    
            if response.status_code in [200, 201]:
                print(f"Successfully sent entry {entry.id} to {inbox_url}")
            else:
                print(f"Failed to send entry {entry.id} to {inbox_url}: {response.status_code} {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"Timeout sending entry {entry.id} to {inbox_url}")
        except requests.exceptions.ConnectionError:
            print(f"Connection error sending entry {entry.id} to {inbox_url}")
        except Exception as e:
            print(f"Exception sending entry {entry.id} to {inbox_url}: {str(e)}")
    print(f"Sent entry {entry.id} to {len(recipients)} remote recipients")
        

def get_mime(sent_content):
    '''gets the mimetype of an entry using the filetype library'''
    decoded_content =  base64.b64decode(sent_content)  
    file_type = filetype.guess(decoded_content)
    print(f"THE NEW ENTRY'S FILETYPE IS: {file_type.mime}")                 
    return file_type.mime  

def get_author_friends(author): 
     # Friends
    friend_pairs = AuthorFriend.objects.filter(
        Q(friending=author) | Q(friended=author)
    ).values_list('friending', 'friended')

    friend_ids = set()
    for friending_id, friended_id in friend_pairs:
        if friending_id != author.id:
            friend_ids.add(friending_id)
        if friended_id != author.id:
            friend_ids.add(friended_id)
    
    friends_list = []
    for friend_id in friend_ids:
        try:
            friends_list.append(Author.objects.get(id=friend_id))
        except Exception as e:
            print(e)
            pass
    print("this author's friends: ",friends_list)
    return friends_list
    
    
          
def author_exists(id):
    '''
    - checks for an author's existence based on their id field
    - returns the author if it exists
    - returns None if this is not a valid author
    
    '''
    id=id.rstrip('/')
    try:
        return Author.objects.get(id=id)
    except Author.DoesNotExist:
        return False
    
def process_new_remote_author(account_serialized):
    '''handles the creation of a new remote author'''
    profile = account_serialized.save()
    print("NEW AUTHOR OBJECT VALIDATED, SAVING TO DB")
    #Set the author as remote and save
    profile.is_local=False 
    #GITHUB ENTRY AUTOMATION, CHECKED AFTER EVERY LOGIN FOR REMOTE PROFILES 
    profile.save()
    create_entries(profile)
    return profile

def get_remote_authors_list(remote_authors_lists):
    '''creates a list of every remote author's json object'''
    all_remote_authors = []
    for remote_author_list in remote_authors_lists:
        for author_json in remote_author_list:
            print(f"AUTHOR PULLED: {author_json}\n")
            all_remote_authors.append(author_json)#contains a json of all of the remote authors 
    return all_remote_authors

def add_or_update_fetched_authors(all_remote_authors):
    '''add new authors to the database or updates existing remote authors, existing local authors are left untouched'''
    for remote_author in all_remote_authors:
        if remote_author.get("id"):
            remote_author['id'] = remote_author.get("id").rstrip('/')
            author_id = remote_author['id']
            try:
                
                if author_exists(author_id):
                    print("EXISTING AUTHOR FOUND")
                    existing_author = Author.objects.get(id=author_id)
                    account_serialized = AuthorSerializer(existing_author, data=remote_author, partial=True)
                else:
                    #SERIALIZE AND SAVE IF THEIR DATA IS VALID
                    print("NEW AUTHOR FOUND")
                    account_serialized = AuthorSerializer(data=remote_author)    
                    print(f"ACCOUNT SERIALIZED: {account_serialized}")
                #IF THEIR DATA IS INVALID, INFORM THE REQUESTER
                if not account_serialized.is_valid():
                    print("NEW AUTHOR OBJECT STRUCTURE INVALID")
                    print(account_serialized.errors)    
                else:
                    #CHECK IF THE AUTHOR IS ALREADY ON THIS NODE
                    print (f"AUTHOR ALREADY EXISTS ON THIS NODE:{author_exists(author_id)}")
                    #CHECK THAT AUTHOR WAS FETCHED FROM THE REMOTE NODE
                    fetched_author = author_exists(author_id)
                    #FOR A NEW REMOTE AUTHOR
                    if not fetched_author:
                        process_new_remote_author(account_serialized)
                    #FOR A FETCHED AUTHOR ALREADY ON OUR NODE
                    else:
                        if not fetched_author.is_local:
                            print("EXISTING AUTHOR REMOTE AUTHOR UPDATED, SAVING TO DB")
                            profile = account_serialized.save()
                        #A fetched remote author who is a local author from our current node will receive no updates
                        else:
                            print("EXISTING AUTHOR FROM OUR NODE FOUND, NO UPDATES MADE.")
                    print(f"AUTHOR {fetched_author.displayName} SAVED TO DATABASE")
            except Exception as e:
                print(e)   
                  
def send_comment_to_entry_author(comment, request=None):
    """
    Send a comment to the entry author's inbox.
    This is used when someone comments on an entry - the comment goes to the entry author's inbox.
    """
    # Don't send comments on deleted entries
    if comment.entry.visibility == 'DELETED':
        print(f"Not sending comment on deleted entry {comment.entry.id} to entry author")
        return
    
    # Get the entry author
    entry_author = comment.entry.author
    print(f"DEBUG: Entry author id: {entry_author.id}")
    print(f"DEBUG: Entry author serial: {entry_author.serial}")
    print(f"DEBUG: Entry author is_local: {entry_author.is_local}")
    
    # Don't send if the comment author is the same as the entry author (local comment on own entry)
    if comment.author == entry_author:
        print(f"Comment author is the same as entry author, not sending to inbox")
        return
    
    # Only send if the entry author is remote (not local)
    if entry_author.is_local:
        print(f"Entry author is local, not sending comment to inbox")
        return
    
    try:
        # Use the entry author ID directly and add /inbox/
        inbox_url = entry_author.id.rstrip('/') + '/inbox/'
        print(f"DEBUG: Entry author id: {entry_author.id}")
        print(f"DEBUG: Entry author serial: {entry_author.serial}")
        print(f"DEBUG: Constructed inbox URL: {inbox_url}")
        
        # Serialize comment
        serialized_comment = CommentSummarySerializer(comment, context={"request": request}).data
        print(f"DEBUG: Serialized comment entry field: {serialized_comment.get('entry', 'NOT_FOUND')}")
        

        # Send POST request to entry author's inbox
        response = requests.post(
            inbox_url,
            json=serialized_comment,
            auth=AUTHTOKEN,
            headers={"Content-Type": "application/json"},
        )
        
        if response.status_code in [200, 201]:
            print(f"Successfully sent comment {comment.id} to entry author's inbox: {inbox_url}")
        else:
            print(f"Failed to send comment {comment.id} to entry author's inbox: {inbox_url}: {response.status_code} {response.text}")
            
    except requests.exceptions.Timeout:
        print(f"Timeout sending comment {comment.id} to entry author's inbox: {inbox_url}")
    except requests.exceptions.ConnectionError:
        print(f"Connection error sending comment {comment.id} to entry author's inbox: {inbox_url}")
    except Exception as e:
        print(f"Exception sending comment {comment.id} to entry author's inbox: {str(e)}")


def send_comment_like_to_comment_author(comment_like, request=None):
    """
    Send a comment like to the comment author's inbox.
    This is used when someone likes a comment - the like goes to the comment author's inbox.
    """
    # Get the comment and its author
    comment = comment_like.comment
    comment_author = comment.author
    
    # Don't send if the like author is the same as the comment author (liking own comment)
    if comment_like.user == comment_author:
        print(f"Like author is the same as comment author, not sending to inbox")
        return
    
    # Only send if the comment author is remote (not local)
    if comment_author.is_local:
        print(f"Comment author is local, not sending like to inbox")
        return
    
    try:
        # Extract host from the author ID and use the correct serial
        author_id = comment_author.id
        author_id = author_id.rstrip('/')
        print(f"DEBUG: Comment author ID: {author_id}")
        print(f"DEBUG: Comment author is_local: {comment_author.is_local}")
        
        # Remove the /api/authors/{wrong_serial} part to get just the host
        host = author_id.replace('/api/authors/' + author_id.split('/')[-1], '')
        print(f"DEBUG: Extracted host: {host}")
        
        # Construct inbox url for the comment author using the correct serial
        inbox_url = f"{author_id}/inbox/"
        print(f"DEBUG: Constructed inbox URL: {inbox_url}")
        
        serialized_like = CommentLikeSummarySerializer(comment_like, context={"request": request}).data
        
        # Create payload in inbox format - send the like data directly
        payload = serialized_like
        
        # Send POST request to comment author's inbox
        response = requests.post(
            inbox_url,
            json=payload,
            auth=AUTHTOKEN,
            headers={"Content-Type": "application/json"},
        )
        
        if response.status_code in [200, 201]:
            print(f"Successfully sent comment like {comment_like.id} to comment author's inbox: {inbox_url}")
        else:
            print(f"Failed to send comment like {comment_like.id} to comment author's inbox: {inbox_url}: {response.status_code} {response.text}")
            
    except requests.exceptions.Timeout:
        print(f"Timeout sending comment like {comment_like.id} to comment author's inbox: {inbox_url}")
    except requests.exceptions.ConnectionError:
        print(f"Connection error sending comment like {comment_like.id} to comment author's inbox: {inbox_url}")
    except Exception as e:
        print(f"Exception sending comment like {comment_like.id} to comment author's inbox: {str(e)}")


def send_entry_like_to_entry_author(entry_like, request=None):
    """
    Send an entry like to the entry author's inbox.
    This is used when someone likes an entry - the like goes to the entry author's inbox.
    """
    # Get the entry and its author
    entry = entry_like.entry
    entry_author = entry.author
    
    # Don't send if the like author is the same as the entry author (liking own entry)
    if entry_like.user == entry_author:
        print(f"Like author is the same as entry author, not sending to inbox")
        return
    
    # Only send if the entry author is remote (not local)
    if entry_author.is_local:
        print(f"Entry author is local, not sending like to inbox")
        return
    
    try:
        # Use the entry author ID directly and add /inbox/
        print(f"DEBUG: Entry author ID: {entry_author.id}")
        print(f"DEBUG: Entry author serial: {entry_author.serial}")
        print(f"DEBUG: Entry author is_local: {entry_author.is_local}")
        
        inbox_url = entry_author.id.rstrip('/') + '/inbox/'
        print(f"DEBUG: Constructed inbox URL: {inbox_url}")
        
        serialized_like = LikeSummarySerializer(entry_like, context={"request": request}).data
        
        
        # Send POST request to entry author's inbox
        response = requests.post(
            inbox_url,
            json=serialized_like,
            auth=AUTHTOKEN,
            headers={"Content-Type": "application/json"},
        )
        
        if response.status_code in [200, 201]:
            print(f"Successfully sent entry like {entry_like.id} to entry author's inbox: {inbox_url}")
        else:
            print(f"Failed to send entry like {entry_like.id} to entry author's inbox: {inbox_url}: {response.status_code} {response.text}")
            
    except requests.exceptions.Timeout:
        print(f"Timeout sending entry like {entry_like.id} to entry author's inbox: {inbox_url}")
    except requests.exceptions.ConnectionError:
        print(f"Connection error sending entry like {entry_like.id} to entry author's inbox: {inbox_url}")
    except Exception as e:
        print(f"Exception sending entry like {entry_like.id} to entry author's inbox: {str(e)}")


def send_entry_deletion_to_remote_followers(entry, request=None):
    """
    Send entry deletion notification to remote followers and friends.
    This ensures deletions are propagated to all connected remote nodes.
    """
    # Finds all remote followers (not local)
    remote_followers = AuthorFollowing.objects.filter(
        following=entry.author,
    ).exclude(follower__is_local=True)
    
    # Gets all remote friends (mutual following)
    remote_friends = AuthorFriend.objects.filter(
        (Q(friending=entry.author) | Q(friended=entry.author)),
    ).exclude(
        Q(friending__is_local=True) | Q(friended__is_local=True)
    ) 
    
    if not remote_followers.exists() and not remote_friends.exists():
        print(f"No remote followers or friends to send deletion notification to.")
        return
    
    recipients = set()
    
 
    for rel in remote_followers:
        recipients.add(rel.follower)
    
    for rel in remote_friends:
        if rel.friending == entry.author:
            recipients.add(rel.friended)
        else:
            recipients.add(rel.friending)
    

    original_visibility = entry.visibility
    entry.visibility = "DELETED"
    
    deletion_payload = EntrySerializer(entry, context={"request": request}).data
    
    entry.visibility = original_visibility
    
    for recipient in recipients:
        try:
            inbox_url = recipient.id.rstrip('/') + '/inbox/'
            
            # Sends POST request to remote inbox
            response = requests.post(
                inbox_url,
                json=deletion_payload,
                auth=AUTHTOKEN,
                headers={"Content-Type": "application/json"},
            ) 
    
            if response.status_code in [200, 201]:
                print(f"Successfully sent entry deletion to {inbox_url}")
            else:
                print(f"Failed to send entry deletion to {inbox_url}: {response.status_code} {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"Timeout sending entry deletion to {inbox_url}")
        except requests.exceptions.ConnectionError:
            print(f"Connection error sending entry deletion to {inbox_url}")
        except Exception as e:
            print(f"Exception sending entry deletion to {inbox_url}: {str(e)}")
    
    print(f"Sent entry deletion notification to {len(recipients)} remote recipients")


def validated_auth(auth_header):
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
    return True
    
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

def decoded_auth_token(auth_header):
    '''returns a decoded auth taken received from an HTTP response header'''
    if isinstance(auth_header, str):
        print("AUTH ENCODED IN UTF-8")
        print("AUTH ENCODED AS BYTES, DECODED TO STRING")
        auth_header_split = auth_header.split(" ")# -> ["Basic", "{auth encoded in bytes}"]
        auth = auth_header_split[1]# -> [takes the last part of ^^ (auth encoded in bytes) and stores it as the auth token] -> {auth_encoded}
        decoded_auth = base64.b64decode(auth.encode('UTF-8'))# -> decodes string auth, encodes it into utf-8 ( a readable string)
        decoded_username, decoded_pass = decoded_auth.decode().split(":", 1)# -> username, password
    else:
        return False
        
    #print(f"AUTH INFO SPLIT: {auth_header_split}")
    #print(f"ENCODED AUTH INFO: {auth}")
    #print(f"DECODED AUTH : {decoded_auth}")
    #print(f"USDERNAME AND PASSWORD: {decoded_username, decoded_pass}")
    
    return decoded_username, decoded_pass