"""
Views package for the wiki app.
Exports all views for easy importing.

Note: Most views are still in the original views.py file.
They are re-exported here to maintain backward compatibility.
"""
# Import from organized view files
from .page import PageViewSet
from .remote import RemotePostReceiver
from .wiki import user_wiki, user_wiki_api

# Import remaining views from the original views file (renamed to _views_legacy.py)
# This avoids circular import issues since the file is no longer named views.py
import importlib.util
import sys
from pathlib import Path

# Get path to legacy views file
_views_file = Path(__file__).parent.parent / '_views_legacy.py'

# Ensure wiki.models and wiki.serializers are in sys.modules before loading legacy views
# This is required for relative imports (from .models import) to work
try:
    importlib.import_module('wiki.models')
except ImportError:
    pass

try:
    importlib.import_module('wiki.serializers')
except ImportError:
    pass

# Load it as a module within the wiki package
spec = importlib.util.spec_from_file_location("wiki._views_legacy", str(_views_file))
_legacy_views = importlib.util.module_from_spec(spec)

# Set up the module's package context so relative imports work
_legacy_views.__package__ = 'wiki'
_legacy_views.__name__ = 'wiki._views_legacy'
_legacy_views.__file__ = str(_views_file)

# Add to sys.modules before execution so relative imports can resolve
sys.modules['wiki._views_legacy'] = _legacy_views

# Now execute the module - this will trigger the imports
# The relative imports should work because __package__ is set to 'wiki'
# and wiki.models/wiki.serializers are already in sys.modules
spec.loader.exec_module(_legacy_views)

# Re-export all needed views
MyLoginView = _legacy_views.MyLoginView
register = _legacy_views.register
register_api = _legacy_views.register_api
login_api = _legacy_views.login_api
get_authors = _legacy_views.get_authors
get_or_edit_author_api = _legacy_views.get_or_edit_author_api
get_author_fqid = _legacy_views.get_author_fqid
get_profile_fqid = _legacy_views.get_profile_fqid
view_local_authors = _legacy_views.view_local_authors
view_external_profile = _legacy_views.view_external_profile
get_profile_api = _legacy_views.get_profile_api
profile_view = _legacy_views.profile_view
edit_profile = _legacy_views.edit_profile
validated_auth = _legacy_views.validated_auth
create_entry = _legacy_views.create_entry
entry_detail = _legacy_views.entry_detail
edit_entry = _legacy_views.edit_entry
delete_entry = _legacy_views.delete_entry
entry_detail_api = _legacy_views.entry_detail_api
entry_detail_fqid_api = _legacy_views.entry_detail_fqid_api
like_entry = _legacy_views.like_entry
like_entry_api = _legacy_views.like_entry_api
get_entry_likes_api = _legacy_views.get_entry_likes_api
get_entry_likes_by_fqid = _legacy_views.get_entry_likes_by_fqid
get_entry_image_api = _legacy_views.get_entry_image_api
get_author_image_api = _legacy_views.get_author_image_api
get_author_entries_api = _legacy_views.get_author_entries_api
view_entry_author = _legacy_views.view_entry_author
add_comment = _legacy_views.add_comment
like_comment = _legacy_views.like_comment
like_comment_api = _legacy_views.like_comment_api
get_entry_comments_api = _legacy_views.get_entry_comments_api
get_entry_comments_fqid_api = _legacy_views.get_entry_comments_fqid_api
get_comment_fqid_api = _legacy_views.get_comment_fqid_api
get_comment_fqid = _legacy_views.get_comment_fqid
get_single_comment_fqid = _legacy_views.get_single_comment_fqid
get_author_comment_by_serial = _legacy_views.get_author_comment_by_serial
get_comment_likes_api = _legacy_views.get_comment_likes_api
get_comment_likes_by_fqid = _legacy_views.get_comment_likes_by_fqid
get_author_comments_api = _legacy_views.get_author_comments_api
author_comments_fqid = _legacy_views.author_comments_fqid
follow_profile = _legacy_views.follow_profile
unfollow_profile = _legacy_views.unfollow_profile
cancel_follow_request = _legacy_views.cancel_follow_request
process_follow_request = _legacy_views.process_follow_request
check_follow_requests = _legacy_views.check_follow_requests
get_local_follow_requests = _legacy_views.get_local_follow_requests
add_local_follower = _legacy_views.add_local_follower
get_local_followers = _legacy_views.get_local_followers
get_local_friends = _legacy_views.get_local_friends
get_local_followings = _legacy_views.get_local_followings
friends_list = _legacy_views.friends_list
followers_list = _legacy_views.followers_list
following_list = _legacy_views.following_list
user_inbox_api = _legacy_views.user_inbox_api
foreign_followers_api = _legacy_views.foreign_followers_api
get_author_likes_api = _legacy_views.get_author_likes_api
get_single_like_api = _legacy_views.get_single_like_api
get_author_likes_by_fqid = _legacy_views.get_author_likes_by_fqid
get_single_like_by_fqid = _legacy_views.get_single_like_by_fqid
is_local_url = _legacy_views.is_local_url

__all__ = [
    # Page
    'PageViewSet',
    # Remote
    'RemotePostReceiver',
    # Wiki
    'user_wiki',
    'user_wiki_api',
    # Auth
    'MyLoginView',
    'register',
    'register_api',
    'login_api',
    # Author
    'get_authors',
    'get_or_edit_author_api',
    'get_author_fqid',
    'get_profile_fqid',
    'view_local_authors',
    'view_external_profile',
    'get_profile_api',
    'profile_view',
    'edit_profile',
    'validated_auth',
    # Entry
    'create_entry',
    'entry_detail',
    'edit_entry',
    'delete_entry',
    'entry_detail_api',
    'entry_detail_fqid_api',
    'like_entry',
    'like_entry_api',
    'get_entry_likes_api',
    'get_entry_likes_by_fqid',
    'get_entry_image_api',
    'get_author_image_api',
    'get_author_entries_api',
    'view_entry_author',
    # Comment
    'add_comment',
    'like_comment',
    'like_comment_api',
    'get_entry_comments_api',
    'get_entry_comments_fqid_api',
    'get_comment_fqid_api',
    'get_comment_fqid',
    'get_single_comment_fqid',
    'get_author_comment_by_serial',
    'get_comment_likes_api',
    'get_comment_likes_by_fqid',
    'get_author_comments_api',
    'author_comments_fqid',
    # Social
    'follow_profile',
    'unfollow_profile',
    'cancel_follow_request',
    'process_follow_request',
    'check_follow_requests',
    'get_local_follow_requests',
    'add_local_follower',
    'get_local_followers',
    'get_local_friends',
    'get_local_followings',
    'friends_list',
    'followers_list',
    'following_list',
    # Inbox
    'user_inbox_api',
    # Remote views
    'foreign_followers_api',
    'get_author_likes_api',
    'get_single_like_api',
    'get_author_likes_by_fqid',
    'get_single_like_by_fqid',
    'is_local_url',
]

