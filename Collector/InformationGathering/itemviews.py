from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from .models import items, Item


@method_decorator(csrf_exempt, name='dispatch')
class ItemViews(View):

    def get(self, request, *args, **kwargs):
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



    def post(self, request, *args, **kwargs):
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



    def put(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            item_id = data.get('id')
            new_name = data.get('name')

            if item_id is None or new_name is None:
                return JsonResponse({'error': 'ID and name are required'}, status=400)

            for item in items:
                if item.id == item_id:
                    item.name = new_name
                    return JsonResponse({'message': 'Item updated successfully', 'id': item_id, 'name': new_name}, status=200)

            return JsonResponse({'error': 'Item not found'}, status=404)
        except (ValueError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid request'}, status=400)



    def delete(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            item_id = data.get('id')

            if item_id is None:
                return JsonResponse({'error': 'ID parameter is required'}, status=400)

            for item in items:
                if item.id == item_id:
                    items.remove(item)
                    return JsonResponse({'message': f'Item {item_id} deleted successfully'}, status=200)

            return JsonResponse({'error': 'Item not found'}, status=404)
        except (ValueError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid request'}, status=400)
