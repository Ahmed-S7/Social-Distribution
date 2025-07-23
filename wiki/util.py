
from .models import Author, RemoteNode
from django.http import HttpResponse, Http404
import uuid
from django.shortcuts import redirect
import traceback
from rest_framework.response import Response
import urllib
from urllib.parse import urlparse
from django.http import Http404, HttpResponseRedirect, HttpResponseServerError, HttpResponse
import traceback
import sys
from django.urls import reverse
import requests
from requests.auth import HTTPBasicAuth
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
    if not remote_followers_fetch.status_code == 200:
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
        
def decoded_fqid(FOREIGN_AUTHOR_FQID):
    '''percent decodes and author's fqid'''
    return urllib.parse.unquote(FOREIGN_AUTHOR_FQID)

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