from django.http import JsonResponse
import logging
from django.views import View
from .whois import TargetWhoisDataCollector

logger = logging.getLogger(__name__)

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
            
            result = await WhoisCollector.run()
            return result
        except Exception as e:
            logger.error(f"Error gathering information: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'An error occurred while gathering information'}
