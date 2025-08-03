from django.urls import path
from .views import app_name_view
from .UserManagement import  RegisterUser, UserInfo, TokenLogin
from .targetmanagement import TargetManagement
from .collector.start import StartInformationGatheringView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('', app_name_view, name='app_name'),
    path('target/', TargetManagement.as_view(), name='target_list_create'),
    path('target/<int:target_id>/', TargetManagement.as_view(), name='target_detail'),
    path('gather/', StartInformationGatheringView.as_view(), name='gather_information'),
    path('api/register/', RegisterUser.as_view(), name='register'),
    path('api/user/', UserInfo.as_view(), name='user_info'),
    path('api/login/', TokenLogin.as_view(), name='token_login'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 


]



