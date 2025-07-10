#!/usr/bin/env python3
"""
Test script to demonstrate the comment API format
"""

import os
import sys
import django
import requests
import json

# Add the project directory to the Python path
sys.path.append('/Users/luism/Documents/school/404/s25-project-white')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 's25_project_white.settings')
django.setup()

from wiki.models import Author, Entry, Comment, CommentLike, User
from wiki.serializers import CommentSummarySerializer, CommentLikeSummarySerializer
import uuid

def test_comment_format():
    """Test that comment objects match the required format"""
    
    # Create test user and author
    user = User.objects.create_user(
        username='test_user_api',
        password='test_password',
    )
    
    author = Author.objects.create(
        id="http://s25-project-white/api/authors/test_api_user",
        user=user,
        displayName='test_api_author',
        description='test_description',
        github='https://github.com/test_api_author',
        serial=uuid.uuid4(),
        web='https://example.com/api_user',
        profileImage='https://example.com/api_user.jpg'
    )
    
    # Create test entry
    entry = Entry.objects.create(
        title='API Test Entry',
        content='This is a test entry for API testing.',
        author=author,
        serial=uuid.uuid4(),
        visibility="PUBLIC"
    )
    
    # Create test comment
    comment = Comment.objects.create(
        entry=entry,
        author=author,
        content='This is a test comment via API.',
        contentType='text/plain'
    )
    
    # Create test comment like
    comment_like = CommentLike.objects.create(
        comment=comment,
        user=author
    )
    
    print("=== COMMENT OBJECT FORMAT ===")
    serializer = CommentSummarySerializer(comment)
    data = serializer.data
    
    print(json.dumps(data, indent=2))
    
    print("\n=== COMMENT LIKE OBJECT FORMAT ===")
    like_serializer = CommentLikeSummarySerializer(comment_like)
    like_data = like_serializer.data
    
    print(json.dumps(like_data, indent=2))
    
    print(f"\n=== API ENDPOINTS TO TEST ===")
    print(f"1. Add comment: POST /api/entry/{entry.serial}/comments/")
    print(f"2. View comments: GET /api/entry/{entry.serial}/comments/view/")
    print(f"3. Like comment: POST /api/comment/{comment.pk}/like/")
    
    # Clean up
    comment_like.delete()
    comment.delete()
    entry.delete()
    author.delete()
    user.delete()

if __name__ == "__main__":
    test_comment_format() 