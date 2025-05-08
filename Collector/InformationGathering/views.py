from django.http import JsonResponse
from .models import User
from django.views import View
from .targetmanagement import TargetManagement
from django.views.decorators.csrf import csrf_exempt



@csrf_exempt
def app_name_view(request):
        return JsonResponse({'app_name': 'InformationGathering'})


