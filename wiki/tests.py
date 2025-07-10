from django.test import TestCase
from rest_framework.test import APIClient
from .models import Author, Entry,FollowRequest, RequestState, AuthorFollowing, AuthorFriend, Like, Comment, CommentLike
from django.contrib.auth.models import User
import uuid
from django.db.models import Q
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.db.models.signals import post_save

from rest_framework import status
BASE_PATH = "/s25-project-white/api"
BASE_URL_PATH = '/s25-project-white/'

from .serializers import CommentSummarySerializer, CommentLikeSummarySerializer


class IdentityTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create user and authenticate properly
        self.user = User.objects.create_user(
            username='test_author',
            password='test_password',
        )
        self.user2 = User.objects.create_user(
            username='test_author2',
            password='test_password2'
        )
        # Proper authentication for Django views
        self.client.login(username='test_author', password='test_password')
        
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
        url = f'{BASE_PATH}/authors/{self.author.serial}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["displayName"], "test_author")

    def test_consistent_identity_entry(self):
        url = f'{BASE_PATH}/authors/{self.author.serial}/entries/{self.entry.serial}/'
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
        url = f'{BASE_PATH}/authors/{self.author.serial}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["displayName"], self.author.displayName)
        self.assertEqual(response.data["description"], self.author.description)
        self.assertEqual(response.data["github"], self.author.github)

    # Identity 1.4 As an author, I want my profile page to show my public entries (most recent first), so they can decide if they want to follow me.
    def test_profile_public_entries(self):
        Entry.objects.create(
            title='Test Entry 2',
            content='This is a test entry 2.',
            author=self.author,
            serial=uuid.uuid4(),
            visibility="PUBLIC"
        )
        url = f'{BASE_PATH}/{self.author.displayName}/profile/'
        response = self.client.get(url)
        entries = response.data.get('entries', [])
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]['title'], "Test Entry 2")  
        self.assertEqual(entries[1]['title'], "Test Entry")

    # Identity 1.5 As an author, I want to my (new, public) GitHub activity to be automatically turned into public entries, so everyone can see my GitHub activity too.
    def test_github_activity(self):
        pass

    # Identity 1.6 As an author, I want to be able to edit my profile: name, description, picture, and GitHub.
    # Identiy 1.7 As an author, I want to be able to use my web browser to manage my profile, so I don't have to use a clunky API.
    def test_edit_profile(self):
        self.client.force_authenticate(user=self.user)
        url = f'{BASE_PATH}/authors/{self.author.serial}/'
        response = self.client.get(url)
        self.assertEqual(response.data["displayName"], self.author.displayName)
        self.assertEqual(response.data["description"], self.author.description)
        self.assertEqual(response.data["github"], self.author.github)

      
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
            displayName='outlandish_name',
            description='test_description2',
            github='https://github.com/test_author2',
            serial=uuid.uuid4(),
            web='https://example.com/2'
        )
        
        self.existing_following= AuthorFollowing.objects.create(
            following=self.receiving_author,
            follower=self.following_author
        )
        self.existing_following2= AuthorFollowing.objects.create(
            following=self.requesting_author2,
            follower=self.receiving_author
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
        url = f'{BASE_PATH}/authors/{self.requesting_author1.serial}/follow_requests/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        
        #print("PASS: UNAUTHENTICATED LOCAL USERS CANNOT CHECK AN INBOX THAT IS NOT THEIRS")
     #Following/Friends 6.8 As an author, my node will know about my followers, who I am following, and my friends, so that I don't have to keep track of it myself.
    def test_check_correct_sending_author(self):
        "the author should be the correct sending author"
        url = f'{BASE_PATH}/authors/{self.receiving_author.serial}/follow_requests/'
        response = self.client.get(url)
        
        #the right sending author
        self.assertContains(response,"sending_author")
        #print("PASS: THE AUTHOR SENDING FOLLOW REQUESTS IS PROPERLY PRESENTED IN THE API")
     
    #Following/Friends 6.8 As an author, my node will know about my followers, who I am following, and my friends, so that I don't have to keep track of it myself.    
    def test_check_correct_initial_state(self):
        "state should be requesting when initially sent"
        url = f'{BASE_PATH}/authors/{self.receiving_author.serial}/follow_requests/'
        response = self.client.get(url)
        
        self.assertContains(response, "state")
        self.assertEqual(response.data[0]["state"], RequestState.REQUESTING)   
        #print("PASS: THE INITIAL STATE OF THE FOLLOW REQUESTS IS CORRECT")

    #Following/Friends 6.1 As an author, I want to follow local authors, so that I can see their public entries.
    #Friends/Following 6.3 As an author, I want to be able to approve or deny other authors following me, so that I don't get followed by people I don't like.
    def test_check_own_follow_requests(self):
        "should return 200 because only authenticated users should be able to check their own inbox (receiving author)"
        url = f'{BASE_PATH}/authors/{self.receiving_author.serial}/follow_requests/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        #print("PASS: LOCAL AUTHORS RECEIVE THE RIGHT RESPONSE WHEN CHECKING INBOX")
    
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
        #print("PASS: ACCEPTED FOLLOW REQUESTS ARE WORKING PROPERLY")
        
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

        #correct status should be rejected now
        self.assertEqual(self.new_follow_request2.state, RequestState.REJECTED)
    
        #print("PASS: REJECTED FOLLOW REQUESTS ARE WORKING PROPERLY")
    
     
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
        #print("PASS: FRIENDSHIP CREATED AFTER MUTUAL FOLLOWING") 
    
    
    #Following/Friends 6.5 As an author, I want to unfollow authors I am following, so that I don't have to see their entries anymore.
    def test_unfollow_user(self):
        
        #"receiving_author" is following "following_author" in this specific test case
        following_author= self.receiving_author
        receiving_author= self.requesting_author2 
   
        #url to followed/unfollowed account's inbox
        url = f'{BASE_PATH}/authors/{receiving_author.serial}/followers/'
        
        #Check the API contents for the follower list of the followed author
        #ensure proper response
        response=self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        #check if the that the following account is in the JSON response of the list of followers 
        self.assertContains(response,"outlandish_name")
      
        #profile page of the followed profile's URL
        followed_profile_url= reverse("wiki:view_external_profile", kwargs={"author_serial":receiving_author.serial})
        
        #unfollow profile endpoint
        unfollow_profile_url= reverse("wiki:unfollow_profile", kwargs={"author_serial":following_author.serial,"following_id": self.existing_following2.id})
         
        #check for a successful page view
        response = self.client.get(followed_profile_url) 
        self.assertEqual(response.status_code, 200)
        
        
        #check that the following from the following author to the receiving author exists
        self.assertEqual(following_author.get_following_id_with(receiving_author), 2)
        
        #attempt to unfollow the followed profile
        response = self.client.post(unfollow_profile_url) 
        
        #Check for a successful redirect after the unfollow
        self.assertEqual(response.status_code, 302)
        
        #Check that the following no longer exists in the DB
        self.assertEqual(following_author.get_following_id_with(receiving_author), None)
        
        #Check the API contents for the follower list of the unfollowed author
        #ensure proper response
        response=self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        #check if the that the unfollowing account is not in the JSON response of the list of followers 
        self.assertNotContains(response,"outlandish_name")
        
        # print("PASS: UNFOLLOWING ACCOUNTS WORKS PROPERLY IN DB AND API")
        
    def test_friend_user(self):
        #Go through logic of creating a friendship, then unfriend and test
        
        
        #url to followed/unfollowed account's inbox
        url = f'{BASE_PATH}/authors/{self.receiving_author.serial}/followers/'
        
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


        #Confirm the following exists
        self.assertTrue(AuthorFollowing.objects.filter(follower=self.following_author, following=self.receiving_author).exists())
        current_following=AuthorFollowing.objects.get(follower=self.following_author, following=self.receiving_author)
        
        #unfriend the account
        unfollow_profile_url= reverse("wiki:unfollow_profile", kwargs={"author_serial":self.receiving_author.serial,"following_id": current_following.id})
        
        #check for a successful redirect after the POST
        response = self.client.post(unfollow_profile_url, {'action':"unfriend"})
        self.assertEqual(response.status_code, 302)
        
        
        #Check that the friendship no longer exists in the DB
        self.assertFalse(self.assertTrue(AuthorFriend.objects.filter(
            (Q(friending=self.receiving_author) & Q(friended=self.following_author)) |
            (Q(friending=self.following_author) & Q(friended=self.receiving_author))
            ).exists()))

        #Check the following is also subsequently deleted
        self.assertFalse(self.following_author.is_following(self.receiving_author))
        
        #Check the API contents for the follower list of the unfollowed author
        #ensure proper response
        response=self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        #check if the that the unfollowing account is not in the JSON response of the list of followers 
        self.assertNotContains(response,self.following_author.displayName)
        
         
        #print("PASS: UNFRIENDING ACCOUNTS WORKS PROPERLY IN DB AND API")
        
    def tearDown(self):
        self.client.logout()    

class LikeEntryTesting(TestCase):
    # Liking An Entry Testing
    # Comments/Like User Story 1.2 Testing
    # Comments/Likes 7.2 As an author, I want to like entries that I can access, so I can show my appreciation.
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.user1 = User.objects.create_user(
            username='test_user1',
            password='test_password1',
        )
        self.user2 = User.objects.create_user(
            username='test_user2', 
            password='test_password2'
        )
        
        # Create test authors
        self.author1 = Author.objects.create(
            id="http://s25-project-white/api/authors/test1",
            user=self.user1,
            displayName='test_author1',
            description='test_description1',
            github='https://github.com/test_author1',
            serial=uuid.uuid4(),
            web='https://example.com/1',
            profileImage='https://example.com/image1.jpg'
        )
        
        self.author2 = Author.objects.create(
            id="http://s25-project-white/api/authors/test2",
            user=self.user2,
            displayName='test_author2', 
            description='test_description2',
            github='https://github.com/test_author2',
            serial=uuid.uuid4(),
            web='https://example.com/2',
            profileImage='https://example.com/image2.jpg'
        )
        
        # Create test entry
        self.entry = Entry.objects.create(
            title='Test Entry',
            content='This is a test entry.',
            author=self.author1,
            serial=uuid.uuid4(),
            visibility="PUBLIC"
        )
    
    def test_like_entry_success(self):
        """Test successful like of an entry"""
        self.client.force_authenticate(user=self.user2)
        url = f'{BASE_PATH}/entry/{self.entry.serial}/like/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'liked')
        self.assertEqual(response.data['message'], 'Entry liked successfully')
        self.assertEqual(response.data['likes_count'], 1)
        
        # Verify like was created in database
        like = Like.objects.filter(entry=self.entry, user=self.author2).first()
        self.assertIsNotNone(like)
        self.assertFalse(like.is_deleted)

    
    def test_like_entry_already_liked(self):
        """Test that user cannot like the same entry twice"""
        self.client.force_authenticate(user=self.user2)
        
        # First like
        url = f'{BASE_PATH}/entry/{self.entry.serial}/like/'
        response1 = self.client.post(url)
        self.assertEqual(response1.status_code, 201)
        
        # Second like attempt
        response2 = self.client.post(url)
        self.assertEqual(response2.status_code, 400)
        self.assertEqual(response2.data['status'], 'already_liked')
        self.assertEqual(response2.data['message'], 'You have already liked this entry')
        
        # Verify only one like exists
        likes = Like.objects.filter(entry=self.entry, user=self.author2)
        self.assertEqual(likes.count(), 1)

class CommentEntryTesting(TestCase):
    # Commenting On An Entry Testing
    # Comments User Story 1.1 Testing
    # Comments/Likes 7.1 As an author, I want to comment on entries that I can access, so I can make a witty reply.
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.user1 = User.objects.create_user(
            username='test_user1',
            password='test_password1',
        )
        self.user2 = User.objects.create_user(
            username='test_user2', 
            password='test_password2'
        )
        
        # Create test authors
        self.author1 = Author.objects.create(
            id="http://s25-project-white/api/authors/test1",
            user=self.user1,
            displayName='test_author1',
            description='test_description1',
            github='https://github.com/test_author1',
            serial=uuid.uuid4(),
            web='https://example.com/1',
            profileImage='https://example.com/image1.jpg'
        )
        
        self.author2 = Author.objects.create(
            id="http://s25-project-white/api/authors/test2",
            user=self.user2,
            displayName='test_author2', 
            description='test_description2',
            github='https://github.com/test_author2',
            serial=uuid.uuid4(),
            web='https://example.com/2',
            profileImage='https://example.com/image2.jpg'
        )
        
        # Create test entry
        self.entry = Entry.objects.create(
            title='Test Entry',
            content='This is a test entry.',
            author=self.author1,
            serial=uuid.uuid4(),
            visibility="PUBLIC"
        )

    def test_add_comment_success(self):
        """Test successful comment addition to an entry"""
        self.client.force_authenticate(user=self.user2)
        
        url = f'{BASE_PATH}/authors/{self.author2.serial}/commented/'
        data = {
            'type': 'comment',
            'comment': 'This is a witty reply!',
            'contentType': 'text/plain',
            'entry': self.entry.serial
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, 201)
        # Check that we get a properly formatted comment object
        self.assertEqual(response.data['type'], 'comment')
        self.assertEqual(response.data['comment'], 'This is a witty reply!')
        self.assertEqual(response.data['author']['displayName'], 'test_author2')
        self.assertEqual(response.data['contentType'], 'text/plain')
        
        # Verify comment was created in database
        comment = Comment.objects.filter(entry=self.entry, author=self.author2).first()
        self.assertIsNotNone(comment)
        self.assertEqual(comment.content, 'This is a witty reply!')
        self.assertFalse(comment.is_deleted)

    def test_add_comment_nonexistent_entry(self):
        """Test commenting on a non-existent entry"""
        self.client.force_authenticate(user=self.user2)
        
        fake_serial = uuid.uuid4()
        url = f'{BASE_PATH}/authors/{self.author2.serial}/commented/'
        data = {
            'type': 'comment',
            'comment': 'This should fail',
            'contentType': 'text/plain',
            'entry': fake_serial
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, 404)
        
        # Verify no comment was created
        comments = Comment.objects.filter(author=self.author2)
        self.assertEqual(comments.count(), 0)


class LikeCommentTesting(TestCase):
    # Liking An Entry Testing
    # Comments/Like User Story 1.3 Testing
    # Comments/Likes 7.3 As an author, I want to like comments that I can access, so I can show my appreciation.
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.user1 = User.objects.create_user(
            username='test_user1',
            password='test_password1',
        )
        self.user2 = User.objects.create_user(
            username='test_user2', 
            password='test_password2'
        )
        
        # Create test authors
        self.author1 = Author.objects.create(
            id="http://s25-project-white/api/authors/test1",
            user=self.user1,
            displayName='test_author1',
            description='test_description1',
            github='https://github.com/test_author1',
            serial=uuid.uuid4(),
            web='https://example.com/1',
            profileImage='https://example.com/image1.jpg'
        )
        
        self.author2 = Author.objects.create(
            id="http://s25-project-white/api/authors/test2",
            user=self.user2,
            displayName='test_author2', 
            description='test_description2',
            github='https://github.com/test_author2',
            serial=uuid.uuid4(),
            web='https://example.com/2',
            profileImage='https://example.com/image2.jpg'
        )
        
        # Create test entry
        self.entry = Entry.objects.create(
            title='Test Entry',
            content='This is a test entry.',
            author=self.author1,
            serial=uuid.uuid4(),
            visibility="PUBLIC"
        )
        
        # Create test comment
        self.comment = Comment.objects.create(
            entry=self.entry,
            author=self.author1,
            content='This is a test comment.'
        )

    def test_like_comment_success(self):
        """Test successful like of a comment"""
        self.client.force_authenticate(user=self.user2)
        
        url = f'{BASE_PATH}/comment/{self.comment.id}/like/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 201)
        # Check that we get a properly formatted like object
        self.assertEqual(response.data['type'], 'like')
        self.assertEqual(response.data['author']['displayName'], 'test_author2')
        
        # Verify like was created in database
        like = CommentLike.objects.filter(comment=self.comment, user=self.author2).first()
        self.assertIsNotNone(like)
        self.assertFalse(like.is_deleted)


class GetEntryLikesTesting(TestCase):
    # View Likes on Public Entry User Story Testing
    # User Story 1.4 testing
    # Comments/Likes 7.4 As an author, when someone sends me a public entry I want to see the likes, so I can tell if it's good or not.
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.user1 = User.objects.create_user(
            username='test_user1',
            password='test_password1',
        )
        self.user2 = User.objects.create_user(
            username='test_user2', 
            password='test_password2'
        )
        self.user3 = User.objects.create_user(
            username='test_user3',
            password='test_password3'
        )
        
        # Create test authors
        self.author1 = Author.objects.create(
            id="http://s25-project-white/api/authors/test1",
            user=self.user1,
            displayName='test_author1',
            description='test_description1',
            github='https://github.com/test_author1',
            serial=uuid.uuid4(),
            web='https://example.com/1',
            profileImage='https://example.com/image1.jpg'
        )
        
        self.author2 = Author.objects.create(
            id="http://s25-project-white/api/authors/test2",
            user=self.user2,
            displayName='test_author2', 
            description='test_description2',
            github='https://github.com/test_author2',
            serial=uuid.uuid4(),
            web='https://example.com/2',
            profileImage='https://example.com/image1.jpg'
        )
        
        self.author3 = Author.objects.create(
            id="http://s25-project-white/api/authors/test3",
            user=self.user3,
            displayName='test_author3',
            description='test_description3',
            github='https://github.com/test_author3',
            serial=uuid.uuid4(),
            web='https://example.com/3',
            profileImage='https://example.com/image1.jpg'
        )
        
        # Create test entries
        self.public_entry = Entry.objects.create(
            title='Public Test Entry',
            content='This is a public test entry.',
            author=self.author1,
            serial=uuid.uuid4(),
            visibility="PUBLIC"
        )
        
        self.friends_only_entry = Entry.objects.create(
            title='Friends Only Entry',
            content='This is a Friends Only test entry.',
            author=self.author1,
            serial=uuid.uuid4(),
            visibility="FRIENDS"
        )
        
        self.unlisted_entry = Entry.objects.create(
            title='Unlisted Entry',
            content='This is an Unlisted test entry.',
            author=self.author1,
            serial=uuid.uuid4(),
            visibility="FRIENDS"
        )

    def test_get_entry_likes_success(self):
        """Test successful retrieval of likes for a public entry"""
        
        self.client.logout()
        self.client.login(username='test_user1', password='test_password1')
        # Create some likes first
        Like.objects.create(entry=self.public_entry, user=self.author2)
        Like.objects.create(entry=self.public_entry, user=self.author3)
        
        url = f'{BASE_PATH}/authors/{self.author1.serial}/entries/{self.public_entry.serial}/likes/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.data['type']), "likes")
        self.assertEqual(response.data['web'], self.public_entry.web)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['src']), 2)
        
        # Verify like data structure
        like = response.data['src'][0]
        self.assertIn('id', like)
        self.assertIn('author', like)
        self.assertIn('id', like['author'])
        self.assertIn('displayName', like['author'])

    def test_get_entry_likes_unauthorized_friends(self):
        """Test that non-public entries return 403 error"""
        self.client.logout()
        self.client.login(username='test_user3', password='test_password3')
        
         #http://127.0.0.1:8000/s25-project-white/api/authors/f802fa6a-c7e5-40e5-907f-6ff25b63ff80/entries/c62fadbb-2f40-4df6-8cf7-0830460a396e/likes/
        url = f'{BASE_PATH}/authors/{self.author1.serial}/entries/{self.friends_only_entry.serial}/likes/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 403)
        
    def test_get_entry_likes_unauthorized_unlisted(self):
        """Test that non-public entries return 403 error"""
        self.client.logout()
        self.client.login(username='test_user3', password='test_password3')
        
         #http://127.0.0.1:8000/s25-project-white/api/authors/f802fa6a-c7e5-40e5-907f-6ff25b63ff80/entries/c62fadbb-2f40-4df6-8cf7-0830460a396e/likes/
        url = f'{BASE_PATH}/authors/{self.author1.serial}/entries/{self.unlisted_entry.serial}/likes/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 403)
        
   



