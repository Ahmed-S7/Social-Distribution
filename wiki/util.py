from .serializers import AuthorSerializer
from .models import Author
from django.http import HttpResponse
import uuid
import traceback


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
    string_serial = str(serial_id)
    
    try:
        newAuthor = Author(
                    
        user = user,
        
        id = f"http://s25-project-white/api/authors/{string_serial}",
                    
        displayName = username,
        
        serial = serial_id,
                    
        web = f"http://s25-project-white/authors/{string_serial}"
        
        )
        newAuthor.save()
        return newAuthor
    
    except Exception as e:
        print("IT FAILED")
        print(f"Exception: {e}")
        traceback.print_exc()
        return None
