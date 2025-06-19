from django.test import TestCase
from rest_framework.test import APIClient
from .models import Author, Entry,FollowRequest, RequestState, AuthorFollowing, AuthorFriend
from django.contrib.auth.models import User
import uuid
from django.db.models import Q
from django.urls import reverse

from rest_framework import status
BASE_PATH = "/s25-project-white/api"

class IdentityTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create user and authenticate properly
        self.user = User.objects.create_user(
            username='test_user',
            password='test_password',
        )
        self.user2 = User.objects.create_user(
            username='test_user2',
            password='test_password2'
        )
        # Proper authentication for Django views
        self.client.login(username='test_user', password='test_password')
        
        self.author = Author.objects.create(
            id=1,
            user=self.user,
            displayName='test_author',
            description='test_description',
            github='https://github.com/test_author',
            serial=uuid.uuid4(),
            web='https://example.com/',
            profileImage = 'https://cdn-icons-png.flaticon.com/256/3135/3135823.png'
        )
        self.entry = Entry.objects.create(
            title='Test Entry',
            content='This is a test entry.',
            author=self.author,
            serial=uuid.uuid4(),
            visibility="PUBLIC"
        )
        self.admin = User.objects.create_superuser(
            username='admin_user',
            password='admin_password', 
            email='admin@ualberta.ca'
        )
        self.client.force_authenticate(user=self.admin)
        self.author2 = Author.objects.create(
            id=2,
            user=self.user2,
            displayName='test_author2',
            description='test_description2',
            github='https://github.com/test_author2',
            serial=uuid.uuid4(),
            web='https://example.com/2'
        )

    # Identity 1.1 As an author, I want a consistent identity per node, so that URLs to me/my entries are predictable and don't stop working
    def test_consistent_identity_author(self):
        url = f'{BASE_PATH}/author/{self.author.serial}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["displayName"], "test_author")

    def test_consistent_identity_entry(self):
        url = f'{BASE_PATH}/entry/{self.entry.serial}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Test Entry")

    # Identity 1.2 As a node admin, I want to host multiple authors on my node, so I can have a friendly online community.
    def test_multiple_authors_on_node(self):
        url = f'{BASE_PATH}/authors/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2) 
        self.assertContains(response, 'test_author')
        self.assertContains(response, 'test_author2')

    # Identity 1.3 As an author, I want a public page with my profile information, so that I can link people to it
    def test_public_profile_page(self):
        self.client.logout()
        url = f'{BASE_PATH}/{self.author.displayName}/profile/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["displayName"], self.author.displayName)
        self.assertEqual(response.data["description"], self.author.description)
        self.assertEqual(response.data["github"], self.author.github)

    # Identity 1.4 As an author, I want my profile page to show my public entries (most recent first), so they can decide if they want to follow me.
    def test_profile_public_entries(self):
        pass

    # Identity 1.5 As an author, I want to my (new, public) GitHub activity to be automatically turned into public entries, so everyone can see my GitHub activity too.
    def test_github_activity(self):
        pass
    
    # Identity 1.6 As an author, I want to be able to edit my profile: name, description, picture, and GitHub.
    # Identiy 1.7 As an author, I want to be able to use my web browser to manage my profile, so I don't have to use a clunky API.
    def test_edit_profile(self):
        url = f'{BASE_PATH}/{self.author.displayName}/profile/'
        response = self.client.get(url)
        self.assertEqual(response.data["displayName"], self.author.displayName)
        self.assertEqual(response.data["description"], self.author.description)
        self.assertEqual(response.data["github"], self.author.github)

        url = f'{BASE_PATH}/{self.author.displayName}/profile/edit/'
        updated_data = {
            'displayName': 'updated_author',
            'description': 'updated_description',
            'github': 'https://github.com/updated_author',
        }
        response = self.client.put(
            url, 
            data=updated_data,
            content_type='application/json'
        )
        self.author.refresh_from_db()
        self.assertEqual(self.author.displayName, updated_data['displayName'])
        self.assertEqual(self.author.description, updated_data['description'])
        self.assertEqual(self.author.github, updated_data['github'])

    def tearDown(self):
        self.client.logout()

class PostingTestCase(TestCase):
    pass

