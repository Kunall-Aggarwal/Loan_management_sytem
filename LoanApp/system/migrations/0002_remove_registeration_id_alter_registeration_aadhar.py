# Generated by Django 4.2.5 on 2023-09-12 18:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='registeration',
            name='id',
        ),
        migrations.AlterField(
            model_name='registeration',
            name='aadhar',
            field=models.CharField(max_length=100, primary_key=True, serialize=False),
        ),
    ]
