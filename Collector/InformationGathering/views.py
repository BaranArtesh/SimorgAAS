from django.http import JsonResponse
# from .models import User
from django.views import View
from .targetmanagement import TargetManagement

def app_name_view(request):
    return JsonResponse({'app_name': 'InformationGathering'})