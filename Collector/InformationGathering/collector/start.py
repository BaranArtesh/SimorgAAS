# from django.http import JsonResponse
# import logging
# from django.views import View
# from .whois import TargetWhoisDataCollector
# from .ipinfo import IPInfoCollector
# from .nmap import NmapCollector
# from .shodan import ShodanCollector
# from .censys import CensysCollector
# from django.utils.decorators import method_decorator
# from django.views.decorators.csrf import csrf_exempt

# logger = logging.getLogger(__name__)

# @method_decorator(csrf_exempt, name='dispatch')
# class StartInformationGatheringView(View):
#     async def get(self, request):
#         target_id = request.GET.get('id')
#         if not target_id:
#             return JsonResponse({'status': 'error', 'message': 'Target ID is required'}, status=400)

#         try:
#             results = await self.gather_all_information(target_id)
#             return JsonResponse(results)
#         except Exception as e:
#             logger.error(f"Unexpected error: {e}", exc_info=True)
#             return JsonResponse({'status': 'error', 'message': 'Internal server error'}, status=500)

#     async def gather_all_information(self, target_id):
      
#         whois_ok = await self.collect_whois_info(target_id)

   
#         ipinfo_ok = await self.collect_ip_info(target_id)

    
#         nmap_ok = await self.run_nmap_scan(target_id)

    
#         shodan_ok = await self.collect_shodan_info(target_id)

        
#         censys_ok = await self.collect_censys_info(target_id)

#         return {
#             'status': 'success',
#             'whois': 'collected' if whois_ok else 'failed',
#             'ip_info': 'collected' if ipinfo_ok else 'failed',
#             'nmap': 'scanned' if nmap_ok else 'failed',
#             'shodan': 'collected' if shodan_ok else 'failed',
#             'censys': 'collected' if censys_ok else 'failed',
#         }

#     async def collect_whois_info(self, target_id):
#         try:
#             whois_collector = TargetWhoisDataCollector(target_id)
#             result = await whois_collector.run()
#             if result.get('status') == 'success':
#                 logger.info(f"WHOIS data collected for target {target_id}")
#                 return True
#         except Exception as e:
#             logger.error(f"Error collecting WHOIS data for target {target_id}: {e}", exc_info=True)
#         return False

#     async def collect_ip_info(self, target_id):
#         try:
#             ipinfo_collector = IPInfoCollector(target_id)
#             result = await ipinfo_collector.run()
#             if result.get('status') == 'success':
#                 logger.info(f"IP info collected for target {target_id}")
#                 return True
#         except Exception as e:
#             logger.error(f"Error collecting IP info for target {target_id}: {e}", exc_info=True)
#         return False

#     async def run_nmap_scan(self, target_id):
#         try:
#             nmap_collector = NmapCollector(target_id)
#             result = await nmap_collector.run()
#             if result.get('status') == 'success':
#                 logger.info(f"Nmap scan completed for target {target_id}")
#                 return True
#             logger.warning(f"Nmap scan failed for target {target_id}: {result.get('message')}")
#         except Exception as e:
#             logger.error(f"Error running Nmap scan for target {target_id}: {e}", exc_info=True)
#         return False

#     async def collect_shodan_info(self, target_id):
#         try:
#             shodan_collector = ShodanCollector(target_id)
#             result = await shodan_collector.run()
#             if result.get('status') == 'success':
#                 logger.info(f"Shodan data collected for target {target_id}")
#                 return True
#             logger.warning(f"Shodan collection failed for target {target_id}: {result.get('message')}")
#         except Exception as e:
#             logger.error(f"Error collecting Shodan data for target {target_id}: {e}", exc_info=True)
#         return False

#     async def collect_censys_info(self, target_id):
#         try:
#             censys_collector = CensysCollector(target_id)
#             result = await censys_collector.run()
#             if result.get('status') == 'success':
#                 logger.info(f"Censys data collected for target {target_id}")
#                 return True
#             logger.warning(f"Censys collection failed for target {target_id}: {result.get('message')}")
#         except Exception as e:
#             logger.error(f"Error collecting Censys data for target {target_id}: {e}", exc_info=True)
#         return False



# from django.http import JsonResponse
# import logging
# from django.views import View
# from .whois import TargetWhoisDataCollector
# from .ipinfo import IPInfoCollector
# from .nmap import NmapCollector
# from .shodan import ShodanCollector
# from .censys import CensysCollector
# # from .zmap import ZMapCollector  # ⬅️ New import
# from django.utils.decorators import method_decorator
# from django.views.decorators.csrf import csrf_exempt
# # from .sonarproject import ProjectSonarCollector


