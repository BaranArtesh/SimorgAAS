from django.http import JsonResponse
from .models import User
from django.views import View
from .UserManagement import UserManagement

def app_name_view(request):
    return JsonResponse({'app_name': 'InformationGathering'})
