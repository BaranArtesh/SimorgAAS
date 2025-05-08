import nmap
import logging
import json
from asgiref.sync import sync_to_async
from django.conf import settings
from django.shortcuts import get_object_or_404
from InformationGathering.models import Target, NmapScan
from django.utils.dateparse import parse_date
from django.utils.timezone import now


logger = logging.getLogger(__name__)

class NmapCollector:
    def __init__(self, target_id):
        self.target_id = target_id
        self.target = None
        self.nmap_scanner = nmap.PortScanner()

    async def _get_target(self):
        """ Get the target object asynchronously """
        if not self.target:
            self.target = await sync_to_async(get_object_or_404)(Target, id=self.target_id)
        return self.target

    async def scan_target(self, ip_address):
        """ Run the Nmap scan using nmap module """
        try:
            logger.info(f"Starting Nmap scan on {ip_address}")
            self.nmap_scanner.scan(ip_address, '1-1024', '-sS -T4 -O')
            return self.nmap_scanner[ip_address]
        except Exception as e:
            logger.error(f"Error during Nmap scan on {ip_address}: {str(e)}")
            return None

    async def collect_nmap_info(self, ip_address):
        """ Collect scan data directly from the scan_target method """
        try:
            scan_data = await self.scan_target(ip_address)
            if scan_data:
                return scan_data
        except Exception as e:
            logger.error(f"Error collecting Nmap information for {ip_address}: {str(e)}")
        return None

    async def save_nmap_info(self, scan_data):
        """ Parse and save Nmap scan results """
        try:
            open_ports = []
            for proto in scan_data.all_protocols():
                ports = scan_data[proto].keys()
                for port in ports:
                    if scan_data[proto][port]['state'] == 'open':
                        open_ports.append({
                            'port': port,
                            'protocol': proto,
                            'service': scan_data[proto][port].get('name')
                        })

            os_info = scan_data.get('osmatch', [{}])[0] if 'osmatch' in scan_data else {}
            os_name = os_info.get('name')
            os_accuracy = int(os_info.get('accuracy', 0))
            os_method = scan_data.get('osclass', [{}])[0].get('osfamily') if 'osclass' in scan_data else None

            await sync_to_async(NmapScan.objects.create)(
                target_id=self.target_id,
                scan_type='TCP',
                status='Success',
                scan_output=json.dumps(scan_data),
                scan_duration=scan_data.get('duration', 0),
                scan_flags={'flags': '-sS -T4 -O'},
                open_ports=open_ports,
                results=scan_data,
                host_os=os_name,
                os_detection_method=os_method,
                os_accuracy=os_accuracy,
                is_vpn=False
            
            )

            logger.info(f"Nmap scan results saved for target {self.target_id}")
            print("\n✅ [Nmap Saved Data]")
            print(f"Target ID      : {self.target_id}")
            print(f"Host OS        : {os_name}")
            print(f"OS Accuracy    : {os_accuracy}%")
            print(f"Open Ports     : {json.dumps(open_ports, indent=2)}")
            print(f"Scan Flags     : -sS -T4 -O")
            print(f"Scan Duration  : {scan_data.get('duration', 0)} sec\n")


            logger.info(f"Nmap scan results saved for target {self.target_id}")
        except Exception as e:
            logger.error(f"Error saving Nmap scan data: {str(e)}")


    async def run(self):
        """ Main method to run scan and save data """
        try:
            target = await self._get_target()
            ip_address = target.host
            scan_data = await self.collect_nmap_info(ip_address)
            if scan_data:
                await self.save_nmap_info(scan_data)
                return {"status": "success", "message": "Nmap scan completed"}
            else:
                return {"status": "error", "message": "Failed to perform Nmap scan"}
        except Exception as e:
            logger.error(f"Error in NmapCollector.run for target {self.target_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
