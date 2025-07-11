import aiohttp
import gzip
import json
import logging
import os
from django.conf import settings
from ..models import Target, ProjectSonarData


logger = logging.getLogger(__name__)

class ProjectSonarCollector:
    BASE_URL = "https://opendata.rapid7.com"
    DATASETS = {
        "fdns": "sonar.fdns_v2",             # Forward DNS
        "rdns": "sonar.rdns_v2",             # Reverse DNS
        "http": "sonar.http",                # HTTP banners
        "ssl": "sonar.ssl",                  # SSL/TLS certs
    }

    def __init__(self, target_id):
        self.target_id = target_id
        self.target = Target.objects.get(id=target_id)
        self.ip = self.target.ip_address
        self.domain = self.target.domain

    async def run(self):
        try:
            for name, dataset in self.DATASETS.items():
                url = await self.get_latest_dataset_url(dataset)
                if url:
                    entries = await self.download_and_parse(url)
                    matched = self.extract_relevant_entries(entries)
                    self.save_to_db(name, matched)
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error in ProjectSonarCollector for {self.target}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def get_latest_dataset_url(self, dataset):
        try:
            index_url = f"{self.BASE_URL}/{dataset}/"
            async with aiohttp.ClientSession() as session:
                async with session.get(index_url) as resp:
                    html = await resp.text()
                    filenames = [line.split('href="')[1].split('"')[0] for line in html.splitlines() if '.json.gz' in line]
                    latest_file = sorted(filenames)[-1]
                    return f"{index_url}{latest_file}"
        except Exception as e:
            logger.warning(f"Could not find latest dataset for {dataset}: {e}")
            return None

    async def download_and_parse(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to download {url}")
                compressed_data = await resp.read()
                decompressed = gzip.decompress(compressed_data)
                return [json.loads(line) for line in decompressed.splitlines()]

    def extract_relevant_entries(self, entries):
        filtered = []
        for entry in entries:
            if self.ip and self.ip in str(entry):
                filtered.append(entry)
            elif self.domain and self.domain in str(entry):
                filtered.append(entry)
        return filtered

    def save_to_db(self, dataset_name, entries):
        if not entries:
            logger.info(f"No relevant {dataset_name} entries for target {self.target}")
            return

        ProjectSonarData.objects.create(
            target=self.target,
            dataset=dataset_name,
            entry_count=len(entries),
            data=entries
        )
        logger.info(f"Saved {len(entries)} {dataset_name} entries for target {self.target}")
