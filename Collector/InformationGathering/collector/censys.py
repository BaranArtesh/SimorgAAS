# import aiohttp
# import logging
# import os
# import time
# import json
# from datetime import datetime
# from asgiref.sync import sync_to_async
# from bs4 import BeautifulSoup
# from django.shortcuts import get_object_or_404
# from dotenv import load_dotenv
# from InformationGathering.models import Target, CensysInfo

# logger = logging.getLogger(__name__)
# load_dotenv()

# class CensysCollector:
#     def __init__(self, target_id, debug=False, max_retries=3):
#         self.target_id = target_id
#         self.target = None
#         self.clean_ip = None
#         self.base_url = "https://search.censys.io/host/"
#         self.debug = debug
#         self.max_retries = max_retries
#         self.proxy = os.getenv("PROXY")

#     async def _get_target(self):
#         if not self.target:
#             self.target = await sync_to_async(get_object_or_404)(Target, id=self.target_id)
#             self.clean_ip = self.target.host.split(":")[1] if ":" in self.target.host else self.target.host
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

#     async def fetch_censys_html(self):
#         url = f"{self.base_url}{self.clean_ip}"
#         for attempt in range(1, self.max_retries + 1):
#             try:
#                 async with aiohttp.ClientSession(headers=self._headers()) as session:
#                     async with session.get(url, proxy=self.proxy, timeout=30) as resp:
#                         if resp.status == 200:
#                             html = await resp.text()
#                             if self.debug:
#                                 with open(f"debug_censys_{self.clean_ip}.html", "w", encoding="utf-8") as f:
#                                     f.write(html)
#                             return html
#                         logger.warning(f"[{attempt}] Censys returned status {resp.status} for {self.clean_ip}")
#             except Exception as e:
#                 logger.warning(f"[{attempt}] Censys request error: {e}")
#                 time.sleep(2)
#         logger.error(f"Failed to fetch Censys HTML for {self.clean_ip} after {self.max_retries} retries.")
#         return None

#     def parse_html_to_structured_data(self, html):
#         soup = BeautifulSoup(html, "html.parser")

#         def safe_text(selector):
#             el = soup.select_one(selector)
#             return el.text.strip() if el else None

#         def get_section_by_title(title):
#             return next((s for s in soup.select("section") if s.select_one("h2") and title.lower() in s.select_one("h2").text.lower()), None)

#         def extract_kv(section):
#             data = {}
#             if section:
#                 for row in section.select("div.grid div.flex"):
#                     try:
#                         key = row.select_one("div.text-sm").text.strip()
#                         value = row.select_one("div.truncate")
#                         data[key] = value.text.strip() if value else ""
#                     except Exception:
#                         continue
#             return data

#         def parse_datetime(value):
#             try:
#                 return datetime.fromisoformat(value.replace("Z", "+00:00"))
#             except:
#                 return None

#         def extract_comma_list(label):
#             dt = soup.find("dt", string=label)
#             if dt:
#                 dd = dt.find_next_sibling("dd")
#                 return [span.text.strip() for span in dd.find_all("span")]
#             return []

#         censys_data = {
#             "ip": safe_text("h1.text-lg.font-semibold") or self.clean_ip,
#         }

#         infra = extract_kv(get_section_by_title("Infrastructure"))
#         tls = extract_kv(get_section_by_title("TLS Certificates"))

#         censys_data.update({
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
#         })

#         services = []
#         protocols = []
#         for block in soup.select("div#services div.flex.flex-col.space-y-6 > div"):
#             try:
#                 proto = block.select_one("div.text-sm.text-gray-500").text.strip()
#                 name = block.select_one("h3").text.strip()
#                 banner_el = block.select_one("pre")
#                 banner = banner_el.text.strip() if banner_el else None
#                 services.append({"port_protocol": proto, "service": name, "banner": banner})
#                 protocols.append(proto)
#             except Exception as e:
#                 logger.warning(f"Service parsing error: {e}")
#                 continue

#         censys_data.update({
#             "services": services,
#             "protocols": protocols,
#             "hostnames": extract_comma_list("Hostnames"),
#             "domains": extract_comma_list("Domains"),
#             "tags": extract_comma_list("Tags"),
#             "vulnerabilities": extract_comma_list("Vulnerabilities"),
#             "last_updated": safe_text("dt:contains('Last Seen') + dd"),
#             "raw_data": {"infra": infra, "tls": tls, "services": services}
#         })

#         return censys_data

#     async def save_censys_info(self, data):
#         ip = data.get("ip")
#         if not ip:
#             logger.error("No IP found; skipping save.")
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
#                 "hostnames": json.dumps(data.get("hostnames", [])),
#                 "domains": json.dumps(data.get("domains", [])),
#                 "tags": json.dumps(data.get("tags", [])),
#                 "vulnerabilities": json.dumps(data.get("vulnerabilities", [])),
#                 "last_updated": data.get("last_updated"),
#                 "raw_data": data.get("raw_data"),
#                 "source": "censys",
#                 "collection_status": "success",
#             }
#         )
#         logger.info(f"[Censys] Data saved for {self.target_id} ({ip})")

#     async def run(self):
#         try:
#             await self._get_target()
#             html = await self.fetch_censys_html()
#             if not html:
#                 return {"status": "error", "message": "Failed to fetch HTML"}
#             parsed = self.parse_html_to_structured_data(html)
#             if not parsed:
#                 return {"status": "error", "message": "Failed to parse HTML"}
#             await self.save_censys_info(parsed)
#             return {"status": "success", "message": "Censys data collected"}
#         except Exception as e:
#             logger.exception("Unhandled error in CensysCollector.run")
#             return {"status": "error", "message": str(e)}

# import logging
# import os
# import time
# import json
# from datetime import datetime
# from asgiref.sync import sync_to_async
# from bs4 import BeautifulSoup
# from django.shortcuts import get_object_or_404
# from dotenv import load_dotenv
# from InformationGathering.models import Target, CensysInfo
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium_stealth import stealth
# import undetected_chromedriver as uc
# import requests

# logger = logging.getLogger(__name__)
# load_dotenv()

# class CensysCollector:
#     def __init__(self, target_id, debug=False, max_retries=3):
#         self.target_id = target_id
#         self.target = None
#         self.clean_ip = None
#         self.base_url = "https://search.censys.io/hosts/"
#         self.debug = debug
#         self.max_retries = max_retries
#         self.proxy = os.getenv("PROXY")

#     async def _get_target(self):
#         if not self.target:
#             self.target = await sync_to_async(get_object_or_404)(Target, id=self.target_id)
#             self.clean_ip = self.target.host.split(":")[1] if ":" in self.target.host else self.target.host
#         return self.target

