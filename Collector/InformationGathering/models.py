from django.db import models
import json

class NmapScan(models.Model):
    target = models.ForeignKey('Target', related_name='nmap_scans', on_delete=models.CASCADE)
    scan_date = models.DateTimeField(auto_now_add=True)
    scan_type = models.CharField(max_length=50, choices=[('TCP', 'TCP Scan'), ('UDP', 'UDP Scan'), ('SYN', 'SYN Scan'), ('Full', 'Full Scan')])
    status = models.CharField(max_length=50, choices=[('Success', 'Success'), ('Failed', 'Failed')])
    scan_output = models.TextField(null=True, blank=True)
    scan_duration = models.FloatField(null=True, blank=True)
    scan_flags = models.JSONField(null=True, blank=True)
    open_ports = models.JSONField(null=True, blank=True)
    results = models.JSONField(null=True, blank=True)
    host_os = models.CharField(max_length=255, null=True, blank=True)
    os_detection_method = models.CharField(max_length=100, null=True, blank=True)
    os_accuracy = models.IntegerField(null=True, blank=True)
    is_vpn = models.BooleanField(default=False)

    def __str__(self):
        return f"Nmap Scan for {self.target.name} ({self.scan_type}) on {self.scan_date}"

    def process_scan_results(self, raw_data):
        self.scan_output = raw_data.get('output', '')
        self.scan_duration = raw_data.get('duration', 0)
        self.scan_flags = raw_data.get('flags', {})
        self.open_ports = raw_data.get('open_ports', [])
        self.results = raw_data.get('results', [])
        self.host_os = raw_data.get('host_os', '')
        self.os_detection_method = raw_data.get('os_detection_method', '')
        self.os_accuracy = raw_data.get('os_accuracy', 0)
        self.is_vpn = raw_data.get('is_vpn', False)

    def save_scan_data(self, raw_data):
        self.process_scan_results(raw_data)
        self.save()

