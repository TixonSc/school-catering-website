# Generated by Django 4.1.7 on 2023-07-18 16:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('artishok_website', '0020_alter_classmanager_options_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='classmanager',
            name='archived',
        ),
        migrations.RemoveField(
            model_name='schoolmanager',
            name='archived',
        ),
    ]