class FollowRequestTesting(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create user and authenticate properly
        self.requesting_user = User.objects.create_user(
            username='test_user',
            password='test_password',
        )
        self.requesting_user2 = User.objects.create_user(
            username='test_user2',
            password='test_password2'
        )
        self.receiving_user = User.objects.create_user(
            username='test_user3',
            password='test_password3'
        )
        self.following_user = User.objects.create_user(
            username='test_user4',
            password='test_password4'
        )
        # Proper authentication for Django views
        self.client.login(username='test_user', password='test_password')
        
        self.requesting_author1 = Author.objects.create(
            id=1,
            user=self.requesting_user,
            displayName='sending_author',
            description='test_description',
            github='https://github.com/test_author',
            serial=uuid.uuid4(),
            web='https://example.com/',
            profileImage = 'https://cdn-icons-png.flaticon.com/256/3135/3135823.png'
        )
        
        self.following_author = Author.objects.create(
            id=4,
            user=self.following_user,
            displayName='receiving_author2',
            description='test_description2',
            github='https://github.com/test_author',
            serial=uuid.uuid4(),
            web='https://example.com/',
            profileImage = 'https://cdn-icons-png.flaticon.com/256/3135/3135823.png'
        )
        
        self.requesting_author2 = Author.objects.create(
            id=2,
            user=self.requesting_user2,
            displayName='sending_author2',
            description='test_description2',
            github='https://github.com/test_author',
            serial=uuid.uuid4(),
            web='https://example.com/',
            profileImage = 'https://cdn-icons-png.flaticon.com/256/3135/3135823.png'
        )
        self.admin = User.objects.create_superuser(
            username='admin_user',
            password='admin_password', 
            email='admin@ualberta.ca'
        )
        self.client.force_authenticate(user=self.receiving_user)
        
        self.receiving_author = Author.objects.create(
            id=3,
            user=self.receiving_user,
            displayName='receiving_author',
            description='test_description2',
            github='https://github.com/test_author2',
            serial=uuid.uuid4(),
            web='https://example.com/2'
        )
        
        self.existing_following= AuthorFollowing.objects.create(
            follower=self.following_author,
            following=self.receiving_author
        )
        self.new_follow_back= FollowRequest.objects.create(
            requester=self.receiving_author,
            requested_account=self.following_author
        )
        self.new_follow_request1= FollowRequest.objects.create(
            requester=self.requesting_author1,
            requested_account=self.receiving_author
        )
        
        self.new_follow_request2= FollowRequest.objects.create(
            requester=self.requesting_author2,
            requested_account=self.receiving_author
        )
        
        
        
    #Following/Friends 6.8 As an author, my node will know about my followers, who I am following, and my friends, so that I don't have to keep track of it myself.    
    #Following/Friends 6.1 As an author, I want to follow local authors, so that I can see their public entries.
    #Following/Friends 6.3 As an author, I want to be able to approve or deny other authors following me, so that I don't get followed by people I don't like.
    #Following/Friends 6.4 As an author, I want to know if I have "follow requests," so I can approve them.
    def test_check_other_inbox(self):
        "should return 400 because only authenticated LOCAL users should be able to check their own inbox (not the requesting author)"
        url = f'{BASE_PATH}/authors/{self.requesting_author1.serial}/inbox/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        print("PASS: UNAUTHENTICATED LOCAL USERS CANNOT CHECK AN INBOX THAT IS NOT THEIRS")
     #Following/Friends 6.8 As an author, my node will know about my followers, who I am following, and my friends, so that I don't have to keep track of it myself.
    def test_check_correct_sending_author(self):
        "the author should be the correct sending author"
        url = f'{BASE_PATH}/authors/{self.receiving_author.serial}/inbox/'
        response = self.client.get(url)
        
        #the right sending author
        self.assertContains(response,"sending_author")
        print("PASS: THE AUTHOR SENDING FOLLOW REQUESTS IS PROPERLY PRESENTED IN THE API")
     #Following/Friends 6.8 As an author, my node will know about my followers, who I am following, and my friends, so that I don't have to keep track of it myself.    
    def test_check_correct_initial_state(self):
        "state should be requesting when initially sent"
        url = f'{BASE_PATH}/authors/{self.receiving_author.serial}/inbox/'
        response = self.client.get(url)
        
        self.assertContains(response, "state")
        self.assertEqual(response.data[0]["state"], RequestState.REQUESTING)   
        print("PASS: THE INITIAL STATE OF THE FOLLOW REQUESTS IS CORRECT")

    #Following/Friends 6.1 As an author, I want to follow local authors, so that I can see their public entries.
    #Friends/Following 6.3 As an author, I want to be able to approve or deny other authors following me, so that I don't get followed by people I don't like.
    def test_check_own_follow_requests(self):
        "should return 200 because only authenticated users should be able to check their own inbox (receiving author)"
        url = f'{BASE_PATH}/authors/{self.receiving_author.serial}/inbox/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        print("PASS: LOCAL AUTHORS RECEIVE THE RIGHT RESPONSE WHEN CHECKING INBOX")
    
    #Following/Friends 6.4 As an author, I want to know if I have "follow requests," so I can approve them.
    #Following/Friends 6.8 As an author, my node will know about my followers, who I am following, and my friends, so that I don't have to keep track of it myself.
    def test_follow_after_accept(self):
    
        #post to the follow request processing page with action being accept
        process_follow_requests_url= reverse("wiki:process_follow_request", kwargs={"author_serial":self.receiving_author.serial, "request_id":self.new_follow_request1.id}) 
        response = self.client.post(process_follow_requests_url, {'action':"accept"})
        
        
        #check for a successful redirect after the POST
        self.assertEqual(response.status_code, 302)

       
        check_follow_requests_url= reverse('wiki:check_follow_requests', kwargs={"username":self.receiving_author.displayName})
        response = self.client.get(check_follow_requests_url)

        #check for a successful Page View
        self.assertEqual(response.status_code, 200)
        

        self.new_follow_request1.refresh_from_db()

        #correct status should be accepted now
        self.assertEqual(self.new_follow_request1.state, RequestState.ACCEPTED)
        
        #check that the requester now follows the account it requested
        self.assertTrue(AuthorFollowing.objects.filter(follower=self.requesting_author1, following=self.receiving_author).exists())
        print("PASS: ACCEPTED FOLLOW REQUESTS ARE WORKING PROPERLY")
        
    #Following/Friends 6.4 As an author, I want to know if I have "follow requests," so I can approve them.    
    #Following/Friends 6.8 As an author, my node will know about my followers, who I am following, and my friends, so that I don't have to keep track of it myself.
    def test_reject_follow_request(self):
        #post to the follow request processing page with
        process_follow_requests_url= reverse("wiki:process_follow_request", kwargs={"author_serial":self.receiving_author.serial, "request_id":self.new_follow_request2.id}) 
        response = self.client.post(process_follow_requests_url, {'action':"reject"})
        
        
        #check for a successful redirect after the POST
        self.assertEqual(response.status_code, 302)

       
        check_follow_requests_url= reverse('wiki:check_follow_requests', kwargs={"username":self.receiving_author.displayName})
        response = self.client.get(check_follow_requests_url)

        #check for a successful Page View
        self.assertEqual(response.status_code, 200)
        

        self.new_follow_request2.refresh_from_db()

        #correct status should be accepted now
        self.assertEqual(self.new_follow_request2.state, RequestState.REJECTED)
    
        print("PASSED: REJECTED FOLLOW REQUESTS ARE WORKING PROPERLY")
   
    #Following/Friends 6.8 As an author, my node will know about my followers, who I am following, and my friends, so that I don't have to keep track of it myself.
    #Following/Friends 6.6 As an author, if I am following another author, and they are following me (only after both follow requests are approved), I want us to be considered friends, so that they can see my friends-only entries.
    def test_friends_created_after_mutual_follow(self):
    
        
        #post to the follow request processing page with action being accept
        process_follow_requests_url= reverse("wiki:process_follow_request", kwargs={"author_serial":self.following_author.serial, "request_id":self.new_follow_back.id}) 
        response = self.client.post(process_follow_requests_url, {'action':"accept"})
        
        
        #check for a successful redirect after the POST
        self.assertEqual(response.status_code, 302)

       
        check_follow_requests_url= reverse('wiki:check_follow_requests', kwargs={"username":self.following_author.displayName})
        response = self.client.get(check_follow_requests_url)

        #check for a successful Page View
        self.assertEqual(response.status_code, 200)
        

        self.new_follow_back.refresh_from_db()

        #correct status should be accepted now
        self.assertEqual(self.new_follow_back.state, RequestState.ACCEPTED)
    
        
        #Check that users are now friends
        self.assertTrue(AuthorFriend.objects.filter(
            (Q(friending=self.receiving_author) & Q(friended=self.following_author)) |
            (Q(friending=self.following_author) & Q(friended=self.receiving_author))
            ).exists())
        
    
  
    def tearDown(self):
        self.client.logout()    
    
class ReadingTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create user and authenticate properly
        self.user = User.objects.create_user(
            username='test_user',
            password='test_password',
        )
        self.user2 = User.objects.create_user(
            username='test_user2',
            password='test_password2'
        )

        self.author = Author.objects.create(
            id=1,
            user=self.user,
            displayName='test_author',
            description='test_description',
            github='https://github.com/test_author',
            serial=uuid.uuid4(),
            web='https://example.com/',
            profileImage = 'https://cdn-icons-png.flaticon.com/256/3135/3135823.png'
        )
        self.publicEntry = Entry.objects.create(
            title='Public Entry',
            content='This is a Public entry.',
            author=self.author,
            serial=uuid.uuid4(),
            visibility="PUBLIC"
        )
        self.unlistedEntry = Entry.objects.create(
            title='Unlisted Entry',
            content='This is a Unlisted entry.',
            author=self.author,
            serial=uuid.uuid4(),
            visibility="UNLISTED"
        )
        self.friendEntry = Entry.objects.create(
            title='Friend Entry',
            content='This is a Friend entry.',
            author=self.author,
            serial=uuid.uuid4(),
            visibility="FRIENDS"
        )
        self.admin = User.objects.create_superuser(
            username='admin_user',
            password='admin_password', 
            email='admin@ualberta.ca'
        )
        self.client.force_authenticate(user=self.admin)
        self.author2 = Author.objects.create(
            id=2,
            user=self.user2,
            displayName='test_author2',
            description='test_description2',
            github='https://github.com/test_author2',
            serial=uuid.uuid4(),
            web='https://example.com/2'
        )

        self.client.login(username='test_user2', password='test_password2')
        self.client.force_authenticate(user=self.user2)

    # Reading 3.1 As an author, I want a "stream" which shows all the entries I should know about, so I don't have to switch between different pages.
        # As an author, I want my stream page to show me all the public entries my node knows about, so I can find new people to follow.
        # As an author, I want my stream page to show me all the unlisted and friends-only entries of all the authors I follow.
        # As an author, I want my stream page to show me the most recent version of an entry if it has been edited.
        # As an author, I want my stream page to not show me entries that have been deleted
    def test_public_entries_in_stream(self):
        url = f'{BASE_PATH}/test_author2/wiki/'
        response = self.client.get(url)
        data = response.json()
        titles = [entry["title"] for entry in data]
        self.assertIn("Public Entry", titles)
        # author2 follows author for unlisted entries
        AuthorFollowing.objects.create(follower=self.author2, following=self.author)
        response = self.client.get(url)
        titles = [entry["title"] for entry in response.json()]
        self.assertIn("Unlisted Entry", titles)
        # author2 and author are friends for friend only entries
        AuthorFriend.objects.create(friending=self.author, friended=self.author2)
        response = self.client.get(url)
        titles = [entry["title"] for entry in response.json()]
        self.assertIn("Friend Entry", titles)

    # Reading 3.2 As an author, I want my "stream" page to be sorted with the most recent entries first.
    def test_most_recent_entry(self):
        new_entry = Entry.objects.create(
        title='New Entry',
        content='This should appear first.',
        author=self.author,
        serial=uuid.uuid4(),
        visibility="PUBLIC"
        )
        url = f'{BASE_PATH}/test_author2/wiki/'
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        titles = [entry["title"] for entry in response.json()]
        self.assertEqual(titles[0], "New Entry")

    def tearDown(self):
        self.client.logout()

class VisibilityTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create user and authenticate properly
        self.user = User.objects.create_user(
            username='test_user',
            password='test_password',
        )
        self.user2 = User.objects.create_user(
            username='test_user2',
            password='test_password2'
        )

        self.author = Author.objects.create(
            id=1,
            user=self.user,
            displayName='test_author',
            description='test_description',
            github='https://github.com/test_author',
            serial=uuid.uuid4(),
            web='https://example.com/',
            profileImage = 'https://cdn-icons-png.flaticon.com/256/3135/3135823.png'
        )
        self.publicEntry = Entry.objects.create(
            title='Public Entry',
            content='This is a Public entry.',
            author=self.author,
            serial=uuid.uuid4(),
            visibility="PUBLIC"
        )
        self.unlistedEntry = Entry.objects.create(
            title='Unlisted Entry',
            content='This is a Unlisted entry.',
            author=self.author,
            serial=uuid.uuid4(),
            visibility="UNLISTED"
        )
        self.friendEntry = Entry.objects.create(
            title='Friend Entry',
            content='This is a Friend entry.',
            author=self.author,
            serial=uuid.uuid4(),
            visibility="FRIENDS"
        )
        self.admin = User.objects.create_superuser(
            username='admin_user',
            password='admin_password', 
            email='admin@ualberta.ca'
        )
        self.client.force_authenticate(user=self.admin)
        self.author2 = Author.objects.create(
            id=2,
            user=self.user2,
            displayName='test_author2',
            description='test_description2',
            github='https://github.com/test_author2',
            serial=uuid.uuid4(),
            web='https://example.com/2'
        )

        self.client.login(username='test_author', password='test_password')
        self.client.force_authenticate(user=self.user2)

    # Visibility 4.1 As an author, I want to be able to make my entries "public", so that everyone can see them.
    def test_public_entry_visibility(self):
        url = f'{BASE_PATH}/entry/{self.publicEntry.serial}/'
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("visibility"), "PUBLIC")
    
    # Visibility 4.2 As an author, I want to be able to make my entries "unlisted," so that my followers see them, and anyone with the link can also see them.
    def test_unlisted_entry_visibility(self):
        url = f'{BASE_PATH}/entry/{self.unlistedEntry.serial}/'
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("visibility"), "UNLISTED")

    # Visibility 4.3 As an author, I want my friends to see my friends-only, unlisted, and public entries in their stream.
    def test_friends_only_visibility(self):
        url = f'{BASE_PATH}/entry/{self.friendEntry.serial}/'
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("visibility"), "FRIENDS")
    
    # Visibility 4.4 As an author, I want anyone following me to see my unlisted and public entries in their stream.
    def test_following_visibility(self):
        self.client.logout()
        self.client.login(username='test_author2', password='test_password2')
        AuthorFollowing.objects.create(follower=self.author2, following=self.author)
        url = f'{BASE_PATH}/test_author2/wiki/'
        response = self.client.get(url)
        data = response.json()
        titles = [entry["title"] for entry in data]
        self.assertIn("Public Entry", titles)
        self.assertIn("Unlisted Entry", titles)

    # Visibility 4.5 As an author, I want everyone to see my public entries in their stream.
    def test_public_entry_on_stream(self):
        self.client.logout()
        self.client.login(username='test_author2', password='test_password2')
        url = f'{BASE_PATH}/test_author2/wiki/'
        response = self.client.get(url)
        data = response.json()
        titles = [entry["title"] for entry in data]
        self.assertIn("Public Entry", titles)

    # Visibility 4.6 As an author, I want everyone to be able to see my public and unlisted entries, if they have a link to it.
    def test_public_unlisted_entry_link(self):
        pass

    # Visibility 4.7 As an author, I don't anyone who isn't a friend to be able to see my friends-only entries and images, so I can feel safe about writing.
    def test_friend_only_entry(self):
        pass

    # Visibility 4.8 As an author, I don't want anyone except the node admin to see my deleted entries.
    def test_deleted_entries_visibility(self):
        self.client.force_authenticate(user=self.user2)
        url = f'{BASE_PATH}/test_author2/wiki/'
        response = self.client.get(url)
        data = response.json()
        titles = [entry["title"] for entry in data]
        self.assertIn("Public Entry", titles)
        self.publicEntry.visibility = "DELETED"
        self.publicEntry.save()
        response = self.client.get(url)
        data = response.json()
        titles = [entry["title"] for entry in data]
        self.assertNotIn("Public Entry", titles)

    # Visibility 4.9 As an author, entries I create should always be visible to me until they are deleted, so I can find them to edit them or review them or get the link or whatever I want to do with them.
    def test_entry_always_visible_to_author(self):
        url = f'{BASE_PATH}/{self.author.displayName}/profile/'
        response = self.client.get(url)
        entries = response.json().get("entries", [])
        titles = [entry["title"] for entry in entries]
        self.assertIn("Public Entry", titles)
        self.assertIn("Unlisted Entry", titles)
        self.assertIn("Friend Entry", titles)

'''
class SharingTestCase(TestCase):
    # Sharing 5.1 As a reader, I can get a link to a public or unlisted entry, so I can send it to my friends over email, discord, slack, etc.
    def test_public_unlisted_link(self):
        pass

    # Sharing 5.2 As a node admin, I want to push images to users on other nodes, so that they are visible by users of other nodes. ⧟ Part 3-5 only.
    def test_push_images_to_other_nodes(self):
        pass

    #Sharing 5.3 As an author, I should be able to browse the public entries of everyone, so that I can see what's going on beyond authors I follow.
        # Note: this should include all local public entries and all public entries received in any inbox.
    def test_browse_public_entries(self):
        pass
'''