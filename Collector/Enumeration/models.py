from django.db import models
from InformationGathering.models import Target  # عدّل حسب مكان موديل Target

class EnumerationResult(models.Model):
    target = models.ForeignKey(Target, on_delete=models.CASCADE, related_name='enumeration_results')
    timestamp = models.DateTimeField(auto_now_add=True)

    smb_shares = models.TextField(blank=True, null=True)
    users_groups = models.TextField(blank=True, null=True)
    services_banners = models.TextField(blank=True, null=True)
    rpc_info = models.TextField(blank=True, null=True)
    netbios_info = models.TextField(blank=True, null=True)
    snmp_data = models.TextField(blank=True, null=True)
    ldap_data = models.TextField(blank=True, null=True)
    os_info = models.JSONField(blank=True, null=True)
    hidden_web_content = models.TextField(blank=True, null=True)

    tools_used = models.CharField(max_length=300, help_text="Comma-separated tools used (e.g. enum4linux, nmap, nessus, nikto-ng)")
    raw_output = models.TextField(blank=True, null=True)  # للإخراج الخام إذا أردت حفظه

    def __str__(self):
        return f"EnumerationResult for {self.target} at {self.timestamp}"



class AdvancedEnumResult(models.Model):
    target = models.GenericIPAddressField()
    domain = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField()
    hostname = models.CharField(max_length=255, blank=True)
    os_info = models.TextField(blank=True)
    open_ports = models.JSONField(default=dict)
    smb_info = models.TextField(blank=True)
    enum4linux_output = models.TextField(blank=True)
    rpc_output = models.TextField(blank=True)
    netbios_info = models.TextField(blank=True)
    snmp_info = models.TextField(blank=True)
    ldap_info = models.TextField(blank=True)
    dns_zone_transfer = models.TextField(blank=True)
    hidden_dirs = models.TextField(blank=True)

    def __str__(self):
        return f"Enum Result - {self.target} @ {self.timestamp}"
