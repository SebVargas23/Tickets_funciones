# Generated by Django 5.1.1 on 2024-10-20 00:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autenticacion', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='cargo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='autenticacion.cargo'),
        ),
    ]