#     def fetch_censys_html_selenium(self):
#         url = f"{self.base_url}{self.clean_ip}"
#         options = uc.ChromeOptions()
#         options.headless = True
#         options.add_argument("--no-sandbox")
#         options.add_argument("--disable-dev-shm-usage")
#         options.add_argument("--disable-blink-features=AutomationControlled")

#         if self.proxy:
#             options.add_argument(f'--proxy-server={self.proxy}')

#         attempt = 0
#         while attempt < self.max_retries:
#             try:
#                 driver = uc.Chrome(version_main=136, options=options)
#                 stealth(driver,
#                     languages=["en-US", "en"],
#                     vendor="Google Inc.",
#                     platform="Win32",
#                     webgl_vendor="Intel Inc.",
#                     renderer="Intel Iris OpenGL Engine",
#                     fix_hairline=True,
#                 )

#                 driver.get(url)
#                 # Wait for the Services section or hostname to appear
#                 WebDriverWait(driver, 15).until(
#                     EC.presence_of_element_located((By.CSS_SELECTOR, "h1.text-lg.font-semibold"))
#                 )

#                 html = driver.page_source

#                 if self.debug:
#                     with open(f"debug_censys_{self.clean_ip}.html", "w", encoding="utf-8") as f:
#                         f.write(html)

#                 if "Access denied" in html or "Rate limit" in html or "Blocked" in html:
#                     logger.warning("Blocked by Censys or Cloudflare")
#                     return None

#                 return html
#             except Exception as e:
#                 attempt += 1
#                 logger.error(f"Error fetching Censys HTML (attempt {attempt}/{self.max_retries}): {e}")
#                 time.sleep(5)  # Wait before retrying
#             finally:
#                 try:
#                     driver.quit()
#                 except:
#                     pass
#         return None

#     def parse_html_to_structured_data(self, html):
#         soup = BeautifulSoup(html, "html.parser")

#         def safe_text(selector):
#             el = soup.select_one(selector)
#             return el.text.strip() if el else None

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
#                     key = row.select_one("div.text-sm")
#                     value = row.select_one("div.truncate") or row.select_one("div.whitespace-nowrap")
#                     if key:
#                         data[key.text.strip()] = value.text.strip() if value else ""
#                 except Exception as e:
#                     logger.debug(f"KV parse error: {e}")
#             return data

#         def parse_datetime(value):
#             try:
#                 return datetime.fromisoformat(value.replace("Z", "+00:00"))
#             except:
#                 return None

#         def extract_comma_list(label):
#             try:
#                 dt = soup.find("dt", string=label)
#                 dd = dt.find_next_sibling("dd") if dt else None
#                 return [span.text.strip() for span in dd.find_all("span")] if dd else []
#             except:
#                 return []

#         censys_data = {
#             "ip": safe_text("h1.text-lg.font-semibold") or self.clean_ip,
#         }

#         infra = extract_kv(get_section_by_title("Infrastructure"))
#         tls = extract_kv(get_section_by_title("TLS Certificates"))

#         censys_data.update({
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
#         })

#         services = []
#         protocols = []
#         service_blocks = soup.select("div#services div.flex.flex-col.space-y-6 > div")
#         for block in service_blocks:
#             try:
#                 proto = block.select_one("div.text-sm.text-gray-500")
#                 name = block.select_one("h3")
#                 banner_el = block.select_one("pre")
#                 services.append({
#                     "port_protocol": proto.text.strip() if proto else "",
#                     "service": name.text.strip() if name else "",
#                     "banner": banner_el.text.strip() if banner_el else ""
#                 })
#                 if proto:
#                     protocols.append(proto.text.strip())
#             except Exception as e:
#                 logger.debug(f"Service parse error: {e}")

#         censys_data["services"] = services
#         censys_data["protocols"] = protocols
#         censys_data["hostnames"] = extract_comma_list("Hostnames")
#         censys_data["domains"] = extract_comma_list("Domains")
#         censys_data["tags"] = extract_comma_list("Tags")
#         censys_data["vulnerabilities"] = extract_comma_list("Vulnerabilities")

#         last_seen_dt = soup.find("dt", string="Last Seen")
#         if last_seen_dt:
#             censys_data["last_updated"] = last_seen_dt.find_next_sibling("dd").text.strip()

#         censys_data["raw_data"] = {
#             "infra": infra,
#             "tls": tls,
#             "services": services,
#         }

#         return censys_data

#     async def save_censys_info(self, data):
#         ip = data.get("ip")
#         if not ip:
#             logger.error("No IP found; skipping Censys save.")
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
#                 "hostnames": json.dumps(data.get("hostnames", [])),
#                 "domains": json.dumps(data.get("domains", [])),
#                 "tags": json.dumps(data.get("tags", [])),
#                 "vulnerabilities": json.dumps(data.get("vulnerabilities", [])),
#                 "last_updated": data.get("last_updated"),
#                 "raw_data": data.get("raw_data"),
#                 "source": "censys",
#                 "collection_status": "success",
#             }
#         )
#         logger.info(f"Saved Censys data for target {self.target_id} ({ip})")

#     async def run(self):
#         try:
#             await self._get_target()
#             html = self.fetch_censys_html_selenium()
#             if not html:
#                 return {"status": "error", "message": "Failed to fetch or received invalid HTML"}
#             parsed = self.parse_html_to_structured_data(html)
#             if not parsed:
#                 return {"status": "error", "message": "Failed to parse HTML"}
#             await self.save_censys_info(parsed)
#             return {"status": "success", "message": "Censys data collected successfully"}
#         except Exception as e:
#             logger.exception("Error in CensysCollector.run:")
#             return {"status": "error", "message": str(e)}




# import logging
# import os
# import json
# import time
# from datetime import datetime
# from asgiref.sync import sync_to_async
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from django.shortcuts import get_object_or_404
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium_stealth import stealth
# from webdriver_manager.chrome import ChromeDriverManager
# from InformationGathering.models import Target, CensysInfo

# logger = logging.getLogger(__name__)
# load_dotenv()

# class CensysCollector:
#     def __init__(self, target_id, debug=False, max_retries=3):
#         self.target_id = target_id
#         self.target = None
#         self.clean_ip = None
#         self.base_url = "https://search.censys.io/host/"
#         self.debug = debug
#         self.max_retries = max_retries

#     async def _get_target(self):
#         if not self.target:
#             self.target = await sync_to_async(get_object_or_404)(Target, id=self.target_id)
#             self.clean_ip = self.target.host.split(":")[1] if ":" in self.target.host else self.target.host
#         return self.target

#     def _get_driver(self):
#         chrome_options = Options()
#         # NOTE: Not headless for better stealth (use headless only when stable)
#         # chrome_options.add_argument("--headless")
#         chrome_options.add_argument("--disable-blink-features=AutomationControlled")
#         chrome_options.add_argument("--no-sandbox")
#         chrome_options.add_argument("--disable-dev-shm-usage")
#         chrome_options.add_argument("--disable-gpu")
#         chrome_options.add_argument("--window-size=1920,1080")

