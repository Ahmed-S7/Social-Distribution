# SocialDistribution

A federated social networking application built with Django that enables users to connect, share content, and interact across distributed nodes in an ActivityPub-like network.

![Project Status](https://img.shields.io/badge/status-completed-success)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Django](https://img.shields.io/badge/django-5.2.4-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## 🎬 Demo Video

Watch the full demonstration of the application's features:

[![SocialDistribution Demo](https://img.youtube.com/vi/aaOTHRIbRf8/maxresdefault.jpg)](https://www.youtube.com/watch?v=aaOTHRIbRf8)

*Click the image above to watch the promotional video demonstrating the main features*

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technologies](#technologies)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Project Information](#project-information)
- [Contributors](#contributors)
- [License](#license)

## 🔍 Overview

SocialDistribution is a distributed social networking platform that implements an ActivityPub-like protocol, allowing users from different servers (nodes) to connect and interact with each other. The application provides a comprehensive social media experience with profiles, posts, comments, likes, and follow relationships, all while supporting cross-node federation.

### Key Highlights

- **Federated Architecture**: Connect and interact with users across multiple distributed nodes
- **RESTful API**: Comprehensive REST API with 60+ endpoints
- **Real-time Features**: Live notifications for follow requests and interactions
- **GitHub Integration**: Automatic post creation from GitHub public events
- **Privacy Controls**: Fine-grained visibility settings for posts (Public, Friends, Unlisted)

## ✨ Features

### Core Social Features

- **User Profiles**: Customizable profiles with display names, descriptions, profile images, and GitHub integration
- **Follow System**: Send follow requests, accept/reject requests, and manage followers
- **Friend System**: Automatic mutual following creates friendships for enhanced visibility
- **Posts & Entries**: Create, edit, and delete posts with multiple content types (plain text, markdown, images)
- **Comments**: Comment on posts with full CRUD operations
- **Likes**: Like posts and comments
- **Activity Feed**: Personalized stream showing posts from followed authors

### Advanced Features

- **Inbox System**: Receive and process remote activities (follow requests, posts, comments, likes) via ActivityPub-like protocol
- **Visibility Controls**: 
  - **Public**: Visible to everyone
  - **Friends Only**: Visible only to mutual friends
  - **Unlisted**: Visible to followers but not in public feeds
- **GitHub Integration**: Automatically create posts from GitHub public events (push events, pull requests, repository creation)
- **Real-time Notifications**: Live popup notifications for new follow requests
- **Soft Deletion**: Data retention for administrative purposes with soft-delete pattern
- **Remote Node Communication**: Connect with other nodes using HTTP Basic Auth
- **Profile Validation**: GitHub URL validation to ensure account authenticity

### User Experience

- **Responsive Design**: Mobile-friendly interface with Bootstrap 5
- **Smooth Animations**: Loading spinners, fade-in transitions, and staggered content reveals
- **AJAX Interactions**: Restful follow/unfollow operations without page refreshes
- **Real-time Updates**: Dynamic count updates after social interactions
- **Modern UI**: Clean, intuitive interface with smooth transitions and animations

## 🛠️ Technologies

### Backend

- **Django 5.2.4**: High-level Python web framework
- **Django REST Framework 3.16.0**: Powerful toolkit for building Web APIs
- **PostgreSQL** (via `psycopg2-binary`): Production-ready database
- **SQLite3**: Development database
- **Gunicorn**: WSGI HTTP server for production
- **WhiteNoise**: Static file serving for Django

### Frontend

- **Bootstrap 5.3.0**: Responsive CSS framework
- **JavaScript (ES6+)**: Modern JavaScript for dynamic interactions
- **AJAX**: Asynchronous requests for seamless user experience
- **Markdown**: Content rendering support

### Key Libraries

- **Requests**: HTTP library for remote node communication
- **Markdown**: Text-to-HTML conversion
- **Pillow**: Image processing
- **Django Extensions**: Extended functionality for Django

### Development & Deployment

- **Heroku**: Cloud platform for deployment
- **Git**: Version control
- **Django Admin**: Administrative interface

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- pip
- PostgreSQL (for production) or SQLite3 (for development)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Ahmed-S7/Social-Distribution.git
   cd Social-Distribution
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Main application: http://127.0.0.1:8000
   - Admin panel: http://127.0.0.1:8000/admin

### Running Tests

```bash
python manage.py test
```

For verbose output:
```bash
python manage.py test --verbosity=2
```

## 📚 API Documentation

Comprehensive API documentation is available in the [project Wiki](https://github.com/Ahmed-S7/Social-Distribution/wiki). The API includes:

- **Author Management**: CRUD operations for authors
- **Entry Management**: Create, read, update, delete posts
- **Social Interactions**: Follow, unfollow, friend operations
- **Comments & Likes**: Interact with content
- **Inbox API**: Receive remote activities
- **Follower/Following Lists**: Query social connections

See the [project description page](https://uofa-cmput404.github.io/general/project.html) for course project details.

## 👥 Contributors

### Authors

* **Ahmed Shittu** - *Lead Developer, Scrum Master, Project Manager*
* **Nina Han** - *Developer*
* **Luis Martinez** - *Developer*
* **Abdullah Faisal** - *Developer*
* **Maro Erivona** - *Developer*

> **Note**: One contributor has been removed as a contributor with their written consent. Their code remains cited where used.

### Active Contributors

**Ahmed Shittu** - Current maintainer and active contributor

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.md) file for license rights and limitations.



