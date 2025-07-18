# Generated by Django 5.2 on 2025-05-10 21:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('InformationGathering', '0010_alter_censysinfo_last_updated_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZmapScan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scan_date', models.DateTimeField(auto_now_add=True)),
                ('scan_type', models.CharField(default='TCP SYN', help_text='e.g., TCP SYN, ICMP Echo', max_length=50)),
                ('status', models.CharField(choices=[('Success', 'Success'), ('Failed', 'Failed')], default='Success', max_length=50)),
                ('scan_flags', models.JSONField(blank=True, help_text='Zmap CLI flags used during scan', null=True)),
                ('raw_output', models.TextField(blank=True, help_text='Raw Zmap output, if available', null=True)),
                ('duration', models.FloatField(blank=True, help_text='Scan duration in seconds', null=True)),
                ('open_ports', models.JSONField(blank=True, help_text='List of open ports detected', null=True)),
                ('responders', models.JSONField(blank=True, help_text='List of IPs that responded', null=True)),
                ('filtered_hosts', models.JSONField(blank=True, help_text='Hosts that were filtered or dropped', null=True)),
                ('total_targets', models.IntegerField(blank=True, null=True)),
                ('total_responded', models.IntegerField(blank=True, null=True)),
                ('vpn_detected', models.BooleanField(default=False)),
                ('scan_source', models.CharField(default='zmap', max_length=100)),
                ('notes', models.TextField(blank=True, null=True)),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='zmap_scans', to='InformationGathering.target')),
            ],
        ),
    ]
