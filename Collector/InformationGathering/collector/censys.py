# import aiohttp
# import logging
# from asgiref.sync import sync_to_async
# from bs4 import BeautifulSoup
# from django.shortcuts import get_object_or_404
# from InformationGathering.models import Target, CensysInfo
# from datetime import datetime

# logger = logging.getLogger(__name__)

# class CensysCollector:
#     def __init__(self, target_id):
#         self.target_id = target_id
#         self.target = None
#         self.base_url = "https://search.censys.io/host/"

#     async def _get_target(self):
#         if not self.target:
#             self.target = await sync_to_async(get_object_or_404)(Target, id=self.target_id)
#         return self.target

#     def _headers(self):
#         return {
#             "User-Agent": (
#                 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#                 "AppleWebKit/537.36 (KHTML, like Gecko) "
#                 "Chrome/123.0.0.0 Safari/537.36"
#             ),
#             "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#             "Accept-Language": "en-US,en;q=0.9",
#         }

#     async def fetch_censys_html(self, ip_address):
#         url = f"{self.base_url}{ip_address}"
#         try:
#             async with aiohttp.ClientSession(headers=self._headers()) as session:
#                 async with session.get(url, timeout=30) as resp:
#                     if resp.status == 200:
#                         return await resp.text()
#                     logger.warning(f"Censys returned status {resp.status} for {ip_address}")
#         except Exception as e:
#             logger.exception(f"Failed to fetch Censys HTML for {ip_address}: {e}")
#         return None

#     def parse_html_to_structured_data(self, html):
#         soup = BeautifulSoup(html, "html.parser")

#         def safe_text(selector):
#             el = soup.select_one(selector)
#             return el.text.strip() if el else None

#         ip = safe_text("h1.text-lg.font-semibold")

#         def get_section_by_title(title):
#             for section in soup.select("section"):
#                 h2 = section.select_one("h2")
#                 if h2 and title.lower() in h2.text.lower():
#                     return section
#             return None

#         def extract_kv(section):
#             data = {}
#             if not section:
#                 return data
#             for row in section.select("div.grid div.flex"):
#                 try:
#                     key = row.select_one("div.text-sm").text.strip()
#                     value = row.select_one("div.truncate")
#                     value_text = value.text.strip() if value else ""
#                     data[key] = value_text
#                 except Exception:
#                     continue
#             return data

#         def parse_datetime(value):
#             try:
#                 return datetime.fromisoformat(value.replace("Z", "+00:00"))
#             except:
#                 return None

#         infra = extract_kv(get_section_by_title("Infrastructure"))
#         tls = extract_kv(get_section_by_title("TLS Certificates"))

#         services = []
#         service_blocks = soup.select("div#services div.flex.flex-col.space-y-6 > div")
#         for block in service_blocks:
#             try:
#                 proto = block.select_one("div.text-sm.text-gray-500").text.strip()
#                 name = block.select_one("h3").text.strip()
#                 banner_el = block.select_one("pre")
#                 banner = banner_el.text.strip() if banner_el else None
#                 services.append({
#                     "port_protocol": proto,
#                     "service": name,
#                     "banner": banner
#                 })
#             except Exception:
#                 continue

#         return {
#             "ip": ip,
#             "asn": int(infra.get("ASN", "").replace("AS", "")) if "ASN" in infra else None,
#             "asn_name": infra.get("Organization"),
#             "asn_country_code": infra.get("Country Code"),
#             "asn_description": infra.get("ASN Name"),
#             "location_city": infra.get("City"),
#             "location_country": infra.get("Country"),
#             "latitude": None,
#             "longitude": None,
#             "tls_issuer": tls.get("Issuer"),
#             "tls_subject": tls.get("Subject"),
#             "tls_not_before": parse_datetime(tls.get("Not Before")),
#             "tls_not_after": parse_datetime(tls.get("Not After")),
#             "protocols": [s.get("port_protocol") for s in services if s.get("port_protocol")],
#             "services": services,
#             "raw_data": {
#                 "infra": infra,
#                 "tls": tls,
#                 "services": services,
#             }
#         }

