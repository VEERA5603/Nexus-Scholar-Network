# Generated by Django 5.1.6 on 2025-03-18 02:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('staffnsn', '0006_award'),
    ]

    operations = [
        migrations.CreateModel(
            name='PublicationCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('journal_national', models.IntegerField(default=0)),
                ('journal_international', models.IntegerField(default=0)),
                ('conference_national', models.IntegerField(default=0)),
                ('conference_international', models.IntegerField(default=0)),
                ('books_published', models.IntegerField(default=0)),
                ('popular_articles', models.IntegerField(default=0)),
                ('faculty', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='publication_categories', to='staffnsn.faculty')),
            ],
        ),
    ]
