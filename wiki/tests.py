from django.test import TestCase
from rest_framework.test import APIClient
from .models import Author, Entry,FollowRequest, RequestState, AuthorFollowing, AuthorFriend, Like, Comment, CommentLike
from django.contrib.auth.models import User
import uuid
from django.db.models import Q
from django.urls import reverse

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
        
        
        
        
    #Following/Friends 6.1 As an author, I want to follow local authors, so that I can see their public entries.
    #6.3 As an author, I want to be able to approve or deny other authors following me, so that I don't get followed by people I don't like.
    #6.4 As an author, I want to know if I have "follow requests," so I can approve them.
    def test_check_other_inbox(self):
        "should return 400 because only authenticated LOCAL users should be able to check their own inbox (not the requesting author)"
        url = f'{BASE_PATH}/authors/{self.requesting_author1.serial}/inbox/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        print("PASS: UNAUTHENTICATED LOCAL USERS CANNOT CHECK AN INBOX THAT IS NOT THEIRS")
    
    def test_check_correct_sending_author(self):
        "the author should be the correct sending author"
        url = f'{BASE_PATH}/authors/{self.receiving_author.serial}/inbox/'
        response = self.client.get(url)
        
        #the right sending author
        self.assertContains(response,"sending_author")
        print("PASS: THE AUTHOR SENDING FOLLOW REQUESTS IS PROPERLY PRESENTED IN THE API")
        
    def test_check_correct_initial_state(self):
        "state should be requesting when initially sent"
        url = f'{BASE_PATH}/authors/{self.receiving_author.serial}/inbox/'
        response = self.client.get(url)
        
        self.assertContains(response, "state")
        self.assertEqual(response.data[0]["state"], RequestState.REQUESTING)   
        print("PASS: THE INITIAL STATE OF THE FOLLOW REQUESTS IS CORRECT")

    #Following/Friends 6.1 As an author, I want to follow local authors, so that I can see their public entries.
    #6.3 As an author, I want to be able to approve or deny other authors following me, so that I don't get followed by people I don't like.
    def test_check_own_follow_requests(self):
        "should return 200 because only authenticated users should be able to check their own inbox (receiving author)"
        url = f'{BASE_PATH}/authors/{self.receiving_author.serial}/inbox/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        print("PASS: LOCAL AUTHORS RECEIVE THE RIGHT RESPONSE WHEN CHECKING INBOX")
    
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
        print("PASS: ACCEPTED FOLLOW REQUESTS IS WORKING PROPERLY")
    
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
   
    #6.8 As an author, my node will know about my followers, who I am following, and my friends, so that I don't have to keep track of it myself.
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
    

class LikeEntryTesting(TestCase):
    # Comments/Like User Story 1.2 Testing
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
    # Comments User Story 1.1 Testing
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
        
        url = f'{BASE_PATH}/entry/{self.entry.serial}/comments/'
        data = {'content': 'This is a witty reply!'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'comment_added')
        self.assertEqual(response.data['message'], 'Comment added successfully')
        self.assertEqual(response.data['content'], 'This is a witty reply!')
        self.assertEqual(response.data['author'], 'test_author2')
        self.assertEqual(response.data['comments_count'], 1)
        
        # Verify comment was created in database
        comment = Comment.objects.filter(entry=self.entry, author=self.author2).first()
        self.assertIsNotNone(comment)
        self.assertEqual(comment.content, 'This is a witty reply!')
        self.assertFalse(comment.is_deleted)

    def test_add_comment_nonexistent_entry(self):
        """Test commenting on a non-existent entry"""
        self.client.force_authenticate(user=self.user2)
        
        fake_serial = uuid.uuid4()
        url = f'{BASE_PATH}/entry/{fake_serial}/comments/'
        data = {'content': 'This should fail'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, 404)
        
        # Verify no comment was created
        comments = Comment.objects.filter(author=self.author2)
        self.assertEqual(comments.count(), 0)


class LikeCommentTesting(TestCase):
    # Comments/Like User Story 1.3 Testing
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
        self.assertEqual(response.data['status'], 'liked')
        self.assertEqual(response.data['message'], 'Comment liked successfully')
        self.assertEqual(response.data['likes_count'], 1)
        
        # Verify like was created in database
        like = CommentLike.objects.filter(comment=self.comment, user=self.author2).first()
        self.assertIsNotNone(like)
        self.assertFalse(like.is_deleted)


class GetEntryLikesTesting(TestCase):
    # View Likes on Public Entry User Story Testing
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
        
        self.private_entry = Entry.objects.create(
            title='Private Test Entry',
            content='This is a private test entry.',
            author=self.author1,
            serial=uuid.uuid4(),
            visibility="FRIENDS"
        )

    def test_get_entry_likes_success(self):
        """Test successful retrieval of likes for a public entry"""
        # Create some likes first
        Like.objects.create(entry=self.public_entry, user=self.author2)
        Like.objects.create(entry=self.public_entry, user=self.author3)
        
        url = f'{BASE_PATH}/entry/{self.public_entry.serial}/likes/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.data['entry_id']), str(self.public_entry.serial))
        self.assertEqual(response.data['entry_title'], 'Public Test Entry')
        self.assertEqual(response.data['total_likes'], 2)
        self.assertEqual(len(response.data['likes']), 2)
        
        # Verify like data structure
        like = response.data['likes'][0]
        self.assertIn('id', like)
        self.assertIn('author', like)
        self.assertIn('id', like['author'])
        self.assertIn('displayName', like['author'])

    def test_get_entry_likes_private_entry(self):
        """Test that non-public entries return 403 error"""
        url = f'{BASE_PATH}/entry/{self.private_entry.serial}/likes/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['error'], 'Entry is not public')



class FriendsOnlyCommentsTesting(TestCase):
    # Friends-Only Entry Comments Visibility User Story Testing
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
        self.assertEqual(response.data['entry_visibility'], 'FRIENDS')
        self.assertEqual(response.data['total_comments'], 1)  # Only friend's comment visible
        
        # Verify only friend's comment is visible
        comment = response.data['comments'][0]
        self.assertEqual(comment['content'], 'This is a comment from a friend.')
        self.assertEqual(comment['author']['displayName'], 'test_author2')

    def test_non_friend_cannot_view(self):
        """Test that non-friends cannot view comments on friends-only entries"""
        self.client.force_authenticate(user=self.user3)  # Non-friend
        
        url = f'{BASE_PATH}/entry/{self.friends_entry.serial}/comments/view/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['error'], 'Only friends can view comments on friends-only entries')

