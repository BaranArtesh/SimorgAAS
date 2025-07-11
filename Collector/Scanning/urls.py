from django.urls import path
from .views import  ReScanOpenPortsView
from InformationGathering.targetmanagement import TargetManagement  # إذا تستخدمه في مشروعك

app_name = "Scanning"

urlpatterns = [
    path('target/', TargetManagement.as_view(), name='TargetManagement'),
    path('target/<int:target_id>/', TargetManagement.as_view(), name='TargetManagement'),
    path('scan/masscan/', ReScanOpenPortsView.as_view(), name='masscan_scan'),
]
