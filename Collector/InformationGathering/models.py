from django.db import models

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
    target = models.OneToOneField(
        "Target", related_name="whois_info", on_delete=models.CASCADE
    )
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
        return f"WHOIS for {self.target.target_id}"



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

    def __str__(self):
        return f"IP Info for {self.target.target_id} ({self.ip_address})"