#         driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

#         stealth(driver,
#             languages=["en-US", "en"],
#             vendor="Google Inc.",
#             platform="Win32",
#             webgl_vendor="Intel Inc.",
#             renderer="Intel Iris OpenGL Engine",
#             fix_hairline=True,
#         )
#         return driver

#     def fetch_censys_html(self):
#         retries = 0
#         url = f"{self.base_url}{self.clean_ip}"

#         while retries < self.max_retries:
#             try:
#                 logger.info(f"[Censys] Attempting fetch for {self.clean_ip} (try {retries + 1})")
#                 driver = self._get_driver()
#                 driver.get(url)
#                 WebDriverWait(driver, 20).until(
#                     EC.presence_of_element_located((By.TAG_NAME, "body"))
#                 )
#                 time.sleep(3)  # Allow full load
#                 html = driver.page_source
#                 driver.quit()

#                 if "Host not found" in html or "Rate limit" in html or "Access denied" in html:
#                     logger.warning("Censys returned error content")
#                     return None
#                 return html

#             except Exception as e:
#                 logger.warning(f"Error fetching Censys HTML (attempt {retries + 1}/{self.max_retries}): {e}")
#                 retries += 1
#                 time.sleep(2 ** retries)

#         logger.error(f"Failed to fetch Censys HTML after {self.max_retries} attempts for {self.clean_ip}")
#         return None

#     def parse_html_to_structured_data(self, html):
#         soup = BeautifulSoup(html, "html.parser")

#         def safe_text(selector):
#             el = soup.select_one(selector)
#             return el.text.strip() if el else None

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
#                     key = row.select_one("div.text-sm")
#                     value = row.select_one("div.truncate")
#                     if key:
#                         data[key.text.strip()] = value.text.strip() if value else ""
#                 except Exception as e:
#                     logger.debug(f"Error parsing key-value pair: {e}")
#             return data

#         def parse_datetime(value):
#             try:
#                 return datetime.fromisoformat(value.replace("Z", "+00:00"))
#             except Exception:
#                 return None

#         def extract_comma_list(label):
#             dt = soup.find("dt", string=label)
#             if dt:
#                 dd = dt.find_next_sibling("dd")
#                 return [span.text.strip() for span in dd.find_all("span")]
#             return []

#         censys_data = {
#             "ip": safe_text("h1.text-lg.font-semibold") or self.clean_ip,
#         }

#         infra = extract_kv(get_section_by_title("Infrastructure"))
#         tls = extract_kv(get_section_by_title("TLS Certificates"))

#         censys_data.update({
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
#         })

#         services = []
#         protocols = []
#         for block in soup.select("div#services div.flex.flex-col.space-y-6 > div"):
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
#                 protocols.append(proto)
#             except Exception as e:
#                 logger.debug(f"Error extracting service: {e}")

#         censys_data["services"] = services
#         censys_data["protocols"] = protocols
#         censys_data["hostnames"] = extract_comma_list("Hostnames")
#         censys_data["domains"] = extract_comma_list("Domains")
#         censys_data["tags"] = extract_comma_list("Tags")
#         censys_data["vulnerabilities"] = extract_comma_list("Vulnerabilities")

#         last_seen_dt = soup.find("dt", string="Last Seen")
#         if last_seen_dt:
#             last_seen_text = last_seen_dt.find_next_sibling("dd").text.strip()
#             censys_data["last_updated"] = last_seen_text

#         censys_data["raw_data"] = {
#             "infra": infra,
#             "tls": tls,
#             "services": services,
#         }

#         return censys_data

#     async def save_censys_info(self, data):
#         ip = data.get("ip")
#         if not ip:
#             logger.error("No IP found; cannot save Censys data.")
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
#                 "hostnames": json.dumps(data.get("hostnames", [])),
#                 "domains": json.dumps(data.get("domains", [])),
#                 "tags": json.dumps(data.get("tags", [])),
#                 "vulnerabilities": json.dumps(data.get("vulnerabilities", [])),
#                 "last_updated": data.get("last_updated"),
#                 "raw_data": data.get("raw_data"),
#                 "source": "censys",
#                 "collection_status": "success",
#             }
#         )
#         logger.info(f"Censys data saved for target {self.target_id} ({ip})")

#     async def run(self):
#         try:
#             await self._get_target()
#             html = self.fetch_censys_html()
#             if not html:
#                 return {"status": "error", "message": "Failed to fetch or received invalid HTML"}
#             parsed = self.parse_html_to_structured_data(html)
#             if not parsed:
#                 return {"status": "error", "message": "Failed to parse HTML"}
#             await self.save_censys_info(parsed)
#             return {"status": "success", "message": "Censys data collected"}
#         except Exception as e:
#             logger.exception("Error in CensysCollector.run:")
#             return {"status": "error", "message": str(e)}




# import logging
# import os
# import json
# import time
# import re
# import ipaddress
# from datetime import datetime
# from dateutil import parser as date_parser  # New: for flexible datetime parsing
# from asgiref.sync import sync_to_async
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from django.shortcuts import get_object_or_404
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium_stealth import stealth
# from webdriver_manager.chrome import ChromeDriverManager
# from InformationGathering.models import Target, CensysInfo

# logger = logging.getLogger(__name__)
# load_dotenv()


# class CensysCollector:
#     def __init__(self, target_id, debug=False, max_retries=3):
#         self.target_id = target_id
#         self.target = None
#         self.clean_ip = None
#         self.base_url = "https://search.censys.io/host/"
#         self.debug = debug
#         self.max_retries = max_retries

#     async def _get_target(self):
#         if not self.target:
#             self.target = await sync_to_async(get_object_or_404)(Target, id=self.target_id)
#             # Extract clean IP (ignoring port information if present)
#             self.clean_ip = self.target.host.split(":")[1] if ":" in self.target.host else self.target.host
#         return self.target

#     def _get_driver(self):
#         chrome_options = Options()
#         # Optional: Toggle headless mode via environment (recommended for debugging)
#         if os.getenv("HEADLESS", "False").lower() in ["true", "1"]:
#             chrome_options.add_argument("--headless")
#         chrome_options.add_argument("--disable-blink-features=AutomationControlled")
#         chrome_options.add_argument("--no-sandbox")
#         chrome_options.add_argument("--disable-dev-shm-usage")
#         chrome_options.add_argument("--disable-gpu")
#         chrome_options.add_argument("--window-size=1920,1080")
#         # Set a custom user-agent for further stealth if needed
#         chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " 
#                                     "(KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36")

#         # Cache ChromeDriver in a local folder to avoid re-downloads
#         driver = webdriver.Chrome(service=Service(ChromeDriverManager(path=".chromedriver").install()),
#                                   options=chrome_options)