#     async def save_censys_info(self, data):
#         ip = data.get("ip")
#         if not ip:
#             logger.error("No IP in parsed Censys data; cannot save.")
#             return

#         await sync_to_async(CensysInfo.objects.update_or_create)(
#             target_id=self.target_id,
#             ip=ip,
#             defaults={
#                 "asn": data.get("asn"),
#                 "asn_name": data.get("asn_name"),
#                 "asn_country_code": data.get("asn_country_code"),
#                 "asn_description": data.get("asn_description"),
#                 "location_city": data.get("location_city"),
#                 "location_country": data.get("location_country"),
#                 "latitude": data.get("latitude"),
#                 "longitude": data.get("longitude"),
#                 "tls_issuer": data.get("tls_issuer"),
#                 "tls_subject": data.get("tls_subject"),
#                 "tls_not_before": data.get("tls_not_before"),
#                 "tls_not_after": data.get("tls_not_after"),
#                 "protocols": data.get("protocols"),
#                 "services": data.get("services"),
#                 "raw_data": data.get("raw_data"),
#                 "source": "censys",
#                 "collection_status": "success",
#             }
#         )
#         logger.info(f"Censys data saved for target {self.target_id} ({ip})")

#     async def run(self):
#         try:
#             target = await self._get_target()
#             ip = target.host

#             html = await self.fetch_censys_html(ip)
#             if not html:
#                 return {"status": "error", "message": "Could not fetch Censys HTML"}

#             parsed = self.parse_html_to_structured_data(html)
#             await self.save_censys_info(parsed)
#             return {"status": "success", "message": "Censys data collected and saved"}
#         except Exception as e:
#             logger.exception(f"Error in CensysCollector.run: {e}")
#             return {"status": "error", "message": str(e)}


