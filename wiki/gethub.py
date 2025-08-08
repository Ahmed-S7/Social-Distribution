import requests
from .models import Entry, Author
def create_entries(author: Author):
    if author.github is None or author.github == '':
        return
    github_url = author.github
    #Parse url to get username
    if github_url[-1] == '/':
        github_url = github_url[:-1]
    username = github_url[github_url.rfind('/')+1:]
    api_url = "https://api.github.com/users/"+ username + "/events/public"
    response = requests.get(api_url)
    if response.status_code != 200:
        return
    events = response.json()

    for event in reversed(events):
        event_id = event.get('id')
        if not Entry.all_objects.filter(title__icontains=event_id).exists():
            event_type = event.get('type')
            created_at = event.get('created_at')
            
            
            if event_type == 'PushEvent':
                actor_display_login = event.get('actor').get('display_login')
                repo_name = event.get('repo').get('name')
                Entry.objects.create(
                    author=author,
                    title="Github Event: " + event_type + ": " + event_id,
                    content=actor_display_login + " pushed to " + repo_name + "!",
                    contentType='text/plain',
                    description="A GitHub Description",
                    visibility='PUBLIC',
                )
            elif event_type == 'PullRequestEvent':
                actor_display_login = event.get('actor').get('display_login')
                payload_action = event.get('payload').get('action')
                pull_request_title = event.get('payload').get('pull_request').get('title')
                pull_request_html_url = event.get('payload').get('pull_request').get('html_url')
                repo_name = event.get('repo').get('name')
                Entry.objects.create(
                    author=author,
                    title="Github Event: " + event_type + ": " + event_id,
                    content = actor_display_login + " " + payload_action + " pull request: " + pull_request_title + " in " + repo_name + ". You can see it here: " + pull_request_html_url,
                    contentType='text/plain',
                    description="A GitHub Description",
                    visibility='PUBLIC',
                )
            elif event_type == 'CreateEvent':
                actor_display_login = event.get('actor').get('display_login')
                payload_ref_type = event.get('payload').get('ref_type')
                repo_name = event.get('repo').get('name')
                Entry.objects.create(
                    author=author,
                    title="Github Event: " + event_type + ": " + event_id,
                    content=actor_display_login + " created a " + payload_ref_type + " at: "  + repo_name,
                    contentType='text/plain',
                    description="A GitHub Description",
                    visibility='PUBLIC',
                )
            else: 
                Entry.objects.create(
                    author = author,
                    title= "Github Event: " + event_type + ": " + event_id,
                    content= "A Github Event",
                    contentType='text/plain',
                    description= "A GitHub Description",
                    visibility= 'PUBLIC',
                )


