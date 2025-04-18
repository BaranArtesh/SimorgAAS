# import aiohttp
# import ipaddress
# import logging
# from datetime import datetime
# from asgiref.sync import sync_to_async
# from django.conf import settings
# from django.core.exceptions import ObjectDoesNotExist
# from InformationGathering.models import IPInfo, Target

# logger = logging.getLogger(__name__)

# class IPInfoCollector:
#     def __init__(self, target_id):
#         self.target_id = target_id
#         self.target = None
#         self.ip = None

#     async def fetch_target(self):
#         try:
#             self.target = await sync_to_async(Target.objects.get)(id=self.target_id)
#             self.ip = self.target.host.replace(",", ".")

#             # تحقق من أن IP صالح
#             ipaddress.ip_address(self.ip)
#             logger.info(f"Target fetched with valid IP: {self.ip}")
#             return self.target
#         except (ObjectDoesNotExist, ValueError) as e:
#             logger.error(f"Invalid target or IP format for ID {self.target_id}: {e}")
#             self.ip = None
#             return None

#     async def fetch_ipinfo_data(self, session):
#         url = f"https://ipinfo.io/{self.ip}?token={settings.IPINFO_TOKEN}"
#         async with session.get(url) as response:
#             if response.status == 200:
#                 data = await response.json()
#                 logger.debug(f"IPInfo data: {data}")
#                 return data
#             logger.error(f"IPInfo API failed: {response.status} - {await response.text()}")
#             return {}

#     async def fetch_abuseipdb_data(self, session):
#         url = f"https://api.abuseipdb.com/api/v2/check?ipAddress={self.ip}&maxAgeInDays=90"
#         headers = {
#             "Key": settings.ABUSEIPDB_API_KEY,
#             "Accept": "application/json"
#         }
#         async with session.get(url, headers=headers) as response:
#             if response.status == 200:
#                 data = await response.json()
#                 logger.debug(f"AbuseIPDB data: {data}")
#                 return data.get("data", {})
#             logger.error(f"AbuseIPDB API failed: {response.status} - {await response.text()}")
#             return {}

#     async def fetch_ipgeolocation_data(self, session):
#         url = f"https://api.ipgeolocation.io/ipgeo?apiKey={settings.IPGEOLOCATION_API_KEY}&ip={self.ip}"
#         async with session.get(url) as response:
#             if response.status == 200:
#                 data = await response.json()
#                 logger.debug(f"IPGeolocation data: {data}")
#                 return data
#             logger.error(f"IPGeolocation API failed: {response.status} - {await response.text()}")
#             return {}

#     def normalize_data(self, ipinfo_data, abuse_data, ipgeo_data):
#         return {
#             "asn": ipinfo_data.get("asn"),
#             "asn_registry": ipinfo_data.get("registry"),
#             "asn_cidr": ipinfo_data.get("cidr"),
#             "asn_country_code": ipinfo_data.get("country"),
#             "asn_description": ipinfo_data.get("org"),
#             "network_name": ipinfo_data.get("network", {}).get("name"),
#             "network_handle": ipinfo_data.get("network", {}).get("handle"),
#             "network_status": ipinfo_data.get("network", {}).get("status"),
#             "org_name": ipgeo_data.get("organization"),
#             "org_street": ipgeo_data.get("street"),
#             "org_city": ipgeo_data.get("city"),
#             "org_state": ipgeo_data.get("state_prov"),
#             "org_postal_code": ipgeo_data.get("zipcode"),
#             "org_country": ipgeo_data.get("country_name"),
#             "abuse_contact_email": abuse_data.get("abuseContactEmail"),
#             "abuse_contact_phone": None,
#             "whois_info_link": ipinfo_data.get("readme"),
#             "abuse_report_link": abuse_data.get("abuseConfidenceScore"),
#             "terms_of_service_link": ipinfo_data.get("privacy"),
#             "geofeed_link": ipinfo_data.get("geofeed"),
#         }

#     async def collect(self):
#         if not await self.fetch_target() or not self.ip:
#             logger.warning(f"Skipping IP info collection due to invalid IP for target {self.target_id}")
#             return None

#         async with aiohttp.ClientSession() as session:
#             ipinfo_data = await self.fetch_ipinfo_data(session)
#             abuse_data = await self.fetch_abuseipdb_data(session)
#             ipgeo_data = await self.fetch_ipgeolocation_data(session)

#             return self.normalize_data(ipinfo_data, abuse_data, ipgeo_data)

#     async def save(self, data):
#         ip_info = await sync_to_async(IPInfo.objects.create)(
#             target=self.target,
#             ip_address=self.ip,
#             **data
#         )
#         logger.info(f"IP info saved for target {self.target_id}")
#         return ip_info

