from django.urls import path
from .views import *

app_name = "profil"

urlpatterns = [
    path('me', ProfileAPIView.as_view(), name='profile-me'),
]