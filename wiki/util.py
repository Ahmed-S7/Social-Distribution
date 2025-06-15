from .serializers import AuthorSerializer
from .models import Author
from django.http import HttpResponse
import uuid


def validUserName(username):
    '''Checks the username to ensure validity using a serializer'''
      
    usernameCheck = AuthorSerializer( 
    data={

            "displayName": username,
                
        }, partial=True)
            
    if usernameCheck.is_valid():
        return True
    
    return False

def saveNewAuthor(user, username):
    '''Saves a new author instance'''
    
    serial = uuid.uuid4()
    try:
        newAuthor = Author(
                    
        user = user,
        
        authorURL = f"http://s25-project-white/api/authors/{user.id}",
                    
        displayName = username,
                    
        web = f"http://s25-project-white/api/{serial}"
        
        )
        newAuthor.save()
        return newAuthor
    
    except Exception as e:
        return HttpResponse(str(e), status=500)
