from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from Scanning.collector.MasscanRescanOpenPorts import MasscanRescanOpenPorts
import json

@method_decorator(csrf_exempt, name='dispatch')
class ReScanOpenPortsView(View):
    async def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            target_id = data.get("target_id")
            if not target_id:
                return JsonResponse({"status": "error", "message": "target_id is required"}, status=400)

            service = MasscanRescanOpenPorts(target_id)
            result = await service.scan_open_ports()
            return JsonResponse(result)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
