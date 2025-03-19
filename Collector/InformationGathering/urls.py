from django.urls import path
from .views import app_name_view
from .views import get_item, add_item

urlpatterns = [
    path('', app_name_view, name='app_name'),
    path('get-item/', get_item, name='get_item'),
    path('add-item/', add_item, name='add_item'),
]
