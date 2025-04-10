from django.http import JsonResponse
import logging
from django.views import View
from .whois import TargetWhoisDataCollector
from .ipinfo import IPInfoCollector
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt




logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class StartInformationGatheringView(View):
    async def get(self, request):
        target_id = request.GET.get('id')
        if not target_id:
            return JsonResponse({'status': 'error', 'message': 'Target ID is required'}, status=400)
        
        results = await self.gather_all_information(target_id)
        return JsonResponse(results)
    
    async def gather_all_information(self, target_id):
        try:
            WhoisCollector = TargetWhoisDataCollector(target_id)
            ipinfocollector = IPInfoCollector(target_id)

            whois_result, ipinfo_result = await WhoisCollector.run(), await ipinfocollector.run()
            
            return {
                'status': 'success',
                'whois': 'collected' if whois_result else 'failed',
                'ip_info': 'collected' if ipinfo_result else 'failed',
            }
        
        except Exception as e:
            logger.error(f"Error gathering information: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'An error occurred while gathering information'}