#         stealth(driver,
#                 languages=["en-US", "en"],
#                 vendor="Google Inc.",
#                 platform="Win32",
#                 webgl_vendor="Intel Inc.",
#                 renderer="Intel Iris OpenGL Engine",
#                 fix_hairline=True,
#                 )
#         return driver

#     def fetch_censys_html(self):
#         retries = 0
#         url = f"{self.base_url}{self.clean_ip}"

#         while retries < self.max_retries:
#             try:
#                 logger.info(f"[Censys] Attempting fetch for {self.clean_ip} (try {retries + 1})")
#                 driver = self._get_driver()
#                 driver.get(url)
#                 WebDriverWait(driver, 20).until(
#                     EC.presence_of_element_located((By.TAG_NAME, "body"))
#                 )
#                 # Allow extra time for JS-rendered content
#                 time.sleep(3)
#                 html = driver.page_source
#                 driver.quit()

#                 # Check for error strings in the HTML
#                 if any(x in html for x in ["Host not found", "Rate limit", "Access denied"]):
#                     logger.warning("Censys returned error content")
#                     return None
#                 return html

#             except Exception as e:
#                 logger.warning(f"Error fetching Censys HTML (attempt {retries + 1}/{self.max_retries}): {e}")
#                 retries += 1
#                 time.sleep(2 ** retries)

#         logger.error(f"Failed to fetch Censys HTML after {self.max_retries} attempts for {self.clean_ip}")
#         return None

#     def parse_html_to_structured_data(self, html):
#         soup = BeautifulSoup(html, "html.parser")

#         # Utility function to safely extract text from a selector
#         def safe_text(selector):
#             el = soup.select_one(selector)
#             return el.text.strip() if el else None

#         # Find a section by matching its h2 title
#         def get_section_by_title(title):
#             for section in soup.select("section"):
#                 h2 = section.select_one("h2")
#                 if h2 and title.lower() in h2.text.lower():
#                     return section
#             return None

#         # Extract key-value pairs from a section (for Infrastructure, TLS, etc.)
#         def extract_kv(section):
#             data = {}
#             if not section:
#                 return data
#             for row in section.select("div.grid div.flex"):
#                 try:
#                     key = row.select_one("div.text-sm")
#                     value = row.select_one("div.truncate")
#                     if key:
#                         data[key.text.strip()] = value.text.strip() if value else ""
#                 except Exception as e:
#                     logger.debug(f"Error parsing key-value pair: {e}")
#             return data

#         # Flexible datetime parser using dateutil (e.g., "May 10, 2025 21:09 UTC")
#         def parse_datetime(value):
#             try:
#                 return date_parser.parse(value)
#             except Exception as e:
#                 logger.debug(f"Error parsing datetime '{value}': {e}")
#                 return None

#         # Extract comma-separated lists (for hostnames, domains, tags, vulnerabilities)
#         def extract_comma_list(label):
#             dt = soup.find("dt", string=label)
#             if dt:
#                 dd = dt.find_next_sibling("dd")
#                 if dd:
#                     return [span.text.strip() for span in dd.find_all("span")]
#             return []

#         # Extract geolocation coordinates by regex looking for "° N, ...° E"
#         def extract_geo(soup):
#             lat = None
#             lon = None
#             text = soup.get_text()
#             match = re.search(r'([-+]?[0-9]*\.?[0-9]+)°\s*N,\s*([-+]?[0-9]*\.?[0-9]+)°\s*E', text)
#             if match:
#                 try:
#                     lat = float(match.group(1))
#                     lon = float(match.group(2))
#                 except Exception as ex:
#                     logger.debug(f"Error converting geo-coordinates: {ex}")
#             return lat, lon

#         censys_data = {
#             "ip": safe_text("h1.text-lg.font-semibold") or self.clean_ip,
#         }

#         infra = extract_kv(get_section_by_title("Infrastructure"))
#         tls = extract_kv(get_section_by_title("TLS Certificates")) or {}

#         # Parse geolocation from any mention of lat/lon in the page content
#         lat, lon = extract_geo(soup)

#         censys_data.update({
#             "asn": int(infra.get("ASN", "").replace("AS", "")) if "ASN" in infra and infra.get("ASN").startswith("AS") else None,
#             "asn_name": infra.get("Organization"),
#             "asn_country_code": infra.get("Country Code"),
#             "asn_description": infra.get("ASN Name"),
#             "location_city": infra.get("City"),
#             "location_country": infra.get("Country"),
#             "latitude": lat,
#             "longitude": lon,
#             "tls_issuer": tls.get("Issuer"),
#             "tls_subject": tls.get("Subject"),
#             "tls_not_before": parse_datetime(tls.get("Not Before")),
#             "tls_not_after": parse_datetime(tls.get("Not After")),
#         })

#         services = []
#         protocols = []
#         # Update services extraction; use try/except in case elements are missing
#         service_blocks = soup.select("div#services div.flex.flex-col.space-y-6 > div")
#         if service_blocks:
#             for block in service_blocks:
#                 try:
#                     proto_el = block.select_one("div.text-sm.text-gray-500")
#                     name_el = block.select_one("h3")
#                     proto = proto_el.text.strip() if proto_el else None
#                     name = name_el.text.strip() if name_el else None
#                     banner_el = block.select_one("pre")
#                     banner = banner_el.text.strip() if banner_el else None

#                     if proto or name:
#                         services.append({
#                             "port_protocol": proto,
#                             "service": name,
#                             "banner": banner
#                         })
#                         if proto:
#                             protocols.append(proto)
#                 except Exception as e:
#                     logger.debug(f"Error extracting service: {e}")
#         else:
#             logger.debug("No service blocks found, check selector and page layout.")

#         censys_data["services"] = services
#         censys_data["protocols"] = protocols
#         censys_data["hostnames"] = extract_comma_list("Hostnames")
#         censys_data["domains"] = extract_comma_list("Domains")
#         censys_data["tags"] = extract_comma_list("Tags")
#         censys_data["vulnerabilities"] = extract_comma_list("Vulnerabilities")

#         # Extract and parse the "Last Seen" timestamp
#         last_seen_dt = soup.find("dt", string="Last Seen")
#         if last_seen_dt:
#             last_seen_text = last_seen_dt.find_next_sibling("dd").text.strip()
#             censys_data["last_updated"] = parse_datetime(last_seen_text)
#         else:
#             censys_data["last_updated"] = None

#         # Save the raw data for debugging and future reference
#         censys_data["raw_data"] = {
#             "infra": infra,
#             "tls": tls,
#             "services": services,
#         }
#         return censys_data

#     async def save_censys_info(self, data):
#         ip = data.get("ip")
#         if not ip:
#             logger.error("No IP found; cannot save Censys data.")
#             return

