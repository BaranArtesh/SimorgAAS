from django.urls import path
from .views import app_name_view
from .targetmanagement import TargetManagement

urlpatterns = [
    path('', app_name_view, name='app_name'),
    path('target/', TargetManagement.as_view(), name='target_management'),
]