import aiohttp
import logging
from asgiref.sync import sync_to_async
from bs4 import BeautifulSoup
from django.shortcuts import get_object_or_404
from InformationGathering.models import Target, CensysInfo
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class CensysCollector:
    def __init__(self, target_id, debug=False):
        self.target_id = target_id
        self.target = None
        self.base_url = "https://search.censys.io/host/"
        self.clean_ip = None
        self.debug = debug

    async def _get_target(self):
        if not self.target:
            self.target = await sync_to_async(get_object_or_404)(Target, id=self.target_id)
            self.clean_ip = self.target.host.split(":")[1] if ":" in self.target.host else self.target.host
        return self.target

    def _headers(self):
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def fetch_censys_html(self):
        url = f"{self.base_url}{self.clean_ip}"
        try:
            async with aiohttp.ClientSession(headers=self._headers()) as session:
                async with session.get(url, timeout=30) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        if self.debug:
                            with open(f"debug_censys_{self.clean_ip}.html", "w", encoding="utf-8") as f:
                                f.write(html)
                        return html
                    logger.warning(f"Censys returned status {resp.status} for {self.clean_ip}")
        except Exception as e:
            logger.exception(f"Failed to fetch Censys HTML for {self.clean_ip}: {e}")
        return None

    def parse_html_to_structured_data(self, html):
        soup = BeautifulSoup(html, "html.parser")

        def safe_text(selector):
            el = soup.select_one(selector)
            return el.text.strip() if el else None

        def get_section_by_title(title):
            for section in soup.select("section"):
                h2 = section.select_one("h2")
                if h2 and title.lower() in h2.text.lower():
                    return section
            return None

        def extract_kv(section):
            data = {}
            if not section:
                return data
            for row in section.select("div.grid div.flex"):
                try:
                    key = row.select_one("div.text-sm").text.strip()
                    value = row.select_one("div.truncate")
                    value_text = value.text.strip() if value else ""
                    data[key] = value_text
                except Exception:
                    continue
            return data

        def parse_datetime(value):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except:
                return None

        censys_data = {}

        ip = safe_text("h1.text-lg.font-semibold")
        censys_data["ip"] = ip or self.clean_ip

        infra = extract_kv(get_section_by_title("Infrastructure"))
        tls = extract_kv(get_section_by_title("TLS Certificates"))

        censys_data.update({
            "asn": int(infra.get("ASN", "").replace("AS", "")) if "ASN" in infra else None,
            "asn_name": infra.get("Organization"),
            "asn_country_code": infra.get("Country Code"),
            "asn_description": infra.get("ASN Name"),
            "location_city": infra.get("City"),
            "location_country": infra.get("Country"),
            "latitude": None,
            "longitude": None,
            "tls_issuer": tls.get("Issuer"),
            "tls_subject": tls.get("Subject"),
            "tls_not_before": parse_datetime(tls.get("Not Before")),
            "tls_not_after": parse_datetime(tls.get("Not After")),
        })

        # Extract services
        services = []
        protocols = []
        service_blocks = soup.select("div#services div.flex.flex-col.space-y-6 > div")
        for block in service_blocks:
            try:
                proto = block.select_one("div.text-sm.text-gray-500").text.strip()
                name = block.select_one("h3").text.strip()
                banner_el = block.select_one("pre")
                banner = banner_el.text.strip() if banner_el else None
                services.append({
                    "port_protocol": proto,
                    "service": name,
                    "banner": banner
                })
                protocols.append(proto)
            except Exception:
                continue
        censys_data["services"] = services
        censys_data["protocols"] = protocols

        # Hostnames, domains, tags, vulnerabilities, last seen
        def extract_comma_list(label):
            dt = soup.find("dt", string=label)
            if dt:
                dd = dt.find_next_sibling("dd")
                return [span.text.strip() for span in dd.find_all("span")]
            return []

        censys_data["hostnames"] = extract_comma_list("Hostnames")
        censys_data["domains"] = extract_comma_list("Domains")
        censys_data["tags"] = extract_comma_list("Tags")
        censys_data["vulnerabilities"] = extract_comma_list("Vulnerabilities")

        last_seen_dt = soup.find("dt", string="Last Seen")
        if last_seen_dt:
            censys_data["last_updated"] = last_seen_dt.find_next_sibling("dd").text.strip()

        censys_data["raw_data"] = {
            "infra": infra,
            "tls": tls,
            "services": services,
        }

        return censys_data

    async def save_censys_info(self, data):
        ip = data.get("ip")
        if not ip:
            logger.error("No IP in parsed Censys data; cannot save.")
            return

        await sync_to_async(CensysInfo.objects.update_or_create)(
            target_id=self.target_id,
            ip=ip,
            defaults={
                "asn": data.get("asn"),
                "asn_name": data.get("asn_name"),
                "asn_country_code": data.get("asn_country_code"),
                "asn_description": data.get("asn_description"),
                "location_city": data.get("location_city"),
                "location_country": data.get("location_country"),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "tls_issuer": data.get("tls_issuer"),
                "tls_subject": data.get("tls_subject"),
                "tls_not_before": data.get("tls_not_before"),
                "tls_not_after": data.get("tls_not_after"),
                "protocols": data.get("protocols"),
                "services": data.get("services"),
                "hostnames": json.dumps(data.get("hostnames", [])),
                "domains": json.dumps(data.get("domains", [])),
                "tags": json.dumps(data.get("tags", [])),
                "vulnerabilities": json.dumps(data.get("vulnerabilities", [])),
                "last_updated": data.get("last_updated"),
                "raw_data": data.get("raw_data"),
                "source": "censys",
                "collection_status": "success",
            }
        )
        logger.info(f"Censys data saved for target {self.target_id} ({ip})")

    async def run(self):
        try:
            await self._get_target()
            html = await self.fetch_censys_html()
            if not html:
                return {"status": "error", "message": "Could not fetch Censys HTML"}

            parsed = self.parse_html_to_structured_data(html)
            await self.save_censys_info(parsed)
            return {"status": "success", "message": "Censys data collected and saved"}
        except Exception as e:
            logger.exception(f"Error in CensysCollector.run: {e}")
            return {"status": "error", "message": str(e)}


