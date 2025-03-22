from django.urls import path
from .views import app_name_view
from .itemviews import ItemViews

urlpatterns = [
    path('', app_name_view, name='app_name'),
    path('items/', ItemViews.as_view(), name='items'),
]

