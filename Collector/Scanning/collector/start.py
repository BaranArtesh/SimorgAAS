from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from Scanning.models import Target
from ..models import ScanResult
from .nampcollector import AdvancedNmapCollector
import subprocess
import asyncio
import time
import json

@method_decorator(csrf_exempt, name='dispatch')
class AdvancedScanView(View):

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            target_id = data.get('target_id')
            ports = data.get('ports', '1-1000')
            rate = data.get('rate', 1000)

            if not target_id:
                return JsonResponse({'status': 'error', 'message': 'target_id is required'}, status=400)

            target = get_object_or_404(Target, id=target_id)
            ip = target.host

            # ✅ Masscan command
            command = [
                'masscan',
                ip,
                '--ports', str(ports),
                '--rate', str(rate),
                '--output-format', 'json',
                '--output-filename', 'masscan_output.json'
            ]

            # ✅ Run Masscan
            start_time = time.time()
            subprocess.run(command, capture_output=True, text=True, check=True)
            duration = time.time() - start_time

            # ✅ Read Masscan Results
            with open('masscan_output.json') as f:
                scan_results = json.load(f)

            open_ports = [entry['port'] for entry in scan_results if entry.get('port')]

            # ✅ Save Masscan Scan
            scan = ScanResult.objects.create(
                target=target,
                raw_output=json.dumps(scan_results),
                open_ports=open_ports,
                duration=duration,
                status='Success'
            )

            # ✅ Run Nmap Collector
            async def run_nmap():
                collector = AdvancedNmapCollector(target_id=target.id)
                return await collector.run()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            nmap_result = loop.run_until_complete(run_nmap())
            loop.close()

            return JsonResponse({
                'status': 'success',
                'target': target_id,
                'masscan_scan_id': scan.id,
                'open_ports': open_ports,
                'nmap_result': nmap_result,
            })

        except subprocess.CalledProcessError as e:
            return JsonResponse({'status': 'error', 'message': e.stderr}, status=500)
        except Exception as ex:
            return JsonResponse({'status': 'error', 'message': str(ex)}, status=500)
