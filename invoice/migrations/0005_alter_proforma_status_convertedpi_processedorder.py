# Generated by Django 5.0.3 on 2024-10-19 14:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0004_alter_orderlist_product'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proforma',
            name='status',
            field=models.CharField(choices=[('lost', 'LOST'), ('open', 'OPEN'), ('closed', 'CLOSED')], default='open', max_length=50, verbose_name='Status'),
        ),
        migrations.CreateModel(
            name='convertedPI',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_processed', models.BooleanField(default=False, verbose_name='Is Processed')),
                ('is_taxInvoice', models.BooleanField(default=False, verbose_name='Is Tax Invoice')),
                ('is_closed', models.BooleanField(default=False, verbose_name='Is Closed')),
                ('is_hold', models.BooleanField(default=False, verbose_name='Is Hold')),
                ('payment_status', models.CharField(choices=[('partial', 'Partial'), ('credit', 'Credit'), ('Full', 'Full')], max_length=50, verbose_name='Payment Status')),
                ('payment1_date', models.DateField(blank=True, null=True, verbose_name='Payment 1 Date')),
                ('payment1_amt', models.IntegerField(blank=True, null=True, verbose_name='Payment 1 Amount')),
                ('payment2_date', models.DateField(blank=True, null=True, verbose_name='Payment 1 Date')),
                ('payment2_amt', models.IntegerField(blank=True, null=True, verbose_name='Payment 2 Amount')),
                ('payment3_date', models.DateField(blank=True, null=True, verbose_name='Payment 1 Date')),
                ('payment3_amt', models.IntegerField(blank=True, null=True, verbose_name='Payment 3 Amount')),
                ('pi_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='invoice.proforma', verbose_name='PI ID')),
            ],
            options={
                'verbose_name': 'Converted PI',
                'verbose_name_plural': 'Converted PIs',
                'db_table': 'Converted_PI',
            },
        ),
        migrations.CreateModel(
            name='processedOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_type', models.CharField(choices=[('export', 'Outbound Insight'), ('online', 'Subscription'), ('domestic', 'Market Research'), ('import', 'Inbound Insight')], max_length=150, verbose_name='Report Type')),
                ('format', models.CharField(choices=[('10 days', '10 Days'), ('weekly', 'weekly'), ('monthly', 'Monthly'), ('sez(weekly)', 'SEZ (Weekly)'), ('incoterm', 'Incoterm'), ('sez', 'SEZ')], max_length=250, verbose_name='Format')),
                ('country', models.CharField(blank=True, max_length=150, null=True, verbose_name='Country')),
                ('hsn', models.CharField(blank=True, max_length=150, null=True, verbose_name='HSN')),
                ('product', models.CharField(blank=True, max_length=550, null=True, verbose_name='Product')),
                ('iec', models.CharField(blank=True, max_length=150, null=True, verbose_name='IEC')),
                ('exporter', models.CharField(blank=True, max_length=250, null=True, verbose_name='Exporter')),
                ('importer', models.CharField(blank=True, max_length=250, null=True, verbose_name='Importer')),
                ('foreign_country', models.CharField(blank=True, max_length=250, null=True, verbose_name='Foreign Country')),
                ('port', models.CharField(blank=True, max_length=250, null=True, verbose_name='Port')),
                ('from_month', models.CharField(max_length=50, verbose_name='From Month')),
                ('to_month', models.CharField(max_length=50, verbose_name='To Month')),
                ('last_dispatch_month', models.CharField(blank=True, max_length=50, null=True, verbose_name='Last Dispatch Month')),
                ('last_dispatch_date', models.DateField(blank=True, null=True, verbose_name='Last Dispatch Date')),
                ('order_status', models.CharField(choices=[('Complete', 'Complete'), ('Pending', 'Pending')], default='pending', max_length=50, verbose_name='Order Status')),
                ('last_sent_date', models.DateField(blank=True, null=True, verbose_name='last_sent_date')),
                ('order_date', models.DateTimeField(auto_now_add=True, verbose_name='last_sent_date')),
                ('pi_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='invoice.proforma', verbose_name='PI ID')),
            ],
            options={
                'verbose_name': 'Order Process',
                'verbose_name_plural': 'Order Process',
                'db_table': 'Processed_Order',
            },
        ),
    ]