#         # Calculate the integer representation of the IP
#         try:
#             ip_int = int(ipaddress.ip_address(ip))
#         except Exception as ex:
#             logger.debug(f"Error converting IP to int: {ex}")
#             ip_int = None

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
#                 "hostnames": json.dumps(data.get("hostnames", [])),
#                 "domains": json.dumps(data.get("domains", [])),
#                 "tags": json.dumps(data.get("tags", [])),
#                 "vulnerabilities": json.dumps(data.get("vulnerabilities", [])),
#                 "last_updated": data.get("last_updated"),
#                 "raw_data": data.get("raw_data"),
#                 "source": "censys",
#                 "collection_status": "success",
#                 # Store the converted IP integer if needed
#                 "ip_int": ip_int,
#             }
#         )
#         logger.info(f"Censys data saved for target {self.target_id} ({ip})")

#     async def run(self):
#         try:
#             await self._get_target()
#             html = self.fetch_censys_html()
#             if not html:
#                 return {"status": "error", "message": "Failed to fetch or received invalid HTML"}
#             parsed = self.parse_html_to_structured_data(html)
#             if not parsed:
#                 return {"status": "error", "message": "Failed to parse HTML"}
#             await self.save_censys_info(parsed)
#             return {"status": "success", "message": "Censys data collected"}
#         except Exception as e:
#             logger.exception("Error in CensysCollector.run:")
#             return {"status": "error", "message": str(e)}



# import logging
# import os
# import json
# import time
# import re
# import ipaddress
# from datetime import datetime
# from dateutil import parser as date_parser  # New: for flexible datetime parsing
# from asgiref.sync import sync_to_async
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from django.shortcuts import get_object_or_404
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium_stealth import stealth
# from webdriver_manager.chrome import ChromeDriverManager
# from InformationGathering.models import Target, CensysInfo

# logger = logging.getLogger(__name__)
# load_dotenv()

# class CensysCollector:
#     def __init__(self, target_id, debug=False, max_retries=3):
#         self.target_id = target_id
#         self.target = None
#         self.clean_ip = None
#         self.base_url = "https://search.censys.io/host/"
#         self.debug = debug
#         self.max_retries = max_retries

#     async def _get_target(self):
#         if not self.target:
#             self.target = await sync_to_async(get_object_or_404)(Target, id=self.target_id)
#             # Extract clean IP (ignoring port information if present)
#             self.clean_ip = self.target.host.split(":")[1] if ":" in self.target.host else self.target.host
#         return self.target

#     def _get_driver(self):
#         chrome_options = Options()
#         # Optional: Toggle headless mode via environment (recommended for debugging)
#         if os.getenv("HEADLESS", "False").lower() in ["true", "1"]:
#             chrome_options.add_argument("--headless")
#         chrome_options.add_argument("--disable-blink-features=AutomationControlled")
#         chrome_options.add_argument("--no-sandbox")
#         chrome_options.add_argument("--disable-dev-shm-usage")
#         chrome_options.add_argument("--disable-gpu")
#         chrome_options.add_argument("--window-size=1920,1080")
#         # Set a custom user-agent for further stealth if needed
#         chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
#                                     "(KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36")

#         # Cache ChromeDriver in a local folder to avoid re-downloads
#         driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

#         stealth(driver,
#                 languages=["en-US", "en"],
#                 vendor="Google Inc.",
#                 platform="Win32",
#                 webgl_vendor="Intel Inc.",
#                 renderer="Intel Iris OpenGL Engine",
#                 fix_hairline=True,
#                 )
#         return driver

#     def fetch_censys_html(self):
#         retries = 0
#         url = f"{self.base_url}{self.clean_ip}"

#         while retries < self.max_retries:
#             driver = None  # Initialize driver variable early
#             try:
#                 logger.info(f"[Censys] Attempting fetch for {self.clean_ip} (try {retries + 1})")
#                 driver = self._get_driver()
#                 driver.get(url)
#                 WebDriverWait(driver, 20).until(
#                     EC.presence_of_element_located((By.TAG_NAME, "body"))
#                 )
#                 time.sleep(3)
#                 html = driver.page_source

#                 # Print the HTML response for debugging purposes
#                 logger.info(f"HTML Response:\n{html}")

#                 # Don't call quit() yet — defer it to finally block
#                 if any(x in html for x in ["Host not found", "Rate limit", "Access denied"]):
#                     logger.warning("Censys returned error content")
#                     return None
#                 return html

#             except Exception as e:
#                 logger.warning(f"Error fetching Censys HTML (attempt {retries + 1}/{self.max_retries}): {e}")
#                 retries += 1
#                 time.sleep(2 ** retries)

#             finally:
#                 if driver:  # Only call quit if driver was initialized
#                     driver.quit()

#         logger.error(f"Failed to fetch Censys HTML after {self.max_retries} attempts for {self.clean_ip}")
#         return None

#     def parse_html_to_structured_data(self, html):
#         soup = BeautifulSoup(html, "html.parser")

#         # Utility function to safely extract text from a selector
#         def safe_text(selector):
#             el = soup.select_one(selector)
#             return el.text.strip() if el else None

#         # Find a section by matching its h2 title
#         def get_section_by_title(title):
#             for section in soup.select("section"):
#                 h2 = section.select_one("h2")
#                 if h2 and title.lower() in h2.text.lower():
#                     return section
#             return None

#         # Extract key-value pairs from a section (for Infrastructure, TLS, etc.)
#         def extract_kv(section):
#             data = {}
#             if not section:
#                 return data
#             for row in section.select("div.grid div.flex"):
#                 try:
#                     key = row.select_one("div.text-sm")
#                     value = row.select_one("div.truncate")
#                     if key:
#                         data[key.text.strip()] = value.text.strip() if value else ""
#                 except Exception as e:
#                     logger.debug(f"Error parsing key-value pair: {e}")
#             return data

#         # Flexible datetime parser using dateutil (e.g., "May 10, 2025 21:09 UTC")
#         def parse_datetime(value):
#             try:
#                 return date_parser.parse(value)
#             except Exception as e:
#                 logger.debug(f"Error parsing datetime '{value}': {e}")
#                 return None

#         # Extract comma-separated lists (for hostnames, domains, tags, vulnerabilities)
#         def extract_comma_list(label):
#             dt = soup.find("dt", string=label)
#             if dt:
#                 dd = dt.find_next_sibling("dd")
#                 if dd:
#                     return [span.text.strip() for span in dd.find_all("span")]
#             return []

#         # Extract geolocation coordinates by regex looking for "° N, ...° E"
#         def extract_geo(soup):
#             lat = None
#             lon = None
#             text = soup.get_text()
#             match = re.search(r'([-+]?[0-9]*\.?[0-9]+)°\s*N,\s*([-+]?[0-9]*\.?[0-9]+)°\s*E', text)
#             if match:
#                 try:
#                     lat = float(match.group(1))
#                     lon = float(match.group(2))
#                 except Exception as ex:
#                     logger.debug(f"Error converting geo-coordinates: {ex}")
#             return lat, lon

