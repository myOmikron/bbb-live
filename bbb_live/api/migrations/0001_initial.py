# Generated by Django 3.1.7 on 2021-03-05 16:24

from django.db import migrations, models

from api.models import Streaming


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    def add_default(apps, schema_editor):
        stream = Streaming.objects.create(running=False)
        stream.save()

    operations = [
        migrations.CreateModel(
            name='Streaming',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('running', models.BooleanField(default=False)),
            ],
        ),
        migrations.RunPython(add_default)
    ]