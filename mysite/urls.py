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
from mysite.views.blogs.views import BlogView
from mysite.views.users.views import UsersView
from mysite.views.contacts.views import ContactsView
from mysite.views.auth.views import RegisterView, LoginView, LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    path('blog/', BlogView.as_view(), name='blog'),
    path('blog/<str:user_id>/', BlogView.as_view(), name='blog'),
    path('blog/<str:user_id>/<str:blog_id>/', BlogView.as_view(), name='blog'),
    
    path('podcast/', PodcastView.as_view(), name='podcast'),
    path('podcast/<str:user_id>/', PodcastView.as_view(), name='podcast'),
    path('podcast/<str:user_id>/<str:podcast_id>/', PodcastView.as_view(), name='podcast'),
    
    path('users/', UsersView.as_view(), name='users'),
    path('users/<str:user_id>/', UsersView.as_view(), name='users'),
    
    path('contacts/', ContactsView.as_view(), name='contacts'),
]
