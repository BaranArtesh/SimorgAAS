from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from .models import User

@method_decorator(csrf_exempt, name='dispatch')
class UserManagement(View):

    def get(self, request, *args, **kwargs):
        username = request.GET.get('username')

        if username:
            user = User.objects.filter(username=username).first()

            if user:
                return JsonResponse({'username': user.username, 'email': user.email, 'is_admin': user.is_admin})
            else:
                return JsonResponse({'error': 'User not found'}, status=404)
        else:
            return JsonResponse({'error': 'Username parameter is required'}, status=400)

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            is_admin = data.get('is_admin')

            if not username or not email or not password:
                return JsonResponse({'error': 'Username, email, and password are required'}, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({'error': 'Username already exists'}, status=400)

            if User.objects.filter(email=email).exists():
                return JsonResponse({'error': 'Email already exists'}, status=400)

            user = User.objects.create(username=username, email=email, password=password, is_admin=is_admin)
            return JsonResponse({'message': 'User created successfully', 'id': user.id}, status=201)

        except (ValueError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid request'}, status=400)
        

    def put(self, request, *args, **kwargs):
        try:
        # Load request data
           data = json.loads(request.body)
           user_id = data.get('id')
           new_email = data.get('email')
           new_password = data.get('password')
           new_is_admin = data.get('is_admin')

        # Validate user ID
           if not user_id:
               return JsonResponse({'error': 'User ID is required'}, status=400)

        # Fetch user from database
           user = User.objects.filter(id=user_id).first()
           if not user:
                return JsonResponse({'error': 'User not found'}, status=404)

        # Update email if provided
           if new_email:
             if User.objects.exclude(id=user_id).filter(email=new_email).exists():
                 return JsonResponse({'error': 'Email already taken'}, status=400)
             user.email = new_email

        # Update password if provided
           if new_password:
                user.password = new_password

        # Update admin status if provided
           if new_is_admin is not None:
              user.is_admin = bool(new_is_admin)

        # Save updates
           user.save()
           return JsonResponse({'message': 'User updated successfully'}, status=200)

        except (ValueError, json.JSONDecodeError):
           return JsonResponse({'error': 'Invalid request'}, status=400)


    def delete(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            user_id = data.get('id')

            if not user_id:
                return JsonResponse({'error': 'User ID is required'}, status=400)

            user = User.objects.filter(id=user_id).first()

            if not user:
                return JsonResponse({'error': 'User not found'}, status=404)

            user.delete()
            return JsonResponse({'message': f'User {user_id} deleted successfully'}, status=200)

        except (ValueError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid request'}, status=400)

    def check_user(self, request, *args, **kwargs):
        """ التحقق من صحة اسم المستخدم وكلمة المرور """
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return JsonResponse({'error': 'Username and password are required'}, status=400)

            user = User.objects.filter(username=username, password=password).first()

            if user:
                return JsonResponse({'message': 'Authentication successful', 'username': user.username, 'is_admin': user.is_admin}, status=200)
            else:
                return JsonResponse({'error': 'Invalid credentials'}, status=401)

        except (ValueError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid request'}, status=400)
