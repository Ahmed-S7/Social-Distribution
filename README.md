[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/BGMWEn7l)
CMPUT404-project-socialdistribution
===================================

CMPUT404-project-socialdistribution

See [the web page](https://uofa-cmput404.github.io/general/project.html) for a description of the project.

Make a distributed social network!

## License

See the [LICENSE](LICENSE.md) file for license rights and limitations (MIT).

## Copyright


## My Role in CMPUT404 Social Distribution Project

As part of a collaborative team, I contributed to the development of a distributed social network. My main contributions were:
- Acting as the lead developer and group coordinator, organizing majority of group meetings
- Coordinating with other teams during the federation process to ensure API adaptability
- Designing and implementing the backend API endpoints using Django REST Framework
- Designing and implementing application features and organizing the project board 
- Integrating federated node communication for cross-server post sharing
- Handling authentication and user permissions
- Writing documentation and maintaining code quality standards
- implementing and testing application features


The authors claiming copyright, if they wish to be known, can list their names here...

* Ahmed Shittu
* Nina Han
* Luis Martinez
* Abdullah Faisal
* Maro Erivona

Note: One contributor has withdrawn from the course and has been removed as a contributor with their written consent. Their code remains cited where used.

This project was completed as part of CMPUT404 at the University of Alberta. You can find the full API documentation below.

#DOCUMENTATION: 
NOTE, as of now endpoints are setup for future pagination compatibility, but currently display a list of limited size per requests
## Authentication API
### `POST /api/login/`

Log in to the website, it returns success if the credentials are correct and the account has been approved by an admin.
```
HTTP 200 OK
Allow: POST, OPTIONS
Content-Type: application/json
Vary: Accept
```
```json
{
    "detail": "Login successful"
}
```
```
Returns 400 Bad Request if the username is already taken or the username/password is not valid.
```
### `POST /api/register/`

Sign up for the website, it returns HTTP 201 (created) if the username and password are valid and awaiting confirmation from an admininstrator.
```
HTTP 201 Created
Allow: OPTIONS, POST
Content-Type: application/json
Vary: Accept
```
```json
{
    "detail": "Registration successful, pending admin approval"
}
```
```
Returns 400 Bad Request if invalid credentials are posted to the endpoint, 500 Internal Server Error upon internal failures during registration.
```
## Authors API
### `GET /api/authors/`

Gets the list of all authors on the application
```
HTTP 200 OK
Allow: GET, OPTIONS
Content-Type: application/json
Vary: Accept
```
```json
{
    "page_number": 1,
    "size": 50,
    "count": 2,
    "type": "authors",
    "authors": [
        {
            "type": "author",
            "id": "http://127.0.0.1:8000/api/authors/57006192-4dbb-4424-a28e-e97a11f6efd4",
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "AnotherNewAuthor",
            "github": "",
            "profileImage": "",
            "web": "http://127.0.0.1:8000/authors/57006192-4dbb-4424-a28e-e97a11f6efd4",
            "description": "",
            "followers_count": 0,
            "friends_count": 0,
            "followings_count": 1,
            "entries_count": 0
        },
        {
            "type": "author",
            "id": "http://127.0.0.1:8000/api/authors/d2d5d357-fb3e-4120-a635-fe0203815f59",
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "newestguy",
            "github": "",
            "profileImage": "https://4vector.com/i/free-vector-default-profile-picture_099397_Default_Profile_Picture.png",
            "web": "http://127.0.0.1:8000/authors/d2d5d357-fb3e-4120-a635-fe0203815f59",
            "description": "",
            "followers_count": 1,
            "friends_count": 0,
            "followings_count": 0,
            "entries_count": 2
        }
    ]
}

```
## Single Authors API
### `GET /api/authors/{author_serial}/`
Get a specific author in the application
```
HTTP 200 OK
Allow: GET, OPTIONS
Content-Type: application/json
Vary: Accept
```
```json
 {
            "type": "author",
            "id": "http://127.0.0.1:8000/api/authors/57006192-4dbb-4424-a28e-e97a11f6efd4",
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "AnotherNewAuthor",
            "github": "",
            "profileImage": "",
            "web": "http://127.0.0.1:8000/authors/57006192-4dbb-4424-a28e-e97a11f6efd4",
            "description": "",
            "followers_count": 0,
            "friends_count": 0,
            "followings_count": 1,
            "entries_count": 0
        }
```
### `PUT /api/authors/`
Updates a specific author in the application
```
upon successful updates:
```
```
HTTP 200 OK
Allow: PUT, GET, OPTIONS
Content-Type: application/json
Vary: Accept
```
```json
{
            "type": "author",
            "id": "http://127.0.0.1:8000/api/authors/d2d5d357-fb3e-4120-a635-fe0203815f59",
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "newestguy",
            "github": "",
            "profileImage": "https://4vector.com/i/free-vector-default-profile-picture_099397_Default_Profile_Picture.png",
            "web": "http://127.0.0.1:8000/authors/d2d5d357-fb3e-4120-a635-fe0203815f59",
            "description": "",
            "followers_count": 1,
            "friends_count": 0,
            "followings_count": 0,
            "entries_count": 2
        }
```
Upon invalid updated information:
```
HTTP 400 Bad Request
Allow: PUT, GET, OPTIONS
Content-Type: application/json
Vary: Accept
```
```json
{
    "displayName": [
        "Display name cannot contain any spaces."
    ],
    "profileImage": [
        "The submitted data was not a file. Check the encoding type on the form."
    ]
}
```
## Author Followers API
### `GET /api/authors/{author_serial}/followers/`
Get a specific author's followers in the application
```
HTTP 200 OK
Allow: OPTIONS, GET
Content-Type: application/json
Vary: Accept
```
```json
{
    "type": "followers",
    "followers": [
        {
            "type": "author",
            "id": "http://127.0.0.1:8000/api/authors/d2d5d357-fb3e-4120-a635-fe0203815f59",
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "newestguy",
            "github": "",
            "profileImage": "https://4vector.com/i/free-vector-default-profile-picture_099397_Default_Profile_Picture.png",
            "web": "http://127.0.0.1:8000/authors/d2d5d357-fb3e-4120-a635-fe0203815f59",
            "description": "",
            "followers_count": 1,
            "friends_count": 0,
            "followings_count": 0,
            "entries_count": 2
        },
        {
            "type": "author",
            "id": "http://127.0.0.1:8000/api/authors/57006192-4dbb-4424-a28e-e97a11f6efd4",
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "AnotherNewAuthor",
            "github": "",
            "profileImage": "",
            "web": "http://127.0.0.1:8000/authors/57006192-4dbb-4424-a28e-e97a11f6efd4",
            "description": "",
            "followers_count": 0,
            "friends_count": 0,
            "followings_count": 1,
            "entries_count": 0
        },
   ]
}
```
```
for a non-existent author:
```
```
HTTP 404 Not Found
Allow: GET, OPTIONS
Content-Type: application/json
Vary: Accept
```
```json
{
    "Error": "We were unable to locate this account: ['“false-id” is not a valid UUID.']"
}
```
```
for a server error in follower retrieval:
```
```
HTTP 500 Internal Server Error
Allow: GET, OPTIONS
Content-Type: application/json
Vary: Accept
```
```json
{
    "Error": "We were unable to get the followers for this account: {exception message here}"
}
```
## Author Follow Requests API
### `GET /api/authors/{author_serial}/follow_requests/`
Get a specific author's follower Requests in the application, only for local authenticated users
```
for a successful GET request:
```
```
HTTP 200 OK
Allow: OPTIONS, POST, GET
Content-Type: application/json
Vary: Accept
```
```json
[
    {
        "type": "follow",
        "state": "requesting",
        "summary": "fan1 has requested to follow ThatGuy",
        "actor": {
            "type": "author",
            "id": "http://127.0.0.1:8000/s25-project-white/api/authors/e025f287-059d-47ae-8201-e6be03082102",
            "host": "http://s25-project-white/api/",
            "displayName": "fan1",
            "github": "",
            "profileImage": "/media/profile_images/90s_background.jpg",
            "web": "http://127.0.0.1:8000/s25-project-white/authors/e025f287-059d-47ae-8201-e6be03082102",
            "description": ""
        },
        "object": {
            "type": "author",
            "id": "http://127.0.0.1:8000/s25-project-white/api/authors/201fc5b1-38f8-451d-8807-fbe326fd0f5e",
            "host": "http://s25-project-white/api/",
            "displayName": "ThatGuy",
            "github": "",
            "profileImage": "/media/profile_images/Thorfinn__Askeladd.jpg",
            "web": "http://127.0.0.1:8000/s25-project-white/authors/201fc5b1-38f8-451d-8807-fbe326fd0f5e",
            "description": "",
            "followers_count": 0,
            "friends_count": 0,
            "followings_count": 1,
            "entries_count": 0
        }
    },
    {
        "type": "follow",
        "state": "accepted",
        "summary": "anotheruser has requested to follow ThatGuy",
        "actor": {
            "type": "author",
            "id": "http://127.0.0.1:8000/s25-project-white/api/authors/99f75995-a05e-497f-afd4-5af96cf3b0b4",
            "host": "http://s25-project-white/api/",
            "displayName": "anotheruser",
            "github": "",
            "profileImage": "/media/profile_images/gutspfp.jpg",
            "web": "http://127.0.0.1:8000/s25-project-white/authors/99f75995-a05e-497f-afd4-5af96cf3b0b4",
            "description": "",
            "followers_count": 0,
            "friends_count": 0,
            "followings_count": 1,
            "entries_count": 0
        },
        "object": {
            "type": "author",
            "id": "http://127.0.0.1:8000/s25-project-white/api/authors/201fc5b1-38f8-451d-8807-fbe326fd0f5e",
            "host": "http://s25-project-white/api/",
            "displayName": "ThatGuy",
            "github": "",
            "profileImage": "/media/profile_images/Thorfinn__Askeladd.jpg",
            "web": "http://127.0.0.1:8000/s25-project-white/authors/201fc5b1-38f8-451d-8807-fbe326fd0f5e",
            "description": "",
            "followers_count": 0,
            "friends_count": 0,
            "followings_count": 1,
            "entries_count": 0
        }
    }
 
]
```
for an unauthorized user with an account found on the node:
```
HTTP 401 Unauthorized
Allow: OPTIONS, POST, GET
Content-Type: application/json
Vary: Accept
```
```json
{
    "error": "user requesting information is not currently logged in, you do not have access to this information"
}
```
```
any requests made from non-users in the application or unauthenticated requests (no login information in the request) will be redirected to the login page
```
## Entry Details API
### `GET /api/authors/{author_serial}/entries/{entry_serial}`
Get a specific entry's information within the application, only for user's with valid visibility

```
If the entry is Friends only, the author making the request must be friends with the entry's author to view it
If the entry is Unlisted, the author making the request must be following the entry's author to view it
If the entry is Public, any *authenticated* author may view it

failures for any of these will yield a 401 unauthorized response (shown below)
```
```
for a successful GET request:
```
```
HTTP 200 OK
Allow: OPTIONS, POST, GET
Content-Type: application/json
Vary: Accept
```
```json
{
    "type": "entry",
    "title": "sdfsfadsa",
    "id": "http://s25-project-white/authors/99f75995-a05e-497f-afd4-5af96cf3b0b4/entries/d783d821-85de-420e-91a9-cd68aa9c1d8e",
    "web": "http://127.0.0.1:8000/s25-project-white/authors/99f75995-a05e-497f-afd4-5af96cf3b0b4",
    "description": "entry by GUTS, titled: 'sdfsfadsa",
    "contentType": "text/plain",
    "content": "asfdasfasd",
    "author": {
        "type": "author",
        "id": "http://127.0.0.1:8000/s25-project-white/api/authors/99f75995-a05e-497f-afd4-5af96cf3b0b4",
        "host": "http://s25-project-white/api/",
        "displayName": "GUTS",
        "web": "http://127.0.0.1:8000/s25-project-white/authors/99f75995-a05e-497f-afd4-5af96cf3b0b4",
        "github": null,
        "profileImage": "/media/profile_images/gutspfp.jpg"
        "description": "",
        "followers_count": 0,
        "friends_count": 0,
        "followings_count": 1,
        "entries_count": 0
    },
    "comments": {
        "type": "comments",
        "web": "http://s25-project-white/authors/99f75995-a05e-497f-afd4-5af96cf3b0b4/entries/d783d821-85de-420e-91a9-cd68aa9c1d8e",
        "id": "http://s25-project-white/authors/99f75995-a05e-497f-afd4-5af96cf3b0b4/entries/d783d821-85de-420e-91a9-cd68aa9c1d8e/comments",
        "page_number": 1,
        "size": 5,
        "count": 0,
        "src": []
    },
    "likes": {
        "type": "likes",
        "web": "http://s25-project-white/authors/99f75995-a05e-497f-afd4-5af96cf3b0b4/entries/d783d821-85de-420e-91a9-cd68aa9c1d8e",
        "id": "http://s25-project-white/authors/99f75995-a05e-497f-afd4-5af96cf3b0b4/entries/d783d821-85de-420e-91a9-cd68aa9c1d8e/likes",
        "page_number": 1,
        "size": 50,
        "count": 1,
        "src": [
            {
                "type": "like",
                "author": {
                    "type": "author",
                    "id": "http://127.0.0.1:8000/s25-project-white/api/authors/f17f2494-9e8d-4f75-889a-5a0e0c145978",
                    "host": "http://s25-project-white/api/",
                    "displayName": "AtestRegisteringUser",
                    "web": "http://127.0.0.1:8000/s25-project-white/authors/f17f2494-9e8d-4f75-889a-5a0e0c145978",
                    "github": null,
                    "profileImage": "/media/profile_images/spideysenses.gif",
                    "description": "",
                    "followers_count": 0,
                    "friends_count": 0,
                    "followings_count": 1,
                    "entries_count": 0
                },
                "published": "2025-07-10T10:11:52+00:00",
                "id": "http://localhost/api/authors/f17f2494-9e8d-4f75-889a-5a0e0c145978/liked/40",
                "object": "http://localhost/api/authors/99f75995-a05e-497f-afd4-5af96cf3b0b4/entries/d783d821-85de-420e-91a9-cd68aa9c1d8e"
            }
        ]
    },
    "published": "2025-07-10T02:19:38.998089-06:00",
    "visibility": "PUBLIC"
}
```
for an unauthorized user with an account found on the node (2 different scenarios):
```
HTTP 401 Unauthorized
Allow: OPTIONS, POST, GET
Content-Type: application/json
Vary: Accept
```
Not friends requesting a friends only entry:
```json
{
    "error": "You are not friends with this author, you cannot view this entry"
}
```
Not following and requesting an unlisted entry:
```json
{
     "error": "You are not following this author, you cannot view this entry"
}
```
```
any requests made from non-users in the application or unauthenticated requests (no login information in the request) will be redirected to the login page
```
## Like Local Entry API
### `POST /api/entry/{entry_serial}/like/`
Like an entry with a specific entry serial on the local node
```
for a successful like on an entry:
```
HTTP 200 OK
Allow: OPTIONS, POST
Content-Type: application/json
Vary: Accept
```json
        {
            "status": "liked",
            "message": "Entry liked successfully",
            "likes_count": 8
        }
```
for an attempted like on a previously like entry:
```
HTTP 400 Bad Request
Allow: POST, OPTIONS
Content-Type: application/json
Vary: Accept
```
```json
       {
          "status": "already_liked",
           "message": "You have already liked this entry",
          "likes_count": 2
      }
```
## Entry Likes API
### `GET /api/entries/{entry_serial}/likes/`
Get a specific entry's information within the application, only for user's with valid visibility

```
If the entry is Friends only, the author making the request must be friends with the entry's author to view it
If the entry is Unlisted, the author making the request must be following the entry's author to view it
If the entry is Public, any *authenticated* author may view it

failures for any of these will yield a 401 unauthorized response (shown below)
```
```
for a successful GET request:
```
```
HTTP 200 OK
Allow: OPTIONS, POST, GET
Content-Type: application/json
Vary: Accept
```
```json
{
 
    "type": "likes",
    "web": "http://s25-project-white/authors/201fc5b1-38f8-451d-8807-fbe326fd0f5e/entries/5a720bf2-3d55-4007-a5e7-3dcf9eabdc4b",
    "id": "http://s25-project-white/entry/5a720bf2-3d55-4007-a5e7-3dcf9eabdc4b/likes",
    "page_number": 1,
    "size": 50,
    "count": 4,
    "src": [
        {
            "type": "like",
            "author": {
                "type": "author",
                "id": "http://127.0.0.1:8000/s25-project-white/api/authors/f802fa6a-c7e5-40e5-907f-6ff25b63ff80",
                "host": "http://s25-project-white/api/",
                "displayName": "AB",
                "web": "http://127.0.0.1:8000/s25-project-white/authors/f802fa6a-c7e5-40e5-907f-6ff25b63ff80",
                "github": null,
                "profileImage": "/media/profile_images/90s_background_e8A8ndq.jpg",
                "description": "",
                "followers_count": 0,
                "friends_count": 0,
                "followings_count": 1,
                "entries_count": 0
            },
            "published": "2025-07-10T11:56:34+00:00",
            "id": "http://localhost/api/authors/f802fa6a-c7e5-40e5-907f-6ff25b63ff80/liked/43",
            "object": "http://localhost/api/authors/201fc5b1-38f8-451d-8807-fbe326fd0f5e/entries/5a720bf2-3d55-4007-a5e7-3dcf9eabdc4b"
        },
        {
            "type": "like",
            "author": {
                "type": "author",
                "id": "http://127.0.0.1:8000/s25-project-white/api/authors/e025f287-059d-47ae-8201-e6be03082102",
                "host": "http://s25-project-white/api/",
                "displayName": "author_2",
                "web": "http://127.0.0.1:8000/s25-project-white/authors/e025f287-059d-47ae-8201-e6be03082102",
                "github": null,
                "profileImage": "/media/profile_images/90s_background.jpg"
                "description": "",
                "followers_count": 0,
                "friends_count": 0,
                "followings_count": 1,
                "entries_count": 0
            },
            "published": "2025-07-10T05:15:36+00:00",
            "id": "http://localhost/api/authors/e025f287-059d-47ae-8201-e6be03082102/liked/33",
            "object": "http://localhost/api/authors/201fc5b1-38f8-451d-8807-fbe326fd0f5e/entries/5a720bf2-3d55-4007-a5e7-3dcf9eabdc4b"
        }
      ]
    }
```
for an unauthorized user with an account found on the node (2 different scenarios):
```
HTTP 401 Unauthorized
Allow: OPTIONS, POST, GET
Content-Type: application/json
Vary: Accept
```
Not friends requesting a friends only entry:
```json
{
    "error": "You are not friends with this author, you cannot view this entry"
}
```
Not following and requesting an unlisted entry:
```json
{
     "error": "You are not following this author, you cannot view this entry"
}
```
```
any requests made from non-users in the application or unauthenticated requests (no login information in the request) will be redirected to the login page
```
## Single like API

### `GET /api/authors/{AUTHOR_SERIAL}/liked/{LIKE_SERIAL}/`

Returns a **single like** object (either for a comment or an entry) for a given author.

```
HTTP 200 OK  
Allow: GET, OPTIONS  
Content-Type: application/json  
Vary: Accept
```

####  When to use
- To retrieve metadata about a specific like made by an author.
- To check if a like exists and on what object it was placed.

#### When *not* to use
- If you need a full list of likes → use `GET /api/authors/{AUTHOR_SERIAL}/liked/`
- Not used for creating or deleting likes.

#### How to use
Make a `GET` request to the following endpoint:

```
/api/authors/{AUTHOR_SERIAL}/liked/{LIKE_SERIAL}/
```

---

### Example: Entry Like Response
```json
{
  "type": "like",
  "author": {
    "type": "author",
    "id": "http://localhost/api/authors/3e9512c0-a78e-4270-a943-3f43159034b7",
    "host": "http://localhost/api/",
    "displayName": "Greg Johnson",
    "web": "http://localhost/authors/greg",
    "github": "http://github.com/gjohnson",
    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
    "description": "",
    "followers_count": 0,
    "friends_count": 0,
    "followings_count": 1,
    "entries_count": 0
  },
  "published": "2025-07-10T03:20:01+00:00",
  "id": "http://localhost/api/authors/3e9512c0-a78e-4270-a943-3f43159034b7/liked/255",
  "object": "http://localhost/api/authors/5cd65a/entries/987"
}
```

---

### Example: Comment Like Response
```json
{
  "type": "like",
  "author": {
    "type": "author",
    "id": "http://localhost/api/authors/3e9512c0-a78e-4270-a943-3f43159034b7",
    "host": "http://localhost/api/",
    "displayName": "Greg Johnson",
    "web": "http://localhost/authors/greg",
    "github": "http://github.com/gjohnson",
    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
    "description": "",
    "followers_count": 0,
    "friends_count": 0,
    "followings_count": 1,
    "entries_count": 0
  },
  "published": "2025-07-10T03:20:01+00:00",
  "id": "http://localhost/api/authors/3e9512c0-a78e-4270-a943-3f43159034b7/liked/255",
  "object": "http://localhost/api/authors/5cd65a/commented/42"
}
```

---

### Response Field Details

| Field       | Type     | Description |
|-------------|----------|-------------|
| `type`      | string   | Always `"like"` |
| `author`    | object   | The author who made the like |
| `published` | string   | ISO 8601 timestamp when the like was created |
| `id`        | string   | Canonical URL to this like |
| `object`    | string   | The URL of the object (entry or comment) that was liked |

---

### Error Responses

| Status Code | Reason |
|-------------|--------|
| 404 Not Found | Like not found for the given author and ID |
| 400 Bad Request | Invalid UUID format or malformed request |


## Likes API

### `GET /api/authors/{AUTHOR_SERIAL}/liked/`

Returns a list of all objects (comments and entries) that a given author has liked.

```
HTTP 200 OK  
Allow: GET, OPTIONS  
Content-Type: application/json  
Vary: Accept
```

### When to use
- When you want to retrieve all the likes an author has performed across the system.
- Useful for displaying a "liked items" history for an author.

### When not to use
- If you want to get likes **on** a particular comment or entry → use the likes endpoint for that object instead.
- If you want a **specific** like → use `GET /api/authors/{AUTHOR_SERIAL}/liked/{LIKE_SERIAL}/`

### How to use
Make a `GET` request to:

```
/api/authors/{AUTHOR_SERIAL}/liked/
```

### Example Response

```json
{
  "type": "likes",
  "web": "http://localhost/authors/greg/liked",
  "id": "http://localhost/api/authors/3e9512c0-a78e-4270-a943-3f43159034b7/liked",
  "page_number": 1,
  "size": 50,
  "count": 2,
  "src": [
    {
      "type": "like",
      "author": {
        "type": "author",
        "id": "http://localhost/api/authors/3e9512c0-a78e-4270-a943-3f43159034b7",
        "host": "http://localhost/api/",
        "displayName": "Greg Johnson",
        "web": "http://localhost/authors/greg",
        "github": "http://github.com/gjohnson",
        "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
        "description": "",
        "followers_count": 0,
        "friends_count": 0,
        "followings_count": 1,
        "entries_count": 0
      },
      "published": "2025-07-10T03:20:01+00:00",
      "id": "http://localhost/api/authors/3e9512c0-a78e-4270-a943-3f43159034b7/liked/255",
      "object": "http://localhost/api/authors/5cd65a/entries/987"
    },
    {
      "type": "like",
      "author": {
        "type": "author",
        "id": "http://localhost/api/authors/3e9512c0-a78e-4270-a943-3f43159034b7",
        "host": "http://localhost/api/",
        "displayName": "Greg Johnson",
        "web": "http://localhost/authors/greg",
        "github": "http://github.com/gjohnson",
        "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
        "description": "",
        "followers_count": 0,
        "friends_count": 0,
        "followings_count": 1,
        "entries_count": 0
      },
      "published": "2025-07-10T03:19:01+00:00",
      "id": "http://localhost/api/authors/3e9512c0-a78e-4270-a943-3f43159034b7/liked/254",
      "object": "http://localhost/api/authors/111/commented/130"
    }
  ]
}
```

### Response Field Details

| Field         | Type     | Description |
|---------------|----------|-------------|
| `type`        | string   | Always `"likes"` |
| `web`         | string   | HTML-friendly link to the author's likes page |
| `id`          | string   | Canonical API link to this author's liked items |
| `page_number` | integer  | The page number of results (pagination placeholder) |
| `size`        | integer  | Max number of items per page (currently fixed at 50) |
| `count`       | integer  | Total number of likes returned |
| `src`         | array    | List of like objects made by the author |

Each `like` object inside `src` includes:
- The liked object's URL (`object`)
- Timestamp of the like (`published`)
- The author who liked it (`author`)
- Unique identifier for the like (`id`)
- Type field set to `"like"`

## Comments API

### `GET /api/authors/{AUTHOR_SERIAL}/commented/`

Returns a paginated list of all comments made **by** the specified author.

### `POST /api/authors/{AUTHOR_SERIAL}/commented/`

Creates a new comment **by** the authenticated user (must match the author making the request).

---

### GET `/api/authors/{AUTHOR_SERIAL}/commented/`

Retrieve comments made by the specified author.

```
HTTP 200 OK  
Allow: GET, OPTIONS  
Content-Type: application/json  
Vary: Accept
```

#### When to use
- To show all comments a specific author has made (e.g., on their profile page or activity feed).

#### When not to use
- If you want comments **on** an entry → use the comments endpoint for the entry instead.

#### Example Response

```json
{
  "type": "comments",
  "web": "http://localhost:8000/s25-project-white/authors/111/commented",
  "id": "http://localhost:8000/s25-project-white/api/authors/111/commented",
  "page_number": 1,
  "size": 5,
  "count": 7,
  "src": [
    {
      "type": "comment",
      "author": {
        "type": "author",
        "id": "http://localhost/api/authors/111",
        "host": "http://localhost/api/",
        "displayName": "Greg Johnson",
        "web": "http://localhost/authors/greg",
        "github": "http://github.com/gjohnson",
        "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
        "description": "",
        "followers_count": 0,
        "friends_count": 0,
        "followings_count": 1,
        "entries_count": 0
      },
      "comment": "Looks great!",
      "contentType": "text/plain",
      "published": "2025-07-10T13:00:00+00:00",
      "id": "http://localhost/api/authors/111/commented/130",
      "entry": "http://localhost/api/authors/222/entries/249",
      "web": "http://localhost/authors/222/entries/249",
      "likes": {
        "type": "likes",
        "id": "http://localhost/api/authors/111/commented/130/likes",
        "web": "http://localhost/authors/greg/comments/130/likes",
        "page_number": 1,
        "size": 50,
        "count": 0,
        "src": []
      }
    }
  ]
}
```

#### Response Field Details

| Field         | Type     | Description |
|---------------|----------|-------------|
| `type`        | string   | Always `"comments"` |
| `web`         | string   | Human-facing URL for these comments |
| `id`          | string   | API endpoint URL |
| `page_number` | integer  | Current page number |
| `size`        | integer  | Number of comments per page (fixed at 5) |
| `count`       | integer  | Total number of comments by the author |
| `src`         | array    | The paginated comment objects |

---

### POST `/api/authors/{AUTHOR_SERIAL}/commented/`

Create a new comment by the authenticated user.

```
HTTP 201 Created  
Allow: POST, OPTIONS  
Content-Type: application/json  
Vary: Accept
```

#### When to use
- When a user is posting a comment to an entry they are allowed to view and interact with.

#### Requirements
- The user must be authenticated.
- The user must be friends with the entry's author (if the entry is friends-only).
- The user must be following the entry's author (if the entry is unlisted).
- A valid comment object must be included in the request body.

#### Example Request Body

```json
{
  "type": "comment",
  "comment": "Nice work!",
  "contentType": "text/plain",
  "entry": "6b705999-35f4-4385-bfef-5f5a733b2583"
}
```

#### Example Response

Returns the newly created comment object in the same format as the `GET` response above.

#### Errors

| Status Code | Description |
|-------------|-------------|
| 400         | Missing or invalid data (`type`, `comment`, `entry`, etc.) |
| 403         | Not allowed to comment due to visibility rules |
| 404         | Entry not found |
| 401         | User not authenticated |

---

### Notes
- Pagination is implemented on the GET request (5 comments per page).
- Sorting is done from newest to oldest.
- Comments with deleted parent entries are excluded.

## Entry Comments API

### `GET /api/authors/{AUTHOR_SERIAL}/entries/{ENTRY_SERIAL}/comments/`

Retrieve a paginated list of comments on the specified entry.

---

### When to use
Use this endpoint to retrieve the most recent comments made **on an entry** (not by a specific user).

---

### Authentication
- **Required** only if the entry is marked as `"FRIENDS"` visibility.
- Users must be a friend of the entry's author or the author themselves to see comments on `"FRIENDS"` entries.

---

### Query Parameters

| Parameter   | Type   | Default | Description                     |
|-------------|--------|---------|---------------------------------|
| `page`      | int    | 1       | The page number of results      |

---

### Example Request

```
GET /api/authors/222/entries/249/comments/
```

---

### Example Success Response

```json
{
  "type": "comments",
  "web": "http://nodebbbb/authors/222/entries/249",
  "id": "http://nodebbbb/authors/222/entries/249/comments",
  "page_number": 1,
  "size": 5,
  "count": 1023,
  "src": [
    {
      "type": "comment",
      "author": {
        "type": "author",
        "id": "http://nodeaaaa/api/authors/111",
        "web": "http://nodeaaaa/authors/greg",
        "host": "http://nodeaaaa/api/",
        "displayName": "Greg Johnson",
        "github": "http://github.com/gjohnson",
        "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
        "description": "",
        "followers_count": 0,
        "friends_count": 0,
        "followings_count": 1,
        "entries_count": 0
      },
      "comment": "Sick Olde English",
      "contentType": "text/markdown",
      "published": "2015-03-09T13:07:04+00:00",
      "id": "http://nodeaaaa/api/authors/111/commented/130",
      "entry": "http://nodebbbb/api/authors/222/entries/249",
      "web": "http://nodebbbb/authors/222/entries/249",
      "likes": {
        "type": "likes",
        "id": "http://nodeaaaa/api/authors/111/commented/130/likes",
        "web": "http://nodeaaaa/authors/greg/comments/130/likes",
        "page_number": 1,
        "size": 50,
        "count": 0,
        "src": []
      }
    }
  ]
}
```

---

### Response Fields

| Field         | Type     | Description                                  |
|---------------|----------|----------------------------------------------|
| `type`        | string   | Always `"comments"`                          |
| `web`         | string   | URL for viewing the entry (HTML)            |
| `id`          | string   | API URL for viewing comments on the entry   |
| `page_number` | integer  | Current page number                         |
| `size`        | integer  | Comments per page (always 5)                |
| `count`       | integer  | Total number of comments                    |
| `src`         | array    | List of comment objects                     |

---

### Possible Errors

| Status | Message                                                       |
|--------|---------------------------------------------------------------|
| 401    | Authentication required to view friends-only entry comments  |
| 403    | Only friends can view comments on friends-only entries       |
| 404    | Entry not found                                               |

---

### Notes
- Results are sorted by most recent first.
- Pagination is implemented with a page size of 5 comments per page.
- Likes on each comment are included inside the comment object.

## Other Local API
### GET /api/hi/wiki/
Get a list of entries from the author's wiki.
```
HTTP 200 OK
Allow: OPTIONS, GET
Content-Type: application/json
Vary: Accept
```
```json
[
    {
        "title": "FOR FRIENDS",
        "content": "whats up!",
        "author": "hi",
        "visibility": "FRIENDS",
        "created_at": "2025-07-08T19:38:06.291322+00:00",
        "serial": "7dcbb63c-0a78-4999-ab5c-4a4ac22d1cd6",
        "contentType": "text/plain"
    },
    {
        "title": "FOR EVERYONE",
        "content": "Hi!",
        "author": "hi",
        "visibility": "PUBLIC",
        "created_at": "2025-07-08T19:36:49.560079+00:00",
        "serial": "4683f30a-4acf-41c7-af72-b8f208abe419",
        "contentType": "text/plain"
    }
]
```
### GET /api/authors/{author_serial}
Get the author's profile information, which includes the author's information as well as all their entries' information.
```
HTTP 200 OK
Allow: OPTIONS, GET
Content-Type: application/json
Vary: Accept
```
```json
{
    "type": "author",
    "id": "http://127.0.0.1:8000/s25-project-white/api/authors/3150981f-c08b-4e0a-b13a-1d45d5a8a950",
    "host": "http://s25-project-white/api/",
    "displayName": "hi",
    "github": null,
    "profileImage": "/media/profile_images/Marshmallow_Cup_YkNfMkY.jpg",
    "web": "http://127.0.0.1:8000/s25-project-white/authors/3150981f-c08b-4e0a-b13a-1d45d5a8a950",
    "description": "",
    "followers_count": 0,
    "friends_count": 0,
    "followings_count": 1,
    "entries_count": 0
    "entries": [
        {
            "type": "entry",
            "title": "FOR EVERYONE",
            "id": "http://s25-project-white/authors/3150981f-c08b-4e0a-b13a-1d45d5a8a950/entries/4683f30a-4acf-41c7-af72-b8f208abe419",
            "web": "http://127.0.0.1:8000/s25-project-white/authors/3150981f-c08b-4e0a-b13a-1d45d5a8a950",
            "description": "entry by hi, titled: 'FOR EVERYONE",
            "contentType": "text/plain",
            "content": "Hi!",
            "author": {
                "type": "author",
                "id": "http://127.0.0.1:8000/s25-project-white/api/authors/3150981f-c08b-4e0a-b13a-1d45d5a8a950",
                "host": "http://s25-project-white/api/",
                "displayName": "hi",
                "web": "http://127.0.0.1:8000/s25-project-white/authors/3150981f-c08b-4e0a-b13a-1d45d5a8a950",
                "github": null,
                "profileImage": "/media/profile_images/Marshmallow_Cup_YkNfMkY.jpg"
                "description": "",
                "followers_count": 0,
                "friends_count": 0,
                "followings_count": 1,
                "entries_count": 0
            },
            "comments": {
                "type": "comments",
                "web": "http://s25-project-white/authors/3150981f-c08b-4e0a-b13a-1d45d5a8a950/entries/4683f30a-4acf-41c7-af72-b8f208abe419",
                "id": "http://s25-project-white/authors/3150981f-c08b-4e0a-b13a-1d45d5a8a950/entries/4683f30a-4acf-41c7-af72-b8f208abe419/comments",
                "page_number": 1,
                "size": 5,
                "count": 1,
                "src": [
                    {
                        "type": "comment",
                        "author": {
                            "type": "author",
                            "id": "http://127.0.0.1:8000/s25-project-white/api/authors/3150981f-c08b-4e0a-b13a-1d45d5a8a950",
                            "host": "http://s25-project-white/api/",
                            "displayName": "hi",
                            "web": "http://127.0.0.1:8000/s25-project-white/authors/3150981f-c08b-4e0a-b13a-1d45d5a8a950",
                            "github": null,
                            "profileImage": "/media/profile_images/Marshmallow_Cup_YkNfMkY.jpg"
                            "description": "",
                            "followers_count": 0,
                            "friends_count": 0,
                            "followings_count": 1,
                            "entries_count": 0
                        },
                        "comment": "wow! cool!",
                        "contentType": "text/plain",
                        "published": "2025-07-08T19:37:25+00:00",
                        "id": "http://localhost/api/authors/3150981f-c08b-4e0a-b13a-1d45d5a8a950/commented/1",
                        "entry": "http://s25-project-white/authors/3150981f-c08b-4e0a-b13a-1d45d5a8a950/entries/4683f30a-4acf-41c7-af72-b8f208abe419",
                        "web": null,
                        "likes": {
                            "type": "likes",
                            "id": "http://localhost/api/authors/3150981f-c08b-4e0a-b13a-1d45d5a8a950/commented/1/likes",
                            "web": "http://localhost/authors/hi/comments/1/likes",
                            "page_number": 1,
                            "size": 50,
                            "count": 0,
                            "src": []
                        }
                    }
                ]
            },
            "likes": {
                "type": "likes",
                "web": "http://s25-project-white/authors/3150981f-c08b-4e0a-b13a-1d45d5a8a950/entries/4683f30a-4acf-41c7-af72-b8f208abe419",
                "id": "http://s25-project-white/authors/3150981f-c08b-4e0a-b13a-1d45d5a8a950/entries/4683f30a-4acf-41c7-af72-b8f208abe419/likes",
                "page_number": 1,
                "size": 50,
                "count": 0,
                "src": []
            },
            "published": "2025-07-08T13:36:49.560079-06:00",
            "visibility": "PUBLIC"
        }
    ]
}
```

## Entry Likes API

### `GET /api/authors/{AUTHOR_SERIAL}/entries/{ENTRY_SERIAL}/likes/`

Retrieve a list of likes on a given entry.

---

### When to use

- When you want to view how many people have liked a public, friends-only, or unlisted entry.
- This is useful for displaying engagement statistics (User Story 1.4 - Comments/Likes).

---

### Authentication

- Required (user must be logged in).
- Visibility rules are enforced:
  - **PUBLIC**: Anyone can access.
  - **FRIENDS**: Only friends of the entry's author or the author themselves can access.
  - **UNLISTED**: Only followers of the entry’s author or the author themselves can access.

---

### Query Parameters

None

---

### Example Usage

#### Request

```
GET /api/authors/111/entries/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763/likes/
```

#### Successful Response (Public Entry)

```json
{
  "type": "likes",
  "web": "http://nodeaaaa/authors/111/entries/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763",
  "id": "http://nodeaaaa/api/authors/111/entries/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763/likes",
  "page_number": 1,
  "size": 50,
  "count": 2,
  "src": [
    {
      "type": "like",
      "author": {
        "type": "author",
        "id": "http://s25-project-white/api/authors/test1",
        "displayName": "test_author1",
        "host": "http://s25-project-white/api/",
        "web": "http://s25-project-white/authors/test1",
        "github": "http://github.com/test1",
        "profileImage": "https://example.com/img1.jpg"
        "description": "",
       "followers_count": 0,
        "friends_count": 0,
        "followings_count": 1,
        "entries_count": 0
      },
      "published": "2025-07-10T21:15:03+00:00",
      "id": "http://s25-project-white/api/authors/test1/liked/1",
      "object": "http://s25-project-white/api/authors/111/entries/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763"
    },
    {
      "type": "like",
      "author": {
        "type": "author",
        "id": "http://s25-project-white/api/authors/test2",
        "displayName": "test_author2",
        "host": "http://s25-project-white/api/",
        "web": "http://s25-project-white/authors/test2",
        "github": "http://github.com/test2",
        "profileImage": "https://example.com/img2.jpg",
        "description": "",
        "followers_count": 0,
        "friends_count": 0,
        "followings_count": 1,
         "entries_count": 0
      },
      "published": "2025-07-10T21:17:44+00:00",
      "id": "http://s25-project-white/api/authors/test2/liked/2",
      "object": "http://s25-project-white/api/authors/111/entries/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763"
    }
  ]
}
```

#### Friends-only Entry (Not Friends)

```json
{
  "error": "You are not friends with this author, you cannot view this entry"
}
```

#### Unlisted Entry (Not Following)

```json
{
  "error": "You are not following this author, you cannot view this entry"
}
```

---

### Response Fields

| Field        | Type     | Description                                      |
|--------------|----------|--------------------------------------------------|
| `type`       | string   | Always `"likes"`                                 |
| `web`        | string   | HTML-friendly page for the entry                 |
| `id`         | string   | API URL for this entry's likes                   |
| `page_number`| integer  | Page of results (pagination support)             |
| `size`       | integer  | Number of results per page                       |
| `count`      | integer  | Total number of likes                            |
| `src`        | array    | List of like objects (see LikeSummarySerializer) |

---

### Like Object Structure (in `src`)

| Field      | Type   | Description                                               |
|------------|--------|-----------------------------------------------------------|
| `type`     | string | Always `"like"`                                           |
| `author`   | object | Summary of the author who liked the entry                 |
| `published`| string | ISO 8601 timestamp of when the like occurred              |
| `id`       | string | Unique URL ID of the like (includes author + like ID)     |
| `object`   | string | URL of the liked entry                                    |

---

### Notes

- Like objects include detailed author data using `AuthorSummarySerializer`.
- Response is paginated (50 likes max per page).
- Sorting is from most recent to oldest.

## Comment Like API

### `POST /api/comment/{comment_id}/like/`

Allows an authenticated author to like a comment. This endpoint is part of **User Story 1.3** (Comments/Likes).

---

### When to Use

- When a user wants to show appreciation for a comment made by another author.
- Enables social interaction between users.

---

### Authentication

- Required: The user must be logged in.

---

### How to Use

1. Authenticate as a user.
2. Send a `POST` request to `/api/comment/{comment_id}/like/`.

---

### Why Use

- To register that an author liked a specific comment.

---

### Why Not Use

- If the comment doesn't exist.
- If the comment has already been liked by the author.

---

### Request Parameters

None

---

### Successful Response

Returns the full comment like object in the required federated format.

#### Example Request

```
POST /api/comment/130/like/
```

#### Example Response (`201 Created`)

```json
{
  "type": "like",
  "author": {
    "type": "author",
    "id": "http://nodebbbb/api/authors/222",
    "host": "http://nodebbbb/api/",
    "displayName": "Lara Croft",
    "web": "http://nodebbbb/authors/222",
    "github": "http://github.com/laracroft",
    "profileImage": "http://nodebbbb/api/authors/222/entries/217/image"
    "description": "",
    "followers_count": 0,
    "friends_count": 0,
    "followings_count": 1,
    "entries_count": 0
  },
  "published": "2025-07-10T13:07:04+00:00",
  "id": "http://nodeaaaa/api/authors/222/liked/255",
  "object": "http://nodeaaaa/api/authors/111/commented/130"
}
```

---

### Error Responses

#### Already Liked

```json
{
  "error": "Comment already liked"
}
```

#### Comment Not Found

```json
{
  "detail": "Not found."
}
```

---

### Response Fields

| Field      | Type   | Description                                                       |
|------------|--------|-------------------------------------------------------------------|
| `type`     | string | Always `"like"`                                                   |
| `author`   | object | Summary of the author who liked the comment                      |
| `published`| string | ISO 8601 timestamp when the like was created                      |
| `id`       | string | URL of the like, includes author ID and like ID                  |
| `object`   | string | URL of the comment that was liked                                |

---

### Notes

- This endpoint prevents duplicate likes by using `get_or_create()`.
- It ensures that only authenticated authors can like comments.
- The format returned matches ActivityPub-style federated specs.


## Like Entry API

### `POST /api/entry/{entry_serial}/like/`

Allows an authenticated author to like a specific entry. This endpoint implements **User Story 1.1** (Comments/Likes).

---

### When to Use

- When a user wants to show appreciation for a specific entry.

---

### Authentication

- Required: The user must be logged in.

---

### How to Use

1. Authenticate as a user.
2. Send a `POST` request to `/api/entry/{entry_serial}/like/`.

---

### Why Use

- To show appreciation for an entry.
- To increase engagement and interactivity between users.

---

### Why Not Use

- If the entry does not exist.
- If the user has already liked the entry.

---

### Request Parameters

None

---

### Successful Response (`201 Created`)

Returns a status indicating that the like was successfully registered.

```json
{
  "status": "liked",
  "message": "Entry liked successfully",
  "likes_count": 8
}
```

---

### Already Liked Response (`400 Bad Request`)

```json
{
  "status": "already_liked",
  "message": "You have already liked this entry",
  "likes_count": 8
}
```

---

### Error Response for Visibility Restriction

```json
{
  "error": "You are not friends with this author, you cannot view this entry"
}
```

---

### Response Fields

| Field         | Type     | Description                                               |
|---------------|----------|-----------------------------------------------------------|
| `status`      | string   | "liked" or "already_liked"                                |
| `message`     | string   | Description for frontend use                              |
| `likes_count` | integer  | Number of total likes on the entry                        |

---

## Get Single Comment API

### `GET /api/authors/{AUTHOR_SERIAL}/commented/{COMMENT_SERIAL}`

Retrieves a **single comment object** by its unique identifier (UUID) made by a specific author.

---

### When to Use

- To fetch the full details of a specific comment authored by a given author.
- To display the comment and associated metadata (author info, timestamp, likes, etc).

---

### Authentication

- Optional.
- If the comment belongs to an entry with restricted visibility (e.g., `FRIENDS` or `UNLISTED`), the requesting user must have appropriate permissions.

---

### How to Use

Send a `GET` request to:

```
/api/authors/{AUTHOR_SERIAL}/commented/{COMMENT_SERIAL}
```

Replace:
- `{AUTHOR_SERIAL}` with the author's unique ID or serial.
- `{COMMENT_SERIAL}` with the UUID of the specific comment.

---

### Why Use

- To retrieve a comment for rendering on a page.
- To inspect details such as the author, comment content, likes, and visibility.

---

### Why Not Use

- If you only need a list of comments on an entry, use the `GET /api/authors/{AUTHOR_SERIAL}/entries/{ENTRY_SERIAL}/comments` endpoint.
- If the comment is not visible to the current user due to privacy restrictions.

---

### Example Request

```http
GET /api/authors/111/commented/130
```

---

### Example Successful Response (`200 OK`)

```json
{
  "type": "comment",
  "author": {
    "type": "author",
    "id": "http://nodeaaaa/api/authors/111",
    "web": "http://nodeaaaa/authors/greg",
    "host": "http://nodeaaaa/api/",
    "displayName": "Greg Johnson",
    "github": "http://github.com/gjohnson",
    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
    "description": "",
    "followers_count": 0,
    "friends_count": 0,
    "followings_count": 1,
    "entries_count": 0
  },
  "comment": "Sick Olde English",
  "contentType": "text/markdown",
  "published": "2015-03-09T13:07:04+00:00",
  "id": "http://nodeaaaa/api/authors/111/commented/130",
  "entry": "http://nodebbbb/api/authors/222/entries/249",
  "web": "http://nodebbbb/authors/222/entries/249",
  "likes": {
    "type": "likes",
    "id": "http://nodeaaaa/api/authors/111/commented/130/likes",
    "web": "http://nodeaaaa/authors/greg/comments/130/likes",
    "page_number": 1,
    "size": 50,
    "count": 0,
    "src": []
  }
}
```

---

### Response Fields

| Field           | Type     | Description                                                      |
|------------------|----------|------------------------------------------------------------------|
| `type`           | string   | Always `"comment"`                                               |
| `author`         | object   | Full summary of the author who made the comment                 |
| `comment`        | string   | The comment content                                              |
| `contentType`    | string   | MIME type of the comment (e.g., `"text/plain"` or `"text/markdown"`) |
| `published`      | string   | ISO 8601 timestamp of when the comment was created              |
| `id`             | string   | URL pointing to the comment resource                            |
| `entry`          | string   | URL of the entry that the comment was posted on                 |
| `web`            | string   | (Optional) Frontend URL to view the comment or entry            |
| `likes`          | object   | Metadata and summaries of likes made on this comment            |

---

### Error Responses

- `404 Not Found` – If the comment does not exist or does not match the author.
- `403 Forbidden` – If the comment is not visible to the current user.

---

### Pagination

- This endpoint returns **a single comment** object and is **not paginated**.

---


---

## FQID-based Entry Comments API

### `GET /api/entries/{ENTRY_FQID}/comments/`

Retrieve a paginated list of comments on an entry using its Fully Qualified ID (FQID).

---

### When to use

- To get comments on an entry when you have the entry's FQID (URL-encoded).
- Supports both local and remote access to entry comments.
- Useful for federated/distributed systems where entries can be referenced by their complete URL.

---

### Authentication

- **Required**

---

### Query Parameters

| Parameter   | Type   | Default | Description                     |
|-------------|--------|---------|---------------------------------|
| `page`      | int    | 1       | The page number of results      |

---

### Example Request

```
GET /api/entries/http%3A//localhost/api/authors/222/entries/249/comments/?page=1
```

---

### Example Success Response

```json
{
  "type": "comments",
  "web": "http://localhost/authors/222/entries/249",
  "id": "http://localhost/api/authors/222/entries/249/comments",
  "page_number": 1,
  "size": 5,
  "count": 3,
  "src": [
    {
      "type": "comment",
      "author": {
        "type": "author",
        "id": "http://localhost/api/authors/111",
        "host": "http://localhost/api/",
        "displayName": "Greg Johnson",
        "web": "http://localhost/authors/greg",
        "github": "http://github.com/gjohnson",
        "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
      },
      "comment": "Great post!",
      "contentType": "text/plain",
      "published": "2025-07-10T13:07:04+00:00",
      "id": "http://localhost/api/authors/111/commented/130",
      "entry": "http://localhost/api/authors/222/entries/249",
      "web": "http://localhost/authors/222/entries/249",
      "likes": {
        "type": "likes",
        "id": "http://localhost/api/authors/111/commented/130/likes",
        "web": "http://localhost/authors/greg/comments/130/likes",
        "page_number": 1,
        "size": 50,
        "count": 0,
        "src": []
      }
    }
  ]
}
```

---

### Response Fields

| Field         | Type     | Description                                  |
|---------------|----------|----------------------------------------------|
| `type`        | string   | Always `"comments"`                          |
| `web`         | string   | URL for viewing the entry (HTML)            |
| `id`          | string   | API URL for viewing comments on the entry   |
| `page_number` | integer  | Current page number                         |
| `size`        | integer  | Comments per page (always 5)                |
| `count`       | integer  | Total number of comments                    |
| `src`         | array    | List of comment objects                     |

---

### Possible Errors

| Status | Message                                                       |
|--------|---------------------------------------------------------------|
| 400    | Invalid FQID format                                           |
| 401    | Authentication required to view friends-only entry comments  |
| 403    | Only friends can view comments on friends-only entries       |
| 404    | Entry not found                                               |

---

### Notes

- FQID must be URL-encoded in the request.
- Supports both local and remote entry access.
- Results are sorted by most recent first.
- Pagination is implemented with a page size of 5 comments per page.

---

## FQID-based Entry Likes API

### `GET /api/entries/{ENTRY_FQID}/likes/`

Retrieve a list of likes on an entry using its Fully Qualified ID (FQID).

---

### When to use

- To get likes on an entry when you have the entry's FQID (URL-encoded).
- Supports local access to entry likes.
- Useful for federated systems where entries are referenced by their complete URL.

---

### Authentication

- **Required** 

---

### Query Parameters

None

---

### Example Request

```
GET /api/entries/http%3A//localhost/api/authors/222/entries/249/likes/
```

---

### Example Success Response

```json
{
  "type": "likes",
  "web": "http://localhost/authors/222/entries/249",
  "id": "http://localhost/api/authors/222/entries/249/likes",
  "page_number": 1,
  "size": 50,
  "count": 2,
  "src": [
    {
      "type": "like",
      "author": {
        "type": "author",
        "id": "http://localhost/api/authors/111",
        "host": "http://localhost/api/",
        "displayName": "Greg Johnson",
        "web": "http://localhost/authors/greg",
        "github": "http://github.com/gjohnson",
        "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
        "description": "",
        "followers_count": 0,
        "friends_count": 0,
        "followings_count": 1,
        "entries_count": 0
      },
      "published": "2025-07-10T13:07:04+00:00",
      "id": "http://localhost/api/authors/111/liked/255",
      "object": "http://localhost/api/authors/222/entries/249"
    }
  ]
}
```

---

### Response Fields

| Field        | Type     | Description                                      |
|--------------|----------|--------------------------------------------------|
| `type`       | string   | Always `"likes"`                                 |
| `web`        | string   | HTML-friendly page for the entry                 |
| `id`         | string   | API URL for this entry's likes                   |
| `page_number`| integer  | Page of results (pagination support)             |
| `size`       | integer  | Number of results per page                       |
| `count`      | integer  | Total number of likes                            |
| `src`        | array    | List of like objects                             |

---

### Possible Errors

| Status | Message                                                       |
|--------|---------------------------------------------------------------|
| 400    | Invalid FQID format                                           |
| 401    | Authentication required                                       |
| 403    | Not authorized to view this entry's likes                     |
| 404    | Entry not found                                               |

---

### Notes

- FQID must be URL-encoded in the request.
- Currently supports local access only.
- Response is paginated (50 likes max per page).
- Sorting is from most recent to oldest.

---

## FQID-based Author Comments API

### `GET /api/authors/{AUTHOR_FQID}/commented/`

Retrieve a paginated list of comments made by an author using their Fully Qualified ID (FQID).

---

### When to use

- To get all comments made by an author when you have their FQID (URL-encoded).
- Supports local access to author comments.
- Useful for federated systems where authors are referenced by their complete URL.

---

### Authentication

- **Required** 

---

### Query Parameters

| Parameter   | Type   | Default | Description                     |
|-------------|--------|---------|---------------------------------|
| `page`      | int    | 1       | The page number of results      |

---

### Example Request

```
GET /api/authors/http%3A//localhost/api/authors/111/commented/?page=1
```

---

### Example Success Response

```json
{
  "type": "comments",
  "web": "http://localhost/authors/111/commented",
  "id": "http://localhost/api/authors/111/commented",
  "page_number": 1,
  "size": 5,
  "count": 3,
  "src": [
    {
      "type": "comment",
      "author": {
        "type": "author",
        "id": "http://localhost/api/authors/111",
        "host": "http://localhost/api/",
        "displayName": "Greg Johnson",
        "web": "http://localhost/authors/greg",
        "github": "http://github.com/gjohnson",
        "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
        "description": "",
        "followers_count": 0,
        "friends_count": 0,
        "followings_count": 1,
        "entries_count": 0
      },
      "comment": "Great post!",
      "contentType": "text/plain",
      "published": "2025-07-10T13:07:04+00:00",
      "id": "http://localhost/api/authors/111/commented/130",
      "entry": "http://localhost/api/authors/222/entries/249",
      "web": "http://localhost/authors/222/entries/249",
      "likes": {
        "type": "likes",
        "id": "http://localhost/api/authors/111/commented/130/likes",
        "web": "http://localhost/authors/greg/comments/130/likes",
        "page_number": 1,
        "size": 50,
        "count": 0,
        "src": []
      }
    }
  ]
}
```

---

### Response Fields

| Field         | Type     | Description                                  |
|---------------|----------|----------------------------------------------|
| `type`        | string   | Always `"comments"`                          |
| `web`         | string   | URL for viewing the author's comments (HTML) |
| `id`          | string   | API URL for viewing the author's comments    |
| `page_number` | integer  | Current page number                         |
| `size`        | integer  | Comments per page (always 5)                |
| `count`       | integer  | Total number of comments                    |
| `src`         | array    | List of comment objects                     |

---

### Possible Errors

| Status | Message                                                       |
|--------|---------------------------------------------------------------|
| 400    | Invalid FQID format                                           |
| 401    | Authentication required                                       |
| 404    | Author not found                                              |

---

### Notes

- FQID must be URL-encoded in the request.
- Currently supports local access only.
- Results are sorted by most recent first.
- Pagination is implemented with a page size of 5 comments per page.

---

## FQID-based Author Likes API

### `GET /api/authors/{AUTHOR_FQID}/liked/`

Retrieve a list of all objects (comments and entries) that an author has liked using their Fully Qualified ID (FQID).

---

### When to use

- To get all likes made by an author when you have their FQID (URL-encoded).
- Supports local access to author likes.
- Useful for federated systems where authors are referenced by their complete URL.

---

### Authentication

- **Required** 

---

### Query Parameters

None

---

### Example Request

```
GET /api/authors/http%3A//localhost/api/authors/111/liked/
```

---

### Example Success Response

```json
{
  "type": "likes",
  "web": "http://localhost/authors/111/liked",
  "id": "http://localhost/api/authors/111/liked",
  "page_number": 1,
  "size": 50,
  "count": 2,
  "src": [
    {
      "type": "like",
      "author": {
        "type": "author",
        "id": "http://localhost/api/authors/111",
        "host": "http://localhost/api/",
        "displayName": "Greg Johnson",
        "web": "http://localhost/authors/greg",
        "github": "http://github.com/gjohnson",
        "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
        "description": "",
        "followers_count": 0,
        "friends_count": 0,
        "followings_count": 1,
        "entries_count": 0
      },
      "published": "2025-07-10T13:07:04+00:00",
      "id": "http://localhost/api/authors/111/liked/255",
      "object": "http://localhost/api/authors/222/entries/249"
    },
    {
      "type": "like",
      "author": {
        "type": "author",
        "id": "http://localhost/api/authors/111",
        "host": "http://localhost/api/",
        "displayName": "Greg Johnson",
        "web": "http://localhost/authors/greg",
        "github": "http://github.com/gjohnson",
        "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
        "description": "",
        "followers_count": 0,
        "friends_count": 0,
        "followings_count": 1,
        "entries_count": 0
      },
      "published": "2025-07-10T13:06:04+00:00",
      "id": "http://localhost/api/authors/111/liked/254",
      "object": "http://localhost/api/authors/333/commented/130"
    }
  ]
}
```

---

### Response Fields

| Field         | Type     | Description                                  |
|---------------|----------|----------------------------------------------|
| `type`        | string   | Always `"likes"`                             |
| `web`         | string   | URL for viewing the author's likes (HTML)    |
| `id`          | string   | API URL for viewing the author's likes       |
| `page_number` | integer  | Current page number                         |
| `size`        | integer  | Likes per page (always 50)                  |
| `count`       | integer  | Total number of likes                       |
| `src`        | array    | List of like objects                        |

---

### Possible Errors

| Status | Message                                                       |
|--------|---------------------------------------------------------------|
| 400    | Invalid FQID format                                           |
| 401    | Authentication required                                       |
| 404    | Author not found                                              |

---

### Notes

- FQID must be URL-encoded in the request.
- Currently supports local access only.
- Combines likes on both entries and comments.
- Response is paginated (50 likes max per page).
- Sorting is from most recent to oldest.

---

## FQID-based Comment Likes API

### `GET /api/authors/{AUTHOR_SERIAL}/entries/{ENTRY_SERIAL}/comments/{COMMENT_FQID}/likes/`

Retrieve a list of likes on a comment using its Fully Qualified ID (FQID).

---

### When to use

- To get likes on a comment when you have the comment's FQID (URL-encoded).
- Supports both local and remote access to comment likes.
- Useful for federated systems where comments are referenced by their complete URL.

---

### Authentication

- **Required**

---

### Query Parameters

None

---

### Example Request

```
GET /api/authors/222/entries/249/comments/http%3A//localhost/api/authors/111/commented/130/likes/
```

---

### Example Success Response

```json
{
  "type": "likes",
  "web": "http://localhost/authors/111/comments/130/likes",
  "id": "http://localhost/api/authors/111/commented/130/likes",
  "page_number": 1,
  "size": 50,
  "count": 1,
  "src": [
    {
      "type": "like",
      {
      "type": "like",
      "author": {
        "type": "author",
        "id": "http://localhost/api/authors/333",
        "host": "http://localhost/api/",
        "displayName": "Jane Doe",
        "web": "http://localhost/authors/jane",
        "github": "http://github.com/janedoe",
        "profileImage": "https://i.imgur.com/example.jpg",
        "followers_count": 12,
        "friends_count": 7,
        "followings_count": 9,
        "entries_count": 15
      },
      "published": "2025-07-10T13:07:04+00:00",
      "id": "http://localhost/api/authors/333/liked/256",
      "object": "http://localhost/api/authors/111/commented/130"
    }
  ]
}
```

---

### Response Fields

| Field        | Type     | Description                                      |
|--------------|----------|--------------------------------------------------|
| `type`       | string   | Always `"likes"`                                 |
| `web`        | string   | HTML-friendly page for the comment's likes      |
| `id`         | string   | API URL for this comment's likes                |
| `page_number`| integer  | Page of results (pagination support)             |
| `size`       | integer  | Number of results per page                       |
| `count`      | integer  | Total number of likes                            |
| `src`        | array    | List of like objects                             |

---

### Possible Errors

| Status | Message                                                       |
|--------|---------------------------------------------------------------|
| 400    | Invalid FQID format                                           |
| 401    | Authentication required                                       |
| 403    | Not authorized to view this comment's likes                   |
| 404    | Comment not found                                             |

---

### Notes

- FQID must be URL-encoded in the request.
- Supports both local and remote comment access.
- Response is paginated (50 likes max per page).
- Sorting is from most recent to oldest.

---

## Single Comment by FQID API

### `GET /api/authors/{AUTHOR_SERIAL}/entries/{ENTRY_SERIAL}/comment/{REMOTE_COMMENT_FQID}/`

Retrieve a single comment by its Fully Qualified ID (FQID).

---

### When to use

- To get a specific comment when you have its FQID (URL-encoded).
- Supports both local and remote access to comments.
- Useful for federated systems where comments are referenced by their complete URL.

---

### Authentication

- **Required** 

---

### Example Request

```
GET /api/authors/222/entries/249/comment/http%3A//localhost/api/authors/111/commented/130/
```

---

### Example Success Response

```json
{
  "type": "comment",
   "author": {
    "type": "author",
    "id": "http://local-node/api/authors/111",
    "host": "http://local-node/api/",
    "displayName": "Greg Johnson",
    "web": "http://local-node/authors/greg",
    "github": "http://github.com/gjohnson",
    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
    "followers_count": 5,
    "friends_count": 2,
    "followings_count": 4,
    "entries_count": 8
  },
  "comment": "Great post!",
  "contentType": "text/plain",
  "published": "2025-07-10T13:07:04+00:00",
  "id": "http://localhost/api/authors/111/commented/130",
  "entry": "http://localhost/api/authors/222/entries/249",
  "web": "http://localhost/authors/222/entries/249",
  "likes": {
    "type": "likes",
    "id": "http://localhost/api/authors/111/commented/130/likes",
    "web": "http://localhost/authors/greg/comments/130/likes",
    "page_number": 1,
    "size": 50,
    "count": 0,
    "src": []
  }
}
```

---

### Response Fields

| Field           | Type     | Description                                                      |
|------------------|----------|------------------------------------------------------------------|
| `type`           | string   | Always `"comment"`                                               |
| `author`         | object   | Full summary of the author who made the comment                 |
| `comment`        | string   | The comment content                                              |
| `contentType`    | string   | MIME type of the comment (e.g., `"text/plain"` or `"text/markdown"`) |
| `published`      | string   | ISO 8601 timestamp of when the comment was created              |
| `id`             | string   | URL pointing to the comment resource                            |
| `entry`          | string   | URL of the entry that the comment was posted on                 |
| `web`            | string   | Frontend URL to view the comment or entry                       |
| `likes`          | object   | Metadata and summaries of likes made on this comment            |

---

### Possible Errors

| Status | Message                                                       |
|--------|---------------------------------------------------------------|
| 400    | Invalid FQID format                                           |
| 401    | Authentication required for restricted content                 |
| 403    | Not authorized to view this comment                            |
| 404    | Comment not found                                             |

---

### Notes

- FQID must be URL-encoded in the request.
- Supports both local and remote comment access.
- Returns a single comment object (not paginated).

---

## Single Comment by FQID (Direct) API

### `GET /api/commented/{COMMENT_FQID}/`

Retrieve a single comment by its Fully Qualified ID (FQID) directly.

---

### When to use

- To get a specific comment when you have its FQID (URL-encoded).
- Supports local access to comments.
- Useful for direct comment lookup without needing author/entry context.

---

### Authentication

- **Required** 

---

### Example Request

```
GET /api/commented/http%3A//localhost/api/authors/111/commented/130/
```

---

### Example Success Response

```json
{
  "type": "comment",
   "author": {
    "type": "author",
    "id": "http://local-node/api/authors/111",
    "host": "http://local-node/api/",
    "displayName": "Greg Johnson",
    "web": "http://local-node/authors/greg",
    "github": "http://github.com/gjohnson",
    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
    "followers_count": 5,
    "friends_count": 2,
    "followings_count": 4,
    "entries_count": 8
  },
  "comment": "Great post!",
  "contentType": "text/plain",
  "published": "2025-07-10T13:07:04+00:00",
  "id": "http://localhost/api/authors/111/commented/130",
  "entry": "http://localhost/api/authors/222/entries/249",
  "web": "http://localhost/authors/222/entries/249",
  "likes": {
    "type": "likes",
    "id": "http://localhost/api/authors/111/commented/130/likes",
    "web": "http://localhost/authors/greg/comments/130/likes",
    "page_number": 1,
    "size": 50,
    "count": 0,
    "src": []
  }
}
```

---

### Response Fields

| Field           | Type     | Description                                                      |
|------------------|----------|------------------------------------------------------------------|
| `type`           | string   | Always `"comment"`                                               |
| `author`         | object   | Full summary of the author who made the comment                 |
| `comment`        | string   | The comment content                                              |
| `contentType`    | string   | MIME type of the comment (e.g., `"text/plain"` or `"text/markdown"`) |
| `published`      | string   | ISO 8601 timestamp of when the comment was created              |
| `id`             | string   | URL pointing to the comment resource                            |
| `entry`          | string   | URL of the entry that the comment was posted on                 |
| `web`            | string   | Frontend URL to view the comment or entry                       |
| `likes`          | object   | Metadata and summaries of likes made on this comment            |

---

### Possible Errors

| Status | Message                                                       |
|--------|---------------------------------------------------------------|
| 400    | Invalid FQID format                                           |
| 401    | Authentication required for restricted content                 |
| 403    | Not authorized to view this comment                            |
| 404    | Comment not found                                             |

---

### Notes

- FQID must be URL-encoded in the request.
- Currently supports local access only.
- Returns a single comment object (not paginated).

---

## Single Like by FQID API

### `GET /api/liked/{LIKE_FQID}/`

Retrieve a single like by its Fully Qualified ID (FQID).

---

### When to use

- To get a specific like when you have its FQID (URL-encoded).
- Supports local access to likes.
- Useful for direct like lookup without needing author context.

---

### Authentication

- **Required** 

---

### Example Request

```
GET /api/liked/http%3A//localhost/api/authors/111/liked/255/
```

---

### Example Success Response

```json
 "author": {
    "type": "author",
    "id": "http://local-node/api/authors/111",
    "host": "http://local-node/api/",
    "displayName": "Greg Johnson",
    "web": "http://local-node/authors/greg",
    "github": "http://github.com/gjohnson",
    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
    "followers_count": 5,
    "friends_count": 2,
    "followings_count": 4,
    "entries_count": 8
  },
  "published": "2025-07-10T13:07:04+00:00",
  "id": "http://localhost/api/authors/111/liked/255",
  "object": "http://localhost/api/authors/222/entries/249"
}
```

---

### Response Fields

| Field       | Type     | Description |
|-------------|----------|-------------|
| `type`      | string   | Always `"like"` |
| `author`    | object   | The author who made the like |
| `published` | string   | ISO 8601 timestamp when the like was created |
| `id`        | string   | Canonical URL to this like |
| `object`    | string   | The URL of the object (entry or comment) that was liked |

---

### Possible Errors

| Status | Message                                                       |
|--------|---------------------------------------------------------------|
| 400    | Invalid FQID format                                           |
| 401    | Authentication required                                       |
| 404    | Like not found                                                |

---

### Notes

- FQID must be URL-encoded in the request.
- Currently supports local access only.
- Returns a single like object (not paginated).
- Works for both entry likes and comment likes.

---

# Missing Endpoints — Full Documentation


---

## Single Author by FQID API

### `GET /api/authors/{AUTHOR_FQID}/`

Retrieve an author's profile using their Fully Qualified ID (FQID).

---

### When to use

- To fetch an author's profile from a **remote** node.
- When you have the author's FQID and need their details.
- Useful in federated environments to resolve remote authors.

---

### Authentication

- Not required 

---

### Example Request

```
GET /api/authors/http%3A//example.com/api/authors/111/
```

---

### Example Success Response

```json
{
  "type": "author",
  "id": "http://remote-node/api/authors/222",
  "host": "http://remote-node/api/",
  "displayName": "Lara Croft",
  "github": "http://github.com/laracroft",
  "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
  "web": "http://remote-node/authors/lara",
  "followers_count": 25,
  "friends_count": 10,
  "followings_count": 18,
  "entries_count": 42
}
```

---

### Response Fields

| Field         | Type   | Description |
|---------------|--------|-------------|
| `type`        | string | Always `"author"` |
| `id`          | string | Canonical URL for the author |
| `host`        | string | Host server URL |
| `displayName` | string | Display name of the author |
| `github`      | string | Author's GitHub profile URL |
| `profileImage`| string | Profile image URL |
| `web`         | string | HTML profile page URL |

---

### Possible Errors

| Status | Message                 |
|--------|-------------------------|
| 401    | Authentication required |
| 404    | Author not found        |

---

### Notes

- FQID must be URL-encoded in the path.
- Works for fetching remote authors your node knows about (or discovers).

---

## Check if Author Has Follower API

### `GET /api/authors/{AUTHOR_SERIAL}/followers/{FOREIGN_AUTHOR_FQID}`

Check if a specific foreign author is following the given author.

---

### When to use

- To verify whether a follow request was accepted.
- Used in friend/follower logic to determine relationship state.

---

### Authentication

- Not required

---

### Example Request

```
GET /api/authors/111/followers/http%3A//remote-node/api/authors/222
```

---

### Example Success Response

```json
{
  "type": "author",
  "id": "http://remote-node/api/authors/222",
  "host": "http://remote-node/api/",
  "displayName": "Lara Croft",
  "github": "http://github.com/laracroft",
  "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
  "web": "http://remote-node/authors/lara",
  "followers_count": 25,
  "friends_count": 10,
  "followings_count": 18,
  "entries_count": 42
}
```

---

### Response Fields

| Field         | Type   | Description |
|---------------|--------|-------------|
| `type`        | string | Always `"author"` |
| `id`          | string | Canonical URL for the foreign author |
| `host`        | string | Host server URL |
| `displayName` | string | Display name of the foreign author |
| `github`      | string | GitHub profile URL |
| `profileImage`| string | Profile image URL |
| `web`         | string | HTML profile page |

---

### Possible Errors

| Status | Message                 |
|--------|-------------------------|
| 404    | Not a follower          |
| 400    | Invalid FQID format     |
| 401    | Authentication required |

---

### Notes

- The `FOREIGN_AUTHOR_FQID` must be URL-encoded.
- Can be used by both local and remote requests.

---

## Add Follower API

### `PUT /api/authors/{AUTHOR_SERIAL}/followers/{FOREIGN_AUTHOR_FQID}`

Add a foreign author as a follower of the given author.

---

### When to use

- To accept a follow request.
- To add a follower relationship in a federated network.

---

### Authentication

- **Required** – must be authenticated as the local author (or admin).

---

### Example Request

```
PUT /api/authors/111/followers/http%3A//remote-node/api/authors/222
```

**Request Body:**
```json
{
  "type": "author",
  "id": "http://remote-node/api/authors/222",
  "host": "http://remote-node/api/",
  "displayName": "Lara Croft",
  "github": "http://github.com/laracroft",
  "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
  "web": "http://remote-node/authors/lara",
  "followers_count": 25,
  "friends_count": 10,
  "followings_count": 18,
  "entries_count": 42
}
```

---

### Example Success Response

```json
{
  "message": "Follower added successfully."
}
```

---

### Possible Errors

| Status | Message                        |
|--------|--------------------------------|
| 401    | Authentication required        |
| 400    | Invalid author object provided |
| 409    | Author is already a follower   |

---

### Notes

- The foreign author ID in the path must be URL-encoded.
- The body should contain the full author object.

---

## Remove Follower API

### `DELETE /api/authors/{AUTHOR_SERIAL}/followers/{FOREIGN_AUTHOR_FQID}`

Remove a foreign author from the follower list of the given author.

---

### When to use

- To revoke a follower relationship (unfollow/remove).
- To enforce privacy or block unwanted followers.

---

### Authentication

- **Required** – must be authenticated as the local author (or admin).

---

### Example Request

```
DELETE /api/authors/111/followers/http%3A//remote-node/api/authors/222
```

---

### Example Success Response

```
HTTP 204 No Content
```

---

### Possible Errors

| Status | Message                 |
|--------|-------------------------|
| 401    | Authentication required |
| 404    | Follower not found      |

---

### Notes

- The `FOREIGN_AUTHOR_FQID` must be URL-encoded.
- Idempotent: deleting a non-existent follower may return 404.

---

## Send Follow Request (Inbox) API

### `POST /api/authors/{AUTHOR_SERIAL}/inbox`

Send a **follow** request object to the specified author's inbox (remote → local).

---

### When to use

- When a remote author wants to follow a local author.
- Part of federation: requests are pushed to the receiver’s inbox.

---

### Authentication

- **Required** – node-to-node or request-level auth (implementation-specific).

---

### Example Request

```
POST /api/authors/111/inbox
```

**Request Body:**
```json
{
  "type": "follow",
  "summary": "actor wants to follow object",
  "actor": {
    {
  "type": "author",
  "id": "http://remote-node/api/authors/222",
  "host": "http://remote-node/api/",
  "displayName": "Lara Croft",
  "github": "http://github.com/laracroft",
  "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
  "web": "http://remote-node/authors/lara",
  "followers_count": 25,
  "friends_count": 10,
  "followings_count": 18,
  "entries_count": 42
 },
  "object": {
    "author": {
    "type": "author",
    "id": "http://local-node/api/authors/111",
    "host": "http://local-node/api/",
    "displayName": "Greg Johnson",
    "web": "http://local-node/authors/greg",
    "github": "http://github.com/gjohnson",
    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
    "followers_count": 5,
    "friends_count": 2,
    "followings_count": 4,
    "entries_count": 8
  }
}
```

---

### Example Success Response

```
HTTP 202 Accepted
```

```json
{ "message": "Follow request accepted for delivery." }
```

---

### Possible Errors

| Status | Message                        |
|--------|--------------------------------|
| 400    | Invalid follow object          |
| 401    | Authentication required        |
| 404    | Target author not found        |
| 409    | Duplicate/Already requested    |

---

### Notes

- The receiver will later decide to accept/reject (out of band).

---

## List Author Entries API

### `GET /api/authors/{AUTHOR_SERIAL}/entries/`

List recent entries authored by the specified author (paginated).

---

### When to use

- To render an author's timeline or profile posts.
- To fetch entries with visibility filtering.

---

### Example Request

```
GET /api/authors/111/entries/?page=1
```

---

### Example Success Response

```json
{
  "type": "entries",
  "web": "http://local-node/authors/111",
  "id": "http://local-node/api/authors/111/entries",
  "page_number": 1,
  "size": 5,
  "count": 2,
  "src": [
    {
      "type": "entry",
      "title": "First Post",
      "id": "http://local-node/api/authors/111/entries/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763",
      "web": "http://local-node/authors/111/entries/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763",
      "description": "A short intro post",
      "contentType": "text/markdown",
      "content": "Hello **world**!",
      "published": "2025-07-10T21:10:00+00:00",
      "visibility": "PUBLIC"
    }
  ]
}
```

---

### Response Fields

| Field         | Type   | Description                           |
|---------------|--------|---------------------------------------|
| `type`        | string | Always `"entries"`                    |
| `web`         | string | HTML listing for the author's entries |
| `id`          | string | API URL for this listing              |
| `page_number` | int    | Current page                          |
| `size`        | int    | Page size (default 5)                 |
| `count`       | int    | Items returned in this page           |
| `src`         | array  | Array of entry objects (summaries)    |

---

### Possible Errors

| Status | Message                      |
|--------|------------------------------|
| 401    | Authentication required      |
| 403    | Not authorized (visibility)  |
| 404    | Author not found             |

---

## Create Entry API

### `POST /api/authors/{AUTHOR_SERIAL}/entries/`

Create a new entry for the specified author (server generates a new ID).

---

### When to use

- Author creates a new post/entry (text or image).

---

### Authentication

- **Required** – must be authenticated as that author.

---

### Example Request

```
POST /api/authors/111/entries/
```

**Request Body:**
```json
{
  "type": "entry",
  "title": "My new post",
  "description": "Short summary",
  "contentType": "text/markdown",
  "content": "This is **awesome**.",
  "visibility": "PUBLIC"
}
```

---

### Example Success Response

```
HTTP 201 Created
```

```json
{
  "type": "entry",
  "title": "My new post",
  "id": "http://local-node/api/authors/111/entries/4f1b9c4a-7a1f-4b59-8d1a-0cd9f8b7f000",
  "web": "http://local-node/authors/111/entries/4f1b9c4a-7a1f-4b59-8d1a-0cd9f8b7f000",
  "description": "Short summary",
  "contentType": "text/markdown",
  "content": "This is **awesome**.",
  "author": {
    "type": "author",
    "id": "http://local-node/api/authors/111",
    "host": "http://local-node/api/",
    "displayName": "Greg Johnson",
    "web": "http://local-node/authors/greg",
    "github": "http://github.com/gjohnson",
    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
    "followers_count": 5,
    "friends_count": 2,
    "followings_count": 4,
    "entries_count": 8
  },
  "comments": {
    "type": "comments",
    "id": "http://local-node/api/authors/111/entries/4f1.../comments",
    "web": "http://local-node/authors/111/entries/4f1...",
    "page_number": 1,
    "size": 5,
    "count": 0,
    "src": []
  },
  "likes": {
    "type": "likes",
    "id": "http://local-node/api/authors/111/entries/4f1.../likes",
    "web": "http://local-node/authors/111/entries/4f1...",
    "page_number": 1,
    "size": 50,
    "count": 0,
    "src": []
  },
  "published": "2025-07-11T02:10:00-06:00",
  "visibility": "PUBLIC"
}
```

---

### Possible Errors

| Status | Message                        |
|--------|--------------------------------|
| 400    | Invalid entry object           |
| 401    | Authentication required        |
| 403    | Not allowed for this author    |

---

## Update Entry API

### `PUT /api/authors/{AUTHOR_SERIAL}/entries/{ENTRY_SERIAL}`

Update an existing entry authored by the specified author.

---

### When to use

- To edit an entry’s content, title, or visibility.

---

### Authentication

- **Required** – must be the author (or admin).

---

### Example Request

```
PUT /api/authors/111/entries/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763
```

**Request Body:**
```json
{
  "title": "Updated title",
  "content": "Updated content",
  "visibility": "FRIENDS"
}
```

---

### Example Success Response

```json
{
  "type": "entry",
  "title": "Updated title",
  "id": "http://local-node/api/authors/111/entries/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763",
  "web": "http://local-node/authors/111/entries/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763",
  "description": "Short summary",
  "contentType": "text/markdown",
  "content": "Updated content",
  "published": "2025-07-10T21:10:00+00:00",
  "visibility": "FRIENDS"
}
```

---

### Possible Errors

| Status | Message                 |
|--------|-------------------------|
| 400    | Invalid update payload  |
| 401    | Authentication required |
| 403    | Not the entry’s author  |
| 404    | Entry not found         |

---

## Delete Entry API

### `DELETE /api/authors/{AUTHOR_SERIAL}/entries/{ENTRY_SERIAL}`

Delete an entry authored by the specified author.

---

### Authentication

- **Required** – must be the author (or admin).

---

### Example Request

```
DELETE /api/authors/111/entries/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763
```

---

### Example Success Response

```
HTTP 204 No Content
```

---

### Possible Errors

| Status | Message                 |
|--------|-------------------------|
| 401    | Authentication required |
| 403    | Not the entry’s author  |
| 404    | Entry not found         |

---

## Get Entry by FQID API

### `GET /api/entries/{ENTRY_FQID}`

Retrieve a single entry using its Fully Qualified ID (FQID).

---

### Authentication

- Visibility rules apply (PUBLIC/FRIENDS/UNLISTED).

---

### Example Request

```
GET /api/entries/http%3A//remote-node/api/authors/222/entries/249
```

---

### Example Success Response

```json
{
  "type": "entry",
  "title": "Remote Post",
  "id": "http://remote-node/api/authors/222/entries/249",
  "web": "http://remote-node/authors/222/entries/249",
  "description": "Post from remote node",
  "contentType": "text/plain",
  "content": "Hello from remote.",
  {
  "type": "author",
  "id": "http://example.com/api/authors/111",
  "host": "http://example.com/api/",
  "displayName": "Lara Croft",
  "github": "http://github.com/laracroft",
  "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
  "web": "http://example.com/authors/lara",
  "followers_count": 15,
  "friends_count": 8,
  "followings_count": 12,
  "entries_count": 23
  },
  "published": "2025-07-10T12:00:00+00:00",
  "visibility": "PUBLIC"
}
```

---

### Possible Errors

| Status | Message                      |
|--------|------------------------------|
| 400    | Invalid FQID format          |
| 401    | Authentication required      |
| 403    | Not authorized (visibility)  |
| 404    | Entry not found              |

---

## Get Entry Image (by Serial) API

### `GET /api/authors/{AUTHOR_SERIAL}/entries/{ENTRY_SERIAL}/image`

Return the binary image represented by an image entry.

---

### Authentication

- Visibility rules apply (PUBLIC/FRIENDS/UNLISTED).

---

### Example Request

```
GET /api/authors/111/entries/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763/image
```

---

### Example Success Response

```
HTTP 200 OK
Content-Type: image/png
<binary data>
```

---

### Possible Errors

| Status | Message                      |
|--------|------------------------------|
| 401    | Authentication required      |
| 403    | Not authorized (visibility)  |
| 404    | Not found or not an image    |

---

### Notes

- Useful for `<img>` tags; decodes base64 image entries for direct serving.

---

## Get Entry Image (by FQID) API

### `GET /api/entries/{ENTRY_FQID}/image`

Return the binary image for an image entry by FQID.

---

### Authentication

- Visibility rules apply.

---

### Example Request

```
GET /api/entries/http%3A//remote-node/api/authors/222/entries/249/image
```

---

### Example Success Response

```
HTTP 200 OK
Content-Type: image/jpeg
<binary data>
```

---

### Possible Errors

| Status | Message                      |
|--------|------------------------------|
| 400    | Invalid FQID format          |
| 401    | Authentication required      |
| 403    | Not authorized (visibility)  |
| 404    | Not found or not an image    |

---

## Send Comment (Inbox) API

### `POST /api/authors/{AUTHOR_SERIAL}/inbox`

Send a **comment** object to the specified author's inbox (remote → local).

---

### When to use

- When a remote author comments on a local author’s entry.
- Part of federation: comments are pushed to the receiver’s inbox.

---

### Authentication

- **Required** – node-to-node or request-level auth (implementation-specific).

---

### Example Request

```
POST /api/authors/111/inbox
```

**Request Body:**
```json
 {
  {
  "type": "author",
  "id": "http://example.com/api/authors/111",
  "host": "http://example.com/api/",
  "displayName": "Lara Croft",
  "github": "http://github.com/laracroft",
  "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
  "web": "http://example.com/authors/lara",
  "followers_count": 15,
  "friends_count": 8,
  "followings_count": 12,
  "entries_count": 23
  },
  "comment": "Nice post!",
  "contentType": "text/markdown",
  "published": "2025-07-10T13:07:04+00:00",
  "entry": "http://local-node/api/authors/111/entries/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763",
  "id": "http://remote-node/api/authors/222/commented/130"
}
```

---

### Example Success Response

```
HTTP 202 Accepted
```

```json
{ "message": "Comment accepted for delivery." }
```

---

### Possible Errors

| Status | Message                          |
|--------|----------------------------------|
| 400    | Invalid comment object           |
| 401    | Authentication required          |
| 404    | Target author or entry not found |

---

## Send Like (Inbox) API

### `POST /api/authors/{AUTHOR_SERIAL}/inbox`

Send a **like** object to the specified author's inbox (remote → local).

---

### When to use

- When a remote author likes a local author’s entry or comment.
- Part of federation: likes are pushed to the receiver’s inbox.

---

### Authentication

- **Required** – node-to-node or request-level auth (implementation-specific).

---

### Example Request

```
POST /api/authors/111/inbox
```

**Request Body:**
```json
{
  "type": "like",
  {
  "type": "author",
  "id": "http://example.com/api/authors/111",
  "host": "http://example.com/api/",
  "displayName": "Lara Croft",
  "github": "http://github.com/laracroft",
  "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
  "web": "http://example.com/authors/lara",
  "followers_count": 15,
  "friends_count": 8,
  "followings_count": 12,
  "entries_count": 23
  },
  "published": "2025-07-10T13:07:04+00:00",
  "id": "http://remote-node/api/authors/222/liked/255",
  "object": "http://local-node/api/authors/111/entries/7b2d7ad6-f630-4bd3-8ae6-b1dd176aa763"
}
```

---

### Example Success Response

```
HTTP 202 Accepted
```

```json
{ "message": "Like accepted for delivery." }
```

---

### Possible Errors

| Status | Message                        |
|--------|--------------------------------|
| 400    | Invalid like object            |
| 401    | Authentication required        |
| 404    | Target author or object not found |

---

### Notes

- The `object` of a like may be an **entry** or a **comment** URL.