#     async def run(self):
#         try:
#             data = await self.collect()
#             if data:
#                 return await self.save(data)
#             logger.warning(f"No data collected for target {self.target_id}")
#             return None
#         except Exception as e:
#             logger.error(f"IP Info collection failed for {self.target_id}: {e}", exc_info=True)
#             return None


import aiohttp
import ipaddress
import logging
from datetime import datetime
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from InformationGathering.models import IPInfo, Target
from .filter import filter_data_with_pandas

logger = logging.getLogger(__name__)

class IPInfoCollector:
    def __init__(self, target_id):
        self.target_id = target_id
        self.target = None
        self.ip = None

    async def fetch_target(self):
        try:
            self.target = await sync_to_async(Target.objects.get)(id=self.target_id)
            self.ip = self.target.host.replace(",", ".")

            # Validate that IP is correct
            ipaddress.ip_address(self.ip)
            logger.info(f"Target fetched with valid IP: {self.ip}")
            return self.target
        except (ObjectDoesNotExist, ValueError) as e:
            logger.error(f"Invalid target or IP format for ID {self.target_id}: {e}")
            self.ip = None
            return None

    async def fetch_ipinfo_data(self, session):
        url = f"https://ipinfo.io/{self.ip}?token={settings.IPINFO_TOKEN}"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                logger.debug(f"IPInfo data: {data}")
                return data
            logger.error(f"IPInfo API failed: {response.status} - {await response.text()}")
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
                logger.debug(f"AbuseIPDB data: {data}")
                return data.get("data", {})
            logger.error(f"AbuseIPDB API failed: {response.status} - {await response.text()}")
            return {}

    async def fetch_ipgeolocation_data(self, session):
        url = f"https://api.ipgeolocation.io/ipgeo?apiKey={settings.IPGEOLOCATION_API_KEY}&ip={self.ip}"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                logger.debug(f"IPGeolocation data: {data}")
                return data
            logger.error(f"IPGeolocation API failed: {response.status} - {await response.text()}")
            return {}

    def normalize_data(self, ipinfo_data, abuse_data, ipgeo_data):
        logger.debug(f"Normalizing data: {ipinfo_data}, {abuse_data}, {ipgeo_data}")
        return {
            "asn": ipinfo_data.get("asn"),
            "asn_registry": ipinfo_data.get("registry"),
            "asn_cidr": ipinfo_data.get("cidr"),
            "asn_country_code": ipinfo_data.get("country"),
            "asn_description": ipinfo_data.get("org"),
            "network_name": ipinfo_data.get("network", {}).get("name"),
            "network_handle": ipinfo_data.get("network", {}).get("handle"),
            "network_status": ipinfo_data.get("network", {}).get("status"),
            "org_name": ipgeo_data.get("organization"),
            "org_street": ipgeo_data.get("street"),
            "org_city": ipgeo_data.get("city"),
            "org_state": ipgeo_data.get("state_prov"),
            "org_postal_code": ipgeo_data.get("zipcode"),
            "org_country": ipgeo_data.get("country_name"),
            "abuse_contact_email": abuse_data.get("abuseContactEmail"),
            "abuse_contact_phone": None,
            "whois_info_link": ipinfo_data.get("readme"),
            "abuse_report_link": abuse_data.get("abuseConfidenceScore"),
            "terms_of_service_link": ipinfo_data.get("privacy"),
            "geofeed_link": ipinfo_data.get("geofeed"),
        }

    async def collect(self):
        if not await self.fetch_target() or not self.ip:
            logger.warning(f"Skipping IP info collection due to invalid IP for target {self.target_id}")
            return None

        async with aiohttp.ClientSession() as session:
            ipinfo_data = await self.fetch_ipinfo_data(session)
            abuse_data = await self.fetch_abuseipdb_data(session)
            ipgeo_data = await self.fetch_ipgeolocation_data(session)

            return self.normalize_data(ipinfo_data, abuse_data, ipgeo_data)

    async def save(self, data):
        ip_info = await sync_to_async(IPInfo.objects.create)(
            target=self.target,
            ip_address=self.ip,
            **data
        )
        logger.info(f"IP info saved for target {self.target_id}")
        return ip_info

    async def run(self):
        try:
            data = await self.collect()
            if data:
                return await self.save(data)
            logger.warning(f"No data collected for target {self.target_id}")
            return None
        except Exception as e:
            logger.error(f"IP Info collection failed for {self.target_id}: {e}", exc_info=True)
            return None
        
async def save(self, data):
    filtered_data = filter_data_with_pandas(data)
    if filtered_data:
        ip_info = await sync_to_async(IPInfo.objects.create)(
            target=self.target,
            ip_address=self.ip,
            **filtered_data
        )
        logger.info(f"تم حفظ معلومات IP للهدف {self.target_id}")
        return ip_info
    return None

