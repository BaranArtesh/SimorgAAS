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
# from InformationGathering.models import Target, ZmapScan # Ensure you have a ZMapInfo model

# logger = logging.getLogger(__name__)
# load_dotenv()

# class ZMapCollector:
#     def __init__(self, target_id, debug=False, max_retries=3):
#         self.target_id = target_id
#         self.target = None
#         self.clean_ip = None
#         self.base_url = "https://zmap.io/" # Replace with actual source
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
#             )
#         }

#     async def fetch_zmap_html(self):
#         url = f"{self.base_url}{self.clean_ip}.html"  # Static file naming convention
#         retries = 0
#         delay = 2

#         while retries < self.max_retries:
#             try:
#                 async with aiohttp.ClientSession(headers=self._headers()) as session:
#                     logger.info(f"Fetching ZMap HTML for {self.clean_ip} (try {retries + 1})")
#                     async with session.get(url, proxy=self.proxy, timeout=30) as resp:
#                         if resp.status == 200:
#                             html = await resp.text()
#                             if self.debug:
#                                 with open(f"debug_zmap_{self.clean_ip}.html", "w", encoding="utf-8") as f:
#                                     f.write(html)
#                             return html
#                         else:
#                             logger.warning(f"ZMap returned status {resp.status} for {self.clean_ip}")
#             except aiohttp.ClientProxyConnectionError as e:
#                 logger.error(f"Proxy error while connecting to ZMap source for {self.clean_ip}: {e}")
#             except Exception as e:
#                 logger.warning(f"Attempt {retries + 1} failed for {self.clean_ip}: {e}")

#             retries += 1
#             time.sleep(delay)
#             delay *= 2

#         logger.error(f"Failed to fetch ZMap HTML after {self.max_retries} attempts for {self.clean_ip}")
#         return None

#     def parse_html_to_structured_data(self, html):
#         soup = BeautifulSoup(html, "html.parser")

#         open_ports = []
#         for row in soup.select("table#ports tr")[1:]:  # assuming there's a table with id="ports"
#             try:
#                 cols = row.find_all("td")
#                 if len(cols) >= 2:
#                     port = cols[0].text.strip()
#                     service = cols[1].text.strip()
#                     open_ports.append({"port": port, "service": service})
#             except Exception as e:
#                 logger.debug(f"Error parsing row: {e}")

#         return {
#             "ip": self.clean_ip,
#             "open_ports": open_ports,
#             "raw_data": {
#                 "html_snippet": html[:1000]  # optional partial storage
#             }
#         }

#     async def save_zmap_info(self, data):
#         ip = data.get("ip")
#         if not ip:
#             logger.error("No IP found; cannot save ZMap data.")
#             return

#         await sync_to_async(ZmapScan.objects.update_or_create)(
#             target_id=self.target_id,
#             ip=ip,
#             defaults={
#                 "open_ports": json.dumps(data.get("open_ports", [])),
#                 "raw_data": data.get("raw_data"),
#                 "source": "zmap",
#                 "collection_status": "success",
#             }
#         )
#         logger.info(f"ZMap data saved for target {self.target_id} ({ip})")

#     async def run(self):
#         try:
#             await self._get_target()
#             html = await self.fetch_zmap_html()
#             if not html:
#                 return {"status": "error", "message": "Failed to fetch ZMap HTML"}
#             parsed = self.parse_html_to_structured_data(html)
#             if not parsed:
#                 return {"status": "error", "message": "Failed to parse ZMap HTML"}
#             await self.save_zmap_info(parsed)
#             return {"status": "success", "message": "ZMap data collected"}
#         except Exception as e:
#             logger.exception("Error in ZMapCollector.run:")
#             return {"status": "error", "message": str(e)}
