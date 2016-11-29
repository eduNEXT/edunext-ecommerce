# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteOptions',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('options_blob', jsonfield.fields.JSONField(default={}, help_text='JSON string containing the extended edunext settings.', verbose_name='Extended Site Options')),
                ('site', models.ForeignKey(related_name='options', to='sites.Site')),
            ],
            options={
                'verbose_name_plural': 'stories',
            },
        ),
    ]
