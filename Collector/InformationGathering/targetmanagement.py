from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Target
from .serializers import TargetSerializer

class TargetManagement(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, target_id=None):
        if target_id:
            target = get_object_or_404(Target, id=target_id, owner=request.user)
            return Response(TargetSerializer(target).data)
        targets = Target.objects.filter(owner=request.user)
        return Response(TargetSerializer(targets, many=True).data)

    def post(self, request):
        serializer = TargetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response({'message': 'Target created', 'id': serializer.data['id']}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, target_id=None):
        target = get_object_or_404(Target, id=target_id, owner=request.user)
        serializer = TargetSerializer(target, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Target updated'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, target_id=None):
        target = get_object_or_404(Target, id=target_id, owner=request.user)
        target.delete()
        return Response({'message': f'Target {target_id} deleted'})
