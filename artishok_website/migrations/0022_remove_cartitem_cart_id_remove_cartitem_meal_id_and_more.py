# Generated by Django 4.1.7 on 2023-07-22 12:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('artishok_website', '0021_remove_classmanager_archived_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cartitem',
            name='cart_id',
        ),
        migrations.RemoveField(
            model_name='cartitem',
            name='meal_id',
        ),
        migrations.RemoveField(
            model_name='cartitem',
            name='menu_item_id',
        ),
        migrations.RemoveField(
            model_name='orderitem',
            name='meal_id',
        ),
        migrations.RemoveField(
            model_name='orderitem',
            name='menu_item_id',
        ),
        migrations.RemoveField(
            model_name='orderitem',
            name='order_id',
        ),
        migrations.AddField(
            model_name='order',
            name='count',
            field=models.IntegerField(default=0, verbose_name='Кількість порцій'),
        ),
        migrations.AddField(
            model_name='order',
            name='meal_id',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to='artishok_website.meal', verbose_name='Прийом їжі'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='menu_item_id',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to='artishok_website.menuitem', verbose_name='Страва'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='profile',
            name='debt',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='child',
            name='verified',
            field=models.CharField(choices=[('RQ', 'Запит'), ('OK', 'Підтверджено'), ('NO', 'Відхилено')], default='RQ', max_length=2, verbose_name='Підтверджено'),
        ),
        migrations.AlterField(
            model_name='order',
            name='datetime',
            field=models.DateTimeField(null=True, verbose_name='Дата та час замовлення'),
        ),
        migrations.AlterField(
            model_name='order',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Ціна замовлення'),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('CAR', 'В кошику'), ('RES', 'Замовлено'), ('ACC', 'Прийнято'), ('DON', 'Виконано'), ('CAN', 'Скасовано')], default='CAR', max_length=3, verbose_name='Статус'),
        ),
        migrations.DeleteModel(
            name='Cart',
        ),
        migrations.DeleteModel(
            name='CartItem',
        ),
        migrations.DeleteModel(
            name='OrderItem',
        ),
    ]
