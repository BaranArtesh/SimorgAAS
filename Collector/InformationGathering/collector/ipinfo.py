import aiohttp
from ipwhois import IPWhois
from django.core.exceptions import ObjectDoesNotExist
import logging
from asgiref.sync import sync_to_async
from django.conf import settings
from django.shortcuts import get_object_or_404
from InformationGathering.models import IPInfo, Target
from datetime import datetime


logger = logging.getLogger(__name__)

class IPInfoCollector:
    def __init__(self, target_id):
        self.target_id = target_id
        self.target = None
        self.ip = None

    async def fetch_target(self):
        self.target = await sync_to_async(Target.objects.get)(id=self.target_id)
        self.ip = self.target.host
        return self.target

    async def fetch_ipinfo_data(self, session):
        url = f"https://ipinfo.io/{self.ip}?token={settings.IPINFO_TOKEN}"
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            logger.error(f"IPInfo API failed with status {response.status}")
            return {}

    async def fetch_abuseipdb_data(self, session):
        url = f"https://api.abuseipdb.com/api/v2/check?ipAddress={self.ip}&maxAgeInDays=90"
        headers = {
            "Key": settings.ABUSEIPDB_API_KEY,
            "Accept": "application/json"
        }
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("data", {})
            logger.error(f"AbuseIPDB API failed with status {response.status}")
            return {}

    async def fetch_ipgeolocation_data(self, session):
        url = f"https://api.ipgeolocation.io/?key={settings.IPGEOLOCATION_API_KEY}&ip={self.ip}"
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            logger.error(f"IPGEOLOCATION API failed with status {response.status}")
            return {}

    async def collect(self):
        await self.fetch_target()

        async with aiohttp.ClientSession() as session:
            ipinfo_data = await self.fetch_ipinfo_data(session)
            abuse_data = await self.fetch_abuseipdb_data(session)
            ipgeolocation_data = await self.fetch_ipgeolocation_data(session)

            return {
                **ipinfo_data,
                **abuse_data,
                **ipgeolocation_data
            }

    async def save(self, data):
        ip_info = await sync_to_async(IPInfo.objects.create)(
            target=self.target,
            ip_address=self.ip,
            asn=data.get("asn"),
            asn_registry=data.get("registry", None),
            asn_cidr=data.get("cidr", None),
            asn_country_code=data.get("country_code", None),
            asn_description=data.get("org"),
            network_name=data.get("network", {}).get("name") if data.get("network") else None,
            network_handle=data.get("network", {}).get("handle") if data.get("network") else None,
            network_status=data.get("network", {}).get("status") if data.get("network") else None,
            org_name=data.get("organization", {}).get("name") if data.get("organization") else None,
            org_street=data.get("organization", {}).get("street") if data.get("organization") else None,
            org_city=data.get("city", None),
            org_state=data.get("region", None),
            org_postal_code=data.get("postal", None),
            org_country=data.get("country_name", None),
            abuse_contact_email=data.get("abuse", {}).get("email"),
            abuse_contact_phone=data.get("abuse", {}).get("phone"),
            whois_info_link=data.get("whois_url", None),
            abuse_report_link=data.get("abuseConfidenceScore", None),
            terms_of_service_link=data.get("terms_of_service", None),
            geofeed_link=data.get("geofeed_url", None),
        )
        logger.info(f"IP info saved for target {self.target_id}")
        return ip_info

    async def run(self):
        try:
            data = await self.collect()
            if data:
                return await self.save(data)
            return None
        except Exception as e:
            logger.error(f"IP Info collection failed for {self.target_id}: {e}", exc_info=True)
            return None
