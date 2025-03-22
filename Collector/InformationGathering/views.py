from django.http import JsonResponse
from .models import items, Item
from .itemviews import ItemViews

def app_name_view(request):
    return JsonResponse({'app_name': 'InformationGathering'})

    