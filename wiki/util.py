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
    
    serial_id = uuid.uuid4()
    
    try:
        newAuthor = Author(
                    
        user = user,
        
        authorURL = f"http://s25-project-white/api/authors/{user.id}",
                    
        displayName = username,
        
        serial = serial_id,
                    
        web = f"http://s25-project-white/api/{serial_id}"
        
        )
        newAuthor.save()
        return newAuthor
    
    except Exception as e:
        print("IT FAILED")
        print(e)
        return None
