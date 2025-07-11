from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from .models import Target
import json

# @method_decorator(csrf_exempt, name='dispatch')
# class TargetManagement(View):
    
#     def get(self, request, target_id=None):
#         if target_id:
#             target = get_object_or_404(Target, id=target_id)
#             data = {
#                 "id": target.id,
#                 "name": target.name,
#                 "host": target.host,
#                 "type": target.type,
#                 "is_local": target.is_local,
#                 "status": target.status,
#                 "created_at": target.created_at.strftime('%Y-%m-%d %H:%M:%S'),
#             }
#             return JsonResponse({"status": "success", "target": data})

#         targets = Target.objects.all()
#         data = [
#             {
#                 "id": target.id,
#                 "name": target.name,
#                 "host": target.host,
#                 "type": target.type,
#                 "is_local": target.is_local,
#                 "status": target.status,
#                 "created_at": target.created_at.strftime('%Y-%m-%d %H:%M:%S'),
#             }
#             for target in targets
#         ]
#         return JsonResponse({"status": "success", "targets": data})
    
#     def post(self, request, *args, **kwargs):
#         try:
#             data = json.loads(request.body)
#             name = data.get('name')
#             host = data.get('host')
#             target_type = data.get('type')
#             is_local = data.get('is_local', False)
#             status = data.get('status')

#             if not all([name, host, target_type, status]):
#                 return JsonResponse({'error': 'Name, host, type, and status are required'}, status=400)

#             if Target.objects.filter(name=name).exists():
#                 return JsonResponse({'error': 'Target name already exists'}, status=400)

#             target = Target.objects.create(name=name, host=host, type=target_type, is_local=is_local, status=status)
#             return JsonResponse({'message': 'Target created successfully', 'id': target.id}, status=201)
        
#         except (ValueError, json.JSONDecodeError):
#             return JsonResponse({'error': 'Invalid JSON request'}, status=400)
    
#     def put(self, request, *args, **kwargs):
#         try:
#             data = json.loads(request.body)
#             target_id = data.get('id')

#             if not target_id:
#                 return JsonResponse({'error': 'Target ID is required'}, status=400)

#             target = Target.objects.filter(id=target_id).first()
#             if not target:
#                 return JsonResponse({'error': 'Target not found'}, status=404)

#             target.name = data.get('name', target.name)
#             target.host = data.get('host', target.host)
#             target.type = data.get('type', target.type)
#             target.is_local = data.get('is_local', target.is_local)
#             target.status = data.get('status', target.status)

#             target.save()
#             return JsonResponse({'message': 'Target updated successfully'}, status=200)
        
#         except (ValueError, json.JSONDecodeError):
#             return JsonResponse({'error': 'Invalid JSON request'}, status=400)
    
#     def delete(self, request, *args, **kwargs):
#         try:
#             data = json.loads(request.body)
#             target_id = data.get('id')

#             if not target_id:
#                 return JsonResponse({'error': 'Target ID is required'}, status=400)

#             target = Target.objects.filter(id=target_id).first()
#             if not target:
#                 return JsonResponse({'error': 'Target not found'}, status=404)

#             target.delete()
#             return JsonResponse({'message': f'Target {target_id} deleted successfully'}, status=200)
        
#         except (ValueError, json.JSONDecodeError):
#             return JsonResponse({'error': 'Invalid JSON request'}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class TargetManagement(View):
    
    def get(self, request, target_id=None):
        if target_id:
            target = get_object_or_404(Target, id=target_id)
            data = {
                "id": target.id,
                "name": target.name,
                "host": target.host,
                "type": target.type,
                "is_local": target.is_local,
                "status": target.status,
                "created_at": target.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
            return JsonResponse({"status": "success", "target": data})

        targets = Target.objects.all()
        data = [
            {
                "id": target.id,
                "name": target.name,
                "host": target.host,
                "type": target.type,
                "is_local": target.is_local,
                "status": target.status,
                "created_at": target.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
            for target in targets
        ]
        return JsonResponse({"status": "success", "targets": data})
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            name = data.get('name')
            host = data.get('host')
            target_type = data.get('type')
            is_local = data.get('is_local', False)
            status = data.get('status')

            if not all([name, host, target_type, status]):
                return JsonResponse({'error': 'Name, host, type, and status are required'}, status=400)

            if Target.objects.filter(name=name).exists():
                return JsonResponse({'error': 'Target name already exists'}, status=400)

            target = Target.objects.create(name=name, host=host, type=target_type, is_local=is_local, status=status)
            return JsonResponse({'message': 'Target created successfully', 'id': target.id}, status=201)
        
        except (ValueError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid JSON request'}, status=400)
    
    def put(self, request, target_id=None, *args, **kwargs):
        if not target_id:
            return JsonResponse({'error': 'Target ID is required'}, status=400)
        try:
            data = json.loads(request.body)
            target = Target.objects.filter(id=target_id).first()
            if not target:
                return JsonResponse({'error': 'Target not found'}, status=404)

            target.name = data.get('name', target.name)
            target.host = data.get('host', target.host)
            target.type = data.get('type', target.type)
            target.is_local = data.get('is_local', target.is_local)
            target.status = data.get('status', target.status)

            target.save()
            return JsonResponse({'message': 'Target updated successfully'}, status=200)
        
        except (ValueError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid JSON request'}, status=400)
    
    def delete(self, request, target_id=None, *args, **kwargs):
        if not target_id:
            return JsonResponse({'error': 'Target ID is required'}, status=400)
        target = Target.objects.filter(id=target_id).first()
        if not target:
            return JsonResponse({'error': 'Target not found'}, status=404)
        target.delete()
        return JsonResponse({'message': f'Target {target_id} deleted successfully'}, status=200)
