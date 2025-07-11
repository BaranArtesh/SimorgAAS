# Generated by Django 5.2.3 on 2025-07-11 13:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('InformationGathering', '0015_zoomeyeinfo'),
        ('Scanning', '0002_rename_ports_masscanscan_open_ports'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScanResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scan_type', models.CharField(choices=[('masscan', 'Masscan'), ('nmap', 'Nmap')], max_length=50)),
                ('scan_date', models.DateTimeField(auto_now_add=True)),
                ('duration', models.FloatField(blank=True, null=True)),
                ('status', models.CharField(choices=[('Success', 'Success'), ('Failed', 'Failed')], default='Success', max_length=50)),
                ('raw_output', models.TextField(blank=True, null=True)),
                ('open_ports', models.JSONField(blank=True, null=True)),
                ('scan_flags', models.JSONField(blank=True, null=True)),
                ('responders', models.JSONField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scan_results', to='InformationGathering.target')),
            ],
        ),
        migrations.DeleteModel(
            name='MasscanScan',
        ),
    ]
