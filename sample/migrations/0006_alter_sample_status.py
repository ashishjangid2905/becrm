# Generated by Django 5.0.3 on 2024-03-29 15:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sample', '0005_alter_sample_month'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sample',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('received', 'Received'), ('rejected', 'Rejected')], default='pending', max_length=50),
        ),
    ]
