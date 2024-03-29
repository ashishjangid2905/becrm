# Generated by Django 5.0.3 on 2024-03-28 16:05

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sample', '0003_sample_last_edited'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sample',
            name='month',
            field=models.SmallIntegerField(blank=True, choices=[(None, 'Any'), (1, 'Jan'), (2, 'Feb'), (3, 'Mar'), (4, 'Apr'), (5, 'May'), (6, 'Jun'), (7, 'Jul'), (8, 'Aug'), (9, 'Sep'), (10, 'Oct'), (11, 'Nov'), (12, 'Dec')], default=None, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(13)]),
        ),
    ]