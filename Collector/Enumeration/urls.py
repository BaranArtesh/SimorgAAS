from django.urls import path
from .views import app_name_view

urlpatterns = [
    path('', app_name_view, name='app_name'),
]
