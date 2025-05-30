import logging
import httpx
import traceback
from bs4 import BeautifulSoup
from asgiref.sync import sync_to_async
from django.shortcuts import get_object_or_404
from InformationGathering.models import Target, ShodanInfo
import json
import asyncio

logger = logging.getLogger(__name__)

class ShodanCollector:
    def __init__(self, target_id):
        self.target_id = target_id
        self.target = None
        self.search_url = None
        self.clean_ip = None

    async def _get_target(self):
        if not self.target:
            self.target = await sync_to_async(get_object_or_404)(Target, id=self.target_id)
            self.clean_ip = self.target.host.split(":")[1] if ":" in self.target.host else self.target.host
        return self.target

    async def fetch_search_data(self):
        self.search_url = f"https://www.shodan.io/host/{self.clean_ip}"
        logger.warning(f"Fetching Shodan data for {self.search_url}")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.search_url, headers=headers)
                if response.status_code == 200:
                    return response.text
                logger.warning(f"Shodan status {response.status_code} for {self.clean_ip}")
                return None
        except Exception as e:
            logger.error(f"Error fetching Shodan HTML for {self.clean_ip}: {e}")
            return None

    async def extract_shodan_data(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        print("++++++++++++++++++++++++++++++++++++++++++++",self._get_text_after_label(soup, 'Operating System'))

        general_info = {
            'country': self._get_text_after_label(soup, 'Country'),
            'city': self._get_text_after_label(soup, 'City'),
            'organization': self._get_text_after_label(soup, 'Organization'),
            'isp': self._get_text_after_label(soup, 'ISP'),
            'asn': self._get_text_after_label(soup, 'ASN'),
            'os': self._get_text_after_label(soup, 'Operating System'),
        }

        ports = []
        ports_section = soup.find('div', {'id': 'ports'})
        if ports_section:
            for port in ports_section.find_all('a'):
                port_text = port.get_text(strip=True)
                if port_text.isdigit():
                    ports.append(int(port_text))

        services = []
        banners = soup.find_all('h1', class_='banner-title')
        for banner in banners:
            service = banner.find('em')
            if service:
                services.append(service.get_text(strip=True))

        # Try alternative service tag
        if not services:
            service_titles = soup.find_all('div', class_='service-title')
            services = [s.get_text(strip=True) for s in service_titles]

        hostnames = self._extract_comma_list_by_label(soup, 'Hostnames')
        domains = self._extract_comma_list_by_label(soup, 'Domains')
        tags = self._extract_comma_list_by_label(soup, 'Tags')

        last_update = self._get_text_after_label(soup, 'Last Update')
        if not last_update:
            time_tag = soup.find('time')
            if time_tag:
                last_update = time_tag.get_text(strip=True)

        vulnerabilities = self._extract_vulnerabilities(soup)

        # Optional: Save debug snapshot
        # with open(f"/tmp/shodan_{self.clean_ip}.html", "w") as f:
        #     f.write(html_content)

        return {
            'ip': self.clean_ip,
            'general_info': general_info,
            'open_ports': ports,
            'services': services,
            'hostnames': hostnames,
            'domains': domains,
            'tags': tags,
            'last_update': last_update,
            'vulnerabilities': vulnerabilities,
        }

    def _get_text_after_label(self, soup, label_text):
        label = soup.find('label', string=label_text)
        if label:
            value_div = label.find_next('div')
            if value_div:
                return value_div.get_text(strip=True)
        return None

    def _extract_comma_list_by_label(self, soup, label_text):
        data = self._get_text_after_label(soup, label_text)
        return [item.strip() for item in data.split(",")] if data else []

    def _extract_vulnerabilities(self, soup):
        vulns_section = soup.find('section', id='vulns')
        if vulns_section:
            return [a.get_text(strip=True) for a in vulns_section.find_all('a')]
        return []

    async def save_shodan_info(self, data):
        instance, _ = await sync_to_async(ShodanInfo.objects.update_or_create)(
            target=self.target,
            defaults={
                'ip': data['ip'],
                'country': data['general_info'].get('country'),
                'city': data['general_info'].get('city'),
                'organization': data['general_info'].get('organization'),
                'isp': data['general_info'].get('isp'),
                'asn': data['general_info'].get('asn'),
                'os': data['general_info'].get('os'),
                'open_ports': json.dumps(data['open_ports']),
                'services': json.dumps(data['services']),
                'hostnames': json.dumps(data['hostnames']),
                'domains': json.dumps(data['domains']),
                'tags': json.dumps(data['tags']),
                'last_update': data['last_update'],
                'vulnerabilities': json.dumps(data['vulnerabilities']),
            }
        )
        return instance

    async def run(self):
        try:
            await self._get_target()
            html = await self.fetch_search_data()

            if not html:
                return {"status": "error", "message": "No data or failed request"}

            await asyncio.sleep(2)  # Optional anti-bot delay

            extracted = await self.extract_shodan_data(html)
            print("===========================================================================",extracted)
            await self.save_shodan_info(extracted)

            return {"status": "success", "message": "Shodan data saved", "data": extracted}
        except Exception as e:
            logger.error(f"ShodanCollector.run error: {e}\n{traceback.format_exc()}")
            return {"status": "error", "message": str(e)}

