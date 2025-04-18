from django.http import JsonResponse
import logging
from django.views import View
from .whois import TargetWhoisDataCollector
from .ipinfo import IPInfoCollector

logger = logging.getLogger(__name__)

class StartInformationGatheringView(View):
    async def get(self, request):
        target_id = request.GET.get('id')
        if not target_id:
            return JsonResponse({'status': 'error', 'message': 'Target ID is required'}, status=400)

        try:
            results = await self.gather_all_information(target_id)
            return JsonResponse(results)
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return JsonResponse({'status': 'error', 'message': 'Internal server error'}, status=500)

    async def gather_all_information(self, target_id):
        WhoisCollector = TargetWhoisDataCollector(target_id)
        whois_result = await WhoisCollector.run()

        ipinfo_result = IPInfoCollector(target_id)
        await ipinfo_result.run() 

        return {
            'status': 'success',
            'whois': 'collected' if whois_result else 'failed',
            'ip_info': 'collected' if ipinfo_result else 'failed',
        }
