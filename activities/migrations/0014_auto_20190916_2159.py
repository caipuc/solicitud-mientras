# Generated by Django 2.2.2 on 2019-09-17 00:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("activities", "0013_auto_20190916_2155"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="activity",
            name="space_1",
        ),
        migrations.AddField(
            model_name="activity",
            name="space",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="space_1",
                to="activities.Space",
            ),
        ),
        migrations.AlterField(
            model_name="activity",
            name="state",
            field=models.CharField(
                choices=[
                    ("A", "Aprobada"),
                    ("R", "Rechazada"),
                    ("P", "Pendiente"),
                    ("C", "Cancelada"),
                    ("PA", "En revisión por Decanato"),
                    ("PC", "En revisión por CAi"),
                ],
                default="PC",
                max_length=2,
            ),
        ),
    ]
