# Generated by Django 5.1.1 on 2024-10-27 22:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0002_rename_comentario_resolucion_ticket_comentario'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicio',
            name='categoria',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='tickets.categoria'),
            preserve_default=False,
        ),
    ]
