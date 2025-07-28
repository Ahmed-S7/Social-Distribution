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
from .serializers import EntrySerializer

#AUTH TOKEN TO BE USED WITH REQUESTS
#YOU NEED TO HAVE A USER WITH THIS GIVEN AUTH ON THE NODE YOU ARE CONNECTING TO IN ORDER TO BE VALIDATED
#YOU ALSO NEED A NODE CREDENTIALS OBJECT WITH THIS USERNAME AND PASSWORD, THIS IS HOW VALIDATION WILL BE DONE
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

def saveNewAuthor(request, user, username, github, profileImage):
    '''Saves a new author instance'''
    
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
        
        host=port+'://'+host+'/api',

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
    ).exclude(follower__host="http://127.0.0.1:8000/api")
    print(f"remote followers: {remote_followers}")
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

def send_all_entries_to_follower(local_author, remote_follower, request=None):
    """
    Send all appropriate entries (public, unlisted, and friends-only if applicable)
    from local_author to remote_follower's inbox.
    """

    # Determine if the remote follower is a friend (mutual following)
    is_friend = AuthorFriend.objects.filter(
        (Q(friending=local_author, friended=remote_follower) | Q(friending=remote_follower, friended=local_author)),
        is_deleted=False
    ).exists()

    # Get all entries the remote follower should see
    entries = Entry.objects.filter(
        author=local_author,
        is_deleted=False
    ).filter(
        Q(visibility="PUBLIC") |
        Q(visibility="UNLISTED") |
        (Q(visibility="FRIENDS") & is_friend)
    ).order_by('created_at')

    inbox_url = remote_follower.id.rstrip('/') + '/inbox/'

    for entry in entries:
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


def get_remote_entries(node):
    """
    Fetch and store all entries from a specific remote node.
    
    Args:
        node: RemoteNode object containing the node's URL and credentials
    
    Returns:
        tuple: (entries_created, entries_updated)
    """
    from .models import Author, Entry
    
    entries_created = 0
    entries_updated = 0
    
    try:
        normalized_url = node.url.rstrip("/")
        print(f"Fetching from node: {normalized_url}")
        
        # Fetch authors from remote node
        authors_response = requests.get(
            f"{normalized_url}/api/authors/",
            auth=AUTHTOKEN,
            timeout=10
        )
        
        if authors_response.status_code == 200:
            authors_data = authors_response.json()
            print(f"Found {len(authors_data.get('authors', []))} authors from {normalized_url}")
            
            # Process each author and their entries
            for author_data in authors_data.get('authors', []):
                # Create or update the remote author
                remote_author, created = Author.objects.get_or_create(
                    id=author_data['id'],
                    defaults={
                        'displayName': author_data.get('displayName', ''),
                        'host': author_data.get('host', ''),
                        'web': author_data.get('web', ''),
                        'github': author_data.get('github', ''),
                        'profileImage': author_data.get('profileImage', ''),
                        'is_local': False,
                    }
                )
                
                if not created:
                    # Update existing author with latest data
                    remote_author.displayName = author_data.get('displayName', remote_author.displayName)
                    remote_author.host = author_data.get('host', remote_author.host)
                    remote_author.web = author_data.get('web', remote_author.web)
                    remote_author.github = author_data.get('github', remote_author.github)
                    remote_author.profileImage = author_data.get('profileImage', remote_author.profileImage)
                    remote_author.save()
                
                # Fetch entries for this author
                author_serial = remote_author.serial
                entries_response = requests.get(
                    f"{normalized_url}/api/authors/{author_serial}/entries/",
                    auth=AUTHTOKEN,
                    timeout=10
                )
                
                if entries_response.status_code == 200:
                    entries_data = entries_response.json()
                    print(f"Found {len(entries_data.get('entries', []))} entries for author {author_serial}")
                    
                    # Process each entry
                    for entry_data in entries_data.get('entries', []):
                        # Check if entry already exists by origin_url
                        existing_entry = Entry.objects.filter(
                            origin_url=entry_data.get('id')
                        ).first()
                        
                        if not existing_entry:
                            # Create new entry
                            try:
                                new_entry = Entry.objects.create(
                                    author=remote_author,
                                    title=entry_data.get('title', ''),
                                    content=entry_data.get('content', ''),
                                    contentType=entry_data.get('contentType', 'text/plain'),
                                    description=entry_data.get('description', ''),
                                    visibility=entry_data.get('visibility', 'PUBLIC'),
                                    origin_url=entry_data.get('id'),
                                    web=entry_data.get('web', ''),
                                    is_local=False,
                                )
                                print(f"Created entry: {new_entry.title}")
                                entries_created += 1
                            except Exception as e:
                                print(f"Error creating entry: {e}")
                        else:
                            # Update existing entry
                            existing_entry.title = entry_data.get('title', existing_entry.title)
                            existing_entry.content = entry_data.get('content', existing_entry.content)
                            existing_entry.contentType = entry_data.get('contentType', existing_entry.contentType)
                            existing_entry.description = entry_data.get('description', existing_entry.description)
                            existing_entry.visibility = entry_data.get('visibility', existing_entry.visibility)
                            existing_entry.web = entry_data.get('web', existing_entry.web)
                            existing_entry.save()
                            print(f"Updated entry: {existing_entry.title}")
                            entries_updated += 1
                else:
                    print(f"Failed to fetch entries for author {author_serial}: {entries_response.status_code}")
                    
        else:
            print(f"Failed to fetch authors from {normalized_url}: {authors_response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching from {node.url}: {e}")
    except Exception as e:
        print(f"Error processing node {node.url}: {e}")
    
    print(f"Node {node.url}: {entries_created} entries created, {entries_updated} entries updated")
    return entries_created, entries_updated
