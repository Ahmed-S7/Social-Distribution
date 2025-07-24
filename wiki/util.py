import requests
from .models import Author, RemoteNode, AuthorFollowing
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
from django.urls import reverse
import requests
from requests.auth import HTTPBasicAuth
from .serializers import EntrySerializer

#AUTH TOKEN TO BE USED WITH REQUESTS
#YOU NEED TO HAVE A USER WITH THIS GIVEN AUTH ON THE NODE YOU ARE CONNECTING TO IN ORDER TO BE VALIDATED
AUTH =  {"username":"white",
        "password":"uniquepass"}

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

def saveNewAuthor(request, user, username, github, profileImage, web):
    '''Saves a new author instance'''
    
    serial_id = uuid.uuid4()
    string_serial = str(serial_id)
    try:
        if request.is_secure():
            port = 'https'
        else: 
            port = 'http'

        host = request.get_host()

        base_id = f"{port}://{host}/s25-project-white/api/authors/{string_serial}"
        base_web = f"{port}://{host}/s25-project-white/authors/{string_serial}"

        newAuthor = Author(
                    
        user = user,
      
        id = base_id,
                    
        displayName = username,
        
        serial = serial_id,
        
        host=port+'://'+host,

        github=github,
    
        web =base_web,
        
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
    remote_followers_fetch = requests.get(FOREIGN_AUTHOR_FQID+"/followers")
    if not remote_followers_fetch.status_code ==200:
        return False
    else:
        return remote_followers_fetch.json()
    
def remote_author_fetched(FOREIGN_AUTHOR_FQID):
    '''returns the author JSONified object from a remote author's FQID (if valid), false otherwise'''
    remote_author_fetch = requests.get(FOREIGN_AUTHOR_FQID)
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
    from .models import AuthorFollowing
    # filter followers whose host is not local
    return [
        follower.follower.id
        for follower in author.followers.all()
        if not follower.follower.is_local
    ]


def send_entry_to_remote_followers(entry, request=None):
    from .models import AuthorFollowing
    from .serializers import EntrySerializer
    from .util import AUTHTOKEN

    # Find all remote followers (not local)
    remote_followers = AuthorFollowing.objects.filter(
        following=entry.author
    ).exclude(follower__host="http://127.0.0.1:8000/")

    for rel in remote_followers:
        follower = rel.follower
        inbox_url = follower.id.rstrip('/') + '/inbox/'

        serialized_entry = EntrySerializer(entry, context={"request": request}).data

        payload = {
            "type": "entry",
            "body": serialized_entry
        }

        try:
            response = requests.post(
                inbox_url,
                json=payload,
                auth=AUTHTOKEN,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code >= 400:
                print(f"Failed to send entry to {inbox_url}: {response.status_code} {response.text}")
        except Exception as e:
            print(f"Exception sending entry to {inbox_url}: {e}")

def send_entry_to_remote_followers(entry, request=None):
    # Find all remote followers (not local)
    remote_followers = [
        rel.follower
        for rel in AuthorFollowing.objects.filter(following=entry.author)
        if not rel.follower.is_local
    ]

    for follower in remote_followers:
        inbox_url = follower.id.rstrip('/') + '/inbox/'
        serialized_entry = EntrySerializer(entry, context={"request": request}).data

       
        payload = {
            "type": "entry",
            "body": serialized_entry
        }

        try:
            response = requests.post(
                inbox_url,
                json=payload,
                auth=AUTHTOKEN,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code >= 400:
                print(f"Failed to send entry to {inbox_url}: {response.status_code} {response.text}")
        except Exception as e:
            print(f"Exception sending entry to {inbox_url}: {e}")
            
            
            
def author_exists(id):
    '''
    - checks for an author's existence based on their id field
    - returns the author if it exists
    - returns None if this is not a valid author
    
    '''
    return Author.objects.filter(id=id)
