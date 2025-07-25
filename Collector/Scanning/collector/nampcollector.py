import nmap
import json
import logging
from asgiref.sync import sync_to_async
from django.shortcuts import get_object_or_404
from InformationGathering.models import Target
from ..models import AdvancedNmapScan

logger = logging.getLogger(__name__)

class AdvancedNmapCollector:
    def __init__(self, target_id):
        self.target_id = target_id
        self.target = None
        self.nm = nmap.PortScanner()

    async def _get_target(self):
        if not self.target:
            self.target = await sync_to_async(get_object_or_404)(Target, id=self.target_id)
        return self.target

    async def perform_scan(self, ip, args, scan_name):
        try:
            logger.info(f"[+] {scan_name}: nmap {args} {ip}")
            self.nm.scan(hosts=ip, arguments=args)
            if ip in self.nm.all_hosts():
                return self.nm[ip]
            else:
                logger.warning(f"[-] No output for {scan_name} on {ip}")
                return None
        except Exception as e:
            logger.error(f"[-] {scan_name} error: {e}")
            return None

    async def run_all_scans(self, ip):
        scans = [
            ("Ping + Port discovery", "-Pn -sS -p 1-65535"),
            ("Aggressive", "-A -T4 -Pn -sV --version-all --osscan-guess --traceroute"),
            ("Vulnerability Scripts", "-Pn --script vuln,auth"),
            ("Vulners DB", "-Pn --script vulners"),
            ("Default NSE", "-Pn -sC"),
            ("Fragment/Evasion", "-f --mtu 16 --data-length 32 --spoof-mac 0"),
            ("DNS Detection", "-n -R --system-dns --dns-servers 8.8.8.8,1.1.1.1")
        ]
        results = {}
        for name, args in scans:
            out = await self.perform_scan(ip, args, name)
            if out:
                results[name] = out
        return results

    async def extract_data(self, results):
        base = results.get("Aggressive", {}) or {}
        osm = (base.get('osmatch') or [{}])[0]
        os_details = {
            "name": osm.get('name'),
            "accuracy": osm.get('accuracy'),
            "osclass": base.get('osclass', [])
        }

        open_ports = []
        filtered_ports = []
        services = []
        protocols = set()
        vulnerabilities = []

        for scan in results.values():
            for proto in ['tcp', 'udp', 'sctp']:
                if proto in scan:
                    for port, info in scan[proto].items():
                        e = {
                            'port': port, 'protocol': proto,
                            'state': info.get('state'),
                            'service': info.get('name'),
                            'product': info.get('product'),
                            'version': info.get('version')
                        }
                        if e['state'] == 'open':
                            open_ports.append(e)
                        elif e['state'] == 'filtered':
                            filtered_ports.append(e)
                        services.append(e)
                        if e['service']:
                            protocols.add(e['service'])

                        if 'script' in info:
                            for sid, out in info['script'].items():
                                vulnerabilities.append({'port': port,'proto': proto,'script': sid,'output': out})

            for scriptlist in ('hostscript', 'tcpscript', 'udpscript'):
                for svc in (scan.get(scriptlist) or []):
                    vulnerabilities.append({'script': svc.get('id'), 'output': svc.get('output')})

        traceroute = base.get('traceroute', {})
        uptime = base.get('uptime', {}).get('lastboot')
        return {
            'os_details': os_details,
            'open_ports': open_ports,
            'filtered_ports': filtered_ports,
            'service_versions': services,
            'protocols_detected': list(protocols),
            'vulnerabilities': vulnerabilities,
            'host_uptime': uptime,
            'traceroute': traceroute,
            'scan_duration': base.get('duration', 0)
        }

    async def save(self, data, raw):
        await sync_to_async(AdvancedNmapScan.objects.create)(
            target_id=self.target_id,
            scan_type="FullAdvanced",
            status="Success",
            scan_output=raw,
            scan_flags={'steps': list(raw.keys())},
            scan_duration=data['scan_duration'],
            open_ports=data['open_ports'],
            filtered_ports=data['filtered_ports'],
            service_versions=data['service_versions'],
            os_details=data['os_details'],
            host_uptime=data['host_uptime'],
            traceroute=data['traceroute'],
            protocols_detected=data['protocols_detected'],
            vulnerabilities=data['vulnerabilities'],
            scripts_output={}
        )
        logger.info(f"✔️ Advanced scan saved for Target {self.target_id}")

    async def run(self):
        try:
            tgt = await self._get_target()
            ip = tgt.host
            results = await self.run_all_scans(ip)
            if not results:
                return {"status": "error", "message": "No results, target unreachable or blocked"}
            data = await self.extract_data(results)
            await self.save(data, results)
            return {"status": "success", "message": "Advanced scan finished"}
        except Exception as e:
            logger.error(f"Exception: {e}")
            return {"status": "error", "message": str(e)}