#         censys_data = {
#             "ip": safe_text("h1.text-lg.font-semibold") or self.clean_ip,
#         }

#         infra = extract_kv(get_section_by_title("Infrastructure"))
#         tls = extract_kv(get_section_by_title("TLS Certificates")) or {}

#         # Parse geolocation from any mention of lat/lon in the page content
#         lat, lon = extract_geo(soup)

#         censys_data.update({
#             "asn": int(infra.get("ASN", "").replace("AS", "")) if "ASN" in infra and infra.get("ASN").startswith("AS") else None,
#             "asn_name": infra.get("Organization"),
#             "asn_country_code": infra.get("Country Code"),
#             "asn_description": infra.get("ASN Name"),
#             "location_city": infra.get("City"),
#             "location_country": infra.get("Country"),
#             "latitude": lat,
#             "longitude": lon,
#             "tls_issuer": tls.get("Issuer"),
#             "tls_subject": tls.get("Subject"),
#             "tls_not_before": parse_datetime(tls.get("Not Before")),
#             "tls_not_after": parse_datetime(tls.get("Not After")),
#         })

#         services = []
#         protocols = []
#         service_blocks = soup.select("div#services div.flex.flex-col.space-y-6 > div")
#         if service_blocks:
#             for block in service_blocks:
#                 try:
#                     proto_el = block.select_one("div.text-sm.text-gray-500")
#                     name_el = block.select_one("h3")
#                     proto = proto_el.text.strip() if proto_el else None
#                     name = name_el.text.strip() if name_el else None
#                     banner_el = block.select_one("pre")
#                     banner = banner_el.text.strip() if banner_el else None

#                     if proto or name:
#                         services.append({
#                             "port_protocol": proto,
#                             "service": name,
#                             "banner": banner
#                         })
#                         if proto:
#                             protocols.append(proto)
#                 except Exception as e:
#                     logger.debug(f"Error extracting service: {e}")
#         else:
#             logger.debug("No service blocks found, check selector and page layout.")

#         censys_data["services"] = services
#         censys_data["protocols"] = protocols
#         censys_data["hostnames"] = extract_comma_list("Hostnames")
#         censys_data["domains"] = extract_comma_list("Domains")
#         censys_data["tags"] = extract_comma_list("Tags")
#         censys_data["vulnerabilities"] = extract_comma_list("Vulnerabilities")

#         # Extract and parse the "Last Seen" timestamp
#         last_seen_dt = soup.find("dt", string="Last Seen")
#         if last_seen_dt:
#             last_seen_text = last_seen_dt.find_next_sibling("dd").text.strip()
#             censys_data["last_updated"] = parse_datetime(last_seen_text)
#         else:
#             censys_data["last_updated"] = None

#         censys_data["raw_data"] = {
#             "infra": infra,
#             "tls": tls,
#             "services": services,
#         }

#         # Save the structured data as JSON
#         with open(f"censys_data_{self.clean_ip}.json", "w") as json_file:
#             json.dump(censys_data, json_file, indent=4)

#         return censys_data

#     async def save_censys_info(self, data):
#         ip = data.get("ip")
#         if not ip:
#             logger.error("No IP found; cannot save Censys data.")
#             return

#         # Calculate the integer representation of the IP
#         try:
#             ip_int = int(ipaddress.ip_address(ip))
#         except Exception as ex:
#             logger.debug(f"Error converting IP to int: {ex}")
#             ip_int = None

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
#                 "hostnames": json.dumps(data.get("hostnames", [])),
#                 "domains": json.dumps(data.get("domains", [])),
#                 "tags": json.dumps(data.get("tags", [])),
#                 "vulnerabilities": json.dumps(data.get("vulnerabilities", [])),
#                 "last_updated": data.get("last_updated"),
#                 "raw_data": data.get("raw_data"),
#                 "source": "censys",
#                 "collection_status": "success",
#                 # Store the converted IP integer if needed
#                 "ip_int": ip_int,
#             }
#         )
#         logger.info(f"Censys data saved for target {self.target_id} ({ip})")

#     async def run(self):
#         try:
#             await self._get_target()
#             html = self.fetch_censys_html()
#             if not html:
#                 return {"status": "error", "message": "Failed to fetch or received invalid HTML"}
#             parsed = self.parse_html_to_structured_data(html)
#             if not parsed:
#                 return {"status": "error", "message": "Failed to parse HTML"}
#             await self.save_censys_info(parsed)
#             return {"status": "success", "message": "Censys data collected"}
#         except Exception as e:
#             logger.exception("Error in CensysCollector.run:")
#             return {"status": "error", "message": str(e)}




# import logging
# import os
# import json
# import time
# import re
# import ipaddress
# from datetime import datetime
# from dateutil import parser as date_parser
# from asgiref.sync import sync_to_async
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from django.shortcuts import get_object_or_404
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium_stealth import stealth
# from webdriver_manager.chrome import ChromeDriverManager
# from InformationGathering.models import Target, CensysInfo
# import tempfile
# from googlesearch import search

# results = search("site:censys.io 8.8.8.8")
# for result in results:
#     print(result)


# logger = logging.getLogger(__name__)
# load_dotenv()

# class CensysCollector:
#     def __init__(self, target_id, debug=False, max_retries=3):
#         self.target_id = target_id
#         self.target = None
#         self.clean_ip = None
#         self.base_url = "https://search.censys.io/host/"
#         self.debug = debug
#         self.max_retries = max_retries


#     async def _get_target(self):
#         if not self.target:
#             self.target = await sync_to_async(get_object_or_404)(Target, id=self.target_id)
#             self.clean_ip = self.target.host.split(":")[1] if ":" in self.target.host else self.target.host
#         return self.target
    
#     # def _get_driver(self):
#     #     chrome_options = Options()
#     #     if os.getenv("HEADLESS", "False").lower() in ["true", "1"]:
#     #         chrome_options.add_argument("--headless=new")
#     #     chrome_options.add_argument("--disable-blink-features=AutomationControlled")
#     #     chrome_options.add_argument("--no-sandbox")
#     #     chrome_options.add_argument("--disable-dev-shm-usage")
#     #     chrome_options.add_argument("--disable-gpu")
#     #     chrome_options.add_argument("--window-size=1920,1080")
#     #     chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36")

#     # # إضافة مجلد مؤقت كـ user-data-dir لتجنب التعارض
#     #     user_data_dir = tempfile.mkdtemp()
#     #     chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

#     #     proxy = os.getenv("CHROME_PROXY")
#     #     if proxy:
#     #         chrome_options.add_argument(f"--proxy-server={proxy}")

#     #     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

