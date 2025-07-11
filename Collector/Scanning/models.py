from django.db import models
from InformationGathering.models import Target

class ScanResult(models.Model):
    SCAN_TYPES = [
        ('masscan', 'Masscan'),
        ('nmap', 'Nmap'),
    ]

    STATUS_CHOICES = [
        ('Success', 'Success'),
        ('Failed', 'Failed'),
    ]

    target = models.ForeignKey(Target, related_name='scan_results', on_delete=models.CASCADE)
    scan_type = models.CharField(max_length=50, choices=SCAN_TYPES)
    scan_date = models.DateTimeField(auto_now_add=True)
    duration = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Success')
    raw_output = models.TextField(null=True, blank=True)
    open_ports = models.JSONField(null=True, blank=True)
    scan_flags = models.JSONField(null=True, blank=True)
    responders = models.JSONField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.scan_type.capitalize()} Scan for {self.target.name} on {self.scan_date.strftime('%Y-%m-%d %H:%M:%S')}"
