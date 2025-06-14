from django.contrib import admin
from .models import Page, Like, RemotePost, Author

# Register your models here.

admin.site.register(Page)
admin.site.register(Like)
admin.site.register(RemotePost)
admin.site.register(Author)
