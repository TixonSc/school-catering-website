# Generated by Django 4.1.7 on 2023-07-18 16:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('artishok_website', '0019_remove_profile_class_id_school_code_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='classmanager',
            options={'verbose_name': 'Менеджер класу', 'verbose_name_plural': 'Менеджери класів'},
        ),
        migrations.RemoveField(
            model_name='classmanager',
            name='school_id',
        ),
        migrations.AddField(
            model_name='classmanager',
            name='class_id',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='artishok_website.class', verbose_name='Клас'),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='SchoolManager',
            fields=[
                ('archived', models.BooleanField(default=False, verbose_name='Видалено (в архіві)')),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('profile_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='artishok_website.profile', verbose_name='Профіль')),
                ('school_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='artishok_website.school', verbose_name='Школа')),
            ],
            options={
                'verbose_name': 'Менеджер школи',
                'verbose_name_plural': 'Менеджери шкіл',
            },
        ),
    ]