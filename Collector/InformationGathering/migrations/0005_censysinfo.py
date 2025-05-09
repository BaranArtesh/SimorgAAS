# Generated by Django 5.2 on 2025-05-01 00:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('InformationGathering', '0004_shodaninfo'),
    ]

    operations = [
        migrations.CreateModel(
            name='CensysInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scan_date', models.DateTimeField(auto_now_add=True)),
                ('raw_data', models.JSONField(blank=True, null=True)),
                ('ip', models.GenericIPAddressField()),
                ('ip_int', models.BigIntegerField(blank=True, null=True)),
                ('asn', models.IntegerField(blank=True, null=True)),
                ('asn_name', models.CharField(blank=True, max_length=255, null=True)),
                ('asn_country_code', models.CharField(blank=True, max_length=2, null=True)),
                ('asn_description', models.TextField(blank=True, null=True)),
                ('location_city', models.CharField(blank=True, max_length=100, null=True)),
                ('location_country', models.CharField(blank=True, max_length=100, null=True)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
                ('protocols', models.JSONField(blank=True, null=True)),
                ('services', models.JSONField(blank=True, null=True)),
                ('tls_issuer', models.CharField(blank=True, max_length=255, null=True)),
                ('tls_subject', models.TextField(blank=True, null=True)),
                ('tls_not_before', models.DateTimeField(blank=True, null=True)),
                ('tls_not_after', models.DateTimeField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(blank=True, null=True)),
                ('source', models.CharField(blank=True, max_length=100, null=True)),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='censys_scans', to='InformationGathering.target')),
            ],
        ),
    ]
