from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from Scanning.models import MasscanScan, Target
import subprocess
import time
import json

@method_decorator(csrf_exempt, name='dispatch')
class StartScanningView(View):

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        target_id = data.get('target_id')
        ports = data.get('ports', '1-1000')
        rate = data.get('rate', 1000)

        target = get_object_or_404(Target, id=target_id)
        ip = target.host

        command = [
            'masscan',
            ip,
            '--ports', str(ports),
            '--rate', str(rate),
            '--output-format', 'json',
            '--output-filename', 'masscan_output.json'
        ]

        start_time = time.time()
        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
            duration = time.time() - start_time

            with open('masscan_output.json') as f:
                scan_results = json.load(f)

            open_ports = [entry['port'] for entry in scan_results if entry.get('port')]

            scan = MasscanScan.objects.create(
                target=target,
                ports_scanned=ports,
                rate=rate,
                raw_output=json.dumps(scan_results),
                open_ports=open_ports,
                duration=duration,
                status='Success'
            )

            return JsonResponse({'status': 'success', 'scan_id': scan.id, 'open_ports': open_ports})
        except subprocess.CalledProcessError as e:
            return JsonResponse({'status': 'error', 'message': e.stderr}, status=500)
