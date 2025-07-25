from django.urls import path
from .views import StartEnumerationAPI

urlpatterns = [
    path('api/enum/start/<int:target_id>/', StartEnumerationAPI.as_view(), name='api_start_enumeration'),
]
