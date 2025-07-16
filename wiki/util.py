from .serializers import AuthorSerializer
from .models import Author, RemoteNode
from django.http import HttpResponse, Http404
import uuid
from django.shortcuts import redirect
import traceback
from rest_framework.response import Response
from urllib.parse import urlparse
from django.http import Http404, HttpResponseRedirect, HttpResponseServerError, HttpResponse
import traceback
import sys
import requests
from requests.auth import HTTPBasicAuth
def validUserName(username):
    '''Checks the username to ensure validity using a serializer'''
      
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
        #URL TEMPORARILY USES LOCAL HOST AS PORT, CHANGE WHEN CONNECTING WITH OTHER NODES OR USING HOSTED SITE
        id = base_id,
                    
        displayName = username,
        
        serial = serial_id,


        github=github,
        #URL TEMPORARILY USES LOCAL HOST AS PORT, CHANGE WHEN CONNECTING WITH OTHER NODES OR USING HOSTED SITE
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
    

def is_valid_serial(id):
    
    try:
        
        id = uuid.UUID(id)
        
        return True
            
    except Exception as e:
        
        return False
