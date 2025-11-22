"""
Wiki/feed views for user activity streams.
"""
from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
import markdown
from ..models import Author, AuthorFollowing, AuthorFriend, Entry
from ..gethub import create_entries


@api_view(['GET'])
def user_wiki_api(request, username):
    current_author = get_object_or_404(Author, user=request.user)
    if request.user.username != username:
        return redirect("wiki:login")
    
    # Followed
    followed_ids = AuthorFollowing.objects.filter(
        follower=current_author
    ).values_list('following', flat=True)

    # Friends
    friend_pairs = AuthorFriend.objects.filter(
        Q(friending=current_author) | Q(friended=current_author)
    ).values_list('friending', 'friended')

    friend_ids = set()
    for friending_id, friended_id in friend_pairs:
        if friending_id != current_author.id:
            friend_ids.add(friending_id)
        if friended_id != current_author.id:
            friend_ids.add(friended_id)

    entries = Entry.objects.filter(
        ~Q(visibility='DELETED') & (
            Q(visibility='PUBLIC') |
            Q(author=current_author) |
            Q(visibility='FRIENDS', author__id__in=friend_ids) |
            Q(visibility='UNLISTED', author__id__in=followed_ids)
        )
    ).order_by('-created_at')
    serialized_entries = []
    for entry in entries:
        entry_data = {
            "title": entry.title,
            "content": entry.content,
            "author": entry.author.displayName,
            "visibility": entry.visibility,
            "created_at": entry.created_at.isoformat(),
            "serial": str(entry.serial),
            "contentType": entry.contentType,
        }
        serialized_entries.append(entry_data)

    return Response(serialized_entries)
    
@login_required
def user_wiki(request, username):
    '''Process all of the logic pertaining to a given user's wiki page'''
    print(f"CURRENT USER IN REQUEST: {request.user.username}")
    if request.user.username != username:
        raise PermissionDenied("You are not allowed to view this page.")
    current_author = get_object_or_404(Author, user=request.user)

    #Add Github Entries to feed
    create_entries(current_author)

    # Followed
    followed_ids = AuthorFollowing.objects.filter(
        follower=current_author
    ).values_list('following', flat=True)

    # Friends
    friend_pairs = AuthorFriend.objects.filter(
        Q(friending=current_author) | Q(friended=current_author)
    ).values_list('friending', 'friended')

    friend_ids = set()
    for friending_id, friended_id in friend_pairs:
        if friending_id != current_author.id:
            friend_ids.add(friending_id)
        if friended_id != current_author.id:
            friend_ids.add(friended_id)

    entries_queryset = Entry.objects.filter(
        ~Q(visibility='DELETED') & (
            Q(visibility='PUBLIC') |
            Q(author=current_author) |
            Q(visibility='FRIENDS', author__id__in=friend_ids) |
            Q(visibility='UNLISTED', author__id__in=followed_ids)
        )
    ).order_by('-created_at')
    
    # Paginate entries
    page_number = request.GET.get('page', 1)
    page_size = 10
    paginator = Paginator(entries_queryset, page_size)
    
    try:
        page_obj = paginator.page(page_number)
    except (ValueError, TypeError):
        page_obj = paginator.page(1)
    except:
        page_obj = paginator.page(paginator.num_pages) if paginator.num_pages > 0 else paginator.page(1)
    
    # Render markdown for entries on current page
    rendered_entries = []
    for entry in page_obj:
        rendered = (
            mark_safe(markdown.markdown(entry.content))
            if entry.contentType == "text/markdown"
            else entry.content
        )
        rendered_entries.append((entry, rendered))

    return render(request, 'wiki.html', {
        'entries': rendered_entries,
        'page_obj': page_obj,
        'paginator': paginator,
        'current_author': current_author,
        'current_author_serial': str(current_author.serial)
    })

