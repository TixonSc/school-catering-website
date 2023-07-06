# Generated by Django 4.1.7 on 2023-03-13 13:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('artishok_website', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Class',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='Menu',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='School',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Pupil',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=64)),
                ('last_name', models.CharField(max_length=64)),
                ('phone_number', models.CharField(blank=True, max_length=28, null=True)),
                ('birth_date', models.DateField(blank=True, null=True)),
                ('class_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='artishok_website.class')),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('role', models.IntegerField()),
                ('first_name', models.CharField(max_length=64)),
                ('last_name', models.CharField(max_length=64)),
                ('phone_number', models.CharField(max_length=28)),
                ('class_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='artishok_website.class')),
                ('school_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='artishok_website.school')),
            ],
        ),
        migrations.CreateModel(
            name='MenuItem',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('weight', models.IntegerField(blank=True, null=True)),
                ('dish_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='artishok_website.dish')),
                ('menu_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='artishok_website.menu')),
            ],
        ),
        migrations.CreateModel(
            name='Meal',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('date', models.DateField()),
                ('time', models.TimeField()),
                ('menu_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='artishok_website.menu')),
                ('school_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='artishok_website.school')),
            ],
        ),
        migrations.AddField(
            model_name='class',
            name='school_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='artishok_website.school'),
        ),
        migrations.CreateModel(
            name='Child',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('verified', models.IntegerField()),
                ('parent_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='artishok_website.profile')),
                ('pupil_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='artishok_website.pupil')),
            ],
        ),
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('cart_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='artishok_website.cart')),
                ('meal_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='artishok_website.meal')),
                ('menu_item_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='artishok_website.menuitem')),
            ],
        ),
        migrations.AddField(
            model_name='cart',
            name='pupil_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='artishok_website.pupil'),
        ),
    ]
