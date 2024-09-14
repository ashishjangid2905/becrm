# Generated by Django 5.0.3 on 2024-08-31 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0004_alter_orderlist_lumpsum_amt_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='proforma',
            name='edited_by',
            field=models.IntegerField(blank=True, null=True, verbose_name='Edited By'),
        ),
        migrations.AddField(
            model_name='proforma',
            name='is_sez',
            field=models.BooleanField(default=False, verbose_name='Is_SEZ'),
        ),
        migrations.AddField(
            model_name='proforma',
            name='lut_no',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='LUT No'),
        ),
        migrations.AddField(
            model_name='proforma',
            name='vendor_code',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Vendor Code'),
        ),
        migrations.AlterField(
            model_name='proforma',
            name='approved_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Approved At'),
        ),
        migrations.AlterField(
            model_name='proforma',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created At'),
        ),
        migrations.AlterField(
            model_name='proforma',
            name='edited_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Edited At'),
        ),
    ]
