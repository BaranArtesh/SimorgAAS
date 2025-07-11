import aiohttp
from ipwhois import IPWhois
import logging
from asgiref.sync import sync_to_async
from django.conf import settings
from django.utils import timezone
from InformationGathering.models import IPInfo, Target
from django.shortcuts import get_object_or_404
import json
from django.utils.dateparse import parse_date

logger = logging.getLogger(__name__)

class IPInfoCollector:
    def __init__(self, target_id):
        self.target_id = target_id
        self.target = None

        
    async def _get_target(self):
        if not self.target:
            self.target = await sync_to_async(get_object_or_404)(Target, id=self.target_id)
        return self.target

    @staticmethod
    def get_ip_info(ip_address):
        try:
            obj = IPWhois(ip_address)
            return obj.lookup_rdap()
        except Exception as e:
            logger.error(f"Error in IP lookup for {ip_address}: {str(e)}")
            return None

    async def collect_ip_info(self, ip_address):
        try:
            ip_info = await sync_to_async(self.get_ip_info)(ip_address)
            data = json.dumps(ip_info)
            return data
        except Exception as e:
            logger.error(f"Error in collecting IP information: {str(e)}")
        return None

    async def save(self, ip_info):
        try:
            cleaned_data = (
                ip_info if isinstance(ip_info, str)
                else json.dumps(ip_info)
            )

            if isinstance(cleaned_data, str) and cleaned_data.startswith('"') and cleaned_data.endswith('"'):
                cleaned_data = cleaned_data[1:-1]

            extracted_data = json.loads(cleaned_data)

            #
            #print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n", extracted_data)

            network = extracted_data.get('network', {})

            # Try to get any contact object dynamically
            contact = None
            for obj in extracted_data.get('objects', {}).values():
                contact_data = obj.get('contact', {})
                if contact_data.get('address'):
                    contact = contact_data
                    break

            address_lines = contact.get('address', [{}])[0].get('value', "").split("\n") if contact else []
            org_street = address_lines[0] if len(address_lines) > 0 else None
            org_city = address_lines[1] if len(address_lines) > 1 else None
            org_state = address_lines[2] if len(address_lines) > 2 else None
            org_postal_code = address_lines[3] if len(address_lines) > 3 else None
            country = address_lines[4] if len(address_lines) > 4 else None

            # Extract contact info by role
            def extract_contact(field):
                for obj in extracted_data.get('objects', {}).values():
                    roles = obj.get('roles', [])
                    if field in roles:
                        return {
                            "name": obj.get('contact', {}).get('name'),
                            "email": obj.get('contact', {}).get('email'),
                            "phone": obj.get('contact', {}).get('phone'),
                            "link": obj.get('links', [None])[0] if obj.get('links') else None
                        }
                return {}

            abuse = extract_contact('abuse')
            admin = extract_contact('admin')
            noc = extract_contact('noc')

            print("ADMIN:", admin)
            print("NOC:", noc)
            print("ABUSE:", abuse)

            await sync_to_async(IPInfo.objects.create)(
                target_id=self.target_id,
                ip_address=extracted_data.get('query'),
                asn=extracted_data.get('asn'),
                asn_registry=extracted_data.get('asn_registry'),
                asn_cidr=extracted_data.get('asn_cidr'),
                asn_country_code=extracted_data.get('asn_country_code'),
                asn_date=parse_date(extracted_data.get('asn_date')) if extracted_data.get('asn_date') else None,
                asn_description=extracted_data.get('asn_description'),
                network_name=network.get('name'),
                network_handle=network.get('handle'),
                network_status=", ".join(network.get('status', [])) if isinstance(network.get('status'), list) else None,
                network_start_address=network.get('start_address'),
                network_end_address=network.get('end_address'),
                network_cidr=network.get('cidr'),
                network_ip_version=network.get('ip_version'),
                network_type=network.get('type'),
                network_parent_handle=network.get('parent_handle'),
                org_name=contact.get('name') if contact else None,
                org_street=org_street,
                org_city=org_city,
                org_state=org_state,
                org_postal_code=org_postal_code,
                org_country=country,
                abuse_contact_name=abuse.get('name'),
                abuse_contact_email=abuse.get('email'),
                abuse_contact_phone=abuse.get('phone'),
                admin_contact_name=admin.get('name'),
                admin_contact_email=admin.get('email'),
                admin_contact_phone=admin.get('phone'),
                noc_contact_name=noc.get('name'),
                noc_contact_email=noc.get('email'),
                noc_contact_phone=noc.get('phone'),
                abuse_report_link=abuse.get('link'),
                whois_info_link=extracted_data.get('whois_url'),
                terms_of_service_link=extracted_data.get('terms_of_service'),
                geofeed_link=extracted_data.get('geofeed'),
            )
        except Exception as e:
            logger.error(f"Error saving IPInfo: {e}")

    async def run(self):
        try:
            target = await self._get_target()
            ip_address = target.host
            ip_info = await self.collect_ip_info(ip_address)
            if ip_info:
                await self.save(ip_info)
                return {"status": "success", "message": "IP Info collected and saved"}
            else:
                return {"status": "error", "message": "Failed to collect IP Info"}
        except Exception as e:
            logger.error(f"Run failed for {self.target_id}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}