# logger = logging.getLogger(__name__)

# @method_decorator(csrf_exempt, name='dispatch')
# class StartInformationGatheringView(View):
#     async def get(self, request):
#         target_id = request.GET.get('id')
#         if not target_id:
#             return JsonResponse({'status': 'error', 'message': 'Target ID is required'}, status=400)

#         try:
#             results = await self.gather_all_information(target_id)
#             return JsonResponse(results)
#         except Exception as e:
#             logger.error(f"Unexpected error: {e}", exc_info=True)
#             return JsonResponse({'status': 'error', 'message': 'Internal server error'}, status=500)

#     async def gather_all_information(self, target_id):
#         whois_ok = await self.collect_whois_info(target_id)
#         ipinfo_ok = await self.collect_ip_info(target_id)
#         nmap_ok = await self.run_nmap_scan(target_id)
#         shodan_ok = await self.collect_shodan_info(target_id)
#         censys_ok = await self.collect_censys_info(target_id)
#         # zmap_ok = await self.run_zmap_scan(target_id)  # ⬅️ New Zmap task
#         # sonar_ok = await self.collect_sonar_info(target_id)



#         return {
#             'status': 'success',
#             'whois': 'collected' if whois_ok else 'failed',
#             'ip_info': 'collected' if ipinfo_ok else 'failed',
#             'nmap': 'scanned' if nmap_ok else 'failed',
#             # 'zmap': 'scanned' if zmap_ok else 'failed',  # ⬅️ New Zmap status
#             'shodan': 'collected' if shodan_ok else 'failed',
#             'censys': 'collected' if censys_ok else 'failed',
#             # 'sonar': 'collected' if sonar_ok else 'failed',
#         }

#     async def collect_whois_info(self, target_id):
#         try:
#             whois_collector = TargetWhoisDataCollector(target_id)
#             result = await whois_collector.run()
#             if result.get('status') == 'success':
#                 logger.info(f"WHOIS data collected for target {target_id}")
#                 return True
#         except Exception as e:
#             logger.error(f"Error collecting WHOIS data for target {target_id}: {e}", exc_info=True)
#         return False

#     async def collect_ip_info(self, target_id):
#         try:
#             ipinfo_collector = IPInfoCollector(target_id)
#             result = await ipinfo_collector.run()
#             if result.get('status') == 'success':
#                 logger.info(f"IP info collected for target {target_id}")
#                 return True
#         except Exception as e:
#             logger.error(f"Error collecting IP info for target {target_id}: {e}", exc_info=True)
#         return False

#     async def run_nmap_scan(self, target_id):
#         try:
#             nmap_collector = NmapCollector(target_id)
#             result = await nmap_collector.run()
#             if result.get('status') == 'success':
#                 logger.info(f"Nmap scan completed for target {target_id}")
#                 return True
#             logger.warning(f"Nmap scan failed for target {target_id}: {result.get('message')}")
#         except Exception as e:
#             logger.error(f"Error running Nmap scan for target {target_id}: {e}", exc_info=True)
#         return False

#     # async def run_zmap_scan(self, target_id):  # ⬅️ New Zmap method
#     #     try:
#     #         zmap_collector = ZMapCollector(target_id)
#     #         result = await zmap_collector.run()
#     #         if result.get('status') == 'success':
#     #             logger.info(f"Zmap scan completed for target {target_id}")
#     #             return True
#     #         logger.warning(f"Zmap scan failed for target {target_id}: {result.get('message')}")
#     #     except Exception as e:
#     #         logger.error(f"Error running Zmap scan for target {target_id}: {e}", exc_info=True)
#     #     return False

#     async def collect_shodan_info(self, target_id):
#         try:
#             shodan_collector = ShodanCollector(target_id)
#             result = await shodan_collector.run()
#             if result.get('status') == 'success':
#                 logger.info(f"Shodan data collected for target {target_id}")
#                 return True
#             logger.warning(f"Shodan collection failed for target {target_id}: {result.get('message')}")
#         except Exception as e:
#             logger.error(f"Error collecting Shodan data for target {target_id}: {e}", exc_info=True)
#         return False

#     async def collect_censys_info(self, target_id):
#         try:
#             censys_collector = CensysCollector(target_id)
#             result = await censys_collector.run()
#             if result.get('status') == 'success':
#                 logger.info(f"Censys data collected for target {target_id}")
#                 return True
#             logger.warning(f"Censys collection failed for target {target_id}: {result.get('message')}")
#         except Exception as e:
#             logger.error(f"Error collecting Censys data for target {target_id}: {e}", exc_info=True)
#         return False


