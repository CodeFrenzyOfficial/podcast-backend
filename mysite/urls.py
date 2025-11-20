"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from mysite.views.podcasts.views import PodcastView
from mysite.views.BlogSlug.views import BlogSlugView
from mysite.views.blogs.views import BlogView
from mysite.views.users.views import UsersView
from mysite.views.contacts.views import ContactsView
from mysite.views.auth.views import RegisterView, LoginView, LogoutView, CurrentUserView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/current/<str:user_id>/', CurrentUserView.as_view(), name='current'),

    path('blog/', BlogView.as_view(), name='blog'),
    path('blog/<str:user_id>/', BlogView.as_view(), name='blog'),
    path('blog/<str:user_id>/<str:blog_id>/', BlogView.as_view(), name='blog'),

    # Blog by Slug
    path('blog/slug/<str:slug>/', BlogSlugView.as_view(), name='blog-slug'),
    
    path('podcast/', PodcastView.as_view(), name='podcast'),
    path('podcast/<str:user_id>/', PodcastView.as_view(), name='podcast'),
    path('podcast/category/<str:category>/', PodcastView.as_view(), name='podcast'),
    path('podcast/<str:user_id>/<str:podcast_id>/', PodcastView.as_view(), name='podcast'),
    
    path('users/', UsersView.as_view(), name='users'),
    path('users/<str:user_id>/', UsersView.as_view(), name='users'),
    
    path('contacts/', ContactsView.as_view(), name='contacts'),
]


# rules_version = '2';

# // Craft rules based on data in your Firestore database
# // allow write: if firestore.get(
# //    /databases/(default)/documents/users/$(request.auth.uid)).data.isAdmin;
# // service firebase.storage {
# //   match /b/{bucket}/o {
# //     match /{allPaths=**} {
# //       // allow read, write: if false;
# //       allow read, write: if request.resource.size < 50 * 1024 * 1024 * 1024;
# //     }
# //   }
# // }