# Generated by Django 4.1.7 on 2023-03-29 16:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artishok_website', '0005_product_is_glucose'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pupil',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]