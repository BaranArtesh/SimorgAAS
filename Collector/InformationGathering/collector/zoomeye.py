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

os.environ['MOZ_ALLOW_ROOT'] = '1'
logger = logging.getLogger(__name__)
load_dotenv()

class ZoomEyeCollector:
    def __init__(self, target_id, debug=False, max_retries=3):
        self.target_id = target_id
        self.target = None
        self.clean_ip = None
        self.base_url = "https://www.zoomeye.org/searchResult?q=ip:"
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
        return webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)

    def fetch_zoomeye_html(self):
        retries = 0
        url = f"{self.base_url}{self.clean_ip}"

        while retries < self.max_retries:
            driver = None
            try:
                logger.info(f"[ZoomEye] Fetching {self.clean_ip} (attempt {retries + 1})")
                driver = self._get_driver()
                driver.get(url)

                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.host-info"))
                )

                html = driver.page_source
                if any(x in html for x in ["Rate limit", "Access denied", "Captcha"]):
                    logger.warning("ZoomEye returned error content")
                    return None
                return html
            except Exception as e:
                logger.warning(f"Error fetching ZoomEye HTML (try {retries + 1}): {e}")
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

        def extract_info_block():
            data = {}
            for block in soup.select("div.host-info ul li"):
                try:
                    key = block.select_one("strong")
                    value = block.get_text(separator=" ", strip=True).replace(key.text, "").strip() if key else ""
                    if key:
                        data[key.text.strip(": ")] = value
                except Exception as e:
                    logger.debug(f"Error extracting block: {e}")
            return data

        def parse_datetime(value):
            try:
                return date_parser.parse(value)
            except Exception as e:
                logger.debug(f"Datetime parse error: {e}")
                return None

        data = {
            "ip": self.clean_ip,
            "title": safe_text("div.host-info h4"),
        }

        metadata = extract_info_block()

        data.update({
            "asn": int(metadata.get("ASN", "").replace("AS", "")) if "ASN" in metadata else None,
            "asn_name": metadata.get("ISP"),
            "asn_country_code": metadata.get("Country Code"),
            "asn_description": metadata.get("Organization"),
            "location_city": metadata.get("City"),
            "location_country": metadata.get("Country"),
            "latitude": None,
            "longitude": None,
            "tls_issuer": metadata.get("TLS Issuer"),
            "tls_subject": metadata.get("TLS Subject"),
            "tls_not_before": parse_datetime(metadata.get("TLS Not Before", "")),
            "tls_not_after": parse_datetime(metadata.get("TLS Not After", ""))
        })

        return data

    async def save_zoomeye_info(self, data):
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
                "source": "zoomeye",
                "collection_status": "success",
                "ip_int": ip_int,
            }
        )

    async def run(self):
        try:
            await self._get_target()
            html = self.fetch_zoomeye_html()
            if not html:
                return {"status": "error", "message": "Failed to fetch HTML"}
            parsed = self.parse_html_to_structured_data(html)
            await self.save_zoomeye_info(parsed)
            return {"status": "success", "message": "ZoomEye data collected"}
        except Exception as e:
            logger.exception("Error in ZoomEyeCollector.run")
            return {"status": "error", "message": str(e)}
