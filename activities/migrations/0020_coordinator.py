# Generated by Django 2.2.5 on 2020-01-17 15:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0019_auto_20190925_2316'),
    ]

    operations = [
        migrations.CreateModel(
            name='Coordinator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('email', models.EmailField(max_length=254)),
            ],
        ),
    ]