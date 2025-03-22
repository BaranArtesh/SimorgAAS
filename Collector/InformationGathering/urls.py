from django.urls import path
from .views import app_name_view
from .UserManagement import UserManagement

urlpatterns = [
    path('', app_name_view, name='app_name'),
    path('users/', UserManagement.as_view(), name='user_management')
]
