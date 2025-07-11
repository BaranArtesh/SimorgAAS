from django.urls import path
from .views import app_name_view
from .targetmanagement import TargetManagement
from .UserManagement import UserManagement
from .collector.start import StartInformationGatheringView

urlpatterns = [
    path('', app_name_view, name='app_name'),
    path('target/', TargetManagement.as_view(), name='target_management'),
    path('users/', UserManagement.as_view(), name='user_management'),
    path('gather/', StartInformationGatheringView.as_view(), name='gather_information'),

]