class FriendsOnlyCommentsTesting(TestCase):
    # Friends-Only Entry Comments Visibility User Story Testing
    # User Story 1.5 testing
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.user1 = User.objects.create_user(
            username='test_user1',
            password='test_password1',
        )
        self.user2 = User.objects.create_user(
            username='test_user2', 
            password='test_password2'
        )
        self.user3 = User.objects.create_user(
            username='test_user3',
            password='test_password3'
        )
        
        # Create test authors
        self.author1 = Author.objects.create(
            id="http://s25-project-white/api/authors/test1",
            user=self.user1,
            displayName='test_author1',
            description='test_description1',
            github='https://github.com/test_author1',
            serial=uuid.uuid4(),
            web='https://example.com/1',
            profileImage=None
        )
        
        self.author2 = Author.objects.create(
            id="http://s25-project-white/api/authors/test2",
            user=self.user2,
            displayName='test_author2', 
            description='test_description2',
            github='https://github.com/test_author2',
            serial=uuid.uuid4(),
            web='https://example.com/2',
            profileImage=None
        )
        
        self.author3 = Author.objects.create(
            id="http://s25-project-white/api/authors/test3",
            user=self.user3,
            displayName='test_author3',
            description='test_description3',
            github='https://github.com/test_author3',
            serial=uuid.uuid4(),
            web='https://example.com/3',
            profileImage=None
        )
        
        
        # Create friends only entries
        self.friends_entry = Entry.objects.create(
            title='Friends-Only Test Entry',
            content='This is a friends-only test entry.',
            author=self.author1,
            serial=uuid.uuid4(),
            visibility="FRIENDS"
        )
        
        # Create friendship between author1 and author2
        self.friendship = AuthorFriend.objects.create(
            friending=self.author1,
            friended=self.author2
        )
        
        # Create comments on friends-only entry
        self.comment1 = Comment.objects.create(
            entry=self.friends_entry,
            author=self.author2,  # Friend
            content='This is a comment from a friend.'
        )

    def test_friends_can_view(self):
        """Test that friends can view comments on friends-only entries"""
        self.client.force_authenticate(user=self.user2)  # Friend
        
        url = f'{BASE_PATH}/entry/{self.friends_entry.serial}/comments/view/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # The API now returns an array of comment objects directly
        self.assertEqual(len(response.data), 1)  # Only friend's comment visible
        
        # Verify only friend's comment is visible
        comment = response.data[0]
        self.assertEqual(comment['comment'], 'This is a comment from a friend.')
        self.assertEqual(comment['author']['displayName'], 'test_author2')

    def test_non_friend_cannot_view(self):
        """Test that non-friends cannot view comments on friends-only entries"""
        self.client.force_authenticate(user=self.user3)  # Non-friend
        
        url = f'{BASE_PATH}/entry/{self.friends_entry.serial}/comments/view/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['error'], 'Only friends can view comments on friends-only entries')


class ReadingTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create user and authenticate properly
        self.user = User.objects.create_user(
            username='test_author',
            password='test_password',
        )
        self.user2 = User.objects.create_user(
            username='test_author2',
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
        self.client.force_authenticate(user=self.user2)
        url = f'{BASE_PATH}/test_author2/wiki/'
        response = self.client.get(url)
        titles = [entry["title"] for entry in response.json()]
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
        Entry.objects.create(
        title='New Entry',
        content='This should appear first.',
        author=self.author,
        serial=uuid.uuid4(),
        visibility="PUBLIC"
        )
        self.client.force_authenticate(user=self.user2)
        url = f'{BASE_PATH}/test_author2/wiki/'
        response = self.client.get(url)
        titles = [entry["title"] for entry in response.json()]
        self.assertEqual(titles[0], "New Entry")

    def tearDown(self):
        self.client.logout()

        
class VisibilityTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create user and authenticate properly
        self.user = User.objects.create_user(
            username='test_author',
            password='test_password',
        )
        self.user2 = User.objects.create_user(
            username='test_author2',
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
        url = f'{BASE_PATH}/authors/{self.author.serial}/entries/{self.publicEntry.serial}/'
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("visibility"), "PUBLIC")
    
    # Visibility 4.2 As an author, I want to be able to make my entries "unlisted," so that my followers see them, and anyone with the link can also see them.
    def test_unlisted_entry_visibility(self):
        url = f'{BASE_PATH}/authors/{self.author.serial}/entries/{self.unlistedEntry.serial}/'
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("visibility"), "UNLISTED")

    # Visibility 4.3 As an author, I want to be able to make my entries "friends-only," so that I don't have to worry about people I don't know seeing them.
    def test_friends_only_entry_visibility(self):
        url = f'{BASE_PATH}/authors/{self.author.serial}/entries/{self.friendEntry.serial}/'
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("visibility"), "FRIENDS")

    # Visibility 4.4 As an author, I want my friends to see my friends-only, unlisted, and public entries in their stream.
    def test_friends_only_visibility(self):
        self.client.force_authenticate(user=self.user2)
        AuthorFriend.objects.create(friending=self.author2, friended=self.author)
        AuthorFollowing.objects.create(follower=self.author2, following=self.author)
        url = f'{BASE_PATH}/test_author2/wiki/'
        response = self.client.get(url)
        titles = [entry["title"] for entry in response.json()]
        self.assertIn("Public Entry", titles)
        self.assertIn("Unlisted Entry", titles)
        self.assertIn("Friend Entry", titles)
    
    # Visibility 4.5 As an author, I want anyone following me to see my unlisted and public entries in their stream.
    def test_following_visibility(self):
        self.client.force_authenticate(user=self.user2)
        AuthorFollowing.objects.create(follower=self.author2, following=self.author)
        url = f'{BASE_PATH}/test_author2/wiki/'
        response = self.client.get(url)
        titles = [entry["title"] for entry in response.json()]
        self.assertIn("Public Entry", titles)
        self.assertIn("Unlisted Entry", titles)

    # Visibility 4.6 As an author, I want everyone to see my public entries in their stream.
    def test_public_entry_on_stream(self):
        self.client.force_authenticate(user=self.user2)
        url = f'{BASE_PATH}/test_author2/wiki/'
        response = self.client.get(url)
        titles = [entry["title"] for entry in response.json()]
        self.assertIn("Public Entry", titles)

    # Visibility 4.7 As an author, I want everyone to be able to see my public and unlisted entries, if they have a link to it.
    def test_public_unlisted_entry_link(self):
        url = f'{BASE_PATH}/authors/{self.author.serial}/entries/{self.unlistedEntry.serial}/'
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.unlistedEntry.title)
        self.assertContains(response, self.unlistedEntry.content)
        url = f'{BASE_PATH}/authors/{self.author.serial}/entries/{self.publicEntry.serial}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.publicEntry.title)
        self.assertContains(response, self.publicEntry.content)

    # Visibility 4.8 As an author, I don't anyone who isn't a friend to be able to see my friends-only entries and images, so I can feel safe about writing.
    def test_friend_only_entry(self):
        self.client.force_authenticate(user=self.user2)
        friendship = AuthorFriend.objects.create(friending=self.author2, friended=self.author)
        url = f'{BASE_PATH}/test_author2/wiki/'
        response = self.client.get(url)
        titles = [entry["title"] for entry in response.json()]
        self.assertIn("Friend Entry", titles)
        friendship.delete()    
        response = self.client.get(url)
        titles = [entry["title"] for entry in response.json()]
        self.assertNotIn("Friend Entry", titles)

    # Visibility 4.9 As an author, I don't want anyone except the node admin to see my deleted entries.
    def test_deleted_entries_visibility(self):
        self.client.force_authenticate(user=self.user2)
        url = f'{BASE_PATH}/test_author2/wiki/'
        response = self.client.get(url)
        titles = [entry["title"] for entry in response.json()]
        self.assertIn("Public Entry", titles)
        self.publicEntry.visibility = "DELETED"
        self.publicEntry.save()
        response = self.client.get(url)
        titles = [entry["title"] for entry in response.json()]
        self.assertNotIn("Public Entry", titles)

    # Visibility 4.10 As an author, entries I create should always be visible to me until they are deleted, so I can find them to edit them or review them or get the link or whatever I want to do with them.
    def test_entry_always_visible_to_author(self):
        url = f'{BASE_PATH}/{self.author.displayName}/profile/'
        response = self.client.get(url)
        entries = response.json().get('entries', [])
        titles = [entry["title"] for entry in entries]
        self.assertIn("Public Entry", titles)
        self.assertIn("Unlisted Entry", titles)
        self.assertIn("Friend Entry", titles)


