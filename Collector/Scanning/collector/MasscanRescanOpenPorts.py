from InformationGathering.models import NmapScan  # أو ScanResult حسب المصدر
from Scanning.collector.masscan import MasscanScanner
from asgiref.sync import sync_to_async

class MasscanRescanOpenPorts:
    def __init__(self, target_id):
        self.target_id = target_id

    async def get_ports_from_nmap(self):
        try:
            latest_scan = await sync_to_async(
                lambda: NmapScan.objects.filter(target_id=self.target_id, status="Success").latest("scan_date")
            )()
        except NmapScan.DoesNotExist:
            return []

        ports = latest_scan.open_ports or []
        return [str(p["port"]) for p in ports if "port" in p]

    async def scan_open_ports(self):
        port_list = await self.get_ports_from_nmap()
        if not port_list:
            return {"status": "error", "message": "No open ports found from previous Nmap scan."}

        ports_str = ",".join(port_list)

        scanner = MasscanScanner(
            target_id=self.target_id,
            ports=ports_str,
            rate="1000"  # يمكنك زيادته حسب الرغبة
        )
        result = await scanner.run()

        if result:
            return {"status": "success", "scan_id": result.id, "ports_scanned": ports_str}
        else:
            return {"status": "error", "message": "Masscan failed"}
