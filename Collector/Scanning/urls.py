from django.urls import path
from .views import  ReScanOpenPortsView
from InformationGathering.targetmanagement import TargetManagement  # إذا تستخدمه في مشروعك
from .collector.start import AdvancedScanView

app_name = "Scanning"

urlpatterns = [
    path('target/', TargetManagement.as_view(), name='TargetManagement'),
    path('target/<int:target_id>/', TargetManagement.as_view(), name='TargetManagement'),
    path('advanced/', AdvancedScanView.as_view(), name='advanced'),
]
