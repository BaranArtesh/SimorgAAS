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
    


class AdvancedNmapScan(models.Model):
    target = models.ForeignKey(Target, on_delete=models.CASCADE)
    scan_type = models.CharField(max_length=100)  # مثل SYN, TCP Connect, UDP, Aggressive
    status = models.CharField(max_length=50)      # success / failed / timeout ...
    scan_output = models.JSONField()              # النص الخام / التفصيلي الكامل
    scan_flags = models.JSONField()               # مثل {"-sV": true, "-A": true}

    scan_duration = models.FloatField(null=True, blank=True)  # بالثواني

    # المنافذ والخدمات
    open_ports = models.JSONField(default=list)              # قائمة المنافذ المفتوحة
    filtered_ports = models.JSONField(default=list)          # المنافذ المحجوبة
    service_versions = models.JSONField(default=list)        # تفاصيل النسخ والخدمات لكل منفذ

    # معلومات النظام والشبكة
    os_details = models.JSONField(default=dict)              # ناتج nmap os detection
    host_uptime = models.CharField(max_length=100, null=True, blank=True)
    traceroute = models.JSONField(null=True, blank=True)     # hops وغيرها

    # السكربتات والثغرات
    scripts_output = models.JSONField(default=dict)          # كل نتائج NSE scripts
    vulnerabilities = models.JSONField(default=list)         # قائمة CVEs أو نتائج تحليل السكربتات

    # البروتوكولات المدعومة (tcp, udp, icmp, sctp, etc)
    protocols_detected = models.JSONField(default=list)

    # معلومات إضافية ممكنة
    ports_scanned = models.IntegerField(default=0)           # NEW: عدد المنافذ المفحوصة
    rate = models.IntegerField(default=0)                    # NEW: سرعة المسح (ports/sec)
    errors = models.JSONField(default=list)                  # NEW: أخطاء حصلت أثناء الفحص

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Advanced Scan for {self.target.host} - {self.created_at.date()}"
