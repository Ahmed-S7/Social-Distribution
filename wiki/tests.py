from django.test import TestCase
from rest_framework.test import APIClient
from .models import Author, Entry,FollowRequest, RequestState
from django.contrib.auth.models import User
import uuid
from django.urls import reverse

BASE_PATH = "/s25-project-white/api"

'''class IdentityTestCase(TestCase):
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
'''
class FollowRequestTesting(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create user and authenticate properly
        self.requesting_user = User.objects.create_user(
            username='test_user',
            password='test_password',
        )
        self.receiving_user = User.objects.create_user(
            username='test_user2',
            password='test_password2'
        )
        # Proper authentication for Django views
        self.client.login(username='test_user', password='test_password')
        
        self.requesting_author = Author.objects.create(
            id=1,
            user=self.requesting_user,
            displayName='sending_author',
            description='test_description',
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
            id=2,
            user=self.receiving_user,
            displayName='receiving_author2',
            description='test_description2',
            github='https://github.com/test_author2',
            serial=uuid.uuid4(),
            web='https://example.com/2'
        )
        
        self.new_follow_request= FollowRequest.objects.create(
            requester=self.requesting_author,
            requested_account=self.receiving_author
        )
    #Following/Friends 6.1 As an author, I want to follow local authors, so that I can see their public entries.
    #6.3 As an author, I want to be able to approve or deny other authors following me, so that I don't get followed by people I don't like.
    def test_check_unavailable_inbox(self):
        "should return 400 because only authenticated users should be able to check their own inbox (not the requesting author)"
        url = f'{BASE_PATH}/authors/{self.requesting_author.serial}/inbox/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
    
    def test_check_correct_sending_author(self):
        "the author should be the correct sending author"
        url = f'{BASE_PATH}/authors/{self.receiving_author.serial}/inbox/'
        response = self.client.get(url)
        
        #the right sending author
        self.assertContains(response,"sending_author")
        
    def check_correct_initial_state(self):
        "state should be requesting when initially sent"
        url = f'{BASE_PATH}/authors/{self.receiving_author.serial}/inbox/'
        response = self.client.get(url)
        
        self.assertContains(response, "state")
        self.assertEqual(response.data[0]["state"], RequestState.REQUESTING)   
    
    
    #6.4 As an author, I want to know if I have "follow requests," so I can approve them.
    def test_check_own_follow_requests(self):
        "should return 200 because only authenticated users should be able to check their own inbox (receiving author)"
        url = f'{BASE_PATH}/authors/{self.receiving_author.serial}/inbox/'
        response = self.client.get(url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
    def tearDown(self):
        self.client.logout()    
    