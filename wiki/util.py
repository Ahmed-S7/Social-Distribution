import requests
from .models import Author, Entry, RemoteNode, AuthorFollowing, AuthorFriend
from django.http import HttpResponse, Http404
import uuid
from django.shortcuts import redirect
import traceback
from rest_framework.response import Response
import urllib
from urllib.parse import urlparse, unquote
from django.http import Http404, HttpResponseRedirect, HttpResponseServerError, HttpResponse
import traceback
import sys
from django.db.models import Q
from django.urls import reverse
import requests
from requests.auth import HTTPBasicAuth
from .serializers import EntrySerializer, CommentSummarySerializer, CommentLikeSummarySerializer, LikeSummarySerializer

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
    remote_followers_fetch = requests.get(FOREIGN_AUTHOR_FQID+"/followers", auth=AUTHTOKEN, timeout=2)
    if not remote_followers_fetch.status_code ==200:
        return False
    else:
        return remote_followers_fetch.json()
    
def remote_author_fetched(FOREIGN_AUTHOR_FQID):
    '''returns the author JSONified object from a remote author's FQID (if valid), false otherwise'''
    remote_author_fetch = requests.get(FOREIGN_AUTHOR_FQID,auth=AUTHTOKEN, timeout=2)
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
        

                   
            
def author_exists(id):
    '''
    - checks for an author's existence based on their id field
    - returns the author if it exists
    - returns None if this is not a valid author
    
    '''
    return Author.objects.filter(id=id)




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