class EntryUserStoriesTest(TestCase):   # POSTING USER STORIES
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='author1', password='testpass')
        self.author = Author.objects.create(user=self.user, displayName='author1', id='http://localhost:8000/api/authors/1', host='http://localhost:8000/api/', web='http://localhost:8000/authors/1')
        self.client.login(username='author1', password='testpass')

    # US 2.1: As an author, I want to make entries, so I can share my thoughts and pictures with other local authors.
    def test_create_text_entry(self):
        """User Story: As an author, I want to make entries (plain text) to share with other local authors."""
        response = self.client.post(reverse('wiki:create_entry'), {
            'title': 'Plain Text Entry',
            'content': 'Hello world!',
            'contentType': 'text/plain',
            'visibility': 'PUBLIC',
        })
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(Entry.objects.filter(title='Plain Text Entry').exists())

    # US 2.2: As an author, I want my node to send my entries to my remote followers and friends, so that remote authors following me can see them.
    def test_send_entry_to_remote(self):
        """User Story: As an author, I want my node to send my entries to my remote followers and friends."""
        # Part 3 - 5
        pass

    # US 2.3: As an author, I want to edit my entries locally, so that I'm not stuck with a typo on a popular entry.
    def test_edit_entry(self):
        """User Story: As an author, I want to edit my entries locally."""
        entry = Entry.objects.create(title='Old Title', content='Old', author=self.author, contentType='text/plain', visibility='PUBLIC')
        response = self.client.post(reverse('wiki:edit_entry', args=[entry.serial]), {
            'title': 'New Title',
            'content': 'New content',
            'contentType': 'text/plain',
            'visibility': 'PUBLIC',
        })
        entry.refresh_from_db()
        self.assertEqual(entry.title, 'New Title')

    # US 2.4: As an author, I want my node to re-send entries I've edited to everywhere they were already sent, so that people don't keep seeing the old version.
    def test_resend_edited_entry_to_remote(self):
        """User Story: As an author, I want my node to re-send entries I've edited to everywhere they were already sent."""
        # Part 3 - 5
        pass

    # US 2.5: As an author, entries I make can be in CommonMark (Markdown), so I can give my entries some basic formatting.
    def test_create_markdown_entry(self):
        """Test creating an entry with markdown formatting"""
        markdown_content = """# My Markdown Entry

This is **bold text** and this is *italic text*.

Here's a list:

- Item 1
- Item 2
- Item 3

> This is a blockquote

You can also use `code` inline."""

        entry = Entry.objects.create(
            title='Markdown Test Entry',
            content=markdown_content,
            author=self.author,
            serial=uuid.uuid4(),
            visibility="PUBLIC",
            contentType="text/markdown"
        )
        
        # Test that the entry was created with markdown content type
        self.assertEqual(entry.contentType, "text/markdown")
        self.assertEqual(entry.content, markdown_content)
        
        # Test that get_formatted_content returns HTML
        formatted_content = entry.get_formatted_content()
        self.assertIn('<h1>', formatted_content)  # Should have h1 tag
        self.assertIn('<strong>', formatted_content)  # Should have bold
        self.assertIn('<em>', formatted_content)  # Should have italic
        self.assertIn('<ul>', formatted_content)  # Should have list
        self.assertIn('<blockquote>', formatted_content)  # Should have blockquote
        self.assertIn('<code>', formatted_content)  # Should have code

    # US 2.8: As an author, entries I create that are in CommonMark can link to images, so that I can illustrate my entries.
    def test_markdown_entry_can_link_to_images(self):
        """Test that markdown entries can include images"""
        markdown_with_images = """# Entry with Images

Here's a cute cat:
![Cat](https://placekitten.com/400/300)

And a landscape:
![Landscape](https://picsum.photos/500/300)

**Bold text** with images works too!"""

        entry = Entry.objects.create(
            title='Markdown Images Test',
            content=markdown_with_images,
            author=self.author,
            serial=uuid.uuid4(),
            visibility="PUBLIC",
            contentType="text/markdown"
        )
        
        # Test that the entry was created with markdown content type
        self.assertEqual(entry.contentType, "text/markdown")
        
        # Test that get_formatted_content includes image tags
        formatted_content = entry.get_formatted_content()
        self.assertIn('<img', formatted_content)  # Should have img tags
        self.assertIn('src="https://placekitten.com/400/300"', formatted_content)
        self.assertIn('src="https://picsum.photos/500/300"', formatted_content)
        self.assertIn('alt="Cat"', formatted_content)
        self.assertIn('alt="Landscape"', formatted_content)



    # US 2.6: As an author, entries I make can be in simple plain text, because I don't always want all the formatting features of CommonMark.
    def test_create_text_entry_again(self):
        """User Story: As an author, entries I make can be in simple plain text."""
        response = self.client.post(reverse('wiki:create_entry'), {
            'title': 'Another Plain Text Entry',
            'content': 'Just text.',
            'contentType': 'text/plain',
            'visibility': 'PUBLIC',
        })
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(Entry.objects.filter(title='Another Plain Text Entry', contentType='text/plain').exists())

    # US 2.7: As an author, entries I create can be images, so that I can share pictures and drawings.
    def test_create_image_entry(self):
        """User Story: As an author, entries I create can be images."""
        # Image US
        pass

    # US 2.9: As an author, I want to delete my own entries locally, so I can remove entries that are out of date or made by mistake.
    def test_delete_entry(self):
        """User Story: As an author, I want to delete my own entries locally."""
        entry = Entry.objects.create(title='To Delete', content='...', author=self.author, contentType='text/plain', visibility='PUBLIC')
        response = self.client.post(reverse('wiki:delete_entry', args=[entry.serial]))
        entry.refresh_from_db()
        self.assertTrue(entry.is_deleted)

    # US 2.10: As an author, I want my node to re-send entries I've deleted to everyone they were already sent to, so I know remote users don't keep seeing my deleted entries forever.
    def test_resend_deleted_entry_to_remote(self):
        """User Story: As an author, I want my node to re-send entries I've deleted to everyone they were already sent to."""
        # Part 3 - 5
        pass

    # US 2.11: As an author, I want to be able to use my web-browser to manage/author my entries, so I don't have to use a clunky API.
    def test_web_ui_entry_creation(self):
        """User Story: As an author, I want to use my web-browser to manage/author my entries."""
        response = self.client.get(reverse('wiki:create_entry'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<form', response.content)

    # US 2.12: As an author, other authors cannot modify my entries, so that I don't get impersonated.
    def test_other_author_cannot_edit(self):
        """User Story: As an author, other authors cannot modify my entries."""
        entry = Entry.objects.create(title='Protected', content='...', author=self.author, contentType='text/plain', visibility='PUBLIC')
        user2 = User.objects.create_user(username='author2', password='testpass2')
        author2 = Author.objects.create(user=user2, displayName='author2', id='http://localhost:8000/api/authors/2', host='http://localhost:8000/api/', web='http://localhost:8000/authors/2')
        self.client.logout()
        self.client.login(username='author2', password='testpass2')
        response = self.client.post(reverse('wiki:edit_entry', args=[entry.serial]), {
            'title': 'Hacked',
            'content': 'Hacked',
            'contentType': 'text/plain',
            'visibility': 'PUBLIC',
        })
        entry.refresh_from_db()
        self.assertNotEqual(entry.title, 'Hacked')

class SharingTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create user and authenticate properly
        self.user = User.objects.create_user(
            username='test_author',
            password='test_password',
        )
        self.user2 = User.objects.create_user(
            username='test_author2',
            password='test_password2'
        )
        self.user2.is_active = True
        self.user2.save()
        self.user.is_active = True
        self.user.save()
        self.author2 = Author.objects.create(
            id=2,
            user=self.user2,
            displayName='test_author2',
            description='test_description2',
            github='https://github.com/test_author2',
            serial=uuid.uuid4(),
            web='https://example.com/2'
        )
        self.author = Author.objects.create(
            id=1,
            user=self.user,
            displayName='test_author',
            description='test_description',
            github='https://github.com/test_author',
            serial=uuid.uuid4(),
            web='https://example.com/',
        )
        self.unlistedEntry = Entry.objects.create(
            title='Unlisted Entry',
            content='This is a Unlisted entry.',
            author=self.author,
            serial=uuid.uuid4(),
            visibility="UNLISTED"
        )
        self.publicEntry = Entry.objects.create(
            title='Public Entry',
            content='This is a Public entry.',
            author=self.author,
            serial=uuid.uuid4(),
            visibility="PUBLIC"
        )
    # Sharing 5.1 As a reader, I can get a link to a public or unlisted entry, so I can send it to my friends over email, discord, slack, etc.
    def test_public_unlisted_link(self):
        url = f'{BASE_PATH}/authors/{self.author.serial}/entries/{self.unlistedEntry.serial}/'
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.unlistedEntry.title)
        self.assertContains(response, self.unlistedEntry.content)

    # Sharing 5.2 As a node admin, I want to push images to users on other nodes, so that they are visible by users of other nodes. ⧟ Part 3-5 only.
    def test_push_images_to_other_nodes(self):
        pass

    #Sharing 5.3 As an author, I should be able to browse the public entries of everyone, so that I can see what's going on beyond authors I follow.
        # Note: this should include all local public entries and all public entries received in any inbox.
    def test_browse_public_entries(self):
        self.client.force_authenticate(user=self.user2)
        url = f'{BASE_PATH}/test_author2/wiki/'
        response = self.client.get(url)
        titles = [entry["title"] for entry in response.json()]
        self.assertIn("Public Entry", titles)

class NodeManagementTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='admin_user',
            password='admin_password', 
            email='admin@ualberta.ca'
        )
        self.register_api_url = f'{BASE_PATH}/register/'
        self.login_api_url = f'{BASE_PATH}/login/'
    
    # Node Management 8.3 As a node admin, I want to be able to allow users to sign-up but require my approval to complete sign-up and use my node, so that I can prevent unwanted users and spambots.
    def test_sign_up_approval(self):
        register_data = {
            'username': 'pending_user',
            'password': 'pass',
            'confirm_password': 'pass',
        }
        response = self.client.post(self.register_api_url, register_data, format='json')
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username='pending_user')
        self.assertFalse(user.is_active)
        login_data = {
            'username': 'pending_user',
            'password': 'pass',
        }
        response = self.client.post(self.login_api_url, login_data, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertIn("pending admin approval", response.json().get('detail', ''))
        user.is_active = True
        user.save()
        response = self.client.post(self.login_api_url, login_data, format='json')
        self.assertEqual(response.status_code, 200)


class SingleLikeAPITesting(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create users and authors
        self.user = User.objects.create_user(
            username='test_author',
            password='test_password',
        )
        self.user2 = User.objects.create_user(
            username='test_author2',
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
            profileImage='https://cdn-icons-png.flaticon.com/256/3135/3135823.png'
        )
        
        self.author2 = Author.objects.create(
            id=2,
            user=self.user2,
            displayName='test_author2',
            description='test_description2',
            github='https://github.com/test_author2',
            serial=uuid.uuid4(),
            web='https://example.com/2'
        )
        
        # Create an entry
        self.entry = Entry.objects.create(
            title='Test Entry',
            content='This is a test entry.',
            author=self.author2,
            serial=uuid.uuid4(),
            visibility="PUBLIC"
        )
        
        # Create a comment
        self.comment = Comment.objects.create(
            content='Test comment',
            author=self.author2,
            entry=self.entry,
            contentType='text/plain'
        )
        
        # Create likes
        self.entry_like = Like.objects.create(
            user=self.author,
            entry=self.entry
        )
        
        self.comment_like = CommentLike.objects.create(
            user=self.author,
            comment=self.comment
        )

    def test_get_single_entry_like(self):
        """Test getting a single entry like by its serial"""
        url = f'{BASE_PATH}/authors/{self.author.serial}/liked/{self.entry_like.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['type'], 'like')
        self.assertEqual(response.data['author']['displayName'], 'test_author')
        self.assertIn('published', response.data)
        self.assertIn('id', response.data)
        self.assertIn('object', response.data)

    def test_get_single_comment_like(self):
        """Test getting a single comment like by its serial"""
        url = f'{BASE_PATH}/authors/{self.author.serial}/liked/{self.comment_like.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['type'], 'like')
        self.assertEqual(response.data['author']['displayName'], 'test_author')
        self.assertIn('published', response.data)
        self.assertIn('id', response.data)
        self.assertIn('object', response.data)

    def test_get_nonexistent_like(self):
        """Test getting a like that doesn't exist"""
        url = f'{BASE_PATH}/authors/{self.author.serial}/liked/99999/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.data)

    def test_get_like_wrong_author(self):
        """Test getting a like with wrong author serial"""
        url = f'{BASE_PATH}/authors/{self.author2.serial}/liked/{self.entry_like.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.data)


class AuthorLikesAPITesting(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create users and authors
        self.user = User.objects.create_user(
            username='test_author',
            password='test_password',
        )
        self.user2 = User.objects.create_user(
            username='test_author2',
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
            profileImage='https://cdn-icons-png.flaticon.com/256/3135/3135823.png'
        )
        
        self.author2 = Author.objects.create(
            id=2,
            user=self.user2,
            displayName='test_author2',
            description='test_description2',
            github='https://github.com/test_author2',
            serial=uuid.uuid4(),
            web='https://example.com/2'
        )
        
        # Create entries
        self.entry1 = Entry.objects.create(
            title='Test Entry 1',
            content='This is test entry 1.',
            author=self.author2,
            serial=uuid.uuid4(),
            visibility="PUBLIC"
        )
        
        self.entry2 = Entry.objects.create(
            title='Test Entry 2',
            content='This is test entry 2.',
            author=self.author2,
            serial=uuid.uuid4(),
            visibility="PUBLIC"
        )
        
        # Create comments
        self.comment1 = Comment.objects.create(
            content='Test comment 1',
            author=self.author2,
            entry=self.entry1,
            contentType='text/plain'
        )
        
        self.comment2 = Comment.objects.create(
            content='Test comment 2',
            author=self.author2,
            entry=self.entry2,
            contentType='text/plain'
        )
        
        # Create likes by the first author
        self.entry_like1 = Like.objects.create(
            user=self.author,
            entry=self.entry1
        )
        
        self.entry_like2 = Like.objects.create(
            user=self.author,
            entry=self.entry2
        )
        
        self.comment_like1 = CommentLike.objects.create(
            user=self.author,
            comment=self.comment1
        )
        
        self.comment_like2 = CommentLike.objects.create(
            user=self.author,
            comment=self.comment2
        )

    def test_get_author_likes_success(self):
        """Test getting all likes by an author"""
        url = f'{BASE_PATH}/authors/{self.author.serial}/liked/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['type'], 'likes')
        self.assertIn('web', response.data)
        self.assertIn('id', response.data)
        self.assertIn('page_number', response.data)
        self.assertIn('size', response.data)
        self.assertIn('count', response.data)
        self.assertIn('src', response.data)
        
        # Should have 4 likes total (2 entry likes + 2 comment likes)
        self.assertEqual(response.data['count'], 4)
        self.assertEqual(len(response.data['src']), 4)
        
        # Check that all likes have the correct format
        for like in response.data['src']:
            self.assertEqual(like['type'], 'like')
            self.assertIn('author', like)
            self.assertIn('published', like)
            self.assertIn('id', like)
            self.assertIn('object', like)
            self.assertEqual(like['author']['displayName'], 'test_author')

    def test_get_author_likes_empty(self):
        """Test getting likes for an author with no likes"""
        url = f'{BASE_PATH}/authors/{self.author2.serial}/liked/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['type'], 'likes')
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['src']), 0)

