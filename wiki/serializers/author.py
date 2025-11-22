"""
Author serializers.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import Author


class AuthorSerializer(serializers.ModelSerializer):
    
    class Meta:
        model= Author
        fields = ["type", "id", "host", "displayName", "github", "profileImage", "web","description","followers_count", "friends_count", "followings_count", "entries_count"]# "followers", "friends", "followings"]
    followers_count  = serializers.SerializerMethodField()
    friends_count = serializers.SerializerMethodField()
    followings_count = serializers.SerializerMethodField()
    entries_count = serializers.SerializerMethodField()
    '''
    NOT PART OF API FOR NOW (working but unpaginated, can be re-integrated)
    
    followers =  serializers.SerializerMethodField()
    friends = serializers.SerializerMethodField()
    followings = serializers.SerializerMethodField()
    '''
    def validate_displayName(self, value):
        # Hardcoded check: prevent username "admin" (case-insensitive)
        if value and value.lower() == "admin":
            raise serializers.ValidationError("This username is invalid and cannot be used.")
        # Enforce no spaces in username
        if  " " in value:
            raise serializers.ValidationError("Display name cannot contain any spaces.")
        if len(value) >= 150:
            raise serializers.ValidationError("Display name cannot be longer than 150 characters")
        return value
    
    def validate_github(self, value):
        """Validate GitHub URL format and account existence"""
        from ..util import validate_github_url
        
        is_valid, error_message = validate_github_url(value)
        if not is_valid:
            raise serializers.ValidationError(error_message)
        return value
    
    def update(self, instance, validated_data):
        """
        Update and return an existing `Author` instance, given the validated data
        """
        # Temporarily disable the post_save signal to avoid conflicts
        from django.db.models.signals import post_save
        from ..models.author import update_user_username
        
        # Disconnect the signal temporarily
        post_save.disconnect(update_user_username, sender=instance.__class__)
        
        try:
            # Update displayName if provided
            if 'displayName' in validated_data:
                instance.displayName = validated_data['displayName']
                # Update user.username to match
                instance.user.username = validated_data['displayName']
                # Save user first
                instance.user.save(update_fields=['username'])

            if 'github' in validated_data:
                instance.github = validated_data['github']
            
            if 'description' in validated_data:
                instance.description = validated_data['description']
        
            if 'profileImage' in validated_data:
                instance.profileImage = validated_data['profileImage']
            
            # Save the instance after all updates
            instance.save()
        finally:
            # Reconnect the signal
            post_save.connect(update_user_username, sender=instance.__class__)
        
        return instance
    def get_followers_count(self, obj):
        return len(obj.get_followers())
    
    def get_friends_count(self, obj):
        return len(obj.get_friends())
    
    def get_followings_count(self, obj):
        return len(obj.get_followings())
    
    def get_entries_count(self,obj):
        return len(obj.posts.all())
    
    '''
    #POSSIBLE FIELDS FOR PROFILE API (WORKING BUT UNPAGINATED):
    
    def get_followers(self, obj):
        followers_list = obj.get_followings()
        followers = []
        followers_list = obj.get_friends()
        for follower in followers_list:
            followers.append({"type":"author",
                            "id":follower.id,
                            "host":follower.host,
                            "displayName":follower.displayName,
                            "github":follower.github,
                            "profileImage":follower.profileImage,
                            "web":follower.web,
                            "description":follower.description,
                            "followers_count":len(follower.get_followers()),
                            "friends_count":len(follower.get_friends()),
                            "followings_count":len(follower.get_followings()),
       
            })
        return followers
    
    def get_friends(self, obj):
        friends = []
        friends_list = obj.get_friends()
        for friend in friends_list:
            friends.append({"type":"author",
                            "id":friend.id,
                            "host":friend.host,
                            "displayName":friend.displayName,
                            "github":friend.github,
                            "profileImage":friend.profileImage,
                            "web":friend.web,
                            "description":friend.description,
                            "followers_count":len(friend.get_followers()),
                            "friends_count":len(friend.get_friends()),
                            "followings_count":len(friend.get_followings()),
            })
        return friends
 
    def get_followings(self, obj):
        followings = []
        followings_list = obj.get_friends()
        for following in followings_list:
            followings.append({"type":"author",
                            "id":following.id,
                            "host":following.host,
                            "displayName":following.displayName,
                            "github":following.github,
                            "profileImage":following.profileImage,
                            "web":following.web,
                            "description":following.description,
                            "followers_count":len(following.get_followers()),
                            "friends_count":len(following.get_friends()),
                            "followings_count":len(following.get_followings()),
                            
            })
        return followings
    '''
    def create(self, validated_data):
        displayName = validated_data.get("id")
        user = User.objects.create(username=displayName, password="uniquepass")

        # Now create the Author and link the new user
        author = Author.objects.create(user=user, **validated_data)
        return author


class AuthorSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = [
            'type', 'id', 'host', 'displayName', 'web', 'github', 'profileImage'
        ]
    type = serializers.SerializerMethodField()
    id = serializers.CharField()
    host = serializers.CharField()
    displayName = serializers.CharField()
    web = serializers.CharField()
    github = serializers.SerializerMethodField()
    profileImage = serializers.SerializerMethodField()

    def get_type(self, obj):
        return 'author'
    def get_profileImage(self, obj):
        # If profileImage is an ImageField, return its URL
        if obj.profileImage:
            return obj.profileImage.url if hasattr(obj.profileImage, 'url') else obj.profileImage
        return None
    def get_github(self,obj):
        return obj.github or None

