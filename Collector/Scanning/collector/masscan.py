import asyncio
import json
import logging
import time
from django.utils.timezone import now
from asgiref.sync import sync_to_async
from InformationGathering.models import Target
from ..models import ScanResult

logger = logging.getLogger(__name__)

class MasscanScanner:
    def __init__(self, target_id, ports="1-65535", rate="1000", options=None):
        self.target_id = target_id
        self.ports = ports
        self.rate = rate
        self.options = options or {}  # خصائص إضافية مثل interface, adapter-ip
        self.target = None

    async def get_target(self):
        if not self.target:
            try:
                self.target = await sync_to_async(Target.objects.get)(id=self.target_id)
            except Target.DoesNotExist:
                logger.warning(f"Target with ID {self.target_id} does not exist.")
                return None
        return self.target

    def build_masscan_command(self, ip):
        cmd = [
            "masscan", ip,
            "--ports", self.ports,
            "--rate", str(self.rate),
            "--output-format", "json",
            "--output-filename", "-",
        ]

        # إعداد الخصائص المتقدمة
        opt = self.options
        if opt.get("interface"):
            cmd += ["--interface", opt["interface"]]
        if opt.get("adapter_ip"):
            cmd += ["--adapter-ip", opt["adapter_ip"]]
        if opt.get("adapter_mac"):
            cmd += ["--adapter-mac", opt["adapter_mac"]]
        if opt.get("router_mac"):
            cmd += ["--router-mac", opt["router_mac"]]
        if opt.get("source_port"):
            cmd += ["--source-port", str(opt["source_port"])]
        if opt.get("retries"):
            cmd += ["--retries", str(opt["retries"])]
        if opt.get("wait"):
            cmd += ["--wait", str(opt["wait"])]
        if opt.get("randomize_hosts"):
            cmd += ["--randomize-hosts"]
        if opt.get("banners"):
            cmd += ["--banners"]
        if opt.get("exclude_file"):
            cmd += ["--excludefile", opt["exclude_file"]]
        if opt.get("include"):
            cmd += ["--include", opt["include"]]
        if opt.get("log_file"):
            cmd += ["--log", opt["log_file"]]
        if opt.get("pcap_file"):
            cmd += ["--pcap", opt["pcap_file"]]
        return cmd

    async def run_masscan_command(self, ip):
        start_time = time.time()
        cmd = self.build_masscan_command(ip)

        logger.info(f"Running masscan command: {' '.join(cmd)}")
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            duration = time.time() - start_time

            if process.returncode != 0:
                logger.error(f"Masscan failed: {stderr.decode()}")
                return None, duration

            try:
                return json.loads(stdout.decode()), duration
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse masscan output: {e}")
                return None, duration

        except Exception as e:
            logger.exception(f"Masscan execution error: {e}")
            return None, 0

    async def save_results(self, results, duration):
        if not results:
            return None

        open_ports = []
        responders = set()

        for entry in results:
            ip = entry.get("ip")
            ports_info = entry.get("ports", [])
            if ip:
                responders.add(ip)
            for port_entry in ports_info:
                open_ports.append({
                    "ip": ip,
                    "port": port_entry.get("port"),
                    "protocol": port_entry.get("proto"),
                    "status": port_entry.get("status", "open"),
                })

        return await sync_to_async(ScanResult.objects.create)(
            target=self.target,
            scan_type="masscan",
            status="Success",
            scan_date=now(),
            duration=duration,
            scan_flags={
                "rate": self.rate,
                "ports": self.ports,
                "options": self.options
            },
            open_ports=open_ports,
            responders=list(responders),
            raw_output=json.dumps(results),
        )

    async def run(self):
        self.target = await self.get_target()
        if not self.target:
            return None

        results, duration = await self.run_masscan_command(self.target.host)

        if results is None:
            return await sync_to_async(ScanResult.objects.create)(
                target=self.target,
                scan_type="masscan",
                status="Failed",
                scan_date=now(),
                duration=duration,
                scan_flags={
                    "rate": self.rate,
                    "ports": self.ports,
                    "options": self.options
                },
                raw_output="Masscan failed or returned no data"
            )

        return await self.save_results(results, duration)
