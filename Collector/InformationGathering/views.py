from django.shortcuts import render
from django.http import JsonResponse
from .models import items 
from django.views.decorators.csrf import csrf_exempt
import json
from .models import items, Item 


def app_name_view(request):
    return JsonResponse({'app_name': 'InformationGathering'})



def get_item(request):
 
    item_id = request.GET.get('id')


    if item_id is not None:
        try:
            item_id = int(item_id) 
 
            item = next((item for item in items if item.id == item_id), None)

            if item:
                return JsonResponse({'id': item.id, 'name': item.name})
            else:
                return JsonResponse({'error': 'Item not found'}, status=404)
        except ValueError:
            return JsonResponse({'error': 'Invalid ID'}, status=400)
    else:
        return JsonResponse({'error': 'ID parameter is required'}, status=400)



@csrf_exempt 
def add_item(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('id')
            item_name = data.get('name')

            if item_id is not None and item_name is not None:
                new_item = Item(item_id, item_name)
                items.append(new_item)

                return JsonResponse({'message': 'Item added successfully', 'id': new_item.id, 'name': new_item.name}, status=201)
            else:
                return JsonResponse({'error': 'ID and name parameters are required'}, status=400)
        except (ValueError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid request'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)