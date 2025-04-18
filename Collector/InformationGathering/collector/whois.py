from InformationGathering.models import Target, WhoisInfo
from django.core.exceptions import ObjectDoesNotExist
import logging
import whois
from asgiref.sync import sync_to_async
from django.shortcuts import get_object_or_404
from datetime import datetime
from .filter import filter_data_with_pandas

logger = logging.getLogger(__name__)

class TargetWhoisDataCollector:
    def __init__(self, target_id):
        self.target_id = target_id
        self.target = None
        self.whois_data = None

    async def get_target(self):
        """ Retrieve the target object from the database using target_id """
        if not self.target:
            self.target = await sync_to_async(get_object_or_404)(Target, id=self.target_id)
        return self.target

    async def is_local_target(self):
        """ Check if the target is local based on the 'is_local' field """
        if self.target and hasattr(self.target, 'is_local') and self.target.is_local:
            logger.info(f"Target {self.target_id} is a local target. No WHOIS data available.")
            return True
        return False

    async def is_domain_type(self):
        """ Check if the target is of type 'domain' """
        if self.target and hasattr(self.target, 'type') and self.target.type.lower() == 'domain':
            return True
        logger.error(f"Target {self.target_id} is not of type 'domain'. Cannot gather WHOIS info.")
        return False

    async def collect_whois_info(self):
        """ Collect WHOIS data using the whois library for domain targets """
        if not await self.is_domain_type():
            return None
    
        if not self.target.host:
            logger.error(f"Target {self.target_id} does not have a valid host for WHOIS query.")
            return None

        try:
            self.whois_data = whois.whois(self.target.host)
            if not self.whois_data:
                logger.error(f"No WHOIS data returned for {self.target.host}.")
                return None
        except Exception as e:
            logger.error(f"Failed to fetch WHOIS data for {self.target.host}: {e}")
            return None

        return self.whois_data

    async def process_whois_data(self):
        """ Process the raw WHOIS data and structure it in a detailed way """
        print(self.whois_data)
        logger.info(f"WHOIS data  {self.whois_data} has been saved successfully.")
        if not self.whois_data:
            return None

        processed_data = {
            'domain_name': self._get_first_value(self.whois_data.domain_name),
            'registrar': self._get_first_value(self.whois_data.registrar),
            'whois_server': self._get_first_value(self.whois_data.whois_server),
            'referral_url': self._get_first_value(self.whois_data.referral_url),
            'updated_date': self._format_datetime(self._get_first_value(self.whois_data.updated_date)),
            'creation_date': self._format_datetime(self._get_first_value(self.whois_data.creation_date)),
            'expiration_date': self._format_datetime(self._get_first_value(self.whois_data.expiration_date)),
            'name_servers': self._get_list_value(self.whois_data.name_servers),
            'status': self._get_first_value(self.whois_data.status),
            'emails': self._get_list_value(self.whois_data.emails),
            'dnssec': self._get_first_value(self.whois_data.dnssec),
            'name': self._get_first_value(self.whois_data.name),
            'org': self._get_first_value(self.whois_data.org),
            'address': self._get_first_value(self.whois_data.address),
            'city': self._get_first_value(self.whois_data.city),
            'state': self._get_first_value(self.whois_data.state),
            'registrant_postal_code': self._get_first_value(self.whois_data.registrant_postal_code),
            'country': self._get_first_value(self.whois_data.country),
        }

        return processed_data

    def _get_first_value(self, value):
        """ Utility function to return the first value of a list or the value itself """
        if isinstance(value, list) and len(value) > 0:
            return value[0]
        return value

    def _get_list_value(self, value):
        """ Utility function to return the value as a list or an empty list if it's not """
        if isinstance(value, list):
            return value
        elif value:
            return [value]
        return []

    def _format_datetime(self, value):
        """ Convert datetime objects to string if value is a datetime """
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return value

    async def save_whois_info(self, processed_data):
        """ Save the detailed WHOIS data into the database """
        if processed_data:
            whois_info = await sync_to_async(WhoisInfo.objects.create)(
                target=self.target,
                domain_name=processed_data['domain_name'],
                registrar=processed_data['registrar'],
                whois_server=processed_data['whois_server'],
                referral_url=processed_data['referral_url'],
                updated_date=processed_data['updated_date'],
                creation_date=processed_data['creation_date'],
                expiration_date=processed_data['expiration_date'],
                name_servers=processed_data['name_servers'],
                status=processed_data['status'],
                emails=processed_data['emails'],
                dnssec=processed_data['dnssec'],
                name=processed_data['name'],
                org=processed_data['org'],
                address=processed_data['address'],
                city=processed_data['city'],
                state=processed_data['state'],
                registrant_postal_code=processed_data['registrant_postal_code'],
                country=processed_data['country']
            )
            logger.info(f"WHOIS data for target {self.target_id} has been saved successfully.")
            return whois_info
        return None

    async def run(self):
        """ Run the entire process to gather, process, and store WHOIS data """
        target = await self.get_target()

        if not target:
            return {'status': 'error', 'message': 'Target not found.'}

        if await self.is_local_target():
            return {'status': 'error', 'message': 'This is a local target, no WHOIS information available.'}

        whois_data = await self.collect_whois_info()

        if not whois_data:
            return {'status': 'error', 'message': 'Unable to collect WHOIS data.'}

        processed_data = await self.process_whois_data()

        if not processed_data:
            return {'status': 'error', 'message': 'Failed to process WHOIS data.'}

        saved_whois_info = await self.save_whois_info(processed_data)

        if not saved_whois_info:
            return {'status': 'error', 'message': 'Failed to save WHOIS information.'}

        return {'status': 'success', 'message': 'WHOIS data gathered and saved successfully.'}
    

async def save_whois_info(self, processed_data):
    filtered_data = filter_data_with_pandas(processed_data)
    if filtered_data:
        whois_info = await sync_to_async(WhoisInfo.objects.create)(
            target=self.target,
            **filtered_data
        )
        logger.info(f"تم حفظ معلومات WHOIS للهدف {self.target_id} بنجاح.")
        return whois_info
    return None

