# Generated by Django 5.0.3 on 2024-07-24 12:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0003_proforma_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderlist',
            name='lumpsum_amt',
            field=models.IntegerField(blank=True, null=True, verbose_name='Lumpsum'),
        ),
        migrations.AlterField(
            model_name='orderlist',
            name='order_status',
            field=models.CharField(default='pending', max_length=50, verbose_name='Order Status'),
        ),
        migrations.AlterField(
            model_name='orderlist',
            name='total_price',
            field=models.IntegerField(blank=True, null=True, verbose_name='Total Price'),
        ),
        migrations.AlterField(
            model_name='orderlist',
            name='unit_price',
            field=models.IntegerField(blank=True, null=True, verbose_name='Unit Price'),
        ),
    ]
