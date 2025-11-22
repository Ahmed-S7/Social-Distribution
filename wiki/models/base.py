"""
Base models and utilities for the wiki app.
Contains BaseModel, managers, and enums used across models.
"""
from django.db import models
from django.db.models import Manager, QuerySet
import pytz
from datetime import datetime


# derived from: Django Software Foundation. (2025). Time zones. Django documentation (Version 5.2). Retrieved from https://docs.djangoproject.com/en/5.2/topics/i18n/timezones/
def get_mst_time():
    edmonton_timezone = pytz.timezone("America/Edmonton")
    naive_now = datetime.now()
    aware_now = edmonton_timezone.localize(naive_now)
    return aware_now


#The following soft-deletion logic (AppQuerySet, AppManager and BaseModel) was derived from Medium's article: https://medium.com/@tomisinabiodun/implementing-soft-delete-in-django-an-intuitive-guide-5c0f95da7f0d, June 15, 2025
class AppQuerySet(QuerySet):
    '''App Query Set that inherits from Django's defalt app query set
    - enables queries to update to is_deleted instead of hard deletion in the database'''
    def delete(self):
        self.update(is_deleted=True)


class AppManager(Manager):
    '''A manager that exterds from the default django app manager
        - this manager enables queries to ignore soft-deleted data
        
        '''
    def get_queryset(self):
        return AppQuerySet(self.model, using=self._db).exclude(is_deleted=True)


class BaseModel(models.Model):
    '''
       A model that extends from the Django base model
     - this model is capable of soft deletion so that deleted entities are still visible in the database  to administors
     - this way, all deleted data is visible in admin dashboards until permenantly deleted by an administrator
    '''
    class Meta:
        abstract = True

    is_deleted = models.BooleanField(default=False)
    
    def delete(self):
        self.is_deleted = True
        self.save()


class VisibilityOptions(models.TextChoices):
    '''Visibility Options For Entries Made In The Application'''
    PUBLIC = "public", "Public"
    UNLISTED = "unlisted", "Unlisted"
    FRIENDS_ONLY = "", "Friends_only"
    DELETED = "deleted", "Deleted"


class RequestState(models.TextChoices):
    """
    stores the possible follow request states 
    """
    REQUESTING = "requesting", "Requesting"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"


class InboxObjectType(models.TextChoices):
    '''stores all of the possible inbox item types'''
    
    FOLLOW = "Follow", "follow"
    LIKE = "like", "Like"
    COMMENT = "comment", "Comment"
    ENTRY = "entry", "Entry" 
    AUTHOR = "author", "Author"

