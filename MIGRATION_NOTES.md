# Code Organization Migration Notes

## Completed

### Models Organization ✅
- Created `wiki/models/` directory structure
- Split `models.py` into:
  - `base.py` - BaseModel, AppManager, AppQuerySet, enums
  - `author.py` - Author model and signals
  - `entry.py` - Entry and Like models
  - `comment.py` - Comment and CommentLike models
  - `social.py` - AuthorFollowing, AuthorFriend, FollowRequest
  - `inbox.py` - InboxItem model
  - `other.py` - Page, RemotePost, RemoteNode, NodeConnectionCredentials
- Updated `models/__init__.py` to export all models
- Updated `admin.py` to use new model imports

### Serializers Organization ✅
- Created `wiki/serializers/` directory structure
- Split `serializers.py` into:
  - `author.py` - AuthorSerializer, AuthorSummarySerializer
  - `entry.py` - EntrySerializer, LikeSerializer, LikeSummarySerializer
  - `comment.py` - CommentSummarySerializer, CommentLikeSummarySerializer
  - `social.py` - FollowRequestSerializer, AuthorFriendSerializer, etc.
  - `inbox.py` - InboxItemSerializer
  - `page.py` - PageSerializer
  - `remote.py` - RemotePostSerializer
- Updated `serializers/__init__.py` to export all serializers
- Fixed circular import issues

### Views Organization (In Progress)
- Created `wiki/views/` directory structure
- Created `views/__init__.py` with all exports
- Created initial view files:
  - `page.py` - PageViewSet
  - `remote.py` - RemotePostReceiver
  - `wiki.py` - user_wiki, user_wiki_api
- Updated `views.py` imports to use new model/serializer structure

## Remaining Work

### Views Organization
The original `views.py` file is 4277 lines with 65+ functions. To complete the organization:

1. **Create remaining view files:**
   - `auth.py` - MyLoginView, register, register_api, login_api
   - `author.py` - All author-related views (get_authors, get_or_edit_author_api, profile views, etc.)
   - `entry.py` - All entry-related views (create_entry, entry_detail, like_entry, etc.)
   - `comment.py` - All comment-related views (add_comment, like_comment, etc.)
   - `social.py` - All follow/friend-related views
   - `inbox.py` - user_inbox_api
   - `remote_views.py` - Remote node communication views

2. **Update `urls.py`:**
   - Change imports from `from .views import ...` to `from .views import ...` (using the new structure)
   - All imports should work through `views/__init__.py`

3. **Test:**
   - Run the application
   - Test all endpoints
   - Fix any import errors

## Import Patterns

### Models
```python
from ..models import Author, Entry, Comment
# or
from wiki.models import Author, Entry, Comment
```

### Serializers
```python
from ..serializers import AuthorSerializer, EntrySerializer
# or
from wiki.serializers import AuthorSerializer, EntrySerializer
```

### Views (once complete)
```python
from ..views import get_authors, create_entry
# or
from wiki.views import get_authors, create_entry
```

## Notes

- All models and serializers are fully organized and working
- Views structure is created but needs functions migrated from `views.py`
- The original `views.py` still works with updated imports
- Once views are migrated, `views.py` can be removed