class Target(models.Model):
    name = models.CharField(max_length=255, unique=True)
    host = models.GenericIPAddressField()
    type = models.CharField(max_length=50)
    is_local = models.BooleanField(default=False)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class User(models.Model):
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class WhoisInfo(models.Model):
    target = models.OneToOneField(Target, on_delete=models.CASCADE)
    domain_name = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    registrar = models.CharField(max_length=255, null=True, blank=True)
    whois_server = models.CharField(max_length=255, null=True, blank=True)
    referral_url = models.URLField(null=True, blank=True)
    updated_date = models.JSONField(null=True, blank=True)
    creation_date = models.DateTimeField(null=True, blank=True)
    expiration_date = models.DateTimeField(null=True, blank=True)
    name_servers = models.JSONField(null=True, blank=True)
    status = models.TextField(null=True, blank=True)
    emails = models.JSONField(null=True, blank=True)
    dnssec = models.CharField(max_length=50, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    org = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    registrant_postal_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"WHOIS for {self.target.name}"


class IPInfo(models.Model):
    target = models.ForeignKey('Target', related_name='ip_info', on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    asn = models.CharField(max_length=50, null=True, blank=True)
    asn_registry = models.CharField(max_length=100, null=True, blank=True)
    asn_cidr = models.CharField(max_length=100, null=True, blank=True)
    asn_country_code = models.CharField(max_length=2, null=True, blank=True)
    asn_date = models.DateField(null=True, blank=True)
    asn_description = models.TextField(null=True, blank=True)
    network_name = models.CharField(max_length=255, null=True, blank=True)
    network_handle = models.CharField(max_length=255, null=True, blank=True)
    network_status = models.CharField(max_length=50, null=True, blank=True)
    network_start_address = models.GenericIPAddressField(null=True, blank=True)
    network_end_address = models.GenericIPAddressField(null=True, blank=True)
    network_cidr = models.CharField(max_length=100, null=True, blank=True)
    network_type = models.CharField(max_length=100, null=True, blank=True)
    network_parent_handle = models.CharField(max_length=50, null=True, blank=True)
    org_name = models.CharField(max_length=255, null=True, blank=True)
    org_street = models.CharField(max_length=255, null=True, blank=True)
    org_city = models.CharField(max_length=100, null=True, blank=True)
    org_state = models.CharField(max_length=100, null=True, blank=True)
    org_postal_code = models.CharField(max_length=20, null=True, blank=True)
    org_country = models.CharField(max_length=100, null=True, blank=True)
    abuse_contact_name = models.CharField(max_length=255, null=True, blank=True)
    abuse_contact_email = models.EmailField(null=True, blank=True)
    abuse_contact_phone = models.CharField(max_length=50, null=True, blank=True)
    admin_contact_name = models.CharField(max_length=255, null=True, blank=True)
    admin_contact_email = models.EmailField(null=True, blank=True)
    noc_contact_name = models.CharField(max_length=255, null=True, blank=True)
    noc_contact_email = models.EmailField(null=True, blank=True)
    noc_contact_phone = models.CharField(max_length=50, null=True, blank=True)
    abuse_report_link = models.URLField(null=True, blank=True)
    whois_info_link = models.URLField(null=True, blank=True)
    terms_of_service_link = models.URLField(null=True, blank=True)
    geofeed_link = models.URLField(null=True, blank=True)
    network_ip_version = models.CharField(max_length=10, null=True, blank=True)
    admin_contact_phone = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"IP Info for {self.target.name} ({self.ip_address})"


# class ShodanInfo(models.Model):
#     target = models.ForeignKey('Target', related_name='shodan_scans', on_delete=models.CASCADE)
#     scan_date = models.DateTimeField(auto_now_add=True)

#     # Raw JSON blob of the Shodan API response
#     raw_data = models.JSONField(null=True, blank=True)

#     # Common summary fields
#     ip_str = models.GenericIPAddressField()                        # The IP that Shodan scanned
#     org = models.CharField(max_length=255, null=True, blank=True)  # Organization name
#     os = models.CharField(max_length=255, null=True, blank=True)   # Operating system fingerprint
#     isp = models.CharField(max_length=255, null=True, blank=True)  # ISP name
#     country_code = models.CharField(max_length=2, null=True, blank=True)
#     city = models.CharField(max_length=100, null=True, blank=True)
#     latitude = models.FloatField(null=True, blank=True)
#     longitude = models.FloatField(null=True, blank=True)
#     asn = models.CharField(max_length=100, null=True, blank=True)  # ASN

#     # Hostnames and domains
#     hostnames = models.JSONField(null=True, blank=True)            # List of hostnames
#     domains = models.JSONField(null=True, blank=True)              # List of domains

#     # Cloudflare-related data
#     cf_ray = models.CharField(max_length=255, null=True, blank=True)  # CF-Ray for tracing Cloudflare traffic
#     cf_cache_status = models.CharField(max_length=50, null=True, blank=True)  # Cache status
#     server_timing = models.TextField(null=True, blank=True)         # Server timing info

#     # Services and ports discovered (e.g. 80/http, 22/ssh)
#     ports = models.JSONField(null=True, blank=True)                # [80, 443, 22, …]
#     services = models.JSONField(null=True, blank=True)             # [{ "port": 80, "service": "http", … }, …]

#     # Vulnerabilities & exploits (if any)
#     vulnerabilities = models.JSONField(null=True, blank=True)      # ["CVE-2020-1234", …]

#     # SSL/TLS certificate details (optional)
#     ssl_issuer = models.CharField(max_length=255, null=True, blank=True)
#     ssl_subject = models.TextField(null=True, blank=True)
#     ssl_not_before = models.DateTimeField(null=True, blank=True)
#     ssl_not_after = models.DateTimeField(null=True, blank=True)

#     def __str__(self):
#         return f"Shodan scan for {self.target.name} @ {self.ip_str} on {self.scan_date}"


class ShodanInfo(models.Model):
    target = models.OneToOneField(Target, on_delete=models.CASCADE, related_name='shodan_info')
    ip = models.GenericIPAddressField()

    # General info fields
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    organization = models.CharField(max_length=255, blank=True, null=True)
    isp = models.CharField(max_length=255, blank=True, null=True)
    asn = models.CharField(max_length=100, blank=True, null=True)
    os = models.CharField(max_length=100, blank=True, null=True)
    hostnames = models.JSONField(null=True, blank=True)
    domains = models.JSONField(null=True, blank=True)
    tags = models.JSONField(null=True, blank=True)
    last_update = models.CharField(max_length=100, null=True, blank=True)
    vulnerabilities = models.JSONField(null=True, blank=True)


    # Ports and services stored as JSON strings
    open_ports = models.TextField(blank=True, default='[]')
    services = models.TextField(blank=True, default='[]')

    timestamp = models.DateTimeField(auto_now_add=True)

    def get_open_ports(self):
        return json.loads(self.open_ports)

    def set_open_ports(self, port_list):
        self.open_ports = json.dumps(port_list)

    def get_services(self):
        return json.loads(self.services)

    def set_services(self, service_list):
        self.services = json.dumps(service_list)

    def __str__(self):
        return f"ShodanInfo for {self.ip}"


class CensysInfo(models.Model):
    target = models.ForeignKey('Target', related_name='censys_scans', on_delete=models.CASCADE)
    scan_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(null=True, blank=True)

    ip = models.GenericIPAddressField()
    ip_int = models.BigIntegerField(null=True, blank=True)

    # Raw HTML and parsed JSON snapshot
    raw_data = models.JSONField(null=True, blank=True)  # Raw HTML parsed as JSON blob (preserve original page structure)
    services = models.JSONField(null=True, blank=True)  # Structured services per port, protocol, etc.
    protocols = models.JSONField(null=True, blank=True)

    # TLS/SSL certificate metadata
    tls_issuer = models.CharField(max_length=255, null=True, blank=True)
    tls_subject = models.TextField(null=True, blank=True)
    tls_not_before = models.DateTimeField(null=True, blank=True)
    tls_not_after = models.DateTimeField(null=True, blank=True)

    # ASN / routing metadata
    asn = models.IntegerField(null=True, blank=True)
    asn_name = models.CharField(max_length=255, null=True, blank=True)
    asn_description = models.TextField(null=True, blank=True)
    asn_country_code = models.CharField(max_length=2, null=True, blank=True)

    # Location metadata
    location_city = models.CharField(max_length=100, null=True, blank=True)
    location_country = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Host identifiers
    domains = models.JSONField(null=True, blank=True)
    hostnames = models.JSONField(null=True, blank=True)
    tags = models.JSONField(null=True, blank=True)
    vulnerabilities = models.JSONField(null=True, blank=True)

    # Source tracking and status
    collection_status = models.CharField(max_length=50, default='success')
    source = models.CharField(max_length=100, default='censys', blank=True)

    def __str__(self):
        return f"Censys scan for {self.target.name} @ {self.ip} on {self.scan_date}"



class ZoomEyeInfo(models.Model):
    target = models.ForeignKey(Target, related_name='zoomeye_scans', on_delete=models.CASCADE)
    scan_date = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField()

    # Host & network metadata
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    isp = models.CharField(max_length=255, blank=True, null=True)
    asn = models.CharField(max_length=100, blank=True, null=True)
    org = models.CharField(max_length=255, blank=True, null=True)
    os = models.CharField(max_length=100, blank=True, null=True)

    # DNS & domain metadata
    hostnames = models.JSONField(null=True, blank=True)
    domains = models.JSONField(null=True, blank=True)
    tags = models.JSONField(null=True, blank=True)

    # Geo
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Services and ports
    open_ports = models.JSONField(null=True, blank=True)
    services = models.JSONField(null=True, blank=True)

    # Vulns
    vulnerabilities = models.JSONField(null=True, blank=True)

    # Raw HTML/JSON dump
    raw_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"ZoomEyeInfo for {self.ip}"

    

class ZmapScan(models.Model):
    target = models.ForeignKey(Target, related_name='zmap_scans', on_delete=models.CASCADE)
    scan_date = models.DateTimeField(auto_now_add=True)
    scan_type = models.CharField(max_length=50, default='TCP SYN', help_text="e.g., TCP SYN, ICMP Echo")
    status = models.CharField(max_length=50, choices=[('Success', 'Success'), ('Failed', 'Failed')], default='Success')
    scan_flags = models.JSONField(null=True, blank=True, help_text="Zmap CLI flags used during scan")
    raw_output = models.TextField(null=True, blank=True, help_text="Raw Zmap output, if available")
    duration = models.FloatField(null=True, blank=True, help_text="Scan duration in seconds")
    open_ports = models.JSONField(null=True, blank=True, help_text="List of open ports detected")
    responders = models.JSONField(null=True, blank=True, help_text="List of IPs that responded")
    filtered_hosts = models.JSONField(null=True, blank=True, help_text="Hosts that were filtered or dropped")
    total_targets = models.IntegerField(null=True, blank=True)
    total_responded = models.IntegerField(null=True, blank=True)
    vpn_detected = models.BooleanField(default=False)
    scan_source = models.CharField(max_length=100, default='zmap')
    notes = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"Zmap Scan for {self.target.name} on {self.scan_date}"

    def process_results(self, parsed_data: dict):
        """Optional helper to populate model fields from a parsed Zmap result."""
        self.raw_output = parsed_data.get('raw_output', '')
        self.duration = parsed_data.get('duration')
        self.scan_flags = parsed_data.get('flags', {})
        self.open_ports = parsed_data.get('open_ports', [])
        self.responders = parsed_data.get('responders', [])
        self.filtered_hosts = parsed_data.get('filtered_hosts', [])
        self.total_targets = parsed_data.get('total_targets', len(self.responders or []))
        self.total_responded = parsed_data.get('total_responded', len(self.responders or []))
        self.vpn_detected = parsed_data.get('vpn_detected', False)
        self.notes = parsed_data.get('notes', '')

    def get_summary(self):
        return {
            'responders': len(self.responders or []),
            'open_ports': len(self.open_ports or []),
            'duration': self.duration,
            'status': self.status,
        }



class ProjectSonarData(models.Model):
    target = models.ForeignKey(Target, on_delete=models.CASCADE)
    dataset = models.CharField(max_length=50)  # fdns, rdns, ssl, http, etc.
    entry_count = models.IntegerField()
    data = models.JSONField()
    collected_at = models.DateTimeField(auto_now_add=True)