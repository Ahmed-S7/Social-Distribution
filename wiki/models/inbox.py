"""
InboxItem model for receiving remote activities.
"""
from django.db import models
from .base import BaseModel, AppManager, InboxObjectType, get_mst_time
from .author import Author


class InboxItem(BaseModel):
    objects = AppManager()
    all_objects = models.Manager()
    '''
    A general model for all of the different objects that can be pushed to the inbox 
    
    FIELDS:
    
    author: the author recieving the inbox item
    
    type: the type of inbox item
    
    content: the JSON in the inbox item
    
    created_at: the time that the inbox item was posted

    use: author.inboxItems to retrieve all of an authors inbox items, this is effectively their inbox
    '''
    
    author = models.ForeignKey(Author, related_name="inboxItems", on_delete=models.CASCADE)
    type = models.CharField(
        max_length = 20,
        choices=InboxObjectType.choices,
        null=False
    )
    body = models.JSONField()
    created_at =models.DateTimeField(default=get_mst_time)
    
    def get_follow_requester_name(self):
        try:
            return self.get_content().get("actor")["displayName"]
        except Exception as e:
            raise e
        
    def get_follow_request_state(self):
        try:
            return self.get_content().get("state")
        except Exception as e:
            raise e
      
    
    def get_content(self):
        return self.body 
    
    def __str__(self):
        return f"{self.author} received Inbox Item object of type {self.type}"