#     #     stealth(driver,
#     #             languages=["en-US", "en"],
#     #             vendor="Google Inc.",
#     #             platform="Win32",
#     #             webgl_vendor="Intel Inc.",
#     #             renderer="Intel Iris OpenGL Engine",
#     #             fix_hairline=True)
#     #     return driver


#     def fetch_censys_html(self):
#         retries = 0
#         url = f"{self.base_url}{self.clean_ip}"

#         while retries < self.max_retries:
#             driver = None
#             try:
#                 logger.info(f"[Censys] Fetching {self.clean_ip} (attempt {retries + 1})")
#                 options = webdriver.ChromeOptions()
#                 options.add_argument("--start-maximized")
#                 driver = webdriver.Chrome(options=options)
#                 driver.get(url)
#                 WebDriverWait(driver, 20).until(
#                     EC.presence_of_element_located((By.CSS_SELECTOR, "h1.text-lg.font-semibold"))
#                 )
#                 time.sleep(2)
#                 html = driver.page_source
#                 if any(x in html for x in ["Host not found", "Rate limit", "Access denied"]):
#                     logger.warning("Censys returned error content")
#                     return None
#                 return html
#             except Exception as e:
#                 logger.warning(f"Error fetching Censys HTML (try {retries + 1}): {e}")
#                 retries += 1
#                 time.sleep(2 ** retries)
#             finally:
#                 if driver:
#                     driver.quit()

#         logger.error(f"Failed to fetch HTML after {self.max_retries} attempts for {self.clean_ip}")
#         return None

#     def parse_html_to_structured_data(self, html):
#         soup = BeautifulSoup(html, "html.parser")

#         def safe_text(selector):
#             el = soup.select_one(selector)
#             return el.text.strip() if el else None

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
#                     key = row.select_one("div.text-sm")
#                     value = row.select_one("div.truncate")
#                     if key:
#                         data[key.text.strip()] = value.text.strip() if value else ""
#                 except Exception as e:
#                     logger.debug(f"Error parsing KV: {e}")
#             return data

#         def parse_datetime(value):
#             try:
#                 return date_parser.parse(value)
#             except Exception as e:
#                 logger.debug(f"Datetime parse error: {e}")
#                 return None

#         def extract_geo():
#             text = soup.get_text()
#             match = re.search(r'([-+]?\d*\.\d+)\u00B0\s*N,\s*([-+]?\d*\.\d+)\u00B0\s*E', text)
#             if match:
#                 return float(match.group(1)), float(match.group(2))
#             return None, None

#         data = {"ip": safe_text("h1.text-lg.font-semibold") or self.clean_ip}
#         infra = extract_kv(get_section_by_title("Infrastructure"))
#         tls = extract_kv(get_section_by_title("TLS Certificates"))
#         lat, lon = extract_geo()

#         data.update({
#             "asn": int(infra.get("ASN", "").replace("AS", "")) if infra.get("ASN", "").startswith("AS") else None,
#             "asn_name": infra.get("Organization"),
#             "asn_country_code": infra.get("Country Code"),
#             "asn_description": infra.get("ASN Name"),
#             "location_city": infra.get("City"),
#             "location_country": infra.get("Country"),
#             "latitude": lat,
#             "longitude": lon,
#             "tls_issuer": tls.get("Issuer"),
#             "tls_subject": tls.get("Subject"),
#             "tls_not_before": parse_datetime(tls.get("Not Before")),
#             "tls_not_after": parse_datetime(tls.get("Not After"))
#         })

#         return data

#     async def save_censys_info(self, data):
#         ip = data.get("ip")
#         if not ip:
#             logger.error("No IP found to save")
#             return

#         try:
#             ip_int = int(ipaddress.ip_address(ip))
#         except Exception as ex:
#             logger.debug(f"IP to int error: {ex}")
#             ip_int = None

#         await sync_to_async(CensysInfo.objects.update_or_create)(
#             target_id=self.target_id,
#             ip=ip,
#             defaults={
#                 **data,
#                 "hostnames": json.dumps(data.get("hostnames", [])),
#                 "domains": json.dumps(data.get("domains", [])),
#                 "tags": json.dumps(data.get("tags", [])),
#                 "vulnerabilities": json.dumps(data.get("vulnerabilities", [])),
#                 "raw_data": data,
#                 "source": "censys",
#                 "collection_status": "success",
#                 "ip_int": ip_int,
#             }
#         )

#     async def run(self):
#         try:
#             await self._get_target()
#             html = self.fetch_censys_html()
#             if not html:
#                 return {"status": "error", "message": "Failed to fetch HTML"}
#             parsed = self.parse_html_to_structured_data(html)
#             await self.save_censys_info(parsed)
#             return {"status": "success", "message": "Censys data collected"}
#         except Exception as e:
#             logger.exception("Error in CensysCollector.run")
#             return {"status": "error", "message": str(e)}




# import aiohttp
# from bs4 import BeautifulSoup
# import logging

# logger = logging.getLogger(__name__)


# class CensysCollector:
#     def __init__(self, target_id):
#         self.target_id = target_id
#         self.base_url = "https://search.censys.io/host/"

#     async def fetch_censys_html(self, ip):
#         try:
#             async with aiohttp.ClientSession() as session:
#                 url = f"{self.base_url}{ip}"
#                 headers = {
#                     "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari/537.36"
#                 }
#                 async with session.get(url, headers=headers, timeout=30) as resp:
#                     if resp.status == 200:
#                         return await resp.text()
#                     else:
#                         logger.warning(f"Censys returned status {resp.status} for IP {ip}")
#                         return None
#         except Exception as e:
#             logger.exception(f"Failed to fetch Censys HTML for {ip}")
#             return None

#     def parse_html_to_structured_data(self, html):
#         try:
#             soup = BeautifulSoup(html, "html.parser")
#             result = {}

#             ip_elem = soup.select_one("h1[data-testid='ip-title']")
#             result["ip"] = ip_elem.text.strip() if ip_elem else None

#             asn_elem = soup.find("a", href=lambda x: x and "/as/" in x)
#             result["asn"] = asn_elem.text.strip() if asn_elem else None

#             location_elem = soup.select_one("div[data-testid='location']")
#             result["location"] = location_elem.text.strip() if location_elem else None

#             provider_elem = soup.find("div", text="Cloud Provider")
#             if provider_elem:
#                 result["cloud_provider"] = provider_elem.find_next("div").text.strip()

#             # Extract open ports
#             port_cards = soup.select("div[data-testid='port-card']")
#             ports = []
#             for card in port_cards:
#                 port_info = {}
#                 port_number_elem = card.select_one("span[data-testid='port-number']")
#                 service_elem = card.select_one("div[data-testid='service-name']")
#                 if port_number_elem and service_elem:
#                     port_info["port"] = port_number_elem.text.strip()
#                     port_info["service"] = service_elem.text.strip()
#                     ports.append(port_info)
#             result["ports"] = ports

