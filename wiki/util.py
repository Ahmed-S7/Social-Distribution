from .serializers import AuthorSerializer
from .models import Author
from django.http import HttpResponse, Http404
import uuid
from django.shortcuts import redirect
import traceback
from rest_framework.response import Response
from urllib.parse import urlparse
from django.http import Http404, HttpResponseRedirect, HttpResponseServerError
import traceback
import sys
def validUserName(username):
    '''Checks the username to ensure validity using a serializer'''
      
    usernameCheck = AuthorSerializer( 
    data={

            "displayName": username,
                
        }, partial=True)
            
    if usernameCheck.is_valid():
        return True
    
    return False

def saveNewAuthor(request, user, username, github=None, profileImage=None, web=None):
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
        
        profileImage=profileImage or "https://cdn.pixabay.com/photo/2016/08/08/09/17/avatar-1577909_640.png",

        github=github,
        #URL TEMPORARILY USES LOCAL HOST AS PORT, CHANGE WHEN CONNECTING WITH OTHER NODES OR USING HOSTED SITE
        web =base_web,
        
        )
        newAuthor.save()
        return newAuthor
    
    except Exception as e:
        print(f"[saveNewAuthor] Exception: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return None
    
    
def get_author_id(request):
    
    absolute_url = request.build_absolute_uri()
        
    parsed = urlparse(absolute_url)
        
    stringified_url =str(parsed.path)
        
    id = stringified_url.strip().split('/')[-1]
        
    return id
    
def get_logged_author(user):
    '''get the author that is currently logged in'''
    try:
        current_user = user.username
        current_author = Author.objects.get(displayName=current_user, is_deleted=False)
        return current_author
    
    except Exception as e:
        print(f"Failed to get current author: {e} ")
        return False
          
def is_valid_serial(id):
    
    try:
        
        id = uuid.UUID(id)
        
        return True
            
    except Exception as e:
        
        return False
        
        