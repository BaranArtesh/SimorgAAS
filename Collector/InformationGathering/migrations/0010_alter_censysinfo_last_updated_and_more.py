# Generated by Django 5.2 on 2025-05-08 08:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('InformationGathering', '0009_censysinfo_collection_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='censysinfo',
            name='last_updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='censysinfo',
            name='source',
            field=models.CharField(blank=True, default='censys', max_length=100),
        ),
    ]