#             return result
#         except Exception as e:
#             logger.exception("Error parsing Censys HTML")
#             return None

#     async def save_censys_info(self, data):
#         from InformationGathering.models import CensysInfo

#         ip_int = data.get("ip")
#         if not ip_int:
#             return

#         await CensysInfo.objects.aupdate_or_create(
#             target_id=self.target_id,
#             ip_int=ip_int,
#             defaults={
#                 "raw_data": data,
#                 "source": "censys",
#                 "collection_status": "success",
#             }
#         )
#         logger.info(f"Censys data saved for target {self.target_id} ({ip_int})")

#     async def run(self):
#         try:
#             target = await self._get_target()
#             ip = target.ip
#             html = await self.fetch_censys_html(ip)
#             if not html:
#                 return {"status": "error", "message": "Failed to fetch or received invalid HTML"}

#             parsed = self.parse_html_to_structured_data(html)
#             if not parsed:
#                 return {"status": "error", "message": "Censys HTML parsing failed"}

#             await self.save_censys_info(parsed)
#             return {"status": "success", "message": "Censys HTML data collected"}
#         except Exception as e:
#             logger.exception("Error in CensysCollector run")
#             return {"status": "error", "message": str(e)}

#     async def _get_target(self):
#         from models import Target
#         return await Target.objects.aget(id=self.target_id)



import logging
import os
import json
import time
import re
import ipaddress
from datetime import datetime
from dateutil import parser as date_parser
from asgiref.sync import sync_to_async
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from django.shortcuts import get_object_or_404
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
from InformationGathering.models import Target, CensysInfo

# Allow running Firefox as root
os.environ['MOZ_ALLOW_ROOT'] = '1'

logger = logging.getLogger(__name__)
load_dotenv()

class CensysCollector:
    def __init__(self, target_id, debug=False, max_retries=3):
        self.target_id = target_id
        self.target = None
        self.clean_ip = None
        self.base_url = "https://search.censys.io/hosts/"
        self.debug = debug
        self.max_retries = max_retries

    async def _get_target(self):
        if not self.target:
            self.target = await sync_to_async(get_object_or_404)(Target, id=self.target_id)
            self.clean_ip = self.target.host.split(":")[1] if ":" in self.target.host else self.target.host
        return self.target

    def _get_driver(self):
        options = Options()
        options.headless = True
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--width=1920")
        options.add_argument("--height=1080")
        # You can add user-agent if needed:
        # options.set_preference("general.useragent.override", "Mozilla/5.0 ...")

        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        return driver

    def fetch_censys_html(self):
        retries = 0
        url = f"{self.base_url}{self.clean_ip}"

        while retries < self.max_retries:
            driver = None
            try:
                logger.info(f"[Censys] Fetching {self.clean_ip} (attempt {retries + 1})")
                driver = self._get_driver()
                driver.get(url)

            # انتظار ظهور العنوان الرئيسي (مثلاً)
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.text-lg.font-semibold"))
                )

            # --- هنا ننتظر ظهور عنصر التحقق ---
                verification_selector = "button.verify-btn"  # مثال: عدّل حسب العنصر الصحيح
                verification_element = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, verification_selector))
                )

            # نضغط عليه مرتين بفاصل زمني
                verification_element.click()
                time.sleep(3)  # فاصل 3 ثواني بين الضغطتين
                verification_element.click()

                time.sleep(3)  # ننتظر الصفحة لتحديث المحتوى بعد التحقق

                html = driver.page_source

                if any(x in html for x in ["Host not found", "Rate limit", "Access denied"]):
                    logger.warning("Censys returned error content")
                    return None
                return html
            except Exception as e:
                logger.warning(f"Error fetching Censys HTML (try {retries + 1}): {e}")
                retries += 1
                time.sleep(2 ** retries)
            finally:
                if driver:
                    driver.quit()

        logger.error(f"Failed to fetch HTML after {self.max_retries} attempts for {self.clean_ip}")
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
                    key = row.select_one("div.text-sm")
                    value = row.select_one("div.truncate")
                    if key:
                        data[key.text.strip()] = value.text.strip() if value else ""
                except Exception as e:
                    logger.debug(f"Error parsing KV: {e}")
            return data

        def parse_datetime(value):
            try:
                return date_parser.parse(value)
            except Exception as e:
                logger.debug(f"Datetime parse error: {e}")
                return None

        def extract_geo():
            text = soup.get_text()
            match = re.search(r'([-+]?\d*\.\d+)\u00B0\s*N,\s*([-+]?\d*\.\d+)\u00B0\s*E', text)
            if match:
                return float(match.group(1)), float(match.group(2))
            return None, None

        data = {"ip": safe_text("h1.text-lg.font-semibold") or self.clean_ip}
        infra = extract_kv(get_section_by_title("Infrastructure"))
        tls = extract_kv(get_section_by_title("TLS Certificates"))
        lat, lon = extract_geo()

        data.update({
            "asn": int(infra.get("ASN", "").replace("AS", "")) if infra.get("ASN", "").startswith("AS") else None,
            "asn_name": infra.get("Organization"),
            "asn_country_code": infra.get("Country Code"),
            "asn_description": infra.get("ASN Name"),
            "location_city": infra.get("City"),
            "location_country": infra.get("Country"),
            "latitude": lat,
            "longitude": lon,
            "tls_issuer": tls.get("Issuer"),
            "tls_subject": tls.get("Subject"),
            "tls_not_before": parse_datetime(tls.get("Not Before")),
            "tls_not_after": parse_datetime(tls.get("Not After"))
        })

        return data

    async def save_censys_info(self, data):
        ip = data.get("ip")
        if not ip:
            logger.error("No IP found to save")
            return

        try:
            ip_int = int(ipaddress.ip_address(ip))
        except Exception as ex:
            logger.debug(f"IP to int error: {ex}")
            ip_int = None

        await sync_to_async(CensysInfo.objects.update_or_create)(
            target_id=self.target_id,
            ip=ip,
            defaults={
                **data,
                "hostnames": json.dumps(data.get("hostnames", [])),
                "domains": json.dumps(data.get("domains", [])),
                "tags": json.dumps(data.get("tags", [])),
                "vulnerabilities": json.dumps(data.get("vulnerabilities", [])),
                "raw_data": data,
                "source": "censys",
                "collection_status": "success",
                "ip_int": ip_int,
            }
        )

    async def run(self):
        try:
            await self._get_target()
            html = self.fetch_censys_html()
            if not html:
                return {"status": "error", "message": "Failed to fetch HTML"}
            parsed = self.parse_html_to_structured_data(html)
            await self.save_censys_info(parsed)
            return {"status": "success", "message": "Censys data collected"}
        except Exception as e:
            logger.exception("Error in CensysCollector.run")
            return {"status": "error", "message": str(e)}