#     # async def collect_sonar_info(self, target_id):
#     #     try:
#     #         from .sonarproject import ProjectSonarCollector
#     #         sonar_collector = ProjectSonarCollector(target_id)
#     #         result = await sonar_collector.run()
#     #         if result.get('status') == 'success':
#     #             logger.info(f"Project Sonar data collected for target {target_id}")
#     #             return True
#     #         logger.warning(f"Project Sonar collection failed for target {target_id}: {result.get('message')}")
#     #     except Exception as e:
#     #         logger.error(f"Error collecting Project Sonar data for target {target_id}: {e}", exc_info=True)
#     #     return False


from django.http import JsonResponse
import logging
from django.views import View
from .whois import TargetWhoisDataCollector
from .ipinfo import IPInfoCollector
from .nmap import NmapCollector
from .shodan import ShodanCollector
from .censys import CensysCollector
from .zoomeye import ZoomEyeCollector  # ✅ New import
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
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
        whois_ok = await self.collect_whois_info(target_id)
        ipinfo_ok = await self.collect_ip_info(target_id)
        nmap_ok = await self.run_nmap_scan(target_id)
        shodan_ok = await self.collect_shodan_info(target_id)
        censys_ok = await self.collect_censys_info(target_id)
        zoomeye_ok = await self.collect_zoomeye_info(target_id)  # ✅ New ZoomEye step

        return {
            'status': 'success',
            'whois': 'collected' if whois_ok else 'failed',
            'ip_info': 'collected' if ipinfo_ok else 'failed',
            'nmap': 'scanned' if nmap_ok else 'failed',
            'shodan': 'collected' if shodan_ok else 'failed',
            'censys': 'collected' if censys_ok else 'failed',
            'zoomeye': 'collected' if zoomeye_ok else 'failed',  # ✅ New ZoomEye status
        }

    async def collect_whois_info(self, target_id):
        try:
            whois_collector = TargetWhoisDataCollector(target_id)
            result = await whois_collector.run()
            if result.get('status') == 'success':
                logger.info(f"WHOIS data collected for target {target_id}")
                return True
        except Exception as e:
            logger.error(f"Error collecting WHOIS data for target {target_id}: {e}", exc_info=True)
        return False

    async def collect_ip_info(self, target_id):
        try:
            ipinfo_collector = IPInfoCollector(target_id)
            result = await ipinfo_collector.run()
            if result.get('status') == 'success':
                logger.info(f"IP info collected for target {target_id}")
                return True
        except Exception as e:
            logger.error(f"Error collecting IP info for target {target_id}: {e}", exc_info=True)
        return False

    async def run_nmap_scan(self, target_id):
        try:
            nmap_collector = NmapCollector(target_id)
            result = await nmap_collector.run()
            if result.get('status') == 'success':
                logger.info(f"Nmap scan completed for target {target_id}")
                return True
            logger.warning(f"Nmap scan failed for target {target_id}: {result.get('message')}")
        except Exception as e:
            logger.error(f"Error running Nmap scan for target {target_id}: {e}", exc_info=True)
        return False

    async def collect_shodan_info(self, target_id):
        try:
            shodan_collector = ShodanCollector(target_id)
            result = await shodan_collector.run()
            if result.get('status') == 'success':
                logger.info(f"Shodan data collected for target {target_id}")
                return True
            logger.warning(f"Shodan collection failed for target {target_id}: {result.get('message')}")
        except Exception as e:
            logger.error(f"Error collecting Shodan data for target {target_id}: {e}", exc_info=True)
        return False

    async def collect_censys_info(self, target_id):
        try:
            censys_collector = CensysCollector(target_id)
            result = await censys_collector.run()
            if result.get('status') == 'success':
                logger.info(f"Censys data collected for target {target_id}")
                return True
            logger.warning(f"Censys collection failed for target {target_id}: {result.get('message')}")
        except Exception as e:
            logger.error(f"Error collecting Censys data for target {target_id}: {e}", exc_info=True)
        return False

    async def collect_zoomeye_info(self, target_id):  # ✅ New method
        try:
            zoomeye_collector = ZoomEyeCollector(target_id)
            result = await zoomeye_collector.run()
            if result.get('status') == 'success':
                logger.info(f"ZoomEye data collected for target {target_id}")
                return True
            logger.warning(f"ZoomEye collection failed for target {target_id}: {result.get('message')}")
        except Exception as e:
            logger.error(f"Error collecting ZoomEye data for target {target_id}: {e}", exc_info=True)
        return False
