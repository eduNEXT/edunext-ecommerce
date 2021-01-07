# Generated by Django 2.2.16 on 2020-12-30 23:08

from django.db import migrations
import jsonfield.encoder
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0061_auto_20200407_1725'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='extended_profile_fields',
            field=jsonfield.fields.JSONField(blank=True, dump_kwargs={'cls': jsonfield.encoder.JSONEncoder, 'separators': (',', ':')}, load_kwargs={}, null=True),
        ),
    ]
