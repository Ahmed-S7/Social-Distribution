"""
Serializers package for the wiki app.
Exports all serializers for easy importing.
"""
from .author import AuthorSerializer, AuthorSummarySerializer
from .entry import EntrySerializer, LikeSerializer, LikeSummarySerializer
from .comment import CommentSummarySerializer, CommentLikeSummarySerializer
from .social import (
    FollowRequestSerializer,
    FollowRequestReadingSerializer,
    AuthorFriendSerializer,
    AuthorFollowingSerializer,
)
from .inbox import InboxItemSerializer
from .page import PageSerializer
from .remote import RemotePostSerializer

__all__ = [
    # Author
    'AuthorSerializer',
    'AuthorSummarySerializer',
    # Entry
    'EntrySerializer',
    'LikeSerializer',
    'LikeSummarySerializer',
    # Comment
    'CommentSummarySerializer',
    'CommentLikeSummarySerializer',
    # Social
    'FollowRequestSerializer',
    'FollowRequestReadingSerializer',
    'AuthorFriendSerializer',
    'AuthorFollowingSerializer',
    # Inbox
    'InboxItemSerializer',
    # Page
    'PageSerializer',
    # Remote
    'RemotePostSerializer',
]

