# Generated by Django 5.0.9 on 2025-01-01 16:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lead', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='leads',
            name='status',
            field=models.CharField(choices=[('new lead', 'New Lead'), ('hot lead', 'Hot Lead'), ('client', 'Client'), ('not interest', 'Not Interested'), ('lost', 'Lost')], default='new lead', max_length=50, verbose_name='Lead Status'),
        ),
    ]